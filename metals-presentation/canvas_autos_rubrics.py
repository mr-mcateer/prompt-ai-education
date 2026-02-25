#!/usr/bin/env python3
"""
Create self-assessed rubrics for "What Nobody Teaches You About Owning a Car"
portfolio series + teacher-graded rubrics for Engines Fab lab assignments.

Target courses:
  23124 — P1 Engines Fab 1
  23344 — P1 Engines Fab 2

Usage:
  python3 canvas_autos_rubrics.py --dry-run     # Preview — no changes
  python3 canvas_autos_rubrics.py --deploy       # Create all rubrics
  python3 canvas_autos_rubrics.py --audit        # Verify rubrics after deploy
"""

import os
import sys
import json
import requests
import argparse

ENGINES_FAB_COURSE_IDS = [23124, 23344]


def get_creds():
    url = os.environ.get("CANVAS_API_URL")
    token = os.environ.get("CANVAS_API_TOKEN")
    if not url or not token:
        print("ERROR: Set CANVAS_API_URL and CANVAS_API_TOKEN")
        sys.exit(1)
    return url, token


def paginated_get(url, headers, params=None):
    """GET with Canvas pagination support."""
    results = []
    page_url = url
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
# RUBRIC DEFINITIONS — 16 self-assessed + 3 teacher-graded
# ══════════════════════════════════════════════════════════════
#
# Canvas rubric format:
#   criteria: { "0": { description, points, ratings: { "0": {description, points}, ... } }, ... }
#   Rating "0" = highest (full credit), "3" = lowest (0 pts)
#
# Self-assessed rubrics use "I did..." language with countable deliverables.
# Every self-assessed rubric includes an Evidence criterion.

RUBRICS = {
    # ── 01 ─────────────────────────────────────────────
    "01 — Your First Car Is Probably a Bad Deal": {
        "title": "01 — Vehicle Selection Self-Assessment",
        "criteria": {
            "0": {
                "description": "Vehicle Candidates",
                "points": 6,
                "ratings": {
                    "0": {"description": "I found 3 vehicles with year, make, model, trim, mileage, and average market price for each", "points": 6},
                    "1": {"description": "I found 2 vehicles with most details", "points": 4},
                    "2": {"description": "I found 1 vehicle or major details are missing", "points": 2},
                    "3": {"description": "No vehicles researched or not submitted", "points": 0},
                },
            },
            "1": {
                "description": "Comparison Data",
                "points": 6,
                "ratings": {
                    "0": {"description": "I compared all 3 vehicles on price, fuel economy, estimated insurance, and reliability ratings", "points": 6},
                    "1": {"description": "I compared on 2-3 of the 4 categories", "points": 4},
                    "2": {"description": "I compared on 1 category only", "points": 2},
                    "3": {"description": "No comparison data provided", "points": 0},
                },
            },
            "2": {
                "description": "Selection Rationale",
                "points": 4,
                "ratings": {
                    "0": {"description": "I wrote a clear paragraph explaining why I chose my portfolio vehicle with specific reasoning tied to my comparison data", "points": 4},
                    "1": {"description": "I wrote a rationale but it is vague or not connected to my comparison data", "points": 3},
                    "2": {"description": "I stated my choice but did not explain why", "points": 2},
                    "3": {"description": "No rationale provided", "points": 0},
                },
            },
            "3": {
                "description": "Evidence",
                "points": 4,
                "ratings": {
                    "0": {"description": "I included links or screenshots from KBB, Edmunds, or other listing sites for all 3 vehicles", "points": 4},
                    "1": {"description": "I included evidence for 1-2 vehicles", "points": 3},
                    "2": {"description": "I named my sources but provided no links or screenshots", "points": 2},
                    "3": {"description": "No evidence of research", "points": 0},
                },
            },
        },
    },

    # ── 02 ─────────────────────────────────────────────
    "02 \u2014 Everything on the Sticker They Hope You Won\u2019t Read": {
        "title": "02 — Sticker & VIN Decode Self-Assessment",
        "criteria": {
            "0": {
                "description": "Sticker Data",
                "points": 6,
                "ratings": {
                    "0": {"description": "I recorded base price, factory options vs. dealer-installed options with costs, destination charge, and total MSRP", "points": 6},
                    "1": {"description": "I recorded 3 of the 4 data points (base price, options, destination, MSRP)", "points": 4},
                    "2": {"description": "I recorded 1-2 data points", "points": 2},
                    "3": {"description": "No sticker data recorded", "points": 0},
                },
            },
            "1": {
                "description": "VIN Decode",
                "points": 6,
                "ratings": {
                    "0": {"description": "I decoded all 17 VIN characters and identified country of origin, manufacturer, vehicle type, engine, model year, assembly plant, and serial sequence", "points": 6},
                    "1": {"description": "I decoded the VIN but missed 2-3 of the key fields (origin, manufacturer, engine, year, plant)", "points": 4},
                    "2": {"description": "I decoded only 1-2 VIN fields", "points": 2},
                    "3": {"description": "No VIN decode completed", "points": 0},
                },
            },
            "2": {
                "description": "Options Analysis",
                "points": 4,
                "ratings": {
                    "0": {"description": "I listed which options are essential vs. unnecessary and explained which I would actually pay for with reasoning", "points": 4},
                    "1": {"description": "I listed essential vs. unnecessary but did not explain my reasoning", "points": 3},
                    "2": {"description": "I made a partial list without categorization", "points": 2},
                    "3": {"description": "No options analysis", "points": 0},
                },
            },
            "3": {
                "description": "Evidence",
                "points": 4,
                "ratings": {
                    "0": {"description": "I included a screenshot or link to the window sticker or build sheet I used", "points": 4},
                    "1": {"description": "I included partial evidence (screenshot is incomplete or hard to read)", "points": 3},
                    "2": {"description": "I named my source but provided no screenshot or link", "points": 2},
                    "3": {"description": "No evidence provided", "points": 0},
                },
            },
        },
    },

    # ── 03 ─────────────────────────────────────────────
    "03 — The Most Expensive Room in the Dealership": {
        "title": "03 — Financing Comparison Self-Assessment",
        "criteria": {
            "0": {
                "description": "Loan Calculations",
                "points": 8,
                "ratings": {
                    "0": {"description": "I calculated monthly payment, total interest, and total cost for all 3 terms (48, 60, and 72 months) at 5.5% APR", "points": 8},
                    "1": {"description": "I completed calculations for 2 of the 3 terms correctly", "points": 6},
                    "2": {"description": "I completed calculations for 1 term only", "points": 3},
                    "3": {"description": "No loan calculations completed", "points": 0},
                },
            },
            "1": {
                "description": "Down Payment",
                "points": 4,
                "ratings": {
                    "0": {"description": "I determined a realistic down payment (targeting 20%), calculated the loan amount (price minus down payment), and showed the math", "points": 4},
                    "1": {"description": "I stated a down payment but did not show how I calculated the loan amount", "points": 3},
                    "2": {"description": "I did not include a down payment in my calculations", "points": 2},
                    "3": {"description": "Not addressed", "points": 0},
                },
            },
            "2": {
                "description": "Term Analysis",
                "points": 4,
                "ratings": {
                    "0": {"description": "I chose a preferred term and wrote a paragraph explaining the tradeoffs between shorter and longer terms", "points": 4},
                    "1": {"description": "I chose a term but my reasoning is weak or generic", "points": 3},
                    "2": {"description": "I stated a preference without any explanation", "points": 2},
                    "3": {"description": "No term preference stated", "points": 0},
                },
            },
            "3": {
                "description": "Math Shown",
                "points": 4,
                "ratings": {
                    "0": {"description": "All numbers are visible, I used a calculator tool (screenshot or link), and each answer includes a brief label", "points": 4},
                    "1": {"description": "Most work is shown but some calculations lack labels or sources", "points": 3},
                    "2": {"description": "I gave answers only without showing how I got them", "points": 2},
                    "3": {"description": "No math shown", "points": 0},
                },
            },
        },
    },

    # ── 04 ─────────────────────────────────────────────
    "04 \u2014 Insurance: You\u2019re Required to Buy It, You Should Understand It": {
        "title": "04 — Insurance Plan Self-Assessment",
        "criteria": {
            "0": {
                "description": "Quote Data",
                "points": 6,
                "ratings": {
                    "0": {"description": "I got an insurance estimate and recorded liability limits, collision deductible, comprehensive deductible, PIP, and UM/UIM coverage", "points": 6},
                    "1": {"description": "I recorded 4 of the 6 coverage types", "points": 4},
                    "2": {"description": "I recorded 1-2 coverage types", "points": 2},
                    "3": {"description": "No insurance data collected", "points": 0},
                },
            },
            "1": {
                "description": "Cost Calculation",
                "points": 6,
                "ratings": {
                    "0": {"description": "I recorded the estimated monthly premium and calculated the annual cost", "points": 6},
                    "1": {"description": "I recorded monthly or annual but not both", "points": 4},
                    "2": {"description": "I estimated a cost without using a quote tool or real data", "points": 2},
                    "3": {"description": "No cost information provided", "points": 0},
                },
            },
            "2": {
                "description": "Deductible Comparison",
                "points": 4,
                "ratings": {
                    "0": {"description": "I calculated both scenarios ($500 vs $1,000 deductible) and determined the savings over 3 claim-free years", "points": 4},
                    "1": {"description": "I calculated one deductible scenario but not both", "points": 3},
                    "2": {"description": "I attempted the comparison but the math is incomplete", "points": 2},
                    "3": {"description": "No deductible comparison", "points": 0},
                },
            },
            "3": {
                "description": "Evidence",
                "points": 4,
                "ratings": {
                    "0": {"description": "I included a screenshot of the online quote tool or a real insurance quote", "points": 4},
                    "1": {"description": "I included partial evidence (screenshot is incomplete)", "points": 3},
                    "2": {"description": "I described my source but provided no screenshot", "points": 2},
                    "3": {"description": "No evidence provided", "points": 0},
                },
            },
        },
    },

    # ── 05 ─────────────────────────────────────────────
    "05 — The Car Payment Is the Smallest Part": {
        "title": "05 — Total Cost of Ownership Self-Assessment",
        "criteria": {
            "0": {
                "description": "TCO Categories",
                "points": 8,
                "ratings": {
                    "0": {"description": "I filled in all 7 cost categories: payment, insurance, fuel, maintenance, registration/fees, depreciation, and parking", "points": 8},
                    "1": {"description": "I filled in 5-6 of the 7 categories", "points": 6},
                    "2": {"description": "I filled in 3-4 categories", "points": 3},
                    "3": {"description": "Fewer than 3 categories or not submitted", "points": 0},
                },
            },
            "1": {
                "description": "Cost Calculations",
                "points": 7,
                "ratings": {
                    "0": {"description": "I calculated monthly cost, annual cost, and cost per mile", "points": 7},
                    "1": {"description": "I calculated 2 of the 3 (monthly, annual, cost-per-mile)", "points": 5},
                    "2": {"description": "I calculated 1 of the 3", "points": 3},
                    "3": {"description": "No cost calculations", "points": 0},
                },
            },
            "2": {
                "description": "New vs Used Comparison",
                "points": 5,
                "ratings": {
                    "0": {"description": "I built a 5-year comparison of new vs. used for the same vehicle with specific numbers for both", "points": 5},
                    "1": {"description": "I compared but the data is incomplete for one option", "points": 4},
                    "2": {"description": "I only analyzed one option (new or used, not both)", "points": 2},
                    "3": {"description": "No comparison built", "points": 0},
                },
            },
            "3": {
                "description": "Reflection",
                "points": 5,
                "ratings": {
                    "0": {"description": "I wrote a paragraph identifying my biggest costs and one realistic step I could take to reduce my TCO", "points": 5},
                    "1": {"description": "I identified my biggest costs but did not include a reduction step", "points": 4},
                    "2": {"description": "I wrote something vague that does not reference my specific data", "points": 2},
                    "3": {"description": "No reflection", "points": 0},
                },
            },
        },
    },

    # ── 06 ─────────────────────────────────────────────
    "06 — Four Patches of Rubber Between You and the Road": {
        "title": "06 — Tire Specifications Self-Assessment",
        "criteria": {
            "0": {
                "description": "Tire Size Lookup",
                "points": 4,
                "ratings": {
                    "0": {"description": "I found the correct tire size from the door jamb placard or owner's manual and cited my source", "points": 4},
                    "1": {"description": "I found the correct size but did not cite my source", "points": 3},
                    "2": {"description": "I guessed a tire size without looking it up", "points": 2},
                    "3": {"description": "No tire size identified", "points": 0},
                },
            },
            "1": {
                "description": "Tire Selection",
                "points": 4,
                "ratings": {
                    "0": {"description": "I selected a specific tire with brand, model, type, price per tire, set-of-4 price, treadwear warranty, and calculated cost per mile", "points": 4},
                    "1": {"description": "I selected a tire with 4-5 of the required details (missing cost-per-mile or warranty)", "points": 3},
                    "2": {"description": "I selected a tire with 1-2 details only", "points": 2},
                    "3": {"description": "No tire selected", "points": 0},
                },
            },
            "2": {
                "description": "Installation Cost",
                "points": 3,
                "ratings": {
                    "0": {"description": "I got an installation estimate from a real source (local shop or online retailer)", "points": 3},
                    "1": {"description": "I estimated a cost without citing a specific source", "points": 2},
                    "2": {"description": "I mentioned installation but did not estimate cost", "points": 1},
                    "3": {"description": "Not addressed", "points": 0},
                },
            },
            "3": {
                "description": "Rotation Schedule",
                "points": 4,
                "ratings": {
                    "0": {"description": "I created a rotation schedule based on manufacturer recommendations and my estimated annual mileage", "points": 4},
                    "1": {"description": "I created a schedule but did not tie it to my annual mileage", "points": 3},
                    "2": {"description": "I mentioned tire rotation but did not create a schedule", "points": 2},
                    "3": {"description": "Rotation not addressed", "points": 0},
                },
            },
        },
    },

    # ── 07 ─────────────────────────────────────────────
    "07 — The 3,000-Mile Myth": {
        "title": "07 — Maintenance Schedule Self-Assessment",
        "criteria": {
            "0": {
                "description": "Owner's Manual Source",
                "points": 4,
                "ratings": {
                    "0": {"description": "I found the digital owner's manual for my portfolio vehicle and cited it (link or title)", "points": 4},
                    "1": {"description": "I found the manual but did not cite it", "points": 3},
                    "2": {"description": "I used a generic maintenance schedule not specific to my vehicle", "points": 2},
                    "3": {"description": "No source identified", "points": 0},
                },
            },
            "1": {
                "description": "Service Intervals",
                "points": 6,
                "ratings": {
                    "0": {"description": "I recorded manufacturer-recommended intervals for all 6+ services: oil (with type/viscosity), tire rotation, coolant flush, transmission fluid, brake fluid, and at least one more", "points": 6},
                    "1": {"description": "I recorded intervals for 4-5 services", "points": 4},
                    "2": {"description": "I recorded intervals for 2-3 services", "points": 2},
                    "3": {"description": "Fewer than 2 services or not submitted", "points": 0},
                },
            },
            "2": {
                "description": "Annual Cost Calculation",
                "points": 5,
                "ratings": {
                    "0": {"description": "I calculated the annual cost of following the manufacturer schedule with local pricing for each service", "points": 5},
                    "1": {"description": "I priced most services but some estimates are missing", "points": 4},
                    "2": {"description": "I gave a total annual cost without a per-service breakdown", "points": 2},
                    "3": {"description": "No cost calculation", "points": 0},
                },
            },
        },
    },

    # ── 08 ─────────────────────────────────────────────
    "08 — Trust, But Verify": {
        "title": "08 — Finding a Mechanic Self-Assessment",
        "criteria": {
            "0": {
                "description": "Shop Research",
                "points": 5,
                "ratings": {
                    "0": {"description": "I researched 3 auto repair shops (at least 1 independent and 1 dealership or chain) with name, address, and all required details", "points": 5},
                    "1": {"description": "I researched 3 shops but am missing details for some", "points": 4},
                    "2": {"description": "I researched only 2 shops", "points": 2},
                    "3": {"description": "Fewer than 2 shops or not submitted", "points": 0},
                },
            },
            "1": {
                "description": "Evaluation Criteria",
                "points": 4,
                "ratings": {
                    "0": {"description": "For each shop I recorded: ASE certifications, Google review count and rating, how they respond to negative reviews, estimate policy (written Y/N), and labor rate", "points": 4},
                    "1": {"description": "I recorded 3-4 of the 5 evaluation criteria for each shop", "points": 3},
                    "2": {"description": "I recorded 1-2 criteria", "points": 2},
                    "3": {"description": "No evaluation criteria recorded", "points": 0},
                },
            },
            "2": {
                "description": "Selection Rationale",
                "points": 3,
                "ratings": {
                    "0": {"description": "I chose a primary shop and wrote a paragraph explaining my choice with specific evidence from my research", "points": 3},
                    "1": {"description": "I chose a shop but my reasoning lacks specific evidence", "points": 2},
                    "2": {"description": "I stated a preference without explanation", "points": 1},
                    "3": {"description": "No selection made", "points": 0},
                },
            },
            "3": {
                "description": "Evidence",
                "points": 3,
                "ratings": {
                    "0": {"description": "I included links to shop pages or screenshots of reviews", "points": 3},
                    "1": {"description": "I included partial evidence", "points": 2},
                    "2": {"description": "I named the shops but provided no links or screenshots", "points": 1},
                    "3": {"description": "No evidence", "points": 0},
                },
            },
        },
    },

    # ── 09 ─────────────────────────────────────────────
    "09 \u2014 What the Seller Won\u2019t Tell You": {
        "title": "09 — Pre-Purchase Inspection Self-Assessment",
        "criteria": {
            "0": {
                "description": "Visual Inspection Section",
                "points": 5,
                "ratings": {
                    "0": {"description": "I listed 10+ visual inspection items with what to look for and what bad results mean", "points": 5},
                    "1": {"description": "I listed 7-9 items with explanations", "points": 4},
                    "2": {"description": "I listed 4-6 items", "points": 2},
                    "3": {"description": "Fewer than 4 items or not submitted", "points": 0},
                },
            },
            "1": {
                "description": "Test Drive Section",
                "points": 4,
                "ratings": {
                    "0": {"description": "I listed 8+ test drive items with instructions on what to check", "points": 4},
                    "1": {"description": "I listed 5-7 items", "points": 3},
                    "2": {"description": "I listed 3-4 items", "points": 2},
                    "3": {"description": "Fewer than 3 items", "points": 0},
                },
            },
            "2": {
                "description": "Seller Questions",
                "points": 4,
                "ratings": {
                    "0": {"description": "I wrote 5+ specific questions to ask the seller", "points": 4},
                    "1": {"description": "I wrote 3-4 questions", "points": 3},
                    "2": {"description": "I wrote 1-2 questions", "points": 2},
                    "3": {"description": "No questions written", "points": 0},
                },
            },
            "3": {
                "description": "History Verification",
                "points": 4,
                "ratings": {
                    "0": {"description": "I listed specific items to check using free VIN tools and named the tools", "points": 4},
                    "1": {"description": "I listed items to check but did not name specific tools", "points": 3},
                    "2": {"description": "I mentioned checking history but no specific items listed", "points": 2},
                    "3": {"description": "No history verification addressed", "points": 0},
                },
            },
            "4": {
                "description": "Format & Usability",
                "points": 3,
                "ratings": {
                    "0": {"description": "My checklist is formatted as a printable document I could actually bring to a car viewing (organized sections, checkboxes or blanks)", "points": 3},
                    "1": {"description": "My checklist is organized but not formatted for printing", "points": 2},
                    "2": {"description": "My checklist is a wall of text with no clear organization", "points": 1},
                    "3": {"description": "No checklist format attempted", "points": 0},
                },
            },
        },
    },

    # ── 10 ─────────────────────────────────────────────
    "10 \u2014 Stranded Is a Plan You Didn\u2019t Make": {
        "title": "10 — Emergency Preparedness Self-Assessment",
        "criteria": {
            "0": {
                "description": "Emergency Kit List",
                "points": 6,
                "ratings": {
                    "0": {"description": "I listed 10+ items across all 3 categories (visibility, recovery, first aid) with product name, source, price, and why each is included", "points": 6},
                    "1": {"description": "I listed 7-9 items with most details", "points": 4},
                    "2": {"description": "I listed 4-6 items", "points": 2},
                    "3": {"description": "Fewer than 4 items or not submitted", "points": 0},
                },
            },
            "1": {
                "description": "Kit Budget",
                "points": 4,
                "ratings": {
                    "0": {"description": "I calculated a total kit cost (in the $50-$200 range) with per-item prices", "points": 4},
                    "1": {"description": "I have a total cost but no per-item breakdown", "points": 3},
                    "2": {"description": "I gave a rough estimate only", "points": 2},
                    "3": {"description": "No cost information", "points": 0},
                },
            },
            "2": {
                "description": "Response Procedures",
                "points": 7,
                "ratings": {
                    "0": {"description": "I wrote step-by-step response procedures for all 3 scenarios: flat tire on a two-lane road, dead battery in a parking lot, and minor fender-bender — referencing which kit items to use and when to call for help", "points": 7},
                    "1": {"description": "I completed 2 of the 3 scenario procedures", "points": 5},
                    "2": {"description": "I completed 1 scenario procedure", "points": 3},
                    "3": {"description": "No response procedures written", "points": 0},
                },
            },
            "3": {
                "description": "Practicality",
                "points": 3,
                "ratings": {
                    "0": {"description": "All items are practical, road-relevant, and would fit in a car trunk", "points": 3},
                    "1": {"description": "Most items are practical but 1-2 are questionable", "points": 2},
                    "2": {"description": "Several items are impractical or not road-relevant", "points": 1},
                    "3": {"description": "Kit is not practical", "points": 0},
                },
            },
        },
    },

    # ── 11 ─────────────────────────────────────────────
    "11 \u2014 Free Repairs You Didn\u2019t Know You Had": {
        "title": "11 — Warranty & Recall Self-Assessment",
        "criteria": {
            "0": {
                "description": "Recall Check",
                "points": 4,
                "ratings": {
                    "0": {"description": "I searched NHTSA.gov/recalls with my portfolio vehicle's VIN and recorded any open recalls with descriptions", "points": 4},
                    "1": {"description": "I searched NHTSA but my results are incomplete", "points": 3},
                    "2": {"description": "I mentioned recalls generally without using the VIN lookup", "points": 2},
                    "3": {"description": "No recall check performed", "points": 0},
                },
            },
            "1": {
                "description": "Warranty Coverage",
                "points": 4,
                "ratings": {
                    "0": {"description": "I identified all 4 warranty types with coverage periods: bumper-to-bumper, powertrain, corrosion, and federal emissions", "points": 4},
                    "1": {"description": "I identified 3 of the 4 warranty types", "points": 3},
                    "2": {"description": "I identified 1-2 warranty types", "points": 2},
                    "3": {"description": "No warranty information", "points": 0},
                },
            },
            "2": {
                "description": "TSB Research",
                "points": 3,
                "ratings": {
                    "0": {"description": "I searched for Technical Service Bulletins related to my vehicle and listed what I found (or documented that none exist)", "points": 3},
                    "1": {"description": "I searched but my documentation is incomplete", "points": 2},
                    "2": {"description": "I did not search for TSBs", "points": 1},
                    "3": {"description": "Not addressed", "points": 0},
                },
            },
            "3": {
                "description": "Summary Document",
                "points": 4,
                "ratings": {
                    "0": {"description": "I created a one-page warranty summary formatted for glovebox use", "points": 4},
                    "1": {"description": "I created a summary but it is not well-formatted or is too long", "points": 3},
                    "2": {"description": "I submitted raw text without formatting", "points": 2},
                    "3": {"description": "No summary document", "points": 0},
                },
            },
        },
    },

    # ── 12 ─────────────────────────────────────────────
    "12 \u2014 The Word \u201cNo\u201d Is Worth Thousands": {
        "title": "12 — Negotiation Plan Self-Assessment",
        "criteria": {
            "0": {
                "description": "Market Research",
                "points": 6,
                "ratings": {
                    "0": {"description": "I looked up the fair market price on Edmunds AND cross-checked on KBB", "points": 6},
                    "1": {"description": "I used only one pricing source (Edmunds or KBB, not both)", "points": 4},
                    "2": {"description": "I estimated a price without using a valuation tool", "points": 2},
                    "3": {"description": "No market research", "points": 0},
                },
            },
            "1": {
                "description": "Price Targets",
                "points": 5,
                "ratings": {
                    "0": {"description": "I set a target price (opening offer) and a walk-away price (absolute maximum) with reasoning for both", "points": 5},
                    "1": {"description": "I set both prices but did not explain my reasoning", "points": 4},
                    "2": {"description": "I set only one price (target or walk-away, not both)", "points": 2},
                    "3": {"description": "No price targets set", "points": 0},
                },
            },
            "2": {
                "description": "Negotiation Phrases",
                "points": 5,
                "ratings": {
                    "0": {"description": "I wrote 3 negotiation phrases specific to my vehicle and situation", "points": 5},
                    "1": {"description": "I wrote 2 phrases", "points": 4},
                    "2": {"description": "I wrote 1 generic phrase", "points": 2},
                    "3": {"description": "No phrases written", "points": 0},
                },
            },
            "3": {
                "description": "Walk-Away Plan",
                "points": 4,
                "ratings": {
                    "0": {"description": "I wrote the exact words I would use to walk away and described what I would do next", "points": 4},
                    "1": {"description": "I described walking away but did not include next steps", "points": 3},
                    "2": {"description": "I mentioned walking away vaguely", "points": 2},
                    "3": {"description": "No walk-away plan", "points": 0},
                },
            },
        },
    },

    # ── 13 ─────────────────────────────────────────────
    "13 — Every Mile Is on Your Record": {
        "title": "13 — Driving Record Self-Assessment",
        "criteria": {
            "0": {
                "description": "Violation Research",
                "points": 4,
                "ratings": {
                    "0": {"description": "I researched 5 Oregon traffic violations (speeding, running a red light, distracted driving, reckless driving, and DUI) with their base fines", "points": 4},
                    "1": {"description": "I researched 3-4 violations with fines", "points": 3},
                    "2": {"description": "I researched 1-2 violations", "points": 2},
                    "3": {"description": "No violations researched", "points": 0},
                },
            },
            "1": {
                "description": "Insurance Impact",
                "points": 4,
                "ratings": {
                    "0": {"description": "For each violation I researched the typical insurance premium increase (both percentage and dollars per month)", "points": 4},
                    "1": {"description": "I researched insurance impact for 3-4 violations", "points": 3},
                    "2": {"description": "I researched impact for 1-2 violations", "points": 2},
                    "3": {"description": "No insurance impact data", "points": 0},
                },
            },
            "2": {
                "description": "3-Year Cost Calculation",
                "points": 4,
                "ratings": {
                    "0": {"description": "I calculated the full 3-year cost of a speeding ticket: court fine + (monthly insurance increase x 36) + any additional costs", "points": 4},
                    "1": {"description": "I calculated partially but missed one cost component", "points": 3},
                    "2": {"description": "I estimated a total without showing the breakdown", "points": 2},
                    "3": {"description": "No cost calculation", "points": 0},
                },
            },
            "3": {
                "description": "Safe Driving Commitment",
                "points": 3,
                "ratings": {
                    "0": {"description": "I wrote a commitment of 5+ sentences stating specific habits with financial reasoning", "points": 3},
                    "1": {"description": "I wrote 3-4 sentences with some financial reasoning", "points": 2},
                    "2": {"description": "I wrote 1-2 sentences without financial reasoning", "points": 1},
                    "3": {"description": "No commitment written", "points": 0},
                },
            },
        },
    },

    # ── 14 ─────────────────────────────────────────────
    "14 — The Breakeven Point": {
        "title": "14 — Long-Term Ownership Self-Assessment",
        "criteria": {
            "0": {
                "description": "Current Value",
                "points": 4,
                "ratings": {
                    "0": {"description": "I looked up my portfolio vehicle's current KBB Private Party Value and cited the source", "points": 4},
                    "1": {"description": "I found a value but did not cite the source", "points": 3},
                    "2": {"description": "I estimated a value without looking it up", "points": 2},
                    "3": {"description": "No current value identified", "points": 0},
                },
            },
            "1": {
                "description": "Depreciation Projection",
                "points": 6,
                "ratings": {
                    "0": {"description": "I projected the vehicle's value at all 5 intervals (years 1, 3, 5, 7, and 10) using the lesson's depreciation rates (20% year 1, 15% years 2-3, 10% years 4-5, 5-7% after)", "points": 6},
                    "1": {"description": "I projected values at 3-4 of the 5 intervals", "points": 4},
                    "2": {"description": "I projected values at 1-2 intervals", "points": 2},
                    "3": {"description": "No depreciation projection", "points": 0},
                },
            },
            "2": {
                "description": "Repair Threshold",
                "points": 5,
                "ratings": {
                    "0": {"description": "I calculated at what future value a $2,000 repair would exceed 50% of the car's worth", "points": 5},
                    "1": {"description": "I attempted the calculation but made a math error", "points": 4},
                    "2": {"description": "I mentioned the concept but did not calculate it", "points": 2},
                    "3": {"description": "Not addressed", "points": 0},
                },
            },
            "3": {
                "description": "Ownership Plan",
                "points": 5,
                "ratings": {
                    "0": {"description": "I wrote a paragraph stating how long I'd keep the vehicle, my optimal ownership window (when repair costs exceed value), when I'd sell, and how (private sale, trade-in, or dealer)", "points": 5},
                    "1": {"description": "I addressed 3 of the 4 elements (keep duration, optimal window, sell timing, sell method)", "points": 4},
                    "2": {"description": "I addressed only 1 element", "points": 2},
                    "3": {"description": "No ownership plan written", "points": 0},
                },
            },
        },
    },

    # ── 15 ─────────────────────────────────────────────
    "15 — The Drivetrain Is Changing": {
        "title": "15 — EV vs Gas Comparison Self-Assessment",
        "criteria": {
            "0": {
                "description": "Gas Vehicle Baseline",
                "points": 5,
                "ratings": {
                    "0": {"description": "I recorded my portfolio vehicle's purchase price, MPG, and estimated annual maintenance cost", "points": 5},
                    "1": {"description": "I recorded 2 of the 3 data points", "points": 4},
                    "2": {"description": "I recorded 1 data point", "points": 2},
                    "3": {"description": "No baseline established", "points": 0},
                },
            },
            "1": {
                "description": "EV/Hybrid Equivalent",
                "points": 5,
                "ratings": {
                    "0": {"description": "I found an electric or hybrid equivalent in the same category with purchase price, efficiency, and maintenance cost, with source cited", "points": 5},
                    "1": {"description": "I found an equivalent but am missing some data points or no source cited", "points": 4},
                    "2": {"description": "I picked a vehicle from the wrong category or with minimal data", "points": 2},
                    "3": {"description": "No equivalent identified", "points": 0},
                },
            },
            "2": {
                "description": "5-Year TCO Comparison",
                "points": 8,
                "ratings": {
                    "0": {"description": "I compared all 5 categories for both vehicles: purchase price (after credits), fuel/electricity, maintenance, insurance, and estimated resale", "points": 8},
                    "1": {"description": "I compared 3-4 of the 5 categories", "points": 6},
                    "2": {"description": "I compared 1-2 categories", "points": 3},
                    "3": {"description": "No TCO comparison built", "points": 0},
                },
            },
            "3": {
                "description": "Written Analysis",
                "points": 7,
                "ratings": {
                    "0": {"description": "I wrote 2-3 paragraphs answering all 3 questions: which costs less, is the EV practical for my situation, and what would need to change", "points": 7},
                    "1": {"description": "I answered 2 of the 3 questions", "points": 5},
                    "2": {"description": "I answered 1 question", "points": 3},
                    "3": {"description": "No written analysis", "points": 0},
                },
            },
        },
    },

    # ── 16 ─────────────────────────────────────────────
    "16 \u2014 Your Owner\u2019s Manual for Owning a Car": {
        "title": "16 — Portfolio Capstone Rubric (Teacher-Graded)",
        "criteria": {
            "0": {
                "description": "Portfolio Completeness",
                "points": 15,
                "ratings": {
                    "0": {"description": "All 15 portfolio pages are present with a title page, assembled into a single document, clearly labeled, and formatted consistently", "points": 15},
                    "1": {"description": "12-14 pages present with mostly consistent formatting", "points": 10},
                    "2": {"description": "8-11 pages present or formatting is inconsistent", "points": 6},
                    "3": {"description": "Fewer than 8 pages or not submitted", "points": 0},
                },
            },
            "1": {
                "description": "Cross-Page Accuracy",
                "points": 10,
                "ratings": {
                    "0": {"description": "Numbers are consistent across pages — insurance matches TCO, maintenance schedule aligns with vehicle, financing matches purchase price", "points": 10},
                    "1": {"description": "1-2 minor inconsistencies across pages", "points": 7},
                    "2": {"description": "Several inconsistencies — numbers don't add up across pages", "points": 4},
                    "3": {"description": "Not checked or major contradictions throughout", "points": 0},
                },
            },
            "2": {
                "description": "Peer Review",
                "points": 10,
                "ratings": {
                    "0": {"description": "Completed portfolio exchange, filled out the 7-item checklist, and provided written feedback to classmate", "points": 10},
                    "1": {"description": "Completed exchange with partial checklist", "points": 7},
                    "2": {"description": "Checklist only, no written feedback", "points": 4},
                    "3": {"description": "No peer review completed", "points": 0},
                },
            },
            "3": {
                "description": "Final Reflection",
                "points": 15,
                "ratings": {
                    "0": {"description": "Full-page reflection addressing The Surprise, The Change, and The Keeper with specific examples from the portfolio", "points": 15},
                    "1": {"description": "Addresses all 3 prompts but is thin on specific examples", "points": 10},
                    "2": {"description": "Addresses 1-2 of the 3 prompts", "points": 6},
                    "3": {"description": "No reflection or missing", "points": 0},
                },
            },
        },
    },

    # ── Lab: Predator 212 Teardown ─────────────────────
    "Predator 212 - Engine Teardown Portfolio": {
        "title": "Engine Teardown Portfolio Rubric (Teacher-Graded)",
        "criteria": {
            "0": {
                "description": "Safety & Procedure",
                "points": 25,
                "ratings": {
                    "0": {"description": "Proper PPE worn throughout, correct tool use, organized workspace, parts stored and labeled in order", "points": 25},
                    "1": {"description": "Mostly safe with minor gaps (missed PPE once, workspace occasionally disorganized)", "points": 18},
                    "2": {"description": "Significant safety lapses or disorganized parts management", "points": 10},
                    "3": {"description": "Unsafe practices or incomplete", "points": 0},
                },
            },
            "1": {
                "description": "Photo/Video Documentation",
                "points": 35,
                "ratings": {
                    "0": {"description": "All 24 required photos and 3 required videos present, clear, properly labeled and described", "points": 35},
                    "1": {"description": "18-23 photos present or videos missing, most labeled", "points": 25},
                    "2": {"description": "12-17 photos, some unlabeled or unclear", "points": 14},
                    "3": {"description": "Fewer than 12 photos or not submitted", "points": 0},
                },
            },
            "2": {
                "description": "Written Assessments",
                "points": 20,
                "ratings": {
                    "0": {"description": "All 10 written assessments are thoughtful, accurate, and demonstrate understanding of component function", "points": 20},
                    "1": {"description": "7-9 assessments completed, mostly accurate", "points": 14},
                    "2": {"description": "4-6 assessments completed", "points": 8},
                    "3": {"description": "Fewer than 4 assessments", "points": 0},
                },
            },
            "3": {
                "description": "Checkpoint Completion",
                "points": 20,
                "ratings": {
                    "0": {"description": "All 6 instructor checkpoints signed before advancing to the next phase", "points": 20},
                    "1": {"description": "4-5 checkpoints signed", "points": 14},
                    "2": {"description": "2-3 checkpoints signed", "points": 8},
                    "3": {"description": "Fewer than 2 checkpoints", "points": 0},
                },
            },
        },
    },

    # ── Lab: Oil Change ────────────────────────────────
    # Three-phase lab (ASE-EF aligned):
    #   Pre-Lab: Student looks up specs for demo vehicle before class
    #   Phase 1: Demo on Mr. McAteer's car — assigned observation roles, students assist
    #   Phase 2: Student performs on own vehicle with buddy (one works, one reads/checks)
    #   Post-Lab: Brief reflection — what was different, what would you do differently
    "Oil Change Lab": {
        "title": "Oil Change Lab Rubric (Teacher-Graded)",
        "criteria": {
            "0": {
                "description": "Pre-Lab Spec Lookup",
                "points": 5,
                "ratings": {
                    "0": {"description": "Before demo day, looked up and recorded the demo vehicle's oil type/viscosity, capacity, drain plug torque, and filter part number from the owner's manual or service database", "points": 5},
                    "1": {"description": "Looked up 2-3 of the 4 specs before class", "points": 4},
                    "2": {"description": "Attempted but only found 1 spec or used wrong source", "points": 2},
                    "3": {"description": "No pre-lab completed", "points": 0},
                },
            },
            "1": {
                "description": "Demo Phase — Active Observation",
                "points": 10,
                "ratings": {
                    "0": {"description": "During class demo, fulfilled assigned observation role (safety, tools, specs, or procedure) and recorded: every step in sequence, tools used at each step, and key callouts (crush washer check, filter gasket lube, drain stream positioning)", "points": 10},
                    "1": {"description": "Good notes but missing role-specific details or 2-3 steps out of order", "points": 7},
                    "2": {"description": "Minimal notes, did not fulfill observation role", "points": 4},
                    "3": {"description": "No demo notes taken", "points": 0},
                },
            },
            "2": {
                "description": "Independent Phase — Procedure Execution",
                "points": 15,
                "ratings": {
                    "0": {"description": "With buddy, completed all steps on own vehicle safely: PPE on, vehicle lifted and secured at correct points, drain plug removed (arm to the side), plug/washer inspected, filter replaced (gasket lubed, hand-tight + turn), refilled to spec, dipstick check, run engine 30 sec, re-check level, torque drain plug to spec", "points": 15},
                    "1": {"description": "All steps completed with one minor omission (e.g., forgot re-check after running engine or didn't torque to spec)", "points": 11},
                    "2": {"description": "Significant procedural error (wrong oil type/amount, skipped filter, unsafe lifting, or worked alone without buddy)", "points": 6},
                    "3": {"description": "Incomplete or not performed", "points": 0},
                },
            },
            "3": {
                "description": "Work Order & Vehicle Specs",
                "points": 10,
                "ratings": {
                    "0": {"description": "Completed shop work order: vehicle year/make/model/mileage, oil type and viscosity per manufacturer, capacity, filter part number, drain plug torque spec — all sourced and cited; time in/time out recorded", "points": 10},
                    "1": {"description": "Work order mostly complete, missing 1-2 specs or no source cited", "points": 7},
                    "2": {"description": "Partial work order, used generic values instead of vehicle-specific", "points": 4},
                    "3": {"description": "No work order completed", "points": 0},
                },
            },
            "4": {
                "description": "Documentation & Reflection",
                "points": 10,
                "ratings": {
                    "0": {"description": "Photos at each key step (before drain, draining, old filter, new filter, refill, dipstick) with captions; plus a brief write-up noting what was different on your car vs. the demo and what you'd do differently next time", "points": 10},
                    "1": {"description": "Photos present but missing 2+ steps or no reflection write-up", "points": 7},
                    "2": {"description": "1-2 photos only, no write-up", "points": 4},
                    "3": {"description": "No documentation", "points": 0},
                },
            },
        },
    },

    # ── Lab: Brake Check & Rotor Turning ───────────────
    # Three-phase lab (ASE-EF aligned):
    #   Pre-Lab: Student looks up brake specs for demo vehicle
    #   Phase 1: Demo on Mr. McAteer's car — observation roles, spec sheet, students assist
    #            Brake dust handled with wet-wipe or HEPA brake washer (never compressed air)
    #   Phase 2: Student performs inspection + measurement on own vehicle with buddy
    #            Lathe work is teacher-supervised (safety-critical)
    #   Post-Lab: Written verdict with spec-vs-actual comparison
    "Brake Check & Rotor Turning Lab": {
        "title": "Brake Check & Rotor Turning Rubric (Teacher-Graded)",
        "criteria": {
            "0": {
                "description": "Pre-Lab Spec Lookup",
                "points": 5,
                "ratings": {
                    "0": {"description": "Before demo day, looked up and recorded the demo vehicle's minimum rotor thickness, discard thickness, maximum runout spec, and minimum pad thickness from service data", "points": 5},
                    "1": {"description": "Looked up 2-3 of the 4 specs", "points": 4},
                    "2": {"description": "Attempted but only found 1 spec", "points": 2},
                    "3": {"description": "No pre-lab completed", "points": 0},
                },
            },
            "1": {
                "description": "Demo Phase — Active Observation",
                "points": 10,
                "ratings": {
                    "0": {"description": "During class demo, fulfilled assigned role and recorded: all measurement readings called out (pad thickness, rotor thickness at 3+ points, runout), tool setup for micrometer and dial indicator, brake dust handling method used, and caliper support technique", "points": 10},
                    "1": {"description": "Good notes but missing 2-3 readings or tool setup details", "points": 7},
                    "2": {"description": "Minimal notes, did not fulfill observation role", "points": 4},
                    "3": {"description": "No demo notes taken", "points": 0},
                },
            },
            "2": {
                "description": "Independent Phase — Brake Inspection",
                "points": 20,
                "ratings": {
                    "0": {"description": "With buddy, on own vehicle: safely removed wheel, cleaned brake dust with wet method (not compressed air), measured pad thickness with calipers (inner and outer), assessed condition (good/fair/replace), checked for uneven wear patterns, inspected brake lines/hoses, and supported caliper properly (wire hook, not hanging by hose)", "points": 20},
                    "1": {"description": "Inspection completed but missing pad measurement, line inspection, or used compressed air on dust", "points": 14},
                    "2": {"description": "Partial inspection — looked at pads but no measurements or condition assessment", "points": 8},
                    "3": {"description": "Inspection not performed", "points": 0},
                },
            },
            "3": {
                "description": "Rotor Measurement & Lathe",
                "points": 20,
                "ratings": {
                    "0": {"description": "Measured rotor thickness with micrometer at 4+ points around the rotor, measured runout with dial indicator, calculated thickness variation, recorded all readings with units in spec-vs-actual format; observed or assisted with lathe work and recorded feed rate, cut depth, and post-turn measurement", "points": 20},
                    "1": {"description": "Thickness at 2-3 points and runout measured, compared to spec, but missing variation calculation or lathe documentation", "points": 14},
                    "2": {"description": "Attempted measurements but inaccurate readings or no comparison to spec", "points": 8},
                    "3": {"description": "No measurements taken", "points": 0},
                },
            },
            "4": {
                "description": "Work Order, Verdict & Reflection",
                "points": 20,
                "ratings": {
                    "0": {"description": "Complete measurement log (spec vs. actual for every reading), photos of pads and rotor surface, completed work order with vehicle info and time in/out, and a written verdict: safe to drive / needs pads / needs rotors / needs both — with reasoning tied directly to the numbers; reflection on what surprised you or what you'd check differently", "points": 20},
                    "1": {"description": "Measurement log and verdict present but missing photos, work order, or reflection", "points": 14},
                    "2": {"description": "Partial documentation, verdict given but not tied to measurements", "points": 8},
                    "3": {"description": "No documentation submitted", "points": 0},
                },
            },
        },
    },
}


# ══════════════════════════════════════════════════════════════
# DEPLOYMENT FUNCTIONS
# ══════════════════════════════════════════════════════════════

def get_assignments(url, headers, cid):
    """Fetch all assignments for a course, keyed by name."""
    assignments = {}
    for a in paginated_get(f"{url}/api/v1/courses/{cid}/assignments", headers, {"per_page": "50"}):
        assignments[a["name"]] = a
    return assignments


def dry_run():
    """Preview what would be created without making changes."""
    url, token = get_creds()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    total_found = 0
    total_missing = 0
    total_exists = 0

    for cid in ENGINES_FAB_COURSE_IDS:
        r = requests.get(f"{url}/api/v1/courses/{cid}", headers=headers)
        cname = r.json().get("name", f"Course {cid}")
        print(f"\n{'═' * 60}")
        print(f"  {cname} (ID: {cid})")
        print(f"{'═' * 60}")

        assignments = get_assignments(url, headers, cid)

        for asgn_name, rubric_def in RUBRICS.items():
            if asgn_name not in assignments:
                print(f"  ⚠ NOT FOUND: \"{asgn_name}\"")
                total_missing += 1
                continue

            asgn = assignments[asgn_name]
            has_rubric = bool(asgn.get("rubric"))

            # Verify point totals match
            rubric_total = sum(c["points"] for c in rubric_def["criteria"].values())
            asgn_points = asgn.get("points_possible", 0)
            points_match = "✓" if rubric_total == asgn_points else f"⚠ MISMATCH ({rubric_total} vs {asgn_points})"

            if has_rubric:
                print(f"  SKIP (rubric exists): {asgn_name}")
                total_exists += 1
            else:
                num_criteria = len(rubric_def["criteria"])
                print(f"  WOULD CREATE: \"{rubric_def['title']}\" ({num_criteria} criteria, {rubric_total} pts) {points_match}")
                total_found += 1

    print(f"\n{'═' * 60}")
    print(f"  DRY RUN SUMMARY")
    print(f"{'═' * 60}")
    print(f"  Would create: {total_found} rubrics")
    print(f"  Already exist: {total_exists}")
    print(f"  Not found: {total_missing}")
    if total_missing > 0:
        print(f"\n  ⚠ {total_missing} assignments not found — check names before deploying")
    print()


def deploy():
    """Create all rubrics on both courses."""
    url, token = get_creds()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    created = 0
    skipped = 0
    failed = 0
    not_found = 0

    for cid in ENGINES_FAB_COURSE_IDS:
        r = requests.get(f"{url}/api/v1/courses/{cid}", headers=headers)
        cname = r.json().get("name", f"Course {cid}")
        print(f"\n{'═' * 60}")
        print(f"  {cname} (ID: {cid})")
        print(f"{'═' * 60}")

        assignments = get_assignments(url, headers, cid)

        for asgn_name, rubric_def in RUBRICS.items():
            if asgn_name not in assignments:
                print(f"  ⚠ NOT FOUND: \"{asgn_name}\"")
                not_found += 1
                continue

            asgn = assignments[asgn_name]
            asgn_id = asgn["id"]

            if asgn.get("rubric"):
                print(f"  SKIP (rubric exists): {asgn_name}")
                skipped += 1
                continue

            payload = {
                "rubric": {
                    "title": rubric_def["title"],
                    "criteria": rubric_def["criteria"],
                },
                "rubric_association": {
                    "association_id": asgn_id,
                    "association_type": "Assignment",
                    "use_for_grading": True,
                    "purpose": "grading",
                },
            }

            r = requests.post(
                f"{url}/api/v1/courses/{cid}/rubrics",
                headers=headers,
                json=payload,
            )

            if r.status_code in (200, 201):
                print(f"  ✓ CREATED: {rubric_def['title']}")
                created += 1
            else:
                print(f"  ✗ FAILED ({r.status_code}): {asgn_name}")
                try:
                    err = r.json()
                    print(f"    Error: {json.dumps(err, indent=2)[:300]}")
                except Exception:
                    print(f"    Response: {r.text[:300]}")
                failed += 1

    print(f"\n{'═' * 60}")
    print(f"  DEPLOYMENT SUMMARY")
    print(f"{'═' * 60}")
    print(f"  Created:   {created}")
    print(f"  Skipped:   {skipped} (already had rubrics)")
    print(f"  Failed:    {failed}")
    print(f"  Not found: {not_found}")
    if failed > 0:
        print(f"\n  ⚠ {failed} rubric(s) failed to create — run --audit to check")
    print()


def audit():
    """Post-deploy audit: verify all rubrics were created correctly."""
    url, token = get_creds()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    for cid in ENGINES_FAB_COURSE_IDS:
        r = requests.get(f"{url}/api/v1/courses/{cid}", headers=headers)
        cname = r.json().get("name", f"Course {cid}")
        print(f"\n{'═' * 60}")
        print(f"  AUDIT: {cname} (ID: {cid})")
        print(f"{'═' * 60}")

        assignments = get_assignments(url, headers, cid)

        ok = 0
        problems = 0

        for asgn_name, rubric_def in RUBRICS.items():
            if asgn_name not in assignments:
                print(f"  ✗ MISSING ASSIGNMENT: \"{asgn_name}\"")
                problems += 1
                continue

            asgn = assignments[asgn_name]
            rubric = asgn.get("rubric")

            if not rubric:
                print(f"  ✗ NO RUBRIC: \"{asgn_name}\"")
                problems += 1
                continue

            # Verify criteria count
            expected_criteria = len(rubric_def["criteria"])
            actual_criteria = len(rubric)

            # Verify point total
            expected_total = sum(c["points"] for c in rubric_def["criteria"].values())
            actual_total = sum(c.get("points", 0) for c in rubric)
            asgn_points = asgn.get("points_possible", 0)

            if actual_criteria != expected_criteria:
                print(f"  ⚠ CRITERIA MISMATCH: \"{asgn_name}\" — expected {expected_criteria}, got {actual_criteria}")
                problems += 1
            elif actual_total != expected_total:
                print(f"  ⚠ POINTS MISMATCH: \"{asgn_name}\" — rubric total {actual_total}, expected {expected_total}")
                problems += 1
            elif actual_total != asgn_points:
                print(f"  ⚠ ASSIGNMENT POINTS MISMATCH: \"{asgn_name}\" — rubric {actual_total} pts vs assignment {asgn_points} pts")
                problems += 1
            else:
                print(f"  ✓ OK: \"{asgn_name}\" ({actual_criteria} criteria, {actual_total} pts)")
                ok += 1

        print(f"\n  Results: {ok} OK, {problems} problems")

    print(f"\n{'═' * 60}")
    print(f"  AUDIT COMPLETE")
    print(f"{'═' * 60}")
    print()


# Assignments that need online_upload added alongside existing online_text_entry
SUBMISSION_TYPE_FIXES = [
    "02 \u2014 Everything on the Sticker They Hope You Won\u2019t Read",
    "04 \u2014 Insurance: You\u2019re Required to Buy It, You Should Understand It",
    "05 — The Car Payment Is the Smallest Part",
    "09 \u2014 What the Seller Won\u2019t Tell You",
    "11 \u2014 Free Repairs You Didn\u2019t Know You Had",
    "15 — The Drivetrain Is Changing",
    "16 \u2014 Your Owner\u2019s Manual for Owning a Car",
]


def redeploy():
    """Delete existing rubrics and recreate with corrected text."""
    url, token = get_creds()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    deleted = 0
    created = 0
    failed = 0

    for cid in ENGINES_FAB_COURSE_IDS:
        r = requests.get(f"{url}/api/v1/courses/{cid}", headers=headers)
        cname = r.json().get("name", f"Course {cid}")
        print(f"\n{'═' * 60}")
        print(f"  REDEPLOY: {cname} (ID: {cid})")
        print(f"{'═' * 60}")

        assignments = get_assignments(url, headers, cid)

        for asgn_name, rubric_def in RUBRICS.items():
            if asgn_name not in assignments:
                print(f"  ⚠ NOT FOUND: \"{asgn_name}\"")
                continue

            asgn = assignments[asgn_name]
            asgn_id = asgn["id"]

            # Delete existing rubric if present
            rubric_settings = asgn.get("rubric_settings", {})
            existing_rubric_id = rubric_settings.get("id") if rubric_settings else None

            if existing_rubric_id:
                r = requests.delete(
                    f"{url}/api/v1/courses/{cid}/rubrics/{existing_rubric_id}",
                    headers=headers,
                )
                if r.status_code in (200, 204):
                    print(f"  DELETED old rubric for: {asgn_name}")
                    deleted += 1
                else:
                    print(f"  ⚠ Failed to delete rubric for {asgn_name}: {r.status_code}")

            # Create new rubric
            payload = {
                "rubric": {
                    "title": rubric_def["title"],
                    "criteria": rubric_def["criteria"],
                },
                "rubric_association": {
                    "association_id": asgn_id,
                    "association_type": "Assignment",
                    "use_for_grading": True,
                    "purpose": "grading",
                },
            }

            r = requests.post(
                f"{url}/api/v1/courses/{cid}/rubrics",
                headers=headers,
                json=payload,
            )

            if r.status_code in (200, 201):
                print(f"  ✓ CREATED: {rubric_def['title']}")
                created += 1
            else:
                print(f"  ✗ FAILED ({r.status_code}): {asgn_name}")
                try:
                    print(f"    {json.dumps(r.json(), indent=2)[:300]}")
                except Exception:
                    print(f"    {r.text[:300]}")
                failed += 1

    print(f"\n{'═' * 60}")
    print(f"  REDEPLOY SUMMARY")
    print(f"{'═' * 60}")
    print(f"  Deleted: {deleted}")
    print(f"  Created: {created}")
    print(f"  Failed:  {failed}")
    print()


def fix_submissions():
    """Add online_upload to assignments that need file upload alongside text entry."""
    url, token = get_creds()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    updated = 0
    skipped = 0

    for cid in ENGINES_FAB_COURSE_IDS:
        r = requests.get(f"{url}/api/v1/courses/{cid}", headers=headers)
        cname = r.json().get("name", f"Course {cid}")
        print(f"\n{'═' * 60}")
        print(f"  FIX SUBMISSIONS: {cname} (ID: {cid})")
        print(f"{'═' * 60}")

        assignments = get_assignments(url, headers, cid)

        for asgn_name in SUBMISSION_TYPE_FIXES:
            if asgn_name not in assignments:
                print(f"  ⚠ NOT FOUND: \"{asgn_name}\"")
                continue

            asgn = assignments[asgn_name]
            asgn_id = asgn["id"]
            current_types = asgn.get("submission_types", [])

            if "online_upload" in current_types and "online_text_entry" in current_types:
                print(f"  SKIP (already has both): {asgn_name}")
                skipped += 1
                continue

            new_types = list(set(current_types + ["online_upload", "online_text_entry"]))

            r = requests.put(
                f"{url}/api/v1/courses/{cid}/assignments/{asgn_id}",
                headers=headers,
                json={"assignment": {"submission_types": new_types}},
            )

            if r.status_code == 200:
                print(f"  ✓ UPDATED: {asgn_name} → {new_types}")
                updated += 1
            else:
                print(f"  ✗ FAILED ({r.status_code}): {asgn_name}")

    print(f"\n{'═' * 60}")
    print(f"  SUBMISSION TYPE SUMMARY")
    print(f"{'═' * 60}")
    print(f"  Updated: {updated}")
    print(f"  Skipped: {skipped}")
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Create self-assessed rubrics for Engines Fab courses"
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without making them")
    parser.add_argument("--deploy", action="store_true", help="Create all rubrics")
    parser.add_argument("--redeploy", action="store_true", help="Delete + recreate all rubrics (for corrections)")
    parser.add_argument("--fix-submissions", action="store_true", help="Add file upload to selected assignments")
    parser.add_argument("--audit", action="store_true", help="Verify rubrics after deployment")
    args = parser.parse_args()

    if args.dry_run:
        dry_run()
    elif args.deploy:
        deploy()
    elif args.redeploy:
        redeploy()
    elif args.fix_submissions:
        fix_submissions()
    elif args.audit:
        audit()
    else:
        parser.print_help()
