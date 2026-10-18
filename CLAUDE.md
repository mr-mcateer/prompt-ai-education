# Project: AI Instructional Designer Engine
# Owner: Andrew McAteer — CTE / Metals / Engines & Fabrication

## Execution Pipeline
1. **Plan first.** Run `python tools/gemini_planner.py "<prompt>"` before taking action on any complex task.
2. **Review.** Read the resulting `execution_plan.md` before executing.
3. **Execute.** Follow Gemini's plan. Use terminal tools for PDFs, Git, and Canvas API.

## Security Rules
- NEVER hardcode API keys in scripts, commands, or chat output.
- ALL secrets live in `.env` and are loaded via `from tools.env_loader import get_env`.
- Canvas scripts: `token = get_env("CANVAS_API_TOKEN")` — never inline tokens and never bare `os.environ.get` for secrets (audited and fixed 2026-10-18; every `canvas_*.py` now goes through env_loader).
- Before running any Canvas API script, verify it uses env_loader, not hardcoded tokens.
- Student PII (grades exports, gradebook snapshots, Synergy dumps) never gets committed. `.gitignore` and `.githooks/pre-commit` both guard this.
- The pre-commit guard only runs if git knows about it. In every fresh clone run: `git config core.hooksPath .githooks`
- Cloud sessions have no `.env`. Canvas and Gemini scripts will exit with a clear error there until the secrets are added to the cloud environment: open the environment menu in the session title bar, choose Edit, and add `CANVAS_API_TOKEN`, `CANVAS_API_URL`, and `GEMINI_API_KEY` under Network secrets (or as environment variables). New sessions pick them up.

## Canvas LMS Context
- District: Corvallis School District 509J (csd509j.instructure.com)
- Base URL: loaded from `CANVAS_API_URL` env var
- Metals course IDs: 23164, 23132, 23157, 23188, 23177
- Engines/Fab course IDs: 23124, 23344

## Code Style
- No em-dashes in any generated content.
- Python scripts go in `tools/` (utilities) or `metals-presentation/` (Canvas-specific).

## Project Structure
```
CLAUDE.md                     # This file — Claude's onboarding doc
CNAME, index.html, img/       # promptaieducation.com static site
.env.example                  # Names of required secrets; real values go in .env (gitignored, currently absent — token rotation pending)
.githooks/pre-commit          # Blocks secrets and student PII from commits (needs core.hooksPath, see Security Rules)
agenda/                       # Weekly class agendas (metals/, se/) as static HTML
metals/                       # Metals build guides and self-grade PDFs (The Dice, welds portfolio)
skills-library/               # Researched catalog of third-party skills and MCPs; nothing in it is active
tools/
  gemini_planner.py           # Gemini planning bridge
  env_loader.py               # Secure env var loader
  canvas_daily_briefing.py    # Daily Canvas pull → briefing markdown
  swarm_evaluator.py          # Gemini grading engine (no Canvas deps)
.claude/
  launch.json                 # Dev-server config
  commands/, agents/          # Canvas slash commands + agents (rehomed here 2026-07-31)
metals-presentation/          # Canvas automation scripts (~22 canvas_*.py)
engine-review/                # Engine presentation assets
csd509j-redesign/             # District website redesign
AUDIT-2026-10-18.md           # Cloud session and setup audit: findings, fixes, open items
```
