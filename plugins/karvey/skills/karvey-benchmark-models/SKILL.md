---
name: karvey-benchmark-models
description: Cross-model benchmark for the Karvey method. Side-by-side comparison of models (e.g. Claude vs GPT vs Gemini) on a skill or task — latency, tokens, cost, and optional LLM-judged quality. Triggers include "karvey benchmark models", "comparar modelos", "compare models", "benchmark de modelos", "model benchmark", "qué modelo conviene", "which model to use", "latencia tokens costo", "latency tokens cost".
allowed-tools: Read, Bash, Glob, Grep, Agent
argument-hint: [task or skill] [--models <list>]
---

# Karvey — Model Benchmark (cross-model)

**CROSS-CUTTING SKILL of the Karvey Method.** It is a **support layer, NOT a phase.** It does not advance or modify the method's cycle: **it never touches `spec.json:phase`**. It can be invoked at any time without altering the project's state.

Inspired by gstack `/benchmark-models`: a side-by-side comparison of models (for example Claude vs GPT vs Gemini) over the same skill or task, measuring latency, tokens, cost, and, optionally, quality judged by an LLM.

## Purpose

Decide **with data** which model is best for a given task or skill in the project. Instead of choosing a model by intuition or habit, this skill runs the same task across several models and delivers an objective comparison table plus a well-founded recommendation.

It is a **meta / diagnostic** skill: it observes and measures, but **it does not modify the project's code** or produce artifacts from the method's phases. It generates no commits, does not change the solution's files, does not advance the phase.

## Steps

1. **Define the task and the models to compare.**
   - Identify the target task or skill (from the argument or by asking the user).
   - Detect the model CLIs available in the environment: `claude`, `codex`/`gpt`, `gemini`, etc.
   - Degrade gracefully: if a CLI is not accessible, exclude it from the benchmark and warn. Compare only the models actually available.

2. **Run the same task on each model.**
   - Use exactly the same prompt/input for all, so the comparison is fair.
   - Run in isolation per model and capture the full output of each one.

3. **Measure latency, tokens, and cost.**
   - Latency: wall-clock time of each run.
   - Tokens: input + output reported by each CLI.
   - Cost: estimate from tokens and each model's current price.

4. **(Optional) Quality judged by an LLM-judge.**
   - If quality needs to be evaluated, use a model as judge to score the outputs against an agreed rubric (accuracy, completeness, format, etc.).
   - Keep the judge fixed and the rubric explicit so the scores are comparable.

5. **Comparison table + recommendation.**
   - Present a side-by-side table: model, latency, tokens, cost, and (if applicable) quality.
   - Close with a clear recommendation of which model is best for that task and why (cost/quality/latency balance per the objective).

## Reminders

- **Does not advance the phase.** This skill never writes `spec.json:phase` or triggers method transitions.
- **Does not touch the project's code.** It only reads, runs test runs, and reports.
- It is invocable at any point in the Karvey cycle as support for decision-making.

---
*Part of the Karvey™ Method — © HainTech, by Mauricio Quezada Ibáñez · Apache 2.0 · see `karvey/LICENSE` and `karvey/TRADEMARK.md`.*
