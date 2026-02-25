#!/usr/bin/env python3
"""
Generate a professional PDF grade report from Canvas grades export CSV.
BLUF (Bottom Line Up Front) executive brief format.

Usage:
    python3 generate_grades_report.py
"""

import csv
import os
from collections import OrderedDict
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer,
    Table, TableStyle,
)

# -- Color palette (matching project standard) -------------------------
C_BLUE = colors.HexColor("#1565C0")
C_WHITE = colors.HexColor("#FFFFFF")
C_GREEN = colors.HexColor("#2E7D32")
C_AMBER = colors.HexColor("#F57F17")
C_RED = colors.HexColor("#C62828")
C_GRAY = colors.HexColor("#9E9E9E")
C_LIGHT_GRAY = colors.HexColor("#F5F5F5")
C_LIGHT_GREEN = colors.HexColor("#E8F5E9")
C_LIGHT_AMBER = colors.HexColor("#FFF8E1")
C_LIGHT_RED = colors.HexColor("#FFEBEE")
C_DARK = colors.HexColor("#212121")
C_MEDIUM = colors.HexColor("#616161")
C_LIGHT_BLUE = colors.HexColor("#E3F2FD")

REPORT_DATE = "February 24, 2026"
CSV_PATH = os.path.join(os.path.dirname(__file__), "metals_grades_export.csv")

# -- Course ordering (period order) ------------------------------------
COURSE_ORDER = [
    "P1 Engines Fab 1",
    "P1 Engines Fab 2",
    "P3 Metals 1",
    "P3 Metals 2",
    "P5 Metals 1",
    "P5 Metals 2",
]

COURSE_INFO = {
    "P1 Engines Fab 1": {"period": "Period 1", "section": "Engines & Fabrication 1", "course_id": 23124},
    "P1 Engines Fab 2": {"period": "Period 1", "section": "Engines & Fabrication 2", "course_id": 23344},
    "P3 Metals 1":      {"period": "Period 3", "section": "Metals 1",               "course_id": 23164},
    "P3 Metals 2":      {"period": "Period 3", "section": "Metals 2",               "course_id": 23132},
    "P5 Metals 1":      {"period": "Period 5", "section": "Metals 1",               "course_id": 23188},
    "P5 Metals 2":      {"period": "Period 5", "section": "Metals 2",               "course_id": 23177},
}

# Skip course 23157 (P3 Metals 3) -- 0 students

# -- Tonight's auto-graded submissions --------------------------------
TONIGHT_GRADED = [
    {
        "student_id": 8384,
        "assignment": "The Exorcism of the Plasma Cutter Practice Lab",
        "score": "20/20",
        "detail": "valid file (STL)",
    },
    {
        "student_id": 21134,
        "assignment": "The Exorcism of the Plasma Cutter Practice Lab",
        "score": "20/20",
        "detail": "file upload (SVG)",
    },
    {
        "student_id": 8348,
        "assignment": "The Exorcism of the Plasma Cutter Practice Lab",
        "score": "20/20",
        "detail": "valid file (DXF)",
    },
    {
        "student_id": 20756,
        "assignment": "The Exorcism of the Plasma Cutter Practice Lab",
        "score": "20/20",
        "detail": "text entry",
    },
]


# -- Styles -------------------------------------------------------------

def _styles():
    ss = getSampleStyleSheet()
    s = {}
    s["title"] = ParagraphStyle(
        "T", parent=ss["Title"], fontSize=28, leading=34,
        textColor=C_BLUE, spaceAfter=4,
    )
    s["subtitle"] = ParagraphStyle(
        "Sub", parent=ss["Normal"], fontSize=13, leading=17,
        textColor=C_MEDIUM, alignment=TA_CENTER,
    )
    s["h1"] = ParagraphStyle(
        "H1", parent=ss["Heading1"], fontSize=16, leading=20,
        textColor=C_BLUE, spaceBefore=10, spaceAfter=6,
    )
    s["h2"] = ParagraphStyle(
        "H2", parent=ss["Heading2"], fontSize=13, leading=16,
        textColor=C_BLUE, spaceBefore=8, spaceAfter=4,
    )
    s["h3"] = ParagraphStyle(
        "H3", parent=ss["Heading3"], fontSize=11, leading=14,
        textColor=C_DARK, spaceBefore=6, spaceAfter=3,
    )
    s["body"] = ParagraphStyle(
        "B", parent=ss["Normal"], fontSize=9, leading=12,
    )
    s["body_italic"] = ParagraphStyle(
        "BI", parent=ss["Normal"], fontSize=9, leading=12,
        textColor=C_MEDIUM,
    )
    s["small"] = ParagraphStyle(
        "Sm", parent=ss["Normal"], fontSize=8, leading=10,
        textColor=C_MEDIUM,
    )
    s["cell"] = ParagraphStyle(
        "C", parent=ss["Normal"], fontSize=8, leading=10,
    )
    s["cell_center"] = ParagraphStyle(
        "CC", parent=ss["Normal"], fontSize=8, leading=10,
        alignment=TA_CENTER,
    )
    s["cell_header"] = ParagraphStyle(
        "CH", parent=ss["Normal"], fontSize=8, leading=10,
        textColor=C_WHITE, alignment=TA_CENTER,
    )
    s["cell_left_header"] = ParagraphStyle(
        "CLH", parent=ss["Normal"], fontSize=8, leading=10,
        textColor=C_WHITE,
    )
    s["metric_big"] = ParagraphStyle(
        "MB", parent=ss["Normal"], fontSize=22, leading=26,
        textColor=C_BLUE, alignment=TA_CENTER,
    )
    s["metric_label"] = ParagraphStyle(
        "ML", parent=ss["Normal"], fontSize=9, leading=11,
        textColor=C_MEDIUM, alignment=TA_CENTER,
    )
    return s


# -- Header / Footer ----------------------------------------------------

def _header_footer(canvas_obj, doc):
    canvas_obj.saveState()
    canvas_obj.setStrokeColor(C_BLUE)
    canvas_obj.setLineWidth(1)
    canvas_obj.line(0.75 * inch, 10.25 * inch, 7.75 * inch, 10.25 * inch)
    canvas_obj.setFont("Helvetica", 8)
    canvas_obj.setFillColor(C_MEDIUM)
    canvas_obj.drawString(0.75 * inch, 10.35 * inch, "Grade Status Report -- All CTE Courses")
    canvas_obj.drawRightString(7.75 * inch, 10.35 * inch, REPORT_DATE)
    canvas_obj.drawCentredString(4.25 * inch, 0.5 * inch, f"Page {doc.page}")
    canvas_obj.restoreState()


# -- Data loading -------------------------------------------------------

def load_csv(csv_path):
    """Load CSV and return list of row dicts."""
    rows = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def _parse_float(val):
    """Safely parse a float, returning None if empty or invalid."""
    if val is None or val == "":
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def _parse_bool(val):
    """Parse a boolean string from CSV."""
    if isinstance(val, bool):
        return val
    return str(val).strip().lower() == "true"


# -- Data analysis ------------------------------------------------------

def analyze_data(rows):
    """
    Analyze CSV rows into structured data for the report.
    Returns dict with course-level and student-level stats.
    """
    # Filter to only courses in our order list
    valid_courses = set(COURSE_ORDER)
    rows = [r for r in rows if r["course_name"] in valid_courses]

    # Build per-course, per-student structure
    courses = OrderedDict()
    for course_name in COURSE_ORDER:
        course_rows = [r for r in rows if r["course_name"] == course_name]
        if not course_rows:
            continue

        students = OrderedDict()
        for r in course_rows:
            sname = r["student_name"]
            if sname not in students:
                students[sname] = {
                    "canvas_id": r.get("student_canvas_id", ""),
                    "assignments": [],
                }
            score = _parse_float(r["score"])
            pts = _parse_float(r["points_possible"])
            students[sname]["assignments"].append({
                "name": r["assignment_name"],
                "score": score,
                "points_possible": pts,
                "late": _parse_bool(r.get("late", "False")),
                "missing": _parse_bool(r.get("missing", "False")),
                "workflow_state": r.get("workflow_state", ""),
            })

        # Compute per-student stats
        student_stats = OrderedDict()
        for sname, sdata in sorted(students.items()):
            asgns = sdata["assignments"]
            # "Graded" means score is not None AND points_possible > 0
            graded = [
                a for a in asgns
                if a["score"] is not None and a["points_possible"] is not None
                and a["points_possible"] > 0
            ]
            missing_count = sum(1 for a in asgns if a["missing"])
            late_count = sum(1 for a in asgns if a["late"])
            total_assignments = len(asgns)

            if graded:
                total_score = sum(a["score"] for a in graded)
                total_possible = sum(a["points_possible"] for a in graded)
                avg_pct = (total_score / total_possible) * 100 if total_possible > 0 else 0.0
            else:
                avg_pct = 0.0

            grade_letter = _pct_to_letter(avg_pct)
            at_risk = avg_pct < 60 or missing_count >= 3

            student_stats[sname] = {
                "canvas_id": sdata["canvas_id"],
                "total_assignments": total_assignments,
                "graded_count": len(graded),
                "missing": missing_count,
                "late": late_count,
                "avg_pct": avg_pct,
                "grade_letter": grade_letter,
                "at_risk": at_risk,
            }

        # Course-level summary
        all_students = list(student_stats.values())
        total_graded = sum(s["graded_count"] for s in all_students)
        total_missing = sum(s["missing"] for s in all_students)
        total_late = sum(s["late"] for s in all_students)
        if all_students:
            # Course average: weighted by actual scores
            all_graded_asgns = []
            for sdata in students.values():
                for a in sdata["assignments"]:
                    if (a["score"] is not None and a["points_possible"] is not None
                            and a["points_possible"] > 0):
                        all_graded_asgns.append(a)
            if all_graded_asgns:
                course_avg = (
                    sum(a["score"] for a in all_graded_asgns)
                    / sum(a["points_possible"] for a in all_graded_asgns)
                    * 100
                )
            else:
                course_avg = 0.0
        else:
            course_avg = 0.0

        courses[course_name] = {
            "student_count": len(student_stats),
            "graded_submissions": total_graded,
            "missing_count": total_missing,
            "late_count": total_late,
            "avg_pct": course_avg,
            "students": student_stats,
        }

    return courses


def _pct_to_letter(pct):
    """Convert percentage to letter grade."""
    if pct >= 90:
        return "A"
    elif pct >= 80:
        return "B"
    elif pct >= 70:
        return "C"
    elif pct >= 60:
        return "D"
    else:
        return "F"


def _grade_distribution(students):
    """Count A/B/C/D/F from student averages."""
    dist = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
    for s in students.values():
        dist[s["grade_letter"]] += 1
    return dist


# -- PDF Construction ----------------------------------------------------

def build_pdf(output_path, courses):
    sty = _styles()
    elements = []

    # Compute global stats
    total_students = sum(c["student_count"] for c in courses.values())
    total_graded = sum(c["graded_submissions"] for c in courses.values())
    total_missing = sum(c["missing_count"] for c in courses.values())
    total_late = sum(c["late_count"] for c in courses.values())

    # Overall weighted average
    all_scores = 0.0
    all_possible = 0.0
    for cdata in courses.values():
        for sdata_dict in [cdata["students"]]:
            # We need original assignment data, but we only stored stats.
            # Recompute from stored avg: use weighted average across courses.
            pass
    # Simpler: weighted average of course averages by student count
    weighted_sum = sum(c["avg_pct"] * c["student_count"] for c in courses.values())
    if total_students > 0:
        overall_avg = weighted_sum / total_students
    else:
        overall_avg = 0.0

    # ================================================================
    # COVER PAGE
    # ================================================================
    elements.append(Spacer(1, 1.8 * inch))
    elements.append(Paragraph("Grade Status Report", sty["title"]))
    elements.append(Spacer(1, 0.15 * inch))
    elements.append(Paragraph(
        f"All CTE Courses -- {REPORT_DATE}", sty["subtitle"]
    ))
    elements.append(Spacer(1, 0.1 * inch))
    elements.append(Paragraph(
        "CTE Metals &amp; Engines, Bend-La Pine Schools", sty["subtitle"]
    ))
    elements.append(Spacer(1, 0.1 * inch))
    elements.append(Paragraph("Instructor: Andrew McAteer", sty["subtitle"]))
    elements.append(Spacer(1, 0.5 * inch))

    # Cover metrics box
    metrics_data = [
        [
            Paragraph(f"<b>{total_students}</b>", sty["metric_big"]),
            Paragraph(f"<b>{total_graded}</b>", sty["metric_big"]),
            Paragraph(f"<b>{overall_avg:.0f}%</b>", sty["metric_big"]),
            Paragraph(f"<b>{total_missing}</b>", sty["metric_big"]),
            Paragraph(f"<b>{total_late}</b>", sty["metric_big"]),
        ],
        [
            Paragraph("Total Students", sty["metric_label"]),
            Paragraph("Graded Submissions", sty["metric_label"]),
            Paragraph("Overall Average", sty["metric_label"]),
            Paragraph("Missing", sty["metric_label"]),
            Paragraph("Late", sty["metric_label"]),
        ],
    ]
    mt = Table(metrics_data, colWidths=[1.3 * inch] * 5)
    mt.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOX", (0, 0), (-1, -1), 0.5, C_BLUE),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8F9FA")),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 8),
    ]))
    elements.append(mt)
    elements.append(Spacer(1, 0.5 * inch))

    elements.append(Paragraph(
        f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
        sty["subtitle"],
    ))
    elements.append(PageBreak())

    # ================================================================
    # DEPARTMENT OVERVIEW
    # ================================================================
    elements.append(Paragraph("Department Overview", sty["h1"]))
    elements.append(Spacer(1, 0.15 * inch))

    header = [
        Paragraph("<b>Course</b>", sty["cell_left_header"]),
        Paragraph("<b>Students</b>", sty["cell_header"]),
        Paragraph("<b>Graded</b>", sty["cell_header"]),
        Paragraph("<b>Missing</b>", sty["cell_header"]),
        Paragraph("<b>Late</b>", sty["cell_header"]),
        Paragraph("<b>Avg %</b>", sty["cell_header"]),
    ]
    rows_table = [header]
    ts = [
        ("BACKGROUND", (0, 0), (-1, 0), C_BLUE),
        ("TEXTCOLOR", (0, 0), (-1, 0), C_WHITE),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E0E0E0")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
    ]

    for i, (cname, cdata) in enumerate(courses.items()):
        row_idx = i + 1
        avg = cdata["avg_pct"]
        # Color-code average
        if avg >= 80:
            avg_color = C_GREEN.hexval()
        elif avg >= 60:
            avg_color = C_AMBER.hexval()
        else:
            avg_color = C_RED.hexval()

        rows_table.append([
            Paragraph(cname, sty["cell"]),
            Paragraph(str(cdata["student_count"]), sty["cell_center"]),
            Paragraph(str(cdata["graded_submissions"]), sty["cell_center"]),
            Paragraph(str(cdata["missing_count"]), sty["cell_center"]),
            Paragraph(str(cdata["late_count"]), sty["cell_center"]),
            Paragraph(
                f'<font color="{avg_color}"><b>{avg:.1f}%</b></font>',
                sty["cell_center"],
            ),
        ])
        if row_idx % 2 == 0:
            ts.append(("BACKGROUND", (0, row_idx), (-1, row_idx), C_LIGHT_GRAY))

    # Totals row
    rows_table.append([
        Paragraph("<b>TOTAL</b>", sty["cell"]),
        Paragraph(f"<b>{total_students}</b>", sty["cell_center"]),
        Paragraph(f"<b>{total_graded}</b>", sty["cell_center"]),
        Paragraph(f"<b>{total_missing}</b>", sty["cell_center"]),
        Paragraph(f"<b>{total_late}</b>", sty["cell_center"]),
        Paragraph(f"<b>{overall_avg:.1f}%</b>", sty["cell_center"]),
    ])
    totals_idx = len(rows_table) - 1
    ts.append(("BACKGROUND", (0, totals_idx), (-1, totals_idx), C_LIGHT_BLUE))
    ts.append(("LINEABOVE", (0, totals_idx), (-1, totals_idx), 1, C_BLUE))

    overview_table = Table(
        rows_table,
        colWidths=[2.2 * inch, 0.8 * inch, 0.8 * inch, 0.8 * inch, 0.8 * inch, 0.9 * inch],
    )
    overview_table.setStyle(TableStyle(ts))
    elements.append(overview_table)
    elements.append(PageBreak())

    # ================================================================
    # GRADE DISTRIBUTION
    # ================================================================
    elements.append(Paragraph("Grade Distribution by Course", sty["h1"]))
    elements.append(Spacer(1, 0.15 * inch))
    elements.append(Paragraph(
        "Letter grades derived from each student's weighted average across all "
        "graded submissions. A = 90-100%, B = 80-89%, C = 70-79%, D = 60-69%, F = below 60%.",
        sty["body"],
    ))
    elements.append(Spacer(1, 0.15 * inch))

    dist_header = [
        Paragraph("<b>Course</b>", sty["cell_left_header"]),
        Paragraph("<b>A</b>", sty["cell_header"]),
        Paragraph("<b>B</b>", sty["cell_header"]),
        Paragraph("<b>C</b>", sty["cell_header"]),
        Paragraph("<b>D</b>", sty["cell_header"]),
        Paragraph("<b>F</b>", sty["cell_header"]),
        Paragraph("<b>Total</b>", sty["cell_header"]),
    ]
    dist_rows = [dist_header]
    dist_ts = [
        ("BACKGROUND", (0, 0), (-1, 0), C_BLUE),
        ("TEXTCOLOR", (0, 0), (-1, 0), C_WHITE),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E0E0E0")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
    ]

    total_dist = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
    for i, (cname, cdata) in enumerate(courses.items()):
        row_idx = i + 1
        dist = _grade_distribution(cdata["students"])
        for grade_ltr in total_dist:
            total_dist[grade_ltr] += dist[grade_ltr]
        dist_rows.append([
            Paragraph(cname, sty["cell"]),
            Paragraph(str(dist["A"]), sty["cell_center"]),
            Paragraph(str(dist["B"]), sty["cell_center"]),
            Paragraph(str(dist["C"]), sty["cell_center"]),
            Paragraph(str(dist["D"]), sty["cell_center"]),
            Paragraph(str(dist["F"]), sty["cell_center"]),
            Paragraph(str(sum(dist.values())), sty["cell_center"]),
        ])
        if row_idx % 2 == 0:
            dist_ts.append(("BACKGROUND", (0, row_idx), (-1, row_idx), C_LIGHT_GRAY))

    # Totals row
    dist_rows.append([
        Paragraph("<b>TOTAL</b>", sty["cell"]),
        Paragraph(f"<b>{total_dist['A']}</b>", sty["cell_center"]),
        Paragraph(f"<b>{total_dist['B']}</b>", sty["cell_center"]),
        Paragraph(f"<b>{total_dist['C']}</b>", sty["cell_center"]),
        Paragraph(f"<b>{total_dist['D']}</b>", sty["cell_center"]),
        Paragraph(f"<b>{total_dist['F']}</b>", sty["cell_center"]),
        Paragraph(f"<b>{sum(total_dist.values())}</b>", sty["cell_center"]),
    ])
    totals_idx = len(dist_rows) - 1
    dist_ts.append(("BACKGROUND", (0, totals_idx), (-1, totals_idx), C_LIGHT_BLUE))
    dist_ts.append(("LINEABOVE", (0, totals_idx), (-1, totals_idx), 1, C_BLUE))

    dist_table = Table(
        dist_rows,
        colWidths=[2.2 * inch, 0.7 * inch, 0.7 * inch, 0.7 * inch, 0.7 * inch, 0.7 * inch, 0.7 * inch],
    )
    dist_table.setStyle(TableStyle(dist_ts))
    elements.append(dist_table)
    elements.append(PageBreak())

    # ================================================================
    # PER-STUDENT DETAIL (one section per course)
    # ================================================================
    elements.append(Paragraph("Per-Student Detail", sty["h1"]))
    elements.append(Spacer(1, 0.1 * inch))

    for cname, cdata in courses.items():
        info = COURSE_INFO.get(cname, {})
        period = info.get("period", "")
        section = info.get("section", "")
        course_id = info.get("course_id", "")

        elements.append(Paragraph(cname, sty["h2"]))
        elements.append(Paragraph(
            f'{period}  |  {section}  |  Canvas ID: {course_id}',
            sty["body_italic"],
        ))
        elements.append(Spacer(1, 0.1 * inch))

        # Student detail table
        stu_header = [
            Paragraph("<b>Student</b>", sty["cell_left_header"]),
            Paragraph("<b>Graded</b>", sty["cell_header"]),
            Paragraph("<b>Avg %</b>", sty["cell_header"]),
            Paragraph("<b>Missing</b>", sty["cell_header"]),
            Paragraph("<b>Late</b>", sty["cell_header"]),
            Paragraph("<b>Grade</b>", sty["cell_header"]),
        ]
        stu_rows = [stu_header]
        stu_ts = [
            ("BACKGROUND", (0, 0), (-1, 0), C_BLUE),
            ("TEXTCOLOR", (0, 0), (-1, 0), C_WHITE),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E0E0E0")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ]

        for i, (sname, sdata) in enumerate(cdata["students"].items()):
            row_idx = i + 1
            avg = sdata["avg_pct"]

            # Color code average
            if avg >= 80:
                avg_color = C_GREEN.hexval()
            elif avg >= 60:
                avg_color = C_AMBER.hexval()
            else:
                avg_color = C_RED.hexval()

            stu_rows.append([
                Paragraph(sname, sty["cell"]),
                Paragraph(str(sdata["graded_count"]), sty["cell_center"]),
                Paragraph(
                    f'<font color="{avg_color}"><b>{avg:.1f}%</b></font>',
                    sty["cell_center"],
                ),
                Paragraph(str(sdata["missing"]), sty["cell_center"]),
                Paragraph(str(sdata["late"]), sty["cell_center"]),
                Paragraph(sdata["grade_letter"], sty["cell_center"]),
            ])

            # At-risk highlight
            if sdata["at_risk"]:
                stu_ts.append(
                    ("BACKGROUND", (0, row_idx), (-1, row_idx), C_LIGHT_RED)
                )
            elif row_idx % 2 == 0:
                stu_ts.append(
                    ("BACKGROUND", (0, row_idx), (-1, row_idx), C_LIGHT_GRAY)
                )

        stu_table = Table(
            stu_rows,
            colWidths=[2.3 * inch, 0.7 * inch, 0.8 * inch, 0.8 * inch, 0.7 * inch, 0.7 * inch],
        )
        stu_table.setStyle(TableStyle(stu_ts))
        elements.append(stu_table)
        elements.append(Spacer(1, 0.2 * inch))

    elements.append(PageBreak())

    # ================================================================
    # TONIGHT'S GRADING ACTIVITY
    # ================================================================
    elements.append(Paragraph("Tonight's Grading Activity", sty["h1"]))
    elements.append(Spacer(1, 0.1 * inch))
    elements.append(Paragraph(
        "The following 4 submissions were auto-graded tonight (February 24, 2026). "
        "Each was awarded full credit after validating the submission type.",
        sty["body"],
    ))
    elements.append(Spacer(1, 0.15 * inch))

    # Look up student names from course data
    all_students_by_id = {}
    for cdata in courses.values():
        for sname, sdata in cdata["students"].items():
            cid = sdata.get("canvas_id", "")
            if cid:
                try:
                    all_students_by_id[int(cid)] = sname
                except (ValueError, TypeError):
                    pass

    tonight_header = [
        Paragraph("<b>Student</b>", sty["cell_left_header"]),
        Paragraph("<b>Assignment</b>", sty["cell_left_header"]),
        Paragraph("<b>Score</b>", sty["cell_header"]),
        Paragraph("<b>Submission Type</b>", sty["cell_left_header"]),
    ]
    tonight_rows = [tonight_header]
    tonight_ts = [
        ("BACKGROUND", (0, 0), (-1, 0), C_BLUE),
        ("TEXTCOLOR", (0, 0), (-1, 0), C_WHITE),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E0E0E0")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("ALIGN", (2, 0), (2, -1), "CENTER"),
    ]

    for i, tg in enumerate(TONIGHT_GRADED):
        row_idx = i + 1
        sname = all_students_by_id.get(tg["student_id"], f"Student {tg['student_id']}")
        tonight_rows.append([
            Paragraph(sname, sty["cell"]),
            Paragraph(tg["assignment"], sty["cell"]),
            Paragraph(tg["score"], sty["cell_center"]),
            Paragraph(tg["detail"], sty["cell"]),
        ])
        if row_idx % 2 == 0:
            tonight_ts.append(
                ("BACKGROUND", (0, row_idx), (-1, row_idx), C_LIGHT_GREEN)
            )
        else:
            tonight_ts.append(
                ("BACKGROUND", (0, row_idx), (-1, row_idx), colors.HexColor("#F1F8E9"))
            )

    tonight_table = Table(
        tonight_rows,
        colWidths=[1.5 * inch, 2.7 * inch, 0.7 * inch, 1.4 * inch],
    )
    tonight_table.setStyle(TableStyle(tonight_ts))
    elements.append(tonight_table)
    elements.append(PageBreak())

    # ================================================================
    # AT-RISK STUDENTS SUMMARY
    # ================================================================
    elements.append(Paragraph("At-Risk Students", sty["h1"]))
    elements.append(Spacer(1, 0.1 * inch))
    elements.append(Paragraph(
        "Students flagged as at-risk have either an average below 60% OR "
        "3 or more missing assignments. These students may need additional "
        "outreach or intervention.",
        sty["body"],
    ))
    elements.append(Spacer(1, 0.15 * inch))

    risk_header = [
        Paragraph("<b>Course</b>", sty["cell_left_header"]),
        Paragraph("<b>Student</b>", sty["cell_left_header"]),
        Paragraph("<b>Avg %</b>", sty["cell_header"]),
        Paragraph("<b>Missing</b>", sty["cell_header"]),
        Paragraph("<b>Concern</b>", sty["cell_left_header"]),
    ]
    risk_rows = [risk_header]
    risk_ts = [
        ("BACKGROUND", (0, 0), (-1, 0), C_RED),
        ("TEXTCOLOR", (0, 0), (-1, 0), C_WHITE),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E0E0E0")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("ALIGN", (2, 0), (3, -1), "CENTER"),
    ]

    risk_count = 0
    for cname, cdata in courses.items():
        for sname, sdata in cdata["students"].items():
            if sdata["at_risk"]:
                risk_count += 1
                concerns = []
                if sdata["avg_pct"] < 60:
                    concerns.append(f"Avg {sdata['avg_pct']:.0f}% (below 60%)")
                if sdata["missing"] >= 3:
                    concerns.append(f"{sdata['missing']} missing assignments")
                concern_str = "; ".join(concerns)

                risk_rows.append([
                    Paragraph(cname, sty["cell"]),
                    Paragraph(sname, sty["cell"]),
                    Paragraph(f"{sdata['avg_pct']:.1f}%", sty["cell_center"]),
                    Paragraph(str(sdata["missing"]), sty["cell_center"]),
                    Paragraph(concern_str, sty["cell"]),
                ])
                row_idx = len(risk_rows) - 1
                risk_ts.append(
                    ("BACKGROUND", (0, row_idx), (-1, row_idx), C_LIGHT_RED)
                )

    if risk_count == 0:
        elements.append(Paragraph(
            "No students currently meet at-risk criteria.", sty["body"]
        ))
    else:
        elements.append(Paragraph(
            f"<b>{risk_count} student(s)</b> flagged across all courses.",
            sty["body"],
        ))
        elements.append(Spacer(1, 0.1 * inch))

        risk_table = Table(
            risk_rows,
            colWidths=[1.3 * inch, 1.5 * inch, 0.7 * inch, 0.7 * inch, 2.1 * inch],
        )
        risk_table.setStyle(TableStyle(risk_ts))
        elements.append(risk_table)

    # ================================================================
    # BUILD
    # ================================================================
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=1 * inch,
        bottomMargin=0.75 * inch,
    )
    doc.build(elements, onFirstPage=_header_footer, onLaterPages=_header_footer)
    print(f"\n  PDF saved: {output_path}")
    print(f"  Courses: {len(courses)}")
    print(f"  Students: {total_students}")
    print(f"  At-risk: {risk_count}")


if __name__ == "__main__":
    print("Loading CSV data...")
    raw_rows = load_csv(CSV_PATH)
    print(f"  Loaded {len(raw_rows)} rows")

    print("Analyzing grade data...")
    courses = analyze_data(raw_rows)

    output = os.path.expanduser("~/Downloads/grade_report_2026-02-24.pdf")
    print(f"Building PDF report...")
    build_pdf(output, courses)
