#!/usr/bin/env python3
"""Fix published state mismatch for 'Portable Angle Grinder Safety' across metals courses."""

import os
import sys

METALS_COURSE_IDS = [23164, 23132, 23157, 23188, 23177]

def main():
    from canvasapi import Canvas
    url = os.environ.get("CANVAS_API_URL")
    token = os.environ.get("CANVAS_API_TOKEN")
    if not url or not token:
        print("ERROR: Set CANVAS_API_URL and CANVAS_API_TOKEN")
        sys.exit(1)
    canvas = Canvas(url, token)

    for cid in METALS_COURSE_IDS:
        course = canvas.get_course(cid)
        course_name = getattr(course, "name", f"Course {cid}")
        for a in course.get_assignments():
            if getattr(a, "name", "") == "Portable Angle Grinder Safety":
                published = getattr(a, "published", None)
                print(f"  {course_name} (ID {cid}): published={published}", end="")
                if not published:
                    a.edit(assignment={"published": True})
                    print(" → PUBLISHED")
                else:
                    print(" (already published)")
                break

if __name__ == "__main__":
    main()
