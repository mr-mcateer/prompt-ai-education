#!/usr/bin/env python3
"""
Canvas Deployment: The Exorcism of the Plasma Cutter — Practice Lab
=====================================================================
Creates:
  1. A project assignment with the full lab brief as description
  2. A reflection quiz (5 short-answer questions) due Thursday
  Both placed in the "3 — Design & Build" module, UNPUBLISHED.

Usage:
  python3 canvas_plasma_lab.py --deploy        # Push to all metals courses
  python3 canvas_plasma_lab.py --dry-run       # Preview without changes
"""

import os
import sys
import argparse
import requests
import json

METALS_COURSE_IDS = [23164, 23132, 23157, 23188, 23177]

# Thursday 2/26/2026 at 11:59 PM Pacific = Friday 2/27 7:59:59 AM UTC
THURSDAY_DUE = "2026-02-27T07:59:59Z"
# Monday 2/23/2026 at 6:00 AM Pacific = Monday 2/23 2:00 PM UTC
MONDAY_UNLOCK = "2026-02-23T14:00:00Z"


def get_creds():
    url = os.environ.get("CANVAS_API_URL")
    token = os.environ.get("CANVAS_API_TOKEN")
    if not url or not token:
        print("ERROR: Set CANVAS_API_URL and CANVAS_API_TOKEN")
        sys.exit(1)
    return url, token


def paginated_get(page_url, headers, params=None):
    results = []
    while page_url:
        r = requests.get(page_url, headers=headers, params=params)
        r.raise_for_status()
        results.extend(r.json())
        links = r.headers.get("Link", "")
        page_url = None
        for link in links.split(","):
            if 'rel="next"' in link:
                page_url = link.split("<")[1].split(">")[0]
        params = None
    return results


# ══════════════════════════════════════════════════════════════
# PROJECT ASSIGNMENT DESCRIPTION (HTML)
# ══════════════════════════════════════════════════════════════

ASSIGNMENT_DESCRIPTION = """
<div style="max-width:850px; font-family:inherit;">

<div style="background: linear-gradient(135deg, #1a1a2e, #2d1b4e); color: #f0f0f0; padding: 30px; border-radius: 8px; margin-bottom: 20px;">
  <h1 style="margin:0 0 8px 0; color:#e2b714; font-size:1.8em;">The Exorcism of the Plasma Cutter</h1>
  <p style="margin:0; font-size:1.1em; color:#c0c0c0;">Practice Lab &mdash; AI Image &rarr; Vector Cleanup &rarr; 3D Model &rarr; .STL Export</p>
  <p style="margin:8px 0 0 0; font-size:0.85em; color:#a0a0a0;">
    Gemini &rarr; SVG Converter &rarr; Adobe Illustrator &rarr; Tinkercad / OnShape / SolidWorks
  </p>
</div>

<div style="background:#f8f9fa; border-left:4px solid #e2b714; padding:15px 20px; margin-bottom:20px; border-radius:0 4px 4px 0;">
  <h3 style="margin:0 0 8px 0; color:#2c3e50;">Project Overview</h3>
  <p style="margin:0; line-height:1.7;">You will use <strong>Google Gemini</strong> to generate a plasma-ready image, convert it to SVG, clean it in <strong>Adobe Illustrator</strong>, then import it into a <strong>3D CAD tool</strong> to extrude it into a solid body and export a finished <strong>.STL file</strong>. This is the real-world workflow for taking a customer concept from idea to manufacturable file.</p>
</div>

<h2 style="color:#2c3e50; border-bottom:2px solid #e2b714; padding-bottom:8px;">The Pipeline</h2>
<table style="width:100%; border-collapse:collapse; margin-bottom:20px;">
  <tr style="background:#2d3a4a; color:white;">
    <th style="padding:10px; text-align:center;">1. Generate</th>
    <th style="padding:10px; text-align:center;">&rarr;</th>
    <th style="padding:10px; text-align:center;">2. Convert</th>
    <th style="padding:10px; text-align:center;">&rarr;</th>
    <th style="padding:10px; text-align:center;">3. Clean</th>
    <th style="padding:10px; text-align:center;">&rarr;</th>
    <th style="padding:10px; text-align:center;">4. Extrude &amp; Export</th>
  </tr>
  <tr style="background:#f8f9fa;">
    <td style="padding:10px; text-align:center;">Gemini (PNG)</td>
    <td style="padding:10px; text-align:center;">&rarr;</td>
    <td style="padding:10px; text-align:center;">Convertio (SVG)</td>
    <td style="padding:10px; text-align:center;">&rarr;</td>
    <td style="padding:10px; text-align:center;">Illustrator</td>
    <td style="padding:10px; text-align:center;">&rarr;</td>
    <td style="padding:10px; text-align:center;">CAD &rarr; .STL</td>
  </tr>
</table>

<h2 style="color:#2c3e50; border-bottom:2px solid #e2b714; padding-bottom:8px;">Timeline &mdash; Two Class Periods</h2>
<div style="display:flex; gap:20px; margin-bottom:20px;">
  <div style="flex:1; background:#f8f9fa; padding:15px; border-radius:6px; border-left:4px solid #4a6fa5;">
    <h3 style="color:#4a6fa5; margin:0 0 8px 0;">DAY 1: Generate, Convert &amp; Clean</h3>
    <ul style="margin:0; padding-left:1.2em; line-height:2;">
      <li><strong>0&ndash;10 min:</strong> Prompt Gemini, generate image</li>
      <li><strong>10&ndash;20 min:</strong> Convert PNG &rarr; SVG online</li>
      <li><strong>20&ndash;40 min:</strong> Open in Illustrator, clean up</li>
      <li><strong>40&ndash;50 min:</strong> Export clean SVG/DXF &mdash; <strong>Checkpoint</strong></li>
    </ul>
  </div>
  <div style="flex:1; background:#f8f9fa; padding:15px; border-radius:6px; border-left:4px solid #e2b714;">
    <h3 style="color:#e2b714; margin:0 0 8px 0;">DAY 2: Import, Extrude &amp; Export</h3>
    <ul style="margin:0; padding-left:1.2em; line-height:2;">
      <li><strong>0&ndash;5 min:</strong> Watch tutorial for your CAD tool</li>
      <li><strong>5&ndash;25 min:</strong> Import file, extrude to 3D solid</li>
      <li><strong>25&ndash;40 min:</strong> Refine model, set dimensions</li>
      <li><strong>40&ndash;50 min:</strong> Export .STL, submit deliverables</li>
    </ul>
  </div>
</div>

<h2 style="color:#2c3e50; border-bottom:2px solid #e2b714; padding-bottom:8px;">Deliverables Checklist</h2>
<ul style="line-height:2; font-size:1.05em;">
  <li>&#x2610; Screenshot of your Gemini prompt + generated image</li>
  <li>&#x2610; Cleaned SVG or DXF file exported from Illustrator (saved to class folder)</li>
  <li>&#x2610; Screenshot of your 3D model in CAD showing the extrusion</li>
  <li>&#x2610; Exported .STL file (saved to class folder)</li>
</ul>

<hr style="border:none; border-top:2px solid #e2b714; margin:30px 0;">

<h2 style="color:#2c3e50; border-bottom:2px solid #e2b714; padding-bottom:8px;">DAY 1: Generate, Convert &amp; Clean in Illustrator</h2>

<h3 style="color:#4a6fa5;">Phase 1 &mdash; Generate Your Image with Gemini</h3>
<p>Go to <strong>gemini.google.com</strong> and paste the prompt below. You may add your own subject, but <strong>do not remove any technical requirements.</strong> These constraints exist because plasma cutters cannot cut grayscale, gradients, or detail finer than the kerf width.</p>

<div style="background:#1a1a2e; color:#f0f0f0; padding:20px; border-radius:8px; margin:15px 0; font-family:monospace; font-size:0.85em; line-height:1.6;">
  <p style="color:#e2b714; font-weight:bold; margin:0 0 8px 0;">&#x1F916; BASE PROMPT &mdash; Copy This, Then Add Your Subject on the First Line</p>
  <p style="margin:0;">"Generate a black and white vector-style image of <strong>[YOUR SUBJECT HERE]</strong>. The design must be a single solid silhouette with no gradients, no grayscale, no shading, and no halftones. Use only pure black (#000000) on a pure white (#FFFFFF) background. All shapes must be connected &mdash; no floating islands or disconnected pieces. Line thickness must be no thinner than 1.5mm. The design should work as a single continuous cut path for a CNC plasma cutter. Keep the design simple with bold, clean outlines. No fine text, no thin crosshatching, no internal detail smaller than 3mm."</p>
</div>

<p><strong>Good subjects:</strong> animal silhouette, mountain scene, sports logo, automotive emblem, tribal design, tree of life, gear motif, constellation, school mascot concept</p>

<div style="background:#fff3cd; border-left:4px solid #e2b714; padding:12px 16px; margin:15px 0; border-radius:0 4px 4px 0;">
  <p style="margin:0;"><strong>&#x26A0; INSPECT BEFORE YOU MOVE ON:</strong> AI generators frequently produce gray tones, disconnected islands, or ultra-thin lines despite clear instructions. If your image has any gray or floating pieces, <strong>regenerate</strong>. Don&rsquo;t try to fix a bad image downstream &mdash; it&rsquo;s faster to re-prompt.</p>
</div>

<h3 style="color:#4a6fa5;">Phase 2 &mdash; Convert PNG to SVG</h3>
<ol style="line-height:2;">
  <li>Save your Gemini image as a <strong>.PNG</strong> file to your desktop or class folder.</li>
  <li>Go to <strong>convertio.co</strong> (or image.online-convert.com).</li>
  <li>Upload your PNG and convert to <strong>.SVG</strong> format.</li>
  <li>Download the SVG to your class folder.</li>
</ol>
<p><em>Why SVG? Illustrator handles SVG natively. You&rsquo;ll do all your cleanup here, then export the final file in whatever format your 3D CAD tool needs.</em></p>

<h3 style="color:#4a6fa5;">Phase 3 &mdash; Clean Up in Adobe Illustrator (Required)</h3>
<p>This is the <strong>most important phase</strong>. Free converters always introduce artifacts. Illustrator is where you fix them.</p>
<ol style="line-height:1.8;">
  <li>Open Illustrator. Go to <strong>File &rarr; Open</strong> and select your downloaded .SVG file.</li>
  <li>Zoom in to <strong>200&ndash;400%</strong> and slowly pan across the entire design. Look for the problems below.</li>
</ol>

<table style="width:100%; border-collapse:collapse; margin:15px 0;">
  <tr style="background:#2d3a4a; color:white;">
    <th style="padding:10px; text-align:left;">Problem</th>
    <th style="padding:10px; text-align:left;">Why It Matters</th>
    <th style="padding:10px; text-align:left;">How to Fix in Illustrator</th>
  </tr>
  <tr style="background:#f8f9fa;">
    <td style="padding:10px;">Stray anchor points / tiny fragments</td>
    <td style="padding:10px;">Creates phantom cut paths the machine will follow</td>
    <td style="padding:10px;">Select with Direct Selection Tool (A), delete. Use <strong>Object &rarr; Path &rarr; Clean Up</strong> to batch-remove.</td>
  </tr>
  <tr>
    <td style="padding:10px;">Open / unclosed paths</td>
    <td style="padding:10px;">Can&rsquo;t extrude an open shape in 3D CAD</td>
    <td style="padding:10px;"><strong>Object &rarr; Path &rarr; Join (Ctrl+J)</strong>. Or use the Pen Tool to close gaps manually.</td>
  </tr>
  <tr style="background:#f8f9fa;">
    <td style="padding:10px;">Duplicate / stacked paths</td>
    <td style="padding:10px;">Machine cuts the same line twice, ruining your part</td>
    <td style="padding:10px;">Select a path, delete it. If the shape is still there, there&rsquo;s a duplicate.</td>
  </tr>
  <tr>
    <td style="padding:10px;">Gray fills or gradients</td>
    <td style="padding:10px;">Plasma only understands cut / no-cut. Gray = confusion.</td>
    <td style="padding:10px;">Select all (Ctrl+A). Set Fill to pure black or pure white only.</td>
  </tr>
  <tr style="background:#f8f9fa;">
    <td style="padding:10px;">Excessive anchor points</td>
    <td style="padding:10px;">Slows CAD import, can crash Tinkercad</td>
    <td style="padding:10px;"><strong>Object &rarr; Path &rarr; Simplify</strong>. Adjust the curve precision slider.</td>
  </tr>
</table>

<h3 style="color:#4a6fa5;">Export from Illustrator for Your Chosen CAD Tool</h3>
<table style="width:100%; border-collapse:collapse; margin:15px 0;">
  <tr style="background:#2d3a4a; color:white;">
    <th style="padding:10px;">3D CAD Tool</th>
    <th style="padding:10px;">Export Format</th>
    <th style="padding:10px;">How to Export</th>
  </tr>
  <tr style="background:#f8f9fa;">
    <td style="padding:10px;"><strong>Tinkercad</strong></td>
    <td style="padding:10px;">.SVG</td>
    <td style="padding:10px;">File &rarr; Save As &rarr; SVG. Use SVG 1.1 profile, Presentation Attributes.</td>
  </tr>
  <tr>
    <td style="padding:10px;"><strong>OnShape</strong></td>
    <td style="padding:10px;">.DXF</td>
    <td style="padding:10px;">File &rarr; Export &rarr; AutoCAD Interchange (DXF). Use R14 or 2000 version.</td>
  </tr>
  <tr style="background:#f8f9fa;">
    <td style="padding:10px;"><strong>SolidWorks</strong></td>
    <td style="padding:10px;">.DXF</td>
    <td style="padding:10px;">Same as OnShape. Use AutoCAD 2000/2002 version for best compatibility.</td>
  </tr>
</table>

<div style="background:#d4edda; border-left:4px solid #22c55e; padding:12px 16px; margin:15px 0; border-radius:0 4px 4px 0;">
  <p style="margin:0;"><strong>&#x2714; Checkpoint:</strong> Before leaving Day 1, show Mr. McAteer your cleaned file in Illustrator. He will verify no duplicates, closed paths, and correct export format.</p>
</div>

<hr style="border:none; border-top:2px solid #e2b714; margin:30px 0;">

<h2 style="color:#2c3e50; border-bottom:2px solid #e2b714; padding-bottom:8px;">DAY 2: Import into 3D CAD, Extrude &amp; Export .STL</h2>

<h3 style="color:#e2b714;">Option A: Tinkercad (Easiest &mdash; Recommended for Beginners)</h3>
<ul style="line-height:1.8;">
  <li><strong>Login:</strong> tinkercad.com using your school Google account</li>
  <li><strong>Imports:</strong> .SVG files</li>
  <li><strong>Tutorial:</strong> Search YouTube for &ldquo;TinkerCad Tutorial - How to Turn a PNG/JPEG Image into a 3D Design&rdquo; by Envision Robotics</li>
</ul>
<ol style="line-height:1.8;">
  <li>Log into Tinkercad and click <strong>Create New Design</strong>.</li>
  <li>Click <strong>Import</strong> (upper right). Select your cleaned .SVG file.</li>
  <li>Set scale to ~100mm width so it fits on the workplane. Click Import.</li>
  <li>Select your imported shape. Drag the white handle upward to set extrusion height (try 5&ndash;10mm).</li>
  <li>Click <strong>Export &rarr; .STL</strong> (upper right). Download to your class folder.</li>
</ol>

<h3 style="color:#e2b714;">Option B: OnShape (Intermediate &mdash; Browser-Based Professional CAD)</h3>
<ul style="line-height:1.8;">
  <li><strong>Login:</strong> cad.onshape.com using your school email (free Education account)</li>
  <li><strong>Imports:</strong> .DXF files</li>
  <li><strong>Tutorial:</strong> Search YouTube for &ldquo;Turning Your 2D DXF into a 3D Model&rdquo; by Onshape</li>
</ul>
<ol style="line-height:1.8;">
  <li>Create a new Document. Click the + button &rarr; Import. Upload your .DXF file.</li>
  <li>Open a Part Studio. Start a Sketch on the Top plane.</li>
  <li>Inside the sketch, click the <strong>Insert DXF/DWG</strong> tool. Select your imported file. Verify units match.</li>
  <li>Click inside a closed region &mdash; it should turn gray (valid closed path). If not, zoom in and close gaps.</li>
  <li>Accept the sketch. Use <strong>Extrude</strong> to give it depth (5&ndash;10mm).</li>
  <li>Right-click the Part Studio tab &rarr; Export &rarr; STL. Save to class folder.</li>
</ol>

<h3 style="color:#e2b714;">Option C: SolidWorks (Advanced &mdash; Industry Standard)</h3>
<ul style="line-height:1.8;">
  <li><strong>Access:</strong> Lab computers with SolidWorks installed</li>
  <li><strong>Imports:</strong> .DXF files</li>
  <li><strong>Tutorial:</strong> Search YouTube for &ldquo;Importing a DWG or DXF file into SOLIDWORKS&rdquo; by TriMech</li>
</ul>
<ol style="line-height:1.8;">
  <li>Open SolidWorks. Go to <strong>File &rarr; Open</strong>, navigate to your .DXF file.</li>
  <li>In the DXF/DWG Import Wizard: select <strong>Import to a new part as 2D Sketch</strong>. Verify units.</li>
  <li>Once imported, run <strong>Tools &rarr; Sketch Tools &rarr; Repair Sketch</strong> to auto-fix gaps.</li>
  <li>Use <strong>Features &rarr; Extruded Boss/Base</strong>. Select your sketch profile. Set depth to 5&ndash;10mm.</li>
  <li>Go to <strong>File &rarr; Save As &rarr; STL (.stl)</strong>. Save to class folder.</li>
</ol>

<div style="background:#f8d7da; border-left:4px solid #ef4444; padding:12px 16px; margin:15px 0; border-radius:0 4px 4px 0;">
  <p style="margin:0;"><strong>&#x26A0; IF YOUR FILE WON&rsquo;T EXTRUDE:</strong> This almost always means you have open paths (gaps where lines don&rsquo;t connect). Go back to Illustrator, zoom in to where the break is, and use <strong>Object &rarr; Path &rarr; Join</strong> or the Pen Tool to close the gap. Then re-export and re-import.</p>
</div>

<hr style="border:none; border-top:2px solid #e2b714; margin:30px 0;">

<h2 style="color:#2c3e50; border-bottom:2px solid #e2b714; padding-bottom:8px;">Grading Rubric</h2>
<table style="width:100%; border-collapse:collapse; margin:15px 0;">
  <tr style="background:#2d3a4a; color:white;">
    <th style="padding:10px; text-align:left;">Criteria</th>
    <th style="padding:10px; text-align:center;">Proficient (4)</th>
    <th style="padding:10px; text-align:center;">Developing (3)</th>
    <th style="padding:10px; text-align:center;">Beginning (2)</th>
  </tr>
  <tr style="background:#f8f9fa;">
    <td style="padding:10px;"><strong>AI Image Generation</strong><br>Clean B&amp;W, no gray, connected shapes</td>
    <td style="padding:10px;">Clean on 1st or 2nd attempt</td>
    <td style="padding:10px;">Minor gray/islands, fixed</td>
    <td style="padding:10px;">Used image with issues, didn&rsquo;t fix</td>
  </tr>
  <tr>
    <td style="padding:10px;"><strong>Illustrator Cleanup</strong><br>Removed artifacts, closed paths, no duplicates</td>
    <td style="padding:10px;">All paths clean and closed</td>
    <td style="padding:10px;">Most paths clean, minor issues</td>
    <td style="padding:10px;">Skipped cleanup or major issues remain</td>
  </tr>
  <tr style="background:#f8f9fa;">
    <td style="padding:10px;"><strong>3D Extrusion</strong><br>Solid body with correct dimensions</td>
    <td style="padding:10px;">Clean solid, correct dimensions</td>
    <td style="padding:10px;">Extruded but minor issues</td>
    <td style="padding:10px;">Could not complete extrusion</td>
  </tr>
  <tr>
    <td style="padding:10px;"><strong>.STL Export</strong><br>Valid file, correct naming, submitted</td>
    <td style="padding:10px;">Valid .STL, properly named</td>
    <td style="padding:10px;">Submitted but naming issues</td>
    <td style="padding:10px;">Not submitted or invalid file</td>
  </tr>
  <tr style="background:#f8f9fa;">
    <td style="padding:10px;"><strong>Reflection</strong><br>Thoughtful, specific, demonstrates understanding</td>
    <td style="padding:10px;">Detailed, shows learning</td>
    <td style="padding:10px;">Complete but surface-level</td>
    <td style="padding:10px;">Incomplete or no effort</td>
  </tr>
</table>
<p style="text-align:right; font-size:1.1em;"><strong>Total: _____ / 20</strong></p>

</div>
"""

# ══════════════════════════════════════════════════════════════
# REFLECTION QUIZ — 5 Short-Answer Questions
# ══════════════════════════════════════════════════════════════
REFLECTION_TITLE = "The Exorcism of the Plasma Cutter — Reflection"
REFLECTION_DESCRIPTION = (
    "<p>Answer each question in <strong>2&ndash;3 complete sentences</strong>. "
    "These reflections are graded on <strong>thoughtfulness and specificity</strong> &mdash; "
    "generic or one-word answers will not receive full credit.</p>"
    "<p>Think about what you actually experienced during the lab, not what you think "
    "the &ldquo;right&rdquo; answer should be.</p>"
)

REFLECTION_QUESTIONS = [
    {
        "stem": (
            "What subject did you choose for your Gemini image, and did it generate "
            "cleanly on the first try? If not, what did you have to change in your prompt "
            "to get a usable result?"
        ),
        "points": 2,
        "bloom": "Comprehension",
        "rubric_note": (
            "Full credit: Names specific subject, describes prompt iteration with detail. "
            "Partial: Vague subject description, no mention of prompt adjustments. "
            "No credit: Blank or single word."
        ),
    },
    {
        "stem": (
            "What was the biggest problem you found when you opened the SVG in Adobe "
            "Illustrator? Describe the specific issue and the tool or method you used to fix it."
        ),
        "points": 2,
        "bloom": "Application",
        "rubric_note": (
            "Full credit: Identifies a specific Illustrator issue (stray anchors, open paths, "
            "duplicates, gray fills) and names the exact tool used to fix it. "
            "Partial: Generic problem description, no tool named. "
            "No credit: Blank or 'nothing was wrong.'"
        ),
    },
    {
        "stem": (
            "Which 3D CAD tool did you use (Tinkercad, OnShape, or SolidWorks), and why "
            "did you choose it? Was the import smooth, or did you run into issues? Explain."
        ),
        "points": 2,
        "bloom": "Comprehension",
        "rubric_note": (
            "Full credit: Names tool, gives reasoning for choice, describes import experience "
            "with specific detail. Partial: Names tool but no reasoning or vague import description. "
            "No credit: Blank."
        ),
    },
    {
        "stem": (
            "If you were going to plasma-cut this design for real, what would you need "
            "to check or change before sending the file to the machine? Think about material "
            "thickness, kerf width, tab placement, and safety."
        ),
        "points": 2,
        "bloom": "Application",
        "rubric_note": (
            "Full credit: Mentions at least 2 of: material thickness, kerf compensation, tab "
            "placement, part fixturing, safety gear, or file format for the plasma table. "
            "Partial: Mentions 1 consideration vaguely. "
            "No credit: Blank or 'nothing.'"
        ),
    },
    {
        "stem": (
            "What is the difference between a .SVG file, a .DXF file, and an .STL file? "
            "Why does each format exist, and at what stage of the pipeline did you use each one?"
        ),
        "points": 2,
        "bloom": "Knowledge",
        "rubric_note": (
            "Full credit: Correctly distinguishes all 3 formats (SVG = vector/web, DXF = CAD "
            "exchange, STL = 3D mesh for manufacturing) and connects each to the pipeline stage. "
            "Partial: Gets 1-2 correct but confuses the third. "
            "No credit: Blank or completely wrong."
        ),
    },
]


def deploy(dry_run=False):
    url, token = get_creds()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    for cid in METALS_COURSE_IDS:
        r = requests.get(f"{url}/api/v1/courses/{cid}", headers=headers)
        cname = r.json().get("name", f"Course {cid}")
        print(f"\n{'═' * 60}")
        print(f"  {cname} (ID: {cid})")
        print(f"{'═' * 60}")

        # Find the Projects assignment group
        groups = paginated_get(
            f"{url}/api/v1/courses/{cid}/assignment_groups?per_page=50", headers
        )
        projects_group_id = None
        for g in groups:
            if g["name"] == "Projects":
                projects_group_id = g["id"]
                break

        if not projects_group_id:
            print("  ⚠ No 'Projects' group found — using default")

        # Find the "3 — Design & Build" module
        modules = paginated_get(
            f"{url}/api/v1/courses/{cid}/modules?per_page=50", headers
        )
        design_module_id = None
        for m in modules:
            if m["name"] == "3 — Design & Build":
                design_module_id = m["id"]
                break

        # Check for existing assignments to avoid duplicates
        existing = paginated_get(
            f"{url}/api/v1/courses/{cid}/assignments?per_page=50", headers
        )
        existing_names = {a["name"] for a in existing}

        # ── 1. Create the Project Assignment ────────────────────
        project_name = "The Exorcism of the Plasma Cutter — Practice Lab"
        if project_name in existing_names:
            print(f"  EXISTS: {project_name}")
            # Find the ID
            project_aid = None
            for a in existing:
                if a["name"] == project_name:
                    project_aid = a["id"]
                    break
        else:
            if dry_run:
                print(f"  [DRY RUN] Would create: {project_name}")
                project_aid = None
            else:
                payload = {
                    "assignment": {
                        "name": project_name,
                        "description": ASSIGNMENT_DESCRIPTION,
                        "points_possible": 20,
                        "grading_type": "points",
                        "submission_types": ["online_upload", "online_text_entry"],
                        "allowed_extensions": ["stl", "svg", "dxf", "png", "jpg", "pdf"],
                        "published": False,
                        "due_at": THURSDAY_DUE,
                        "unlock_at": MONDAY_UNLOCK,
                        "position": 4,  # After Handrail Plaque
                    }
                }
                if projects_group_id:
                    payload["assignment"]["assignment_group_id"] = projects_group_id

                r = requests.post(
                    f"{url}/api/v1/courses/{cid}/assignments",
                    headers=headers,
                    json=payload,
                )
                if r.status_code in (200, 201):
                    project_aid = r.json()["id"]
                    print(f"  CREATED: {project_name} (ID: {project_aid}, 20 pts, unpublished)")
                else:
                    print(f"  ⚠ Failed to create project: {r.status_code}")
                    try:
                        print(f"    {r.json()}")
                    except Exception:
                        pass
                    project_aid = None

        # ── 2. Create the Reflection Quiz ───────────────────────
        reflection_name = REFLECTION_TITLE
        if reflection_name in existing_names:
            print(f"  EXISTS: {reflection_name}")
        else:
            if dry_run:
                print(f"  [DRY RUN] Would create quiz: {reflection_name}")
            else:
                # Check for existing quizzes
                quizzes = paginated_get(
                    f"{url}/api/v1/courses/{cid}/quizzes?per_page=50", headers
                )
                quiz_exists = any(q["title"] == reflection_name for q in quizzes)

                if quiz_exists:
                    print(f"  QUIZ EXISTS: {reflection_name}")
                else:
                    # Create the quiz
                    quiz_payload = {
                        "quiz": {
                            "title": reflection_name,
                            "description": REFLECTION_DESCRIPTION,
                            "quiz_type": "assignment",
                            "time_limit": None,  # No time limit for reflection
                            "allowed_attempts": 1,
                            "scoring_policy": "keep_highest",
                            "show_correct_answers": False,  # Short answer — graded manually
                            "one_question_at_a_time": False,
                            "shuffle_answers": False,
                            "due_at": THURSDAY_DUE,
                            "unlock_at": MONDAY_UNLOCK,
                            "published": False,
                        }
                    }
                    if projects_group_id:
                        quiz_payload["quiz"]["assignment_group_id"] = projects_group_id

                    r = requests.post(
                        f"{url}/api/v1/courses/{cid}/quizzes",
                        headers=headers,
                        json=quiz_payload,
                    )
                    if r.status_code in (200, 201):
                        quiz = r.json()
                        quiz_id = quiz["id"]
                        print(f"  CREATED QUIZ: {reflection_name} (ID: {quiz_id}, unpublished)")

                        # Add questions
                        for idx, q in enumerate(REFLECTION_QUESTIONS, 1):
                            q_payload = {
                                "question": {
                                    "question_name": f"Reflection {idx}",
                                    "question_text": (
                                        f"<p>{q['stem']}</p>"
                                        f"<p style='color:#666; font-size:0.85em;'>"
                                        f"<em>Answer in 2&ndash;3 complete sentences.</em></p>"
                                    ),
                                    "question_type": "essay_question",
                                    "points_possible": q["points"],
                                    "position": idx,
                                }
                            }
                            qr = requests.post(
                                f"{url}/api/v1/courses/{cid}/quizzes/{quiz_id}/questions",
                                headers=headers,
                                json=q_payload,
                            )
                            if qr.status_code in (200, 201):
                                print(f"    Q{idx}: {q['stem'][:60]}... ({q['points']} pts)")
                            else:
                                print(f"    ⚠ Q{idx} failed: {qr.status_code}")
                    else:
                        print(f"  ⚠ Failed to create quiz: {r.status_code}")
                        try:
                            print(f"    {r.json()}")
                        except Exception:
                            pass

        # ── 3. Add both to the Design & Build module ────────────
        if design_module_id and not dry_run:
            # Get current module items
            current_items = paginated_get(
                f"{url}/api/v1/courses/{cid}/modules/{design_module_id}/items?per_page=50",
                headers,
            )
            current_titles = {item.get("title", "") for item in current_items}

            # Add project assignment
            if project_aid and project_name not in current_titles:
                r = requests.post(
                    f"{url}/api/v1/courses/{cid}/modules/{design_module_id}/items",
                    headers=headers,
                    json={
                        "module_item": {
                            "type": "Assignment",
                            "content_id": project_aid,
                        }
                    },
                )
                if r.status_code in (200, 201):
                    print(f"  ADDED to module: {project_name}")
                else:
                    print(f"  ⚠ Module add failed for project: {r.status_code}")

            # Add reflection quiz (need to find its assignment ID)
            quizzes = paginated_get(
                f"{url}/api/v1/courses/{cid}/quizzes?per_page=50", headers
            )
            for q in quizzes:
                if q["title"] == reflection_name:
                    quiz_assignment_id = q.get("assignment_id")
                    if quiz_assignment_id and reflection_name not in current_titles:
                        r = requests.post(
                            f"{url}/api/v1/courses/{cid}/modules/{design_module_id}/items",
                            headers=headers,
                            json={
                                "module_item": {
                                    "type": "Assignment",
                                    "content_id": quiz_assignment_id,
                                }
                            },
                        )
                        if r.status_code in (200, 201):
                            print(f"  ADDED to module: {reflection_name}")
                        else:
                            print(f"  ⚠ Module add failed for reflection: {r.status_code}")
                    break
        elif dry_run:
            print(f"  [DRY RUN] Would add both to '3 — Design & Build' module")

        print(f"  ✓ Done for {cname}")

    print(f"\n{'═' * 60}")
    print(f"  DEPLOYMENT COMPLETE")
    print(f"{'═' * 60}")
    print(f"""
  Created across all 5 metals courses (UNPUBLISHED):

    1. "The Exorcism of the Plasma Cutter — Practice Lab" (20 pts)
       - Full project brief with pipeline, timeline, troubleshooting
       - Accepts .STL, .SVG, .DXF, .PNG, .JPG, .PDF uploads
       - Due Thursday, unlocks Monday
       - In "3 — Design & Build" module

    2. "The Exorcism of the Plasma Cutter — Reflection" (10 pts)
       - 5 short-answer essay questions
       - Graded manually for thoughtfulness
       - Due Thursday, unlocks Monday
       - In "3 — Design & Build" module

  NEXT: Review in Canvas, publish when ready for Monday.
""")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--deploy", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.dry_run:
        print("DRY RUN — no changes will be made\n")
        deploy(dry_run=True)
    elif args.deploy:
        deploy(dry_run=False)
    else:
        parser.print_help()
