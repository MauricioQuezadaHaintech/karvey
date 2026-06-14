---
name: karvey-devex
description: Developer-experience reviewer for the Karvey method. Walks the actual onboarding flow, measures time-to-hello-world, finds friction points and "docs lies". Plan-stage and live modes. Triggers include "karvey devex", "developer experience", "onboarding", "time to hello world", "fricción", "friction", "DX review".
allowed-tools: Read, Bash, Glob, Grep, Agent
argument-hint: [--mode plan|live]
---

# Karvey DevEx — DX Reviewer

> **CROSS-CUTTING SKILL of the Karvey™ Method.** This is a **support layer**, NOT a phase.
> It does NOT modify `spec.json:phase`. It does NOT advance the method's flow. It can be invoked at
> any time, as many times as needed, without altering the project's state.

Inspired by gstack `/plan-devex-review` + `/devex-review`.

## Purpose

Measure and improve the **experience of whoever adopts or uses the project** (developer experience).
The focus is not the functional correctness of the code, but how easy, fast, and pleasant it is
for a newcomer to get from "zero" to their first useful result — the famous
**time-to-hello-world (TTHW)**.

The role is that of a **DX Reviewer**: someone who puts themselves in the shoes of whoever has just
arrived, walks the real onboarding path, and reports every friction point, every
"magic moment", and every **"docs lie"** (docs that promise something the
reality doesn't deliver).

### Two modes

| Mode | When | What it does |
|------|------|--------------|
| **`plan`** | There's a plan/architecture but no running implementation yet | Design-level review: estimates the expected TTHW, identifies anticipated friction and the "magic moments" the design should deliver. |
| **`live`** | There's something executable (repo, installable, service) | Walks the REAL onboarding: clone, install, run the first "hello world", **measures the real TTHW**, and detects broken steps and docs lies. |

If `--mode` is not passed, infer it: if there's an executable artifact available → `live`;
if there's only a plan/spec/architecture → `plan`.

### Three lenses (always apply all three)

1. **Expansion (what's missing)** — gaps in the path: undocumented steps, hidden
   prerequisites, configuration nobody explained, cases the onboarding ignores.
2. **Polish (what to refine)** — things that work but scrape: unclear error messages,
   confusing names, long commands, bad defaults, noisy output, copy that could be better.
3. **Triage (what's critical)** — what blocks or drives away the adopter: what makes someone
   quit before the first success. This is what gets fixed first.

## Steps

### `plan` mode

1. **Read the project's plan / architecture / spec** (`spec.json`, `requirements`,
   `architecture`, design READMEs, mockups). Identify who the target adopter is
   (internal dev? external integrator? technical end user?).
2. **Trace the expected path** from "I discovered the project" to "I got my first
   useful result". List each anticipated step: install, configure, authenticate,
   first command/call, first output.
3. **Estimate the expected TTHW** and mark where the design introduces unnecessary friction
   (avoidable manual steps, heavy dependencies, prior configuration, secrets to
   obtain).
4. **Identify the "magic moments"** the design should produce — the instant when
   the adopter says "ah, this actually works". Verify the plan delivers them early.
5. **Apply the three lenses** (Expansion / Polish / Triage) over the design.
6. **Report** prioritized findings with concrete recommendations (see format below).

### `live` mode

1. **Start from true zero.** Simulate a clean environment. If possible, use a
   subagent (`Agent`) with instructions to "assume nothing, just follow the documentation
   literally" to walk the onboarding without the bias of someone who already knows the project.
2. **Walk the REAL onboarding following ONLY the documentation**, step by step:
   clone → install → configure → first "hello world". **Time it** from the start
   to the first useful result → that's the **real TTHW**.
3. **Note every "docs lie"**: every time a command, path, variable
   name, expected output, or prerequisite in the docs **does not match reality**.
   Cite the doc, the command executed, and what actually happened.
4. **Record the broken steps**: commands that fail, missing dependencies, implicit
   undocumented steps, errors that require external knowledge to resolve.
5. **Locate the true "magic moment"** and measure how much it costs to reach it. If it arrives
   late or never, that's critical Triage.
6. **Apply the three lenses** over the real experience lived.
7. **Report** prioritized findings with recommendations (see format below).

### Report format (both modes)

- **DX verdict** + **TTHW** (estimated in `plan`, measured in `live`).
- **Critical (Triage)** — what blocks or scares off the adopter. Fix first.
- **Friction (Polish)** — what scrapes but doesn't block.
- **Gaps (Expansion)** — what's missing.
- **Docs lies** — only in `live`: doc vs. reality, with citation.
- **Magic moments** — where they are and whether they arrive in time.
- Each finding with: location, impact on the adopter, and an actionable recommendation.

## Reminders

- **Does not advance the phase.** Do not touch `spec.json:phase` or mark anything as completed in the
  method's flow. This skill only observes, measures, and recommends.
- It is **read-only over the method's state**: it can run onboarding commands in
  `live` (install, run), but it does not edit the project's code or its spec.
- It can be run as many times as wanted, in any phase of the project.

---
*Part of the Karvey™ Method — © HainTech, by Mauricio Quezada Ibáñez · Apache 2.0 · see `karvey/LICENSE` and `karvey/TRADEMARK.md`.*
