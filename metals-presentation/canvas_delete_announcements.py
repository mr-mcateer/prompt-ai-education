#!/usr/bin/env python3
"""Delete ALL announcements from all metals courses."""

import os
import sys
import requests

METALS_COURSE_IDS = [23164, 23132, 23157, 23188, 23177]

def main():
    url = os.environ.get("CANVAS_API_URL")
    token = os.environ.get("CANVAS_API_TOKEN")
    if not url or not token:
        print("ERROR: Set CANVAS_API_URL and CANVAS_API_TOKEN")
        sys.exit(1)

    headers = {"Authorization": f"Bearer {token}"}

    for cid in METALS_COURSE_IDS:
        r = requests.get(f"{url}/api/v1/courses/{cid}", headers=headers)
        cname = r.json().get("name", f"Course {cid}")
        print(f"\n  {cname} (ID: {cid})")

        # Get all announcements (they're discussion_topics with only_announcements=true)
        page_url = f"{url}/api/v1/courses/{cid}/discussion_topics?only_announcements=true&per_page=50"
        while page_url:
            r = requests.get(page_url, headers=headers)
            announcements = r.json()

            for ann in announcements:
                ann_id = ann["id"]
                title = ann.get("title", "Untitled")
                dr = requests.delete(
                    f"{url}/api/v1/courses/{cid}/discussion_topics/{ann_id}",
                    headers=headers,
                )
                if dr.status_code in (200, 204):
                    print(f"    DELETED: {title}")
                else:
                    print(f"    ⚠ Failed to delete {title}: {dr.status_code}")

            # Pagination
            links = r.headers.get("Link", "")
            page_url = None
            for link in links.split(","):
                if 'rel="next"' in link:
                    page_url = link.split("<")[1].split(">")[0]

        if not announcements:
            print(f"    (no announcements found)")

if __name__ == "__main__":
    main()
