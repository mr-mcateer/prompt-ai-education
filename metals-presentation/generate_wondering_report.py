#!/usr/bin/env python3
"""
Generate PDF report of teacher wonderings from a grading session.
BLUF (Bottom Line Up Front) executive brief format.

Usage:
    python3 generate_wondering_report.py
"""

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
C_WONDERING_BG = colors.HexColor("#F0F4F8")

QUALITY_COLORS = {
    "complete": C_GREEN,
    "partial": C_AMBER,
    "minimal": C_RED,
}

QUALITY_BG = {
    "complete": C_LIGHT_GREEN,
    "partial": C_LIGHT_AMBER,
    "minimal": C_LIGHT_RED,
}

REPORT_DATE = "February 24, 2026"

# -- Course ordering (period order: P1, P3, P5) ------------------------
COURSE_ORDER = [
    "P1 Engines Fab 2",
    "P3 Metals 1",
    "P3 Metals 2",
    "P5 Metals 1",
    "P5 Metals 2",
]

COURSE_INFO = {
    "P1 Engines Fab 2": {"period": "Period 1", "section": "Engines & Fabrication 2", "course_id": 23344},
    "P3 Metals 1":      {"period": "Period 3", "section": "Metals 1",               "course_id": 23164},
    "P3 Metals 2":      {"period": "Period 3", "section": "Metals 2",               "course_id": 23132},
    "P5 Metals 1":      {"period": "Period 5", "section": "Metals 1",               "course_id": 23188},
    "P5 Metals 2":      {"period": "Period 5", "section": "Metals 2",               "course_id": 23177},
}

# -- Hardcoded wonderings from the 2026-02-24 grading session -----------

WONDERINGS = [
    # P3 Metals 1 (23164)
    {"course": "P3 Metals 1", "assignment": "Portable Tool Organizer - SolidWorks", "student": "Student 4586", "quality": "complete", "files": ["Holmboe_Simon_Tray.stl"], "wondering": "Looking at your tray, I can see it fitting into an organizer -- are you planning on adding dividers inside it later?"},
    {"course": "P3 Metals 1", "assignment": "Portable Tool Organizer - SolidWorks", "student": "Student 8384", "quality": "complete", "files": ["Iain_Bailes_Tool Holder for Bob Lid.SLDPRT", "Tool Holder for Bob Middle Tier.SLDPRT", "Tool Holder for Bob Top Tier.SLDPRT", "Tool Holder for Bob bottom tier.SLDPRT"], "wondering": "Looking at your files, I'm curious about the 'for Bob' part in all the names. Is Bob the lucky recipient of this awesome tool organizer, or is there a story behind that?"},
    {"course": "P3 Metals 1", "assignment": "Portable Tool Organizer - SolidWorks", "student": "Student 8435", "quality": "complete", "files": ["bobsbox 2.stl", "Bobs Box 1.stl", "bobsbox 3.stl"], "wondering": "Hey, looking at your files -- I see you've got 'bobsbox+1', '+2', and '+3' here. Are those all separate parts that'll connect for your organizer, or different design ideas you were exploring?"},
    {"course": "P3 Metals 1", "assignment": "Portable Tool Organizer - SolidWorks", "student": "Student 11921", "quality": "complete", "files": ["BOBs toolbox_KB_(bottom).SLDPRT", "BOB's toolbox_KB (top).SLDPRT", "BOB's toolbox_KB (middle).SLDPRT"], "wondering": "Hey, quick question -- I'm just curious about the 'BOB's' in the file names for your toolbox parts. Is that a specific type of organizer you're modeling or is it for someone named Bob?"},
    {"course": "P3 Metals 1", "assignment": "Portable Tool Organizer - SolidWorks", "student": "Student 21134", "quality": "complete", "files": ["bottom tray.SLDPRT"], "wondering": "Curious about your decision to put the bottom and tray in a single part file. What was your thinking behind integrating them like that instead of separate parts?"},
    {"course": "P3 Metals 1", "assignment": "Sheet Metal Cell Phone Stand - POP Writeup", "student": "Student 4586", "quality": "complete", "files": ["Phone Holder POP.pdf"], "wondering": "I noticed your Pro Tip about adding 0.5-1mm extra to account for the metal thickness eating into the internal space. Did that small adjustment make a big difference when you went to fit the actual phone?"},
    {"course": "P3 Metals 1", "assignment": "Sheet Metal Cell Phone Stand - POP Writeup", "student": "Student 8384", "quality": "partial", "files": ["Iain_Bailes_Phone Holder POP.pdf"], "wondering": "Iain, looking at your plan, you're using the 'sheet metal cutter' for Pieces B and D, but then the Plasma CNC for A and C. Curious if there's a specific reason you're splitting up the cutting methods for different parts?"},
    {"course": "P3 Metals 1", "assignment": "Sheet Metal Cell Phone Stand - POP Writeup", "student": "Student 8435", "quality": "complete", "files": ["Plan of procedures phone holder.pdf"], "wondering": "Looking at your plan, the way you describe measuring the 'Geometric Side Triangles' after angling the main plates (Step 3) is pretty smart. I'm wondering if you've tried dry-fitting it yet to see how those angles might change with different phone sizes or viewing preferences?"},
    {"course": "P3 Metals 1", "assignment": "Sheet Metal Cell Phone Stand - POP Writeup", "student": "Student 11921", "quality": "complete", "files": ["Plan of Procedure_ Sheet Metal Phone Dock.pdf"], "wondering": "Kaydenn, looking at your POP-- I saw you mentioned deburring a drilled hole and checking the charging cable in your rubric. I was curious where you planned to add the actual drilling step for that hole?"},
    {"course": "P3 Metals 1", "assignment": "Sheet Metal Cell Phone Stand - POP Writeup", "student": "Student 21134", "quality": "complete", "files": ["pop metal phone stand.docx"], "wondering": "I can see you mentioned hot glue or welding for the main lean -- that's a pretty wide range of joining methods! Were you thinking about different versions of the stand, or just giving options?"},
    {"course": "P3 Metals 1", "assignment": "Campus Handrail Plaque - Design & Fabrication", "student": "Student 4586", "quality": "complete", "files": ["Bodacious Vihelmo-Jaban.stl"], "wondering": "Looking at your file, 'Bodacious+Vihelmo-Jaban.stl' -- I'm curious about the 'Bodacious' part. Does that refer to a specific design style you're going for with the handrail plaque?"},
    {"course": "P3 Metals 1", "assignment": "Campus Handrail Plaque - Design & Fabrication", "student": "Student 8384", "quality": "complete", "files": ["Bailes_Iain_Raider Logo for Railing v3 (Finished) RECTANGLE.svg"], "wondering": "Looking at your design, Iain, the detail on the Raider logo is really clean. How are you imagining this piece will attach to the handrail once it's fabricated?"},
    {"course": "P3 Metals 1", "assignment": "Campus Handrail Plaque - Design & Fabrication", "student": "Student 8435", "quality": "complete", "files": ["handrail Plaque.svg"], "wondering": "Looking at your design, I see how the plaque will sit on the handrail. Did you think about how the handrail's curve might affect how it attaches?"},
    {"course": "P3 Metals 1", "assignment": "Campus Handrail Plaque - Design & Fabrication", "student": "Student 21134", "quality": "complete", "files": ["travis.martinez.tile.ai"], "wondering": "Looking at your design for the plaque, I noticed the school logo is pretty close to the top edge. Was that specific placement something you planned for a particular reason?"},
    {"course": "P3 Metals 1", "assignment": "The Exorcism of the Plasma Cutter - Practice Lab", "student": "Student 8384", "quality": "complete", "files": ["CVXC v2.svg", "Screenshot.png", "Exorcism of Plasma Cutter Sign.stl"], "wondering": "Hey, this looks pretty solid for the plasma cutter practice. I'm curious -- is there a story behind the 'CVXC' letters you picked for your design?"},
    {"course": "P3 Metals 1", "assignment": "The Exorcism of the Plasma Cutter - Practice Lab", "student": "Student 21134", "quality": "complete", "files": ["bbrs.svg"], "wondering": "Hey, quick question -- I was looking at your bbrs.svg file. Did you intentionally leave out lead-ins and lead-outs on those cuts, or are you planning to add those in the CAM software before cutting?"},
    {"course": "P3 Metals 1", "assignment": "Shop Cleanup - Thursday 2/5", "student": "Student 8384", "quality": "complete", "files": ["text_entry"], "wondering": "I noticed you mentioned sweeping around the tables in the center -- did you find a lot of metal shavings or mostly dust out there?"},
    # P3 Metals 2 (23132)
    {"course": "P3 Metals 2", "assignment": "Portable Tool Organizer - SolidWorks", "student": "Student 8354", "quality": "complete", "files": ["Ziniker_Lincoln_ToolOrganizerMIDDLE.SLDPRT", "ToolOrganizerTOP.SLDPRT", "ToolOrganizerBOTTOM.SLDPRT"], "wondering": "Hey Lincoln, looking at your SolidWorks parts for the organizer -- having separate TOP, MIDDLE, and BOTTOM sections is neat. Are you thinking of making the middle section stackable, or will it be a fixed part of the overall assembly?"},
    {"course": "P3 Metals 2", "assignment": "Sheet Metal Cell Phone Stand - POP Writeup", "student": "Student 4671", "quality": "complete", "files": ["Sheet Metal P.O.P - AG.pdf"], "wondering": "Hey Audrey, I noticed in your reflection you mentioned the industrial hot glue was surprisingly durable for assembling the stand. Did you try out any other joining methods that didn't work as well before deciding on the hot glue for this project?"},
    {"course": "P3 Metals 2", "assignment": "Sheet Metal Cell Phone Stand - POP Writeup", "student": "Student 8370", "quality": "complete", "files": ["Dawson phone holder POP.docx"], "wondering": "Hey, quick question -- I see you're planning to use glue to put all the sheet metal pieces together. What made you decide on glue for this project?"},
    {"course": "P3 Metals 2", "assignment": "The Exorcism of the Plasma Cutter - Practice Lab", "student": "Student 8370", "quality": "complete", "files": ["Baseball Logo 1.svg", "CVHS Baseball.stl"], "wondering": "Looking at your files, I noticed the `CVHS+Baseball.stl` file. I'm curious if you had a specific plan for how that 3D model would fit into our plasma cutter practice, or if you were thinking ahead to another machine?"},
    # P5 Metals 1 (23188)
    {"course": "P5 Metals 1", "assignment": "Portable Tool Organizer - SolidWorks", "student": "Student 1320", "quality": "complete", "files": ["Exquisite Kup-Elzing.stl"], "wondering": "I noticed your file name includes 'Exquisite+Kup'. Is that 'Kup' section designed to hold something specific, like a measuring tape or small bits?"},
    {"course": "P5 Metals 1", "assignment": "Portable Tool Organizer - SolidWorks", "student": "Student 1768", "quality": "partial", "files": ["Ellis_ToolOrganizerRoof.SLDPRT", "Ellis_ToolOrganizerHandle.SLDPRT", "Ellis_ToolOrganizerSecondShelf.SLDPRT", "Ellis_ToolOrganizerBaseShelf.SLDPRT"], "wondering": "Ellis, these part files for your organizer are looking good -- I can clearly see the roof and shelves taking shape. I'm curious if you've started modeling the side walls or any other structural pieces that will hold it all together?"},
    {"course": "P5 Metals 1", "assignment": "Portable Tool Organizer - SolidWorks", "student": "Student 3623", "quality": "complete", "files": ["McKeown_North_ToolOrganizerBottom.SLDPRT", "ToolOrganizerMiddle.SLDPRT", "ToolOrganizerTop.SLDPRT"], "wondering": "Looking at your three separate SolidWorks files for the organizer, it's cool to see the layered approach. I'm wondering if you've already thought about how you'll access tools in the middle section once it's all put together?"},
    {"course": "P5 Metals 1", "assignment": "Portable Tool Organizer - SolidWorks", "student": "Student 8348", "quality": "complete", "files": ["Inman_ToolOrganizer.SLDPRT"], "wondering": "I can see you've got some good compartments laid out in there. I'm wondering if you designed those for any specific tools you have in mind?"},
    {"course": "P5 Metals 1", "assignment": "Portable Tool Organizer - SolidWorks", "student": "Student 8430", "quality": "complete", "files": ["bob bottom box.SLDPRT", "bob top box.SLDPRT", "bob middle box.SLDPRT"], "wondering": "Hey, I see you've got the top, middle, and bottom sections modeled out. I'm curious -- what's your plan for how these will connect or stack together in the final portable organizer?"},
    {"course": "P5 Metals 1", "assignment": "Portable Tool Organizer - SolidWorks", "student": "Student 11596", "quality": "complete", "files": ["Smith_ToolOrganizer.SLDASM"], "wondering": "Hey, looking at your `ToolOrganizer.SLDASM` file -- I'm curious if you modeled all the individual parts for it, or if you brought in some standard components from the SolidWorks library?"},
    {"course": "P5 Metals 1", "assignment": "Portable Tool Organizer - SolidWorks", "student": "Student 20460", "quality": "complete", "files": ["Slupe_ToolOrganizer.zip"], "wondering": "Looking at your Portable Tool Organizer design -- I'm wondering if you considered adding any kind of latching mechanism, or if it's meant to stay open?"},
    {"course": "P5 Metals 1", "assignment": "Portable Tool Organizer - SolidWorks", "student": "Student 20528", "quality": "complete", "files": ["bob box.SLDPRT", "bob box lid.SLDPRT", "bob box Assem1.SLDASM", "bob midSLDPRT.SLDPRT", "bob top.SLDPRT"], "wondering": "I was looking at your files for the tool organizer, and I noticed the 'bob+' prefix on all your part names -- like 'bob+box.SLDPRT'. Was there a specific reason or story behind calling it 'bob'?"},
    {"course": "P5 Metals 1", "assignment": "Portable Tool Organizer - SolidWorks", "student": "Student 20756", "quality": "complete", "files": ["Bottom Tool Caddy-Hans.SLDPRT", "Tool Caddy_HAns.SLDASM", "Middle Tool Caddy- Hans.SLDPRT", "Tool Caddy Cover- Hans.SLDPRT", "Top Tool Caddy-Hans.SLDPRT"], "wondering": "Hey Hans, looking at your 'Tool Caddy_HAns.SLDASM', I'm curious if you designed the 'Middle Tool Caddy' to be modular, or if it's fixed in place?"},
    {"course": "P5 Metals 1", "assignment": "Portable Tool Organizer - SolidWorks", "student": "Student 22591", "quality": "complete", "files": ["Rutherford_Cordell_tool tray organizer.png"], "wondering": "Hey, quick question -- I'm curious about that little blue piece with the two holes sticking up from the top tray. What's the plan for that part?"},
    {"course": "P5 Metals 1", "assignment": "Sheet Metal Cell Phone Stand - POP Writeup", "student": "Student 1320", "quality": "complete", "files": ["Morris_PhoneStand_POP.docx"], "wondering": "Hey, that's an interesting safety tip about rubbing the metal edges on a concrete sidewalk. Is that a technique you've actually used before, or did you learn it somewhere else?"},
    {"course": "P5 Metals 1", "assignment": "Sheet Metal Cell Phone Stand - POP Writeup", "student": "Student 1768", "quality": "complete", "files": ["Sheet Metal Phone Stand POP.docx"], "wondering": "Hey Calan, I can see you're thinking through the build process. You mentioned using hot glue in the description, but then folding the metal in the procedure--what changed your mind there?"},
    {"course": "P5 Metals 1", "assignment": "Sheet Metal Cell Phone Stand - POP Writeup", "student": "Student 3623", "quality": "partial", "files": ["McKeown_North_PhoneStandPOPTemplate.pdf"], "wondering": "Hey North, looking at your POP--I noticed you're planning to use hot glue in steps 5, 6, and 7. What was your thinking behind using hot glue for a metal project?"},
    {"course": "P5 Metals 1", "assignment": "Sheet Metal Cell Phone Stand - POP Writeup", "student": "Student 8348", "quality": "complete", "files": ["Inman_Phonestand_POP.pdf"], "wondering": "Hey, quick question -- I saw you used hot glue to put together your initial prototype pieces. How did that hold up for testing, or did you try anything else to temporarily join them?"},
    {"course": "P5 Metals 1", "assignment": "Sheet Metal Cell Phone Stand - POP Writeup", "student": "Student 8430", "quality": "partial", "files": ["phone holderPOP Template.pdf"], "wondering": "Hey Odin, I'm checking out your POP for the phone stand. I'm curious about using hot glue for the main assembly -- what made you choose that over, say, rivets or a different kind of joint for the sheet metal?"},
    {"course": "P5 Metals 1", "assignment": "Sheet Metal Cell Phone Stand - POP Writeup", "student": "Student 11596", "quality": "complete", "files": ["Copy of POP Template.pdf"], "wondering": "Hey, Jackson-- Looking at your assembly steps, I noticed you planned to use hot glue to attach the two main pieces in step 13. What made you decide on hot glue there instead of a different fastening method for the final connection?"},
    {"course": "P5 Metals 1", "assignment": "Sheet Metal Cell Phone Stand - POP Writeup", "student": "Student 20528", "quality": "complete", "files": ["Plan of Procedure_ Sheet Metal Phone Dock.pdf"], "wondering": "Hey Matthew, I noticed you listed hot glue for 'Edge Treatment' in step 5. Are you using that just to temporarily hold things while you work, or is it part of the final assembly for the stand?"},
    {"course": "P5 Metals 1", "assignment": "Sheet Metal Cell Phone Stand - POP Writeup", "student": "Student 20623", "quality": "complete", "files": ["Phone Holder POP.docx"], "wondering": "Hey Bodhi -- looking at your POP, I'm curious about using thermal polymer adhesive for structural bonding. Did you test out different adhesives, or was hot glue chosen for a specific reason?"},
    {"course": "P5 Metals 1", "assignment": "Sheet Metal Cell Phone Stand - POP Writeup", "student": "Student 20756", "quality": "partial", "files": ["Pop template-Hans Phone stand.docx"], "wondering": "Hey, quick question -- I noticed your Bill of Materials section mentions 'wood required' for this project. Are you thinking about incorporating a different material into your sheet metal stand, or is that just a placeholder for now?"},
    {"course": "P5 Metals 1", "assignment": "Campus Handrail Plaque - Design & Fabrication", "student": "Student 1320", "quality": "complete", "files": ["Terrific Fulffy-Vihelmo.svg"], "wondering": "Hey, looking at your .svg file -- I'm curious about the 'Fulffy' part of the name. Is that a specific texture or design style you're planning to achieve with the metal for the plaque?"},
    {"course": "P5 Metals 1", "assignment": "Campus Handrail Plaque - Design & Fabrication", "student": "Student 20623", "quality": "complete", "files": ["Bodhi Railing Sign.zip"], "wondering": "Hey, looking at your 'Bodhi' sign design-- I'm curious about the word 'Bodhi' itself. Was there a specific reason or story behind choosing that name for the handrail plaque?"},
    {"course": "P5 Metals 1", "assignment": "Campus Handrail Plaque - Design & Fabrication", "student": "Student 20756", "quality": "complete", "files": ["sign for rails 33 (2).ai"], "wondering": "Looking at your design file for the handrail plaque -- does the '33' in the filename relate to a specific rail you have in mind on campus?"},
    {"course": "P5 Metals 1", "assignment": "The Exorcism of the Plasma Cutter - Practice Lab", "student": "Student 3623", "quality": "complete", "files": ["McKeown_North_RaiderLogo.dxf", "RaiderLogo.pdf"], "wondering": "Hey, I noticed you included both the DXF and the PDF for your Raider logo. Was there a specific reason you decided to export it as a PDF as well as the DXF?"},
    {"course": "P5 Metals 1", "assignment": "The Exorcism of the Plasma Cutter - Practice Lab", "student": "Student 8348", "quality": "complete", "files": ["celestial_being.dxf", "Screenshot.png", "Celestial Being Symbol.stl"], "wondering": "I can see you put a lot of work into the details on this symbol. I'm wondering how you're thinking about those really fine, thin areas when it comes to the plasma cutter--it'll be interesting to see how it handles those."},
    {"course": "P5 Metals 1", "assignment": "The Exorcism of the Plasma Cutter - Practice Lab", "student": "Student 20460", "quality": "complete", "files": ["Lopez crab sign.svg", "Lopez crab sign.pdf", "Lopez crab sign.dxf"], "wondering": "Good call thinking about the gaps between letters to avoid losing detail with the plasma cutter. How are you planning on making sure those gaps are big enough before you cut it?"},
    {"course": "P5 Metals 1", "assignment": "The Exorcism of the Plasma Cutter - Practice Lab", "student": "Student 20756", "quality": "complete", "files": ["text_entry"], "wondering": "Hey, quick question -- when you were having trouble starting on the thicker metal, did it make a different sound compared to when it was working well on the thinner stuff?"},
    {"course": "P5 Metals 1", "assignment": "Shop Cleanup - Thursday 2/19", "student": "Student 20756", "quality": "minimal", "files": ["text_entry"], "wondering": "Hey, quick question -- when you swept the welding room area, did you get under the welding booths too, or just the main walkways?"},
    {"course": "P5 Metals 1", "assignment": "Shop Cleanup - Thursday 2/5", "student": "Student 20756", "quality": "complete", "files": ["text_entry"], "wondering": "Hey, quick question -- I'm curious what kind of sanding you guys were doing in the welding area today?"},
    # P5 Metals 2 (23177)
    {"course": "P5 Metals 2", "assignment": "Portable Tool Organizer - SolidWorks", "student": "Student 4823", "quality": "complete", "files": ["base Tray1.SLDPRT", "Middle Tray1.SLDPRT", "stack Tray1.SLDPRT"], "wondering": "Hey, looking at your files -- `base+Tray1`, `Middle+Tray1`, and `stack+Tray1` -- I'm curious about the 'Tray1' part of the name. Is that a specific design you're calling 'Tray1', or are you thinking of making different tray versions later?"},
    {"course": "P5 Metals 2", "assignment": "Sheet Metal Cell Phone Stand - POP Writeup", "student": "Student 4823", "quality": "complete", "files": ["1771870447.80859.jpg"], "wondering": "Hey, looking at this stand -- I'm curious about the front lip. Did you intentionally make it a bit narrower than the back panel, or was that just how the material worked out?"},
    {"course": "P5 Metals 2", "assignment": "Sheet Metal Cell Phone Stand - POP Writeup", "student": "Student 10263", "quality": "partial", "files": ["POP Template.docx"], "wondering": "Looking at your POP, I noticed it asks for 'Total Anticipated Wood Required'. Are you planning to use wood for some part of the sheet metal stand, or is that just a leftover from a different template?"},
    {"course": "P5 Metals 2", "assignment": "Campus Handrail Plaque - Design & Fabrication", "student": "Student 10263", "quality": "partial", "files": ["PersonalGuardRailTile.pdf"], "wondering": "Looking at your design here, Abe -- I'm curious if the 'Blown Supercharged V8's All Day!' is just a personal motto, or if you're thinking of incorporating that into the actual handrail plaque somehow?"},
    {"course": "P5 Metals 2", "assignment": "Shop Cleanup - Thursday 2/19", "student": "Student 4823", "quality": "complete", "files": ["text_entry"], "wondering": "Looking at your cleanup note about the welding booths--was it pretty easy to tell if the gas was off at each one?"},
    {"course": "P5 Metals 2", "assignment": "Shop Cleanup - Thursday 2/5", "student": "Student 4823", "quality": "complete", "files": ["text_entry"], "wondering": "Hey, quick question--when you checked the welding booths, did you actually have to turn any of the gas lines off, or were they already good?"},
    # P1 Engines Fab 2 (23344)
    {"course": "P1 Engines Fab 2", "assignment": "Shop Cleanup - Thursday 2/19", "student": "Student 20756", "quality": "complete", "files": ["text_entry"], "wondering": "Hey, quick question -- when you say 'our Engine,' were you working on that with a specific group today?"},
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
    s["metric_big"] = ParagraphStyle(
        "MB", parent=ss["Normal"], fontSize=22, leading=26,
        textColor=C_BLUE, alignment=TA_CENTER,
    )
    s["metric_label"] = ParagraphStyle(
        "ML", parent=ss["Normal"], fontSize=9, leading=11,
        textColor=C_MEDIUM, alignment=TA_CENTER,
    )
    s["wondering_text"] = ParagraphStyle(
        "WT", parent=ss["Normal"], fontSize=9, leading=13,
        leftIndent=12, rightIndent=12, spaceBefore=4, spaceAfter=4,
        textColor=C_DARK,
    )
    s["file_list"] = ParagraphStyle(
        "FL", parent=ss["Normal"], fontSize=7.5, leading=10,
        textColor=C_MEDIUM, leftIndent=6,
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
    canvas_obj.drawString(0.75 * inch, 10.35 * inch, "Grading Action Brief -- Personal Wonderings")
    canvas_obj.drawRightString(7.75 * inch, 10.35 * inch, REPORT_DATE)
    canvas_obj.drawCentredString(4.25 * inch, 0.5 * inch, f"Page {doc.page}")
    canvas_obj.restoreState()


# -- Data helpers --------------------------------------------------------

def _organize_by_course(wonderings):
    """Group wonderings by course, then by assignment within each course."""
    by_course = OrderedDict()
    for course_name in COURSE_ORDER:
        items = [w for w in wonderings if w["course"] == course_name]
        if items:
            by_assignment = OrderedDict()
            for w in items:
                asgn = w["assignment"]
                if asgn not in by_assignment:
                    by_assignment[asgn] = []
                by_assignment[asgn].append(w)
            by_course[course_name] = by_assignment
    return by_course


def _compute_stats(wonderings):
    """Compute summary statistics."""
    courses = set(w["course"] for w in wonderings)
    students = set((w["course"], w["student"]) for w in wonderings)
    quality_counts = {"complete": 0, "partial": 0, "minimal": 0}
    for w in wonderings:
        q = w["quality"]
        quality_counts[q] = quality_counts.get(q, 0) + 1
    assignments_covered = set((w["course"], w["assignment"]) for w in wonderings)
    return {
        "num_courses": len(courses),
        "num_students": len(students),
        "num_wonderings": len(wonderings),
        "num_assignments": len(assignments_covered),
        "quality_counts": quality_counts,
    }


def _course_stats(wonderings):
    """Per-course stats for the summary table."""
    stats = OrderedDict()
    for course_name in COURSE_ORDER:
        items = [w for w in wonderings if w["course"] == course_name]
        if items:
            students = set(w["student"] for w in items)
            stats[course_name] = {
                "students_commented": len(students),
                "wonderings_posted": len(items),
            }
    return stats


# -- Wondering box -------------------------------------------------------

def _wondering_box(wondering_text, sty):
    """Create a shaded box containing the wondering text."""
    inner = Paragraph(
        f'<i>"{wondering_text}"</i>',
        sty["wondering_text"],
    )
    box_table = Table(
        [[inner]],
        colWidths=[6.0 * inch],
    )
    box_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), C_WONDERING_BG),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#B0BEC5")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("ROUNDEDCORNERS", [3, 3, 3, 3]),
    ]))
    return box_table


# -- PDF Construction ----------------------------------------------------

def build_pdf(output_path):
    sty = _styles()
    elements = []
    organized = _organize_by_course(WONDERINGS)
    stats = _compute_stats(WONDERINGS)
    per_course = _course_stats(WONDERINGS)

    # ================================================================
    # COVER PAGE
    # ================================================================
    elements.append(Spacer(1, 1.8 * inch))
    elements.append(Paragraph("Grading Action Brief", sty["title"]))
    elements.append(Spacer(1, 0.15 * inch))
    elements.append(Paragraph(
        f"Personal Wonderings -- {REPORT_DATE}", sty["subtitle"]
    ))
    elements.append(Spacer(1, 0.1 * inch))
    elements.append(Paragraph(
        "CTE Metals &amp; Engines, Bend-La Pine Schools", sty["subtitle"]
    ))
    elements.append(Spacer(1, 0.1 * inch))
    elements.append(Paragraph("Instructor: Andrew McAteer", sty["subtitle"]))
    elements.append(Spacer(1, 0.5 * inch))

    # Cover metrics
    metrics_data = [
        [
            Paragraph(f"<b>{stats['num_courses']}</b>", sty["metric_big"]),
            Paragraph(f"<b>{stats['num_students']}</b>", sty["metric_big"]),
            Paragraph(f"<b>{stats['num_wonderings']}</b>", sty["metric_big"]),
            Paragraph(f"<b>{stats['num_assignments']}</b>", sty["metric_big"]),
        ],
        [
            Paragraph("Courses Covered", sty["metric_label"]),
            Paragraph("Students Commented", sty["metric_label"]),
            Paragraph("Wonderings Generated", sty["metric_label"]),
            Paragraph("Assignments Reviewed", sty["metric_label"]),
        ],
    ]
    mt = Table(metrics_data, colWidths=[1.6 * inch] * 4)
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

    # Quality distribution mini-row
    qc = stats["quality_counts"]
    quality_data = [
        [
            Paragraph(f'<font color="{C_GREEN.hexval()}"><b>{qc.get("complete", 0)}</b></font>', sty["metric_big"]),
            Paragraph(f'<font color="{C_AMBER.hexval()}"><b>{qc.get("partial", 0)}</b></font>', sty["metric_big"]),
            Paragraph(f'<font color="{C_RED.hexval()}"><b>{qc.get("minimal", 0)}</b></font>', sty["metric_big"]),
        ],
        [
            Paragraph("Complete", sty["metric_label"]),
            Paragraph("Partial", sty["metric_label"]),
            Paragraph("Minimal", sty["metric_label"]),
        ],
    ]
    qt = Table(quality_data, colWidths=[2.1 * inch] * 3)
    qt.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOX", (0, 0), (-1, -1), 0.5, C_GRAY),
        ("BACKGROUND", (0, 0), (0, -1), C_LIGHT_GREEN),
        ("BACKGROUND", (1, 0), (1, -1), C_LIGHT_AMBER),
        ("BACKGROUND", (2, 0), (2, -1), C_LIGHT_RED),
        ("TOPPADDING", (0, 0), (-1, 0), 6),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 6),
    ]))
    elements.append(qt)
    elements.append(Spacer(1, 0.4 * inch))

    elements.append(Paragraph(
        f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
        sty["subtitle"],
    ))
    elements.append(PageBreak())

    # ================================================================
    # EXECUTIVE SUMMARY
    # ================================================================
    elements.append(Paragraph("Executive Summary", sty["h1"]))
    elements.append(Spacer(1, 0.15 * inch))

    elements.append(Paragraph(
        "This brief documents all personal wonderings posted to Canvas on the "
        "evening of February 24, 2026. Each wondering is a single, brief "
        "question designed to prompt student thinking about their submitted "
        "work. Wonderings were generated after reviewing file attachments and "
        "text entries across all active assignments.",
        sty["body"],
    ))
    elements.append(Spacer(1, 0.2 * inch))

    # Summary table: Course | Students Commented | Wonderings Posted
    header = [
        Paragraph("<b>Course</b>", sty["cell_header"]),
        Paragraph("<b>Period</b>", sty["cell_header"]),
        Paragraph("<b>Students Commented</b>", sty["cell_header"]),
        Paragraph("<b>Wonderings Posted</b>", sty["cell_header"]),
    ]
    rows = [header]
    ts = [
        ("BACKGROUND", (0, 0), (-1, 0), C_BLUE),
        ("TEXTCOLOR", (0, 0), (-1, 0), C_WHITE),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E0E0E0")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("ALIGN", (2, 0), (-1, -1), "CENTER"),
    ]
    total_students = 0
    total_wonderings = 0
    for i, (cname, cstats) in enumerate(per_course.items()):
        row_idx = i + 1
        info = COURSE_INFO.get(cname, {})
        rows.append([
            Paragraph(cname, sty["cell"]),
            Paragraph(info.get("period", ""), sty["cell_center"]),
            Paragraph(str(cstats["students_commented"]), sty["cell_center"]),
            Paragraph(str(cstats["wonderings_posted"]), sty["cell_center"]),
        ])
        total_students += cstats["students_commented"]
        total_wonderings += cstats["wonderings_posted"]
        if row_idx % 2 == 0:
            ts.append(("BACKGROUND", (0, row_idx), (-1, row_idx), C_LIGHT_GRAY))

    # Totals row
    rows.append([
        Paragraph("<b>TOTAL</b>", sty["cell"]),
        Paragraph("", sty["cell_center"]),
        Paragraph(f"<b>{total_students}</b>", sty["cell_center"]),
        Paragraph(f"<b>{total_wonderings}</b>", sty["cell_center"]),
    ])
    ts.append(("BACKGROUND", (0, len(rows) - 1), (-1, len(rows) - 1), colors.HexColor("#E3F2FD")))
    ts.append(("LINEABOVE", (0, len(rows) - 1), (-1, len(rows) - 1), 1, C_BLUE))

    summary_table = Table(
        rows,
        colWidths=[2.0 * inch, 1.0 * inch, 1.6 * inch, 1.6 * inch],
    )
    summary_table.setStyle(TableStyle(ts))
    elements.append(summary_table)
    elements.append(Spacer(1, 0.25 * inch))

    # Note about no-reviewable-content submissions
    elements.append(Paragraph(
        "<b>Note on scope:</b> Some graded submissions (particularly Shop "
        "Cleanup check-ins and reflection assignments) had no downloadable "
        "file attachments. Where a text entry was present, a wondering was "
        "still generated. Submissions with no reviewable content at all were "
        "skipped entirely and are not listed in this report.",
        sty["body"],
    ))

    # Quality legend
    elements.append(Spacer(1, 0.15 * inch))
    legend_data = [[
        "", Paragraph("<b>Complete</b> -- Full submission with files", sty["small"]),
        "", Paragraph("<b>Partial</b> -- Incomplete or missing elements", sty["small"]),
        "", Paragraph("<b>Minimal</b> -- Very little student content", sty["small"]),
    ]]
    legend = Table(
        legend_data,
        colWidths=[0.18 * inch, 2.1 * inch, 0.18 * inch, 2.1 * inch, 0.18 * inch, 2.1 * inch],
    )
    legend.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), C_GREEN),
        ("BACKGROUND", (2, 0), (2, 0), C_AMBER),
        ("BACKGROUND", (4, 0), (4, 0), C_RED),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    elements.append(legend)

    elements.append(PageBreak())

    # ================================================================
    # DETAIL SECTIONS (one per course, grouped by assignment)
    # ================================================================
    for course_name, assignments in organized.items():
        info = COURSE_INFO.get(course_name, {})
        period = info.get("period", "")
        section = info.get("section", "")
        course_id = info.get("course_id", "")

        # Course header
        elements.append(Paragraph(
            f"{course_name}",
            sty["h1"],
        ))
        elements.append(Paragraph(
            f'{period}  |  {section}  |  Canvas ID: {course_id}',
            sty["body_italic"],
        ))
        elements.append(Spacer(1, 0.15 * inch))

        for assignment_name, items in assignments.items():
            elements.append(Paragraph(
                f"{assignment_name}",
                sty["h2"],
            ))
            elements.append(Spacer(1, 0.05 * inch))

            for w in items:
                student_block = []

                # Student header line with quality badge
                qcolor = QUALITY_COLORS.get(w["quality"], C_GRAY)
                qbg = QUALITY_BG.get(w["quality"], C_LIGHT_GRAY)
                badge = f'<font color="{qcolor.hexval()}">[{w["quality"].upper()}]</font>'
                student_block.append(Paragraph(
                    f'{badge}  <b>{w["student"]}</b>',
                    sty["h3"],
                ))

                # Files
                file_list = w.get("files", [])
                if file_list:
                    files_str = ", ".join(file_list)
                    student_block.append(Paragraph(
                        f"Files: {files_str}",
                        sty["file_list"],
                    ))

                # Wondering box
                student_block.append(Spacer(1, 0.04 * inch))
                student_block.append(_wondering_box(w["wondering"], sty))
                student_block.append(Spacer(1, 0.12 * inch))

                elements.append(KeepTogether(student_block))

        elements.append(Spacer(1, 0.1 * inch))

        # Don't page-break after the very last course
        if course_name != list(organized.keys())[-1]:
            elements.append(PageBreak())

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


if __name__ == "__main__":
    output = os.path.expanduser("~/Downloads/grading_brief_2026-02-24.pdf")
    build_pdf(output)
