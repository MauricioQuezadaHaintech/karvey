---
name: karvey-investigate
description: Karvey support — a root-cause report: no fix without investigation (dates the symptom, what changed, data flow, hypotheses). Triggers include "karvey investigate", "investigar bug", "por qué falla", "why does it fail".
allowed-tools: Read, Bash, Glob, Grep, Agent
argument-hint: [symptom description]
---

# Karvey Investigate — Root-Cause Analysis

## Purpose

A **cross-cutting** skill of the Karvey Method: a debugging and root-cause-analysis support layer (the Debugger role, inspired by gstack `/investigate`). **It is NOT a phase of the linear pipeline**: it does not modify `spec.json:phase` nor advance the phase flow. It is invoked any time a symptom, bug or unexpected behavior shows up, and when it finishes the pipeline continues exactly where it was.

**Iron Law:** NEVER apply fixes without first investigating the root cause. The investigation produces evidence and a recommendation; the fix is applied by `karvey-impl`, respecting the corresponding gates.

It is **stack-agnostic**: it uses the target's real runtime (see `../karvey/rules/targets.md`), whether it's Python/Azure Functions, Vue, SQL Server, Node-RED, Asterisk, etc.

## Steps

1. **Capture the exact symptom, how to reproduce it, and WHEN it started.**
   - Write down the observed behavior vs. the expected one, the literal error message, stack trace, exit code, and the minimal steps to reproduce.
   - If there is no reliable repro, get one before continuing. Without a repro there is no serious investigation.
   - **Date the symptom.** Get the timestamp of the report and, if possible, of the first occurrence. Ask the reporter if it is not in the ticket. This gives you the **incident window** (first occurrence → report), and steps 2 and 3 are useless without it. An investigation that never establishes a date is not an investigation; it is a code review.

2. **Check what is already known before reading any code.**
   - Read the incident tracker (`docs/bugs_dev_testing.md`, `incidents-index.md` — see `../karvey/rules/incident-tracking.md`): this symptom may already be diagnosed, or reopened.
   - Read the engineering standards (`../karvey/rules/engineering-standards.md`) for the layer involved: a known gray zone or a documented migration often IS the explanation.
   - Skim the team's `CHANGELOG.md` for the incident window.
   - The team's accumulated knowledge is a first-class source of evidence. Skipping it means re-deriving from scratch a root cause somebody already paid for.

3. **Ask "what CHANGED?" before "what is WRONG?".**
   - For any symptom that is new or recently reported, the causal question is historical, not static. Before reading source code, inspect the incident window: `CHANGELOG.md` entries, `git log` (including `git log -S` for the symbol involved), merges to the deploy branches, releases, **and changes outside the application code** — configuration, security headers/CSP, secrets and their rotation, infra, feature flags, external provider or quota changes.
   - Only after this, move on to reading code. Most recent symptoms are explained by a recent change, and that change is frequently not in the repo you are staring at.

4. **Trace the data flow / relevant code path.**
   - Use Grep/Glob to locate the entry point and follow the data flow down to the symptom.
   - Read (Read) the files involved end to end along the path: input → transformations → output.
   - Identify the boundaries (SP calls, webhooks, external APIs, queues/events) where the data can get corrupted or lost.
   - **The path does not stop at the repo boundary.** Follow it into whatever component actually holds the next hop — the other repo, the SP, the gateway, the provider's configuration. If a repo you need is not available to you, say so explicitly and name what you would inspect; do not silently downgrade the conclusion to what happened to be reachable.

5. **Formulate explicit hypotheses.**
   - Write each hypothesis as a falsifiable claim: "X fails because Y".
   - Prioritize by likelihood and by verification cost (verify the cheapest and most likely first).

6. **Test each hypothesis with evidence.**
   - Confirm or rule out with concrete evidence: logs, temporary prints/traces, read queries, state inspection, and **reproduction in the target's real runtime** (see `../karvey/rules/targets.md`).
   - Each hypothesis is closed with a verdict: confirmed / ruled out, and the evidence that backs it.
   - Do not mix several diagnostic changes at once: change one variable at a time so the signal is not contaminated.
   - **Never state what a symbol does without opening it.** Helpers, wrappers and loggers defined inside the project are the usual trap: their behavior is a project decision, not a language default. If a claim in the report depends on what `logger.error`, a retry helper or a guard actually does, read its definition and cite file and line. An unread assumption is not evidence.

7. **Causal-coherence check — this is a gate, not a formality.**
   - Before declaring a root cause, confirm it explains the symptom **in time**: a cause that predates the incident window cannot by itself explain a symptom that started inside it.
   - If the finding turns out to be pre-existing ("this has been here since the first commit"), then it is **latent fragility, not the cause**. That is a valid, reportable finding — but the investigation is not finished: something recent turned a latent weakness into a live failure. Go back to step 3 and find the trigger.
   - State the verdict explicitly in the report: *cause* (explains the window) vs. *contributing fragility* (made the failure worse or silent). Confusing the two sends the team to fix something real that will not stop the incident.

8. **Stop after ~3 failed attempts.**
   - If after ~3 hypothesis-test cycles the root cause is still not reached, **stop and ask for help** instead of continuing blindly or firing off speculative fixes.
   - Report what was ruled out, what is still uncertain, and what information or access is missing to move forward.

9. **Report the root cause with evidence and a fix recommendation.**
   - Deliver: the incident window, the identified root cause, the evidence that supports it, the impact scope, and the fix recommendation.
   - Separate **root cause** from **contributing fragility**, and **verified fact** from **open hypothesis** — each labeled, never blended into one narrative.
   - **Before recommending a mechanism, check whether the codebase already has it.** Retry/backoff, reconnection, degraded-state indicators, circuit breakers: a sibling module has usually solved it already. Cite that implementation as the pattern to follow instead of designing a new one; consistency beats novelty and the existing one is already battle-tested.
   - **Do not apply the fix here.** The fix is executed by `karvey-impl`, respecting the method's gates.

## Constraints

- It does not advance or change the pipeline phase (`spec.json:phase` stays intact).
- It does not apply corrective changes; it only diagnoses and recommends.
- Temporary diagnostic changes (prints, traces) must be reverted or flagged so that `karvey-impl` cleans them up.
- **No undated investigation.** Without an incident window there is no causal claim — at most a list of weaknesses.
- **No pre-existing finding may be reported as the cause of a new symptom** without a trigger that explains the window.
- **No claim about a symbol's behavior without having read its definition**, cited by file and line.

---
*Part of the Karvey™ Method — © HainTech, by Mauricio Quezada Ibáñez · Apache 2.0 · see `karvey/LICENSE` and `../karvey/TRADEMARK.md`.*
