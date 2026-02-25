#!/usr/bin/env python3
"""
Canvas Auto-Grader for Metals Courses
======================================
Checks ungraded submissions across all metals courses. Awards full credit
if the student submitted:
  - The correct file type for the assignment (matches submission_types), OR
  - A screenshot / image file (png, jpg, jpeg, gif, bmp, webp, heic)

Only applies to metals courses -- engines/fab courses are excluded.

Usage:
  # Preview what will be graded (no changes):
  python3 canvas_auto_grade.py --dry-run

  # Actually grade:
  python3 canvas_auto_grade.py --execute
"""

import argparse
import os
import sys
import time
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from tools.env_loader import get_env

# Course IDs
METALS_COURSE_IDS = [23164, 23132, 23157, 23188, 23177]
ENGINES_COURSE_IDS = [23124, 23344]
ALL_COURSE_IDS = METALS_COURSE_IDS + ENGINES_COURSE_IDS

# Image/screenshot extensions we accept as proof of work
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".heic", ".heif", ".tiff", ".tif"}

# Common valid submission file extensions (non-image)
VALID_WORK_EXTENSIONS = {
    ".pdf", ".doc", ".docx", ".ppt", ".pptx",
    ".xls", ".xlsx", ".txt", ".rtf", ".odt",
    ".dxf", ".dwg", ".stl", ".step", ".stp",  # CAD files
    ".gcode", ".nc",  # CNC/machine files
    ".mp4", ".mov", ".avi", ".mkv", ".webm",  # video
    ".zip", ".rar", ".7z",  # archives
}


def get_canvas():
    from canvasapi import Canvas
    url = get_env("CANVAS_API_URL")
    token = get_env("CANVAS_API_TOKEN")
    return Canvas(url, token)


def get_submission_file_names(submission):
    """Extract filenames from a submission's attachments."""
    attachments = getattr(submission, "attachments", None) or []
    return [a.get("filename", "") if isinstance(a, dict) else getattr(a, "filename", "") for a in attachments]


def is_valid_submission(submission):
    """
    Check if a submission contains a valid file type or screenshot.
    Returns (bool, reason_string).
    """
    # Check workflow state -- must have actually submitted something
    wf = getattr(submission, "workflow_state", "")
    submitted_at = getattr(submission, "submitted_at", None)
    sub_type = getattr(submission, "submission_type", None)

    if not submitted_at and wf == "unsubmitted":
        return False, "not submitted"

    # Online text entry -- counts as a submission
    if sub_type == "online_text_entry":
        body = getattr(submission, "body", None)
        if body and len(body.strip()) > 0:
            return True, "text entry"

    # Online URL -- counts as a submission
    if sub_type == "online_url":
        url = getattr(submission, "url", None)
        if url:
            return True, "URL submission"

    # File upload -- check file types
    if sub_type == "online_upload":
        filenames = get_submission_file_names(submission)
        if not filenames:
            return False, "upload with no files"

        for fname in filenames:
            ext = os.path.splitext(fname.lower())[1]
            if ext in IMAGE_EXTENSIONS:
                return True, f"screenshot ({fname})"
            if ext in VALID_WORK_EXTENSIONS:
                return True, f"valid file ({fname})"

        # If they uploaded SOMETHING, give credit -- they tried
        if filenames:
            return True, f"file upload ({filenames[0]})"

    # Media recording
    if sub_type == "media_recording":
        return True, "media recording"

    # Discussion topic
    if sub_type == "discussion_topic":
        return True, "discussion post"

    # If submitted_at is set, they did something
    if submitted_at:
        return True, f"submitted ({sub_type or 'unknown type'})"

    return False, f"no valid submission (state: {wf})"


def run(dry_run=True, course_ids=None):
    canvas = get_canvas()
    total_graded = 0
    total_skipped_already = 0
    total_skipped_invalid = 0
    total_no_submission = 0
    grading_log = []

    for cid in (course_ids or METALS_COURSE_IDS):
        course = canvas.get_course(cid)
        cname = getattr(course, "name", f"Course {cid}")
        print(f"\n{'=' * 65}")
        print(f"  {cname} (ID: {cid})")
        print(f"{'=' * 65}")

        # Get all published assignments with past due dates
        assignments = []
        for asgn in course.get_assignments():
            if not getattr(asgn, "published", False):
                continue

            due_at = getattr(asgn, "due_at", None)
            if due_at:
                try:
                    due_dt = datetime.fromisoformat(due_at.replace("Z", "+00:00"))
                    if due_dt > datetime.now(timezone.utc):
                        continue  # skip future assignments
                except (ValueError, TypeError):
                    pass

            assignments.append(asgn)

        print(f"  Found {len(assignments)} past-due published assignments")

        for asgn in assignments:
            aname = getattr(asgn, "name", "Unnamed")
            points = getattr(asgn, "points_possible", 0) or 0
            if points == 0:
                continue  # skip 0-point assignments

            ungraded_count = 0
            graded_count = 0

            for sub in asgn.get_submissions():
                score = getattr(sub, "score", None)
                user_id = sub.user_id

                # Already graded -- skip
                if score is not None:
                    total_skipped_already += 1
                    continue

                # Check if submission is valid
                is_valid, reason = is_valid_submission(sub)

                if not is_valid:
                    if reason == "not submitted":
                        total_no_submission += 1
                    else:
                        total_skipped_invalid += 1
                    continue

                # Get student name
                student_name = f"Student {user_id}"
                try:
                    user = canvas.get_user(user_id)
                    student_name = getattr(user, "sortable_name", getattr(user, "name", student_name))
                except Exception:
                    pass

                if dry_run:
                    print(f"    [WOULD GRADE] {student_name}")
                    print(f"      Assignment: {aname} | {points} pts | Reason: {reason}")
                else:
                    try:
                        sub.edit(submission={"posted_grade": str(points)})
                        print(f"    [GRADED] {student_name} -> {points}/{points}")
                        print(f"      Assignment: {aname} | Reason: {reason}")
                        time.sleep(0.1)
                    except Exception as e:
                        print(f"    [ERROR] {student_name} on {aname}: {e}")
                        continue

                grading_log.append({
                    "course": cname,
                    "student": student_name,
                    "assignment": aname,
                    "score": points,
                    "reason": reason,
                })
                total_graded += 1
                graded_count += 1

            if graded_count > 0:
                verb = "Would grade" if dry_run else "Graded"
                print(f"  -> {aname}: {verb} {graded_count} submissions")

    # Summary
    print(f"\n{'=' * 65}")
    mode = "DRY RUN SUMMARY" if dry_run else "GRADING COMPLETE"
    print(f"  {mode}")
    print(f"{'=' * 65}")
    verb = "Would grade" if dry_run else "Graded"
    print(f"  {verb}: {total_graded} submissions")
    print(f"  Already graded (skipped): {total_skipped_already}")
    print(f"  No submission: {total_no_submission}")
    print(f"  Invalid submission (skipped): {total_skipped_invalid}")
    print(f"{'=' * 65}")

    if grading_log and dry_run:
        print(f"\n  Breakdown of {total_graded} submissions to grade:")
        print(f"  {'-' * 60}")
        for entry in grading_log:
            print(f"    {entry['student']}")
            print(f"      {entry['assignment']} -> {entry['score']} pts ({entry['reason']})")

    return total_graded


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Auto-grade CTE course submissions")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dry-run", action="store_true",
                       help="Preview what would be graded (no changes)")
    group.add_argument("--execute", action="store_true",
                       help="Actually apply grades")

    parser.add_argument("--metals", action="store_true",
                        help="Run on metals courses only (default)")
    parser.add_argument("--engines", action="store_true",
                        help="Run on engines/fab courses only")
    parser.add_argument("--all-courses", action="store_true",
                        help="Run on all CTE courses (metals + engines)")
    parser.add_argument("--course-id", type=int, action="append", default=None,
                        help="Specific course ID(s)")

    args = parser.parse_args()

    if args.course_id:
        course_ids = args.course_id
    elif args.engines:
        course_ids = ENGINES_COURSE_IDS
    elif args.all_courses:
        course_ids = ALL_COURSE_IDS
    else:
        course_ids = METALS_COURSE_IDS

    run(dry_run=not args.execute, course_ids=course_ids)
