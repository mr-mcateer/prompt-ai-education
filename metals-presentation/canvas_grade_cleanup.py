#!/usr/bin/env python3
"""
Bulk-grade Shop Cleanup assignments in Canvas.
Grades all enrolled students at 10/10 for the 2/19 Shop Cleanup assignments
across all metals courses.

Usage:
  # Preview what will be graded (no changes):
  python3 canvas_grade_cleanup.py --dry-run

  # Actually grade:
  python3 canvas_grade_cleanup.py --execute
"""

import argparse
import os
import sys
import time
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from tools.env_loader import get_env

ALL_COURSE_IDS = [23164, 23132, 23157, 23188, 23177, 23124, 23344]
CLEANUP_PATTERN = "Shop Cleanup"
GRADE_SCORE = 10.0  # out of 10


def get_canvas():
    from canvasapi import Canvas
    url = get_env("CANVAS_API_URL")
    token = get_env("CANVAS_API_TOKEN")
    return Canvas(url, token)


def run(dry_run=True):
    canvas = get_canvas()
    total_graded = 0
    total_skipped = 0

    for cid in ALL_COURSE_IDS:
        course = canvas.get_course(cid)
        cname = getattr(course, "name", f"Course {cid}")
        print(f"\n{'=' * 60}")
        print(f"  {cname} (ID: {cid})")
        print(f"{'=' * 60}")

        # Find Shop Cleanup assignments that are ungraded
        for asgn in course.get_assignments():
            aname = getattr(asgn, "name", "")
            if CLEANUP_PATTERN not in aname:
                continue
            if not getattr(asgn, "published", False):
                continue

            # Skip future assignments (due date after today)
            due_at = getattr(asgn, "due_at", None)
            if due_at:
                try:
                    due_dt = datetime.fromisoformat(due_at.replace("Z", "+00:00"))
                    if due_dt > datetime.now(timezone.utc):
                        continue
                except (ValueError, TypeError):
                    pass

            points = getattr(asgn, "points_possible", 0)
            print(f"\n  Assignment: {aname} ({points} pts, due: {due_at})")

            # Get all submissions
            for sub in asgn.get_submissions():
                wf = getattr(sub, "workflow_state", "")
                score = getattr(sub, "score", None)
                user_id = sub.user_id

                # Skip already-graded submissions
                if score is not None:
                    total_skipped += 1
                    continue

                # Get student name from enrollment
                student_name = f"Student {user_id}"
                try:
                    user = canvas.get_user(user_id)
                    student_name = getattr(user, "sortable_name", getattr(user, "name", student_name))
                except Exception:
                    pass

                if dry_run:
                    print(f"    [DRY RUN] Would grade: {student_name} -> {GRADE_SCORE}/{points}")
                else:
                    try:
                        sub.edit(submission={"posted_grade": str(GRADE_SCORE)})
                        print(f"    [GRADED] {student_name} -> {GRADE_SCORE}/{points}")
                        time.sleep(0.1)  # Rate limit safety
                    except Exception as e:
                        print(f"    [ERROR] {student_name}: {e}")

                total_graded += 1

    print(f"\n{'=' * 60}")
    mode = "DRY RUN" if dry_run else "COMPLETE"
    print(f"  {mode}")
    print(f"{'=' * 60}")
    print(f"  Would grade: {total_graded}" if dry_run else f"  Graded: {total_graded}")
    print(f"  Already graded (skipped): {total_skipped}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bulk-grade Shop Cleanup assignments")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dry-run", action="store_true",
                       help="Preview changes without grading")
    group.add_argument("--execute", action="store_true",
                       help="Actually grade the assignments")
    args = parser.parse_args()

    run(dry_run=not args.execute)
