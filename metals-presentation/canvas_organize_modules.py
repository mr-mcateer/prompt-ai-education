#!/usr/bin/env python3
"""
Organize Canvas modules using best-practice instructional design.

Design philosophy:
  - Modules tell a story of PROGRESSION, not just categories
  - Names communicate what students WILL BE ABLE TO DO
  - Sequence mirrors the actual shop experience:
      Get certified → Learn your materials → Build with increasing complexity → Go pro
  - Every assignment lives inside a module so students see ONE linear path
  - Existing modules (Safety Tests, Shop Maintenance) are renamed/repositioned, not duplicated

Everything is created UNPUBLISHED so the instructor can review before going live.
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


# ══════════════════════════════════════════════════════════════
# MODULE BLUEPRINT
# ══════════════════════════════════════════════════════════════
# Each module is defined in SEQUENCE (position matters).
# "items" are assignment/quiz/page names that should be added.
# "type" tells us what kind of Canvas item to look for.
#
# The design follows Understanding by Design (UbD) / backward design:
#   Module 1: Safety gates (must pass before touching equipment)
#   Module 2: Material knowledge (builds vocabulary + ID skills)
#   Module 3: Foundational fabrication (first real builds)
#   Module 4: Capstone (integrate everything into a professional product)
#   Module 5: Ongoing citizenship (daily expectations)

MODULE_BLUEPRINT = [
    {
        "name": "1 — Shop Safety Certifications",
        "position": 1,
        "require_sequential_progress": True,
        "published": False,
        "rename_from": "Safety Tests",  # Rename existing module instead of creating new
        "items": [
            # These already exist in the Safety Tests module — they'll stay
            {"title": "General Shop Safety", "type": "assignment"},
            {"title": "Portable Angle Grinder Safety", "type": "assignment"},
            {"title": "Abrasive Cutoff Saw", "type": "assignment"},
            {"title": "Arc Welding", "type": "assignment"},
            {"title": "Metal Bandsaw", "type": "assignment"},
        ],
        "completion_requirements": {
            "General Shop Safety": {"type": "min_score", "min_score": 15},
            "Portable Angle Grinder Safety": {"type": "must_submit"},
            "Abrasive Cutoff Saw": {"type": "must_submit"},
            "Arc Welding": {"type": "must_submit"},
            "Metal Bandsaw": {"type": "must_submit"},
        },
    },
    {
        "name": "2 — Know Your Metals",
        "position": 2,
        "require_sequential_progress": False,
        "published": False,
        "items": [
            {"title": "Metal Types — Study Guide", "type": "page"},
            {"title": "Metal Types — Unit Quiz", "type": "assignment"},
        ],
    },
    {
        "name": "3 — Design & Build",
        "position": 3,
        "require_sequential_progress": False,
        "published": False,
        "items": [
            {"title": "Portable Tool Organizer - SolidWorks", "type": "assignment"},
            {"title": "Sheet Metal Cell Phone Stand - POP Writeup", "type": "assignment"},
            {"title": "Campus Handrail Plaque - Design & Fabrication", "type": "assignment"},
        ],
    },
    {
        "name": "4 — Metal Entrepreneur Challenge",
        "position": 4,
        "require_sequential_progress": False,
        "published": False,
        "items": [
            {"title": "Metal Entrepreneur Challenge", "type": "assignment"},
        ],
    },
    {
        "name": "5 — Shop Citizenship",
        "position": 5,
        "require_sequential_progress": False,
        "published": False,
        "rename_from": "Shop Maintenance",  # Rename existing module
        "items": [
            {"title": "Thursday Cleanup - Week 1", "type": "assignment"},
            {"title": "Thursday Cleanup - Week 2", "type": "assignment"},
            {"title": "Thursday Cleanup - Week 3", "type": "assignment"},
            {"title": "Thursday Cleanup - Week 4", "type": "assignment"},
            {"title": "Thursday Cleanup - Week 5", "type": "assignment"},
            {"title": "Thursday Cleanup - Week 6", "type": "assignment"},
        ],
    },
]


def paginated_get(url, headers, params=None):
    """GET with Canvas pagination support."""
    results = []
    page_url = url
    while page_url:
        r = requests.get(page_url, headers=headers, params=params)
        r.raise_for_status()
        results.extend(r.json())
        # Parse Link header for next page
        links = r.headers.get("Link", "")
        page_url = None
        for link in links.split(","):
            if 'rel="next"' in link:
                page_url = link.split("<")[1].split(">")[0]
        params = None  # params are in the URL for subsequent pages
    return results


def organize_modules(dry_run=False):
    url, token = get_creds()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    for cid in METALS_COURSE_IDS:
        # Get course name
        r = requests.get(f"{url}/api/v1/courses/{cid}", headers=headers)
        cname = r.json().get("name", f"Course {cid}")
        print(f"\n{'═' * 70}")
        print(f"  {cname} (ID: {cid})")
        print(f"{'═' * 70}")

        # ── Gather existing data ─────────────────────────────────
        # Get all assignments (for looking up IDs)
        assignments = {}
        for a in paginated_get(f"{url}/api/v1/courses/{cid}/assignments", headers, {"per_page": "50"}):
            assignments[a["name"]] = a

        # Get all pages (for looking up page URLs)
        pages = {}
        for p in paginated_get(f"{url}/api/v1/courses/{cid}/pages", headers, {"per_page": "50"}):
            pages[p["title"]] = p

        # Get existing modules with their items
        existing_modules = {}
        for m in paginated_get(f"{url}/api/v1/courses/{cid}/modules", headers, {"per_page": "50", "include[]": "items"}):
            existing_modules[m["name"]] = m

        # Track which assignment IDs are already in a module (to avoid duplicates)
        items_already_in_modules = set()
        for m in existing_modules.values():
            for item in m.get("items", []):
                content_id = item.get("content_id")
                if content_id:
                    items_already_in_modules.add(content_id)

        print(f"  Found {len(assignments)} assignments, {len(pages)} pages, {len(existing_modules)} existing modules")

        # ── Process each module in the blueprint ─────────────────
        for blueprint in MODULE_BLUEPRINT:
            bp_name = blueprint["name"]
            rename_from = blueprint.get("rename_from")
            module_id = None

            # Check if module already exists (by new name)
            if bp_name in existing_modules:
                module_id = existing_modules[bp_name]["id"]
                print(f"\n  MODULE EXISTS: {bp_name}")

            # Check if we should rename an existing module
            elif rename_from and rename_from in existing_modules:
                old_module = existing_modules[rename_from]
                module_id = old_module["id"]
                if dry_run:
                    print(f"\n  [DRY RUN] WOULD RENAME: '{rename_from}' → '{bp_name}'")
                else:
                    r = requests.put(
                        f"{url}/api/v1/courses/{cid}/modules/{module_id}",
                        headers=headers,
                        json={"module": {
                            "name": bp_name,
                            "position": blueprint["position"],
                            "require_sequential_progress": blueprint.get("require_sequential_progress", False),
                        }},
                    )
                    if r.status_code == 200:
                        print(f"\n  RENAMED: '{rename_from}' → '{bp_name}' (position {blueprint['position']})")
                    else:
                        print(f"\n  ⚠ Failed to rename '{rename_from}': {r.status_code}")
                        try:
                            print(f"    {r.json()}")
                        except Exception:
                            pass

            # Create new module
            else:
                if dry_run:
                    print(f"\n  [DRY RUN] WOULD CREATE MODULE: {bp_name}")
                else:
                    r = requests.post(
                        f"{url}/api/v1/courses/{cid}/modules",
                        headers=headers,
                        json={"module": {
                            "name": bp_name,
                            "position": blueprint["position"],
                            "require_sequential_progress": blueprint.get("require_sequential_progress", False),
                            "published": blueprint.get("published", False),
                        }},
                    )
                    if r.status_code in (200, 201):
                        module_id = r.json()["id"]
                        print(f"\n  CREATED MODULE: {bp_name} (position {blueprint['position']})")
                    else:
                        print(f"\n  ⚠ Failed to create module '{bp_name}': {r.status_code}")
                        try:
                            print(f"    {r.json()}")
                        except Exception:
                            pass
                        continue

            if dry_run:
                for item in blueprint["items"]:
                    print(f"    [DRY RUN] Would add: [{item['type']}] {item['title']}")
                continue

            if not module_id:
                continue

            # Get current items in this module
            current_items = paginated_get(
                f"{url}/api/v1/courses/{cid}/modules/{module_id}/items",
                headers, {"per_page": "50"}
            )
            current_item_content_ids = set()
            current_item_titles = set()
            for ci in current_items:
                if ci.get("content_id"):
                    current_item_content_ids.add(ci["content_id"])
                current_item_titles.add(ci.get("title", ""))

            # Add items that aren't already in this module
            for idx, item_spec in enumerate(blueprint["items"]):
                title = item_spec["title"]
                item_type = item_spec["type"]

                if item_type == "assignment":
                    if title not in assignments:
                        # Try fuzzy match for cleanup assignments
                        matched = False
                        for aname in assignments:
                            if title.lower() in aname.lower() or aname.lower() in title.lower():
                                title = aname
                                matched = True
                                break
                        if not matched:
                            print(f"    ⚠ Assignment not found: {title}")
                            continue

                    asgn = assignments[title]
                    asgn_id = asgn["id"]

                    # Skip if already in this module
                    if asgn_id in current_item_content_ids:
                        print(f"    SKIP (already in module): {title}")
                        continue

                    # Add to module
                    r = requests.post(
                        f"{url}/api/v1/courses/{cid}/modules/{module_id}/items",
                        headers=headers,
                        json={"module_item": {
                            "type": "Assignment",
                            "content_id": asgn_id,
                            "position": idx + 1,
                        }},
                    )
                    if r.status_code in (200, 201):
                        print(f"    ADDED: {title}")
                        new_item_id = r.json().get("id")

                        # Set completion requirements if specified
                        comp_reqs = blueprint.get("completion_requirements", {})
                        if title in comp_reqs and new_item_id:
                            req = comp_reqs[title]
                            r2 = requests.put(
                                f"{url}/api/v1/courses/{cid}/modules/{module_id}/items/{new_item_id}",
                                headers=headers,
                                json={"module_item": {"completion_requirement": req}},
                            )
                            if r2.status_code == 200:
                                print(f"           requirement: {req['type']}")
                            else:
                                print(f"           ⚠ requirement failed: {r2.status_code}")
                    else:
                        print(f"    ⚠ Failed to add {title}: {r.status_code}")
                        try:
                            print(f"      {r.json()}")
                        except Exception:
                            pass

                elif item_type == "page":
                    if title not in pages:
                        print(f"    ⚠ Page not found: {title} (create it first)")
                        continue

                    page = pages[title]
                    page_url_slug = page.get("url", "")

                    # Skip if already in module (check by title since pages don't have content_id the same way)
                    if title in current_item_titles:
                        print(f"    SKIP (already in module): {title}")
                        continue

                    r = requests.post(
                        f"{url}/api/v1/courses/{cid}/modules/{module_id}/items",
                        headers=headers,
                        json={"module_item": {
                            "type": "Page",
                            "page_url": page_url_slug,
                            "position": idx + 1,
                        }},
                    )
                    if r.status_code in (200, 201):
                        print(f"    ADDED: {title} (page)")
                    else:
                        print(f"    ⚠ Failed to add page {title}: {r.status_code}")
                        try:
                            print(f"      {r.json()}")
                        except Exception:
                            pass

        # ── Reorder modules to match blueprint positions ─────────
        # Refresh module list after changes
        updated_modules = paginated_get(
            f"{url}/api/v1/courses/{cid}/modules", headers, {"per_page": "50"}
        )
        bp_names = [bp["name"] for bp in MODULE_BLUEPRINT]
        for m in updated_modules:
            if m["name"] in bp_names:
                expected_pos = bp_names.index(m["name"]) + 1
                if m.get("position") != expected_pos:
                    if not dry_run:
                        requests.put(
                            f"{url}/api/v1/courses/{cid}/modules/{m['id']}",
                            headers=headers,
                            json={"module": {"position": expected_pos}},
                        )

        print(f"\n  ✓ Module organization complete for {cname}")

    # ── Summary ──────────────────────────────────────────────
    print(f"\n{'═' * 70}")
    print(f"  MODULE ORGANIZATION COMPLETE")
    print(f"{'═' * 70}")
    print(f"""
  Module structure (all 5 courses):

    1 — Shop Safety Certifications
        Sequential progress required. Students must pass General Shop
        Safety (100%) before unlocking machine-specific certifications.
        → General Shop Safety
        → Portable Angle Grinder Safety
        → Abrasive Cutoff Saw
        → Arc Welding
        → Metal Bandsaw

    2 — Know Your Metals
        Material science foundation. Study guide + unit quiz.
        → Metal Types — Study Guide (page)
        → Metal Types — Unit Quiz

    3 — Design & Build
        Progressive fabrication projects, each building new skills.
        → Portable Tool Organizer — SolidWorks (CAD)
        → Sheet Metal Cell Phone Stand — POP Writeup (planning + fabrication)
        → Campus Handrail Plaque — Design & Fabrication (real-world install)

    4 — Metal Entrepreneur Challenge
        Capstone: design, build, price, and sell a real product.
        → Metal Entrepreneur Challenge

    5 — Shop Citizenship
        Daily shop expectations and weekly cleanup accountability.
        → Thursday Cleanup weeks

  STATUS: All new modules are UNPUBLISHED.
  NEXT: Review in Canvas, then publish when ready.
""")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Organize Canvas modules for metals courses")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without making them")
    parser.add_argument("--deploy", action="store_true", help="Apply changes to all courses")
    args = parser.parse_args()

    if args.dry_run:
        print("DRY RUN — no changes will be made\n")
        organize_modules(dry_run=True)
    elif args.deploy:
        organize_modules(dry_run=False)
    else:
        parser.print_help()
