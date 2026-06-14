---
name: karvey-scrape
description: Web data extractor for the Karvey method. Pulls data from a web page; first call prototypes the extraction, then codifies it into a reusable, tested script/skill for fast re-runs. Triggers include "karvey scrape", "scraping", "extraer datos web", "extract web data", "scrapear", "scrape", "codificar skill", "codify skill", "skillify".
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
argument-hint: [url] [--codify]
---

# karvey-scrape

**CROSS-CUTTING SKILL of the Karvey™ Method.** It is a **support layer, NOT a phase**. It does not change `spec.json:phase` or advance the method's flow. It can be invoked from any phase when you need to extract data from a web page and, optionally, leave that extraction codified as a reusable artifact.

Inspired by gstack's `/scrape` + `/skillify`: it combines a **web extractor** (quick prototype) with a **skill codifier** (reusable script + test + fixture).

## Purpose

- **Prototype**: on the first call, extract the requested data from the target page. When the content is dynamic or requires interaction (JS, login, pagination, scroll), use the available browse runtime; for static HTML, `curl`/`fetch` + parsing is enough.
- **Codify (`--codify` / skillify)**: synthesize from the prototype a **reusable script + test + fixture**, run the test, and **ask for confirmation before committing**.
- **Result**: repeatable, fast extractions for recurring intents, without having to rediscover selectors or logic each time.

## Steps

### 1. Prototype (first call)

1. Receive the `[url]` and the description of the data to extract.
2. Determine the nature of the page:
   - **Static** → download HTML and parse (CSS/XPath selectors, scoped regex, embedded JSON).
   - **Dynamic / interactive** → use the browse runtime (navigate, wait for selectors, scroll, pagination, login if applicable).
3. Extract the requested data and present it to the user in a structured format (JSON/table).
4. Record the relevant details of the extraction: URL, selectors/queries, navigation steps, output format. This is the basis for codification.

### 2. Codify (`--codify` / skillify)

When `--codify` is passed (or the user asks to "codify skill" / "skillify"):

1. **Synthesize the reusable script** from the prototype: parameterize URL/inputs, encapsulate selectors and navigation steps, define the output contract.
2. **Generate a test** that validates the extraction against a **fixture** (snapshot of the HTML/response captured in the prototype), so the test is deterministic and does not depend on the network.
3. **Run the test** and adjust until it passes.
4. **Ask for explicit confirmation before committing** the script + test + fixture.

## Rules

- **Respect sites' terms of use and `robots.txt`.** Do not use this skill for abusive scraping, evasion of protections, or unauthorized mass collection.
- **Does not advance the phase.** It's a support layer; never modify `spec.json:phase` from here.
- Keep fixtures scoped and tests deterministic (no network calls in the test).
- Do not commit anything without the user's confirmation.

---
*Part of the Karvey™ Method — © HainTech, by Mauricio Quezada Ibáñez · Apache 2.0 · see `karvey/LICENSE` and `karvey/TRADEMARK.md`.*
