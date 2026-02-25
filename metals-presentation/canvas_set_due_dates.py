#!/usr/bin/env python3
"""
Set due dates for P1 Engines Fab courses.

Pacing strategy:
  - Semester 2: Feb 2 → June 11, 2026
  - Spring break: March 23-27 (no assignments due that week)
  - Consumer ed series: 1 assignment per week, Thursdays at 11:59 PM PT
  - Labs slot in between consumer ed assignments during shop weeks
  - Capstone (#16) due June 4 — one week buffer before semester end

Usage:
  python3 canvas_set_due_dates.py --dry-run     # Preview
  python3 canvas_set_due_dates.py --deploy       # Set all due dates
"""

import os
import sys
import requests
import json
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


# Due dates: Thursdays at 11:59 PM Pacific
# PST (pre-DST, before Mar 8) = UTC-8 → 07:59:59 UTC
# PDT (post-DST, Mar 8+)     = UTC-7 → 06:59:59 UTC
#
# Pacing:
#   Feb 23-27:  Finish engine reassembly (Predator 212 due 3/20)
#   Mar 2-6:    Oil change labs in shop
#   Mar 9-13:   Brake check / rotor turning labs in shop
#   Mar 16-20:  Lab wrap-up + consumer ed begins
#   Mar 23-27:  SPRING BREAK
#   Mar 30+:    Consumer ed series, 1-2 per week through June 8
#
DUE_DATES = {
    # ── Labs (Module 3) — done in shop first ──────────────
    "Oil Change Lab":                                                                 "2026-03-13T07:59:59Z",  # Thu 3/12 (oil change week)
    "Brake Check & Rotor Turning Lab":                                                "2026-03-20T07:59:59Z",  # Thu 3/19 (brake week)

    # ── Consumer Ed Series (Module 4) ──────────────────────
    # Starts after labs + spring break, 1-2 per week
    "01 \u2014 Your First Car Is Probably a Bad Deal":                                "2026-04-03T06:59:59Z",  # Thu 4/2 (first week back)
    "02 \u2014 Everything on the Sticker They Hope You Won\u2019t Read":              "2026-04-10T06:59:59Z",  # Thu 4/9
    "03 \u2014 The Most Expensive Room in the Dealership":                            "2026-04-17T06:59:59Z",  # Thu 4/16
    "04 \u2014 Insurance: You\u2019re Required to Buy It, You Should Understand It":  "2026-04-24T06:59:59Z",  # Thu 4/23
    "05 \u2014 The Car Payment Is the Smallest Part":                                 "2026-05-01T06:59:59Z",  # Thu 4/30
    "06 \u2014 Four Patches of Rubber Between You and the Road":                      "2026-05-01T06:59:59Z",  # Thu 4/30 (2 this week — shorter assignments)
    "07 \u2014 The 3,000-Mile Myth":                                                  "2026-05-08T06:59:59Z",  # Thu 5/7
    "08 \u2014 Trust, But Verify":                                                    "2026-05-08T06:59:59Z",  # Thu 5/7 (2 this week — shorter assignments)
    "09 \u2014 What the Seller Won\u2019t Tell You":                                  "2026-05-15T06:59:59Z",  # Thu 5/14
    "10 \u2014 Stranded Is a Plan You Didn\u2019t Make":                              "2026-05-22T06:59:59Z",  # Thu 5/21
    "11 \u2014 Free Repairs You Didn\u2019t Know You Had":                            "2026-05-22T06:59:59Z",  # Thu 5/21 (2 this week — shorter assignments)
    "12 \u2014 The Word \u201cNo\u201d Is Worth Thousands":                           "2026-05-29T06:59:59Z",  # Thu 5/28
    "13 \u2014 Every Mile Is on Your Record":                                         "2026-05-29T06:59:59Z",  # Thu 5/28 (2 this week — shorter assignments)
    "14 \u2014 The Breakeven Point":                                                  "2026-06-05T06:59:59Z",  # Thu 6/4
    "15 \u2014 The Drivetrain Is Changing":                                           "2026-06-05T06:59:59Z",  # Thu 6/4 (2 this week)
    "16 \u2014 Your Owner\u2019s Manual for Owning a Car":                            "2026-06-09T06:59:59Z",  # Mon 6/8 (capstone, 3 days before end)
}


def set_due_dates(dry_run=False):
    url, token = get_creds()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    updated = 0
    skipped = 0
    not_found = 0

    for cid in ENGINES_FAB_COURSE_IDS:
        r = requests.get(f"{url}/api/v1/courses/{cid}", headers=headers)
        cname = r.json().get("name", f"Course {cid}")
        print(f"\n{'═' * 65}")
        print(f"  {'DRY RUN — ' if dry_run else ''}SET DUE DATES: {cname} (ID: {cid})")
        print(f"{'═' * 65}")

        # Get assignments
        assignments = {}
        for a in paginated_get(f"{url}/api/v1/courses/{cid}/assignments", headers, {"per_page": "50"}):
            assignments[a["name"]] = a

        for asgn_name, due_date in DUE_DATES.items():
            if asgn_name not in assignments:
                print(f"  ⚠ NOT FOUND: \"{asgn_name}\"")
                not_found += 1
                continue

            asgn = assignments[asgn_name]
            asgn_id = asgn["id"]
            current_due = asgn.get("due_at")

            if dry_run:
                status = f"(currently: {current_due or 'none'})"
                print(f"  WOULD SET: {asgn_name}")
                print(f"             → {due_date}  {status}")
                continue

            r = requests.put(
                f"{url}/api/v1/courses/{cid}/assignments/{asgn_id}",
                headers=headers,
                json={"assignment": {"due_at": due_date}},
            )

            if r.status_code == 200:
                print(f"  ✓ SET: {asgn_name} → {due_date}")
                updated += 1
            else:
                print(f"  ✗ FAILED ({r.status_code}): {asgn_name}")
                skipped += 1

    if not dry_run:
        print(f"\n{'═' * 65}")
        print(f"  SUMMARY: Updated {updated}, Failed {skipped}, Not found {not_found}")
        print(f"{'═' * 65}")
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Set due dates for Engines Fab courses")
    parser.add_argument("--dry-run", action="store_true", help="Preview without changes")
    parser.add_argument("--deploy", action="store_true", help="Set all due dates")
    args = parser.parse_args()

    if args.dry_run:
        set_due_dates(dry_run=True)
    elif args.deploy:
        set_due_dates(dry_run=False)
    else:
        parser.print_help()
