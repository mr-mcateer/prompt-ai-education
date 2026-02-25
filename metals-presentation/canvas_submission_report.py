#!/usr/bin/env python3
"""
Canvas Student Submission Status PDF Report
=============================================
Pulls submission data from Canvas LMS for all CTE courses and generates
a professionally styled PDF report showing completion status, late/missing
patterns, and per-student breakdowns organized by class.

Usage:
  python3 canvas_submission_report.py --all
  python3 canvas_submission_report.py --metals-only
  python3 canvas_submission_report.py --engines-only
  python3 canvas_submission_report.py --from-csv metals_grades_export.csv
  python3 canvas_submission_report.py --output custom_report.pdf
"""

import argparse
import csv
import os
import sys
import time
from collections import defaultdict
from datetime import datetime
from io import BytesIO

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer,
    Table, TableStyle,
)

# ── Project imports ──────────────────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from tools.env_loader import get_env

# ── Course configuration ─────────────────────────────────────
METALS_IDS = [23164, 23132, 23157, 23188, 23177]
ENGINES_IDS = [23124, 23344]
ALL_IDS = METALS_IDS + ENGINES_IDS

DEPARTMENT_MAP = {}
for cid in METALS_IDS:
    DEPARTMENT_MAP[cid] = "Metals"
for cid in ENGINES_IDS:
    DEPARTMENT_MAP[cid] = "Engines & Fabrication"

# ── Color palette ────────────────────────────────────────────
C_GREEN = colors.HexColor("#2E7D32")
C_DARK_GREEN = colors.HexColor("#1B5E20")
C_AMBER = colors.HexColor("#F57F17")
C_RED = colors.HexColor("#C62828")
C_GRAY = colors.HexColor("#9E9E9E")
C_LIGHT_GRAY = colors.HexColor("#F5F5F5")
C_BLUE = colors.HexColor("#1565C0")
C_WHITE = colors.HexColor("#FFFFFF")
C_RISK_BG = colors.HexColor("#FFEBEE")
C_LIGHT_GREEN = colors.HexColor("#E8F5E9")
C_LIGHT_AMBER = colors.HexColor("#FFF8E1")

# Matplotlib colors (matching)
MPL_GREEN = "#2E7D32"
MPL_AMBER = "#F57F17"
MPL_RED = "#C62828"
MPL_GRAY = "#9E9E9E"
MPL_BLUE = "#1565C0"

# ══════════════════════════════════════════════════════════════
# SECTION 1: DATA COLLECTION
# ══════════════════════════════════════════════════════════════

def get_canvas():
    """Initialize Canvas API connection using secure env loader."""
    from canvasapi import Canvas
    url = get_env("CANVAS_API_URL")
    token = get_env("CANVAS_API_TOKEN")
    return Canvas(url, token)


def collect_data(course_ids):
    """Fetch enrollment, assignment, and submission data from Canvas API."""
    canvas = get_canvas()
    data = {}

    for cid in course_ids:
        print(f"\n{'=' * 60}")
        course = canvas.get_course(cid)
        cname = getattr(course, "name", f"Course {cid}")
        print(f"  Fetching: {cname} (ID: {cid})")
        print(f"{'=' * 60}")

        # Enrollments
        print("  Students...", end="")
        students = {}
        for enr in course.get_enrollments(type=["StudentEnrollment"]):
            u = enr.user
            uid = u["id"]
            name = u.get("sortable_name", u.get("name", "Unknown"))
            if name.startswith("Unknown ("):
                continue
            students[uid] = {"name": name}
        print(f" {len(students)} found")

        # Assignments
        print("  Assignments...", end="")
        raw_assignments = list(course.get_assignments())
        assignments = []
        for a in raw_assignments:
            if not getattr(a, "published", False):
                continue
            assignments.append({
                "id": a.id,
                "name": getattr(a, "name", "Unnamed"),
                "points_possible": getattr(a, "points_possible", 0) or 0,
                "due_at": getattr(a, "due_at", None),
            })
        print(f" {len(assignments)} published")

        # Submissions
        submissions = {}  # {(student_id, assignment_id): {...}}
        for a in raw_assignments:
            if not getattr(a, "published", False):
                continue
            aname = getattr(a, "name", "Unnamed")
            print(f"    {aname[:50]}...", end="")
            try:
                subs = list(a.get_submissions())
            except Exception as e:
                print(f" [ERROR: {e}]")
                continue
            count = 0
            for s in subs:
                uid = s.user_id
                if uid not in students:
                    continue
                submissions[(uid, a.id)] = {
                    "score": getattr(s, "score", None),
                    "submitted_at": getattr(s, "submitted_at", None),
                    "due_at": getattr(a, "due_at", None),
                    "late": getattr(s, "late", False),
                    "missing": getattr(s, "missing", False),
                    "workflow_state": getattr(s, "workflow_state", "unsubmitted"),
                    "points_possible": getattr(a, "points_possible", 0) or 0,
                    "assignment_name": aname,
                }
                count += 1
            print(f" ({count})")
            time.sleep(0.05)

        data[cid] = {
            "name": cname,
            "department": DEPARTMENT_MAP.get(cid, "Unknown"),
            "students": students,
            "assignments": assignments,
            "submissions": submissions,
        }

    return data


def collect_from_csv(csv_path):
    """Load submission data from an existing CSV export."""
    data = {}
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cid = int(row["course_id"])
            cname = row["course_name"]
            student_name = row["student_name"]
            student_id = int(row["student_canvas_id"])

            if student_name.startswith("Unknown ("):
                continue

            if cid not in data:
                data[cid] = {
                    "name": cname,
                    "department": DEPARTMENT_MAP.get(cid, "Unknown"),
                    "students": {},
                    "assignments": [],
                    "submissions": {},
                    "_assignment_ids_seen": set(),
                }

            course = data[cid]
            course["students"][student_id] = {"name": student_name}

            aid = int(row["assignment_id"])
            if aid not in course["_assignment_ids_seen"]:
                course["_assignment_ids_seen"].add(aid)
                course["assignments"].append({
                    "id": aid,
                    "name": row["assignment_name"],
                    "points_possible": float(row["points_possible"]) if row["points_possible"] else 0,
                    "due_at": row.get("due_at", None),
                })

            score = float(row["score"]) if row["score"] else None
            course["submissions"][(student_id, aid)] = {
                "score": score,
                "submitted_at": row.get("submitted_at") or None,
                "due_at": row.get("due_at") or None,
                "late": row.get("late", "False") == "True",
                "missing": row.get("missing", "False") == "True",
                "workflow_state": row.get("workflow_state", "unsubmitted"),
                "points_possible": float(row["points_possible"]) if row["points_possible"] else 0,
                "assignment_name": row["assignment_name"],
            }

    # Clean up temp keys
    for cid in data:
        data[cid].pop("_assignment_ids_seen", None)

    return data


# ══════════════════════════════════════════════════════════════
# SECTION 2: DATA ANALYSIS
# ══════════════════════════════════════════════════════════════

def classify_status(sub):
    """Return a status string for a submission record."""
    if sub is None:
        return "unsubmitted"
    wf = sub["workflow_state"]
    if sub["missing"]:
        return "missing"
    if sub["late"]:
        return "late"
    if wf in ("graded", "submitted", "pending_review"):
        return "submitted"
    return "unsubmitted"


def analyze(data):
    """Compute all statistics needed for the PDF report."""
    result = {"courses": {}, "totals": {}, "departments": {}}
    all_students = 0
    all_submitted = 0
    all_late = 0
    all_missing = 0
    all_unsubmitted = 0
    all_graded_scores = []
    all_at_risk = 0
    dept_stats = defaultdict(lambda: {
        "students": 0, "submitted": 0, "late": 0, "missing": 0,
        "unsubmitted": 0, "scores": [], "courses": 0,
    })

    for cid, course in data.items():
        students = course["students"]
        assignments = course["assignments"]
        subs = course["submissions"]
        num_students = len(students)
        num_assignments = len(assignments)
        dept = course["department"]

        # Per-assignment stats
        asgn_stats = []
        for a in assignments:
            aid = a["id"]
            a_submitted = 0
            a_late = 0
            a_missing = 0
            a_scores = []
            for sid in students:
                sub = subs.get((sid, aid))
                status = classify_status(sub)
                if status == "submitted":
                    a_submitted += 1
                elif status == "late":
                    a_late += 1
                    a_submitted += 1  # late counts as submitted too
                elif status == "missing":
                    a_missing += 1
                if sub and sub["score"] is not None:
                    a_scores.append(sub["score"])

            avg_score = sum(a_scores) / len(a_scores) if a_scores else 0
            avg_pct = (avg_score / a["points_possible"] * 100) if a["points_possible"] and a_scores else 0
            sub_rate = (a_submitted / num_students * 100) if num_students else 0

            asgn_stats.append({
                "id": aid,
                "name": a["name"],
                "points": a["points_possible"],
                "due_at": a["due_at"],
                "submitted": a_submitted,
                "late": a_late,
                "missing": a_missing,
                "avg_score": avg_score,
                "avg_pct": avg_pct,
                "sub_rate": sub_rate,
                "scores": a_scores,
            })

        # Per-student stats
        student_stats = []
        course_at_risk = 0
        for sid, sinfo in students.items():
            s_submitted = 0
            s_late = 0
            s_missing = 0
            s_unsubmitted = 0
            s_scores = []
            s_statuses = {}  # aid -> status

            for a in assignments:
                aid = a["id"]
                sub = subs.get((sid, aid))
                status = classify_status(sub)
                s_statuses[aid] = status

                if status == "submitted":
                    s_submitted += 1
                elif status == "late":
                    s_late += 1
                    s_submitted += 1
                elif status == "missing":
                    s_missing += 1
                else:
                    s_unsubmitted += 1

                if sub and sub["score"] is not None:
                    s_scores.append(sub["score"] / sub["points_possible"] * 100 if sub["points_possible"] else 0)

            completion = (s_submitted / num_assignments * 100) if num_assignments else 0
            avg_pct = sum(s_scores) / len(s_scores) if s_scores else 0
            at_risk = s_missing >= 2 or (completion < 50 and num_assignments > 0)
            if at_risk:
                course_at_risk += 1

            student_stats.append({
                "id": sid,
                "name": sinfo["name"],
                "submitted": s_submitted,
                "late": s_late,
                "missing": s_missing,
                "unsubmitted": s_unsubmitted,
                "completion": completion,
                "avg_pct": avg_pct,
                "at_risk": at_risk,
                "statuses": s_statuses,
            })

        student_stats.sort(key=lambda s: s["name"])

        # Course-level totals
        c_submitted = sum(1 for s in student_stats for a in assignments
                         if classify_status(subs.get((s["id"], a["id"]))) in ("submitted", "late"))
        c_late = sum(s["late"] for s in student_stats)
        c_missing = sum(s["missing"] for s in student_stats)
        c_unsubmitted = sum(s["unsubmitted"] for s in student_stats)
        c_total_pairs = num_students * num_assignments
        c_completion = (c_submitted / c_total_pairs * 100) if c_total_pairs else 0

        # Grade distribution
        all_pcts = []
        for sid in students:
            for a in assignments:
                sub = subs.get((sid, a["id"]))
                if sub and sub["score"] is not None and sub["points_possible"]:
                    pct = sub["score"] / sub["points_possible"] * 100
                    all_pcts.append(pct)
                    all_graded_scores.append(pct)

        grade_dist = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
        for p in all_pcts:
            if p >= 90: grade_dist["A"] += 1
            elif p >= 80: grade_dist["B"] += 1
            elif p >= 70: grade_dist["C"] += 1
            elif p >= 60: grade_dist["D"] += 1
            else: grade_dist["F"] += 1

        result["courses"][cid] = {
            "name": course["name"],
            "department": dept,
            "num_students": num_students,
            "num_assignments": num_assignments,
            "completion": c_completion,
            "submitted": c_submitted,
            "late": c_late,
            "missing": c_missing,
            "unsubmitted": c_unsubmitted,
            "at_risk": course_at_risk,
            "grade_dist": grade_dist,
            "assignments": asgn_stats,
            "students": student_stats,
        }

        all_students += num_students
        all_submitted += c_submitted
        all_late += c_late
        all_missing += c_missing
        all_unsubmitted += c_unsubmitted
        all_at_risk += course_at_risk

        ds = dept_stats[dept]
        ds["students"] += num_students
        ds["submitted"] += c_submitted
        ds["late"] += c_late
        ds["missing"] += c_missing
        ds["unsubmitted"] += c_unsubmitted
        ds["courses"] += 1

    total_pairs = all_submitted + all_missing + all_unsubmitted
    result["totals"] = {
        "students": all_students,
        "submitted": all_submitted,
        "late": all_late,
        "missing": all_missing,
        "unsubmitted": all_unsubmitted,
        "completion": (all_submitted / total_pairs * 100) if total_pairs else 0,
        "at_risk": all_at_risk,
        "avg_grade": sum(all_graded_scores) / len(all_graded_scores) if all_graded_scores else 0,
    }
    result["departments"] = dict(dept_stats)

    return result


# ══════════════════════════════════════════════════════════════
# SECTION 3: CHART GENERATION
# ══════════════════════════════════════════════════════════════

def _fig_to_image(fig, width=5*inch, height=3*inch):
    """Convert a matplotlib figure to a ReportLab Image flowable."""
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    buf.seek(0)
    return Image(buf, width=width, height=height)


def chart_status_pie(analysis):
    """Pie chart of overall submission status breakdown."""
    t = analysis["totals"]
    on_time = t["submitted"] - t["late"]
    values = [on_time, t["late"], t["missing"], t["unsubmitted"]]
    labels = ["On Time", "Late", "Missing", "Unsubmitted"]
    chart_colors = [MPL_GREEN, MPL_AMBER, MPL_RED, MPL_GRAY]

    # Filter out zero values
    filtered = [(v, l, c) for v, l, c in zip(values, labels, chart_colors) if v > 0]
    if not filtered:
        return Spacer(1, 0.1 * inch)
    values, labels, chart_colors = zip(*filtered)

    fig, ax = plt.subplots(figsize=(4, 3))
    wedges, texts, autotexts = ax.pie(
        values, labels=labels, colors=chart_colors, autopct="%1.0f%%",
        startangle=90, textprops={"fontsize": 9},
    )
    for at in autotexts:
        at.set_fontsize(8)
        at.set_color("white")
        at.set_fontweight("bold")
    ax.set_title("Overall Submission Status", fontsize=11, fontweight="bold", pad=10)
    fig.tight_layout()
    return _fig_to_image(fig, width=3.5*inch, height=2.8*inch)


def chart_completion_by_course(analysis):
    """Horizontal bar chart of completion rates per course."""
    courses = analysis["courses"]
    names = []
    rates = []
    bar_colors = []
    for cid in sorted(courses, key=lambda c: courses[c]["name"]):
        c = courses[cid]
        if c["num_students"] == 0:
            continue
        short_name = c["name"]
        if len(short_name) > 25:
            short_name = short_name[:22] + "..."
        names.append(short_name)
        rates.append(c["completion"])
        bar_colors.append(MPL_GREEN if c["completion"] >= 70 else MPL_AMBER if c["completion"] >= 50 else MPL_RED)

    fig, ax = plt.subplots(figsize=(6, max(2.5, len(names) * 0.45)))
    bars = ax.barh(names, rates, color=bar_colors, height=0.6)
    ax.set_xlim(0, 105)
    ax.set_xlabel("Completion %", fontsize=9)
    ax.set_title("Completion Rate by Course", fontsize=11, fontweight="bold")
    ax.xaxis.set_major_formatter(mticker.PercentFormatter())
    for bar, rate in zip(bars, rates):
        ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2,
                f"{rate:.0f}%", va="center", fontsize=8)
    ax.tick_params(axis="y", labelsize=8)
    fig.tight_layout()
    return _fig_to_image(fig, width=6*inch, height=max(2.5, len(names)*0.45)*inch)


def chart_grade_distribution(course_analysis):
    """Bar chart of grade distribution for a single course."""
    dist = course_analysis["grade_dist"]
    grades = ["A", "B", "C", "D", "F"]
    counts = [dist.get(g, 0) for g in grades]
    grade_colors = ["#1B5E20", "#2E7D32", "#F57F17", "#E65100", "#C62828"]

    fig, ax = plt.subplots(figsize=(3.5, 2))
    ax.bar(grades, counts, color=grade_colors, width=0.6)
    ax.set_ylabel("Count", fontsize=8)
    ax.set_title("Grade Distribution", fontsize=10, fontweight="bold")
    ax.tick_params(labelsize=8)
    ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    fig.tight_layout()
    return _fig_to_image(fig, width=3*inch, height=1.8*inch)


def chart_missing_by_assignment(analysis):
    """Bar chart of missing rates across all assignments."""
    asgn_missing = defaultdict(lambda: {"missing": 0, "total": 0})
    for cid, c in analysis["courses"].items():
        for a in c["assignments"]:
            key = a["name"]
            asgn_missing[key]["missing"] += a["missing"]
            asgn_missing[key]["total"] += c["num_students"]

    if not asgn_missing:
        return Spacer(1, 0.1*inch)

    items = sorted(asgn_missing.items(),
                   key=lambda x: x[1]["missing"]/max(x[1]["total"], 1), reverse=True)[:10]
    names = []
    rates = []
    for name, d in items:
        short = name[:30] + "..." if len(name) > 30 else name
        names.append(short)
        rates.append(d["missing"] / max(d["total"], 1) * 100)

    fig, ax = plt.subplots(figsize=(6, max(2.5, len(names)*0.4)))
    ax.barh(names, rates, color=MPL_RED, height=0.6)
    ax.set_xlim(0, max(rates + [10]) * 1.15)
    ax.set_xlabel("Missing %", fontsize=9)
    ax.set_title("Assignments with Highest Missing Rates", fontsize=11, fontweight="bold")
    ax.tick_params(axis="y", labelsize=8)
    fig.tight_layout()
    return _fig_to_image(fig, width=6*inch, height=max(2.5, len(names)*0.4)*inch)


# ══════════════════════════════════════════════════════════════
# SECTION 4: PDF CONSTRUCTION
# ══════════════════════════════════════════════════════════════

def _styles():
    """Build custom paragraph styles."""
    ss = getSampleStyleSheet()
    custom = {}
    custom["title"] = ParagraphStyle(
        "CoverTitle", parent=ss["Title"], fontSize=28, leading=34,
        textColor=C_BLUE, spaceAfter=6,
    )
    custom["subtitle"] = ParagraphStyle(
        "CoverSubtitle", parent=ss["Normal"], fontSize=14, leading=18,
        textColor=colors.HexColor("#424242"), alignment=TA_CENTER,
    )
    custom["h1"] = ParagraphStyle(
        "SectionH1", parent=ss["Heading1"], fontSize=18, leading=22,
        textColor=C_BLUE, spaceBefore=12, spaceAfter=8,
    )
    custom["h2"] = ParagraphStyle(
        "SectionH2", parent=ss["Heading2"], fontSize=14, leading=17,
        textColor=colors.HexColor("#1565C0"), spaceBefore=10, spaceAfter=6,
    )
    custom["body"] = ParagraphStyle(
        "Body", parent=ss["Normal"], fontSize=10, leading=13,
    )
    custom["small"] = ParagraphStyle(
        "Small", parent=ss["Normal"], fontSize=8, leading=10,
        textColor=colors.HexColor("#616161"),
    )
    custom["metric_big"] = ParagraphStyle(
        "MetricBig", parent=ss["Normal"], fontSize=24, leading=28,
        textColor=C_BLUE, alignment=TA_CENTER,
    )
    custom["metric_label"] = ParagraphStyle(
        "MetricLabel", parent=ss["Normal"], fontSize=9, leading=11,
        textColor=colors.HexColor("#757575"), alignment=TA_CENTER,
    )
    custom["cell"] = ParagraphStyle(
        "Cell", parent=ss["Normal"], fontSize=8, leading=10,
    )
    custom["cell_center"] = ParagraphStyle(
        "CellCenter", parent=ss["Normal"], fontSize=8, leading=10,
        alignment=TA_CENTER,
    )
    custom["cell_header"] = ParagraphStyle(
        "CellHeader", parent=ss["Normal"], fontSize=8, leading=10,
        textColor=C_WHITE, alignment=TA_CENTER,
    )
    return custom


def _header_footer(canvas_obj, doc):
    """Draw header/footer on each page."""
    canvas_obj.saveState()
    # Header line
    canvas_obj.setStrokeColor(C_BLUE)
    canvas_obj.setLineWidth(1)
    canvas_obj.line(0.75*inch, 10.25*inch, 7.75*inch, 10.25*inch)
    canvas_obj.setFont("Helvetica", 8)
    canvas_obj.setFillColor(colors.HexColor("#757575"))
    canvas_obj.drawString(0.75*inch, 10.35*inch, "CTE Submission Report")
    canvas_obj.drawRightString(7.75*inch, 10.35*inch, datetime.now().strftime("%B %d, %Y"))
    # Footer
    canvas_obj.setFont("Helvetica", 8)
    canvas_obj.drawCentredString(4.25*inch, 0.5*inch, f"Page {doc.page}")
    canvas_obj.restoreState()


def _metric_cell(value, label, styles):
    """Create a small metric display (big number + label beneath)."""
    return [
        Paragraph(str(value), styles["metric_big"]),
        Paragraph(label, styles["metric_label"]),
    ]


def _status_color(status):
    """Return a color for a submission status."""
    return {
        "submitted": C_GREEN,
        "late": C_AMBER,
        "missing": C_RED,
        "unsubmitted": C_LIGHT_GRAY,
    }.get(status, C_LIGHT_GRAY)


def build_pdf(analysis, output_path):
    """Assemble the full PDF report."""
    sty = _styles()
    elements = []

    # ── COVER PAGE ────────────────────────────────────────────
    elements.append(Spacer(1, 2*inch))
    elements.append(Paragraph("Student Submission<br/>Status Report", sty["title"]))
    elements.append(Spacer(1, 0.3*inch))
    elements.append(Paragraph("CTE Department, Bend-La Pine Schools", sty["subtitle"]))
    elements.append(Spacer(1, 0.15*inch))
    elements.append(Paragraph("Instructor: Andrew McAteer", sty["subtitle"]))
    elements.append(Spacer(1, 0.5*inch))

    t = analysis["totals"]
    cover_data = [
        [f"{len(analysis['courses'])} Courses", f"{t['students']} Students",
         f"{t['submitted']} Submissions"],
    ]
    cover_table = Table(cover_data, colWidths=[2.2*inch]*3)
    cover_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 12),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#424242")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
    ]))
    elements.append(cover_table)
    elements.append(Spacer(1, 1*inch))
    elements.append(Paragraph(
        f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
        sty["subtitle"]
    ))
    elements.append(PageBreak())

    # ── EXECUTIVE SUMMARY ─────────────────────────────────────
    elements.append(Paragraph("Executive Summary", sty["h1"]))
    elements.append(Spacer(1, 0.2*inch))

    # Key metrics row
    metrics_data = [[
        Paragraph(f"<b>{t['students']}</b>", sty["metric_big"]),
        Paragraph(f"<b>{t['completion']:.0f}%</b>", sty["metric_big"]),
        Paragraph(f"<b>{t['avg_grade']:.0f}%</b>", sty["metric_big"]),
        Paragraph(f"<b>{t['at_risk']}</b>", sty["metric_big"]),
    ], [
        Paragraph("Total Students", sty["metric_label"]),
        Paragraph("Completion Rate", sty["metric_label"]),
        Paragraph("Avg Grade", sty["metric_label"]),
        Paragraph("At Risk", sty["metric_label"]),
    ]]
    metrics_table = Table(metrics_data, colWidths=[1.65*inch]*4)
    metrics_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 2),
        ("TOPPADDING", (0, 1), (-1, 1), 0),
        ("BOX", (0, 0), (-1, -1), 0.5, C_BLUE),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, C_LIGHT_GRAY),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8F9FA")),
        ("ROUNDEDCORNERS", [4, 4, 4, 4]),
    ]))
    elements.append(metrics_table)
    elements.append(Spacer(1, 0.3*inch))

    # Charts side by side via table
    pie_chart = chart_status_pie(analysis)
    comp_chart = chart_completion_by_course(analysis)
    elements.append(pie_chart)
    elements.append(Spacer(1, 0.2*inch))
    elements.append(comp_chart)
    elements.append(PageBreak())

    # ── DEPARTMENT OVERVIEW ───────────────────────────────────
    if len(analysis["departments"]) > 1:
        elements.append(Paragraph("Department Overview", sty["h1"]))
        elements.append(Spacer(1, 0.15*inch))

        dept_header = [
            Paragraph("<b>Department</b>", sty["cell_header"]),
            Paragraph("<b>Courses</b>", sty["cell_header"]),
            Paragraph("<b>Students</b>", sty["cell_header"]),
            Paragraph("<b>Submitted</b>", sty["cell_header"]),
            Paragraph("<b>Late</b>", sty["cell_header"]),
            Paragraph("<b>Missing</b>", sty["cell_header"]),
        ]
        dept_rows = [dept_header]
        for dname, ds in analysis["departments"].items():
            dept_rows.append([
                Paragraph(dname, sty["cell"]),
                Paragraph(str(ds["courses"]), sty["cell_center"]),
                Paragraph(str(ds["students"]), sty["cell_center"]),
                Paragraph(str(ds["submitted"]), sty["cell_center"]),
                Paragraph(str(ds["late"]), sty["cell_center"]),
                Paragraph(str(ds["missing"]), sty["cell_center"]),
            ])

        dept_table = Table(dept_rows, colWidths=[2*inch, 0.8*inch, 0.9*inch, 1*inch, 0.8*inch, 0.9*inch])
        dept_style = [
            ("BACKGROUND", (0, 0), (-1, 0), C_BLUE),
            ("TEXTCOLOR", (0, 0), (-1, 0), C_WHITE),
            ("ALIGN", (1, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E0E0E0")),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]
        for i in range(1, len(dept_rows)):
            if i % 2 == 0:
                dept_style.append(("BACKGROUND", (0, i), (-1, i), C_LIGHT_GRAY))
        dept_table.setStyle(TableStyle(dept_style))
        elements.append(dept_table)
        elements.append(PageBreak())

    # ── PER-COURSE DETAIL ─────────────────────────────────────
    for cid in sorted(analysis["courses"], key=lambda c: analysis["courses"][c]["name"]):
        c = analysis["courses"][cid]

        # Skip empty courses (no enrolled students)
        if c["num_students"] == 0:
            continue

        elements.append(Paragraph(f"{c['name']}", sty["h1"]))

        # Summary stats
        summary_data = [
            ["Students", "Assignments", "Completion", "Late", "Missing", "At Risk"],
            [str(c["num_students"]), str(c["num_assignments"]),
             f"{c['completion']:.0f}%", str(c["late"]), str(c["missing"]),
             str(c["at_risk"])],
        ]
        summary_table = Table(summary_data, colWidths=[1.05*inch]*6)
        summary_style = [
            ("BACKGROUND", (0, 0), (-1, 0), C_BLUE),
            ("TEXTCOLOR", (0, 0), (-1, 0), C_WHITE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E0E0E0")),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]
        summary_table.setStyle(TableStyle(summary_style))
        elements.append(summary_table)
        elements.append(Spacer(1, 0.2*inch))

        # Completion matrix
        if c["assignments"] and c["students"]:
            elements.append(Paragraph("Submission Matrix", sty["h2"]))

            num_asgn = len(c["assignments"])
            use_numbers = num_asgn > 8  # Use numbered columns for wide matrices

            # Build header row
            asgn_names = []
            if use_numbers:
                for i in range(num_asgn):
                    asgn_names.append(Paragraph(f"<b>{i+1}</b>", sty["cell_header"]))
            else:
                for a in c["assignments"]:
                    short = a["name"][:18] + ".." if len(a["name"]) > 18 else a["name"]
                    asgn_names.append(Paragraph(f"<b>{short}</b>", sty["cell_header"]))

            header_row = [Paragraph("<b>Student</b>", sty["cell_header"])] + asgn_names
            matrix_rows = [header_row]

            # Column widths: narrower for many assignments
            if use_numbers:
                asgn_col_w = min(0.38, 5.5 / max(num_asgn, 1))
            else:
                asgn_col_w = min(1.0, 5.5 / max(num_asgn, 1))
            name_col_w = 1.4 if use_numbers else 1.8
            col_widths = [name_col_w*inch] + [asgn_col_w*inch]*num_asgn

            font_size = 6 if use_numbers else 7

            style_cmds = [
                ("BACKGROUND", (0, 0), (-1, 0), C_BLUE),
                ("TEXTCOLOR", (0, 0), (-1, 0), C_WHITE),
                ("FONTSIZE", (0, 0), (-1, -1), font_size),
                ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#E0E0E0")),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
            ]

            for row_idx, student in enumerate(c["students"], start=1):
                name_cell = Paragraph(student["name"], sty["cell"])
                row = [name_cell]
                for col_idx, a in enumerate(c["assignments"], start=1):
                    status = student["statuses"].get(a["id"], "unsubmitted")
                    # Use single-char symbols for compact display
                    if use_numbers:
                        cell_text = {
                            "submitted": "\u2713", "late": "L",
                            "missing": "\u2717", "unsubmitted": "-",
                        }.get(status, "-")
                    else:
                        cell_text = {
                            "submitted": "OK", "late": "LATE",
                            "missing": "X", "unsubmitted": "-",
                        }.get(status, "-")
                    row.append(Paragraph(cell_text, sty["cell_center"]))

                    bg_color = _status_color(status)
                    style_cmds.append(
                        ("BACKGROUND", (col_idx, row_idx), (col_idx, row_idx), bg_color)
                    )
                    if status in ("submitted", "missing"):
                        style_cmds.append(
                            ("TEXTCOLOR", (col_idx, row_idx), (col_idx, row_idx), C_WHITE)
                        )

                if student["at_risk"]:
                    style_cmds.append(
                        ("BACKGROUND", (0, row_idx), (0, row_idx), C_RISK_BG)
                    )

                matrix_rows.append(row)

            matrix_table = Table(matrix_rows, colWidths=col_widths, repeatRows=1)
            matrix_table.setStyle(TableStyle(style_cmds))
            elements.append(matrix_table)
            elements.append(Spacer(1, 0.1*inch))

            # Status legend
            legend_data = [[
                "", Paragraph("Submitted", sty["small"]),
                "", Paragraph("Late", sty["small"]),
                "", Paragraph("Missing", sty["small"]),
                "", Paragraph("Not submitted", sty["small"]),
            ]]
            legend_table = Table(legend_data, colWidths=[0.18*inch, 0.85*inch, 0.18*inch, 0.5*inch, 0.18*inch, 0.6*inch, 0.18*inch, 1*inch])
            legend_table.setStyle(TableStyle([
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BACKGROUND", (0, 0), (0, 0), C_GREEN),
                ("BACKGROUND", (2, 0), (2, 0), C_AMBER),
                ("BACKGROUND", (4, 0), (4, 0), C_RED),
                ("BACKGROUND", (6, 0), (6, 0), C_GRAY),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]))
            elements.append(legend_table)

            # Assignment key (numbered legend) for compact matrices
            if use_numbers:
                elements.append(Spacer(1, 0.1*inch))
                key_text = "  ".join(
                    f"<b>{i+1}</b>: {a['name'][:35]}"
                    for i, a in enumerate(c["assignments"])
                )
                elements.append(Paragraph(key_text, sty["small"]))

        elements.append(Spacer(1, 0.2*inch))

        # Grade distribution chart
        if sum(c["grade_dist"].values()) > 0:
            elements.append(chart_grade_distribution(c))

        # At-risk students callout (keep together to avoid page splits)
        at_risk_students = [s for s in c["students"] if s["at_risk"]]
        if at_risk_students:
            risk_elements = []
            risk_elements.append(Spacer(1, 0.15*inch))
            risk_elements.append(Paragraph("Students Needing Attention", sty["h2"]))
            risk_header = [
                Paragraph("<b>Student</b>", sty["cell_header"]),
                Paragraph("<b>Completion</b>", sty["cell_header"]),
                Paragraph("<b>Avg Grade</b>", sty["cell_header"]),
                Paragraph("<b>Missing</b>", sty["cell_header"]),
                Paragraph("<b>Late</b>", sty["cell_header"]),
            ]
            risk_rows = [risk_header]
            for s in at_risk_students:
                risk_rows.append([
                    Paragraph(s["name"], sty["cell"]),
                    Paragraph(f"{s['completion']:.0f}%", sty["cell_center"]),
                    Paragraph(f"{s['avg_pct']:.0f}%" if s["avg_pct"] else "N/A", sty["cell_center"]),
                    Paragraph(str(s["missing"]), sty["cell_center"]),
                    Paragraph(str(s["late"]), sty["cell_center"]),
                ])
            risk_table = Table(risk_rows, colWidths=[2*inch, 1*inch, 1*inch, 0.8*inch, 0.8*inch])
            risk_style = [
                ("BACKGROUND", (0, 0), (-1, 0), C_RED),
                ("TEXTCOLOR", (0, 0), (-1, 0), C_WHITE),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E0E0E0")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ALIGN", (1, 0), (-1, -1), "CENTER"),
            ]
            for i in range(1, len(risk_rows)):
                risk_style.append(("BACKGROUND", (0, i), (-1, i), C_RISK_BG))
            risk_table.setStyle(TableStyle(risk_style))
            risk_elements.append(risk_table)
            elements.append(KeepTogether(risk_elements))

        elements.append(PageBreak())

    # ── LATE/MISSING PATTERNS ─────────────────────────────────
    elements.append(Paragraph("Late & Missing Patterns", sty["h1"]))
    elements.append(Spacer(1, 0.1*inch))
    elements.append(Paragraph(
        "Assignments with the highest missing rates across all courses. "
        "High missing rates may indicate unclear instructions or visibility issues.",
        sty["body"]
    ))
    elements.append(Spacer(1, 0.2*inch))
    elements.append(chart_missing_by_assignment(analysis))

    # Build the PDF
    doc = SimpleDocTemplate(
        output_path, pagesize=letter,
        leftMargin=0.75*inch, rightMargin=0.75*inch,
        topMargin=1*inch, bottomMargin=0.75*inch,
    )
    doc.build(elements, onFirstPage=_header_footer, onLaterPages=_header_footer)
    print(f"\n  PDF saved: {output_path}")


# ══════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Canvas Student Submission Status PDF Report"
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--all", action="store_true",
                       help="Report on all 7 courses (metals + engines)")
    group.add_argument("--metals-only", action="store_true",
                       help="Report on 5 metals courses only")
    group.add_argument("--engines-only", action="store_true",
                       help="Report on 2 engines/fab courses only")
    group.add_argument("--course-id", type=int, action="append",
                       help="Specific course ID(s)")
    parser.add_argument("--from-csv", type=str, default=None,
                        help="Use existing CSV instead of live Canvas API")
    parser.add_argument("--output", type=str, default=None,
                        help="Output PDF path (default: submission_report_YYYY-MM-DD.pdf)")
    args = parser.parse_args()

    # Determine course IDs
    if args.all:
        course_ids = ALL_IDS
    elif args.metals_only:
        course_ids = METALS_IDS
    elif args.engines_only:
        course_ids = ENGINES_IDS
    elif args.course_id:
        course_ids = args.course_id
    else:
        course_ids = ALL_IDS  # default to all

    # Output path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if args.output:
        output_path = args.output
    else:
        date_str = datetime.now().strftime("%Y-%m-%d")
        output_path = os.path.join(script_dir, f"submission_report_{date_str}.pdf")

    # Collect data
    print("\n" + "=" * 60)
    print("  CANVAS SUBMISSION STATUS REPORT")
    print("=" * 60)

    if args.from_csv:
        print(f"  Loading data from CSV: {args.from_csv}")
        data = collect_from_csv(args.from_csv)
    else:
        print(f"  Fetching data from Canvas API for {len(course_ids)} courses...")
        data = collect_data(course_ids)

    if not data:
        print("  No data found. Check course IDs or CSV path.")
        sys.exit(1)

    # Analyze
    print("\n  Analyzing submission patterns...")
    analysis = analyze(data)

    # Build PDF
    print(f"  Building PDF report...")
    build_pdf(analysis, output_path)

    # Summary
    t = analysis["totals"]
    print(f"\n{'=' * 60}")
    print(f"  REPORT COMPLETE")
    print(f"{'=' * 60}")
    print(f"  Output: {output_path}")
    print(f"  Courses: {len(analysis['courses'])}")
    print(f"  Students: {t['students']}")
    print(f"  Completion: {t['completion']:.0f}%")
    print(f"  At Risk: {t['at_risk']}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
