# Generate Module

Generate a complete Canvas LMS module for a given topic.

## Instructions

1. Run the Gemini planner first:
   ```
   python tools/gemini_planner.py "Design a Canvas module for: $ARGUMENTS"
   ```
2. Read the resulting `execution_plan.md`.
3. Follow the plan to create:
   - Module structure (pages, assignments, quizzes)
   - Rubrics for each graded item
   - Proper due date sequencing
4. Use `tools/env_loader.py` for all API credentials.
5. Push the module to Canvas using the API.

## Arguments
- $ARGUMENTS: The module topic (e.g., "The French Revolution", "Arc Welding Safety")
