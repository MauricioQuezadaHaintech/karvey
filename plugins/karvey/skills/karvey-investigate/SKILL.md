---
name: karvey-investigate
description: Systematic root-cause debugging for the Karvey method. Iron Law — no fixes without investigation first. Traces data flow, forms and tests hypotheses, stops after repeated failures. Triggers include "karvey investigate", "investigar bug", "root cause", "depurar", "por qué falla", "debugging".
allowed-tools: Read, Bash, Glob, Grep, Agent
argument-hint: [symptom description]
---

# Karvey Investigate — Root-Cause Analysis

## Purpose

A **cross-cutting** skill of the Karvey Method: a debugging and root-cause-analysis support layer (the Debugger role, inspired by gstack `/investigate`). **It is NOT a phase of the linear pipeline**: it does not modify `spec.json:phase` nor advance the phase flow. It is invoked any time a symptom, bug or unexpected behavior shows up, and when it finishes the pipeline continues exactly where it was.

**Iron Law:** NEVER apply fixes without first investigating the root cause. The investigation produces evidence and a recommendation; the fix is applied by `karvey-impl`, respecting the corresponding gates.

It is **stack-agnostic**: it uses the target's real runtime (see `karvey/rules/targets.md`), whether it's Python/Azure Functions, Vue, SQL Server, Node-RED, Asterisk, etc.

## Steps

1. **Capture the exact symptom and how to reproduce it.**
   - Write down the observed behavior vs. the expected one, the literal error message, stack trace, exit code, and the minimal steps to reproduce.
   - If there is no reliable repro, get one before continuing. Without a repro there is no serious investigation.

2. **Trace the data flow / relevant code path.**
   - Use Grep/Glob to locate the entry point and follow the data flow down to the symptom.
   - Read (Read) the files involved end to end along the path: input → transformations → output.
   - Identify the boundaries (SP calls, webhooks, external APIs, queues/events) where the data can get corrupted or lost.

3. **Formulate explicit hypotheses.**
   - Write each hypothesis as a falsifiable claim: "X fails because Y".
   - Prioritize by likelihood and by verification cost (verify the cheapest and most likely first).

4. **Test each hypothesis with evidence.**
   - Confirm or rule out with concrete evidence: logs, temporary prints/traces, read queries, state inspection, and **reproduction in the target's real runtime** (see `karvey/rules/targets.md`).
   - Each hypothesis is closed with a verdict: confirmed / ruled out, and the evidence that backs it.
   - Do not mix several diagnostic changes at once: change one variable at a time so the signal is not contaminated.

5. **Stop after ~3 failed attempts.**
   - If after ~3 hypothesis-test cycles the root cause is still not reached, **stop and ask for help** instead of continuing blindly or firing off speculative fixes.
   - Report what was ruled out, what is still uncertain, and what information or access is missing to move forward.

6. **Report the root cause with evidence and a fix recommendation.**
   - Deliver: identified root cause, the evidence that supports it, the impact scope, and the fix recommendation.
   - **Do not apply the fix here.** The fix is executed by `karvey-impl`, respecting the method's gates.

## Constraints

- It does not advance or change the pipeline phase (`spec.json:phase` stays intact).
- It does not apply corrective changes; it only diagnoses and recommends.
- Temporary diagnostic changes (prints, traces) must be reverted or flagged so that `karvey-impl` cleans them up.

---
*Part of the Karvey™ Method — © HainTech, by Mauricio Quezada Ibáñez · Apache 2.0 · see `karvey/LICENSE` and `karvey/TRADEMARK.md`.*
