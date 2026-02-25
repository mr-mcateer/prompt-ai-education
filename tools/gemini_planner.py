#!/usr/bin/env python3
"""
Gemini Planning Agent — Level 1
Sends your raw prompt to Gemini, returns a structured execution_plan.md
that Claude Code reads and executes.

Usage:
    python tools/gemini_planner.py "Build a 2-week welding safety module"
    python tools/gemini_planner.py --file my_idea.txt
"""
import sys
import json
import argparse
from pathlib import Path

# Add project root to path for env_loader
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools.env_loader import get_env

try:
    from google import genai
except ImportError:
    print("ERROR: google-genai not installed.")
    print("Run: pip3 install google-genai")
    sys.exit(1)


SYSTEM_PROMPT = """You are an expert instructional designer and curriculum architect
for Career & Technical Education (CTE) programs. You specialize in metals fabrication,
engines/automotive, and shop safety courses.

When given a task, produce a detailed execution plan in Markdown format that a
CLI-based code agent (Claude Code) can follow step by step.

Your plan must include:
1. A clear objective summary
2. Numbered execution steps (each step = one terminal action or API call)
3. File paths for any content to be created
4. Canvas LMS module/assignment structure if applicable
5. Due date calculations if applicable (use ISO 8601 format)
6. Rubric criteria with point values if graded items are involved

Format your output as a Markdown document starting with `# Execution Plan`.
Be explicit about every action. Claude Code cannot infer — it needs exact steps.
Never include API keys or tokens in the plan. Reference environment variables instead."""


def plan(prompt: str, output_path: str = "execution_plan.md") -> str:
    api_key = get_env("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)

    print(f"Sending to Gemini: {prompt[:80]}...")
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=genai.types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
        ),
    )

    plan_text = response.text
    out = Path(output_path)
    out.write_text(plan_text, encoding="utf-8")
    print(f"Plan written to: {out.resolve()}")
    return plan_text


def main():
    parser = argparse.ArgumentParser(description="Gemini Planning Agent")
    parser.add_argument("prompt", nargs="?", help="The planning prompt")
    parser.add_argument("--file", "-f", help="Read prompt from a file")
    parser.add_argument("--output", "-o", default="execution_plan.md",
                        help="Output file path (default: execution_plan.md)")
    args = parser.parse_args()

    if args.file:
        prompt = Path(args.file).read_text(encoding="utf-8")
    elif args.prompt:
        prompt = args.prompt
    else:
        parser.print_help()
        sys.exit(1)

    plan(prompt, args.output)


if __name__ == "__main__":
    main()
