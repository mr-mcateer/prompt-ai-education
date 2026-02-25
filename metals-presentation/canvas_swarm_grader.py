#!/usr/bin/env python3
"""
Canvas Agent Swarm Grader -- AI-assisted submission review for Metals courses.
Uses Gemini to review each submission against the rubric and generate
clarifying questions per criterion. Does NOT assign scores.

Modes:
  --dry-run    List evaluable submissions (no downloads, no Gemini calls)
  --evaluate   Download files, run Gemini review, generate terminal report
  --execute    Full pipeline + post clarifying questions as Canvas comments

Usage:
  python3 canvas_swarm_grader.py --dry-run
  python3 canvas_swarm_grader.py --evaluate --assignment "Sheet Metal"
  python3 canvas_swarm_grader.py --evaluate --student-id 12345
  python3 canvas_swarm_grader.py --execute --assignment "Sheet Metal"
"""

import argparse
import concurrent.futures
import os
import sys
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone

import requests

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from tools.env_loader import get_env
from tools.swarm_evaluator import (
    extract_text_from_docx,
    extract_text_from_pdf,
    get_gemini_client,
    review_image_submission,
    review_submission_personal,
    review_text_submission,
    strip_html,
)

# ── Constants ─────────────────────────────────────────────────
METALS_COURSE_IDS = [23164, 23132, 23157, 23188, 23177]
ENGINES_COURSE_IDS = [23124, 23344]
ALL_COURSE_IDS = METALS_COURSE_IDS + ENGINES_COURSE_IDS
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".heic"}
DOC_EXTENSIONS = {".pdf", ".docx", ".doc"}
CAD_EXTENSIONS = {".stl", ".dxf", ".dwg", ".step", ".stp", ".gcode", ".nc"}

# Rubric definitions (imported from canvas_create_rubrics.py structure)
# We load these as fallback; prefer live rubrics from Canvas API
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from canvas_create_rubrics import RUBRICS as FALLBACK_RUBRICS
except ImportError:
    FALLBACK_RUBRICS = {}

MIME_MAP = {
    ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
    ".gif": "image/gif", ".bmp": "image/bmp", ".webp": "image/webp",
    ".heic": "image/heic",
}


# ── Data Classes ──────────────────────────────────────────────

@dataclass
class SubmissionContent:
    content_type: str  # "text", "image", "cad_file", "url", "media", "unknown"
    text: str = None
    image_bytes: bytes = None
    image_mime: str = None
    filename: str = None
    size_kb: float = 0


@dataclass
class ReviewResult:
    student_name: str
    student_id: int
    assignment_name: str
    assignment_id: int
    course_name: str
    review_data: dict = field(default_factory=dict)
    contents_summary: list = field(default_factory=list)
    error: str = None


# ── Rate Limiter ──────────────────────────────────────────────

class RateLimiter:
    def __init__(self, calls_per_minute=30):
        self.delay = 60.0 / calls_per_minute
        self.lock = threading.Lock()
        self.last_call = 0

    def wait(self):
        with self.lock:
            now = time.time()
            elapsed = now - self.last_call
            if elapsed < self.delay:
                time.sleep(self.delay - elapsed)
            self.last_call = time.time()


# ── Canvas Helpers ────────────────────────────────────────────

def get_canvas():
    from canvasapi import Canvas
    url = get_env("CANVAS_API_URL")
    token = get_env("CANVAS_API_TOKEN")
    return Canvas(url, token)


def fetch_rubric_for_assignment(assignment, assignment_name=None):
    """
    Extract rubric criteria from a Canvas assignment.
    Returns a dict in the same format as RUBRICS criteria, or None.
    """
    # Try live rubric from Canvas
    rubric = getattr(assignment, "rubric", None)
    if rubric and isinstance(rubric, list):
        criteria = {}
        for i, crit in enumerate(rubric):
            ratings = {}
            for j, r in enumerate(crit.get("ratings", [])):
                ratings[str(j)] = {
                    "description": r.get("description", ""),
                    "points": r.get("points", 0),
                }
            criteria[str(i)] = {
                "description": crit.get("description", ""),
                "points": crit.get("points", 0),
                "ratings": ratings,
                "canvas_id": crit.get("id", ""),
            }
        return criteria

    # Fallback to local definitions
    aname = assignment_name or getattr(assignment, "name", "")
    for key, rubric_def in FALLBACK_RUBRICS.items():
        if key in aname or aname in key:
            return rubric_def["criteria"]

    return None


def _att_get(attachment, key, default=None):
    """Get attribute from attachment (handles both dict and File object)."""
    if isinstance(attachment, dict):
        return attachment.get(key, default)
    return getattr(attachment, key, default)


def download_attachment(attachment, token):
    """Download a single attachment. Returns (filename, bytes, content_type) or (filename, None, error)."""
    filename = _att_get(attachment, "filename") or _att_get(attachment, "display_name", "unknown")
    url = _att_get(attachment, "url")
    size = _att_get(attachment, "size", 0)

    if not url:
        return filename, None, "no download URL"

    if size and size > MAX_FILE_SIZE_BYTES:
        return filename, None, f"too large ({size / 1024 / 1024:.1f} MB)"

    try:
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.get(url, headers=headers, timeout=30, allow_redirects=True)
        resp.raise_for_status()
        return filename, resp.content, resp.headers.get("content-type", "")
    except Exception as e:
        return filename, None, str(e)


def download_all_attachments(attachments, token, max_workers=4):
    """Download multiple attachments concurrently. Returns list of (filename, bytes, content_type)."""
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(download_attachment, att, token): att for att in attachments}
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())
    return results


# ── Content Preparation ───────────────────────────────────────

def prepare_submission(submission, downloaded_files):
    """Route submission content to appropriate handlers. Returns list of SubmissionContent."""
    contents = []
    sub_type = getattr(submission, "submission_type", None)

    # Text entry
    if sub_type == "online_text_entry":
        body = getattr(submission, "body", None)
        if body:
            text = strip_html(body)
            if text:
                contents.append(SubmissionContent(
                    content_type="text", text=text, filename="text_entry",
                ))

    # URL submission
    if sub_type == "online_url":
        url = getattr(submission, "url", None)
        if url:
            contents.append(SubmissionContent(
                content_type="url", text=f"URL submitted: {url}", filename="url_entry",
            ))

    # Media recording
    if sub_type == "media_recording":
        contents.append(SubmissionContent(
            content_type="media", text="[Media recording -- requires manual review]",
            filename="media_recording",
        ))

    # Process downloaded files
    for filename, file_bytes, content_type in downloaded_files:
        if file_bytes is None:
            contents.append(SubmissionContent(
                content_type="unknown", text=f"[Download failed: {content_type}]",
                filename=filename,
            ))
            continue

        ext = os.path.splitext(filename.lower())[1]
        size_kb = len(file_bytes) / 1024

        if ext in IMAGE_EXTENSIONS:
            mime = MIME_MAP.get(ext, "image/jpeg")
            contents.append(SubmissionContent(
                content_type="image", image_bytes=file_bytes, image_mime=mime,
                filename=filename, size_kb=size_kb,
            ))
        elif ext == ".pdf":
            text = extract_text_from_pdf(file_bytes)
            contents.append(SubmissionContent(
                content_type="text", text=text, filename=filename, size_kb=size_kb,
            ))
        elif ext in (".docx", ".doc"):
            text = extract_text_from_docx(file_bytes)
            contents.append(SubmissionContent(
                content_type="text", text=text, filename=filename, size_kb=size_kb,
            ))
        elif ext in CAD_EXTENSIONS:
            contents.append(SubmissionContent(
                content_type="cad_file",
                text=f"[CAD/machine file: {filename}, {size_kb:.0f} KB]",
                filename=filename, size_kb=size_kb,
            ))
        else:
            contents.append(SubmissionContent(
                content_type="unknown", text=f"[File: {filename}, {size_kb:.0f} KB]",
                filename=filename, size_kb=size_kb,
            ))

    return contents


# ── Evaluation ────────────────────────────────────────────────

def evaluate_submission(gemini_client, rubric_criteria, student_name,
                        assignment_name, contents, rate_limiter):
    """Evaluate a single submission via Gemini. Returns review dict."""
    # Combine all text content
    all_text = []
    image_content = None
    file_metadata = []

    for c in contents:
        if c.content_type == "text" and c.text:
            all_text.append(c.text)
        if c.content_type == "image" and c.image_bytes and not image_content:
            image_content = c  # use first image
        if c.filename:
            file_metadata.append({
                "filename": c.filename,
                "size_kb": f"{c.size_kb:.0f}",
                "type": c.content_type,
            })

    combined_text = "\n\n".join(all_text) if all_text else None

    rate_limiter.wait()

    # Choose review method
    if image_content:
        return review_image_submission(
            gemini_client, rubric_criteria,
            image_content.image_bytes, image_content.image_mime,
            assignment_name, supplemental_text=combined_text,
            file_metadata=file_metadata if len(file_metadata) > 1 else None,
        )
    elif combined_text:
        return review_text_submission(
            gemini_client, rubric_criteria,
            combined_text, assignment_name,
            file_metadata=file_metadata if file_metadata else None,
        )
    else:
        return {
            "criterion_reviews": [],
            "overall_observations": "No reviewable content found in submission.",
            "flags": ["no_content"],
            "submission_quality": "empty",
        }


# ── Personal Mode Evaluation ─────────────────────────────────

def evaluate_submission_personal(gemini_client, student_name,
                                  assignment_name, contents, rate_limiter):
    """Evaluate a single submission in personal mode. Returns dict with 'wondering'."""
    all_text = []
    image_content = None
    file_metadata = []

    for c in contents:
        if c.content_type == "text" and c.text:
            all_text.append(c.text)
        if c.content_type == "image" and c.image_bytes and not image_content:
            image_content = c
        if c.filename:
            file_metadata.append({
                "filename": c.filename,
                "type": c.content_type,
            })

    combined_text = "\n\n".join(all_text) if all_text else None

    rate_limiter.wait()

    return review_submission_personal(
        gemini_client, assignment_name,
        contents_text=combined_text,
        image_bytes=image_content.image_bytes if image_content else None,
        image_mime=image_content.image_mime if image_content else None,
        file_metadata=file_metadata if file_metadata else None,
    )


def format_personal_comment(review_data):
    """Format personal wondering into a plain Canvas comment."""
    return review_data.get("wondering", "").strip()


# ── Comment Formatting ────────────────────────────────────────

def format_review_comment(review_data):
    """Format review data into a clean Canvas comment."""
    lines = []
    lines.append("Questions from your submission review:")
    lines.append("")

    for cr in review_data.get("criterion_reviews", []):
        cname = cr.get("criterion_name", "Unknown")
        questions = cr.get("questions", [])
        if questions:
            lines.append(f"{cname}:")
            for q in questions:
                lines.append(f"  - {q}")
            lines.append("")

    flags = review_data.get("flags", [])
    if flags:
        lines.append("Items to address:")
        for f in flags:
            label = f.replace("_", " ").title()
            lines.append(f"  - {label}")
        lines.append("")

    overall = review_data.get("overall_observations", "")
    if overall:
        lines.append(f"Overall: {overall}")

    return "\n".join(lines)


# ── Report Output ─────────────────────────────────────────────

def print_review_report(all_results):
    """Print the full review report to terminal."""
    print(f"\n{'=' * 70}")
    print(f"  AGENT SWARM REVIEW REPORT")
    print(f"  Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")
    print(f"{'=' * 70}")

    total = len(all_results)
    errors = sum(1 for r in all_results if r.error)
    reviewed = total - errors
    print(f"  Submissions reviewed: {reviewed}")
    print(f"  Errors: {errors}")

    # Group by course
    by_course = {}
    for r in all_results:
        by_course.setdefault(r.course_name, []).append(r)

    for course_name, results in sorted(by_course.items()):
        print(f"\n{'=' * 70}")
        print(f"  {course_name}")
        print(f"{'=' * 70}")

        # Group by assignment within course
        by_asgn = {}
        for r in results:
            by_asgn.setdefault(r.assignment_name, []).append(r)

        for asgn_name, asgn_results in sorted(by_asgn.items()):
            print(f"\n  Assignment: {asgn_name}")
            print(f"  {'-' * 60}")

            for r in sorted(asgn_results, key=lambda x: x.student_name):
                print(f"\n    Student: {r.student_name}")

                if r.error:
                    print(f"    [ERROR] {r.error}")
                    continue

                rd = r.review_data
                quality = rd.get("submission_quality", "unknown")
                print(f"    Quality: {quality}")

                # Content summary
                if r.contents_summary:
                    print(f"    Files: {', '.join(r.contents_summary)}")

                # Personal mode: show wondering
                wondering = rd.get("wondering", "")
                if wondering:
                    print(f"    Wondering: {wondering}")
                else:
                    # Per-criterion reviews (standard mode)
                    for cr in rd.get("criterion_reviews", []):
                        cname = cr.get("criterion_name", "?")
                        comp = cr.get("completeness", "?")
                        obs = cr.get("observations", "")
                        print(f"\n    [{comp.upper()}] {cname}")
                        if obs:
                            print(f"      Observation: {obs}")
                        for q in cr.get("questions", []):
                            print(f"      ? {q}")

                    # Flags
                    flags = rd.get("flags", [])
                    if flags:
                        print(f"\n    Flags: {', '.join(flags)}")

                    # Overall
                    overall = rd.get("overall_observations", "")
                    if overall:
                        print(f"\n    Summary: {overall}")

    print(f"\n{'=' * 70}")
    print(f"  END OF REPORT")
    print(f"{'=' * 70}")


# ── Main Pipeline ─────────────────────────────────────────────

def run(mode, course_ids, assignment_filter, student_id_filter,
        ungraded_only, gemini_rpm, all_submissions, personal=False):
    """Main execution pipeline."""

    canvas = get_canvas()
    token = get_env("CANVAS_API_TOKEN")
    all_results = []

    # Only init Gemini for evaluate/execute
    gemini_client = None
    rate_limiter = None
    if mode in ("evaluate", "execute"):
        gemini_client = get_gemini_client()
        rate_limiter = RateLimiter(calls_per_minute=gemini_rpm)

    for cid in course_ids:
        course = canvas.get_course(cid, include=["total_students"])
        cname = getattr(course, "name", f"Course {cid}")
        print(f"\n{'=' * 65}")
        print(f"  {cname} (ID: {cid})")
        print(f"{'=' * 65}")

        # Get published assignments with rubrics
        evaluable = []
        for asgn in course.get_assignments(include=["rubric"]):
            if not getattr(asgn, "published", False):
                continue

            aname = getattr(asgn, "name", "")

            # Filter by assignment name if specified
            if assignment_filter and assignment_filter.lower() not in aname.lower():
                continue

            # Skip future assignments
            due_at = getattr(asgn, "due_at", None)
            if due_at:
                try:
                    due_dt = datetime.fromisoformat(due_at.replace("Z", "+00:00"))
                    if due_dt > datetime.now(timezone.utc):
                        continue
                except (ValueError, TypeError):
                    pass

            # Personal mode: no rubric needed
            if personal:
                rubric = None
            else:
                rubric = fetch_rubric_for_assignment(asgn, aname)
                if not rubric:
                    continue

            points = getattr(asgn, "points_possible", 0) or 0
            if points == 0:
                continue

            evaluable.append((asgn, aname, rubric, points))

        label = "past-due assignments" if personal else "assignments with rubrics"
        print(f"  Found {len(evaluable)} {label}")

        for asgn, aname, rubric, points in evaluable:
            print(f"\n  Assignment: {aname} ({points} pts)")

            submissions_to_review = []
            for sub in asgn.get_submissions():
                uid = sub.user_id

                # Filter by student ID if specified
                if student_id_filter and uid != student_id_filter:
                    continue

                # Skip already graded (unless --all-submissions)
                score = getattr(sub, "score", None)
                if ungraded_only and not all_submissions and score is not None:
                    continue

                # Must have submitted something
                submitted_at = getattr(sub, "submitted_at", None)
                wf = getattr(sub, "workflow_state", "")
                if not submitted_at and wf == "unsubmitted":
                    continue

                # Get student name
                student_name = f"Student {uid}"
                try:
                    user = canvas.get_user(uid)
                    student_name = getattr(user, "sortable_name",
                                           getattr(user, "name", student_name))
                except Exception:
                    pass

                submissions_to_review.append((sub, uid, student_name))

            if not submissions_to_review:
                print(f"    No submissions to review")
                continue

            print(f"    {len(submissions_to_review)} submissions to review")

            # ── DRY RUN: just list ────────────────────────────
            if mode == "dry-run":
                for sub, uid, sname in submissions_to_review:
                    sub_type = getattr(sub, "submission_type", "unknown")
                    attachments = getattr(sub, "attachments", []) or []
                    fnames = [_att_get(a, "filename", "?") for a in attachments]
                    files_str = ", ".join(fnames) if fnames else sub_type
                    print(f"      {sname} | {files_str}")
                continue

            # ── EVALUATE / EXECUTE: download + review ─────────
            for sub, uid, sname in submissions_to_review:
                print(f"    Reviewing: {sname}...", end="", flush=True)

                try:
                    # Download attachments
                    attachments = getattr(sub, "attachments", []) or []
                    if attachments:
                        downloaded = download_all_attachments(attachments, token)
                    else:
                        downloaded = []

                    # Prepare content
                    contents = prepare_submission(sub, downloaded)
                    contents_summary = [c.filename for c in contents if c.filename]

                    if not contents:
                        print(" [no content]")
                        all_results.append(ReviewResult(
                            student_name=sname, student_id=uid,
                            assignment_name=aname, assignment_id=asgn.id,
                            course_name=cname, error="no reviewable content",
                            contents_summary=contents_summary,
                        ))
                        continue

                    # Evaluate via Gemini
                    if personal:
                        review_data = evaluate_submission_personal(
                            gemini_client, sname, aname, contents, rate_limiter,
                        )
                    else:
                        review_data = evaluate_submission(
                            gemini_client, rubric, sname, aname, contents, rate_limiter,
                        )

                    result = ReviewResult(
                        student_name=sname, student_id=uid,
                        assignment_name=aname, assignment_id=asgn.id,
                        course_name=cname, review_data=review_data,
                        contents_summary=contents_summary,
                    )

                    if personal:
                        wondering = review_data.get("wondering", "")
                        if "error" in review_data and not wondering:
                            result.error = review_data.get("error", "unknown")
                            print(f" [error: {result.error[:50]}]")
                        else:
                            quality = review_data.get("submission_quality", "?")
                            preview = wondering[:80] + "..." if len(wondering) > 80 else wondering
                            print(f" [{quality}] {preview}")
                    else:
                        if "error" in review_data and review_data.get("criterion_reviews") == []:
                            result.error = review_data["error"]
                            print(f" [error: {result.error[:50]}]")
                        else:
                            quality = review_data.get("submission_quality", "?")
                            n_questions = sum(
                                len(cr.get("questions", []))
                                for cr in review_data.get("criterion_reviews", [])
                            )
                            print(f" [{quality}, {n_questions} questions]")

                    all_results.append(result)

                    # Post comment if execute mode
                    if mode == "execute" and not result.error:
                        if personal:
                            comment_text = format_personal_comment(review_data)
                        else:
                            comment_text = format_review_comment(review_data)
                        if comment_text.strip():
                            try:
                                sub.edit(comment={"text_comment": comment_text})
                                print(f"      [COMMENT POSTED]")
                                time.sleep(0.1)
                            except Exception as e:
                                print(f"      [COMMENT ERROR: {e}]")

                except Exception as e:
                    print(f" [error: {e}]")
                    all_results.append(ReviewResult(
                        student_name=sname, student_id=uid,
                        assignment_name=aname, assignment_id=asgn.id,
                        course_name=cname, error=str(e),
                    ))

            time.sleep(0.1)  # Canvas rate limit

    # Print report for evaluate/execute modes
    if mode in ("evaluate", "execute") and all_results:
        print_review_report(all_results)

    # Dry run summary
    if mode == "dry-run":
        total = sum(1 for _ in all_results) if all_results else 0
        print(f"\n{'=' * 65}")
        print(f"  DRY RUN COMPLETE")
        print(f"{'=' * 65}")
        # Count from terminal output since dry-run doesn't populate all_results
        print(f"  Use --evaluate to run AI review")
        print(f"  Use --execute to review + post comments to Canvas")
        print(f"{'=' * 65}")

    return all_results


# ── CLI ───────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="AI-assisted submission review for metals courses (questions only, no scores)"
    )

    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument("--dry-run", action="store_true",
                            help="List evaluable submissions (no downloads, no Gemini)")
    mode_group.add_argument("--evaluate", action="store_true",
                            help="Run AI review and generate report (no Canvas writes)")
    mode_group.add_argument("--execute", action="store_true",
                            help="Run AI review and post comments to Canvas")

    parser.add_argument("--assignment", type=str, default=None,
                        help="Filter by assignment name (partial match)")
    parser.add_argument("--metals", action="store_true",
                        help="Run on metals courses only (default)")
    parser.add_argument("--engines", action="store_true",
                        help="Run on engines/fab courses only")
    parser.add_argument("--all-courses", action="store_true",
                        help="Run on all CTE courses (metals + engines)")
    parser.add_argument("--course-id", type=int, action="append", default=None,
                        help="Specific course ID(s)")
    parser.add_argument("--student-id", type=int, default=None,
                        help="Evaluate a single student by Canvas ID")
    parser.add_argument("--ungraded-only", action="store_true", default=True,
                        help="Only review ungraded submissions (default)")
    parser.add_argument("--all-submissions", action="store_true",
                        help="Review all submissions including already graded")
    parser.add_argument("--gemini-rpm", type=int, default=30,
                        help="Gemini API rate limit in calls/minute (default: 30)")
    parser.add_argument("--personal", action="store_true",
                        help="Personal mode: post one brief wondering per student (no rubric needed)")

    args = parser.parse_args()

    # Personal mode auto-enables all-submissions (since auto-grade runs first)
    if args.personal:
        args.all_submissions = True

    # Determine mode
    if args.dry_run:
        mode = "dry-run"
    elif args.evaluate:
        mode = "evaluate"
    else:
        mode = "execute"

    # Determine course IDs
    if args.course_id:
        course_ids = args.course_id
        course_label = f"{len(course_ids)} specified course(s)"
    elif args.engines:
        course_ids = ENGINES_COURSE_IDS
        course_label = f"{len(course_ids)} engines/fab sections"
    elif args.all_courses:
        course_ids = ALL_COURSE_IDS
        course_label = f"{len(course_ids)} CTE sections (metals + engines)"
    else:
        course_ids = METALS_COURSE_IDS
        course_label = f"{len(course_ids)} metals sections"

    print(f"\n{'=' * 65}")
    print(f"  CANVAS AGENT SWARM GRADER")
    print(f"  Mode: {mode.upper()}")
    print(f"  Courses: {course_label}")
    if args.assignment:
        print(f"  Assignment filter: {args.assignment}")
    if args.student_id:
        print(f"  Student filter: {args.student_id}")
    if args.personal:
        print(f"  Style: PERSONAL (one wondering per student)")
    print(f"{'=' * 65}")

    run(
        mode=mode,
        course_ids=course_ids,
        assignment_filter=args.assignment,
        student_id_filter=args.student_id,
        ungraded_only=args.ungraded_only,
        gemini_rpm=args.gemini_rpm,
        all_submissions=args.all_submissions,
        personal=args.personal,
    )


if __name__ == "__main__":
    main()
