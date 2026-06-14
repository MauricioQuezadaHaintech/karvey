---
name: karvey-second-opinion
description: Independent cross-model code review for the Karvey method. Get an adversarial second opinion from a different AI model (e.g. Claude vs GPT/Codex/Gemini). Three modes: Review (PASS/FAIL), Challenge (adversarial), Consult. Triggers include "karvey second opinion", "segunda opinión", "cross-model review", "revisión independiente", "codex", "otro modelo".
allowed-tools: Read, Bash, Glob, Grep, Agent
argument-hint: [--mode review|challenge|consult] [<file or diff>]
---

# Karvey — Second Opinion (cross-model reviewer)

## Purpose

This is a **cross-cutting** skill of the Karvey Method: a **support layer, NOT a phase**. It does not change `spec.json:phase` nor advance the method's flow. It can be invoked at any time without altering the state of the Karvey project.

The goal is to obtain an **independent cross-model second opinion**: asking an AI model *different* from the current one (for example Claude reviewing GPT/Codex/Gemini's work, or vice versa) to look at the same code with fresh eyes. Model diversity catches failures that a single model, due to its own biases and blind spots, cannot see on its own.

It is especially useful **before releasing something sensitive**: production changes, security logic, data handling, migrations, or anything high-impact where a single pair of eyes is not enough.

Inspired by gstack's `/codex` pattern: invoke an external reviewer to cross-check.

### What this skill does NOT do

- **It does NOT replace `karvey-qa`'s safety gate.** It is a complement. This skill's verdict alone does NOT approve anything for release.
- **It does NOT advance the phase** of the Karvey Method nor modify `spec.json`.
- **It is NOT the final authority**: it is one more input to the human decision.

## Modes

| Mode | What it does | When to use it |
|------|----------|---------------|
| **Review** | Structured review with a **PASS / FAIL** verdict and a list of prioritized findings. | Before releasing; standard quality check. |
| **Challenge** | **Adversarial** review: the external model actively tries to refute, break, or find the edge case that takes down the solution. | When something "looks fine" but the cost of being wrong is high. |
| **Consult** | Open conversation, no verdict. Design questions, trade-offs, alternatives. | Exploration, architecture doubts, comparing approaches. |

Default mode if not specified: **Review**.

## Steps

### 1. Identify the diff / files to review

Determine the exact scope of the review:

- If the user passed a file or path as an argument → that is the scope.
- If not, get the current diff of the work in progress:
  ```bash
  git diff
  git diff --staged
  git diff origin/dev...HEAD   # or the corresponding base branch
  ```
- Gather the minimal necessary context: the diff, the touched files, and the requirement/objective the code must meet (read `spec.json` or the Karvey task if it exists).

### 2. Invoke a model different from the current one

The key is **model diversity**. Detect what is available and degrade gracefully:

1. **External CLI of another model** (preferred). Detect whether it exists on the system:
   ```bash
   command -v codex   2>/dev/null && echo "codex disponible"
   command -v gemini  2>/dev/null && echo "gemini disponible"
   command -v llm     2>/dev/null && echo "llm disponible"
   ```
   If one is available, invoke it passing the diff/context and the prompt according to the mode. This gives a genuinely cross-model opinion.

2. **Graceful degradation (fallback)**: if NO CLI of another model is accessible, use a subagent (`Agent`) with an **explicit adversarial prompt** that instructs it to act as an independent, skeptical reviewer — explicitly looking for what the original author overlooked. Make it clear in the report that this was an intra-model fallback (same model family), so the real diversity is lower.

The prompt to the external reviewer must include, according to the mode:
- **Review**: "You are an independent reviewer. Evaluate this change against the requirement. Deliver a PASS or FAIL verdict and prioritized findings (blocking / major / minor)."
- **Challenge**: "You are an adversarial reviewer. Your job is to try to break this solution: find edge cases, fragile assumptions, race conditions, security or data failures. Assume there is a bug and look for it."
- **Consult**: "Let's talk openly about this design. What trade-offs do you see? What alternatives would you consider?"

### 3. Consolidate and compare against the own review

- Take the external model's findings.
- Contrast them with the own review (the current model's).
- Classify each point into: **agreements** (both models see it), **discrepancies** (one yes, the other no), and **new findings** that only the external model raised.

### 4. Report

Deliver a clear report with:
- **Mode used** and **which external model** was invoked (or whether it was an intra-model fallback).
- **Verdict** (in Review/Challenge modes): PASS / FAIL — remembering it is NOT release approval on its own.
- **Agreements**: findings where both models concur (high confidence).
- **Discrepancies**: where the opinions differ, with the reasoning behind each position.
- **New findings**: what only the second model detected.
- **Recommendation**: what to bring back to `karvey-qa`'s gate and to the human decision.

## Final reminder

This skill **complements, does not replace** `karvey-qa`'s safety gate. A favorable second opinion does not authorize a release: the QA gate and human approval remain mandatory. And this skill **never advances the phase** of the Karvey Method.

---
*Part of the Karvey™ Method — © HainTech, by Mauricio Quezada Ibáñez · Apache 2.0 · see `karvey/LICENSE` and `karvey/TRADEMARK.md`.*
