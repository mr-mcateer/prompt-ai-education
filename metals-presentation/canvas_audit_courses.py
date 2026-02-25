#!/usr/bin/env python3
"""
Canvas Course Audit & Sync Tool
================================
Compares assignment structure across multiple Canvas courses and optionally
syncs them so they all have the same assignments and settings.

Usage:
  # Step 1 — Audit differences:
  python3 canvas_audit_courses.py --audit

  # Step 2 — Sync missing assignments from a source course to others:
  python3 canvas_audit_courses.py --sync --source-id <SOURCE_COURSE_ID>

Environment variables required:
  CANVAS_API_URL   e.g. https://csd509j.instructure.com
  CANVAS_API_TOKEN your API access token
"""

import argparse
import json
import os
import sys

METALS_COURSE_IDS = [23164, 23132, 23157, 23188, 23177]


def get_canvas():
    from canvasapi import Canvas
    url = os.environ.get("CANVAS_API_URL")
    token = os.environ.get("CANVAS_API_TOKEN")
    if not url or not token:
        print("ERROR: Set CANVAS_API_URL and CANVAS_API_TOKEN")
        sys.exit(1)
    return Canvas(url, token)


def audit_courses():
    """Compare assignment structure across all metals courses."""
    canvas = get_canvas()

    courses = {}
    for cid in METALS_COURSE_IDS:
        course = canvas.get_course(cid)
        course_name = getattr(course, "name", f"Course {cid}")

        # Get assignments
        assignments = []
        for a in course.get_assignments():
            assignments.append({
                "id": a.id,
                "name": getattr(a, "name", ""),
                "points_possible": getattr(a, "points_possible", 0),
                "submission_types": getattr(a, "submission_types", []),
                "due_at": getattr(a, "due_at", None),
                "published": getattr(a, "published", False),
                "assignment_group_id": getattr(a, "assignment_group_id", None),
            })

        # Get assignment groups
        groups = []
        for g in course.get_assignment_groups():
            groups.append({
                "id": g.id,
                "name": getattr(g, "name", ""),
                "group_weight": getattr(g, "group_weight", 0),
            })

        # Get modules
        modules = []
        for m in course.get_modules():
            items = []
            try:
                for item in m.get_module_items():
                    items.append({
                        "title": getattr(item, "title", ""),
                        "type": getattr(item, "type", ""),
                    })
            except Exception:
                pass
            modules.append({
                "id": m.id,
                "name": getattr(m, "name", ""),
                "published": getattr(m, "published", False),
                "items_count": len(items),
                "items": items,
            })

        # Get course settings
        settings = {
            "grading_standard_id": getattr(course, "grading_standard_id", None),
            "default_view": getattr(course, "default_view", None),
            "hide_final_grades": getattr(course, "hide_final_grades", None),
        }

        # Student count
        enrollments = list(course.get_enrollments(type=["StudentEnrollment"]))

        courses[cid] = {
            "name": course_name,
            "assignments": sorted(assignments, key=lambda a: a["name"]),
            "assignment_groups": sorted(groups, key=lambda g: g["name"]),
            "modules": modules,
            "settings": settings,
            "student_count": len(enrollments),
        }

    # ── Print audit report ────────────────────────────────────
    print("=" * 80)
    print("  CANVAS METALS COURSE AUDIT")
    print("=" * 80)

    # Course overview
    print(f"\n{'─' * 80}")
    print(f"  {'Course':<30s} {'ID':>6s}  {'Students':>8s}  {'Assignments':>11s}  {'Modules':>7s}")
    print(f"{'─' * 80}")
    for cid in METALS_COURSE_IDS:
        c = courses[cid]
        print(f"  {c['name']:<30s} {cid:>6d}  {c['student_count']:>8d}  "
              f"{len(c['assignments']):>11d}  {len(c['modules']):>7d}")

    # Assignment comparison
    print(f"\n{'═' * 80}")
    print(f"  ASSIGNMENT COMPARISON")
    print(f"{'═' * 80}")

    # Collect all unique assignment names
    all_names = set()
    for c in courses.values():
        for a in c["assignments"]:
            all_names.add(a["name"])

    all_names = sorted(all_names)

    for name in all_names:
        present_in = []
        missing_from = []
        points = set()
        due_dates = set()
        published_states = set()

        for cid in METALS_COURSE_IDS:
            c = courses[cid]
            match = [a for a in c["assignments"] if a["name"] == name]
            if match:
                present_in.append(cid)
                a = match[0]
                points.add(a["points_possible"])
                due_dates.add(a["due_at"])
                published_states.add(a["published"])
            else:
                missing_from.append(cid)

        status = "OK" if len(missing_from) == 0 else "MISMATCH"
        points_str = "/".join(str(p) for p in points)
        due_str = "/".join(str(d) for d in due_dates)
        pub_str = "/".join(str(p) for p in published_states)

        if status == "MISMATCH" or len(points) > 1 or len(due_dates) > 1 or len(published_states) > 1:
            print(f"\n  [{status}] {name}")
            print(f"    Points: {points_str}  |  Due: {due_str}  |  Published: {pub_str}")
            if missing_from:
                missing_names = [courses[cid]["name"] for cid in missing_from]
                print(f"    MISSING FROM: {', '.join(missing_names)}")
            if len(points) > 1:
                print(f"    POINTS MISMATCH across courses")
            if len(due_dates) > 1:
                print(f"    DUE DATE MISMATCH across courses")
            if len(published_states) > 1:
                print(f"    PUBLISHED STATE MISMATCH across courses")
        else:
            print(f"  [OK] {name}  ({points_str} pts, published={pub_str})")

    # Assignment group comparison
    print(f"\n{'═' * 80}")
    print(f"  ASSIGNMENT GROUP COMPARISON")
    print(f"{'═' * 80}")
    all_group_names = set()
    for c in courses.values():
        for g in c["assignment_groups"]:
            all_group_names.add(g["name"])
    for gname in sorted(all_group_names):
        present = []
        weights = set()
        for cid in METALS_COURSE_IDS:
            c = courses[cid]
            match = [g for g in c["assignment_groups"] if g["name"] == gname]
            if match:
                present.append(cid)
                weights.add(match[0]["group_weight"])
        status = "OK" if len(present) == len(METALS_COURSE_IDS) else "MISMATCH"
        weight_str = "/".join(str(w) for w in weights)
        print(f"  [{status}] {gname} (weight: {weight_str}, in {len(present)}/{len(METALS_COURSE_IDS)} courses)")

    # Module comparison
    print(f"\n{'═' * 80}")
    print(f"  MODULE COMPARISON")
    print(f"{'═' * 80}")
    for cid in METALS_COURSE_IDS:
        c = courses[cid]
        print(f"\n  {c['name']}:")
        if c["modules"]:
            for m in c["modules"]:
                pub = "published" if m["published"] else "UNPUBLISHED"
                print(f"    - {m['name']} ({m['items_count']} items, {pub})")
        else:
            print(f"    (no modules)")

    print(f"\n{'═' * 80}")
    print(f"  AUDIT COMPLETE")
    print(f"{'═' * 80}")

    return courses


def sync_courses(source_id):
    """Sync assignments from source course to all other metals courses."""
    canvas = get_canvas()
    source = canvas.get_course(source_id)
    source_name = getattr(source, "name", f"Course {source_id}")
    print(f"Source course: {source_name} (ID: {source_id})")

    # Get source assignments
    source_assignments = {}
    for a in source.get_assignments():
        name = getattr(a, "name", "")
        source_assignments[name] = {
            "name": name,
            "description": getattr(a, "description", ""),
            "points_possible": getattr(a, "points_possible", 0),
            "submission_types": getattr(a, "submission_types", []),
            "due_at": getattr(a, "due_at", None),
            "unlock_at": getattr(a, "unlock_at", None),
            "lock_at": getattr(a, "lock_at", None),
            "published": getattr(a, "published", False),
        }

    print(f"  Source has {len(source_assignments)} assignments")

    target_ids = [cid for cid in METALS_COURSE_IDS if cid != source_id]

    for cid in target_ids:
        target = canvas.get_course(cid)
        target_name = getattr(target, "name", f"Course {cid}")
        print(f"\n{'─' * 60}")
        print(f"  Syncing to: {target_name} (ID: {cid})")

        # Get existing assignments
        existing = {}
        for a in target.get_assignments():
            existing[getattr(a, "name", "")] = a

        for name, src_data in source_assignments.items():
            if name in existing:
                # Check if settings match, update if different
                tgt = existing[name]
                changes = {}
                if getattr(tgt, "points_possible", 0) != src_data["points_possible"]:
                    changes["points_possible"] = src_data["points_possible"]
                if getattr(tgt, "due_at", None) != src_data["due_at"]:
                    changes["due_at"] = src_data["due_at"]

                if changes:
                    tgt.edit(assignment=changes)
                    print(f"    UPDATED: {name} ({changes})")
                else:
                    print(f"    OK: {name}")
            else:
                # Create missing assignment
                new_params = {
                    "name": src_data["name"],
                    "description": src_data["description"],
                    "points_possible": src_data["points_possible"],
                    "submission_types": src_data["submission_types"],
                    "due_at": src_data["due_at"],
                    "unlock_at": src_data["unlock_at"],
                    "lock_at": src_data["lock_at"],
                    "published": src_data["published"],
                }
                target.create_assignment(assignment=new_params)
                print(f"    CREATED: {name} ({src_data['points_possible']} pts)")

    print(f"\n{'═' * 60}")
    print(f"  SYNC COMPLETE")
    print(f"{'═' * 60}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Canvas Course Audit & Sync")
    parser.add_argument("--audit", action="store_true",
                        help="Audit differences across metals courses")
    parser.add_argument("--sync", action="store_true",
                        help="Sync assignments from source to all others")
    parser.add_argument("--source-id", type=int,
                        help="Source course ID for sync")
    args = parser.parse_args()

    if args.audit:
        audit_courses()
    elif args.sync:
        if not args.source_id:
            print("ERROR: --sync requires --source-id <ID>")
            sys.exit(1)
        sync_courses(args.source_id)
    else:
        parser.print_help()
