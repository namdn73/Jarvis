# Jarvis: Fupan (复盘) Retrospective

> A retrospective analysis of the vibe coding journey for the Jarvis personal voice AI assistant.
> Generated on 2026-06-24. Based on chat histories: planning, session1, session2, session3.

---

## Project Timeline

```
| Phase                        | Description                                  | Sessions |
|------------------------------|----------------------------------------------|----------|
| Planning & Design            | 20-question design interview + /grilling     | planning |
| Environment Bootstrap        | Scaffold, deps, Python version hell          | session1 |
| Backend Core                 | config, state, DB, FastAPI skeleton          | session2 |
| Audio Pipeline               | Speaker, listener, wake word, live demo      | session3 |
| Agent & API                  | DeepAgent, tools, WebSocket, routes          | 4–5B     |
| Test Suites                  | 42 backend + 15 frontend tests               | 6, 10    |
| Frontend                     | React+Vite, canvas, UI, integration          | 7–9, 11  |
```

---

## Phase-by-Phase Analysis

---

### Phase 1: Planning & Design

**Duration:** Single session. ~30+ user messages.

**Objective:** Define every architectural decision before a single line of code is written.

#### Summary

The user started with a high-level idea ("build a Jarvis-like voice assistant") and invoked `/init-cc` followed by `/grilling`. Claude conducted a 20-question structured interview covering the full voice loop, state machine, UI aesthetic, memory model, tooling, and deployment environment. Every significant decision was justified with a recommendation and tradeoffs before the user confirmed.

#### What Went Right ✅

- **Using `/grilling` proactively.** The user didn't just say "make me a plan" — they invoked a structured stress-test. This forced 20 key decisions up front instead of discovering them painfully mid-implementation.
- **Letting Claude recommend, not just ask.** On almost every question, the user accepted the recommendation with one word. This moved faster than endless back-and-forth while still keeping the user in control.
- **Caught the Docker-on-Windows mic problem before building.** The grilling session revealed that mic access in Docker on Windows is fundamentally broken. Pivoting to native Windows before writing any code saved hours of debugging.
- **Separated UI aesthetic from functionality.** By anchoring the design to the Iron Man JARVIS visual language early ("which one looks more like Jarvis?"), the frontend direction was never in doubt later.
- **The memory model distinction was brilliant.** The user asked "is SQLite history similar to agent memory?" — this one question led to a clear, principled decision: SQLite = your personal log, AGENTS.md = agent preferences.

#### What Went Wrong ⚠️

- **Porcupine was chosen without checking its licensing status first.** The planning session recommended pvporcupine as the wake word engine and the user accepted. It was only discovered during Session 1 that Picovoice had gone enterprise-only and discontinued free access keys. A 30-second web search during the planning session would have caught this and chosen openWakeWord from the start.
- **Deployment was over-specified, then removed.** Docker was designed for two full questions (#17) before being dropped because mic access doesn't work on Windows Docker. The time spent on that discussion was wasted. A faster approach: ask the OS first, then rule out Docker.

#### Prompting Polish

```
❌ Bad Example (Loose Vibe Coding):
"i want to build jarvis - a personal voice AI assistant which can activate by
activated word and its job is to web search and show me the news or information
related to the topic i concern. I want to build it with python, langchain deepagent
(search it if you dont know), fastAPI backend, frontend (i dont know yet, suggest me).
/init-cc"

✅ Good Example (Structured Vibe Coding):
> **Goal**: Bootstrap a production-ready Claude Code workspace for Jarvis — a
>   wake-word-activated voice assistant that searches the web and displays results.
> **Known stack**: Python backend (FastAPI, uv), langchain deepagent agent,
>   React+TypeScript frontend, openai-whisper STT.
> **Unknown/need advice**: Wake word engine (free, offline), TTS solution,
>   frontend framework, deployment approach.
> **Action**: Run /init-cc to generate CLAUDE.md, settings.json, .gitignore, .env.example.
>   Then run /grilling on the full architecture before writing any code.
> **Validation**: After init, confirm CLAUDE.md has KISS/DRY standards and the correct
>   MCP server for LangChain docs.
```

The original prompt works — it triggers the right skills. But the structured version pre-answers half the interview questions and sets explicit validation criteria, cutting the design session from ~30 messages to ~15.

---

### Phase 2: Environment Bootstrap (Session 1)

**Duration:** Single session. ~80+ messages. Longest session by far.

**Objective:** Scaffold project structure, install dependencies, verify `uv sync` runs cleanly.

#### Summary

A straightforward scaffold turned into a multi-hour dependency maze. The core problem: `openai-whisper` ships only as an sdist whose `setup.py` uses a Python 3.14-incompatible `exec()/locals()` pattern. This cascaded into: wrong Python version, AV blocking freshly downloaded executables, OneDrive locking venv files, numba version conflicts, and setuptools version issues. The session also required switching from pvporcupine to openWakeWord mid-flight after discovering Picovoice had gone enterprise-only.

#### What Went Right ✅

- **Systematic diagnosis.** Each failure was correctly diagnosed: Python 3.14 exec() scoping change, AV blocking uv-downloaded executables, OneDrive locking .venv scripts. Claude didn't blindly retry the same command.
- **Correct pivot to official Python 3.12.** Rather than trying workarounds for the AV blocking issue, Claude explained exactly why Python 3.12 from the software center would be trusted, and the user installed it. Clean fix.
- **OpenWakeWord pivot handled gracefully.** When Picovoice turned out to be enterprise-only, the switch to openWakeWord was made in one commit: deps updated, CLAUDE.md updated, architecture doc updated.
- **User caught the Gemini model update.** The user independently changed the model to `gemini-3.5-flash` and asked if it was free — Claude verified via web search. This is exactly the kind of proactive checking that prevents runtime surprises.

#### What Went Wrong ⚠️

- **Excessive retry loops.** There were ~15 distinct attempts to get `uv sync` working, many of them trying minor variations on the same failing approach (setuptools versions, no-build-isolation flags, extra-build-dependencies). A faster path: identify the root cause (openai-whisper's setup.py is fundamentally incompatible with build isolation) and jump straight to the working solution (`extra-build-dependencies = ["setuptools<72"]` + `openai-whisper>=20250625`).
- **OneDrive + venv is a known hostile combination.** Multiple failures were caused by OneDrive scanning and locking newly created Python executables. This should be a permanent note in CLAUDE.md: always set `UV_PROJECT_ENVIRONMENT` outside the OneDrive path, or better, add `.venv/` to OneDrive's exclusion list before starting.
- **Picovoice was never verified as free before being recommended.** This forced a mid-session architectural change and required updating 3 files.
- **No `.python-version` check at the start.** Checking the available Python versions and their AV/OneDrive trust status at the very beginning of any new session would have saved most of the wasted time.

#### Prompting Polish

```
❌ Bad Example (Loose Vibe Coding):
"the plan is updated, check the task again and run uv sync if there is nothing left"

✅ Good Example (Structured Vibe Coding):
> **Goal**: Verify Session 1 is complete and environment is healthy.
> **Action**:
>   1. Read ImplementationPlan/general/task.md — check all Session 1 boxes are ticked.
>   2. Run `uv sync --dev` and confirm it exits with code 0.
>   3. Run `uv run python -c "import fastapi, whisper, openwakeword; print('OK')"`.
> **Validation**: All three checks pass with no errors. If uv sync fails, diagnose
>   before attempting fixes (check Python version, AV blocking, OneDrive locking).
```

The original prompt is fine for a quick status check. The structured version adds explicit validation steps so Claude doesn't mark tasks done without actually verifying them.

---

### Phase 3: Backend Core (Session 2)

**Duration:** Single session. ~30 messages. Fastest session after the scaffold.

**Objective:** Implement `config.py`, `state.py`, `db/models.py`, `db/database.py`, `main.py`.

#### Summary

The cleanest session in the project. Five files were written in parallel, a DB round-trip smoke test was run (with a tiny workaround for PowerShell multi-line string syntax), and everything was committed. The only friction was a PowerShell `SyntaxError` when trying to run multi-line Python one-liners in `uv run python -c "..."`.

#### What Went Right ✅

- **Read the plan files first.** The session prompt explicitly asked Claude to read the architecture and backend plan before implementing. This meant the output matched the spec exactly without clarifying questions.
- **Parallel file writes.** All 5 files were written in a single round, not sequentially. This is the correct pattern for independent file creation.
- **Smoke test workaround was pragmatic.** When the PowerShell inline Python had syntax issues, Claude wrote a temporary `test_session2.py` file, ran it, then deleted it. Simple and effective.

#### What Went Wrong ⚠️

- **Minor**: `datetime.utcnow()` deprecation warning appeared in the smoke test. It was noted but not fixed. A good habit is to fix deprecation warnings when you see them, not defer them.
- **Minor**: The session prompt came as a single vague instruction ("implement Session 2") rather than naming the specific files. This worked because CLAUDE.md and the plan files filled in the gap — but it relies on Claude reading the right files.

#### Prompting Polish

```
❌ Bad Example (Loose Vibe Coding):
"Read ImplementationPlan/general/architecture.md and ImplementationPlan/backend/plan.md
first, then implement Session 2 from ImplementationPlan/general/task.md"

✅ Good Example (Structured Vibe Coding):
> **Goal**: Implement Session 2 — Backend Core.
> **Files to create**: backend/config.py, backend/state.py, backend/db/models.py,
>   backend/db/database.py, backend/main.py.
> **Before starting**: Read architecture.md, backend/plan.md, and task.md.
> **Action**: Write all 5 files in parallel, then run a DB round-trip smoke test
>   (create a DbSession row, flush, verify the id is set).
> **Validation**: `uv run pytest` passes (or no tests yet — confirm import chain works
>   with `uv run python -c "from backend.main import app"`).
> **On completion**: Update task.md checkboxes and commit.
```

This is a minor improvement — the original works well. The key addition is naming the specific files and the commit instruction up front.

---

### Phase 4: Audio Pipeline (Session 3)

**Duration:** Single session. ~40 messages. First session with a real live test.

**Objective:** Implement `speaker.py`, `listener.py`, `wake_word.py` and verify with a real mic test.

#### Summary

Three audio modules were written in parallel. One missing dependency (`soundfile`) was caught and added. The server started but the `hey_jarvis_v0.1.onnx` model wasn't pre-downloaded — Claude ran `openwakeword.utils.download_models()` to fetch it, then restarted the server. The user confirmed it worked with "good it works". Session ended with the user learning how to stop and restart the server.

#### What Went Right ✅

- **Live validation was non-negotiable.** The session plan included a manual test step ("say 'hey Jarvis' → greeting plays"). Claude didn't skip it or say "it should work" — it actually ran the server and waited for user confirmation. This caught the missing ONNX model issue that unit tests would have missed.
- **The `/verify` pattern worked perfectly here.** Starting the server, monitoring output, downloading missing models, and confirming audio worked is exactly what the verify skill is designed for.
- **Clean process management.** When the server needed to be killed, Claude found the PID via `netstat -ano` and killed it cleanly — no `rm -rf` or force-deletions.

#### What Went Wrong ⚠️

- **The openWakeWord ONNX model download was not part of the plan.** It should have been. When adding a new dependency that requires pre-downloaded model files, always add a model download step to the task list.
- **The `sleep 30` pattern was blocked by the harness.** Claude tried to use `sleep 30 && tail -20 ...` to wait for the server to start, which was blocked. The correct pattern (using `run_in_background: true` and waiting for notification) had to be found by trial and error.
- **Background job approach for starting the server.** Multiple methods were tried (`Start-Process`, `Start-Job`, PowerShell background job) before settling on `run_in_background: true`. This is now known to be the correct pattern for this environment.

#### Prompting Polish

```
❌ Bad Example (Loose Vibe Coding):
"check the checklist in session 3 in task.md if you already tick all the boxes"

✅ Good Example (Structured Vibe Coding):
> **Goal**: Verify all Session 3 checkboxes in task.md are complete and accurate.
> **Action**:
>   1. Read task.md and list which boxes are ticked vs unticked.
>   2. For "Manual test: say 'hey Jarvis' → greeting plays" — if not ticked,
>      start the server with run_in_background=true, confirm it reaches
>      "[wake_word] listening for 'hey Jarvis'" in output.
>   3. If the ONNX model is missing, download it via openwakeword.utils.download_models().
> **Validation**: Server output shows "listening for 'hey Jarvis'" with no errors.
>   All 5 boxes ticked and committed.
```

---

### Phase 5: Agent, API, Tests & Frontend (Sessions 4–11)

**Note:** Chat histories for sessions 4–11 are not included in the ChatHistory folder provided. The analysis below is reconstructed from the git log and the completed task list in `task.md`.

#### Summary

From the git history, the remaining 8 sessions built out the complete system:
- **Session 4**: DeepAgent with 3 tools (Tavily search, datetime, browser opener), FilesystemBackend for AGENTS.md memory, thread_id for session recall.
- **Session 5**: WebSocket endpoint, /health, /history, /preferences routes, full pipeline wiring.
- **Session 5B**: Latency optimizations — switched to `tiny` Whisper model, sentence-streaming TTS, disabled unused DeepAgent built-in tools.
- **Session 6**: 42 backend tests across 5 test files, all passing.
- **Sessions 7–9**: Full React+Vite+TypeScript frontend — Fibonacci sphere, waveform canvas, status badge, result cards, conversation log, split IDLE/ACTIVE layout.
- **Session 10**: 15 frontend tests (Vitest), all passing.
- **Session 11**: End-to-end integration, session recall verification, frontend build, final CLAUDE.md update.

#### What Can Be Inferred ✅

- The decision to split into small, focused sessions (5B separately for optimizations, frontend split into setup/canvas/components/tests) paid off — each commit is clean and purposeful.
- 57 total tests (42 backend + 15 frontend) with all passing suggests the implementation was done carefully with validation built in throughout.
- The session recall feature (thread_id reuse within 2-hour window) was implemented at the end of session 11 in `wake_word.py` — this is noted in the final commit message, which means it was added as a polish step rather than part of the original agent plan. Good instinct to add it as integration detail.

---

## Cross-Cutting Analysis

### Agentic Patterns Scorecard

| Pattern | Rating | Notes |
|---------|--------|-------|
| Subagent Delegation | 🌒 | Not used — all work done in single conversation threads. Could have parallelized research (e.g., verifying Picovoice licensing) via a subagent. |
| Autonomous Execution (`/goal`) | 🌑 | Not used. Sessions 4–11 had clear plans that would have benefited from `/goal` to let Claude execute entire sessions without step-by-step approval. |
| Batch Testing Before Scaling | 🌔 | Good: temp smoke test files used in sessions 2–3. Each session ended with a working test before committing. |
| Automated Validation (CI/CD) | 🌒 | `uv run pytest` and `npm run test` were run manually after each session. No CI pipeline or pre-commit hooks were set up. |
| Structured Prompting | 🌓 | Planning was excellent (used `/grilling`). Implementation prompts were functional but often missing explicit validation criteria. |
| Architecture-First Thinking | 🌕 | Outstanding. The planning session resolved 20 architectural decisions before any code. CLAUDE.md and ImplementationPlan docs were created and referenced in every session. |
| Model Selection Strategy | 🌓 | gemini-2.0-flash chosen correctly for latency. Whisper was downgraded to `tiny` in Session 5B. No explicit LLM strategy for Claude itself (always used Sonnet 4.6). |
| Downtime Optimization | 🌒 | Idle time during model downloads, dependency failures, and server waits was not used productively. No parallel work streams. |

---

### Model Switching Analysis

Claude Sonnet 4.6 was used throughout all sessions. No model switching occurred for the Claude Code agent itself.

**For the Jarvis app models:**
- Gemini `gemini-2.0-flash` → later upgraded by user to `gemini-3.5-flash` (verified free tier).
- Whisper `base` → downgraded to `tiny` in Session 5B for latency reasons.

**Recommendation:** For future projects, use a fast/cheap model (like Haiku) for repetitive tasks like "check the checkboxes" or "update the task list", and reserve Sonnet/Opus for design decisions and complex implementations.

---

### Time Efficiency Analysis

**Session breakdown (estimated from message density):**

| Session | Est. Duration | Hands-on vs. AI-working |
|---------|--------------|------------------------|
| Planning | ~45 min | ~70% hands-on (Q&A format) |
| Session 1 | ~90 min | ~40% hands-on, ~60% AI retrying deps |
| Session 2 | ~20 min | ~20% hands-on, clean |
| Session 3 | ~35 min | ~30% hands-on, model download wait |
| Sessions 4–11 | ~4 hrs est. | ~15% hands-on (from clean commits) |

**Largest time sinks identified:**
1. **Dependency hell in Session 1** (~60–90 min): openai-whisper on Python 3.14/3.12, AV blocking, OneDrive locking, numba overrides. Root cause: wrong Python version + OneDrive incompatibility not pre-checked.
2. **Picovoice pivot** (~15 min): Could have been avoided with a quick licensing check during planning.
3. **Wake word model download discovery** (~10 min): Should be in the task list as a setup step.

---

## Key Takeaways

- **Architecture-first vibe coding works.** Using `/grilling` before Session 1 meant zero architectural surprises during implementation. Every "what should I use for X" decision was already made before the first file was written.

- **OneDrive + Python venv = hostile environment.** The single biggest time sink in the project was OneDrive scanning and locking `.venv` executables. Always set `UV_PROJECT_ENVIRONMENT` to a path outside OneDrive (e.g., `C:\Users\DOANN\.jarvis-venv`) or add `.venv/` to OneDrive's sync exclusion list.

- **Verify licensing before recommending dependencies.** Picovoice was recommended, accepted, planned for, and scaffolded before anyone checked if it was still free. A 10-second web search during the planning session prevents this class of mid-session pivot.

- **The "one task per session" discipline scales well.** Each session had a clear scope (one domain: audio, or agent, or frontend canvas). The small-commit pattern (10 commits for 10 sessions) made git history readable and regressions easy to bisect.

- **Validation is part of the task, not a bonus step.** Sessions where manual testing was explicitly part of the task list (Session 3 wake word test) caught real issues (missing ONNX model). Sessions without explicit manual test steps (Session 2 smoke test) relied on import checks only.

---

## Recommendations for Next Project

1. **Pre-flight check for Windows projects**: Before any `uv sync`, run a 3-point check: Python version (≥3.12, from trusted installer), `.venv` location (outside OneDrive), and AV exclusion list (add `.venv/` and the uv cache dir). Add this to CLAUDE.md.

2. **Verify all third-party dependencies are still free/available** during the planning/grilling session. Add a "dependency audit" step to `/grilling` for any library that requires an API key or account.

3. **Use `/goal` for clean sessions 4+.** Once the architecture is locked and the code patterns are established, use `/goal` with a session task list as input. Let Claude execute the full session autonomously without step-by-step approval — review the git diff at the end.

4. **Add model download steps to task lists** for any dependency that requires pre-downloading weights (Whisper, openWakeWord ONNX, etc.). These are easy to forget and cause live-test failures.

5. **Set up a pre-commit hook for `uv run pytest`** so every commit is validated automatically. This prevents the "fix the bug, forget to re-run tests" pattern.

6. **Export chat histories immediately after each session** while the `/export` command still works. The `ChatHistory/` folder already exists — rename it before running `/export` if there's a conflict (or fix the bug by using a subdirectory per session).

7. **Parallelize independent planning with background agents.** During Session 1's dependency wait time (~60 min), a background agent could have been drafting the backend plan or the architecture doc. Downtime is free parallelism.

---

*Jarvis fupan complete. 10 sessions, 57 tests, one working voice assistant.* 🎙️
