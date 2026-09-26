# Skills Library

Researched 2026-09-26. Free or open source only; nothing here sends student PII to a third party.

Open `toolchest.html` for the full catalog (install commands, user reports, privacy notes). `catalog.json` holds the same data.

Nothing in this folder is active. To use a skill, copy its folder into `~/.claude/skills/` (all projects) or `.claude/skills/` (this repo), or zip it and upload in claude.ai under Settings > Capabilities. MCP folders hold a `config.json` snippet with env placeholders; real values come from `.env`.

Tiers: **S** install now, **A** when the need comes up, **B** only for a specific setup. *Link only* means the license does not allow redistribution, so only `SOURCE.txt` or nothing was copied.

## Classroom

| Tier | Pick | Type | License | Local copy |
|---|---|---|---|---|
| S | [canvas-mcp (vishalsachdev)](https://github.com/vishalsachdev/canvas-mcp) | mcp + 8 skills | MIT | [`teaching/canvas-mcp-vishalsachdev`](teaching/canvas-mcp-vishalsachdev) |
| S | [Claude for Teachers](https://claude.com/solutions/teachers (announcement: https://www.anthropic.com/news/claude-for-teachers)) | platform (free Anthropic plan for verified US K-12 teachers) | proprietary service, free for 1 year (si | link only |
| A | [canvas-lms-mcp (bruchris)](https://github.com/bruchris/canvas-lms-mcp) | mcp + 16 skills (also a Claude Code plugin) | MIT | [`teaching/canvas-lms-mcp-bruchris`](teaching/canvas-lms-mcp-bruchris) |
| A | [k12-teacher-skills (Anthropic + Learning Commons)](https://github.com/anthropics/k12-teacher-skills) | skills (plugin k12-education) | Apache-2.0 | [`teaching/k12-teacher-skills-anthropic`](teaching/k12-teacher-skills-anthropic) |
| A | [education-agent-skills (Gareth Manning)](https://github.com/GarethManning/education-agent-skills) | skills (plugin, 165 skills) | CC-BY-SA-4.0 | [`teaching/education-agent-skills-manning`](teaching/education-agent-skills-manning) |
| A | [text2qti](https://github.com/gpoore/text2qti) | CLI tool (pairs with any skill) | BSD-3-Clause | [`teaching/text2qti`](teaching/text2qti) |
| A | [Anthropic document skills (docx, pptx, pdf, xlsx)](https://github.com/anthropics/skills) | skills | proprietary source-available (All rights | link only |
| B | [homework-grader (ChantillyAn)](https://github.com/ChantillyAn/homework-grader) | skill | MIT | [`teaching/homework-grader`](teaching/homework-grader) |
| B | [teaching-skills (YujxZJCN)](https://github.com/YujxZJCN/teaching-skills) | skills (plugin, 15 skills) | MIT | [`teaching/teaching-skills-yujx`](teaching/teaching-skills-yujx) |
| B | [Learning Commons Knowledge Graph MCP](https://github.com/learning-commons-org/knowledge-graph) | mcp (remote hosted) | code MIT; open datasets CC-BY-4.0 / CC0; | [`teaching/learning-commons-kg-mcp`](teaching/learning-commons-kg-mcp) |

## Shop

| Tier | Pick | Type | License | Local copy |
|---|---|---|---|---|
| S | [FreeCAD MCP](https://github.com/neka-nat/freecad-mcp) | mcp | MIT | [`shop/freecad-mcp`](shop/freecad-mcp) |
| S | [OpenSCAD MCP](https://github.com/RobertCoop/openscad-mcp) | mcp | MIT | [`shop/openscad-mcp`](shop/openscad-mcp) |
| A | [build123d MCP](https://github.com/pzfreo/build123d-mcp) | mcp | Apache-2.0 | [`shop/build123d-mcp`](shop/build123d-mcp) |
| A | [3d-print-modeling skill](https://github.com/m-esm/3d-print-modeling) | skill | MIT | link only |
| A | [MCP 3D Printer Server](https://github.com/DMontgomery40/mcp-3D-printer-server) | mcp | GPL-2.0 | [`shop/printer-mcp`](shop/printer-mcp) |
| B | [MCP for Blender (blender-mcp)](https://github.com/ahujasid/mcp-for-blender) | mcp | MIT | [`shop/blender-mcp`](shop/blender-mcp) |
| B | [AgentCADCAM skills](https://github.com/jeremylongworth-source/AgentCADCAM) | skill | MIT | link only |
| B | [eq-reference-mcp](https://github.com/joshuabryson/eq-reference-mcp) | mcp | MIT | [`shop/eq-reference-mcp`](shop/eq-reference-mcp) |
| B | [ha-mcp (Home Assistant MCP)](https://github.com/homeassistant-ai/ha-mcp) | mcp | MIT | [`shop/ha-mcp`](shop/ha-mcp) |
| B | [Fusion 360 MCP Server](https://github.com/faust-machines/fusion360-mcp-server) | mcp | MIT | [`shop/fusion360-mcp`](shop/fusion360-mcp) |
| B | [Jarvis Onshape MCP](https://github.com/ReshefElisha/jarvis-onshape-mcp) | plugin | MIT | [`shop/onshape-jarvis`](shop/onshape-jarvis) |
| B | [homebox-mcp](https://github.com/dgahagan/homebox-mcp) | mcp | MIT | [`shop/homebox-mcp`](shop/homebox-mcp) |
| B | [CNCjs MCP (CNC-design-control-MCP)](https://github.com/brs077/CNC-design-control-MCP) | mcp | MIT | [`shop/cncjs-mcp`](shop/cncjs-mcp) |
| B | [KiCAD MCP Server](https://github.com/mixelpixx/KiCAD-MCP-Server) | mcp | MIT | [`shop/kicad-mcp`](shop/kicad-mcp) |

## Home

| Tier | Pick | Type | License | Local copy |
|---|---|---|---|---|
| S | [Basic Memory (MCP server + 15 companion skills)](https://github.com/basicmachines-co/basic-memory) | mcp + skills | AGPL-3.0 (server); skills/README states  | [`personal/basic-memory`](personal/basic-memory) |
| S | [Obsidian Skills (kepano)](https://github.com/kepano/obsidian-skills) | skill (plugin marketplace) | MIT | [`personal/obsidian-skills`](personal/obsidian-skills) |
| S | [iMCP](https://github.com/mattt/iMCP) | mcp (macOS app) | MIT | [`personal/imcp`](personal/imcp) |
| S | [Life-admin decoder skills (from pm-claude-skills)](https://github.com/mohitagw15856/pm-claude-skills) | skills / plugin | MIT | [`personal/life-admin-decoders`](personal/life-admin-decoders) |
| A | [Playwright MCP](https://github.com/microsoft/playwright-mcp) | mcp | Apache-2.0 | [`personal/playwright-mcp`](personal/playwright-mcp) |
| A | [MarkItDown MCP](https://github.com/microsoft/markitdown) | mcp | MIT | [`personal/markitdown-mcp`](personal/markitdown-mcp) |
| A | [Paperless-ngx MCP](https://github.com/baruchiro/paperless-mcp) | mcp | ISC | [`personal/paperless-mcp`](personal/paperless-mcp) |
| A | [Actual Budget MCP](https://github.com/s-stefanov/actual-mcp) | mcp | MIT | [`personal/actual-budget-mcp`](personal/actual-budget-mcp) |
| A | [Todoist official MCP](https://github.com/Doist/todoist-mcp) | mcp (remote) | MIT | [`personal/todoist-mcp`](personal/todoist-mcp) |
| A | [Apple Notes MCP (sweetrb)](https://github.com/sweetrb/apple-notes-mcp) | mcp + skill | MIT | [`personal/apple-notes-mcp`](personal/apple-notes-mcp) |
| A | [Home Assistant: ha-mcp (plus official MCP Server integration)](https://github.com/homeassistant-ai/ha-mcp) | mcp | MIT | [`personal/ha-mcp`](personal/ha-mcp) |
| A | [Apple Health MCP (neiltron)](https://github.com/neiltron/apple-health-mcp) | mcp | MIT | [`personal/apple-health-mcp`](personal/apple-health-mcp) |
| B | [Garmin MCP](https://github.com/Taxuspt/garmin_mcp) | mcp | MIT | [`personal/garmin-mcp`](personal/garmin-mcp) |
| B | [Official MCP Memory server](https://github.com/modelcontextprotocol/servers/tree/main/src/memory) | mcp | MIT, transitioning to Apache-2.0 | [`personal/memory-server-official`](personal/memory-server-official) |
| B | [Graphiti MCP (Zep)](https://github.com/getzep/graphiti/tree/main/mcp_server) | mcp | Apache-2.0 | [`personal/graphiti-mcp`](personal/graphiti-mcp) |

## Core

| Tier | Pick | Type | License | Local copy |
|---|---|---|---|---|
| S | [skill-creator](https://github.com/anthropics/skills) | skill | Apache-2.0 | [`core/skill-creator`](core/skill-creator) |
| S | [document-skills (docx, pptx, xlsx, pdf)](https://github.com/anthropics/skills) | skill | Proprietary, source-available (c) Anthro | link only |
| S | [frontend-design](https://github.com/anthropics/skills) | skill | Apache-2.0 | [`core/frontend-design`](core/frontend-design) |
| S | [superpowers (brainstorming, writing-plans, executing-plans, systematic-debugging, TDD, verification-before-completion, writing-skills)](https://github.com/obra/superpowers) | collection | MIT | link only |
| S | [Anthropic official plugin marketplace (claude-plugins-official)](https://github.com/anthropics/claude-plugins-official) | collection | Apache-2.0 (repo; each plugin has its ow | link only |
| A | [canvas-design + algorithmic-art](https://github.com/anthropics/skills) | skill | Apache-2.0 | link only |
| A | [theme-factory](https://github.com/anthropics/skills) | skill | Apache-2.0 | [`core/theme-factory`](core/theme-factory) |
| A | [mcp-builder](https://github.com/anthropics/skills) | skill | Apache-2.0 | [`core/mcp-builder`](core/mcp-builder) |
| A | [Context7](https://github.com/upstash/context7) | mcp | MIT (server/CLI; hosted backend is propr | link only |
| A | [Playwright MCP](https://github.com/microsoft/playwright-mcp) | mcp | Apache-2.0 | [`core/playwright-mcp`](core/playwright-mcp) |
| A | [Filesystem MCP (reference server)](https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem) | mcp | MIT / Apache-2.0 (transition) | [`core/mcp-filesystem`](core/mcp-filesystem) |
| A | [Exa MCP](https://github.com/exa-labs/exa-mcp-server) | mcp | MIT | [`core/exa-mcp`](core/exa-mcp) |
| A | [MarkItDown MCP](https://github.com/microsoft/markitdown/tree/main/packages/markitdown-mcp) | mcp | MIT | [`core/markitdown-mcp`](core/markitdown-mcp) |
| A | [Excalidraw MCP App (official)](https://github.com/excalidraw/excalidraw-mcp) | mcp | MIT declared in package.json, but no LIC | link only |
| B | [webapp-testing](https://github.com/anthropics/skills) | skill | Apache-2.0 | [`core/webapp-testing`](core/webapp-testing) |
| B | [PAL MCP (formerly Zen MCP)](https://github.com/BeehiveInnovations/pal-mcp-server) | mcp | Apache-2.0 | [`core/pal-mcp`](core/pal-mcp) |
| B | [Desktop Commander](https://github.com/wonderwhy-er/DesktopCommanderMCP) | mcp | MIT | [`core/desktop-commander`](core/desktop-commander) |
| B | [Fetch + Sequential Thinking (reference servers)](https://github.com/modelcontextprotocol/servers) | mcp | MIT / Apache-2.0 (transition) | link only |
| B | [GitHub MCP (official)](https://github.com/github/github-mcp-server) | mcp | MIT | [`core/github-mcp`](core/github-mcp) |
| B | [Brave Search MCP](https://github.com/brave/brave-search-mcp-server) | mcp | MIT | [`core/brave-search-mcp`](core/brave-search-mcp) |
| B | [Remotion skills](https://github.com/remotion-dev/skills) | skill | No LICENSE in repo; Remotion uses the cu | link only |

## Gaps worth building

- **Classroom:** CTE lesson and unit skill: no skill knows Oregon CTE Programs of Study, AWS SENSE welding levels, NIMS machining credentials, OSHA 10, or small-engine (ASE/OPEE) competencies. Fork k12-lesson-plan-creation and add references/cte.md plus a standards file; reuse its docx renderer and eval rubrics.
- **Classroom:** Shop safety test and machine sign-off skill: generate per-machine safety quizzes (text2qti or New Quizzes via bruchris MCP), demo checklists, and track sign-offs in Canvas outcomes or a local CSV so students cannot run a machine until passed.
- **Classroom:** Parent and guardian communication skill: nothing K-12 specific exists. Should draft ParentSquare/Canvas-inbox messages from anonymized Canvas data, apply district tone and translation (Spanish), and re-identify locally only at send time.
- **Classroom:** IEP/504 accommodation skill (local only): keep accommodations in a local file keyed by pseudonym, apply them automatically when generating materials, and push extended time via set_student_quiz_accommodation. Nothing like this exists; only a parent-side IEP meeting-prep skill was found on skills.lc.
- **Classroom:** Canvas quiz-to-QTI skill: a thin SKILL.md that teaches Claude the text2qti syntax, runs it, and validates the zip would close the loop; no maintained one exists (examark is close but stale and not SKILL.md format).
- **Classroom:** Grading calibration bridge: port homework-grader's kappa calibration and the k12 eval rubrics into his Gemini swarm_evaluator.
- **Shop:** Welding Procedure Specification (WPS/PQR) generator skill. Build a skill with AWS D1.1 / D1.3 prequalified joint tables (student-level), process variables for GMAW/FCAW/SMAW/GTAW, and a printable WPS template. Pair with eq-reference for fillet weld sizing.
- **Shop:** Feeds and speeds calculator skill (mill, lathe, drill, tap, plasma cut charts). engineer-mcp and eq-reference do not cover machining. Build a deterministic Python skill: SFM tables by material and tool, RPM = SFM x 3.82 / D, chipload, tap drill charts, plasma amperage and cut speed by thickness.
- **Shop:** Small engine diagnostics and torque spec lookup. No MCP or skill for Briggs/Honda/Kohler service data. Build a local skill with a curated spec table and troubleshooting trees (no spark, no fuel, compression), plus a PDF-manual RAG using Claude's PDF skill over manuals the teacher already owns.
- **Shop:** Weld photo critique. Only research models and startups. Claude vision works natively; a skill with AWS visual inspection criteria (undercut, porosity, overlap, profile) and a rubric would help. An inspector noted on WeldingWeb you cannot emulate a CWI without one; keep it formative.
- **Shop:** SDS / OSHA / shop safety documentation. No SDS MCP. Build a skill that turns manufacturer SDS PDFs into one-page student summaries, JSA and machine-specific safety test generators (OR-OSHA and OSHA 1910 Subpart O, 1910.252 welding).
- **Shop:** G-code explainer and verifier for students. Build a skill that parses G-code offline (no machine connection), explains each block, flags missing G54/G20/G21, rapids below clearance plane, and plots the toolpath to PNG.
- **Shop:** Plasma/laser DXF and nesting. openscad-mcp and build123d export DXF; korals-ai/mcp-cad (Apache-2.0, 0 stars, Sept 2026) reads/edits DXF via ezdxf; no open nesting MCP found. Candidate: wrap SVGnest/Deepnest or a simple rectangle nester as a skill.
- **Shop:** Bend allowance / sheet metal calcs. Simple deterministic skill: K-factor tables, bend deduction, setback, press brake tonnage.
- **Shop:** Reddit sentiment. reddit.com, news.ycombinator.com, xda, makeuseof and similar sites were blocked by the egress proxy in this session; sentiment is drawn from GitHub issues and search-result summaries of articles. Re-check Reddit manually before purchase-level decisions.
- **Home:** Email triage skill. No strong free local option beyond the Gmail connector; a custom triage skill on top of it is the practical route.
- **Home:** Downloads and file organizer skill. Nothing licensed worth taking; Claude Code file access plus a short custom skill covers it.
- **Home:** Phone-reachable local memory. Local-first memory on the phone needs paid Basic Memory Cloud or a self-hosted tunnel.
- **Home:** Travel and family logistics. No dedicated open source MCP; existing Google connectors plus a skill cover most of it.
