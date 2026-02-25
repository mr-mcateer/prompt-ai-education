#!/usr/bin/env python3
"""
Canvas Course Flow Checker -- Panel of Experts
================================================
Analyzes Canvas courses for hidden content, broken flow, instructional
design gaps, and technical errors. Organized as four expert perspectives:
  1. Visibility -- hidden/unpublished items students cannot see
  2. Flow       -- module sequencing, prerequisites, orphaned content
  3. Design     -- due dates, points, rubrics, assignment group placement
  4. Technical  -- weight totals, duplicates, broken references

Usage:
  python3 canvas_flow_check.py --dry-run                    # All 7 courses
  python3 canvas_flow_check.py --dry-run --course-id 23164  # Single course
  python3 canvas_flow_check.py --dry-run --metals           # Metals only
  python3 canvas_flow_check.py --dry-run --engines          # Engines only
  python3 canvas_flow_check.py --dry-run --markdown         # Save report
  python3 canvas_flow_check.py --fix                        # Auto-fix safe issues
"""

import argparse
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from tools.env_loader import get_env

# ── Constants ─────────────────────────────────────────────────
METALS_IDS = [23164, 23132, 23157, 23188, 23177]
ENGINES_IDS = [23124, 23344]
ALL_IDS = METALS_IDS + ENGINES_IDS

# ANSI colors
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
GREEN = "\033[92m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


# ── Data Structures ──────────────────────────────────────────

class Severity(Enum):
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"


SEVERITY_COLORS = {
    Severity.CRITICAL: RED,
    Severity.WARNING: YELLOW,
    Severity.INFO: CYAN,
}

EXPERT_LABELS = {
    "visibility": "Visibility Expert",
    "flow": "Flow Expert",
    "design": "Instructional Design Expert",
    "technical": "Technical Expert",
}


@dataclass
class Finding:
    expert: str          # "visibility", "flow", "design", "technical"
    severity: Severity
    title: str
    detail: str
    fix_suggestion: str
    auto_fixable: bool = False
    fix_action: dict = field(default_factory=dict)


@dataclass
class CourseData:
    course_id: int
    course_name: str
    assignments: list
    assignment_groups: list
    modules: list           # list of (module, [items])
    pages: list
    discussions: list
    # Derived lookups
    assignments_by_id: dict = field(default_factory=dict)
    assignments_by_name: dict = field(default_factory=dict)
    module_item_content_ids: set = field(default_factory=set)
    module_item_titles: set = field(default_factory=set)
    pages_by_title: dict = field(default_factory=dict)


# ── Canvas Connection ────────────────────────────────────────

def get_canvas():
    from canvasapi import Canvas
    url = get_env("CANVAS_API_URL")
    token = get_env("CANVAS_API_TOKEN")
    return Canvas(url, token)


# ── Data Pull ────────────────────────────────────────────────

def pull_course_data(canvas, course_id):
    """Pull all structural data for one course."""
    course = canvas.get_course(course_id, include=["total_students"])
    course_name = getattr(course, "name", f"Course {course_id}")

    assignments = list(course.get_assignments(include=["rubric"]))
    time.sleep(0.1)

    assignment_groups = list(course.get_assignment_groups())
    time.sleep(0.1)

    modules_with_items = []
    for m in course.get_modules():
        try:
            items = list(m.get_module_items())
        except Exception:
            items = []
        modules_with_items.append((m, items))
        time.sleep(0.1)

    try:
        pages = list(course.get_pages())
    except Exception:
        pages = []
    time.sleep(0.1)

    try:
        discussions = list(course.get_discussion_topics())
    except Exception:
        discussions = []

    data = CourseData(
        course_id=course_id,
        course_name=course_name,
        assignments=assignments,
        assignment_groups=assignment_groups,
        modules=modules_with_items,
        pages=pages,
        discussions=discussions,
    )

    # Build derived lookups
    for a in assignments:
        data.assignments_by_id[a.id] = a
        data.assignments_by_name[getattr(a, "name", "")] = a

    for _m, items in modules_with_items:
        for item in items:
            content_id = getattr(item, "content_id", None)
            if content_id:
                data.module_item_content_ids.add(content_id)
            title = getattr(item, "title", "")
            if title:
                data.module_item_titles.add(title)

    for p in pages:
        data.pages_by_title[getattr(p, "title", "")] = p

    return data


# ── Expert 1: Visibility ────────────────────────────────────

def visibility_expert(data):
    """Find hidden/unpublished content that students cannot see."""
    findings = []
    now = datetime.now(timezone.utc)

    # V1: Unpublished modules
    for m, items in data.modules:
        if not getattr(m, "published", True):
            findings.append(Finding(
                expert="visibility",
                severity=Severity.WARNING,
                title=f"Unpublished module: {getattr(m, 'name', '?')}",
                detail=f"Module '{getattr(m, 'name', '')}' with {len(items)} item(s) "
                       f"is not visible to students.",
                fix_suggestion="Publish the module if students should access it.",
            ))

    # V2: Published module containing unpublished assignments
    for m, items in data.modules:
        if not getattr(m, "published", False):
            continue
        for item in items:
            content_id = getattr(item, "content_id", None)
            item_type = getattr(item, "type", "")
            title = getattr(item, "title", "?")

            if item_type == "Assignment" and content_id in data.assignments_by_id:
                asgn = data.assignments_by_id[content_id]
                if not getattr(asgn, "published", True):
                    due_at = getattr(asgn, "due_at", None)
                    past_due = False
                    if due_at:
                        try:
                            due_dt = datetime.fromisoformat(
                                due_at.replace("Z", "+00:00"))
                            past_due = due_dt < now
                        except (ValueError, TypeError):
                            pass

                    sev = Severity.CRITICAL if past_due else Severity.WARNING
                    findings.append(Finding(
                        expert="visibility",
                        severity=sev,
                        title="Unpublished assignment in published module",
                        detail=f"'{title}' in module '{getattr(m, 'name', '')}' "
                               f"is unpublished"
                               + (" and PAST DUE" if past_due else "") + ".",
                        fix_suggestion="Publish this assignment so students can access it.",
                        auto_fixable=past_due,
                        fix_action=({"type": "publish_assignment",
                                     "assignment_id": asgn.id,
                                     "course_id": data.course_id}
                                    if past_due else {}),
                    ))

    # V3: Published module containing unpublished pages
    for m, items in data.modules:
        if not getattr(m, "published", False):
            continue
        for item in items:
            if getattr(item, "type", "") == "Page":
                title = getattr(item, "title", "")
                page = data.pages_by_title.get(title)
                if page and not getattr(page, "published", True):
                    page_url = getattr(page, "url", None)
                    findings.append(Finding(
                        expert="visibility",
                        severity=Severity.WARNING,
                        title="Unpublished page in published module",
                        detail=f"Page '{title}' in module "
                               f"'{getattr(m, 'name', '')}' is unpublished.",
                        fix_suggestion="Publish the page or remove from the module.",
                        auto_fixable=True,
                        fix_action={"type": "publish_page",
                                    "page_url": page_url,
                                    "page_title": title,
                                    "course_id": data.course_id},
                    ))

    # V4: Published module containing unpublished discussions
    discussions_by_id = {d.id: d for d in data.discussions}
    for m, items in data.modules:
        if not getattr(m, "published", False):
            continue
        for item in items:
            if getattr(item, "type", "") == "Discussion":
                content_id = getattr(item, "content_id", None)
                if content_id and content_id in discussions_by_id:
                    d = discussions_by_id[content_id]
                    if not getattr(d, "published", True):
                        findings.append(Finding(
                            expert="visibility",
                            severity=Severity.WARNING,
                            title="Unpublished discussion in published module",
                            detail=f"Discussion '{getattr(d, 'title', '?')}' in "
                                   f"module '{getattr(m, 'name', '')}' is unpublished.",
                            fix_suggestion="Publish the discussion or remove from module.",
                        ))

    # V5: Published assignment locked past due date
    for a in data.assignments:
        if not getattr(a, "published", False):
            continue
        unlock_at = getattr(a, "unlock_at", None)
        due_at = getattr(a, "due_at", None)
        if unlock_at and due_at:
            try:
                unlock_dt = datetime.fromisoformat(
                    unlock_at.replace("Z", "+00:00"))
                due_dt = datetime.fromisoformat(due_at.replace("Z", "+00:00"))
                if unlock_dt > now and due_dt < now:
                    findings.append(Finding(
                        expert="visibility",
                        severity=Severity.CRITICAL,
                        title=f"Assignment locked but past due: "
                              f"{getattr(a, 'name', '?')}",
                        detail=f"'{getattr(a, 'name', '')}' unlock date is "
                               f"{unlock_at} (future) but due date is "
                               f"{due_at} (past).",
                        fix_suggestion="Remove unlock date or extend due date.",
                    ))
            except (ValueError, TypeError):
                pass

    return findings


# ── Expert 2: Flow ───────────────────────────────────────────

def flow_expert(data):
    """Check module ordering, prerequisites, completion requirements."""
    findings = []
    published_modules = [(m, items) for m, items in data.modules
                         if getattr(m, "published", False)]

    # F1: Empty published modules
    for m, items in published_modules:
        if len(items) == 0:
            findings.append(Finding(
                expert="flow",
                severity=Severity.WARNING,
                title=f"Empty published module: {getattr(m, 'name', '?')}",
                detail=f"Module '{getattr(m, 'name', '')}' is published but "
                       f"has no items. Students see an empty section.",
                fix_suggestion="Add items to this module or unpublish it.",
            ))

    # F2: Modules without completion requirements
    for m, items in published_modules:
        if not items:
            continue
        has_any_req = any(
            getattr(item, "completion_requirement", None) for item in items
        )
        if not has_any_req:
            findings.append(Finding(
                expert="flow",
                severity=Severity.INFO,
                title=f"No completion requirements: {getattr(m, 'name', '?')}",
                detail=f"Module '{getattr(m, 'name', '')}' has {len(items)} "
                       f"item(s) but none have completion requirements.",
                fix_suggestion="Add completion requirements (must_submit, "
                               "min_score, etc.) to track student progress.",
            ))

    # F3: Broken prerequisite references
    module_ids = {m.id for m, _ in data.modules}
    published_ids = {m.id for m, _ in published_modules}
    for m, _items in data.modules:
        prereqs = getattr(m, "prerequisite_module_ids", []) or []
        for pid in prereqs:
            if pid not in module_ids:
                findings.append(Finding(
                    expert="flow",
                    severity=Severity.CRITICAL,
                    title="Broken prerequisite reference",
                    detail=f"Module '{getattr(m, 'name', '')}' requires "
                           f"module ID {pid} which does not exist.",
                    fix_suggestion="Remove the invalid prerequisite.",
                ))
            elif pid not in published_ids:
                findings.append(Finding(
                    expert="flow",
                    severity=Severity.WARNING,
                    title="Prerequisite module is unpublished",
                    detail=f"Module '{getattr(m, 'name', '')}' requires an "
                           f"unpublished module (ID: {pid}) as prerequisite.",
                    fix_suggestion="Publish the prerequisite or remove the req.",
                ))

    # F4: Sequential progress with items missing completion reqs
    for m, items in published_modules:
        if not getattr(m, "require_sequential_progress", False) or not items:
            continue
        missing = [getattr(item, "title", "?") for item in items
                   if not getattr(item, "completion_requirement", None)]
        if missing:
            preview = ", ".join(missing[:3])
            if len(missing) > 3:
                preview += f" (+{len(missing) - 3} more)"
            findings.append(Finding(
                expert="flow",
                severity=Severity.WARNING,
                title=f"Sequential module with unrequired items: "
                      f"{getattr(m, 'name', '?')}",
                detail=f"Module '{getattr(m, 'name', '')}' requires sequential "
                       f"progress but {len(missing)} item(s) have no completion "
                       f"requirement: {preview}",
                fix_suggestion="Add completion requirements to all items in "
                               "sequential modules.",
            ))

    # F5: Orphaned assignments (published but not in any module)
    # Note: Quiz-type module items have content_id = quiz_id (not assignment_id),
    # so we also check by title to catch quizzes linked via their quiz ID.
    for a in data.assignments:
        if not getattr(a, "published", False):
            continue
        name = getattr(a, "name", "")
        in_module_by_id = a.id in data.module_item_content_ids
        in_module_by_title = name in data.module_item_titles
        if not in_module_by_id and not in_module_by_title:
            findings.append(Finding(
                expert="flow",
                severity=Severity.WARNING,
                title=f"Orphaned assignment: {name or '?'}",
                detail=f"Published assignment '{name}' is not "
                       f"in any module. Students may not discover it.",
                fix_suggestion="Add this assignment to the appropriate module.",
            ))

    return findings


# ── Expert 3: Instructional Design ───────────────────────────

def design_expert(data):
    """Low-hanging improvements: dates, points, rubrics, groups."""
    findings = []

    # D1: Published assignments missing due dates
    for a in data.assignments:
        if not getattr(a, "published", False):
            continue
        sub_types = getattr(a, "submission_types", []) or []
        if "none" in sub_types or "not_graded" in sub_types:
            continue
        if not getattr(a, "due_at", None):
            points = getattr(a, "points_possible", 0) or 0
            findings.append(Finding(
                expert="design",
                severity=Severity.WARNING,
                title=f"No due date: {getattr(a, 'name', '?')}",
                detail=f"Published assignment '{getattr(a, 'name', '')}' "
                       f"({points} pts) has no due date.",
                fix_suggestion="Set a due date so students have clear deadlines.",
            ))

    # D2: Graded assignments with 0 points
    for a in data.assignments:
        if not getattr(a, "published", False):
            continue
        points = getattr(a, "points_possible", None)
        grading_type = getattr(a, "grading_type", "")
        if grading_type in ("not_graded", "pass_fail"):
            continue
        if points is not None and points == 0:
            findings.append(Finding(
                expert="design",
                severity=Severity.WARNING,
                title=f"Zero points: {getattr(a, 'name', '?')}",
                detail=f"Assignment '{getattr(a, 'name', '')}' has 0 points "
                       f"possible but is graded ({grading_type}).",
                fix_suggestion="Set appropriate point value or change to "
                               "not_graded.",
            ))

    # D3: Major assignments (>=20 pts, file upload) without rubrics
    for a in data.assignments:
        if not getattr(a, "published", False):
            continue
        points = getattr(a, "points_possible", 0) or 0
        sub_types = getattr(a, "submission_types", []) or []
        has_rubric = getattr(a, "rubric", None)
        has_upload = any(t in sub_types
                         for t in ("online_upload", "online_text_entry"))
        if points >= 20 and has_upload and not has_rubric:
            findings.append(Finding(
                expert="design",
                severity=Severity.INFO,
                title=f"No rubric on major assignment: {getattr(a, 'name', '?')}",
                detail=f"'{getattr(a, 'name', '')}' is worth {points} pts with "
                       f"file submission but has no rubric attached.",
                fix_suggestion="Create and attach a rubric for consistent grading.",
            ))

    # D4: Assignments in "Imported Assignments" group
    imported_group_id = None
    for g in data.assignment_groups:
        if "imported" in getattr(g, "name", "").lower():
            imported_group_id = g.id
            break

    if imported_group_id:
        imports = [a for a in data.assignments
                   if getattr(a, "assignment_group_id", None) == imported_group_id
                   and getattr(a, "published", False)]
        if imports:
            names = [getattr(a, "name", "?") for a in imports]
            preview = ", ".join(names[:5])
            if len(names) > 5:
                preview += f" (+{len(names) - 5} more)"
            findings.append(Finding(
                expert="design",
                severity=Severity.WARNING,
                title=f"{len(imports)} assignment(s) in 'Imported Assignments'",
                detail=f"These published assignments are in the default import "
                       f"group: {preview}",
                fix_suggestion="Move these to the correct assignment group.",
            ))

    # D5: 0% weight group with graded work
    for g in data.assignment_groups:
        weight = getattr(g, "group_weight", 0) or 0
        gname = getattr(g, "name", "")
        if weight == 0:
            graded = [a for a in data.assignments
                      if getattr(a, "assignment_group_id", None) == g.id
                      and getattr(a, "published", False)
                      and (getattr(a, "points_possible", 0) or 0) > 0]
            if graded:
                total_pts = sum(
                    getattr(a, "points_possible", 0) or 0 for a in graded)
                findings.append(Finding(
                    expert="design",
                    severity=Severity.CRITICAL,
                    title=f"0% weight group with graded work: {gname}",
                    detail=f"Group '{gname}' has 0% weight but contains "
                           f"{len(graded)} graded assignment(s) worth "
                           f"{total_pts} total pts. This work does not count "
                           f"toward the final grade.",
                    fix_suggestion="Set an appropriate weight for this group or "
                                   "move assignments to a weighted group.",
                ))

    return findings


# ── Expert 4: Technical ──────────────────────────────────────

def technical_expert(data):
    """Weight totals, broken references, duplicates, structural integrity."""
    findings = []

    # T1: Assignment group weights don't sum to 100%
    total_weight = sum(
        getattr(g, "group_weight", 0) or 0 for g in data.assignment_groups)
    if abs(total_weight - 100) > 0.01 and total_weight > 0:
        detail_parts = [f"{getattr(g, 'name', '?')}: "
                        f"{getattr(g, 'group_weight', 0)}%"
                        for g in data.assignment_groups]
        findings.append(Finding(
            expert="technical",
            severity=Severity.CRITICAL,
            title=f"Group weights sum to {total_weight}% (not 100%)",
            detail=f"Groups: {', '.join(detail_parts)}.",
            fix_suggestion=f"Adjust weights to sum to 100%. "
                           f"Currently off by {total_weight - 100:+.1f}%.",
        ))

    # T2: Duplicate items across modules (or within the same module)
    seen_items = {}  # (type, content_id) -> module_name
    for m, items in data.modules:
        mname = getattr(m, "name", "?")
        for item in items:
            content_id = getattr(item, "content_id", None)
            item_type = getattr(item, "type", "")
            title = getattr(item, "title", "?")
            if content_id:
                key = (item_type, content_id)
                if key in seen_items:
                    prev_module = seen_items[key]
                    if prev_module == mname:
                        detail = (f"'{title}' ({item_type}) appears "
                                  f"twice in '{mname}'.")
                    else:
                        detail = (f"'{title}' ({item_type}) appears in "
                                  f"both '{prev_module}' and '{mname}'.")
                    findings.append(Finding(
                        expert="technical",
                        severity=Severity.WARNING,
                        title=f"Duplicate item: {title}",
                        detail=detail,
                        fix_suggestion="Remove the duplicate.",
                    ))
                else:
                    seen_items[key] = mname

    # T3: Module items referencing deleted content
    for m, items in data.modules:
        mname = getattr(m, "name", "?")
        for item in items:
            content_id = getattr(item, "content_id", None)
            item_type = getattr(item, "type", "")
            title = getattr(item, "title", "?")

            if item_type == "Assignment" and content_id:
                if content_id not in data.assignments_by_id:
                    findings.append(Finding(
                        expert="technical",
                        severity=Severity.CRITICAL,
                        title=f"Broken reference: {title}",
                        detail=f"Module '{mname}' references assignment ID "
                               f"{content_id} ('{title}') which does not exist.",
                        fix_suggestion="Remove this item from the module.",
                    ))

            if item_type == "Page" and title:
                if title not in data.pages_by_title:
                    found = any(getattr(p, "page_id", None) == content_id
                                for p in data.pages)
                    if not found:
                        findings.append(Finding(
                            expert="technical",
                            severity=Severity.WARNING,
                            title=f"Possibly broken page ref: {title}",
                            detail=f"Module '{mname}' references page "
                                   f"'{title}' which was not found.",
                            fix_suggestion="Verify this page exists or remove "
                                           "from module.",
                        ))

    # T4: Graded assignment with no submission type
    for a in data.assignments:
        if not getattr(a, "published", False):
            continue
        sub_types = getattr(a, "submission_types", []) or []
        points = getattr(a, "points_possible", 0) or 0
        name = getattr(a, "name", "?")
        if points > 0 and ("none" in sub_types or not sub_types):
            findings.append(Finding(
                expert="technical",
                severity=Severity.WARNING,
                title=f"Graded but no submission type: {name}",
                detail=f"'{name}' is worth {points} pts but "
                       f"submission_types={sub_types}. Students cannot submit.",
                fix_suggestion="Set a submission type or change to not_graded.",
            ))

    # T5: Weighted group with zero assignments
    for g in data.assignment_groups:
        gname = getattr(g, "name", "")
        weight = getattr(g, "group_weight", 0) or 0
        in_group = [a for a in data.assignments
                    if getattr(a, "assignment_group_id", None) == g.id]
        if not in_group and weight > 0:
            findings.append(Finding(
                expert="technical",
                severity=Severity.WARNING,
                title=f"Weighted group with no assignments: {gname}",
                detail=f"Group '{gname}' has {weight}% weight but contains "
                       f"no assignments.",
                fix_suggestion="Add assignments or set weight to 0%.",
            ))

    return findings


# ── Report Formatting ────────────────────────────────────────

def print_report(all_findings):
    """Print color-coded terminal report."""
    print()
    print(f"{BOLD}{'=' * 65}{RESET}")
    print(f"{BOLD}  CANVAS COURSE FLOW CHECK -- PANEL OF EXPERTS{RESET}")
    print(f"  Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")
    print(f"{'=' * 65}")

    grand_counts = {Severity.CRITICAL: 0, Severity.WARNING: 0, Severity.INFO: 0}
    grand_fixable = 0
    issue_counter = {}  # title -> count across courses

    for course_id, (course_name, findings) in all_findings.items():
        print(f"\n{BOLD}{'=' * 65}{RESET}")
        print(f"{BOLD}  {course_name} (ID: {course_id}){RESET}")
        print(f"{'=' * 65}")

        counts = {Severity.CRITICAL: 0, Severity.WARNING: 0, Severity.INFO: 0}
        fixable = 0

        # Group by expert
        by_expert = {}
        for f in findings:
            by_expert.setdefault(f.expert, []).append(f)

        for expert_key in ("visibility", "flow", "design", "technical"):
            expert_findings = by_expert.get(expert_key, [])
            label = EXPERT_LABELS[expert_key]
            print(f"\n  {DIM}--- {label} ---{RESET}")

            if not expert_findings:
                print(f"  {GREEN}  No issues found.{RESET}")
                continue

            for f in expert_findings:
                color = SEVERITY_COLORS[f.severity]
                counts[f.severity] += 1
                grand_counts[f.severity] += 1
                if f.auto_fixable:
                    fixable += 1
                    grand_fixable += 1

                # Track for grand summary
                issue_counter[f.title] = issue_counter.get(f.title, 0) + 1

                print(f"  {color}[{f.severity.value}]{RESET} {f.title}")
                print(f"    {f.detail}")
                print(f"    {DIM}Fix: {f.fix_suggestion}{RESET}")

        # Per-course summary
        print(f"\n  {'─' * 61}")
        crit = counts[Severity.CRITICAL]
        warn = counts[Severity.WARNING]
        info = counts[Severity.INFO]
        print(f"  Summary: "
              f"{RED}CRITICAL: {crit}{RESET}  "
              f"{YELLOW}WARNING: {warn}{RESET}  "
              f"{CYAN}INFO: {info}{RESET}")
        if fixable:
            print(f"  Auto-fixable: {fixable} (use --fix to apply)")

    # Grand summary
    total = sum(grand_counts.values())
    print(f"\n{BOLD}{'=' * 65}{RESET}")
    print(f"{BOLD}  GRAND SUMMARY ({len(all_findings)} course(s)){RESET}")
    print(f"{'=' * 65}")
    print(f"  Total findings: {total}")
    print(f"    {RED}CRITICAL: {grand_counts[Severity.CRITICAL]}{RESET}  "
          f"{YELLOW}WARNING: {grand_counts[Severity.WARNING]}{RESET}  "
          f"{CYAN}INFO: {grand_counts[Severity.INFO]}{RESET}")

    if issue_counter:
        print(f"\n  Most common issues:")
        sorted_issues = sorted(issue_counter.items(), key=lambda x: -x[1])
        for i, (title, count) in enumerate(sorted_issues[:5], 1):
            print(f"    {i}. {title} ({count}x across courses)")

    if grand_fixable:
        print(f"\n  {GREEN}Auto-fixable: {grand_fixable}{RESET}")
    print(f"{'=' * 65}\n")


def save_markdown(all_findings, output_dir=None):
    """Save report as markdown file."""
    output_dir = output_dir or os.path.expanduser("~/Downloads")
    filename = f"flow_check_{datetime.now().strftime('%Y-%m-%d')}.md"
    path = os.path.join(output_dir, filename)

    lines = []
    lines.append("# Canvas Course Flow Check -- Panel of Experts")
    lines.append(f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")
    lines.append("")

    grand_counts = {Severity.CRITICAL: 0, Severity.WARNING: 0, Severity.INFO: 0}

    for course_id, (course_name, findings) in all_findings.items():
        lines.append(f"## {course_name} (ID: {course_id})")
        lines.append("")

        by_expert = {}
        for f in findings:
            by_expert.setdefault(f.expert, []).append(f)

        for expert_key in ("visibility", "flow", "design", "technical"):
            expert_findings = by_expert.get(expert_key, [])
            label = EXPERT_LABELS[expert_key]
            lines.append(f"### {label}")
            lines.append("")

            if not expert_findings:
                lines.append("No issues found.")
                lines.append("")
                continue

            for f in expert_findings:
                grand_counts[f.severity] += 1
                fix_tag = " (auto-fixable)" if f.auto_fixable else ""
                lines.append(f"- **[{f.severity.value}]** {f.title}{fix_tag}")
                lines.append(f"  - {f.detail}")
                lines.append(f"  - Fix: {f.fix_suggestion}")

            lines.append("")

        lines.append("---")
        lines.append("")

    # Grand summary
    total = sum(grand_counts.values())
    lines.append("## Grand Summary")
    lines.append("")
    lines.append(f"- Total findings: {total}")
    lines.append(f"- CRITICAL: {grand_counts[Severity.CRITICAL]}")
    lines.append(f"- WARNING: {grand_counts[Severity.WARNING]}")
    lines.append(f"- INFO: {grand_counts[Severity.INFO]}")

    with open(path, "w") as fh:
        fh.write("\n".join(lines) + "\n")

    print(f"  Markdown report saved: {path}")
    return path


# ── Auto-Fix ─────────────────────────────────────────────────

def apply_fixes(all_findings, canvas):
    """Apply auto-fixable findings with confirmation."""
    fixable = []
    for _cid, (_cname, findings) in all_findings.items():
        for f in findings:
            if f.auto_fixable:
                fixable.append(f)

    if not fixable:
        print(f"\n  {GREEN}No auto-fixable issues found.{RESET}")
        return

    print(f"\n{'=' * 65}")
    print(f"  AUTO-FIX: {len(fixable)} issue(s) can be fixed")
    print(f"{'=' * 65}")

    for f in fixable:
        color = SEVERITY_COLORS[f.severity]
        print(f"  {color}[{f.severity.value}]{RESET} {f.title}")
        print(f"    {f.detail}")
        print(f"    Would: {f.fix_suggestion}")

    print(f"\n  Apply all {len(fixable)} fixes? [y/N] ", end="", flush=True)
    confirm = input().strip().lower()
    if confirm != "y":
        print("  Aborted. No changes made.")
        return

    fixed = 0
    failed = 0
    for f in fixable:
        action = f.fix_action
        try:
            if action.get("type") == "publish_assignment":
                course = canvas.get_course(action["course_id"])
                asgn = course.get_assignment(action["assignment_id"])
                asgn.edit(assignment={"published": True})
                print(f"  {GREEN}FIXED:{RESET} Published "
                      f"'{getattr(asgn, 'name', '?')}'")
                fixed += 1
            elif action.get("type") == "publish_page":
                course = canvas.get_course(action["course_id"])
                page = course.get_page(action["page_url"])
                page.edit(wiki_page={"published": True})
                print(f"  {GREEN}FIXED:{RESET} Published page "
                      f"'{action.get('page_title', '?')}'")
                fixed += 1
            time.sleep(0.1)
        except Exception as e:
            print(f"  {RED}FAILED:{RESET} {f.title} -- {e}")
            failed += 1

    print(f"\n  Done: {fixed} fixed, {failed} failed.")


# ── Main ─────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Canvas Course Flow Checker -- Panel of Experts")

    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true",
                      help="Analyze and report only (no changes)")
    mode.add_argument("--fix", action="store_true",
                      help="Analyze, report, then auto-fix safe issues")

    parser.add_argument("--course-id", type=int, action="append", default=None,
                        help="Specific course ID(s) to check (repeatable)")
    parser.add_argument("--metals", action="store_true",
                        help="Check metals courses only")
    parser.add_argument("--engines", action="store_true",
                        help="Check engines/fab courses only")
    parser.add_argument("--markdown", action="store_true",
                        help="Save markdown report to ~/Downloads/")
    parser.add_argument("--output", type=str, default=None,
                        help="Custom output directory for markdown report")

    args = parser.parse_args()

    # Determine course list
    if args.course_id:
        course_ids = args.course_id
    elif args.metals:
        course_ids = METALS_IDS
    elif args.engines:
        course_ids = ENGINES_IDS
    else:
        course_ids = ALL_IDS

    canvas = get_canvas()

    # all_findings: {course_id: (course_name, [Finding, ...])}
    all_findings = {}

    for cid in course_ids:
        print(f"\n  Pulling data for course {cid}...", flush=True)
        try:
            data = pull_course_data(canvas, cid)
        except Exception as e:
            print(f"  {RED}ERROR pulling course {cid}: {e}{RESET}",
                  file=sys.stderr)
            continue

        print(f"  Analyzing {data.course_name}...", flush=True)
        findings = []
        findings += visibility_expert(data)
        findings += flow_expert(data)
        findings += design_expert(data)
        findings += technical_expert(data)

        all_findings[cid] = (data.course_name, findings)

    # Output
    print_report(all_findings)

    if args.markdown:
        save_markdown(all_findings, args.output)

    if args.fix:
        apply_fixes(all_findings, canvas)


if __name__ == "__main__":
    main()
