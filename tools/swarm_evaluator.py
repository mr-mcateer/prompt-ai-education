#!/usr/bin/env python3
"""
Swarm Evaluator -- Gemini-powered submission review engine.
Generates clarifying questions per rubric criterion. Does NOT assign scores.

This module handles:
  - Text extraction from PDF and DOCX files
  - HTML stripping for text entries
  - Gemini prompt construction and API calls
  - Response parsing and validation

No Canvas dependency -- this is a pure evaluation engine.

Usage (as library):
    from tools.swarm_evaluator import get_gemini_client, review_text_submission
    client = get_gemini_client()
    result = review_text_submission(client, rubric_criteria, text, "Assignment Name")
"""

import json
import os
import re
import sys
from html.parser import HTMLParser
from io import BytesIO, StringIO
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools.env_loader import get_env

# ── Constants ─────────────────────────────────────────────────
GEMINI_MODEL = "gemini-2.5-flash"
MAX_TEXT_CHARS = 8000  # truncate long submissions

SYSTEM_PROMPT = """You are an experienced Career & Technical Education (CTE) metals fabrication \
teacher reviewing student submissions. Your job is NOT to score the work. Your job is to \
generate specific, constructive clarifying questions that will help the teacher grade \
and help the student improve.

For each rubric criterion, generate 1-2 questions based on what you observe in the \
submission. Questions should:
- Reference specific content from the submission
- Ask about gaps or unclear elements
- Be constructive and encouraging, not critical
- Help the teacher identify what level the student is at
- Use plain language a high school student can understand

Also note any flags (missing sections, incomplete work, off-topic content).

Respond with ONLY valid JSON. No markdown code fences, no text before or after."""

RESPONSE_SCHEMA = """{
  "criterion_reviews": [
    {
      "criterion_name": "exact criterion name from rubric",
      "observations": "what you found in the submission for this criterion",
      "questions": ["specific question 1", "specific question 2"],
      "completeness": "complete|partial|missing"
    }
  ],
  "overall_observations": "2-3 sentence summary of the submission",
  "flags": ["flag1", "flag2"],
  "submission_quality": "complete|partial|minimal|empty"
}"""


# ── HTML Stripping ────────────────────────────────────────────

class _HTMLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.result = StringIO()

    def handle_data(self, data):
        self.result.write(data)

    def get_text(self):
        return self.result.getvalue()


def strip_html(html_string):
    """Strip HTML tags, return plain text."""
    if not html_string:
        return ""
    stripper = _HTMLStripper()
    try:
        stripper.feed(html_string)
        return stripper.get_text().strip()
    except Exception:
        # Fallback: regex strip
        return re.sub(r"<[^>]+>", "", html_string).strip()


# ── Text Extraction ───────────────────────────────────────────

def extract_text_from_pdf(file_bytes):
    """Extract text from PDF bytes using pymupdf. Returns plain text or error string."""
    try:
        import fitz  # pymupdf
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        pages = []
        for page in doc:
            pages.append(page.get_text())
        doc.close()
        text = "\n\n".join(pages).strip()
        return text if text else "[PDF contained no extractable text -- may be scanned images]"
    except Exception as e:
        return f"[PDF extraction error: {e}]"


def extract_text_from_docx(file_bytes):
    """Extract text from DOCX bytes using python-docx. Returns plain text or error string."""
    try:
        from docx import Document
        doc = Document(BytesIO(file_bytes))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        text = "\n".join(paragraphs).strip()
        return text if text else "[DOCX contained no text]"
    except Exception as e:
        return f"[DOCX extraction error: {e}]"


# ── Gemini Client ─────────────────────────────────────────────

def get_gemini_client():
    """Initialize and return a Gemini API client."""
    try:
        from google import genai
    except ImportError:
        print("ERROR: google-genai not installed. Run: pip3 install google-genai")
        sys.exit(1)

    api_key = get_env("GEMINI_API_KEY")
    return genai.Client(api_key=api_key)


# ── Prompt Building ───────────────────────────────────────────

def _format_rubric_for_prompt(rubric_criteria):
    """Format rubric criteria dict into readable text for the prompt."""
    lines = []
    for idx in sorted(rubric_criteria.keys(), key=lambda k: int(k) if k.isdigit() else k):
        crit = rubric_criteria[idx]
        desc = crit["description"]
        pts = crit["points"]
        lines.append(f"Criterion: {desc} ({pts} points max)")
        lines.append("  Rating Levels:")
        for ridx in sorted(crit["ratings"].keys(), key=lambda k: int(k) if k.isdigit() else k):
            r = crit["ratings"][ridx]
            lines.append(f"    - {r['points']} pts: {r['description']}")
        lines.append("")
    return "\n".join(lines)


def build_review_prompt(rubric_criteria, assignment_name, submission_text=None,
                        has_image=False, file_metadata=None):
    """Build the user prompt for Gemini review."""
    rubric_block = _format_rubric_for_prompt(rubric_criteria)

    parts = [
        f'Review this student submission for the assignment "{assignment_name}".',
        "",
        "RUBRIC CRITERIA:",
        rubric_block,
    ]

    if submission_text:
        text = submission_text[:MAX_TEXT_CHARS]
        if len(submission_text) > MAX_TEXT_CHARS:
            text += "\n[... text truncated ...]"
        parts.extend([
            "SUBMISSION TEXT:",
            "--- BEGIN STUDENT TEXT ---",
            text,
            "--- END STUDENT TEXT ---",
            "",
        ])

    if has_image:
        parts.extend([
            "[An image is attached for visual analysis]",
            "Analyze the image for evidence of: quality of work, completeness, "
            "craftsmanship, documentation thoroughness. Note what you can observe "
            "about fabrication quality, finish, and professionalism.",
            "",
        ])

    if file_metadata:
        parts.extend([
            "ADDITIONAL FILES SUBMITTED:",
            *[f"  - {f['filename']} ({f.get('size_kb', '?')} KB, {f.get('type', 'unknown')})"
              for f in file_metadata],
            "",
        ])

    parts.extend([
        "Respond with this JSON structure:",
        RESPONSE_SCHEMA,
        "",
        "IMPORTANT: criterion_name must exactly match the criterion names from the rubric above.",
    ])

    return "\n".join(parts)


# ── Gemini API Calls ──────────────────────────────────────────

def review_text_submission(client, rubric_criteria, text, assignment_name,
                           file_metadata=None):
    """Send text submission to Gemini for review. Returns parsed dict or error dict."""
    from google import genai as genai_module

    prompt = build_review_prompt(
        rubric_criteria, assignment_name,
        submission_text=text, file_metadata=file_metadata,
    )

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=genai_module.types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.3,
            ),
        )
        return parse_review_response(response.text)
    except Exception as e:
        return {"error": str(e), "criterion_reviews": [], "submission_quality": "error"}


def review_image_submission(client, rubric_criteria, image_bytes, mime_type,
                            assignment_name, supplemental_text=None,
                            file_metadata=None):
    """Send image submission to Gemini vision for review. Returns parsed dict or error dict."""
    from google import genai as genai_module

    prompt = build_review_prompt(
        rubric_criteria, assignment_name,
        submission_text=supplemental_text, has_image=True,
        file_metadata=file_metadata,
    )

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[
                genai_module.types.Part.from_text(text=prompt),
                genai_module.types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
            ],
            config=genai_module.types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.3,
            ),
        )
        return parse_review_response(response.text)
    except Exception as e:
        return {"error": str(e), "criterion_reviews": [], "submission_quality": "error"}


# ── Response Parsing ──────────────────────────────────────────

def parse_review_response(response_text):
    """Parse Gemini JSON response. Handles markdown fences and validation."""
    if not response_text:
        return {"error": "empty response", "criterion_reviews": [], "submission_quality": "error"}

    text = response_text.strip()

    # Strip markdown code fences if present
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first line (```json or ```) and last line (```)
        if lines[-1].strip() == "```":
            lines = lines[1:-1]
        else:
            lines = lines[1:]
        text = "\n".join(lines).strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        return {
            "error": f"JSON parse error: {e}",
            "raw_response": response_text[:500],
            "criterion_reviews": [],
            "submission_quality": "error",
        }

    # Validate expected keys
    if "criterion_reviews" not in data:
        data["criterion_reviews"] = []
    if "submission_quality" not in data:
        data["submission_quality"] = "unknown"
    if "overall_observations" not in data:
        data["overall_observations"] = ""
    if "flags" not in data:
        data["flags"] = []

    return data


# ── Personal Mode (casual teacher wonderings) ────────────────

PERSONAL_SYSTEM_PROMPT = """You are Mr. McAteer, a CTE metals and fabrication teacher. You just \
looked at a student's work and want to leave a quick, genuine note. You are NOT evaluating \
or grading. You noticed something specific and have one brief wondering about it.

Rules:
- Write ONE wondering, 1-2 sentences max
- Reference something SPECIFIC you see in their work (a technique, material choice, layout detail, dimension, process step, a phrase they wrote)
- Sound like a real teacher talking to a student at their workstation
- Be casual and encouraging
- Use plain language a high school student would use
- NEVER use em-dashes. Use double dashes (--) if you need a dash
- Vary your openers. Do not start with "Great job" or "Nice work" every time. Mix it up: "I noticed...", "Curious about...", "I can see...", "Hey, quick question --", "Looking at your...", etc.
- Do not use the word "submission". Say "this", "your work", or reference the specific thing
- The wondering should be a genuine question you would actually want to know the answer to

Respond with ONLY valid JSON. No markdown code fences, no text before or after."""

PERSONAL_RESPONSE_SCHEMA = """{
  "wondering": "your one brief wondering about their work",
  "submission_quality": "complete|partial|minimal|empty"
}"""


def build_personal_prompt(assignment_name, submission_text=None,
                          has_image=False, file_metadata=None):
    """Build a minimal prompt for personal wondering mode."""
    parts = [
        f'A student turned in work for "{assignment_name}". '
        "Look at what they submitted and write one brief wondering.",
        "",
    ]

    if submission_text:
        text = submission_text[:MAX_TEXT_CHARS]
        if len(submission_text) > MAX_TEXT_CHARS:
            text += "\n[... text truncated ...]"
        parts.extend([
            "STUDENT'S WORK:",
            text,
            "",
        ])

    if has_image:
        parts.extend([
            "[A photo of their work is attached]",
            "Look at the image and find one specific detail to ask about.",
            "",
        ])

    if file_metadata:
        parts.extend([
            "Files submitted:",
            *[f"  - {f['filename']}" for f in file_metadata],
            "",
        ])

    parts.extend([
        "Respond with this JSON:",
        PERSONAL_RESPONSE_SCHEMA,
    ])

    return "\n".join(parts)


def review_submission_personal(client, assignment_name, contents_text=None,
                               image_bytes=None, image_mime=None,
                               file_metadata=None):
    """Generate a single personal wondering about a submission. Returns dict."""
    from google import genai as genai_module

    has_image = image_bytes is not None
    prompt = build_personal_prompt(
        assignment_name, submission_text=contents_text,
        has_image=has_image, file_metadata=file_metadata,
    )

    try:
        if has_image:
            contents = [
                genai_module.types.Part.from_text(text=prompt),
                genai_module.types.Part.from_bytes(data=image_bytes, mime_type=image_mime),
            ]
        else:
            contents = prompt

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents,
            config=genai_module.types.GenerateContentConfig(
                system_instruction=PERSONAL_SYSTEM_PROMPT,
                temperature=0.7,
            ),
        )
        return parse_personal_response(response.text)
    except Exception as e:
        return {"error": str(e), "wondering": "", "submission_quality": "error"}


def parse_personal_response(response_text):
    """Parse personal mode JSON response."""
    if not response_text:
        return {"error": "empty response", "wondering": "", "submission_quality": "error"}

    text = response_text.strip()

    # Strip markdown code fences if present
    if text.startswith("```"):
        lines = text.split("\n")
        if lines[-1].strip() == "```":
            lines = lines[1:-1]
        else:
            lines = lines[1:]
        text = "\n".join(lines).strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        return {
            "error": f"JSON parse error: {e}",
            "wondering": "",
            "submission_quality": "error",
        }

    if "wondering" not in data:
        data["wondering"] = ""
    if "submission_quality" not in data:
        data["submission_quality"] = "unknown"

    # Enforce no em-dashes -- replace with double dash
    if data["wondering"]:
        data["wondering"] = data["wondering"].replace("\u2014", "--").replace("\u2013", "--")

    return data
