#!/usr/bin/env python3
"""
Metal Types Quiz — Canvas LMS Deployment Script
================================================
Aligned to the Metal Types presentation (20 slides).
Designed using instructional design best practices:
  - Bloom's taxonomy levels noted per question (Knowledge / Comprehension / Application)
  - Plausible distractors drawn from actual slide content
  - Specific corrective feedback for every wrong answer
  - No "all of the above" / "none of the above"
  - Stems written as complete questions
  - 2 attempts allowed, auto-graded
  - Due Thursday Feb 26, 2026

Usage:
  # Step 1 — Review quiz locally (no Canvas connection needed):
  python3 quiz_metal_types.py --review

  # Step 2 — List your Canvas courses to find the right course ID:
  python3 quiz_metal_types.py --list-courses

  # Step 3 — Deploy to Canvas:
  python3 quiz_metal_types.py --deploy --course-id <ID>

Environment variables required for Canvas:
  CANVAS_API_URL   e.g. https://yourschool.instructure.com
  CANVAS_API_TOKEN your API access token
"""

import argparse
import json
import os
import sys
import textwrap

# ──────────────────────────────────────────────────────────────
# QUIZ METADATA
# ──────────────────────────────────────────────────────────────
QUIZ_TITLE = "Metal Types — Unit Quiz"
QUIZ_DESCRIPTION = (
    "<p>This quiz covers the Metal Types unit including:</p>"
    "<ul>"
    "<li>Ferrous vs. non-ferrous classification</li>"
    "<li>Metal identification methods</li>"
    "<li>Properties of mild steel, 4140, tool steel, cast iron, "
    "6061 aluminum, copper, brass, titanium, and stainless steel</li>"
    "<li>MIG welding, lathe turning, and milling basics</li>"
    "</ul>"
    "<p><strong>2 attempts allowed.</strong> Your highest score is kept. "
    "Read each question carefully — feedback is provided for incorrect answers.</p>"
)
QUIZ_TYPE = "assignment"
QUIZ_TIME_LIMIT = 30  # minutes
QUIZ_ALLOWED_ATTEMPTS = 2
QUIZ_SCORING_POLICY = "keep_highest"
QUIZ_SHOW_CORRECT_ANSWERS = True
QUIZ_SHOW_CORRECT_ANSWERS_LAST_ATTEMPT = True  # show after final attempt
QUIZ_ONE_QUESTION_AT_A_TIME = False
QUIZ_SHUFFLE_ANSWERS = True
QUIZ_DUE_AT = "2026-02-26T23:59:00Z"
QUIZ_UNLOCK_AT = "2026-02-24T06:00:00Z"
QUIZ_LOCK_AT = "2026-02-27T06:00:00Z"
QUIZ_POINTS_POSSIBLE = 25  # 25 questions x 1 point each

# ──────────────────────────────────────────────────────────────
# QUESTIONS
# ──────────────────────────────────────────────────────────────
# Each question dict:
#   "stem"       : the question text
#   "answers"    : list of {"text", "correct" (bool), "feedback"}
#   "slide"      : source slide number(s) for alignment verification
#   "bloom"      : Bloom's taxonomy level
#   "points"     : point value (default 1)

QUESTIONS = [
    # ── Q1: Ferrous Definition (Slide 3) ──────────────────────
    {
        "stem": "What does the term \"ferrous\" mean when classifying metals?",
        "answers": [
            {"text": "The metal contains iron as a primary element",
             "correct": True,
             "feedback": "Correct! Ferrous comes from the Latin 'ferrum' meaning iron."},
            {"text": "The metal is resistant to corrosion",
             "correct": False,
             "feedback": "Incorrect. Corrosion resistance is not what defines ferrous metals — in fact, most ferrous metals rust easily. Ferrous means the metal contains iron."},
            {"text": "The metal is lightweight and non-magnetic",
             "correct": False,
             "feedback": "Incorrect. Lightweight and non-magnetic describe non-ferrous metals. Ferrous metals contain iron and are typically magnetic."},
            {"text": "The metal was manufactured using a furnace",
             "correct": False,
             "feedback": "Incorrect. The term ferrous refers to iron content, not the manufacturing process. It comes from the Latin word 'ferrum' (iron)."},
        ],
        "slide": 3, "bloom": "Knowledge", "points": 1,
    },

    # ── Q2: Non-Ferrous Examples (Slide 3) ────────────────────
    {
        "stem": "Which of the following is a non-ferrous metal?",
        "answers": [
            {"text": "Aluminum",
             "correct": True,
             "feedback": "Correct! Aluminum contains no iron and is classified as non-ferrous."},
            {"text": "Mild steel",
             "correct": False,
             "feedback": "Incorrect. Mild steel is ferrous — it's an iron-carbon alloy with about 0.18% carbon."},
            {"text": "Cast iron",
             "correct": False,
             "feedback": "Incorrect. Cast iron is ferrous — it contains 2-4% carbon in an iron base."},
            {"text": "Stainless steel",
             "correct": False,
             "feedback": "Incorrect. Stainless steel is ferrous — it still contains iron, even though the chromium prevents rust."},
        ],
        "slide": 3, "bloom": "Knowledge", "points": 1,
    },

    # ── Q3: Magnet Test (Slide 5 — Metal ID Methods) ─────────
    {
        "stem": "You touch a magnet to an unknown metal sample and it sticks firmly. What can you conclude?",
        "answers": [
            {"text": "The metal is ferrous (contains iron)",
             "correct": True,
             "feedback": "Correct! If a magnet sticks, the metal contains iron and is classified as ferrous."},
            {"text": "The metal is stainless steel specifically",
             "correct": False,
             "feedback": "Incorrect. A strong magnetic response rules out most stainless steels (which are weakly magnetic or non-magnetic). It indicates a ferrous metal like mild steel or 4140."},
            {"text": "The metal is aluminum",
             "correct": False,
             "feedback": "Incorrect. Aluminum is non-ferrous and non-magnetic — a magnet will not stick to it."},
            {"text": "The metal is definitely not going to rust",
             "correct": False,
             "feedback": "Incorrect. Most strongly magnetic (ferrous) metals actually rust easily. Magnetism indicates iron content, and iron is prone to oxidation."},
        ],
        "slide": 5, "bloom": "Comprehension", "points": 1,
    },

    # ── Q4: Spark Test (Slide 5 — Metal ID Methods) ──────────
    {
        "stem": "During a spark test on a bench grinder, a metal produces long, white, branching sparks with many forks. Which metal is this most likely?",
        "answers": [
            {"text": "Mild steel",
             "correct": True,
             "feedback": "Correct! Long, white, branching sparks with many forks (carbon bursts) are characteristic of mild steel."},
            {"text": "Stainless steel",
             "correct": False,
             "feedback": "Incorrect. Stainless steel produces short, dark-red sparks with very few forks due to its low carbon content."},
            {"text": "Aluminum",
             "correct": False,
             "feedback": "Incorrect. Aluminum produces no sparks at all on a grinder — it's a non-ferrous metal."},
            {"text": "Cast iron",
             "correct": False,
             "feedback": "Incorrect. Cast iron produces short, red, fine streams — not the long, branching white sparks described."},
        ],
        "slide": 5, "bloom": "Application", "points": 1,
    },

    # ── Q5: Why Metal Selection Matters (Slide 4) ─────────────
    {
        "stem": "Why is it important to identify the type of metal before starting a welding project?",
        "answers": [
            {"text": "Different metals require different welding wire, gas, and machine settings",
             "correct": True,
             "feedback": "Correct! Using the wrong wire or gas for a metal type results in contaminated welds, no fusion, and scrapped parts."},
            {"text": "All metals weld the same way once they are hot enough",
             "correct": False,
             "feedback": "Incorrect. Metals have very different welding requirements. For example, steel uses ER70S-6 wire with C25 gas, while aluminum needs ER4043 wire with 100% argon."},
            {"text": "Metal identification is only important for machining, not welding",
             "correct": False,
             "feedback": "Incorrect. Metal identification is critical for welding — using steel wire on aluminum creates a contaminated weld with no fusion."},
            {"text": "The color of the metal determines which welding helmet to use",
             "correct": False,
             "feedback": "Incorrect. Welding helmet shade is based on the welding process and amperage, not the metal color. The metal type determines wire, gas, and settings."},
        ],
        "slide": 4, "bloom": "Comprehension", "points": 1,
    },

    # ── Q6: Mild Steel Properties (Slide 6) ───────────────────
    {
        "stem": "Which property makes mild steel (1018/A36) the most common metal for beginner shop projects?",
        "answers": [
            {"text": "It has excellent machinability and weldability at low cost",
             "correct": True,
             "feedback": "Correct! Mild steel is cheap (~$1/lb), easy to weld, and machines beautifully — making it ideal for learning."},
            {"text": "It never rusts, so students don't need to apply finish",
             "correct": False,
             "feedback": "Incorrect. Mild steel rusts very easily! Students must oil or prime it. Its popularity comes from low cost and ease of working."},
            {"text": "It is the lightest structural metal available",
             "correct": False,
             "feedback": "Incorrect. Mild steel is heavy (7.87 g/cm³). Aluminum is about 1/3 the weight. Mild steel is popular because it's cheap and forgiving to work with."},
            {"text": "It can be heat treated to extreme hardness",
             "correct": False,
             "feedback": "Incorrect. Mild steel (0.18% carbon) cannot be meaningfully heat treated. For heat treatability, you'd use 4140 chrome-moly steel."},
        ],
        "slide": 6, "bloom": "Comprehension", "points": 1,
    },

    # ── Q7: Mild Steel Corrosion (Slide 6) ────────────────────
    {
        "stem": "A student leaves a bare mild steel project on the workbench over the weekend without applying any finish. What will most likely happen?",
        "answers": [
            {"text": "The surface will develop rust (iron oxide)",
             "correct": True,
             "feedback": "Correct! Mild steel rusts quickly when exposed to air and moisture. Always oil or prime bare steel."},
            {"text": "The surface will develop a protective green patina",
             "correct": False,
             "feedback": "Incorrect. Green patina (verdigris) forms on copper, not steel. Mild steel develops orange-brown iron oxide (rust)."},
            {"text": "Nothing — mild steel is naturally corrosion resistant",
             "correct": False,
             "feedback": "Incorrect. Mild steel is one of the most rust-prone metals in the shop. It needs oil, primer, or paint to prevent corrosion."},
            {"text": "The mill scale will protect it from corrosion indefinitely",
             "correct": False,
             "feedback": "Incorrect. Mill scale offers minimal protection and breaks down over time. Any scratched or ground area will rust quickly."},
        ],
        "slide": 6, "bloom": "Application", "points": 1,
    },

    # ── Q8: 4140 Chrome-Moly (Slide 7) ───────────────────────
    {
        "stem": "What is the key advantage of 4140 chrome-moly steel over mild steel?",
        "answers": [
            {"text": "It can be heat treated (hardened and tempered) for greater strength",
             "correct": True,
             "feedback": "Correct! 4140 has 0.40% carbon plus chromium and molybdenum, making it heat treatable to Rockwell 55+."},
            {"text": "It is less expensive than mild steel",
             "correct": False,
             "feedback": "Incorrect. 4140 costs more than mild steel due to its alloy content (chromium + molybdenum)."},
            {"text": "It does not require any welding preheat",
             "correct": False,
             "feedback": "Incorrect. 4140 actually requires preheat to ~400°F before welding to prevent cracking — a disadvantage compared to mild steel."},
            {"text": "It is completely rust-proof",
             "correct": False,
             "feedback": "Incorrect. 4140 still rusts (it's ferrous with only small amounts of chromium). For rust resistance, you'd choose stainless steel."},
        ],
        "slide": 7, "bloom": "Comprehension", "points": 1,
    },

    # ── Q9: Tool Steel (Slide 8) ──────────────────────────────
    {
        "stem": "Why would a machinist choose tool steel (A2 or D2) for making a stamping die?",
        "answers": [
            {"text": "Tool steel can be hardened to Rockwell 58-62 HRC, resisting deformation under repeated impact",
             "correct": True,
             "feedback": "Correct! Tool steel's extreme hardness after heat treatment makes it ideal for dies, punches, and cutting tools that must hold their shape."},
            {"text": "Tool steel is the easiest metal to weld",
             "correct": False,
             "feedback": "Incorrect. Tool steel is very difficult to weld and has a high risk of cracking. Its value is in hardness, not weldability."},
            {"text": "Tool steel is the cheapest option for any shop project",
             "correct": False,
             "feedback": "Incorrect. Tool steel is expensive ($$$). It's chosen specifically when extreme hardness and wear resistance are required, not for cost savings."},
            {"text": "Tool steel is the lightest ferrous metal",
             "correct": False,
             "feedback": "Incorrect. Tool steel has similar density to other steels (~7.86 g/cm³). It's chosen for its hardness, not weight savings."},
        ],
        "slide": 8, "bloom": "Application", "points": 1,
    },

    # ── Q10: Cast Iron (Slide 9) ──────────────────────────────
    {
        "stem": "What is the most important safety consideration when welding cast iron?",
        "answers": [
            {"text": "It requires preheat to 500°F+ and special nickel rods, or the weld will crack",
             "correct": True,
             "feedback": "Correct! Cast iron is brittle and thermally sensitive. Cold welding causes cracking. Always consult the instructor before attempting."},
            {"text": "Cast iron cannot be welded under any circumstances",
             "correct": False,
             "feedback": "Incorrect. Cast iron CAN be welded, but it requires specific preparation: preheating to 500°F+ and using nickel-based filler rods with slow cooling."},
            {"text": "Cast iron melts at a lower temperature than aluminum",
             "correct": False,
             "feedback": "Incorrect. Cast iron melts at approximately 2,100°F, significantly higher than aluminum (1,220°F). The concern is cracking from thermal shock, not low melting point."},
            {"text": "Cast iron produces toxic fumes that require special ventilation",
             "correct": False,
             "feedback": "Incorrect. While all welding requires ventilation, cast iron's primary risk is cracking from thermal stress, not unique fume hazards."},
        ],
        "slide": 9, "bloom": "Knowledge", "points": 1,
    },

    # ── Q11: Cast Iron Identification (Slide 9) ──────────────
    {
        "stem": "How do the machining chips from grey cast iron differ from those produced by mild steel?",
        "answers": [
            {"text": "Cast iron chips are powdery/dusty, while mild steel produces curled ribbon chips",
             "correct": True,
             "feedback": "Correct! The graphite flakes in grey cast iron cause chips to break into powder rather than forming continuous curls like steel."},
            {"text": "Cast iron chips are long and stringy like aluminum",
             "correct": False,
             "feedback": "Incorrect. Grey cast iron chips are powdery due to graphite flakes in the microstructure. Aluminum can produce long, gummy chips."},
            {"text": "Cast iron cannot be machined at all",
             "correct": False,
             "feedback": "Incorrect. Grey cast iron actually has excellent machinability! It machines easily and cleanly, producing powdery chips."},
            {"text": "There is no visible difference between cast iron and steel chips",
             "correct": False,
             "feedback": "Incorrect. The difference is dramatic — steel makes curled ribbons while cast iron makes dark powder/dust."},
        ],
        "slide": 9, "bloom": "Knowledge", "points": 1,
    },

    # ── Q12: 6061 Aluminum Weight (Slide 10) ──────────────────
    {
        "stem": "Approximately how does the weight of 6061 aluminum compare to mild steel for the same size piece?",
        "answers": [
            {"text": "Aluminum is about 1/3 the weight of steel",
             "correct": True,
             "feedback": "Correct! 6061 aluminum has a density of 2.70 g/cm³ compared to steel's 7.87 g/cm³ — roughly one-third."},
            {"text": "Aluminum is about the same weight as steel",
             "correct": False,
             "feedback": "Incorrect. Aluminum is dramatically lighter — about 1/3 the weight of steel. You can feel the difference instantly by picking up same-size pieces."},
            {"text": "Aluminum is heavier than steel",
             "correct": False,
             "feedback": "Incorrect. Aluminum (2.70 g/cm³) is much lighter than steel (7.87 g/cm³). Copper and brass are heavier than steel."},
            {"text": "Aluminum is about half the weight of steel",
             "correct": False,
             "feedback": "Close, but not quite. Aluminum is about 1/3 the weight of steel (2.70 vs. 7.87 g/cm³), not 1/2."},
        ],
        "slide": 10, "bloom": "Knowledge", "points": 1,
    },

    # ── Q13: Aluminum Welding (Slide 10) ──────────────────────
    {
        "stem": "What shielding gas is required when MIG welding aluminum?",
        "answers": [
            {"text": "100% Argon",
             "correct": True,
             "feedback": "Correct! Aluminum MIG welding requires 100% argon shielding gas and ER4043 aluminum wire."},
            {"text": "C25 (75% Argon / 25% CO2)",
             "correct": False,
             "feedback": "Incorrect. C25 is the gas mix for MIG welding steel. CO2 reacts with molten aluminum and contaminates the weld. Aluminum needs 100% argon."},
            {"text": "100% CO2",
             "correct": False,
             "feedback": "Incorrect. CO2 reacts aggressively with molten aluminum. Aluminum requires 100% argon for proper shielding."},
            {"text": "No shielding gas is needed for aluminum",
             "correct": False,
             "feedback": "Incorrect. Aluminum is extremely reactive with oxygen when molten. Without argon shielding, the weld pool oxidizes immediately and fails."},
        ],
        "slide": 10, "bloom": "Knowledge", "points": 1,
    },

    # ── Q14: Copper Properties (Slide 11) ─────────────────────
    {
        "stem": "Which unique property makes copper the standard material for electrical wiring?",
        "answers": [
            {"text": "It has the best electrical conductivity of any common metal",
             "correct": True,
             "feedback": "Correct! Copper is the #1 electrical conductor among common metals (only silver is better, but far too expensive for wiring)."},
            {"text": "It is the lightest non-ferrous metal",
             "correct": False,
             "feedback": "Incorrect. Copper is actually heavier than steel (8.96 g/cm³). Aluminum is the lightest common structural metal. Copper is used for its conductivity."},
            {"text": "It is the hardest non-ferrous metal",
             "correct": False,
             "feedback": "Incorrect. Copper is actually very soft (Brinell ~50). Titanium is much harder. Copper is chosen for wiring because of its electrical conductivity."},
            {"text": "It is the cheapest metal available",
             "correct": False,
             "feedback": "Incorrect. Copper costs ~$4-5/lb, much more than mild steel (~$1/lb). It's used for wiring because no other affordable metal conducts electricity as well."},
        ],
        "slide": 11, "bloom": "Comprehension", "points": 1,
    },

    # ── Q15: Brass Machinability (Slide 12) ───────────────────
    {
        "stem": "Why is 360 brass considered the best metal for lathe projects that require a premium surface finish?",
        "answers": [
            {"text": "It has outstanding machinability — chips break cleanly and the surface finishes beautifully",
             "correct": True,
             "feedback": "Correct! 360 (free-machining) brass contains a small amount of lead that causes chips to break short and clean, leaving an excellent surface."},
            {"text": "Brass is the hardest metal so it holds tight tolerances",
             "correct": False,
             "feedback": "Incorrect. Brass is actually low-medium hardness (Brinell ~120). Its machining advantage comes from excellent chip-breaking, not hardness."},
            {"text": "Brass is magnetic which helps hold it in the chuck",
             "correct": False,
             "feedback": "Incorrect. Brass is non-ferrous and non-magnetic. It machines well because of its metallurgical properties, not magnetic properties."},
            {"text": "Brass is less expensive than mild steel",
             "correct": False,
             "feedback": "Incorrect. Brass ($$) is more expensive than mild steel ($). Its premium is justified by the exceptional surface finish and appearance."},
        ],
        "slide": 12, "bloom": "Comprehension", "points": 1,
    },

    # ── Q16: Brass Safety Property (Slide 12) ─────────────────
    {
        "stem": "Why are tools designed for use near explosives or flammable materials often made from brass?",
        "answers": [
            {"text": "Brass is non-sparking, so it won't ignite flammable vapors on impact",
             "correct": True,
             "feedback": "Correct! Brass doesn't produce sparks when struck, making it the standard material for tools used in explosive environments."},
            {"text": "Brass is the strongest metal available for tools",
             "correct": False,
             "feedback": "Incorrect. Brass is softer than steel. It's chosen for explosive environments specifically because it's non-sparking, not because of strength."},
            {"text": "Brass is cheaper than steel for tool manufacturing",
             "correct": False,
             "feedback": "Incorrect. Brass costs more than steel. The non-sparking safety property is what justifies the extra cost in hazardous environments."},
            {"text": "Brass tools are lighter and easier to carry",
             "correct": False,
             "feedback": "Incorrect. Brass (8.50 g/cm³) is actually heavier than steel (7.87 g/cm³). The critical property is that brass is non-sparking."},
        ],
        "slide": 12, "bloom": "Comprehension", "points": 1,
    },

    # ── Q17: Titanium (Slide 13) ──────────────────────────────
    {
        "stem": "What makes titanium valuable for aerospace and medical implant applications?",
        "answers": [
            {"text": "It has the best strength-to-weight ratio of any common metal and is biocompatible",
             "correct": True,
             "feedback": "Correct! Titanium is as strong as steel at 60% the weight, and the body doesn't reject it — making it ideal for both aircraft and implants."},
            {"text": "It is the cheapest structural metal per pound",
             "correct": False,
             "feedback": "Incorrect. Titanium is extremely expensive (~$15-25/lb). It's used in aerospace and medical despite the cost because of its unique strength-to-weight ratio and biocompatibility."},
            {"text": "It is easy to machine and weld with standard equipment",
             "correct": False,
             "feedback": "Incorrect. Titanium is very difficult to machine (extreme heat) and requires argon shielding on BOTH sides when welding. Its value is in performance, not ease of use."},
            {"text": "It is strongly magnetic which aids in manufacturing",
             "correct": False,
             "feedback": "Incorrect. Titanium is non-ferrous and non-magnetic. Its aerospace value comes from strength-to-weight ratio, corrosion resistance, and heat resistance."},
        ],
        "slide": 13, "bloom": "Comprehension", "points": 1,
    },

    # ── Q18: Stainless Steel Classification (Slide 14) ───────
    {
        "stem": "A student claims stainless steel is non-ferrous because it doesn't rust. Is this correct?",
        "answers": [
            {"text": "No — stainless steel is ferrous because it contains iron; the chromium prevents rust, not the absence of iron",
             "correct": True,
             "feedback": "Correct! Stainless steel contains iron (making it ferrous). The 10.5%+ chromium forms a protective oxide layer that prevents rust."},
            {"text": "Yes — any metal that doesn't rust is non-ferrous",
             "correct": False,
             "feedback": "Incorrect. Ferrous/non-ferrous is about iron content, not rust behavior. Stainless steel contains iron (ferrous) but resists rust because of chromium."},
            {"text": "Yes — the magnet test confirms stainless is non-ferrous",
             "correct": False,
             "feedback": "Incorrect. The magnet test is unreliable for stainless — some grades are weakly magnetic. Stainless IS ferrous (contains iron); its chromium just prevents rust."},
            {"text": "No — but only because stainless is actually an aluminum alloy",
             "correct": False,
             "feedback": "Incorrect. Stainless steel is an iron alloy with chromium and nickel — not aluminum. It's ferrous because iron is its primary element."},
        ],
        "slide": 14, "bloom": "Comprehension", "points": 1,
    },

    # ── Q19: Stainless Cross-Contamination (Slide 14) ────────
    {
        "stem": "Why must you never use a grinding wheel on stainless steel that was previously used on mild steel?",
        "answers": [
            {"text": "Carbon steel particles embed in the stainless surface and cause rust spots (cross-contamination)",
             "correct": True,
             "feedback": "Correct! Carbon steel particles from the wheel embed in the stainless, creating rust spots that defeat the purpose of using stainless steel."},
            {"text": "The stainless steel will melt because it has a lower melting point",
             "correct": False,
             "feedback": "Incorrect. Stainless steel has a similar melting point to mild steel. The issue is cross-contamination — carbon steel particles cause rust."},
            {"text": "The grinding wheel will shatter on the harder stainless",
             "correct": False,
             "feedback": "Incorrect. While stainless is harder, a proper grinding wheel handles it fine. The concern is carbon steel particles embedding in the stainless and causing rust."},
            {"text": "Mixing metals creates toxic fumes",
             "correct": False,
             "feedback": "Incorrect. While welding fumes always need ventilation, grinding cross-contamination is about corrosion, not fumes. Steel particles in stainless create rust spots."},
        ],
        "slide": 14, "bloom": "Comprehension", "points": 1,
    },

    # ── Q20: MIG Welding Basics (Slide 15) ────────────────────
    {
        "stem": "What is the correct wire and gas combination for MIG welding mild steel?",
        "answers": [
            {"text": "ER70S-6 wire with C25 gas (75% Argon / 25% CO2)",
             "correct": True,
             "feedback": "Correct! ER70S-6 is the standard mild steel MIG wire, and C25 is the standard shielding gas mix for steel."},
            {"text": "ER4043 wire with 100% Argon",
             "correct": False,
             "feedback": "Incorrect. ER4043 with 100% argon is the setup for MIG welding aluminum. Mild steel uses ER70S-6 wire with C25 gas."},
            {"text": "ER70S-6 wire with 100% CO2",
             "correct": False,
             "feedback": "Partially right wire, wrong gas. While 100% CO2 can work, C25 (75% Argon / 25% CO2) is the standard shop mix that produces a cleaner, more stable arc."},
            {"text": "Any wire works as long as the gas is correct",
             "correct": False,
             "feedback": "Incorrect. Wire and gas must BOTH match the base metal. Steel wire on aluminum = contaminated weld. Aluminum wire on steel = no fusion."},
        ],
        "slide": 15, "bloom": "Knowledge", "points": 1,
    },

    # ── Q21: MIG Travel Speed (Slide 15) ─────────────────────
    {
        "stem": "A student's MIG weld bead looks cold, narrow, and ropy with poor penetration. What is the most likely cause?",
        "answers": [
            {"text": "The student is moving the gun too fast along the joint",
             "correct": True,
             "feedback": "Correct! Moving too fast doesn't allow enough heat to build up, resulting in a cold, narrow bead with poor penetration into the base metal."},
            {"text": "The student is using too much shielding gas",
             "correct": False,
             "feedback": "Incorrect. Excess shielding gas can cause turbulence but typically doesn't produce a cold, ropy bead. That symptom points to excessive travel speed."},
            {"text": "The student is moving the gun too slowly",
             "correct": False,
             "feedback": "Incorrect. Moving too slowly causes the opposite problem — excessive heat, a wide bead, and burn-through. A cold, ropy bead means too fast."},
            {"text": "The welding helmet shade is too dark",
             "correct": False,
             "feedback": "Incorrect. Helmet shade affects visibility but doesn't change the weld bead characteristics. A cold, ropy bead indicates the gun is moving too fast."},
        ],
        "slide": 15, "bloom": "Application", "points": 1,
    },

    # ── Q22: Lathe Safety (Slide 16) ──────────────────────────
    {
        "stem": "What is the #1 safety rule when operating a metal lathe?",
        "answers": [
            {"text": "Never leave the chuck key in the chuck",
             "correct": True,
             "feedback": "Correct! If the lathe starts with the chuck key inserted, it becomes a high-speed projectile. Remove the key immediately after tightening."},
            {"text": "Always wear gloves when operating the lathe",
             "correct": False,
             "feedback": "Incorrect — and dangerous! Gloves should NEVER be worn near a spinning lathe. They can catch and pull your hand into the workpiece."},
            {"text": "Run the lathe at maximum speed for all materials",
             "correct": False,
             "feedback": "Incorrect. RPM must be adjusted for the material — stainless requires only 200-400 RPM while aluminum can handle 800-1500 RPM. Wrong speed can damage the tool and workpiece."},
            {"text": "Stand directly in front of the chuck when starting",
             "correct": False,
             "feedback": "Incorrect — and dangerous! Always stand to the SIDE of the chuck, not in front. If a workpiece comes loose, it's ejected toward the front."},
        ],
        "slide": 16, "bloom": "Knowledge", "points": 1,
    },

    # ── Q23: Lathe RPM Application (Slide 16) ────────────────
    {
        "stem": "A student needs to turn a piece of stainless steel on the lathe. What RPM range should they use?",
        "answers": [
            {"text": "200-400 RPM (slow)",
             "correct": True,
             "feedback": "Correct! Stainless steel work-hardens, so it needs low RPM with aggressive feed to cut properly. Going too fast causes the surface to harden."},
            {"text": "800-1500 RPM (fast)",
             "correct": False,
             "feedback": "Incorrect. 800-1500 RPM is the range for aluminum. Running stainless that fast would cause extreme work-hardening, destroying both the tool and workpiece."},
            {"text": "300-600 RPM (moderate)",
             "correct": False,
             "feedback": "Close, but too fast for stainless. 300-600 RPM is the range for mild steel. Stainless needs 200-400 RPM because it work-hardens."},
            {"text": "RPM doesn't matter as long as you use cutting fluid",
             "correct": False,
             "feedback": "Incorrect. Cutting fluid helps, but RPM is critical for stainless. Too-high RPM causes work-hardening where the surface gets progressively harder with each pass."},
        ],
        "slide": 16, "bloom": "Application", "points": 1,
    },

    # ── Q24: Milling Safety (Slide 17) ────────────────────────
    {
        "stem": "Why is secure workholding (tight vise) critical when milling?",
        "answers": [
            {"text": "A loose workpiece can catch the cutter and become a projectile or shatter the end mill",
             "correct": True,
             "feedback": "Correct! A spinning end mill can grab a loose workpiece instantly. The workpiece becomes a projectile, and the end mill can shatter, sending fragments flying."},
            {"text": "A loose workpiece will produce a better surface finish",
             "correct": False,
             "feedback": "Incorrect — a loose workpiece produces a terrible finish (if you're lucky) or a dangerous situation (if it catches). Secure clamping is a safety requirement."},
            {"text": "The vise needs to be tight only for stainless, not for aluminum",
             "correct": False,
             "feedback": "Incorrect. The vise must be tight for ALL materials. Any loose workpiece is dangerous regardless of the metal being machined."},
            {"text": "Tight clamping is optional if you use climb milling",
             "correct": False,
             "feedback": "Incorrect. Climb milling actually increases the pulling force on the workpiece, making secure clamping even MORE critical."},
        ],
        "slide": 17, "bloom": "Comprehension", "points": 1,
    },

    # ── Q25: Application Scenario (Slides 18-20) ─────────────
    {
        "stem": "You need to build a budget go-kart frame that is easy to weld, strong enough for the load, and as inexpensive as possible. Which metal should you choose?",
        "answers": [
            {"text": "Mild steel — cheap, excellent weldability, strong enough for the application",
             "correct": True,
             "feedback": "Correct! Mild steel at ~$1/lb with excellent weldability is the clear choice for a budget frame. It's the 'pine' of metals — affordable and forgiving."},
            {"text": "Titanium — strongest metal available for frames",
             "correct": False,
             "feedback": "Incorrect. Titanium has great strength-to-weight, but at ~$15-25/lb it violates the 'budget' requirement. A titanium go-kart frame would cost 15-25x more."},
            {"text": "Stainless steel — it won't rust outdoors",
             "correct": False,
             "feedback": "Incorrect. Stainless costs 3-4x mild steel and is harder to weld. For a budget go-kart, mild steel with paint or powder coat is the right choice."},
            {"text": "6061 aluminum — lighter means faster",
             "correct": False,
             "feedback": "Incorrect. While aluminum is lighter, it's harder to weld (requires TIG or special MIG setup), more expensive, and a budget go-kart doesn't need weight savings."},
        ],
        "slide": "18-20", "bloom": "Application", "points": 1,
    },
]


# ──────────────────────────────────────────────────────────────
# REVIEW MODE — print quiz for human vetting
# ──────────────────────────────────────────────────────────────
def review_quiz():
    """Print the full quiz for review before deployment."""
    print("=" * 72)
    print(f"  QUIZ REVIEW: {QUIZ_TITLE}")
    print(f"  Questions: {len(QUESTIONS)}  |  Points: {sum(q['points'] for q in QUESTIONS)}")
    print(f"  Time Limit: {QUIZ_TIME_LIMIT} min  |  Attempts: {QUIZ_ALLOWED_ATTEMPTS}")
    print(f"  Due: {QUIZ_DUE_AT}  |  Scoring: {QUIZ_SCORING_POLICY}")
    print("=" * 72)

    bloom_counts = {}
    for i, q in enumerate(QUESTIONS, 1):
        bloom = q["bloom"]
        bloom_counts[bloom] = bloom_counts.get(bloom, 0) + 1

        print(f"\n{'─' * 72}")
        print(f"  Q{i} [{bloom}] (Slide {q['slide']})  —  {q['points']} pt")
        print(f"{'─' * 72}")
        print(f"  {q['stem']}")
        for j, a in enumerate(q["answers"]):
            marker = "✓" if a["correct"] else " "
            letter = chr(65 + j)
            print(f"    [{marker}] {letter}. {a['text']}")
            print(f"        → {a['feedback']}")

    print(f"\n{'=' * 72}")
    print("  BLOOM'S TAXONOMY DISTRIBUTION")
    print(f"{'=' * 72}")
    for level, count in sorted(bloom_counts.items()):
        bar = "█" * count
        print(f"  {level:15s}  {count:2d}  {bar}")

    print(f"\n  SLIDE ALIGNMENT CHECK")
    print(f"{'─' * 72}")
    slide_map = {}
    for i, q in enumerate(QUESTIONS, 1):
        s = str(q["slide"])
        slide_map.setdefault(s, []).append(i)
    for s in sorted(slide_map.keys(), key=lambda x: int(x.split("-")[0])):
        qs = ", ".join(f"Q{q}" for q in slide_map[s])
        print(f"  Slide {s:>5s}:  {qs}")

    print(f"\n  DISTRACTOR ANALYSIS")
    print(f"{'─' * 72}")
    correct_positions = [0, 0, 0, 0]
    for q in QUESTIONS:
        for j, a in enumerate(q["answers"]):
            if a["correct"]:
                correct_positions[j] += 1
    for j in range(4):
        letter = chr(65 + j)
        print(f"  Correct answer in position {letter}: {correct_positions[j]}/{len(QUESTIONS)}")
    print(f"  (Note: answers will be shuffled in Canvas)")

    print(f"\n{'=' * 72}")
    print(f"  TOTAL: {len(QUESTIONS)} questions, {sum(q['points'] for q in QUESTIONS)} points")
    print(f"  Quiz appears well-formed. Review above, then deploy with:")
    print(f"  python3 quiz_metal_types.py --deploy --course-id <COURSE_ID>")
    print(f"{'=' * 72}")


# ──────────────────────────────────────────────────────────────
# CANVAS DEPLOYMENT
# ──────────────────────────────────────────────────────────────
def list_courses():
    """List available Canvas courses."""
    from canvasapi import Canvas
    url = os.environ.get("CANVAS_API_URL")
    token = os.environ.get("CANVAS_API_TOKEN")
    if not url or not token:
        print("ERROR: Set CANVAS_API_URL and CANVAS_API_TOKEN environment variables.")
        print("  export CANVAS_API_URL=https://yourschool.instructure.com")
        print("  export CANVAS_API_TOKEN=your_token_here")
        sys.exit(1)

    canvas = Canvas(url, token)
    print(f"\nYour Canvas Courses (active):")
    print(f"{'─' * 60}")
    for course in canvas.get_courses(enrollment_state="active"):
        name = getattr(course, "name", "Unnamed")
        cid = course.id
        print(f"  ID: {cid:>8d}  |  {name}")
    print(f"\nUse the ID for your metals class with --course-id")


def deploy_quiz(course_id):
    """Deploy the quiz to Canvas."""
    from canvasapi import Canvas
    url = os.environ.get("CANVAS_API_URL")
    token = os.environ.get("CANVAS_API_TOKEN")
    if not url or not token:
        print("ERROR: Set CANVAS_API_URL and CANVAS_API_TOKEN environment variables.")
        sys.exit(1)

    canvas = Canvas(url, token)
    course = canvas.get_course(course_id)
    print(f"Connected to course: {course.name} (ID: {course.id})")

    # Create the quiz
    quiz_params = {
        "title": QUIZ_TITLE,
        "description": QUIZ_DESCRIPTION,
        "quiz_type": QUIZ_TYPE,
        "time_limit": QUIZ_TIME_LIMIT,
        "allowed_attempts": QUIZ_ALLOWED_ATTEMPTS,
        "scoring_policy": QUIZ_SCORING_POLICY,
        "show_correct_answers": QUIZ_SHOW_CORRECT_ANSWERS,
        "show_correct_answers_last_attempt": QUIZ_SHOW_CORRECT_ANSWERS_LAST_ATTEMPT,
        "one_question_at_a_time": QUIZ_ONE_QUESTION_AT_A_TIME,
        "shuffle_answers": QUIZ_SHUFFLE_ANSWERS,
        "due_at": QUIZ_DUE_AT,
        "unlock_at": QUIZ_UNLOCK_AT,
        "lock_at": QUIZ_LOCK_AT,
    }
    print(f"Creating quiz: {QUIZ_TITLE}...")
    quiz = course.create_quiz(quiz=quiz_params)
    print(f"  Quiz created (ID: {quiz.id})")

    # Add questions
    for i, q in enumerate(QUESTIONS, 1):
        answers = []
        for a in q["answers"]:
            answer = {
                "answer_text": a["text"],
                "answer_weight": 100 if a["correct"] else 0,
                "answer_comment": a["feedback"],
            }
            answers.append(answer)

        question_params = {
            "question_name": f"Q{i}",
            "question_text": f"<p>{q['stem']}</p>",
            "question_type": "multiple_choice_question",
            "points_possible": q["points"],
            "answers": answers,
        }
        quiz.create_question(question=question_params)
        print(f"  Added Q{i}: {q['stem'][:60]}...")

    print(f"\n{'=' * 60}")
    print(f"  Quiz deployed successfully!")
    print(f"  Title:    {QUIZ_TITLE}")
    print(f"  Questions: {len(QUESTIONS)}")
    print(f"  Points:   {sum(q['points'] for q in QUESTIONS)}")
    print(f"  Due:      {QUIZ_DUE_AT}")
    print(f"  Attempts: {QUIZ_ALLOWED_ATTEMPTS}")
    print(f"  Status:   UNPUBLISHED (publish in Canvas when ready)")
    print(f"{'=' * 60}")
    print(f"\n  IMPORTANT: The quiz is created as UNPUBLISHED.")
    print(f"  Go to Canvas → {course.name} → Quizzes → {QUIZ_TITLE}")
    print(f"  Review it, then click 'Publish' when satisfied.")


# ──────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Metal Types Quiz — Canvas Deployment")
    parser.add_argument("--review", action="store_true",
                        help="Print quiz for review (no Canvas connection needed)")
    parser.add_argument("--list-courses", action="store_true",
                        help="List your Canvas courses to find the right course ID")
    parser.add_argument("--deploy", action="store_true",
                        help="Deploy quiz to Canvas")
    parser.add_argument("--course-id", type=int,
                        help="Canvas course ID for deployment")
    args = parser.parse_args()

    if args.review:
        review_quiz()
    elif args.list_courses:
        list_courses()
    elif args.deploy:
        if not args.course_id:
            print("ERROR: --deploy requires --course-id <ID>")
            print("  Run --list-courses first to find your course ID.")
            sys.exit(1)
        deploy_quiz(args.course_id)
    else:
        parser.print_help()
