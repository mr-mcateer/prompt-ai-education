#!/usr/bin/env python3
"""
Create weekly Thursday cleanup assignments + one Deep Clean Monday for metals courses.

Strategy:
  - Semester 2: Feb 2 → June 11, 2026
  - Spring break: March 23-27 (no cleanup that week)
  - Weekly Thursday cleanup: 10 pts each, Citizenship & Safety group
  - One Deep Clean Monday: 20 pts, Citizenship & Safety group
  - All new assignments created UNPUBLISHED
  - Fix existing cleanup assignments (wrong group, inconsistent descriptions)
  - Add all to Module 5 — Shop Citizenship

Usage:
  python3 canvas_metals_cleanup.py --dry-run     # Preview
  python3 canvas_metals_cleanup.py --deploy       # Create everything
  python3 canvas_metals_cleanup.py --publish-past # Publish cleanups whose due date has passed
"""

import os
import sys
import requests
import json
import argparse

METALS_COURSE_IDS = [23164, 23132, 23157, 23188, 23177]


def get_creds():
    url = os.environ.get("CANVAS_API_URL")
    token = os.environ.get("CANVAS_API_TOKEN")
    if not url or not token:
        print("ERROR: Set CANVAS_API_URL and CANVAS_API_TOKEN")
        sys.exit(1)
    return url, token


def paginated_get(url, headers, params=None):
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


# ── Cleanup description HTML ──────────────────────────────────

WEEKLY_CLEANUP_DESC = """<div style="max-width:700px;font-family:inherit;">

<div style="background-color:#fef9e7;border-left:4px solid #f39c12;padding:15px 20px;margin-bottom:16px;">
  <p style="margin:0 0 4px 0;font-size:16px;"><strong>Weekly Shop Cleanup</strong></p>
  <p style="margin:0;font-size:14px;line-height:1.6;color:#444;">Every Thursday, last 15 minutes of class. The shop should look better than when you found it.</p>
</div>

<p style="font-size:14px;line-height:1.7;"><strong>Your checklist:</strong></p>
<ul style="font-size:14px;line-height:1.8;color:#333;">
  <li><strong>Your workstation</strong> &mdash; Wipe down surfaces, return all tools to their homes, sweep your area</li>
  <li><strong>Machines you used</strong> &mdash; Clean chips and debris, wipe surfaces, organize tooling</li>
  <li><strong>Floor around you</strong> &mdash; Sweep metal shavings, mop any oil or coolant, clear walkways</li>
  <li><strong>Scrap &amp; trash</strong> &mdash; Metal scraps in the scrap bin, trash in the trash can, rags in the rag bin</li>
  <li><strong>Safety gear</strong> &mdash; Wipe down safety glasses, hang aprons, check your area is clear</li>
</ul>

<div style="background-color:#f0f4f8;border-left:4px solid #2c3e50;padding:12px 16px;margin:15px 0;">
  <p style="margin:0;font-size:14px;"><strong>How this is graded (10 pts):</strong></p>
  <ul style="font-size:13px;line-height:1.7;color:#333;margin:6px 0 0 0;">
    <li><strong>Effort (4 pts)</strong> &mdash; You stayed busy the full 15 minutes, found tasks without being told</li>
    <li><strong>Quality (4 pts)</strong> &mdash; Your area is actually clean, not just moved around</li>
    <li><strong>Attitude (2 pts)</strong> &mdash; No phone, no standing around, helped others when your area was done</li>
  </ul>
</div>

<p style="font-size:13px;color:#666;">This is part of your <strong>Citizenship &amp; Safety</strong> grade (25% of your overall grade). Showing up and going through the motions gets you a 6. Doing it right gets you a 10.</p>

</div>"""

DEEP_CLEAN_DESC = """<div style="max-width:700px;font-family:inherit;">

<div style="background-color:#fdf2f2;border-left:4px solid #c0392b;padding:15px 20px;margin-bottom:16px;">
  <p style="margin:0 0 4px 0;font-size:16px;"><strong>Deep Clean Day</strong></p>
  <p style="margin:0;font-size:14px;line-height:1.6;color:#444;">This is not a regular Thursday cleanup. This is a full-period, top-to-bottom shop restoration. Every surface, every machine, every drawer, every corner.</p>
</div>

<p style="font-size:14px;line-height:1.7;"><strong>Today we take it to the extreme.</strong> The shop should look like it did on the first day of school &mdash; or better.</p>

<p style="font-size:14px;line-height:1.7;"><strong>Deep clean stations (assigned by Mr. McAteer):</strong></p>
<ul style="font-size:14px;line-height:1.8;color:#333;">
  <li><strong>Welding bays</strong> &mdash; Scrub tables, clean curtains, organize filler rod, empty slag bins, wipe machines, restock gloves and tips</li>
  <li><strong>Machine surfaces</strong> &mdash; Degrease lathe beds, mill tables, bandsaw tables. Clean chip trays. Organize tooling drawers</li>
  <li><strong>Tool storage</strong> &mdash; Every tool in its home. Shadow boards complete. Broken or missing tools reported. Drawers organized</li>
  <li><strong>Floor &mdash; all of it</strong> &mdash; Sweep everything. Mop oily areas with Simple Green. Under machines, behind equipment, corners</li>
  <li><strong>Safety stations</strong> &mdash; Clean safety glasses, check fire extinguisher access, clear eyewash area, restock first aid supplies</li>
  <li><strong>Supply restock</strong> &mdash; Refill shop towels, Simple Green bottles, replace worn rags, restock consumables at each station</li>
  <li><strong>Scrap &amp; waste</strong> &mdash; Sort scrap by metal type, empty all trash cans, replace liners, check waste oil container level</li>
  <li><strong>Walls &amp; windows</strong> &mdash; Wipe down light switches, clean windows, remove tape and old signs, dust shelves</li>
</ul>

<div style="background-color:#e8f4e8;border-left:4px solid #27ae60;padding:12px 16px;margin:15px 0;">
  <p style="margin:0;font-size:14px;"><strong>What I am looking for (20 pts):</strong></p>
  <ul style="font-size:13px;line-height:1.7;color:#333;margin:6px 0 0 0;">
    <li><strong>Initiative (6 pts)</strong> &mdash; You find work without being told. When one station is done, you move to the next. You don&rsquo;t stop until the bell</li>
    <li><strong>Thoroughness (6 pts)</strong> &mdash; Surfaces are actually clean. Drawers are actually organized. You did it right, not just fast</li>
    <li><strong>Teamwork (4 pts)</strong> &mdash; You helped others, shared supplies, communicated about what still needed doing</li>
    <li><strong>Professional attitude (4 pts)</strong> &mdash; No phone, no complaints, no standing around. This is what a real shop looks like at close</li>
  </ul>
</div>

<p style="font-size:13px;color:#666;">This is part of your <strong>Citizenship &amp; Safety</strong> grade. Treat the shop like it&rsquo;s yours &mdash; because it is.</p>

</div>"""


# ── Schedule ──────────────────────────────────────────────────
# All Thursdays in Semester 2 (Feb 2 → Jun 11, 2026)
# Due at 11:59 PM Pacific (PST before Mar 8 = UTC-8, PDT after = UTC-7)
# Spring break: Mar 23-27 → skip that Thursday (3/26)

WEEKLY_CLEANUPS = [
    # (name, due_at_utc)
    # PST = UTC-8 → 11:59 PM = 07:59 next day
    # PDT = UTC-7 → 11:59 PM = 06:59 next day
    ("Shop Cleanup \u2014 Thursday 2/5",   "2026-02-06T07:59:59Z"),
    ("Shop Cleanup \u2014 Thursday 2/12",  "2026-02-13T07:59:59Z"),
    ("Shop Cleanup \u2014 Thursday 2/19",  "2026-02-20T07:59:59Z"),
    ("Shop Cleanup \u2014 Thursday 2/26",  "2026-02-27T07:59:59Z"),
    ("Shop Cleanup \u2014 Thursday 3/5",   "2026-03-06T07:59:59Z"),
    ("Shop Cleanup \u2014 Thursday 3/12",  "2026-03-13T07:59:59Z"),
    ("Shop Cleanup \u2014 Thursday 3/19",  "2026-03-20T07:59:59Z"),
    # Mar 26 = spring break — SKIP
    ("Shop Cleanup \u2014 Thursday 4/2",   "2026-04-03T06:59:59Z"),  # PDT
    ("Shop Cleanup \u2014 Thursday 4/9",   "2026-04-10T06:59:59Z"),
    ("Shop Cleanup \u2014 Thursday 4/16",  "2026-04-17T06:59:59Z"),
    ("Shop Cleanup \u2014 Thursday 4/23",  "2026-04-24T06:59:59Z"),
    ("Shop Cleanup \u2014 Thursday 4/30",  "2026-05-01T06:59:59Z"),
    ("Shop Cleanup \u2014 Thursday 5/7",   "2026-05-08T06:59:59Z"),
    ("Shop Cleanup \u2014 Thursday 5/14",  "2026-05-15T06:59:59Z"),
    ("Shop Cleanup \u2014 Thursday 5/21",  "2026-05-22T06:59:59Z"),
    ("Shop Cleanup \u2014 Thursday 5/28",  "2026-05-29T06:59:59Z"),
    ("Shop Cleanup \u2014 Thursday 6/4",   "2026-06-05T06:59:59Z"),
    ("Shop Cleanup \u2014 Thursday 6/11",  "2026-06-12T06:59:59Z"),
]

# Deep Clean Monday — after spring break, fresh start
DEEP_CLEAN = (
    "Deep Clean Day \u2014 Monday 3/30",
    "2026-03-31T06:59:59Z",  # Mon 3/30 at 11:59 PM PDT
)


def get_citizenship_group_id(url, headers, cid):
    """Find the Citizenship & Safety assignment group ID."""
    groups = paginated_get(
        f"{url}/api/v1/courses/{cid}/assignment_groups", headers, {"per_page": "50"}
    )
    for g in groups:
        if "citizenship" in g["name"].lower() or "safety" in g["name"].lower():
            return g["id"]
    return None


def get_module5_id(url, headers, cid):
    """Find Module 5 — Shop Citizenship."""
    modules = paginated_get(
        f"{url}/api/v1/courses/{cid}/modules", headers, {"per_page": "50"}
    )
    for m in modules:
        if "citizenship" in m["name"].lower() or ("5" in m["name"] and "shop" in m["name"].lower()):
            return m["id"]
    return None


def find_existing(existing, name):
    """Find an assignment by name, checking em dash variants."""
    if name in existing:
        return existing[name]
    # Canvas might store em dashes differently
    for ename, a in existing.items():
        if ename.replace("\u2014", "-") == name.replace("\u2014", "-"):
            return a
    return None


# Map old (wrong) cleanup names to the correct new name
RENAME_MAP = {
    "Shop Cleanup \u2014 Thursday 2/13": "Shop Cleanup \u2014 Thursday 2/12",
    "Shop Cleanup — Thursday 2/13":      "Shop Cleanup \u2014 Thursday 2/12",
}


def deploy(dry_run=False):
    url, token = get_creds()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    total_created = 0
    total_fixed = 0
    total_skipped = 0

    for cid in METALS_COURSE_IDS:
        r = requests.get(f"{url}/api/v1/courses/{cid}", headers=headers)
        cname = r.json().get("name", f"Course {cid}")
        print(f"\n{'═' * 65}")
        print(f"  {'DRY RUN — ' if dry_run else ''}{cname} (ID: {cid})")
        print(f"{'═' * 65}")

        # Get existing assignments
        existing = {}
        for a in paginated_get(f"{url}/api/v1/courses/{cid}/assignments", headers, {"per_page": "50"}):
            existing[a["name"]] = a

        cit_group_id = get_citizenship_group_id(url, headers, cid)
        mod5_id = get_module5_id(url, headers, cid)

        if not cit_group_id:
            print("  ERROR: Citizenship & Safety group not found!")
            continue
        if not mod5_id:
            print("  ERROR: Module 5 not found!")
            continue

        print(f"  Citizenship group: {cit_group_id}, Module 5: {mod5_id}")

        # Get items already in Module 5
        mod5_content_ids = set()
        mod5_items = paginated_get(
            f"{url}/api/v1/courses/{cid}/modules/{mod5_id}/items", headers, {"per_page": "50"}
        )
        for item in mod5_items:
            if item.get("content_id"):
                mod5_content_ids.add(item["content_id"])

        # ── Fix existing cleanup assignments that have wrong names ──
        for old_name, new_name in RENAME_MAP.items():
            if old_name in existing:
                a = existing[old_name]
                # Find the correct due date from our schedule
                target_due = None
                for sched_name, sched_due in WEEKLY_CLEANUPS:
                    if sched_name == new_name:
                        target_due = sched_due
                        break

                fixes = {"name": new_name}
                if target_due:
                    fixes["due_at"] = target_due
                if a.get("assignment_group_id") != cit_group_id:
                    fixes["assignment_group_id"] = cit_group_id
                fixes["description"] = WEEKLY_CLEANUP_DESC
                fixes["points_possible"] = 10
                fixes["submission_types"] = ["online_text_entry"]

                if dry_run:
                    print(f"  WOULD RENAME+FIX: '{old_name}' → '{new_name}'")
                else:
                    r = requests.put(
                        f"{url}/api/v1/courses/{cid}/assignments/{a['id']}",
                        headers=headers,
                        json={"assignment": fixes},
                    )
                    if r.status_code == 200:
                        print(f"  RENAMED+FIXED: '{old_name}' → '{new_name}'")
                        total_fixed += 1
                    else:
                        print(f"  FAIL renaming '{old_name}': {r.status_code}")

                # Track that this target name is now handled
                existing[new_name] = a
                del existing[old_name]

        # ── Fix existing 2/19 cleanup (correct name, but wrong group/desc) ──
        for name_variant in ["Shop Cleanup \u2014 Thursday 2/19", "Shop Cleanup — Thursday 2/19"]:
            if name_variant in existing:
                a = existing[name_variant]
                target_name = "Shop Cleanup \u2014 Thursday 2/19"
                fixes = {}
                if a.get("assignment_group_id") != cit_group_id:
                    fixes["assignment_group_id"] = cit_group_id
                if a.get("points_possible") != 10:
                    fixes["points_possible"] = 10
                if len(a.get("description", "")) < 200:
                    fixes["description"] = WEEKLY_CLEANUP_DESC
                if a.get("name") != target_name:
                    fixes["name"] = target_name
                sub_types = a.get("submission_types", [])
                if sub_types != ["online_text_entry"]:
                    fixes["submission_types"] = ["online_text_entry"]
                # Fix due date
                if a.get("due_at") != "2026-02-20T07:59:59Z":
                    fixes["due_at"] = "2026-02-20T07:59:59Z"

                if fixes:
                    if dry_run:
                        print(f"  WOULD FIX: {name_variant} → {list(fixes.keys())}")
                    else:
                        r = requests.put(
                            f"{url}/api/v1/courses/{cid}/assignments/{a['id']}",
                            headers=headers,
                            json={"assignment": fixes},
                        )
                        if r.status_code == 200:
                            print(f"  FIXED: {name_variant}")
                            total_fixed += 1
                        else:
                            print(f"  FAIL fixing {name_variant}: {r.status_code}")
                # Track as handled
                existing["Shop Cleanup \u2014 Thursday 2/19"] = a
                break

        # ── Create weekly cleanups (skip any that already exist) ──
        for asgn_name, due_at in WEEKLY_CLEANUPS:
            if find_existing(existing, asgn_name):
                print(f"  SKIP (exists): {asgn_name}")
                total_skipped += 1
                continue

            if dry_run:
                print(f"  WOULD CREATE: {asgn_name} (10 pts, due {due_at})")
                continue

            payload = {
                "assignment": {
                    "name": asgn_name,
                    "description": WEEKLY_CLEANUP_DESC,
                    "points_possible": 10,
                    "due_at": due_at,
                    "assignment_group_id": cit_group_id,
                    "submission_types": ["online_text_entry"],
                    "published": False,
                    "grading_type": "points",
                }
            }

            r = requests.post(
                f"{url}/api/v1/courses/{cid}/assignments",
                headers=headers,
                json=payload,
            )

            if r.status_code in (200, 201):
                new_id = r.json()["id"]
                print(f"  CREATED: {asgn_name} (id: {new_id})")
                total_created += 1

                # Add to Module 5 if not already there
                if new_id not in mod5_content_ids:
                    r2 = requests.post(
                        f"{url}/api/v1/courses/{cid}/modules/{mod5_id}/items",
                        headers=headers,
                        json={"module_item": {"type": "Assignment", "content_id": new_id}},
                    )
                    if r2.status_code not in (200, 201):
                        print(f"    ⚠ Failed to add to Module 5: {r2.status_code}")
            else:
                print(f"  FAIL ({r.status_code}): {asgn_name}")

        # ── Create deep clean day ─────────────────────────────
        dc_name, dc_due = DEEP_CLEAN
        if find_existing(existing, dc_name):
            print(f"  SKIP (exists): {dc_name}")
        elif dry_run:
            print(f"  WOULD CREATE: {dc_name} (20 pts, due {dc_due})")
        else:
            payload = {
                "assignment": {
                    "name": dc_name,
                    "description": DEEP_CLEAN_DESC,
                    "points_possible": 20,
                    "due_at": dc_due,
                    "assignment_group_id": cit_group_id,
                    "submission_types": ["online_text_entry"],
                    "published": False,
                    "grading_type": "points",
                }
            }

            r = requests.post(
                f"{url}/api/v1/courses/{cid}/assignments",
                headers=headers,
                json=payload,
            )

            if r.status_code in (200, 201):
                new_id = r.json()["id"]
                print(f"  CREATED: {dc_name} (id: {new_id})")
                total_created += 1

                if new_id not in mod5_content_ids:
                    r2 = requests.post(
                        f"{url}/api/v1/courses/{cid}/modules/{mod5_id}/items",
                        headers=headers,
                        json={"module_item": {"type": "Assignment", "content_id": new_id}},
                    )
                    if r2.status_code not in (200, 201):
                        print(f"    ⚠ Failed to add to Module 5: {r2.status_code}")
            else:
                print(f"  FAIL ({r.status_code}): {dc_name}")

    print(f"\n{'═' * 65}")
    print(f"  SUMMARY: Created {total_created}, Fixed {total_fixed}, Skipped {total_skipped}")
    print(f"{'═' * 65}\n")


def publish_past():
    """Publish cleanup assignments whose due date has already passed."""
    from datetime import datetime, timezone
    url, token = get_creds()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    now = datetime.now(timezone.utc)

    published = 0
    for cid in METALS_COURSE_IDS:
        r = requests.get(f"{url}/api/v1/courses/{cid}", headers=headers)
        cname = r.json().get("name", f"Course {cid}")
        print(f"\n  {cname} (ID: {cid})")

        for a in paginated_get(f"{url}/api/v1/courses/{cid}/assignments", headers, {"per_page": "50"}):
            name = a["name"]
            if "cleanup" not in name.lower() and "deep clean" not in name.lower():
                continue
            if a.get("published"):
                continue
            due = a.get("due_at")
            if not due:
                continue
            due_dt = datetime.fromisoformat(due.replace("Z", "+00:00"))
            if due_dt < now:
                r = requests.put(
                    f"{url}/api/v1/courses/{cid}/assignments/{a['id']}",
                    headers=headers,
                    json={"assignment": {"published": True}},
                )
                if r.status_code == 200:
                    print(f"    PUBLISHED: {name}")
                    published += 1
                else:
                    print(f"    FAIL: {name} ({r.status_code})")

    print(f"\n  Published {published} past-due cleanup assignments.\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Manage metals cleanup assignments")
    parser.add_argument("--dry-run", action="store_true", help="Preview without changes")
    parser.add_argument("--deploy", action="store_true", help="Create all cleanup assignments")
    parser.add_argument("--publish-past", action="store_true", help="Publish cleanups with past due dates")
    args = parser.parse_args()

    if args.dry_run:
        deploy(dry_run=True)
    elif args.deploy:
        deploy(dry_run=False)
    elif args.publish_past:
        publish_past()
    else:
        parser.print_help()
