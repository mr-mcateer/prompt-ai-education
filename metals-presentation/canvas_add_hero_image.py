#!/usr/bin/env python3
"""
Upload the Gemini hero image to each metals course and embed it
at the top of "The Exorcism of the Plasma Cutter — Practice Lab" assignment.
"""

import os, sys, requests, json

CANVAS_URL = os.environ.get("CANVAS_API_URL", "https://csd509j.instructure.com")
TOKEN = os.environ.get("CANVAS_API_TOKEN", "")
HEADERS = {"Authorization": f"Bearer {TOKEN}"}
METALS_COURSE_IDS = [23164, 23132, 23157, 23188, 23177]
IMAGE_PATH = os.path.expanduser("~/Downloads/Gemini_Generated_Image_vhpazlvhpazlvhpa.png")
ASSIGNMENT_NAME = "The Exorcism of the Plasma Cutter — Practice Lab"


def upload_file_to_course(course_id, file_path, folder_path="course files"):
    """Upload a file to a Canvas course using the 3-step upload process."""
    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)

    # Step 1: Notify Canvas
    r = requests.post(
        f"{CANVAS_URL}/api/v1/courses/{course_id}/files",
        headers=HEADERS,
        data={
            "name": file_name,
            "size": file_size,
            "content_type": "image/png",
            "parent_folder_path": folder_path,
        },
    )
    r.raise_for_status()
    step1 = r.json()

    # Step 2: Upload file data
    upload_url = step1["upload_url"]
    upload_params = step1["upload_params"]
    with open(file_path, "rb") as f:
        r2 = requests.post(
            upload_url,
            data=upload_params,
            files={"file": (file_name, f, "image/png")},
        )
    # Canvas may return 301/302 redirect — follow it
    if r2.status_code in (301, 302):
        r2 = requests.get(r2.headers["Location"], headers=HEADERS)
    r2.raise_for_status()
    file_info = r2.json()

    # Step 3: Confirm (some installs require this)
    if "id" in file_info:
        return file_info
    confirm_url = file_info.get("location")
    if confirm_url:
        r3 = requests.get(confirm_url, headers=HEADERS)
        r3.raise_for_status()
        return r3.json()
    return file_info


def find_assignment(course_id, name):
    """Find an assignment by name in a course."""
    url = f"{CANVAS_URL}/api/v1/courses/{course_id}/assignments"
    params = {"search_term": name[:30], "per_page": 100}
    r = requests.get(url, headers=HEADERS, params=params)
    r.raise_for_status()
    for a in r.json():
        if a["name"] == name:
            return a
    return None


def update_assignment_with_image(course_id, assignment_id, image_url, current_desc):
    """Prepend the hero image to the assignment description."""
    hero_html = f"""<div style="text-align:center; margin-bottom:20px;">
  <img src="{image_url}" alt="The Exorcism of the Plasma Cutter" style="max-width:100%; border-radius:8px; box-shadow: 0 4px 16px rgba(0,0,0,0.3);" />
</div>
"""
    # If image is already in the description, skip
    if "Exorcism of the Plasma Cutter" in (current_desc or "") and "<img" in (current_desc or ""):
        return False

    new_desc = hero_html + (current_desc or "")
    r = requests.put(
        f"{CANVAS_URL}/api/v1/courses/{course_id}/assignments/{assignment_id}",
        headers=HEADERS,
        json={"assignment": {"description": new_desc}},
    )
    r.raise_for_status()
    return True


COURSE_NAMES = {
    23164: "P3 Metals 1",
    23132: "P3 Metals 2",
    23157: "P3 Metals 3",
    23188: "P5 Metals 1",
    23177: "P5 Metals 2",
}

if __name__ == "__main__":
    if not TOKEN:
        print("ERROR: Set CANVAS_API_TOKEN")
        sys.exit(1)
    if not os.path.exists(IMAGE_PATH):
        print(f"ERROR: Image not found at {IMAGE_PATH}")
        sys.exit(1)

    print(f"Image: {IMAGE_PATH} ({os.path.getsize(IMAGE_PATH) / 1024 / 1024:.1f} MB)")
    print()

    for cid in METALS_COURSE_IDS:
        name = COURSE_NAMES.get(cid, f"Course {cid}")
        print(f"{'═' * 60}")
        print(f"  {name} (ID: {cid})")
        print(f"{'═' * 60}")

        # Upload image
        print("  Uploading image...", end=" ", flush=True)
        file_info = upload_file_to_course(cid, IMAGE_PATH)
        file_id = file_info.get("id")
        # Canvas file URL for embedding
        preview_url = file_info.get("url") or file_info.get("preview_url", "")
        # Use the /files/:id/preview URL pattern for Canvas-hosted images
        canvas_img_url = f"{CANVAS_URL}/courses/{cid}/files/{file_id}/preview"
        print(f"OK (file ID: {file_id})")

        # Find assignment
        print("  Finding assignment...", end=" ", flush=True)
        assignment = find_assignment(cid, ASSIGNMENT_NAME)
        if not assignment:
            print(f"NOT FOUND — skipping")
            continue
        print(f"OK (ID: {assignment['id']})")

        # Update description
        print("  Embedding hero image...", end=" ", flush=True)
        updated = update_assignment_with_image(
            cid, assignment["id"], canvas_img_url, assignment.get("description", "")
        )
        if updated:
            print("✓ Done")
        else:
            print("Already has image — skipped")

        print()

    print("═" * 60)
    print("  ALL COURSES UPDATED")
    print("═" * 60)
