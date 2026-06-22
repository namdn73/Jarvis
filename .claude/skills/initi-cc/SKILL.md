---
name: init-cc
description: "Comprehensive project bootstrapping skill for Claude Code. Performs a deep diagnostic interview to understand the project's purpose, tech stack, coding habits, and constraints, then automatically generates all configuration files (CLAUDE.md, .claude/settings.json, .gitignore, .env.example), initializes git, creates the skills directory, and runs a smoke test. Activate when the user says '/init-cc', 'initialize this project', 'bootstrap this repo', or 'set up this workspace'."
---
 
# init-cc: Claude Code Project Bootstrapper
 
## Overview
 
This skill transforms a blank directory or existing repository into a fully
configured Claude Code workspace. It replaces the need to manually create
configuration files by conducting a deep diagnostic interview and then
auto-generating everything.
 
## Trigger Phrases
 
Activate this skill when the user says any of the following:
- `/init-cc`
- "Initialize this project"
- "Bootstrap this repo"
- "Set up this workspace"
- "Run init"
## Execution Flow
 
Execute the following phases **in strict order**. Do NOT skip phases. Do NOT
begin generating files until the interview is fully complete and the user has
confirmed the summary.
 
---
 
## Phase 1: Deep Diagnostic Interview (The Grill)
 
Conduct an in-depth, structured interview with the user across 4 rounds.
Present questions using the `ask_user_input` tool with multi-select where
appropriate. Include sensible defaults but always allow write-in answers.
 
#### Round 1: Project Identity & Purpose
- What type of project is this? (Web app, CLI tool, API backend, Library/SDK,
  Mobile app, AI agent pipeline, Data pipeline, Monorepo, Other)
- Describe the project's purpose in 1–2 sentences. What problem does it solve?
- Who is the target user or audience?
- Is this a greenfield project or are we working with existing code?
- What is the scale? (Personal project, Team project, Enterprise/production)
#### Round 2: Technology Stack & Architecture
- Primary programming language(s)? (TypeScript, Python, Go, Rust, Java, etc.)
- Frontend framework? (None, React, Vue, Svelte, Next.js, etc.)
- Backend framework? (None, FastAPI, Express, Django, Flask, etc.)
- Database? (None, PostgreSQL, SQLite, MongoDB, Neo4j, Supabase, etc.)
- Package manager? (npm/pnpm/yarn, pip/uv/poetry, cargo, etc.)
- Deployment target? (Local only, Docker, Vercel, AWS/GCP, HPC/Slurm, etc.)
- Testing framework? (pytest, vitest, jest, None)
- Any specific libraries or APIs that are mandatory for this project?
#### Round 3: Coding Standards, Habits & Rules
- Code style preferences? (e.g., "Always use type hints", "Prefer functional style")
- Git commit message convention? (Conventional Commits, Free-form, Other)
- Things Claude should NEVER do in this project?
- Things Claude should ALWAYS do?
- How should Claude handle uncertainty?
  (Ask first | Make a reasonable choice and explain | Stay minimal and flag it)
#### Round 4: Claude Code Configuration
- Which tools should be explicitly **allowed**?
  Common options: `Bash`, `Read`, `Write`, `Edit`, `Glob`, `Grep`,
  `WebFetch`, `WebSearch`, `Task` (sub-agents)
- Any tools to **ban** entirely? (e.g., `WebFetch` for offline projects)
- Do you need any **MCP server** integrations? (PostgreSQL, GitHub, Slack, etc.)
- Do you want any **custom slash commands**? (e.g., `/test`, `/lint`, `/deploy`)
- Should a `skills/` directory be created for reusable Claude Code skill files?
### Interview Completion
 
After all 4 rounds, compile a **structured summary** of all answers and present
it to the user for confirmation. Ask:
 
> "Here is your project profile. Should I proceed with generating your
> workspace configuration, or would you like to adjust anything?"
 
Do NOT proceed to Phase 2 until the user explicitly confirms.
 
---
 
## Phase 2: Generate Configuration Files
 
After user confirmation, generate the following files. Adapt ALL content based
on the interview answers. Do NOT use generic templates — every file must
reflect the specific project.
 
### 2.1: CLAUDE.md
 
Create `CLAUDE.md` in the project root. Claude Code reads this automatically
at the start of every session. Structure it as follows:
 
```markdown
# [Project Name]
 
## Project Overview
[1–2 sentence description from Round 1]
 
## Tech Stack
[Structured list from Round 2]
 
## Coding Standards
[Rules and habits from Round 3, written as imperative instructions]
 
## Rules for Claude
 
### Never Do
[Non-negotiables from Round 3 as bullet list]
 
### Always Do
[Mandatory practices from Round 3 as bullet list]
 
### Uncertainty Handling
[Preference from Round 3]
 
## Common Commands
[Key commands for this stack: run, test, lint, build, deploy]
```
 
### 2.2: .claude/settings.json
 
Create the `.claude/` directory and write `settings.json`.
This is Claude Code's agent configuration file. Populate based on Round 4:
 
```json
{
  "allowedTools": ["Read", "Write", "Edit", "Bash", "Glob", "Grep", "LS"],
  "bannedTools": [],
  "mcpServers": {}
}
```
 
- Only include `mcpServers` if the user specified MCP integrations.
- Only add `bannedTools` entries the user explicitly requested.
- Add `"Task"` to `allowedTools` if sub-agents were enabled.
- For custom slash commands, create `.claude/commands/<name>.md` files —
  each file's content is the instruction Claude runs when the user types `/<name>`.
### 2.3: .env.example
 
Generate only if the project has secrets, API keys, or env-specific config.
Every value must be a descriptive placeholder, never a real secret.
 
```
# [Project Name] — Environment Variables
# Copy to .env and fill in real values. Never commit .env.
 
DATABASE_URL=postgresql://user:password@localhost:5432/mydb
OPENAI_API_KEY=sk-...
```
 
Skip this file entirely if the project has no external services or secrets.
 
### 2.4: .gitignore
 
Generate a `.gitignore` tailored to the detected stack. Always include:
- `.env`
- OS files: `.DS_Store`, `Thumbs.db`
- IDE folders: `.idea/`, `.vscode/`
- Language-specific build outputs and cache dirs (e.g., `__pycache__/`,
  `node_modules/`, `dist/`, `.pytest_cache/`, `.ruff_cache/`)
- Any secrets or credential files implied by the mentioned tools
### 2.5: skills/ directory (optional)
 
If the user requested a skills directory, create:
```
skills/
└── README.md   ← brief note on what skill files are and how to add them
```
 
---
 
## Phase 3: Optional Git Initialization
 
If the project is greenfield (no existing git repo), ask:
 
> "Should I run `git init` and make an initial commit with these config files?"
 
If yes → run `git init`, stage only the generated files (never `.env`),
and commit with: `git commit -m "chore: initialize Claude Code workspace"`
 
If the repo already exists, skip this phase entirely.
 
---
 
## Phase 4: Smoke Test
 
Run a quick check to confirm everything is in place:
 
```bash
echo "=== Claude Code workspace check ===" && \
ls CLAUDE.md .claude/settings.json && \
echo "✅ CLAUDE.md found" && \
echo "✅ .claude/settings.json found" && \
[ -f .env.example ] && echo "✅ .env.example found" || echo "⏭  .env.example skipped" && \
[ -d skills ] && echo "✅ skills/ directory found" || echo "⏭  skills/ directory skipped" && \
echo "=== Done ==="
```
 
Report results. Fix anything missing before completing.
 
---
 
## Phase 5: Handoff Summary
 
Present a clean completion message:
 
```
✅ Claude Code workspace initialized for [Project Name]
 
Generated:
  CLAUDE.md                     — Primary Claude context (auto-loaded each session)
  .claude/settings.json         — Tool permissions & MCP config
  .gitignore                    — Stack-tailored ignore rules
  .env.example                  — Env variable template        [if applicable]
  .claude/commands/<name>.md    — Custom slash commands        [if applicable]
  skills/                       — Skill drop-in directory      [if applicable]
 
Next steps:
  1. Review CLAUDE.md and tweak any rules that don't fit yet
  2. Copy .env.example → .env and fill in real values
  3. Start your Claude Code session — CLAUDE.md loads automatically
```