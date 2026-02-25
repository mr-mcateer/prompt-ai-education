#!/usr/bin/env python3
"""
Canvas Daily Briefing Generator
================================
Pulls live data from all Canvas courses and generates a daily briefing
with grade distributions, at-risk students, upcoming deadlines, suggested
agendas, and a full roster snapshot.

Usage:
    python3 tools/canvas_daily_briefing.py                  # Tomorrow's briefing
    python3 tools/canvas_daily_briefing.py --date 2026-03-03  # Specific date
    python3 tools/canvas_daily_briefing.py --output ~/Desktop  # Custom output dir

Output:
    Writes markdown briefing to ~/Downloads/daily_briefing_YYYY-MM-DD.md
    Also prints full briefing to terminal.

Architecture:
    1. DATA PULL   -- Paginated Canvas REST API calls for enrollments,
                      assignments, and submissions across all courses
    2. ANALYSIS    -- Per-course grade distribution, missing work detection,
                      at-risk/high-performer identification
    3. BRIEFING    -- Markdown report with agendas, insights, roster tables
    4. SAVE        -- Write to file + terminal output

Refinement Notes:
    - "Missing" = past-due + no submission + not excused
    - At-risk threshold: 3+ missing OR current_score < 60%
    - High performer threshold: current_score >= 90%
    - Shop Cleanup assignments are recurring weekly -- expect high missing
      counts if students forget to check in
    - Engines/Fab courses have portfolio assignments that are cumulative
    - Metal Types Quiz and Plasma Lab are key Module 3 deliverables
    - The S1 Credit assignments (safety certs) should mostly be done by now

Future Improvements:
    - Add trend analysis (compare to last week's pull)
    - Add Synergy/SIS attendance data correlation
    - Add parent email draft for at-risk students
    - Add weekly summary mode (--weekly)
    - Filter out Test Student from rosters automatically
"""

import argparse
import json
import os
import sys
import time
from collections import defaultdict
from datetime import datetime, date, timedelta

# Project imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from tools.env_loader import get_env

import requests

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

TOKEN = get_env("CANVAS_API_TOKEN")
URL = get_env("CANVAS_API_URL").rstrip("/")
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

# Course groupings
METALS_IDS = [23164, 23132, 23157, 23188, 23177]
ENGINES_IDS = [23124, 23344]
ALL_IDS = METALS_IDS + ENGINES_IDS

# Course metadata for agenda context (update each semester)
COURSE_CONTEXT = {
    "metals": {
        "period": "Periods 3 & 5",
        "current_module": "Module 3",
        "current_focus": "Handrail plaque project, plasma cutting lab",
        "upcoming": "Metal Entrepreneur Challenge due Friday",
        "bell_work": "Metal types review -- name 3 ferrous metals and 3 non-ferrous metals",
        "safety_note": "Review plasma cutter PPE requirements before lab",
    },
    "engines": {
        "period": "Period 1",
        "current_module": "Module 2 wrap-up, Module 3 starts March 2",
        "current_focus": "Engine reassembly completion",
        "upcoming": "Oil change and brake labs next week",
        "bell_work": "Quick review question on engine parts from last week's teardown/reassembly",
        "safety_note": None,
    },
}

# Thresholds
AT_RISK_MISSING = 3       # Missing assignment count to flag
AT_RISK_SCORE = 60.0      # Score below this = at-risk
HIGH_PERFORMER_SCORE = 90.0


# ---------------------------------------------------------------------------
# Canvas API helper
# ---------------------------------------------------------------------------

def api_get(endpoint, params=None):
    """Paginated GET from Canvas REST API."""
    results = []
    url = f"{URL}/api/v1{endpoint}"
    p = params or {}
    p["per_page"] = 100
    while url:
        r = requests.get(url, headers=HEADERS, params=p)
        if r.status_code != 200:
            print(f"  WARN: {r.status_code} on {endpoint}", file=sys.stderr)
            break
        data = r.json()
        if isinstance(data, list):
            results.extend(data)
        else:
            return data
        url = r.links.get("next", {}).get("url")
        p = {}  # params only on first request
        time.sleep(0.1)
    return results


# ---------------------------------------------------------------------------
# Data pull
# ---------------------------------------------------------------------------

def pull_course(cid):
    """Pull enrollments, assignments, and submissions for one course."""
    info = api_get(f"/courses/{cid}")
    course_name = info.get("name", f"Course {cid}") if isinstance(info, dict) else f"Course {cid}"

    # Active student enrollments
    enrollments = api_get(f"/courses/{cid}/enrollments",
                          {"type[]": "StudentEnrollment", "state[]": "active"})
    students = []
    for e in enrollments:
        u = e.get("user", {})
        students.append({
            "id": u.get("id"),
            "name": u.get("sortable_name", u.get("name", "Unknown")),
            "current_score": e.get("grades", {}).get("current_score"),
            "current_grade": e.get("grades", {}).get("current_grade"),
            "final_score": e.get("grades", {}).get("final_score"),
        })

    # Assignments (ordered by position)
    assignments = api_get(f"/courses/{cid}/assignments", {"order_by": "position"})
    asgn_list = []
    for a in assignments:
        asgn_list.append({
            "id": a.get("id"),
            "name": a.get("name"),
            "due_at": a.get("due_at"),
            "points_possible": a.get("points_possible"),
            "published": a.get("published"),
            "submission_types": a.get("submission_types"),
            "has_submitted_submissions": a.get("has_submitted_submissions"),
            "grading_type": a.get("grading_type"),
        })

    # Submissions for published assignments
    submissions = []
    pub_asgns = [a for a in asgn_list if a.get("published")]
    for a in pub_asgns:
        subs = api_get(f"/courses/{cid}/assignments/{a['id']}/submissions")
        for s in subs:
            submissions.append({
                "assignment_id": a["id"],
                "assignment_name": a["name"],
                "user_id": s.get("user_id"),
                "workflow_state": s.get("workflow_state"),
                "submitted_at": s.get("submitted_at"),
                "score": s.get("score"),
                "grade": s.get("grade"),
                "late": s.get("late"),
                "missing": s.get("missing"),
                "excused": s.get("excused"),
                "points_possible": a["points_possible"],
            })

    return {
        "course_id": cid,
        "course_name": course_name,
        "students": students,
        "assignments": asgn_list,
        "submissions": submissions,
    }


def pull_all_courses():
    """Pull data from every configured course. Returns dict."""
    print("=== Canvas Daily Briefing Data Pull ===", file=sys.stderr)
    all_data = {"pulled_at": datetime.now().isoformat(), "courses": {}}

    for cid in ALL_IDS:
        print(f"  Pulling course {cid}...", file=sys.stderr)
        try:
            all_data["courses"][str(cid)] = pull_course(cid)
        except Exception as e:
            print(f"    ERROR: {e}", file=sys.stderr)
            all_data["courses"][str(cid)] = {"error": str(e)}

    return all_data


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------

def parse_date(s):
    """Parse ISO date string to date object."""
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).date()
    except Exception:
        return None


def analyze_course(cdata, today):
    """Analyze a single course. Returns structured insights or None if empty."""
    students = {s["id"]: s for s in cdata.get("students", [])}
    assignments = cdata.get("assignments", [])
    submissions = cdata.get("submissions", [])

    if not students:
        return None

    pub_asgns = [a for a in assignments if a.get("published")]

    # Due this week (Mon-Sat of target week)
    # Find the Monday of the target week
    days_since_monday = today.weekday()
    week_start = today - timedelta(days=days_since_monday)
    week_end = week_start + timedelta(days=5)  # Saturday

    due_this_week = [a for a in pub_asgns
                     if parse_date(a.get("due_at")) and week_start <= parse_date(a["due_at"]) <= week_end]

    # Due next week
    next_start = week_end + timedelta(days=2)  # next Monday
    next_end = next_start + timedelta(days=5)
    due_next_week = [a for a in pub_asgns
                     if parse_date(a.get("due_at")) and next_start <= parse_date(a["due_at"]) <= next_end]

    # Student submission analysis
    student_stats = {}
    for sid, sinfo in students.items():
        student_stats[sid] = {
            "name": sinfo["name"],
            "current_score": sinfo.get("current_score"),
            "current_grade": sinfo.get("current_grade"),
            "submitted": 0,
            "missing": 0,
            "late": 0,
            "graded": 0,
            "ungraded": 0,
            "missing_assignments": [],
        }

    for sub in submissions:
        uid = sub.get("user_id")
        if uid not in student_stats:
            continue
        st = student_stats[uid]

        ws = sub.get("workflow_state", "")
        if ws == "unsubmitted" or (not sub.get("submitted_at") and not sub.get("excused")):
            # Only count as missing if past due
            asgn_match = [a for a in pub_asgns if a["id"] == sub["assignment_id"]]
            if asgn_match:
                d = parse_date(asgn_match[0].get("due_at"))
                if d and d < today:
                    st["missing"] += 1
                    st["missing_assignments"].append(sub["assignment_name"])
        elif sub.get("excused"):
            pass
        else:
            st["submitted"] += 1
            if sub.get("late"):
                st["late"] += 1
            if sub.get("score") is not None:
                st["graded"] += 1
            else:
                st["ungraded"] += 1

    # Ungraded submissions (teacher action items)
    ungraded_subs = [
        sub for sub in submissions
        if sub.get("user_id") in student_stats
        and sub.get("submitted_at")
        and sub.get("score") is None
        and not sub.get("excused")
    ]

    # Classify students
    at_risk = [st for st in student_stats.values()
               if st["missing"] >= AT_RISK_MISSING
               or (st["current_score"] is not None and st["current_score"] < AT_RISK_SCORE)]
    at_risk.sort(key=lambda x: x["missing"], reverse=True)

    high_perf = [st for st in student_stats.values()
                 if st["current_score"] is not None and st["current_score"] >= HIGH_PERFORMER_SCORE]
    high_perf.sort(key=lambda x: x["current_score"] or 0, reverse=True)

    return {
        "course_name": cdata["course_name"],
        "student_count": len(students),
        "assignment_count": len(pub_asgns),
        "due_this_week": due_this_week,
        "due_next_week": due_next_week,
        "student_stats": student_stats,
        "at_risk": at_risk,
        "high_performers": high_perf,
        "needs_grading": len(ungraded_subs),
        "ungraded_details": ungraded_subs[:20],
    }


def grade_distribution(stats):
    """Return letter grade counts from student stats dict."""
    dist = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0, "N/A": 0}
    for st in stats.values():
        s = st["current_score"]
        if s is None:
            dist["N/A"] += 1
        elif s >= 90:
            dist["A"] += 1
        elif s >= 80:
            dist["B"] += 1
        elif s >= 70:
            dist["C"] += 1
        elif s >= 60:
            dist["D"] += 1
        else:
            dist["F"] += 1
    return dist


# ---------------------------------------------------------------------------
# Briefing builder
# ---------------------------------------------------------------------------

def build_briefing(data, target_date):
    """Build the full markdown briefing."""
    today = target_date
    day_name = today.strftime("%A")
    date_str = today.strftime("%B %d, %Y")

    lines = []
    lines.append(f"# Daily Briefing -- {day_name}, {date_str}")
    lines.append(f"*Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} | Data as of {data['pulled_at'][:16]}*\n")
    lines.append("---\n")

    # ===== AT A GLANCE =====
    lines.append("## At a Glance\n")

    total_students = 0
    total_ungraded = 0
    total_at_risk = 0
    all_analyses = {}

    for cid_str, cdata in data["courses"].items():
        if "error" in cdata or not cdata.get("students"):
            continue
        a = analyze_course(cdata, today)
        if a:
            all_analyses[cid_str] = a
            total_students += a["student_count"]
            total_ungraded += a["needs_grading"]
            total_at_risk += len(a["at_risk"])

    lines.append("| Metric | Count |")
    lines.append("|--------|-------|")
    lines.append(f"| Active Students | {total_students} |")
    lines.append(f"| Submissions Needing Grading | {total_ungraded} |")
    lines.append(f"| At-Risk Students (3+ missing or <60%) | {total_at_risk} |")
    lines.append("")

    # ===== ENGINES/FAB =====
    lines.append("---\n")
    ctx = COURSE_CONTEXT["engines"]
    lines.append(f"## {ctx['period']}: Engines & Fabrication\n")

    for cid in ENGINES_IDS:
        a = all_analyses.get(str(cid))
        if not a:
            continue
        _render_course_section(lines, str(cid), a, today)

    _render_agenda(lines, "engines", all_analyses, ENGINES_IDS)

    # ===== METALS =====
    lines.append("---\n")
    ctx = COURSE_CONTEXT["metals"]
    lines.append(f"## {ctx['period']}: Metals\n")

    for cid in METALS_IDS:
        a = all_analyses.get(str(cid))
        if not a:
            continue
        _render_course_section(lines, str(cid), a, today)

    _render_agenda(lines, "metals", all_analyses, METALS_IDS)

    # ===== INSIGHTS =====
    lines.append("---\n")
    lines.append("## Insights & Reminders\n")

    if total_ungraded > 0:
        lines.append(f"- **Grading backlog:** {total_ungraded} submissions across all courses need grading")

    all_at_risk_names = set()
    for a in all_analyses.values():
        for st in a["at_risk"]:
            all_at_risk_names.add(st["name"])
    if all_at_risk_names:
        lines.append(f"- **Unique at-risk students across all sections:** {len(all_at_risk_names)}")

    lines.append("- **Exemplar portfolios** are live on Canvas for all Engines/Fab assignments")
    lines.append("- Check district calendar for any schedule changes this week")
    lines.append("")

    # ===== FULL ROSTER =====
    lines.append("---\n")
    lines.append("## Full Roster Snapshot\n")

    for group_name, group_ids in [("Engines & Fab", ENGINES_IDS), ("Metals", METALS_IDS)]:
        lines.append(f"### {group_name}\n")
        for cid in group_ids:
            a = all_analyses.get(str(cid))
            if not a:
                continue
            lines.append(f"**{a['course_name']}**\n")
            lines.append("| Student | Score | Missing | Late | Status |")
            lines.append("|---------|-------|---------|------|--------|")
            for sid, st in sorted(a["student_stats"].items(), key=lambda x: x[1]["name"]):
                score = f"{st['current_score']:.0f}%" if st['current_score'] is not None else "--"
                if st["missing"] >= AT_RISK_MISSING or (st["current_score"] is not None and st["current_score"] < AT_RISK_SCORE):
                    status = "AT RISK"
                elif st["current_score"] is not None and st["current_score"] >= HIGH_PERFORMER_SCORE:
                    status = "Strong"
                elif st["missing"] > 0:
                    status = "Watch"
                else:
                    status = "OK"
                lines.append(f"| {st['name']} | {score} | {st['missing']} | {st['late']} | {status} |")
            lines.append("")

    lines.append("---\n")
    lines.append("*End of briefing. Generated by `tools/canvas_daily_briefing.py`*")
    return "\n".join(lines)


def _render_course_section(lines, cid, a, today):
    """Render a single course's detail section."""
    lines.append(f"### {a['course_name']} (ID: {cid})")
    lines.append(f"**Students:** {a['student_count']} | **Assignments:** {a['assignment_count']} | **Needs Grading:** {a['needs_grading']}\n")

    dist = grade_distribution(a["student_stats"])
    lines.append(f"**Grade Distribution:** A:{dist['A']} B:{dist['B']} C:{dist['C']} D:{dist['D']} F:{dist['F']}\n")

    if a["due_this_week"]:
        lines.append("**Due This Week:**")
        for asgn in a["due_this_week"]:
            d = parse_date(asgn.get("due_at"))
            lines.append(f"- {asgn['name']} ({asgn['points_possible']} pts) -- due {d.strftime('%a %m/%d') if d else 'TBD'}")
        lines.append("")

    if a["due_next_week"]:
        lines.append("**Coming Next Week:**")
        for asgn in a["due_next_week"]:
            d = parse_date(asgn.get("due_at"))
            lines.append(f"- {asgn['name']} ({asgn['points_possible']} pts) -- due {d.strftime('%a %m/%d') if d else 'TBD'}")
        lines.append("")

    if a["at_risk"]:
        lines.append("**At-Risk Students:**")
        for st in a["at_risk"]:
            score_str = f"{st['current_score']:.0f}%" if st['current_score'] is not None else "N/A"
            lines.append(f"- **{st['name']}** -- Score: {score_str}, Missing: {st['missing']}")
            for ma in st["missing_assignments"][:5]:
                lines.append(f"  - {ma}")
        lines.append("")

    if a["high_performers"]:
        lines.append("**High Performers:**")
        for st in a["high_performers"]:
            lines.append(f"- {st['name']} -- {st['current_score']:.0f}%")
        lines.append("")

    if a["needs_grading"] > 0:
        lines.append(f"**Ungraded Submissions ({a['needs_grading']}):**")
        ungraded_by_asgn = defaultdict(int)
        for ug in a["ungraded_details"]:
            ungraded_by_asgn[ug["assignment_name"]] += 1
        for aname, count in ungraded_by_asgn.items():
            lines.append(f"- {aname}: {count} submission(s)")
        lines.append("")


def _render_agenda(lines, group_key, all_analyses, course_ids):
    """Render suggested agenda for a course group."""
    ctx = COURSE_CONTEXT[group_key]
    lines.append(f"### Suggested Agenda -- {ctx['period']}\n")
    lines.append(f"*Context: {ctx['current_module']}. {ctx['current_focus']}.*\n")
    lines.append(f"- **Bell work:** {ctx['bell_work']}")
    if ctx.get("upcoming"):
        lines.append(f"- **Reminder:** {ctx['upcoming']}")
    lines.append(f"- **Main activity:** {ctx['current_focus']}")
    if ctx.get("safety_note"):
        lines.append(f"- **Safety check:** {ctx['safety_note']}")
    lines.append("- **Close-out:** Cleanup, check Canvas for missing work")

    # Dynamic teacher notes based on data
    for cid in course_ids:
        a = all_analyses.get(str(cid))
        if not a:
            continue
        if a["needs_grading"] > 5:
            lines.append(f"- **Teacher note:** {a['needs_grading']} submissions need grading in {a['course_name']}")
        if a["at_risk"]:
            names = [s["name"].split(",")[0] for s in a["at_risk"][:3]]
            lines.append(f"- **Check in with:** {', '.join(names)} (falling behind)")
    lines.append("")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Canvas Daily Briefing Generator")
    parser.add_argument("--date", type=str, default=None,
                        help="Target date YYYY-MM-DD (default: tomorrow)")
    parser.add_argument("--output", type=str, default=None,
                        help="Output directory (default: ~/Downloads)")
    parser.add_argument("--cached", type=str, default=None,
                        help="Use cached JSON data file instead of pulling live")
    args = parser.parse_args()

    # Determine target date
    if args.date:
        target_date = date.fromisoformat(args.date)
    else:
        target_date = date.today() + timedelta(days=1)

    # Pull or load data
    if args.cached and os.path.exists(args.cached):
        print(f"Using cached data: {args.cached}", file=sys.stderr)
        with open(args.cached) as f:
            data = json.load(f)
    else:
        data = pull_all_courses()
        # Save raw data for debugging/caching
        cache_path = "/tmp/canvas_briefing_data.json"
        with open(cache_path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"  Cached raw data: {cache_path}", file=sys.stderr)

    # Build briefing
    briefing = build_briefing(data, target_date)

    # Save
    output_dir = args.output or os.path.expanduser("~/Downloads")
    filename = f"daily_briefing_{target_date.isoformat()}.md"
    out_path = os.path.join(output_dir, filename)
    with open(out_path, "w") as f:
        f.write(briefing)

    print(f"\nBriefing saved: {out_path} ({len(briefing):,} chars)", file=sys.stderr)
    print("", file=sys.stderr)

    # Print to terminal
    print(briefing)


if __name__ == "__main__":
    main()
