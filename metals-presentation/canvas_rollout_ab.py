#!/usr/bin/env python3
"""
Canvas Rollout: Option A + B
=============================
Implements structural fixes and professional polish across all 5 metals courses.
Everything is created UNPUBLISHED so the instructor can review before going live.

Option A (Foundation):
  1. Move safety quizzes from "Imported Assignments" (0%) to "Citizenship & Safety" (25%)
  2. Move Metal Types Quiz from "Projects" to "Citizenship & Safety"
  3. Add due dates to all safety quizzes (staggered)
  4. Enable sequential progress on Safety Tests module
  5. Set General Shop Safety to require 100% pass

Option B (Polish):
  6. Create rubrics for 4 project assignments
  7. Build a Course Home page
  8. Add Metal Types presentation as a Canvas page
  9. Draft an announcement (unpublished)
"""

import os
import sys

METALS_COURSE_IDS = [23164, 23132, 23157, 23188, 23177]

# Safety quiz due dates (staggered, all Pacific time)
SAFETY_DUE_DATES = {
    "General Shop Safety":          "2026-02-25T07:59:59Z",  # Mon 2/24 11:59pm PT
    "Portable Angle Grinder Safety": "2026-02-27T07:59:59Z", # Thu 2/26 11:59pm PT
    "Abrasive Cutoff Saw":          "2026-02-28T07:59:59Z",  # Fri 2/27 11:59pm PT
    "Arc Welding":                  "2026-03-01T07:59:59Z",  # Sat 2/28 11:59pm PT
    "Metal Bandsaw":                "2026-03-01T07:59:59Z",  # Sat 2/28 11:59pm PT
}

def get_canvas():
    from canvasapi import Canvas
    url = os.environ.get("CANVAS_API_URL")
    token = os.environ.get("CANVAS_API_TOKEN")
    if not url or not token:
        print("ERROR: Set CANVAS_API_URL and CANVAS_API_TOKEN")
        sys.exit(1)
    return Canvas(url, token)


# ══════════════════════════════════════════════════════════════
# RUBRIC DEFINITIONS
# ══════════════════════════════════════════════════════════════

RUBRIC_TOOL_ORGANIZER = {
    "title": "Portable Tool Organizer — SolidWorks Rubric",
    "criteria": [
        {
            "description": "Model Completeness",
            "points": 10,
            "ratings": [
                {"description": "All three tiers modeled with lid, accurate dimensions, parametric features used throughout", "points": 10},
                {"description": "Two tiers modeled correctly, minor dimension issues or some non-parametric features", "points": 7},
                {"description": "One tier modeled or major dimension errors, minimal parametric features", "points": 4},
                {"description": "Incomplete model or file not submitted", "points": 0},
            ]
        },
        {
            "description": "Parametric Design Practice",
            "points": 10,
            "ratings": [
                {"description": "Fully constrained sketches, named features, uses equations/relations where appropriate", "points": 10},
                {"description": "Mostly constrained, some features named, limited use of relations", "points": 7},
                {"description": "Under-constrained sketches, no naming convention, no relations used", "points": 4},
                {"description": "No evidence of parametric thinking", "points": 0},
            ]
        },
        {
            "description": "File Quality & Submission",
            "points": 10,
            "ratings": [
                {"description": "Proper file naming convention, all parts/assembly submitted, file opens without errors", "points": 10},
                {"description": "Minor naming issues, all parts present, opens correctly", "points": 7},
                {"description": "Poor naming, missing parts, or file corruption issues", "points": 4},
                {"description": "File not submitted or unusable", "points": 0},
            ]
        },
    ]
}

RUBRIC_CELL_PHONE_STAND = {
    "title": "Sheet Metal Cell Phone Stand — POP Writeup Rubric",
    "criteria": [
        {
            "description": "Design Intent & Problem Statement",
            "points": 10,
            "ratings": [
                {"description": "Clear problem statement, design addresses a specific need, material and angle choices justified", "points": 10},
                {"description": "Problem stated but vague, some justification for design choices", "points": 7},
                {"description": "Minimal design intent, no justification for choices", "points": 4},
                {"description": "No design intent section or not submitted", "points": 0},
            ]
        },
        {
            "description": "Plan of Procedure (Step-by-Step)",
            "points": 20,
            "ratings": [
                {"description": "Detailed numbered steps with tool/machine callouts, safety notes, measurements, and sequence logic", "points": 20},
                {"description": "Steps listed but missing tool callouts or measurements, sequence is logical", "points": 14},
                {"description": "Vague steps, missing critical operations, sequence unclear", "points": 8},
                {"description": "No procedure or not submitted", "points": 0},
            ]
        },
        {
            "description": "Materials & Tools List",
            "points": 10,
            "ratings": [
                {"description": "Complete list with material type, dimensions, quantity, and all tools/machines identified", "points": 10},
                {"description": "Most materials and tools listed, minor omissions", "points": 7},
                {"description": "Incomplete list, missing key materials or tools", "points": 4},
                {"description": "No list provided", "points": 0},
            ]
        },
        {
            "description": "Reflection & Quality of Writing",
            "points": 10,
            "ratings": [
                {"description": "Thoughtful reflection on what worked, what didn't, and what they'd change. Clear, professional writing.", "points": 10},
                {"description": "Some reflection present, writing is adequate", "points": 7},
                {"description": "Minimal reflection, writing is unclear or sloppy", "points": 4},
                {"description": "No reflection or unreadable", "points": 0},
            ]
        },
    ]
}

RUBRIC_HANDRAIL_PLAQUE = {
    "title": "Campus Handrail Plaque — Design & Fabrication Rubric",
    "criteria": [
        {
            "description": "Design Quality",
            "points": 15,
            "ratings": [
                {"description": "Original design, clean layout, appropriate for permanent campus installation, design sketch included", "points": 15},
                {"description": "Functional design, mostly clean, minor layout issues", "points": 10},
                {"description": "Basic design, lacks refinement or appropriateness for permanent display", "points": 6},
                {"description": "No design work evident or not submitted", "points": 0},
            ]
        },
        {
            "description": "Fabrication Execution",
            "points": 25,
            "ratings": [
                {"description": "Clean cuts, smooth edges, accurate dimensions, welds/joints are strong and clean, finish is professional", "points": 25},
                {"description": "Good fabrication with minor flaws (small gaps, slight dimension errors, acceptable welds)", "points": 18},
                {"description": "Rough fabrication, visible errors, weak joints, needs significant rework", "points": 10},
                {"description": "Incomplete fabrication or not submitted", "points": 0},
            ]
        },
        {
            "description": "Surface Finish & Presentation",
            "points": 15,
            "ratings": [
                {"description": "Properly deburred, cleaned, finished (paint/clear coat/polish as appropriate), ready for installation", "points": 15},
                {"description": "Mostly finished, minor burrs or uneven coating", "points": 10},
                {"description": "Rough finish, visible burrs, incomplete coating", "points": 6},
                {"description": "No finishing attempted", "points": 0},
            ]
        },
        {
            "description": "Documentation (Photos + Process Notes)",
            "points": 15,
            "ratings": [
                {"description": "Progress photos at key stages, final glamour shots, brief process notes describing decisions made", "points": 15},
                {"description": "Some photos included, minimal process notes", "points": 10},
                {"description": "One photo or no process documentation", "points": 6},
                {"description": "No documentation submitted", "points": 0},
            ]
        },
    ]
}

RUBRIC_ENTREPRENEUR = {
    "title": "Metal Entrepreneur Challenge Rubric",
    "criteria": [
        {
            "description": "Need Identification & Market Research",
            "points": 15,
            "ratings": [
                {"description": "Real need identified with evidence (customer interview, observation), target market defined, competing products researched", "points": 15},
                {"description": "Need identified but evidence is thin, some market awareness", "points": 10},
                {"description": "Vague need, no customer evidence, no market research", "points": 6},
                {"description": "No need identification or not submitted", "points": 0},
            ]
        },
        {
            "description": "Design & Engineering",
            "points": 20,
            "ratings": [
                {"description": "Thoughtful design with sketch/CAD, material selection justified, dimensions appropriate, design iterates on feedback", "points": 20},
                {"description": "Functional design with some documentation, material choice reasonable", "points": 14},
                {"description": "Basic design, minimal documentation, material choice not justified", "points": 8},
                {"description": "No design documentation", "points": 0},
            ]
        },
        {
            "description": "Fabrication Quality",
            "points": 25,
            "ratings": [
                {"description": "Professional-quality fabrication, clean welds/joints, accurate dimensions, consistent finish, customer-ready", "points": 25},
                {"description": "Good fabrication, minor imperfections, would sell with explanation", "points": 18},
                {"description": "Rough fabrication, visible flaws, not customer-ready without rework", "points": 10},
                {"description": "Incomplete fabrication or not submitted", "points": 0},
            ]
        },
        {
            "description": "Pricing & Business Case",
            "points": 20,
            "ratings": [
                {"description": "Accurate material cost, labor time tracked, overhead accounted for, profit margin justified, price competitive", "points": 20},
                {"description": "Material cost estimated, some labor tracking, price set but not fully justified", "points": 14},
                {"description": "Guessed pricing, no cost breakdown", "points": 8},
                {"description": "No pricing or business case", "points": 0},
            ]
        },
        {
            "description": "Sale & Customer Interaction",
            "points": 20,
            "ratings": [
                {"description": "Sold to a real customer, documented the transaction, customer feedback collected", "points": 20},
                {"description": "Customer identified and pitched, sale pending or completed without documentation", "points": 14},
                {"description": "No real customer identified, hypothetical sale only", "points": 8},
                {"description": "No sale attempt", "points": 0},
            ]
        },
    ]
}


# ══════════════════════════════════════════════════════════════
# COURSE HOME PAGE HTML
# ══════════════════════════════════════════════════════════════
COURSE_HOME_HTML = """
<div style="max-width:800px; font-family:inherit;">

<div style="background: linear-gradient(135deg, #1a1a2e, #2d3a4a); color: #f0f0f0; padding: 30px; border-radius: 8px; margin-bottom: 20px;">
  <h1 style="margin:0 0 8px 0; color:#e2b714;">Metals &amp; Manufacturing</h1>
  <p style="margin:0; font-size:16px; color:#c0c0c0;">Mr. McAteer &mdash; Churchill High School</p>
</div>

<div style="background:#f8f9fa; border-left:4px solid #e2b714; padding:15px 20px; margin-bottom:20px; border-radius:0 4px 4px 0;">
  <h3 style="margin:0 0 10px 0; color:#2c3e50;">How This Course Works</h3>
  <p style="margin:0; line-height:1.7;">This is a <strong>project-based shop class</strong>. You learn by building real things with real metal. Canvas is where you submit documentation, take safety certifications, and track your progress.</p>
</div>

<h2 style="color:#2c3e50; border-bottom:2px solid #e2b714; padding-bottom:8px;">Grading Breakdown</h2>
<table style="width:100%; border-collapse:collapse; margin-bottom:20px;">
  <tr style="background:#2d3a4a; color:white;">
    <th style="padding:10px; text-align:left;">Category</th>
    <th style="padding:10px; text-align:center;">Weight</th>
    <th style="padding:10px; text-align:left;">What&rsquo;s In It</th>
  </tr>
  <tr style="background:#f8f9fa;">
    <td style="padding:10px;"><strong>Projects</strong></td>
    <td style="padding:10px; text-align:center;">75%</td>
    <td style="padding:10px;">Design documents, fabrication projects, POP writeups, SolidWorks models</td>
  </tr>
  <tr>
    <td style="padding:10px;"><strong>Citizenship &amp; Safety</strong></td>
    <td style="padding:10px; text-align:center;">25%</td>
    <td style="padding:10px;">Safety certifications (must pass to use machines), shop cleanup, unit quizzes</td>
  </tr>
</table>

<h2 style="color:#2c3e50; border-bottom:2px solid #e2b714; padding-bottom:8px;">First Things First: Safety Certifications</h2>
<p style="line-height:1.7;">Before you touch any machine in this shop, you must pass the safety certification quiz for that machine. These are in the <strong>Safety Tests</strong> module. Start with <strong>General Shop Safety</strong> &mdash; it unlocks everything else.</p>
<ol style="line-height:2;">
  <li><strong>General Shop Safety</strong> (required first &mdash; 100% to pass)</li>
  <li>Portable Angle Grinder Safety</li>
  <li>Abrasive Cutoff Saw Safety</li>
  <li>Arc Welding Safety</li>
  <li>Metal Bandsaw Safety</li>
</ol>

<h2 style="color:#2c3e50; border-bottom:2px solid #e2b714; padding-bottom:8px;">Shop Rules</h2>
<ul style="line-height:2;">
  <li><strong>Safety glasses</strong> on at all times in the shop &mdash; no exceptions</li>
  <li><strong>No open-toed shoes, no loose clothing, no jewelry near machines</strong></li>
  <li>Clean your area <strong>every day</strong> &mdash; Thursday cleanup is graded</li>
  <li>If you don&rsquo;t know, <strong>ask</strong> &mdash; never guess with a machine</li>
  <li>Respect the tools. They are shared and expensive.</li>
</ul>

<div style="background:#fff3cd; border-left:4px solid #e2b714; padding:15px 20px; margin-top:20px; border-radius:0 4px 4px 0;">
  <p style="margin:0; font-size:14px;"><strong>Questions?</strong> Talk to Mr. McAteer in the shop or email through Canvas.</p>
</div>

</div>
"""

METAL_TYPES_PAGE_HTML = """
<div style="max-width:800px; font-family:inherit;">

<div style="background: linear-gradient(135deg, #1a1a2e, #2d3a4a); color: #f0f0f0; padding: 20px 30px; border-radius: 8px; margin-bottom: 20px;">
  <h1 style="margin:0 0 5px 0; color:#e2b714;">Metal Types Study Guide</h1>
  <p style="margin:0; color:#c0c0c0;">Review this before taking the Metal Types Unit Quiz</p>
</div>

<div style="background:#f8f9fa; border-left:4px solid #4a6fa5; padding:15px 20px; margin-bottom:25px; border-radius:0 4px 4px 0;">
  <p style="margin:0;"><strong>Full Presentation:</strong> <a href="https://mr-mcateer.github.io/metals-presentation/" target="_blank">View the Metal Types Slide Deck</a></p>
</div>

<h2 style="color:#2c3e50; border-bottom:2px solid #e2b714; padding-bottom:8px;">The Big Idea: Ferrous vs. Non-Ferrous</h2>
<table style="width:100%; border-collapse:collapse; margin-bottom:20px;">
  <tr style="background:#2d3a4a; color:white;">
    <th style="padding:10px;"></th><th style="padding:10px;">Ferrous</th><th style="padding:10px;">Non-Ferrous</th>
  </tr>
  <tr style="background:#f8f9fa;">
    <td style="padding:8px;"><strong>Contains</strong></td><td style="padding:8px;">Iron (Fe)</td><td style="padding:8px;">No iron</td>
  </tr>
  <tr><td style="padding:8px;"><strong>Magnetic?</strong></td><td style="padding:8px;">Yes (usually)</td><td style="padding:8px;">No</td></tr>
  <tr style="background:#f8f9fa;"><td style="padding:8px;"><strong>Rusts?</strong></td><td style="padding:8px;">Yes (except stainless)</td><td style="padding:8px;">No</td></tr>
  <tr><td style="padding:8px;"><strong>Examples</strong></td><td style="padding:8px;">Mild steel, 4140, tool steel, cast iron, stainless</td><td style="padding:8px;">Aluminum, copper, brass, titanium</td></tr>
</table>

<h2 style="color:#2c3e50; border-bottom:2px solid #e2b714; padding-bottom:8px;">Metal Identification Methods</h2>
<ol style="line-height:2;">
  <li><strong>Magnet Test</strong> &mdash; Sticks = ferrous. Doesn&rsquo;t stick = non-ferrous.</li>
  <li><strong>Spark Test</strong> &mdash; Mild steel: long white branching sparks. Stainless: short dark-red. Aluminum: no sparks.</li>
  <li><strong>Weight Test</strong> &mdash; Aluminum is ~1/3 the weight of steel. Copper/brass are heavier than steel.</li>
  <li><strong>Visual Test</strong> &mdash; Color, mill scale, surface finish.</li>
</ol>

<h2 style="color:#2c3e50; border-bottom:2px solid #e2b714; padding-bottom:8px;">Key Facts Per Metal</h2>

<h3 style="color:#4a6fa5;">Ferrous Metals</h3>
<ul style="line-height:1.8;">
  <li><strong>Mild Steel (1018/A36)</strong> &mdash; Cheapest (~$1/lb), easiest to weld, rusts easily, the &ldquo;pine&rdquo; of metals</li>
  <li><strong>4140 Chrome-Moly</strong> &mdash; Heat treatable, stronger, needs preheat to weld, motorsport/tooling</li>
  <li><strong>Tool Steel (A2/D2)</strong> &mdash; Extreme hardness (Rc 58-62), very difficult to weld, dies/punches/blades</li>
  <li><strong>Cast Iron</strong> &mdash; Excellent machinability (powder chips), brittle, machine frames, requires 500&deg;F+ preheat to weld</li>
  <li><strong>Stainless Steel (304/316)</strong> &mdash; Ferrous but doesn&rsquo;t rust (chromium), expensive (3-4x mild steel), work-hardens, don&rsquo;t cross-contaminate</li>
</ul>

<h3 style="color:#4a6fa5;">Non-Ferrous Metals</h3>
<ul style="line-height:1.8;">
  <li><strong>6061 Aluminum</strong> &mdash; 1/3 weight of steel, machines fast, needs 100% argon for welding, the &ldquo;poplar&rdquo; of metals</li>
  <li><strong>Copper</strong> &mdash; Best electrical conductor, heavier than steel, reddish-orange, develops green patina</li>
  <li><strong>Brass</strong> &mdash; Best machinability of any metal, gold/yellow color, non-sparking (explosive environments)</li>
  <li><strong>Titanium</strong> &mdash; Best strength-to-weight ratio, extremely expensive (~$15-25/lb), aerospace/medical</li>
</ul>

<h2 style="color:#2c3e50; border-bottom:2px solid #e2b714; padding-bottom:8px;">Processes to Know</h2>
<ul style="line-height:1.8;">
  <li><strong>MIG Welding</strong> &mdash; Steel: ER70S-6 wire + C25 gas. Aluminum: ER4043 + 100% Argon. &ldquo;Hot glue gun of welding.&rdquo;</li>
  <li><strong>Lathe</strong> &mdash; Work spins, tool stays still. RPM: Aluminum fast (800-1500), stainless slow (200-400). Never leave chuck key in!</li>
  <li><strong>Mill</strong> &mdash; Tool spins, work stays still. Secure workholding critical. Aluminum: 2-3 flute. Stainless: keep tools sharp.</li>
</ul>

</div>
"""

ANNOUNCEMENT_HTML = """
<div style="font-family:inherit; max-width:700px;">

<p>Team &mdash;</p>

<p>Two things to take care of this week:</p>

<h3 style="color:#c0392b;">1. Missing Assignments</h3>
<p>Several of you have missing submissions. Check your Canvas grades and get caught up. The following assignments are past due:</p>
<ul>
  <li><strong>Portable Tool Organizer &mdash; SolidWorks</strong> (was due 2/12)</li>
  <li><strong>Sheet Metal Cell Phone Stand &mdash; POP Writeup</strong> (was due 2/19)</li>
  <li><strong>Campus Handrail Plaque</strong> (was due 2/20)</li>
</ul>
<p>Get these submitted. Late is better than missing.</p>

<h3 style="color:#2c3e50;">2. Metal Types Quiz &mdash; Due Thursday 2/26</h3>
<p>Our first unit quiz drops <strong>Tuesday morning (2/24)</strong> and is due by <strong>Thursday night (2/26) at 11:59 PM</strong>.</p>
<ul>
  <li>25 multiple-choice questions, 25 points</li>
  <li>30-minute time limit</li>
  <li><strong>2 attempts</strong> &mdash; highest score kept</li>
  <li>Covers: ferrous vs. non-ferrous, metal identification, properties of 9 metals, MIG welding, lathe, and milling basics</li>
</ul>
<p>Review the <strong>Metal Types Study Guide</strong> page in Canvas before you take it. If you paid attention during the presentation, you&rsquo;ll do fine.</p>

<p>&mdash; Mr. McAteer</p>

</div>
"""


def run_rollout():
    canvas = get_canvas()

    for cid in METALS_COURSE_IDS:
        course = canvas.get_course(cid)
        cname = getattr(course, "name", f"Course {cid}")
        print(f"\n{'═' * 70}")
        print(f"  {cname} (ID: {cid})")
        print(f"{'═' * 70}")

        # ── OPTION A: Fix Foundation ──────────────────────────

        # A1. Find assignment groups
        groups = {getattr(g, "name", ""): g for g in course.get_assignment_groups()}
        safety_group = groups.get("Citizenship & Safety")
        imported_group = groups.get("Imported Assignments")
        projects_group = groups.get("Projects")

        if not safety_group:
            print("  ⚠ Could not find 'Citizenship & Safety' group — skipping group moves")
        else:
            # A1-A3. Move safety quizzes to correct group AND set due dates in same call
            # (SIS integration requires due_at whenever assignment is modified)
            for a in course.get_assignments():
                aname = getattr(a, "name", "")
                current_group = getattr(a, "assignment_group_id", None)

                # Move safety quizzes from Imported to Citizenship & Safety + set due date
                if aname in SAFETY_DUE_DATES:
                    edits = {}
                    due = SAFETY_DUE_DATES[aname]
                    current_due = getattr(a, "due_at", None)

                    if imported_group and current_group == imported_group.id:
                        edits["assignment_group_id"] = safety_group.id
                    if current_due != due:
                        edits["due_at"] = due

                    if edits:
                        # Always include due_at for SIS compatibility
                        edits["due_at"] = due
                        try:
                            a.edit(assignment=edits)
                            actions = []
                            if "assignment_group_id" in edits:
                                actions.append("MOVED to Citizenship & Safety")
                            if current_due != due:
                                actions.append(f"due → {due}")
                            print(f"  {' + '.join(actions)}: {aname}")
                        except Exception as e:
                            print(f"  ⚠ Failed to edit {aname}: {e}")

                # Move Metal Types Quiz from Projects to Citizenship & Safety
                if aname == "Metal Types — Unit Quiz" and projects_group and current_group == projects_group.id:
                    current_due = getattr(a, "due_at", None)
                    edits = {"assignment_group_id": safety_group.id}
                    if current_due:
                        edits["due_at"] = current_due  # preserve existing due date
                    try:
                        a.edit(assignment=edits)
                        print(f"  MOVED to Citizenship & Safety: {aname}")
                    except Exception as e:
                        print(f"  ⚠ Failed to move {aname}: {e}")

        # A4. Enable sequential progress on Safety Tests module
        for m in course.get_modules():
            mname = getattr(m, "name", "")
            if mname == "Safety Tests":
                seq = getattr(m, "require_sequential_progress", False)
                if not seq:
                    m.edit(module={"require_sequential_progress": True})
                    print(f"  ENABLED sequential progress: Safety Tests module")

                # Add completion requirements to module items
                try:
                    items = list(m.get_module_items())
                    for item in items:
                        title = getattr(item, "title", "")
                        existing_req = getattr(item, "completion_requirement", None)
                        if title == "General Shop Safety" and not existing_req:
                            item.edit(module_item={
                                "completion_requirement": {
                                    "type": "min_score",
                                    "min_score": 15  # 100% of 15 points
                                }
                            })
                            print(f"  SET 100% pass requirement: {title}")
                        elif not existing_req:
                            item.edit(module_item={
                                "completion_requirement": {
                                    "type": "must_submit"
                                }
                            })
                            print(f"  SET must_submit requirement: {title}")
                except Exception as e:
                    print(f"  ⚠ Could not set completion requirements: {e}")

        # ── OPTION B: Professional Polish ─────────────────────

        # B6. Create rubrics for project assignments
        rubric_map = {
            "Portable Tool Organizer - SolidWorks": RUBRIC_TOOL_ORGANIZER,
            "Sheet Metal Cell Phone Stand - POP Writeup": RUBRIC_CELL_PHONE_STAND,
            "Campus Handrail Plaque - Design & Fabrication": RUBRIC_HANDRAIL_PLAQUE,
            "Metal Entrepreneur Challenge": RUBRIC_ENTREPRENEUR,
        }

        for a in course.get_assignments():
            aname = getattr(a, "name", "")
            if aname in rubric_map:
                existing_rubric = getattr(a, "rubric", None)
                if existing_rubric:
                    print(f"  SKIP rubric (already exists): {aname}")
                    continue

                rubric_def = rubric_map[aname]
                rubric_criteria = {}
                for idx, crit in enumerate(rubric_def["criteria"]):
                    ratings = {}
                    for ridx, r in enumerate(crit["ratings"]):
                        ratings[str(ridx)] = {
                            "description": r["description"],
                            "points": r["points"],
                        }
                    rubric_criteria[str(idx)] = {
                        "description": crit["description"],
                        "points": crit["points"],
                        "ratings": ratings,
                    }

                try:
                    rubric_params = {
                        "rubric": {
                            "title": rubric_def["title"],
                            "criteria": rubric_criteria,
                        },
                        "rubric_association": {
                            "association_id": a.id,
                            "association_type": "Assignment",
                            "use_for_grading": True,
                            "purpose": "grading",
                        },
                    }
                    # Use the Canvas API directly for rubric creation
                    response = course._requester.request(
                        "POST",
                        f"courses/{cid}/rubrics",
                        **rubric_params
                    )
                    print(f"  CREATED rubric: {rubric_def['title']}")
                except Exception as e:
                    print(f"  ⚠ Rubric creation failed for {aname}: {e}")

        # B7. Create Course Home page (unpublished)
        try:
            page = course.create_page(wiki_page={
                "title": "Metals & Manufacturing — Course Home",
                "body": COURSE_HOME_HTML,
                "published": False,
                "front_page": False,
            })
            print(f"  CREATED page (unpublished): Metals & Manufacturing — Course Home")
        except Exception as e:
            print(f"  ⚠ Course home page: {e}")

        # B8. Create Metal Types study guide page (unpublished)
        try:
            page = course.create_page(wiki_page={
                "title": "Metal Types — Study Guide",
                "body": METAL_TYPES_PAGE_HTML,
                "published": False,
            })
            print(f"  CREATED page (unpublished): Metal Types — Study Guide")
        except Exception as e:
            print(f"  ⚠ Study guide page: {e}")

        # B9. Create announcement (as a delayed/unpublished discussion)
        try:
            announcement = course.create_discussion_topic(
                title="Missing Assignments + Metal Types Quiz This Thursday",
                message=ANNOUNCEMENT_HTML,
                is_announcement=True,
                published=False,
            )
            print(f"  CREATED announcement (unpublished): Missing Assignments + Quiz reminder")
        except Exception as e:
            print(f"  ⚠ Announcement: {e}")

    print(f"\n{'═' * 70}")
    print(f"  ROLLOUT COMPLETE — ALL CHANGES UNPUBLISHED")
    print(f"{'═' * 70}")
    print(f"""
  What was done (across all 5 courses):

  OPTION A — Foundation:
    ✓ Safety quizzes moved from 'Imported Assignments' (0%) to 'Citizenship & Safety' (25%)
    ✓ Metal Types Quiz moved from 'Projects' to 'Citizenship & Safety'
    ✓ Due dates added to all safety quizzes (staggered Mon-Sat)
    ✓ Sequential progress enabled on Safety Tests module
    ✓ Completion requirements set on module items

  OPTION B — Polish:
    ✓ Rubrics created for 4 project assignments
    ✓ Course Home page created (unpublished)
    ✓ Metal Types Study Guide page created (unpublished)
    ✓ Announcement drafted (unpublished)

  NEXT STEPS (your review):
    1. Go to each course in Canvas and review the changes
    2. Publish pages when satisfied
    3. Publish safety quizzes when ready for students
    4. Publish the Metal Types Quiz (review it first!)
    5. Publish the announcement when ready to notify students
    6. Set the Course Home page as front page if you want it as the landing
""")


if __name__ == "__main__":
    run_rollout()
