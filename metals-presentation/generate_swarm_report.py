#!/usr/bin/env python3
"""
Generate PDF report from Agent Swarm Grader results.
Parses the execute/evaluate output and builds a styled PDF.

Usage:
    python3 generate_swarm_report.py
"""

import os
import sys
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

# ── Color palette ─────────────────────────────────────────────
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

COMPLETENESS_COLORS = {
    "complete": C_GREEN,
    "partial": C_AMBER,
    "missing": C_RED,
    "minimal": C_RED,
}

QUALITY_COLORS = {
    "complete": C_GREEN,
    "partial": C_AMBER,
    "minimal": C_RED,
    "empty": C_GRAY,
}

QUALITY_BG = {
    "complete": C_LIGHT_GREEN,
    "partial": C_LIGHT_AMBER,
    "minimal": C_LIGHT_RED,
    "empty": C_LIGHT_GRAY,
}


# ── Student review data ──────────────────────────────────────
# Hardcoded from the execute run on 2026-02-23

REVIEWS = [
    # ── P3 Metals 1 ──
    {
        "course": "P3 Metals 1",
        "student": "Student 11921",
        "quality": "partial",
        "file": "Plan of Procedure - Sheet Metal Phone Dock.pdf",
        "criteria": [
            {
                "name": "Design Intent & Problem Statement",
                "completeness": "partial",
                "observation": "States objective to design a functional phone stand. Lists skills practiced. No explicit problem statement or justification for material/angle choices.",
                "questions": [
                    "Could you expand on what specific problem or need your design aims to solve for someone using a phone stand?",
                    "You chose 20-22 gauge galvanized steel. What were your reasons for selecting this specific type and thickness of metal?",
                ],
            },
            {
                "name": "Plan of Procedure (Step-by-Step)",
                "completeness": "partial",
                "observation": "Numbered procedure broken into phases. Includes some tools and safety reminders. Lacks specific measurements or angles for bends.",
                "questions": [
                    "Could you add specific measurements for the total length, width, and distances for each bend line on your flat pattern?",
                    "What specific angles are you planning for 'The Cradle' and 'The Back/Stand' bends?",
                ],
            },
            {
                "name": "Materials & Tools List",
                "completeness": "partial",
                "observation": "Lists material type and various tools. Specific dimensions for the material and quantity are not provided.",
                "questions": [
                    "Could you add the specific dimensions (length and width) and quantity needed for one stand?",
                    "Are there any other tools for measuring angles or final finishing that should be added?",
                ],
            },
            {
                "name": "Reflection & Writing Quality",
                "completeness": "missing",
                "observation": "Well-organized writing. 'Quality Check' section is a rubric, not a personal reflection.",
                "questions": [
                    "Could you add a section reflecting on your experience -- most challenging part, what you learned, what you'd do differently?",
                ],
            },
        ],
        "flags": ["Missing specific dimensions/quantity", "Missing angles in procedure", "Quality Check is a rubric, not reflection", "Placeholder images for finish product"],
    },
    {
        "course": "P3 Metals 1",
        "student": "Student 21134",
        "quality": "partial",
        "file": "pop metal phone stand.docx",
        "criteria": [
            {
                "name": "Design Intent & Problem Statement",
                "completeness": "partial",
                "observation": "Provides design concept name ('The Simple Slant') and specs. No explicit problem statement or material justification.",
                "questions": [
                    "What specific problem does 'The Simple Slant' solve for a cell phone user?",
                    "What are the advantages of 22-gauge galvanized steel for a cell phone stand?",
                ],
            },
            {
                "name": "Plan of Procedure (Step-by-Step)",
                "completeness": "partial",
                "observation": "Phases with tools and measurements. Unclear how 'Back Supports' and 'Under support' are created. Hot glue vs. weld gap.",
                "questions": [
                    "How are the 'Back Supports' and 'Under support' created from your 3\" x 7\" flat pattern?",
                    "Which assembly method do you plan to use -- hot glue or welding -- and what safety precautions are needed?",
                ],
            },
            {
                "name": "Materials & Tools List",
                "completeness": "partial",
                "observation": "Identifies material and tools throughout but no consolidated list.",
                "questions": [
                    "Could you provide a single, consolidated list of all materials with quantities and dimensions?",
                    "Please create a complete list of all tools from layout to final assembly.",
                ],
            },
            {
                "name": "Reflection & Writing Quality",
                "completeness": "partial",
                "observation": "Clear writing. 'Design Ideas to Enhance' shows thought. No dedicated reflection on planning process.",
                "questions": [
                    "Could you reflect on the planning process? What was the most challenging part?",
                ],
            },
        ],
        "flags": ["No explicit problem statement", "Materials/tools not consolidated", "Hot glue vs. weld ambiguity", "No dedicated reflection"],
    },
    {
        "course": "P3 Metals 1",
        "student": "Student 8384",
        "quality": "partial",
        "file": "Iain Bailes Phone Holder POP.pdf",
        "criteria": [
            {
                "name": "Design Intent & Problem Statement",
                "completeness": "missing",
                "observation": "No design intent or problem statement section. Title implies a 'Phone Holder' but nothing explicit.",
                "questions": [
                    "What specific problem were you trying to solve with this phone holder design?",
                    "Why did you choose sheet metal, and how did that influence your design?",
                ],
            },
            {
                "name": "Plan of Procedure (Step-by-Step)",
                "completeness": "partial",
                "observation": "4 numbered steps starting with cardboard prototype. 'Sheet metal cutter' and 'Plasma CNC' mentioned. Hot glue for assembly.",
                "questions": [
                    "Could you specify which type of sheet metal cutter you plan to use and why?",
                    "What alternative metal joining techniques did you consider instead of hot glue?",
                ],
            },
            {
                "name": "Materials & Tools List",
                "completeness": "partial",
                "observation": "BOM table provided with dimensions and calculations. No separate tools list.",
                "questions": [
                    "Could you add a separate section listing all tools and safety equipment?",
                    "Since you mentioned hot glue, could you add adhesive to your BOM?",
                ],
            },
            {
                "name": "Reflection & Writing Quality",
                "completeness": "minimal",
                "observation": "No reflection section. Template instructions (yellow/orange highlights) still present. Pages 4-7 blank.",
                "questions": [
                    "Could you add a reflection on your design and planning process?",
                    "Please remove template instructions and highlighted text.",
                ],
            },
        ],
        "flags": ["Missing design intent", "Missing tools list", "Template instructions not removed", "Blank pages 4-7", "No dimensioned drawing"],
    },
    # ── P3 Metals 2 ──
    {
        "course": "P3 Metals 2",
        "student": "Student 4671",
        "quality": "partial",
        "file": "Sheet Metal P.O.P - AG.pdf",
        "criteria": [
            {
                "name": "Design Intent & Problem Statement",
                "completeness": "partial",
                "observation": "Identifies problems: lack of horizontal stands and durability. No justification for material/angle choices.",
                "questions": [
                    "How does 22-gauge galvanized steel specifically make your stand more durable?",
                    "How do your chosen angles ensure the phone is held securely horizontally?",
                ],
            },
            {
                "name": "Plan of Procedure (Step-by-Step)",
                "completeness": "partial",
                "observation": "Lists general steps. Lacks specific dimensions, detailed tool callouts. Bending not mentioned.",
                "questions": [
                    "Could you add specific dimensions for the shapes you drew and cut?",
                    "Can you describe where and how you planned to bend the metal?",
                ],
            },
            {
                "name": "Materials & Tools List",
                "completeness": "partial",
                "observation": "Lists steel and hot glue. Missing dimensions, quantity, and comprehensive tools list.",
                "questions": [
                    "Could you specify dimensions and quantity for the galvanized steel?",
                    "Could you create a separate list of all tools used?",
                ],
            },
            {
                "name": "Reflection & Writing Quality",
                "completeness": "complete",
                "observation": "Thoughtful reflection on creativity, hot glue safety incident, and material durability. Clear and professional.",
                "questions": [
                    "What specific aspects allowed you to be most creative?",
                    "What observations led you to conclude hot glue was durable?",
                ],
            },
        ],
        "flags": ["Missing dimensions in BOM", "No dedicated tools list", "Photos section empty"],
    },
    {
        "course": "P3 Metals 2",
        "student": "Student 8370",
        "quality": "minimal",
        "file": "Dawson phone holder POP.docx",
        "criteria": [
            {
                "name": "Design Intent & Problem Statement",
                "completeness": "missing",
                "observation": "Jumps directly into procedural steps. No problem statement or design justification.",
                "questions": [
                    "What specific problem were you trying to solve with this stand?",
                    "How do the dimensions help your stand meet a specific user need?",
                ],
            },
            {
                "name": "Plan of Procedure (Step-by-Step)",
                "completeness": "partial",
                "observation": "Numbered list with some dimensions. Lacks tool callouts. Deburring after gluing seems out of order. Hot glue for assembly.",
                "questions": [
                    "What specific tools would you use for cutting safely?",
                    "What more permanent methods for joining sheet metal could you consider?",
                ],
            },
            {
                "name": "Materials & Tools List",
                "completeness": "partial",
                "observation": "Identifies starting sheet size. Missing metal type/gauge and comprehensive tools list.",
                "questions": [
                    "What specific type and gauge of sheet metal did you plan to use?",
                    "Could you list all tools needed for each step?",
                ],
            },
            {
                "name": "Reflection & Writing Quality",
                "completeness": "missing",
                "observation": "No reflective component. Spelling error: 'Coutout'.",
                "questions": [
                    "What did you learn while planning this stand?",
                    "What would you change or improve if making it again?",
                ],
            },
        ],
        "flags": ["Missing 3 of 4 sections", "Hot glue for metal assembly", "Spelling error: 'Coutout'"],
    },
    # ── P5 Metals 1 ──
    {
        "course": "P5 Metals 1",
        "student": "Student 11596",
        "quality": "partial",
        "file": "Copy of POP Template.pdf",
        "criteria": [
            {
                "name": "Design Intent & Problem Statement",
                "completeness": "minimal",
                "observation": "Title implies purpose. Reflection mentions triangle cut for charger. No explicit problem statement.",
                "questions": [
                    "What specific problem were you trying to solve for an iPhone user?",
                    "How does the triangle cut for the charger address a specific need?",
                ],
            },
            {
                "name": "Plan of Procedure (Step-by-Step)",
                "completeness": "partial",
                "observation": "13 numbered steps with dimensions and some tools (scribe, tin snips, center punch, rivets). Missing bending tool details and safety callouts.",
                "questions": [
                    "What specific tools did you use for 90-degree bends?",
                    "What is a 'triangle punch' and why did you choose hot glue over other joining methods?",
                ],
            },
            {
                "name": "Materials & Tools List",
                "completeness": "partial",
                "observation": "BOM table lists two sheet metal pieces. No consolidated tools list.",
                "questions": [
                    "Can you specify the exact type of sheet metal (mild steel, aluminum)?",
                    "Could you create a consolidated list of all tools?",
                ],
            },
            {
                "name": "Reflection & Writing Quality",
                "completeness": "complete",
                "observation": "Discusses benefit of drawing steps, success of charger opening, and base stability improvement. Clear and professional.",
                "questions": [
                    "How did drawing every step help you make the process more efficient?",
                    "What specific design changes would improve base stability?",
                ],
            },
        ],
        "flags": ["No explicit problem statement", "Missing consolidated tools list", "Missing 3-view drawing", "Template placeholder for teacher initials"],
    },
    {
        "course": "P5 Metals 1",
        "student": "Student 1320",
        "quality": "partial",
        "file": "Morris PhoneStand POP.docx",
        "criteria": [
            {
                "name": "Design Intent & Problem Statement",
                "completeness": "partial",
                "observation": "Describes 'Triple-Stack Slot' design for iPhone 14. Material thickness and pocket depth justified.",
                "questions": [
                    "What specific problem does your 'Triple-Stack Slot' stand solve?",
                    "Why was 0.5-inch thick sheet metal chosen for a laminated assembly?",
                ],
            },
            {
                "name": "Plan of Procedure (Step-by-Step)",
                "completeness": "partial",
                "observation": "Assembly steps 2-4 detailed. Step 1 missing. Super glue and fingers for clamping. 75-degree tilt specified.",
                "questions": [
                    "Could you add Step 1 describing how individual components are prepared?",
                    "What specific tools and measurements ensure parts fit correctly?",
                ],
            },
            {
                "name": "Materials & Tools List",
                "completeness": "partial",
                "observation": "Lists sheet metal and super glue. Component List section empty.",
                "questions": [
                    "Could you provide a complete list of all individual metal components with dimensions?",
                    "What tools are needed to cut, measure, and prepare the metal pieces?",
                ],
            },
            {
                "name": "Reflection & Writing Quality",
                "completeness": "partial",
                "observation": "Clear writing with good technical terms. Safety note included. No explicit reflection section.",
                "questions": [
                    "What did you learn planning the 'Triple-Stack Slot' design?",
                    "What would you change about your design or procedure?",
                ],
            },
        ],
        "flags": ["Missing Step 1", "Empty Component List", "Title says 'sheet box' not 'cell phone stand'", "No reflection section"],
    },
    {
        "course": "P5 Metals 1",
        "student": "Student 1768",
        "quality": "partial",
        "file": "Sheet Metal Phone Stand POP.docx",
        "criteria": [
            {
                "name": "Design Intent & Problem Statement",
                "completeness": "partial",
                "observation": "States project purpose. Mentions challenge of cutting hands. Contradiction: hot glue vs. folding metal.",
                "questions": [
                    "Can you clarify: hot glue or folding? Why did you change your approach?",
                    "What features allow your stand to hold a phone both vertically and horizontally?",
                ],
            },
            {
                "name": "Plan of Procedure (Step-by-Step)",
                "completeness": "partial",
                "observation": "Phased procedure (1.1-1.5). General actions without specific measurements or tool callouts.",
                "questions": [
                    "Could you add specific dimensions and cutting tools for each part?",
                    "What measurements or angles ensure the phone rest holds securely?",
                ],
            },
            {
                "name": "Materials & Tools List",
                "completeness": "partial",
                "observation": "Lists 'scrap sheet metal' without gauge. Tools categorized. 'Hope puncher' typo.",
                "questions": [
                    "Could you specify thickness and dimensions of the sheet metal?",
                    "What is a 'Hope puncher'? (likely 'hole puncher')",
                ],
            },
            {
                "name": "Reflection & Writing Quality",
                "completeness": "missing",
                "observation": "Reflection section completely blank. Informal language ('damn hands', 'My brain'). PPE lists 'Common Sense' instead of physical gear.",
                "questions": [
                    "Remember to fill in the PROJECT REFLECTION after building your stand.",
                    "How might you rephrase informal language for professional documentation?",
                ],
            },
        ],
        "flags": ["Reflection blank", "Hot glue vs. folding contradiction", "'Hope puncher' typo", "'Common Sense' listed as PPE"],
    },
    {
        "course": "P5 Metals 1",
        "student": "Student 20623",
        "quality": "partial",
        "file": "Phone Holder POP.docx",
        "criteria": [
            {
                "name": "Design Intent & Problem Statement",
                "completeness": "partial",
                "observation": "Clear goal: 'functional desktop art' with iPhone orientation and MagSafe compatibility. Triangular aesthetic identified.",
                "questions": [
                    "What properties of galvanized sheet metal make it good for 'functional desktop art'?",
                    "Were there structural reasons for the triangular aesthetic beyond visual impact?",
                ],
            },
            {
                "name": "Plan of Procedure (Step-by-Step)",
                "completeness": "partial",
                "observation": "Logical phases (Prototyping, CAD, Cutting, Cold-Forming, Integration). Key tools mentioned. Missing measurements and safety.",
                "questions": [
                    "Could you add specific measurements for mock-up dimensions and bend angles?",
                    "What safety precautions for ArcLight Plasma CNC and angle grinder?",
                ],
            },
            {
                "name": "Materials & Tools List",
                "completeness": "missing",
                "observation": "'Bill of Materials & Tooling' section present but completely empty.",
                "questions": [
                    "Could you fill in the BOM with material dimensions, quantity, and all tools?",
                ],
            },
            {
                "name": "Reflection & Writing Quality",
                "completeness": "minimal",
                "observation": "Well-organized, professional writing. 'Final Evaluation' checks product but lacks process reflection.",
                "questions": [
                    "Could you add a reflection on the fabrication process -- challenges, learning?",
                ],
            },
        ],
        "flags": ["BOM section completely empty", "Final Evaluation is checklist, not reflection"],
    },
    {
        "course": "P5 Metals 1",
        "student": "Student 20756",
        "quality": "minimal",
        "file": "Pop template - Hans Phone stand.docx",
        "criteria": [
            {
                "name": "Design Intent & Problem Statement",
                "completeness": "missing",
                "observation": "Contains template instructions only. No student content for design intent.",
                "questions": [
                    "What specific problem is your stand designed to solve?",
                    "What were your initial design ideas?",
                ],
            },
            {
                "name": "Plan of Procedure (Step-by-Step)",
                "completeness": "missing",
                "observation": "'PLAN STEPS:' heading present. No actual steps from student.",
                "questions": [
                    "Could you walk through the main steps from cutting to finishing?",
                    "What tools and safety precautions for each step?",
                ],
            },
            {
                "name": "Materials & Tools List",
                "completeness": "missing",
                "observation": "BOM heading present. Prompt says 'Wood Required' for a metal project.",
                "questions": [
                    "Could you list all materials including type, dimensions, and quantity?",
                    "What tools were needed for each fabrication step?",
                ],
            },
            {
                "name": "Reflection & Writing Quality",
                "completeness": "missing",
                "observation": "No student-written reflection. Only template text.",
                "questions": [
                    "What was the most challenging part?",
                    "What would you do differently?",
                ],
            },
        ],
        "flags": ["Mostly template -- very little student content", "'Wood Required' on a metal project", "All 4 criteria missing"],
    },
    {
        "course": "P5 Metals 1",
        "student": "Student 8348",
        "quality": "partial",
        "file": "Inman Phonestand POP.pdf",
        "criteria": [
            {
                "name": "Design Intent & Problem Statement",
                "completeness": "partial",
                "observation": "Clearly states problem. Aims for 'elegant' design minimizing material. Target phone specified.",
                "questions": [
                    "How did wanting elegance and minimal waste influence specific design choices?",
                    "Beyond holding a phone, what properties of sheet metal made it a good choice?",
                ],
            },
            {
                "name": "Plan of Procedure (Step-by-Step)",
                "completeness": "partial",
                "observation": "Iterative process documented. Mentions sheet metal cutter and cornice brake. Documented what actually happened, not what was planned.",
                "questions": [
                    "Could you add dimensions and angles for your final prototype?",
                    "Which type of cutter did you use and why?",
                ],
            },
            {
                "name": "Materials & Tools List",
                "completeness": "partial",
                "observation": "BOM lists initial scrap (18 gauge, 12x12 galvanized). Missing final dimensions and consolidated tools list.",
                "questions": [
                    "Could you add the final dimensions for your finished stand?",
                    "Could you create a separate tools list?",
                ],
            },
            {
                "name": "Reflection & Writing Quality",
                "completeness": "complete",
                "observation": "Thoughtful reflection on cardboard vs. sheet metal properties. Clear articulation of iterative progression.",
                "questions": [
                    "How did understanding material differences change your final design?",
                    "What was most surprising about moving from cardboard to metal?",
                ],
            },
        ],
        "flags": ["Lost dimensioned sketch (acknowledged)", "Teacher initials column empty", "No consolidated tools list"],
    },
    {
        "course": "P5 Metals 1",
        "student": "Student 8430",
        "quality": "partial",
        "file": "phone holder POP Template.pdf",
        "criteria": [
            {
                "name": "Design Intent & Problem Statement",
                "completeness": "missing",
                "observation": "No problem statement or design intent section. Purpose implied by title only.",
                "questions": [
                    "What problem or need were you addressing?",
                    "Why did you choose these specific dimensions and triangular shape?",
                ],
            },
            {
                "name": "Plan of Procedure (Step-by-Step)",
                "completeness": "partial",
                "observation": "12 numbered steps with some tools and measurements. Relies heavily on hot glue. Some unclear step details.",
                "questions": [
                    "What safety precautions for collecting and cutting sheet metal?",
                    "Is the 1/2x3\" piece separate or a bent section of the 6.5\" piece?",
                ],
            },
            {
                "name": "Materials & Tools List",
                "completeness": "partial",
                "observation": "BOM table provided. Thickness column blank. No separate tools list. Dimensions differ from procedure.",
                "questions": [
                    "Please fill in the thickness for each piece.",
                    "How do BOM dimensions relate to procedure cut dimensions?",
                ],
            },
            {
                "name": "Reflection & Writing Quality",
                "completeness": "missing",
                "observation": "No dedicated reflection section.",
                "questions": [
                    "What did you learn while developing this plan?",
                    "What changes might you make to your design?",
                ],
            },
        ],
        "flags": ["Missing design intent", "Missing reflection", "BOM vs. procedure dimension discrepancy", "No dimensioned drawing"],
    },
    # ── P5 Metals 2 ──
    {
        "course": "P5 Metals 2",
        "student": "Student 10263",
        "quality": "minimal",
        "file": "POP Template.docx",
        "criteria": [
            {
                "name": "Design Intent & Problem Statement",
                "completeness": "missing",
                "observation": "Contains drawing prompt only. No student content.",
                "questions": [
                    "What specific problem is your stand designed to solve?",
                    "Why did you choose certain materials or angles?",
                ],
            },
            {
                "name": "Plan of Procedure (Step-by-Step)",
                "completeness": "missing",
                "observation": "'PLAN STEPS:' heading and instruction only. No steps from student.",
                "questions": [
                    "Could you list specific numbered steps to fabricate your stand?",
                    "What tools, measurements, and safety for each step?",
                ],
            },
            {
                "name": "Materials & Tools List",
                "completeness": "missing",
                "observation": "BOM heading with 'Wood Required' -- wrong material for sheet metal project.",
                "questions": [
                    "What type and dimensions of sheet metal will you use?",
                    "What tools do you anticipate needing?",
                ],
            },
            {
                "name": "Reflection & Writing Quality",
                "completeness": "missing",
                "observation": "Template prompts only. No student reflection.",
                "questions": [
                    "What did you find most challenging during planning?",
                    "What would you approach differently?",
                ],
            },
        ],
        "flags": ["Template only -- no student content", "'Wood Required' for metal project", "All 4 criteria missing"],
    },
    {
        "course": "P5 Metals 2",
        "student": "Student 4823",
        "quality": "minimal",
        "file": "1771870447.80859.jpg (photo only)",
        "criteria": [
            {
                "name": "Design Intent & Problem Statement",
                "completeness": "missing",
                "observation": "Photo shows completed stand. No written problem statement or design justification.",
                "questions": [
                    "What specific problem were you solving with this stand?",
                    "Why did you choose this type of metal?",
                ],
            },
            {
                "name": "Plan of Procedure (Step-by-Step)",
                "completeness": "missing",
                "observation": "Photo shows finished product with cuts and bends. No written procedure.",
                "questions": [
                    "Could you outline the step-by-step process from start to finish?",
                    "What tools did you use for cutting and bending?",
                ],
            },
            {
                "name": "Materials & Tools List",
                "completeness": "missing",
                "observation": "Photo shows sheet metal material. No written list.",
                "questions": [
                    "What kind of sheet metal and starting dimensions?",
                    "Could you list all tools used?",
                ],
            },
            {
                "name": "Reflection & Writing Quality",
                "completeness": "missing",
                "observation": "Photo only. No written reflection. Stand shows raw finish with surface scratches and tool marks.",
                "questions": [
                    "What was the most challenging part of making your stand?",
                    "What would you do differently next time?",
                ],
            },
        ],
        "flags": ["Photo only -- entire writeup component missing", "Raw metal finish with scratches", "No written content at all"],
    },
]


# ── PDF Building ──────────────────────────────────────────────

def _styles():
    ss = getSampleStyleSheet()
    s = {}
    s["title"] = ParagraphStyle("T", parent=ss["Title"], fontSize=26, leading=32, textColor=C_BLUE, spaceAfter=4)
    s["subtitle"] = ParagraphStyle("Sub", parent=ss["Normal"], fontSize=13, leading=17, textColor=C_MEDIUM, alignment=TA_CENTER)
    s["h1"] = ParagraphStyle("H1", parent=ss["Heading1"], fontSize=16, leading=20, textColor=C_BLUE, spaceBefore=10, spaceAfter=6)
    s["h2"] = ParagraphStyle("H2", parent=ss["Heading2"], fontSize=13, leading=16, textColor=colors.HexColor("#1565C0"), spaceBefore=8, spaceAfter=4)
    s["h3"] = ParagraphStyle("H3", parent=ss["Heading3"], fontSize=11, leading=14, textColor=C_DARK, spaceBefore=6, spaceAfter=3)
    s["body"] = ParagraphStyle("B", parent=ss["Normal"], fontSize=9, leading=12)
    s["body_italic"] = ParagraphStyle("BI", parent=ss["Normal"], fontSize=9, leading=12, textColor=C_MEDIUM)
    s["small"] = ParagraphStyle("Sm", parent=ss["Normal"], fontSize=8, leading=10, textColor=C_MEDIUM)
    s["question"] = ParagraphStyle("Q", parent=ss["Normal"], fontSize=9, leading=12, leftIndent=18, textColor=colors.HexColor("#1565C0"))
    s["flag"] = ParagraphStyle("F", parent=ss["Normal"], fontSize=8, leading=10, leftIndent=18, textColor=C_RED)
    s["cell"] = ParagraphStyle("C", parent=ss["Normal"], fontSize=8, leading=10)
    s["cell_center"] = ParagraphStyle("CC", parent=ss["Normal"], fontSize=8, leading=10, alignment=TA_CENTER)
    s["cell_header"] = ParagraphStyle("CH", parent=ss["Normal"], fontSize=8, leading=10, textColor=C_WHITE, alignment=TA_CENTER)
    s["metric_big"] = ParagraphStyle("MB", parent=ss["Normal"], fontSize=22, leading=26, textColor=C_BLUE, alignment=TA_CENTER)
    s["metric_label"] = ParagraphStyle("ML", parent=ss["Normal"], fontSize=9, leading=11, textColor=C_MEDIUM, alignment=TA_CENTER)
    return s


def _header_footer(canvas_obj, doc):
    canvas_obj.saveState()
    canvas_obj.setStrokeColor(C_BLUE)
    canvas_obj.setLineWidth(1)
    canvas_obj.line(0.75*inch, 10.25*inch, 7.75*inch, 10.25*inch)
    canvas_obj.setFont("Helvetica", 8)
    canvas_obj.setFillColor(C_MEDIUM)
    canvas_obj.drawString(0.75*inch, 10.35*inch, "Agent Swarm Review Report -- POP Writeup")
    canvas_obj.drawRightString(7.75*inch, 10.35*inch, datetime.now().strftime("%B %d, %Y"))
    canvas_obj.setFont("Helvetica", 8)
    canvas_obj.drawCentredString(4.25*inch, 0.5*inch, f"Page {doc.page}")
    canvas_obj.restoreState()


def build_pdf(output_path):
    sty = _styles()
    elements = []

    # ── Cover ─────────────────────────────────────────────
    elements.append(Spacer(1, 1.8*inch))
    elements.append(Paragraph("Agent Swarm<br/>Review Report", sty["title"]))
    elements.append(Spacer(1, 0.2*inch))
    elements.append(Paragraph("Sheet Metal Cell Phone Stand -- POP Writeup", sty["subtitle"]))
    elements.append(Spacer(1, 0.1*inch))
    elements.append(Paragraph("CTE Metals, Bend-La Pine Schools", sty["subtitle"]))
    elements.append(Spacer(1, 0.1*inch))
    elements.append(Paragraph("Instructor: Andrew McAteer", sty["subtitle"]))
    elements.append(Spacer(1, 0.5*inch))

    # Cover metrics
    total_students = len(REVIEWS)
    total_questions = sum(len(q) for r in REVIEWS for c in r["criteria"] for q in [c["questions"]])
    quality_counts = {}
    for r in REVIEWS:
        quality_counts[r["quality"]] = quality_counts.get(r["quality"], 0) + 1
    completeness_counts = {"complete": 0, "partial": 0, "missing": 0, "minimal": 0}
    for r in REVIEWS:
        for c in r["criteria"]:
            comp = c["completeness"]
            completeness_counts[comp] = completeness_counts.get(comp, 0) + 1

    metrics_data = [
        [
            Paragraph(f"<b>{total_students}</b>", sty["metric_big"]),
            Paragraph(f"<b>{total_questions}</b>", sty["metric_big"]),
            Paragraph(f"<b>{completeness_counts.get('complete', 0)}</b>", sty["metric_big"]),
            Paragraph(f"<b>{completeness_counts.get('missing', 0) + completeness_counts.get('minimal', 0)}</b>", sty["metric_big"]),
        ],
        [
            Paragraph("Students Reviewed", sty["metric_label"]),
            Paragraph("Clarifying Questions", sty["metric_label"]),
            Paragraph("Criteria Complete", sty["metric_label"]),
            Paragraph("Criteria Missing", sty["metric_label"]),
        ],
    ]
    mt = Table(metrics_data, colWidths=[1.6*inch]*4)
    mt.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOX", (0, 0), (-1, -1), 0.5, C_BLUE),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8F9FA")),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 8),
    ]))
    elements.append(mt)
    elements.append(Spacer(1, 0.5*inch))
    elements.append(Paragraph(
        f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
        sty["subtitle"]
    ))
    elements.append(PageBreak())

    # ── Summary Table ─────────────────────────────────────
    elements.append(Paragraph("Submission Overview", sty["h1"]))
    elements.append(Spacer(1, 0.1*inch))

    header = [
        Paragraph("<b>Student</b>", sty["cell_header"]),
        Paragraph("<b>Course</b>", sty["cell_header"]),
        Paragraph("<b>Quality</b>", sty["cell_header"]),
        Paragraph("<b>Design</b>", sty["cell_header"]),
        Paragraph("<b>Procedure</b>", sty["cell_header"]),
        Paragraph("<b>Materials</b>", sty["cell_header"]),
        Paragraph("<b>Reflection</b>", sty["cell_header"]),
    ]
    rows = [header]
    table_style = [
        ("BACKGROUND", (0, 0), (-1, 0), C_BLUE),
        ("TEXTCOLOR", (0, 0), (-1, 0), C_WHITE),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E0E0E0")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (2, 0), (-1, -1), "CENTER"),
    ]

    for i, r in enumerate(REVIEWS):
        row_idx = i + 1
        criteria_status = []
        for c in r["criteria"]:
            comp = c["completeness"]
            icon = {"complete": "OK", "partial": "~", "missing": "X", "minimal": "!"}
            criteria_status.append(Paragraph(icon.get(comp, "?"), sty["cell_center"]))

        # Pad to 4 criteria
        while len(criteria_status) < 4:
            criteria_status.append(Paragraph("-", sty["cell_center"]))

        row = [
            Paragraph(r["student"], sty["cell"]),
            Paragraph(r["course"], sty["cell"]),
            Paragraph(r["quality"].upper(), sty["cell_center"]),
        ] + criteria_status[:4]
        rows.append(row)

        # Color the quality cell
        qc = QUALITY_BG.get(r["quality"], C_LIGHT_GRAY)
        table_style.append(("BACKGROUND", (2, row_idx), (2, row_idx), qc))

        # Color each criterion cell
        for ci, c in enumerate(r["criteria"][:4]):
            bg = QUALITY_BG.get(c["completeness"], C_LIGHT_GRAY)
            table_style.append(("BACKGROUND", (3+ci, row_idx), (3+ci, row_idx), bg))

        if row_idx % 2 == 0:
            table_style.append(("BACKGROUND", (0, row_idx), (1, row_idx), C_LIGHT_GRAY))

    summary_table = Table(rows, colWidths=[1.2*inch, 1.0*inch, 0.65*inch, 0.7*inch, 0.75*inch, 0.7*inch, 0.75*inch])
    summary_table.setStyle(TableStyle(table_style))
    elements.append(summary_table)

    elements.append(Spacer(1, 0.15*inch))
    legend_data = [[
        "", Paragraph("Complete", sty["small"]),
        "", Paragraph("Partial", sty["small"]),
        "", Paragraph("Missing/Minimal", sty["small"]),
    ]]
    legend = Table(legend_data, colWidths=[0.18*inch, 0.9*inch, 0.18*inch, 0.7*inch, 0.18*inch, 1.1*inch])
    legend.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), C_GREEN),
        ("BACKGROUND", (2, 0), (2, 0), C_AMBER),
        ("BACKGROUND", (4, 0), (4, 0), C_RED),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    elements.append(legend)

    # ── Common Patterns ───────────────────────────────────
    elements.append(Spacer(1, 0.3*inch))
    elements.append(Paragraph("Common Patterns Across Submissions", sty["h2"]))
    patterns = [
        "<b>Hot glue on metal:</b> Flagged on 5+ students. Students choosing hot glue for sheet metal assembly instead of welding, riveting, or mechanical fasteners.",
        "<b>Missing reflection sections:</b> Most students skipped or left blank the reflection component.",
        "<b>Template text left in:</b> Several students submitted documents with template instructions, highlighted placeholders, or 'Wood Required' prompts still visible.",
        "<b>Missing BOM/tools lists:</b> Even students with good procedures failed to provide a consolidated materials and tools list.",
        "<b>Vague procedure steps:</b> Many procedures lack specific dimensions, bend angles, and tool callouts.",
    ]
    for p in patterns:
        elements.append(Paragraph(f"  {p}", sty["body"]))
        elements.append(Spacer(1, 0.05*inch))

    elements.append(PageBreak())

    # ── Per-Student Detail ────────────────────────────────
    current_course = None
    for r in REVIEWS:
        if r["course"] != current_course:
            current_course = r["course"]
            elements.append(Paragraph(current_course, sty["h1"]))

        # Student card
        student_elements = []
        student_elements.append(Paragraph(f"{r['student']}", sty["h2"]))

        # Quality badge + file
        qcolor = QUALITY_COLORS.get(r["quality"], C_GRAY)
        student_elements.append(Paragraph(
            f'<font color="{qcolor.hexval()}">[{r["quality"].upper()}]</font>'
            f'  <font color="#616161">{r["file"]}</font>',
            sty["body"]
        ))
        student_elements.append(Spacer(1, 0.1*inch))

        # Each criterion
        for c in r["criteria"]:
            comp = c["completeness"]
            cc = COMPLETENESS_COLORS.get(comp, C_GRAY)
            student_elements.append(Paragraph(
                f'<font color="{cc.hexval()}">[{comp.upper()}]</font> <b>{c["name"]}</b>',
                sty["h3"]
            ))
            student_elements.append(Paragraph(c["observation"], sty["body_italic"]))

            for q in c["questions"]:
                student_elements.append(Paragraph(f"? {q}", sty["question"]))
            student_elements.append(Spacer(1, 0.08*inch))

        # Flags
        if r["flags"]:
            student_elements.append(Paragraph("<b>Flags:</b>", sty["small"]))
            for f in r["flags"]:
                student_elements.append(Paragraph(f"  - {f}", sty["flag"]))

        student_elements.append(Spacer(1, 0.25*inch))

        # Keep student card together if possible
        elements.append(KeepTogether(student_elements))

    # Build
    script_dir = os.path.dirname(os.path.abspath(__file__))
    doc = SimpleDocTemplate(
        output_path, pagesize=letter,
        leftMargin=0.75*inch, rightMargin=0.75*inch,
        topMargin=1*inch, bottomMargin=0.75*inch,
    )
    doc.build(elements, onFirstPage=_header_footer, onLaterPages=_header_footer)
    print(f"\n  PDF saved: {output_path}")


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    date_str = datetime.now().strftime("%Y-%m-%d")
    output = os.path.join(script_dir, f"swarm_review_pop_{date_str}.pdf")
    build_pdf(output)
