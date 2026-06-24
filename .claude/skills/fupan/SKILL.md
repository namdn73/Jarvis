---
name: fupan
description: >-
  Project retrospective (复盘) skill. Analyzes one or more @conversation
  chat histories to produce a detailed step-by-step retrospective of the
  user's vibe coding journey: what was built, how it was built, what went
  right, what went wrong, and how to improve prompting and workflow.
  Trigger when the user says '/fupan', 'do a fupan', 'retrospective',
  'review my workflow', or 'analyze my chat history'.
---

# Fupan (复盘): Project Retrospective Skill

## Overview

This skill turns completed project conversations into a structured
retrospective document. It reads the full transcript of each provided
`@conversation`, reconstructs the chronological workflow, and produces a
teaching-quality analysis covering: timeline, decisions, prompting quality,
agentic patterns, and actionable improvements.

## Trigger Phrases

Activate this skill when the user says any of the following:

- `/fupan`
- "Do a fupan"
- "Retrospective"
- "Review my workflow"
- "Analyze my chat history"
- "Summarize what we built"
- "What did we do in this project?"

## Required Inputs

The user MUST provide one or more `@conversation` mentions. Each mention
resolves to a Conversation ID that maps to a transcript file at:

```
<appDataDir>/brain/<conversation-id>/.system_generated/logs/transcript.jsonl
```

If the user does not provide any `@conversation` mentions, ask them:

> "To do a proper Fupan, I need the chat histories to analyze. Please
> mention the conversations using `@conversation` so I can read them.
> You can mention as many as you like!"

## Execution Flow

Execute the following phases **in strict order**. Do NOT skip phases.

---

### Phase 1: Extract & Reconstruct Timeline

For each provided conversation, extract all user messages from the
transcript using:

```bash
jq -c 'select(.type == "USER_INPUT") | {step: .step_index, time: .created_at, content: .content}' \
  <appDataDir>/brain/<conversation-id>/.system_generated/logs/transcript.jsonl
```

From the extracted data, reconstruct:

1. **Chronological order** of all conversations (sort by earliest timestamp).
2. **Session durations** — calculate how long each conversation lasted
   (first message → last message).
3. **Key decision points** — identify moments where the user changed
   direction, approved a plan, rejected a suggestion, or switched models.
4. **Tool/skill usage** — note which tools, skills, slash commands
   (`/goal`, `/init-agy`, `/modern-web-guidance`, etc.), and subagents
   were leveraged.

---

### Phase 2: Identify Workflow Phases

Group the timeline into logical **phases** of the project. A phase is a
distinct period of work with a clear objective. Common phase patterns
include:

- **Bootstrapping** — Project setup, config, rules
- **Research & Planning** — Exploration, architecture decisions
- **Content/Data Creation** — Writing, generating assets, populating data
- **Development** — Building features, coding, implementing
- **Iteration & Debugging** — Fixing bugs, refining UI, polish
- **Refactoring** — Restructuring, cleanup, separation of concerns
- **Presentation** — README, documentation, demo preparation

For each phase, record:

- Phase name and objective
- Start and end timestamps
- Number of user messages (interaction density)
- Key outcomes and artifacts produced

---

### Phase 3: Analyze Each Phase (The Core Analysis)

For **each phase** identified in Phase 2, produce the following structured
analysis:

#### 3a. Summary

A 2-3 sentence description of what happened in this phase.

#### 3b. What Went Right ✅

Identify and praise effective patterns, such as:

- Smart delegation (using subagents, `/goal`)
- Good architectural decisions
- Effective use of tooling
- Clear communication with the AI
- Testing before scaling (batch-first approach)

#### 3c. What Went Wrong (or Could Be Improved) ⚠️

Identify friction points, such as:

- Ambiguous prompts that caused rework
- Missing architecture decisions that led to later refactors
- Manual work that could have been automated
- Idle time during quota limits or waiting periods
- Scope creep or context switching

#### 3d. Prompting Polish (Before → After Examples)

This is the **most important** section. For each phase, find 1-2 real
prompts from the user's actual chat history and rewrite them using the
**Intent-Based Prompting** format.

Format each example as:

```
❌ Bad Example (Loose Vibe Coding):
"[exact quote from the user's actual chat history]"

✅ Good Example (Structured Vibe Coding):
> **Goal**: [What the user wants to achieve]
> **Current Issue**: [What's wrong right now — if applicable]
> **Action**: [Specific steps for the AI to take]
> **Validation**: [How to verify it worked — if applicable]
```

**Rules for prompt rewriting:**

- Always use the user's REAL prompts as the "bad" example — do NOT
  fabricate fake prompts.
- The rewritten version should preserve the user's original intent exactly
  but add structure, specificity, and validation criteria.
- Do NOT be condescending. Frame it as "here's how to get even better
  results" not "here's what you did wrong."
- Acknowledge that loose vibe coding is fine for simple tasks. The
  structured format is specifically for complex, multi-step, or
  ambiguous requests.

---

### Phase 4: Cross-Cutting Analysis

After analyzing individual phases, provide higher-level observations that
span the entire project:

#### 4a. Agentic Patterns Scorecard

Rate the user's usage of the following agentic patterns on a scale of
🌑 (not used) to 🌕 (mastered):

| Pattern | Rating | Notes |
|---------|--------|-------|
| Subagent Delegation | 🌑🌒🌓🌔🌕 | ... |
| Autonomous Execution (`/goal`) | 🌑🌒🌓🌔🌕 | ... |
| Batch Testing Before Scaling | 🌑🌒🌓🌔🌕 | ... |
| Automated Validation (CI/CD) | 🌑🌒🌓🌔🌕 | ... |
| Structured Prompting | 🌑🌒🌓🌔🌕 | ... |
| Architecture-First Thinking | 🌑🌒🌓🌔🌕 | ... |
| Model Selection Strategy | 🌑🌒🌓🌔🌕 | ... |
| Downtime Optimization | 🌑🌒🌓🌔🌕 | ... |

#### 4b. Model Switching Analysis

If the user switched between AI models during the project, analyze:

- Which models were used for which tasks?
- Was the switching strategic (e.g., fast model for simple tasks,
  thinking model for complex planning)?
- Recommendations for future model selection.

#### 4c. Time Efficiency Analysis

Calculate and present:

- Total wall-clock time across all conversations
- Estimated "hands-on" time vs. "AI working autonomously" time
- Longest idle gaps and what caused them
- Recommendations for reducing idle time

---

### Phase 5: Generate the Retrospective Document

Write the full retrospective to a file in the project root called
`[project_name]_fupan.md` (or a name the user specifies).

The document MUST follow this structure:

```markdown
# [Project Name]: Fupan (复盘) Retrospective

> A retrospective analysis of the vibe coding journey for [Project Name].
> Generated on [date].

## Project Timeline

[Mermaid Gantt chart or timeline table showing all phases]

## Phase-by-Phase Analysis

### Phase 1: [Name]
[Full analysis from Phase 3]

### Phase 2: [Name]
[Full analysis from Phase 3]

[... repeat for all phases ...]

## Cross-Cutting Analysis

### Agentic Patterns Scorecard
[Table from Phase 4a]

### Model Switching Analysis
[From Phase 4b]

### Time Efficiency Analysis
[From Phase 4c]

## Key Takeaways

[3-5 bullet points summarizing the most important lessons]

## Recommendations for Next Project

[Actionable list of what to do differently next time]
```

---

### Phase 6: Present & Discuss

After generating the document:

1. Point the user to the generated file.
2. Highlight the **top 3 most impactful improvements** they can make.
3. Ask if they want to dive deeper into any specific phase or topic.
4. Offer to update `GEMINI.md` with any new rules or practices discovered
   during the retrospective.

---

## Common Mistakes

1. **Skipping real prompt examples.** The Before → After prompt rewriting
   is the highest-value part of the Fupan. Never skip it or use
   fabricated examples.
2. **Being too harsh or too soft.** Strike a balance — celebrate what
   went well genuinely, and frame improvements as opportunities not
   failures.
3. **Ignoring the timeline.** The chronological reconstruction is critical
   for understanding how the project evolved. Don't just summarize
   topics — show the journey.
