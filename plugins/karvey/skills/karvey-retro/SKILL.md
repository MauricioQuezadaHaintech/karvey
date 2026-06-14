---
name: karvey-retro
description: Team-aware retrospective for the Karvey method. Per-person breakdowns, shipping streaks, test-health trends, and growth opportunities from commit history and work patterns. Triggers include "karvey retro", "retrospectiva", "retrospective", "retro semanal", "weekly retro", "velocity", "qué mejorar", "what to improve", "review de equipo", "team review".
allowed-tools: Read, Bash, Glob, Grep, Agent
argument-hint: [--since <date/range>] [<repo>]
---

# Karvey Retro — Team retrospective

## Purpose

**CROSS-CUTTING SKILL of the Karvey Method.** It is a support layer, **NOT a phase**: it does not change `spec.json:phase` or advance the cycle. It can be invoked at any time without altering the project's state.

Inspired by gstack `/retro`, its goal is to **learn from the cycle at the team and person level, in order to improve**. It looks at the work history (commits, authors, frequency, test health) and produces a retrospective with a per-person breakdown, shipping streaks, trends, and concrete growth opportunities.

The focus is **constructive, improvement-oriented — never blame**. It respects people's privacy: the tone is one of learning, not punitive evaluation.

## Steps

### 1. Analyze the git history

Walk the repos declared in `project.json:repos` and extract the activity for the requested range (default: the last cycle / last week; honor `--since` if provided).

- Commits per author, frequency, and temporal distribution.
- Files/areas touched by each person.
- Size of the changes (lines added/removed) as a signal of magnitude, not as a productivity metric.

```bash
# For each repo in project.json:repos
git -C <repo> log --since="<range>" --pretty='%an|%ad|%s' --date=short --no-merges
git -C <repo> shortlog -sne --since="<range>" --no-merges
```

### 2. Cross-reference with test health and spec/docs progress

- Lean on **karvey-health** (if available) for the cycle's test-health trend.
- Cross-reference the activity with the progress reflected in `docs/` and the spec (which requirements/tasks were closed, what's still pending).
- Look for signals: tests that broke and got fixed, fragile areas, debt that reappears cycle after cycle.

### 3. Generate the breakdown

Produce, from the data above:

- **Per person:** what they worked on, their shipping streak, their trend relative to previous cycles.
- **Shipping streaks:** continuity and consistency of the team's work delivery.
- **Trends:** test health going up/down, velocity, focus vs. spread.
- **Growth opportunities:** areas where each person/team can improve, in supportive language.

### 4. Present the retro with concrete actions

Deliver the retrospective with:

- Cycle summary (what went well, what was hard).
- Breakdown per person and per team.
- **Concrete, actionable items** for the next cycle (no generalities).
- A constructive tone throughout.

## Hook into the cycle

This skill **can be hooked into the cycle closeout in karvey-archive (PHASE 12)** as the cycle's learning step. Even so, **it does not advance the phase**: `spec.json:phase` stays intact before and after running the retro.

## Privacy and tone

- Focus on **improvement, not blame**.
- Constructive language; the metrics are signals for conversation, not for ranking people.
- Do not expose sensitive data beyond what's necessary for the team retrospective.

---
*Part of the Karvey™ Method — © HainTech, by Mauricio Quezada Ibáñez · Apache 2.0 · see `karvey/LICENSE` and `karvey/TRADEMARK.md`.*
