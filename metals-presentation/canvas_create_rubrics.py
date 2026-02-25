#!/usr/bin/env python3
"""
Create rubrics via Canvas REST API directly (canvasapi library has a bug with nested rubric criteria).
Announcements cannot be created as drafts in Canvas — they will be created as delayed posts instead.
"""

import os
import sys
import requests
import json

METALS_COURSE_IDS = [23164, 23132, 23157, 23188, 23177]

def get_creds():
    url = os.environ.get("CANVAS_API_URL")
    token = os.environ.get("CANVAS_API_TOKEN")
    if not url or not token:
        print("ERROR: Set CANVAS_API_URL and CANVAS_API_TOKEN")
        sys.exit(1)
    return url, token

RUBRICS = {
    "Portable Tool Organizer - SolidWorks": {
        "title": "Portable Tool Organizer — SolidWorks Rubric",
        "criteria": {
            "0": {
                "description": "Model Completeness",
                "points": 10,
                "ratings": {
                    "0": {"description": "All three tiers modeled with lid, accurate dimensions, parametric features", "points": 10},
                    "1": {"description": "Two tiers correct, minor dimension issues", "points": 7},
                    "2": {"description": "One tier or major errors", "points": 4},
                    "3": {"description": "Incomplete or not submitted", "points": 0},
                }
            },
            "1": {
                "description": "Parametric Design Practice",
                "points": 10,
                "ratings": {
                    "0": {"description": "Fully constrained sketches, named features, equations/relations used", "points": 10},
                    "1": {"description": "Mostly constrained, some features named", "points": 7},
                    "2": {"description": "Under-constrained, no naming, no relations", "points": 4},
                    "3": {"description": "No parametric thinking evident", "points": 0},
                }
            },
            "2": {
                "description": "File Quality & Submission",
                "points": 10,
                "ratings": {
                    "0": {"description": "Proper naming, all parts submitted, opens without errors", "points": 10},
                    "1": {"description": "Minor naming issues, all parts present", "points": 7},
                    "2": {"description": "Poor naming, missing parts, or corruption", "points": 4},
                    "3": {"description": "Not submitted or unusable", "points": 0},
                }
            },
        }
    },
    "Sheet Metal Cell Phone Stand - POP Writeup": {
        "title": "Sheet Metal Cell Phone Stand — POP Writeup Rubric",
        "criteria": {
            "0": {
                "description": "Design Intent & Problem Statement",
                "points": 10,
                "ratings": {
                    "0": {"description": "Clear problem, material/angle choices justified", "points": 10},
                    "1": {"description": "Problem stated but vague, some justification", "points": 7},
                    "2": {"description": "Minimal intent, no justification", "points": 4},
                    "3": {"description": "Missing or not submitted", "points": 0},
                }
            },
            "1": {
                "description": "Plan of Procedure (Step-by-Step)",
                "points": 20,
                "ratings": {
                    "0": {"description": "Detailed numbered steps with tools, safety, measurements, logical sequence", "points": 20},
                    "1": {"description": "Steps listed but missing tool callouts or measurements", "points": 14},
                    "2": {"description": "Vague steps, missing operations, unclear sequence", "points": 8},
                    "3": {"description": "No procedure or not submitted", "points": 0},
                }
            },
            "2": {
                "description": "Materials & Tools List",
                "points": 10,
                "ratings": {
                    "0": {"description": "Complete list: material type, dimensions, quantity, all tools identified", "points": 10},
                    "1": {"description": "Most items listed, minor omissions", "points": 7},
                    "2": {"description": "Incomplete, missing key items", "points": 4},
                    "3": {"description": "No list", "points": 0},
                }
            },
            "3": {
                "description": "Reflection & Writing Quality",
                "points": 10,
                "ratings": {
                    "0": {"description": "Thoughtful reflection on process, clear professional writing", "points": 10},
                    "1": {"description": "Some reflection, adequate writing", "points": 7},
                    "2": {"description": "Minimal reflection, unclear writing", "points": 4},
                    "3": {"description": "No reflection or unreadable", "points": 0},
                }
            },
        }
    },
    "Campus Handrail Plaque - Design & Fabrication": {
        "title": "Campus Handrail Plaque — Design & Fabrication Rubric",
        "criteria": {
            "0": {
                "description": "Design Quality",
                "points": 15,
                "ratings": {
                    "0": {"description": "Original, clean layout, appropriate for permanent installation, sketch included", "points": 15},
                    "1": {"description": "Functional, mostly clean, minor issues", "points": 10},
                    "2": {"description": "Basic, lacks refinement for permanent display", "points": 6},
                    "3": {"description": "No design work or not submitted", "points": 0},
                }
            },
            "1": {
                "description": "Fabrication Execution",
                "points": 25,
                "ratings": {
                    "0": {"description": "Clean cuts, smooth edges, accurate dimensions, strong clean welds, professional finish", "points": 25},
                    "1": {"description": "Good with minor flaws (small gaps, slight errors, acceptable welds)", "points": 18},
                    "2": {"description": "Rough, visible errors, weak joints, needs rework", "points": 10},
                    "3": {"description": "Incomplete or not submitted", "points": 0},
                }
            },
            "2": {
                "description": "Surface Finish & Presentation",
                "points": 15,
                "ratings": {
                    "0": {"description": "Deburred, cleaned, finished (paint/clear/polish), installation-ready", "points": 15},
                    "1": {"description": "Mostly finished, minor burrs or uneven coating", "points": 10},
                    "2": {"description": "Rough finish, visible burrs, incomplete", "points": 6},
                    "3": {"description": "No finishing attempted", "points": 0},
                }
            },
            "3": {
                "description": "Documentation (Photos + Process Notes)",
                "points": 15,
                "ratings": {
                    "0": {"description": "Progress photos at key stages, final shots, process notes", "points": 15},
                    "1": {"description": "Some photos, minimal notes", "points": 10},
                    "2": {"description": "One photo or no documentation", "points": 6},
                    "3": {"description": "Nothing submitted", "points": 0},
                }
            },
        }
    },
    "Metal Entrepreneur Challenge": {
        "title": "Metal Entrepreneur Challenge Rubric",
        "criteria": {
            "0": {
                "description": "Need Identification & Market Research",
                "points": 15,
                "ratings": {
                    "0": {"description": "Real need with evidence, target market defined, competition researched", "points": 15},
                    "1": {"description": "Need identified, thin evidence, some awareness", "points": 10},
                    "2": {"description": "Vague need, no evidence", "points": 6},
                    "3": {"description": "Missing", "points": 0},
                }
            },
            "1": {
                "description": "Design & Engineering",
                "points": 20,
                "ratings": {
                    "0": {"description": "Sketch/CAD, material justified, dimensions right, iterates on feedback", "points": 20},
                    "1": {"description": "Functional design, some docs, reasonable material", "points": 14},
                    "2": {"description": "Basic, minimal docs, unjustified material", "points": 8},
                    "3": {"description": "No design docs", "points": 0},
                }
            },
            "2": {
                "description": "Fabrication Quality",
                "points": 25,
                "ratings": {
                    "0": {"description": "Professional quality, clean welds/joints, customer-ready", "points": 25},
                    "1": {"description": "Good, minor imperfections, sellable", "points": 18},
                    "2": {"description": "Rough, visible flaws, needs rework", "points": 10},
                    "3": {"description": "Incomplete", "points": 0},
                }
            },
            "3": {
                "description": "Pricing & Business Case",
                "points": 20,
                "ratings": {
                    "0": {"description": "Material cost, labor tracked, overhead, profit margin, competitive price", "points": 20},
                    "1": {"description": "Material estimated, some tracking, price set", "points": 14},
                    "2": {"description": "Guessed pricing, no breakdown", "points": 8},
                    "3": {"description": "No pricing", "points": 0},
                }
            },
            "4": {
                "description": "Sale & Customer Interaction",
                "points": 20,
                "ratings": {
                    "0": {"description": "Sold to real customer, documented, feedback collected", "points": 20},
                    "1": {"description": "Customer pitched, sale pending or undocumented", "points": 14},
                    "2": {"description": "No real customer, hypothetical only", "points": 8},
                    "3": {"description": "No sale attempt", "points": 0},
                }
            },
        }
    },
}


def create_rubrics():
    url, token = get_creds()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    for cid in METALS_COURSE_IDS:
        # Get course name
        r = requests.get(f"{url}/api/v1/courses/{cid}", headers=headers)
        cname = r.json().get("name", f"Course {cid}")
        print(f"\n{'═' * 60}")
        print(f"  {cname} (ID: {cid})")
        print(f"{'═' * 60}")

        # Get assignments to find IDs
        assignments = {}
        page_url = f"{url}/api/v1/courses/{cid}/assignments?per_page=50"
        while page_url:
            r = requests.get(page_url, headers=headers)
            for a in r.json():
                assignments[a["name"]] = a
            # Pagination
            links = r.headers.get("Link", "")
            page_url = None
            for link in links.split(","):
                if 'rel="next"' in link:
                    page_url = link.split("<")[1].split(">")[0]

        for asgn_name, rubric_def in RUBRICS.items():
            if asgn_name not in assignments:
                print(f"  ⚠ Assignment not found: {asgn_name}")
                continue

            asgn = assignments[asgn_name]
            asgn_id = asgn["id"]

            # Check if rubric already exists
            if asgn.get("rubric"):
                print(f"  SKIP (rubric exists): {asgn_name}")
                continue

            # Create rubric via REST API
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
                }
            }

            r = requests.post(
                f"{url}/api/v1/courses/{cid}/rubrics",
                headers=headers,
                json=payload,
            )

            if r.status_code in (200, 201):
                print(f"  CREATED rubric: {rubric_def['title']}")
            else:
                print(f"  ⚠ Failed ({r.status_code}): {asgn_name}")
                # Try to get more error info
                try:
                    err = r.json()
                    print(f"    Error: {json.dumps(err, indent=2)[:300]}")
                except Exception:
                    print(f"    Response: {r.text[:300]}")


def create_delayed_announcements():
    """Create announcements with a delayed post date (future) so they don't go live immediately."""
    url, token = get_creds()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    announcement_html = """<p>Team —</p>
<p>Two things to take care of this week:</p>
<h3 style="color:#c0392b;">1. Missing Assignments</h3>
<p>Several of you have missing submissions. Check your Canvas grades and get caught up:</p>
<ul>
<li><strong>Portable Tool Organizer — SolidWorks</strong> (was due 2/12)</li>
<li><strong>Sheet Metal Cell Phone Stand — POP Writeup</strong> (was due 2/19)</li>
<li><strong>Campus Handrail Plaque</strong> (was due 2/20)</li>
</ul>
<p>Get these submitted. Late is better than missing.</p>
<h3 style="color:#2c3e50;">2. Metal Types Quiz — Due Thursday 2/26</h3>
<p>Our first unit quiz drops <strong>Tuesday morning (2/24)</strong> and is due by <strong>Thursday night (2/26) at 11:59 PM</strong>.</p>
<ul>
<li>25 multiple-choice questions, 25 points</li>
<li>30-minute time limit</li>
<li><strong>2 attempts</strong> — highest score kept</li>
<li>Covers: ferrous vs. non-ferrous, metal identification, 9 metals, MIG welding, lathe, and milling</li>
</ul>
<p>Review the <strong>Metal Types Study Guide</strong> page in Canvas before you take it.</p>
<p>— Mr. McAteer</p>"""

    for cid in METALS_COURSE_IDS:
        r = requests.get(f"{url}/api/v1/courses/{cid}", headers=headers)
        cname = r.json().get("name", f"Course {cid}")

        payload = {
            "title": "Missing Assignments + Metal Types Quiz This Thursday",
            "message": announcement_html,
            "is_announcement": True,
            "published": True,
            "delayed_post_at": "2026-02-24T14:00:00Z",  # Mon 2/24 6am PT
        }

        r = requests.post(
            f"{url}/api/v1/courses/{cid}/discussion_topics",
            headers=headers,
            json=payload,
        )

        if r.status_code in (200, 201):
            print(f"  CREATED delayed announcement: {cname} (posts Mon 2/24 6am PT)")
        else:
            print(f"  ⚠ Announcement failed for {cname}: {r.status_code}")
            try:
                print(f"    {r.json()}")
            except Exception:
                print(f"    {r.text[:200]}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--rubrics", action="store_true")
    parser.add_argument("--announcements", action="store_true")
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()

    if args.rubrics or args.all:
        create_rubrics()
    if args.announcements or args.all:
        create_delayed_announcements()
    if not (args.rubrics or args.announcements or args.all):
        parser.print_help()
