# Project: AI Instructional Designer Engine
# Owner: Andrew McAteer — CTE / Metals / Engines & Fabrication

## Execution Pipeline
1. **Plan first.** Run `python tools/gemini_planner.py "<prompt>"` before taking action on any complex task.
2. **Review.** Read the resulting `execution_plan.md` before executing.
3. **Execute.** Follow Gemini's plan. Use terminal tools for PDFs, Git, and Canvas API.
4. **Update state.** After completing a phase, update `.planning/state.md`.

## Security Rules
- NEVER hardcode API keys in scripts, commands, or chat output.
- ALL secrets live in `.env` and are loaded via `from tools.env_loader import get_env`.
- Canvas scripts: `token = get_env("CANVAS_API_TOKEN")` — never inline tokens.
- Before running any Canvas API script, verify it uses env_loader, not hardcoded tokens.

## Canvas LMS Context
- District: Bend-La Pine Schools (CSD 509J)
- Base URL: loaded from `CANVAS_API_URL` env var
- Metals course IDs: 23164, 23132, 23157, 23188, 23177
- Engines/Fab course IDs: 23124, 23344

## Code Style
- No em-dashes in any generated content.
- Check `docs/templates/` before formatting new assignments.
- Python scripts go in `tools/` (utilities) or `metals-presentation/` (Canvas-specific).

## Project Structure
```
.env                          # THE VAULT — all secrets here
.gitignore                    # Prevents .env from being committed
CLAUDE.md                     # This file — Claude's onboarding doc
tools/
  gemini_planner.py           # Level 1: Gemini planning bridge
  env_loader.py               # Secure env var loader
.claude/
  commands/                   # Level 3A: Slash commands
  skills/                     # Level 3B: Auto-injected context
  settings.json               # Level 3C: Hooks configuration
.planning/
  roadmap.md                  # Level 5: Gemini-authored phases
  state.md                    # Level 5: Execution progress tracker
metals-presentation/          # Canvas automation scripts
engine-review/                # Engine presentation assets
csd509j-redesign/             # District website redesign
```
