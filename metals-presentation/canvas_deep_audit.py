#!/usr/bin/env python3
"""
Deep instructional audit of Canvas metals courses.
Pulls everything: assignments, rubrics, modules, pages, discussions,
grading policies, due date patterns, submission patterns.
"""

import os
import sys
import json
from datetime import datetime, timezone

METALS_COURSE_IDS = [23164, 23132, 23157, 23188, 23177]

def get_canvas():
    from canvasapi import Canvas
    url = os.environ.get("CANVAS_API_URL")
    token = os.environ.get("CANVAS_API_TOKEN")
    if not url or not token:
        print("ERROR: Set CANVAS_API_URL and CANVAS_API_TOKEN")
        sys.exit(1)
    return Canvas(url, token)

def audit():
    canvas = get_canvas()
    # Use first course as representative (they're identical per prior audit)
    course = canvas.get_course(23164, include=["total_students"])
    course_name = getattr(course, "name", "")

    print("=" * 80)
    print("  DEEP INSTRUCTIONAL AUDIT — METALS COURSES")
    print("  Representative course:", course_name)
    print("=" * 80)

    # ── ASSIGNMENTS ───────────────────────────────────────────
    print("\n\n" + "═" * 80)
    print("  1. ASSIGNMENT INVENTORY")
    print("═" * 80)

    assignments = list(course.get_assignments())
    for a in assignments:
        name = getattr(a, "name", "")
        desc = getattr(a, "description", "") or "(no description)"
        points = getattr(a, "points_possible", 0)
        sub_types = getattr(a, "submission_types", [])
        due = getattr(a, "due_at", None)
        published = getattr(a, "published", False)
        grading_type = getattr(a, "grading_type", "")
        group_id = getattr(a, "assignment_group_id", "")
        has_rubric = getattr(a, "rubric", None)
        rubric_settings = getattr(a, "rubric_settings", None)
        peer_reviews = getattr(a, "peer_reviews", False)
        moderated = getattr(a, "moderated_grading", False)
        omit_from_final = getattr(a, "omit_from_final_grade", False)
        lock_at = getattr(a, "lock_at", None)
        unlock_at = getattr(a, "unlock_at", None)
        allowed_extensions = getattr(a, "allowed_extensions", [])

        print(f"\n  {'─' * 76}")
        print(f"  {name}")
        print(f"  {'─' * 76}")
        print(f"    Points: {points}  |  Grading: {grading_type}  |  Published: {published}")
        print(f"    Submission types: {sub_types}")
        print(f"    Due: {due}  |  Unlock: {unlock_at}  |  Lock: {lock_at}")
        print(f"    Has rubric: {bool(has_rubric)}  |  Peer reviews: {peer_reviews}")
        print(f"    Omit from final: {omit_from_final}  |  Allowed extensions: {allowed_extensions}")
        # Truncate description for display
        desc_clean = desc.replace("\n", " ").replace("<p>", "").replace("</p>", " ")
        desc_clean = desc_clean.replace("<br>", " ").replace("<strong>", "").replace("</strong>", "")
        desc_clean = desc_clean.replace("<ul>", "").replace("</ul>", "").replace("<li>", "- ").replace("</li>", " ")
        desc_clean = desc_clean.replace("&nbsp;", " ").replace("<em>", "").replace("</em>", "")
        desc_clean = " ".join(desc_clean.split())[:500]
        print(f"    Description: {desc_clean}")

        if has_rubric:
            print(f"    Rubric criteria:")
            for crit in has_rubric:
                cdesc = crit.get("description", "")
                cpts = crit.get("points", 0)
                ratings = crit.get("ratings", [])
                rating_str = " | ".join(f"{r.get('description','')}: {r.get('points','')}" for r in ratings)
                print(f"      - {cdesc} ({cpts} pts): {rating_str}")

    # ── ASSIGNMENT GROUPS & WEIGHTING ─────────────────────────
    print("\n\n" + "═" * 80)
    print("  2. GRADING STRUCTURE")
    print("═" * 80)

    groups = list(course.get_assignment_groups())
    total_weight = 0
    for g in groups:
        gname = getattr(g, "name", "")
        weight = getattr(g, "group_weight", 0)
        total_weight += weight
        # Count assignments in this group
        group_assignments = [a for a in assignments if getattr(a, "assignment_group_id", None) == g.id]
        group_points = sum(getattr(a, "points_possible", 0) or 0 for a in group_assignments)
        print(f"  {gname}: {weight}% weight, {len(group_assignments)} assignments, {group_points} total pts")
        for a in group_assignments:
            pub = "✓" if getattr(a, "published", False) else "✗"
            print(f"    [{pub}] {getattr(a, 'name', '')} ({getattr(a, 'points_possible', 0)} pts)")

    print(f"\n  Total weight: {total_weight}%")
    if total_weight != 100:
        print(f"  ⚠ WARNING: weights don't sum to 100%!")

    # ── MODULES ───────────────────────────────────────────────
    print("\n\n" + "═" * 80)
    print("  3. MODULE STRUCTURE")
    print("═" * 80)

    modules = list(course.get_modules())
    for m in modules:
        mname = getattr(m, "name", "")
        published = getattr(m, "published", False)
        prereqs = getattr(m, "prerequisite_module_ids", [])
        require_sequential = getattr(m, "require_sequential_progress", False)
        print(f"\n  Module: {mname} (published={published})")
        print(f"    Sequential progress required: {require_sequential}")
        print(f"    Prerequisites: {prereqs if prereqs else 'none'}")
        try:
            items = list(m.get_module_items())
            for item in items:
                title = getattr(item, "title", "")
                itype = getattr(item, "type", "")
                completion_req = getattr(item, "completion_requirement", None)
                print(f"    - [{itype}] {title}", end="")
                if completion_req:
                    print(f"  (requirement: {completion_req})", end="")
                print()
        except Exception as e:
            print(f"    Error reading items: {e}")

    # ── PAGES ─────────────────────────────────────────────────
    print("\n\n" + "═" * 80)
    print("  4. PAGES / CONTENT")
    print("═" * 80)

    try:
        pages = list(course.get_pages())
        if pages:
            for p in pages:
                title = getattr(p, "title", "")
                published = getattr(p, "published", False)
                print(f"  [{('✓' if published else '✗')}] {title}")
        else:
            print("  (no pages)")
    except Exception as e:
        print(f"  Error: {e}")

    # ── DISCUSSIONS ───────────────────────────────────────────
    print("\n\n" + "═" * 80)
    print("  5. DISCUSSIONS")
    print("═" * 80)

    try:
        discussions = list(course.get_discussion_topics())
        if discussions:
            for d in discussions:
                title = getattr(d, "title", "")
                published = getattr(d, "published", False)
                print(f"  [{('✓' if published else '✗')}] {title}")
        else:
            print("  (no discussions)")
    except Exception as e:
        print(f"  Error: {e}")

    # ── SUBMISSION ANALYTICS ──────────────────────────────────
    print("\n\n" + "═" * 80)
    print("  6. SUBMISSION PATTERN ANALYSIS (across all 5 courses)")
    print("═" * 80)

    all_courses_data = {}
    for cid in METALS_COURSE_IDS:
        c = canvas.get_course(cid)
        cname = getattr(c, "name", "")
        enrollments = list(c.get_enrollments(type=["StudentEnrollment"]))
        student_count = len(enrollments)

        # Per-assignment submission stats
        asgn_stats = []
        for a in c.get_assignments():
            aname = getattr(a, "name", "")
            points = getattr(a, "points_possible", 0)
            published = getattr(a, "published", False)
            if not published:
                continue

            subs = list(a.get_submissions())
            submitted = 0
            graded_count = 0
            scores = []
            late_count = 0
            missing_count = 0

            for s in subs:
                wf = getattr(s, "workflow_state", "")
                score = getattr(s, "score", None)
                late = getattr(s, "late", False)
                missing = getattr(s, "missing", False)

                if wf in ("submitted", "graded", "pending_review"):
                    submitted += 1
                if score is not None:
                    graded_count += 1
                    scores.append(score)
                if late:
                    late_count += 1
                if missing:
                    missing_count += 1

            avg = sum(scores) / len(scores) if scores else 0
            avg_pct = (avg / points * 100) if points and scores else 0

            asgn_stats.append({
                "name": aname,
                "student_count": student_count,
                "submitted": submitted,
                "graded": graded_count,
                "avg_score": avg,
                "avg_pct": avg_pct,
                "points": points,
                "late": late_count,
                "missing": missing_count,
                "scores": scores,
            })

        all_courses_data[cid] = {"name": cname, "students": student_count, "stats": asgn_stats}

    for cid, data in all_courses_data.items():
        print(f"\n  {data['name']} ({data['students']} students):")
        for s in data["stats"]:
            sub_rate = (s["submitted"] / s["student_count"] * 100) if s["student_count"] else 0
            print(f"    {s['name'][:45]:<45s}  "
                  f"Sub: {s['submitted']:>2d}/{s['student_count']:<2d} ({sub_rate:>5.1f}%)  "
                  f"Avg: {s['avg_pct']:>5.1f}%  "
                  f"Late: {s['late']}  Missing: {s['missing']}")

    # ── COURSE SETTINGS ───────────────────────────────────────
    print("\n\n" + "═" * 80)
    print("  7. COURSE SETTINGS")
    print("═" * 80)

    settings_attrs = [
        "default_view", "hide_final_grades", "grading_standard_id",
        "restrict_enrollments_to_course_dates", "time_zone",
        "storage_quota_mb", "is_public", "public_syllabus",
        "allow_student_forum_attachments", "allow_wiki_comments",
    ]
    for attr in settings_attrs:
        val = getattr(course, attr, "N/A")
        print(f"  {attr}: {val}")

    print("\n" + "=" * 80)
    print("  AUDIT COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    audit()
