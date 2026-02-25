#!/usr/bin/env python3
"""
Canvas Grades & Submissions Exporter
=====================================
Pulls all assignments, submissions, and grades from your Canvas metals
courses into a single local CSV spreadsheet.

Usage:
  # Step 1 — List courses to find your metals class IDs:
  python3 canvas_export_grades.py --list-courses

  # Step 2 — Export one course:
  python3 canvas_export_grades.py --course-id 12345

  # Step 3 — Export multiple courses into one spreadsheet:
  python3 canvas_export_grades.py --course-id 12345 --course-id 67890

  # Step 4 — Export with detailed submission data (comments, attachments):
  python3 canvas_export_grades.py --course-id 12345 --detailed

Environment variables required:
  CANVAS_API_URL   e.g. https://yourschool.instructure.com
  CANVAS_API_TOKEN your API access token

Output:
  metals_grades_export.csv  — one row per student per assignment
"""

import argparse
import csv
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from tools.env_loader import get_env


def get_canvas():
    """Initialize Canvas API connection."""
    from canvasapi import Canvas
    url = get_env("CANVAS_API_URL")
    token = get_env("CANVAS_API_TOKEN")
    return Canvas(url, token)


def list_courses():
    """List available Canvas courses."""
    canvas = get_canvas()
    print(f"\nYour Canvas Courses (active):")
    print(f"{'─' * 72}")
    print(f"  {'ID':>8s}  {'Name':<45s}  {'Term':<15s}")
    print(f"{'─' * 72}")
    for course in canvas.get_courses(enrollment_state="active"):
        name = getattr(course, "name", "Unnamed")[:45]
        term = getattr(course, "enrollment_term_id", "")
        print(f"  {course.id:>8d}  {name:<45s}  {str(term):<15s}")
    print(f"\nUse --course-id <ID> to export grades.")


def export_grades(course_ids, detailed=False):
    """Export all assignments and submissions to CSV."""
    canvas = get_canvas()
    output_dir = os.path.dirname(os.path.abspath(__file__))
    output_file = os.path.join(output_dir, "metals_grades_export.csv")

    all_rows = []

    for course_id in course_ids:
        print(f"\n{'═' * 60}")
        course = canvas.get_course(course_id)
        course_name = getattr(course, "name", f"Course {course_id}")
        print(f"  Course: {course_name} (ID: {course_id})")
        print(f"{'═' * 60}")

        # ── Get all students ──────────────────────────────────
        print("  Fetching students...")
        students = {}
        for enrollment in course.get_enrollments(type=["StudentEnrollment"]):
            user = enrollment.user
            uid = user["id"]
            students[uid] = {
                "name": user.get("sortable_name", user.get("name", "Unknown")),
                "sis_id": user.get("sis_user_id", ""),
            }
        print(f"    Found {len(students)} students")

        # ── Get all assignments ───────────────────────────────
        print("  Fetching assignments...")
        assignments = list(course.get_assignments())
        print(f"    Found {len(assignments)} assignments")

        # ── Get submissions for each assignment ───────────────
        for asgn in assignments:
            asgn_name = getattr(asgn, "name", "Unnamed")
            asgn_type = getattr(asgn, "submission_types", [])
            points_possible = getattr(asgn, "points_possible", 0)
            due_at = getattr(asgn, "due_at", None)
            asgn_group = getattr(asgn, "assignment_group_id", "")

            print(f"    Processing: {asgn_name[:50]}...", end="")

            try:
                submissions = list(asgn.get_submissions())
            except Exception as e:
                print(f" [ERROR: {e}]")
                continue

            sub_count = 0
            for sub in submissions:
                user_id = sub.user_id
                student_info = students.get(user_id, {
                    "name": f"Unknown ({user_id})",
                    "sis_id": "",
                })

                # Skip unsubmitted unless they have a grade
                workflow = getattr(sub, "workflow_state", "unsubmitted")
                score = getattr(sub, "score", None)
                grade = getattr(sub, "grade", None)
                submitted_at = getattr(sub, "submitted_at", None)
                late = getattr(sub, "late", False)
                missing = getattr(sub, "missing", False)
                attempt = getattr(sub, "attempt", None)

                if workflow == "unsubmitted" and score is None:
                    # Still record missing assignments
                    if missing:
                        pass  # fall through to record
                    else:
                        continue

                row = {
                    "course_name": course_name,
                    "course_id": course_id,
                    "student_name": student_info["name"],
                    "student_sis_id": student_info["sis_id"],
                    "student_canvas_id": user_id,
                    "assignment_name": asgn_name,
                    "assignment_id": asgn.id,
                    "assignment_type": ", ".join(asgn_type) if isinstance(asgn_type, list) else str(asgn_type),
                    "points_possible": points_possible,
                    "score": score,
                    "grade": grade,
                    "percentage": round(score / points_possible * 100, 1) if score is not None and points_possible else None,
                    "submitted_at": submitted_at,
                    "due_at": due_at,
                    "late": late,
                    "missing": missing,
                    "attempt": attempt,
                    "workflow_state": workflow,
                }

                if detailed:
                    # Pull submission comments
                    comments = getattr(sub, "submission_comments", [])
                    try:
                        comment_text = "; ".join(
                            (c.get("comment", "") if isinstance(c, dict)
                             else getattr(c, "comment", str(c)))
                            for c in comments
                        ) if comments else ""
                    except Exception:
                        comment_text = ""
                    row["comments"] = comment_text

                    # Attachments
                    attachments = getattr(sub, "attachments", [])
                    try:
                        attach_names = ", ".join(
                            (a.get("display_name", "") if isinstance(a, dict)
                             else getattr(a, "display_name", getattr(a, "filename", str(a))))
                            for a in attachments
                        ) if attachments else ""
                    except Exception:
                        attach_names = ""
                    row["attachments"] = attach_names

                all_rows.append(row)
                sub_count += 1

            print(f" ({sub_count} submissions)")

    # ── Write CSV ─────────────────────────────────────────────
    if not all_rows:
        print("\nNo submissions found. Check your course IDs.")
        return

    # Determine columns
    fieldnames = [
        "course_name", "course_id",
        "student_name", "student_sis_id", "student_canvas_id",
        "assignment_name", "assignment_id", "assignment_type",
        "points_possible", "score", "grade", "percentage",
        "submitted_at", "due_at", "late", "missing",
        "attempt", "workflow_state",
    ]
    if detailed:
        fieldnames.extend(["comments", "attachments"])

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"\n{'═' * 60}")
    print(f"  EXPORT COMPLETE")
    print(f"{'═' * 60}")
    print(f"  File: {output_file}")
    print(f"  Rows: {len(all_rows)}")
    print(f"  Courses: {len(course_ids)}")

    # Summary stats
    graded = [r for r in all_rows if r["score"] is not None]
    missing_count = sum(1 for r in all_rows if r["missing"])
    late_count = sum(1 for r in all_rows if r["late"])
    if graded:
        avg = sum(r["percentage"] for r in graded if r["percentage"] is not None) / len([r for r in graded if r["percentage"] is not None])
        print(f"  Graded submissions: {len(graded)}")
        print(f"  Average score: {avg:.1f}%")
    print(f"  Missing: {missing_count}")
    print(f"  Late: {late_count}")
    print(f"{'═' * 60}")


# ──────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Canvas Grades Exporter")
    parser.add_argument("--list-courses", action="store_true",
                        help="List Canvas courses to find IDs")
    parser.add_argument("--course-id", type=int, action="append",
                        help="Course ID(s) to export (can specify multiple)")
    parser.add_argument("--detailed", action="store_true",
                        help="Include submission comments and attachment names")
    args = parser.parse_args()

    if args.list_courses:
        list_courses()
    elif args.course_id:
        export_grades(args.course_id, detailed=args.detailed)
    else:
        parser.print_help()
