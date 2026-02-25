#!/usr/bin/env python3
"""
Publish Module 2 "Know Your Metals" across all Metals courses.

Links the orphaned "Metal Types -- Unit Quiz" and "Metal Types -- Study Guide"
into Module 2, then publishes the module and both items so students can see them.

Usage:
  python3 canvas_publish_metals_quiz.py --dry-run    # Preview (no changes)
  python3 canvas_publish_metals_quiz.py --execute    # Apply changes
"""

import argparse
import os
import sys
import time
import requests

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from tools.env_loader import get_env

METALS_COURSE_IDS = [23164, 23132, 23157, 23188, 23177]

MODULE_NAME = "2 \u2014 Know Your Metals"
QUIZ_NAME = "Metal Types \u2014 Unit Quiz"
PAGE_NAME = "Metal Types \u2014 Study Guide"

# ANSI colors
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"


def get_creds():
    url = get_env("CANVAS_API_URL")
    token = get_env("CANVAS_API_TOKEN")
    return url, token


def paginated_get(url, headers, params=None):
    """GET with Canvas pagination."""
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


def run(dry_run=True):
    url, token = get_creds()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    mode = "DRY RUN" if dry_run else "EXECUTE"
    print(f"\n{BOLD}{'=' * 65}{RESET}")
    print(f"{BOLD}  Publish Module 2 'Know Your Metals' -- {mode}{RESET}")
    print(f"{'=' * 65}")

    success = 0
    errors = 0

    for cid in METALS_COURSE_IDS:
        r = requests.get(f"{url}/api/v1/courses/{cid}", headers=headers)
        cname = r.json().get("name", f"Course {cid}")
        print(f"\n  {BOLD}{cname} (ID: {cid}){RESET}")

        try:
            # ── Find all assignments ────────────────────────────
            assignments = {}
            for a in paginated_get(
                f"{url}/api/v1/courses/{cid}/assignments", headers,
                {"per_page": "100"}
            ):
                assignments[a["name"]] = a
            time.sleep(0.1)

            # ── Find all pages ──────────────────────────────────
            pages = {}
            for p in paginated_get(
                f"{url}/api/v1/courses/{cid}/pages", headers,
                {"per_page": "100"}
            ):
                pages[p["title"]] = p
            time.sleep(0.1)

            # ── Find Module 2 ──────────────────────────────────
            modules = paginated_get(
                f"{url}/api/v1/courses/{cid}/modules", headers,
                {"per_page": "50", "include[]": "items"}
            )
            time.sleep(0.1)

            module = None
            for m in modules:
                if m["name"] == MODULE_NAME:
                    module = m
                    break

            if not module:
                print(f"    {RED}Module not found: {MODULE_NAME}{RESET}")
                errors += 1
                continue

            module_id = module["id"]
            is_published = module.get("published", False)
            print(f"    Module: {MODULE_NAME} (ID: {module_id}, "
                  f"published={is_published})")

            # Current items in the module
            current_items = module.get("items", [])
            current_content_ids = set()
            current_titles = set()
            for ci in current_items:
                if ci.get("content_id"):
                    current_content_ids.add(ci["content_id"])
                current_titles.add(ci.get("title", ""))

            # ── Link Study Guide page ──────────────────────────
            if PAGE_NAME in pages:
                page = pages[PAGE_NAME]
                page_slug = page.get("url", "")
                page_published = page.get("published", False)
                print(f"    Page: {PAGE_NAME} (published={page_published})")

                if PAGE_NAME in current_titles:
                    print(f"    {DIM}Page already in module (skip link){RESET}")
                else:
                    if dry_run:
                        print(f"    {YELLOW}[DRY RUN] Would add page "
                              f"to module at position 1{RESET}")
                    else:
                        r = requests.post(
                            f"{url}/api/v1/courses/{cid}/modules/"
                            f"{module_id}/items",
                            headers=headers,
                            json={"module_item": {
                                "type": "Page",
                                "page_url": page_slug,
                                "position": 1,
                            }},
                        )
                        if r.status_code in (200, 201):
                            print(f"    {GREEN}Linked page into module "
                                  f"at position 1{RESET}")
                        else:
                            print(f"    {RED}Failed to link page: "
                                  f"{r.status_code}{RESET}")
                        time.sleep(0.1)

                # Publish the page
                if not page_published:
                    if dry_run:
                        print(f"    {YELLOW}[DRY RUN] Would publish "
                              f"page{RESET}")
                    else:
                        r = requests.put(
                            f"{url}/api/v1/courses/{cid}/pages/{page_slug}",
                            headers=headers,
                            json={"wiki_page": {"published": True}},
                        )
                        if r.status_code == 200:
                            print(f"    {GREEN}Published page{RESET}")
                        else:
                            print(f"    {RED}Failed to publish page: "
                                  f"{r.status_code}{RESET}")
                        time.sleep(0.1)
                else:
                    print(f"    {DIM}Page already published{RESET}")
            else:
                print(f"    {RED}Page not found: {PAGE_NAME}{RESET}")

            # ── Link Quiz assignment ───────────────────────────
            if QUIZ_NAME in assignments:
                asgn = assignments[QUIZ_NAME]
                asgn_id = asgn["id"]
                asgn_published = asgn.get("published", False)
                print(f"    Quiz: {QUIZ_NAME} (ID: {asgn_id}, "
                      f"published={asgn_published})")

                if asgn_id in current_content_ids:
                    print(f"    {DIM}Quiz already in module (skip link){RESET}")
                else:
                    if dry_run:
                        print(f"    {YELLOW}[DRY RUN] Would add quiz "
                              f"to module at position 2{RESET}")
                    else:
                        r = requests.post(
                            f"{url}/api/v1/courses/{cid}/modules/"
                            f"{module_id}/items",
                            headers=headers,
                            json={"module_item": {
                                "type": "Assignment",
                                "content_id": asgn_id,
                                "position": 2,
                            }},
                        )
                        if r.status_code in (200, 201):
                            print(f"    {GREEN}Linked quiz into module "
                                  f"at position 2{RESET}")
                        else:
                            print(f"    {RED}Failed to link quiz: "
                                  f"{r.status_code}{RESET}")
                        time.sleep(0.1)

                # Publish the assignment
                if not asgn_published:
                    if dry_run:
                        print(f"    {YELLOW}[DRY RUN] Would publish "
                              f"quiz{RESET}")
                    else:
                        r = requests.put(
                            f"{url}/api/v1/courses/{cid}/assignments/{asgn_id}",
                            headers=headers,
                            json={"assignment": {"published": True}},
                        )
                        if r.status_code == 200:
                            print(f"    {GREEN}Published quiz{RESET}")
                        else:
                            print(f"    {RED}Failed to publish quiz: "
                                  f"{r.status_code}{RESET}")
                        time.sleep(0.1)
                else:
                    print(f"    {DIM}Quiz already published{RESET}")
            else:
                print(f"    {RED}Quiz not found: {QUIZ_NAME}{RESET}")

            # ── Publish the module ─────────────────────────────
            if not is_published:
                if dry_run:
                    print(f"    {YELLOW}[DRY RUN] Would publish "
                          f"module{RESET}")
                else:
                    r = requests.put(
                        f"{url}/api/v1/courses/{cid}/modules/{module_id}",
                        headers=headers,
                        json={"module": {"published": True}},
                    )
                    if r.status_code == 200:
                        print(f"    {GREEN}Published module{RESET}")
                    else:
                        print(f"    {RED}Failed to publish module: "
                              f"{r.status_code}{RESET}")
                    time.sleep(0.1)
            else:
                print(f"    {DIM}Module already published{RESET}")

            success += 1

        except Exception as e:
            print(f"    {RED}ERROR: {e}{RESET}")
            errors += 1

    print(f"\n{'=' * 65}")
    print(f"  Done: {success} courses updated, {errors} errors")
    print(f"{'=' * 65}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Publish Module 2 'Know Your Metals' across Metals courses")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true",
                      help="Preview changes without making them")
    mode.add_argument("--execute", action="store_true",
                      help="Apply changes to all courses")
    args = parser.parse_args()

    run(dry_run=args.dry_run)
