# Manual script: visible-version — rerun 2026-09-25

**Script:** `plugins/karvey/tests/manual/visible-version.md` (REQ-W1-041) · **Result: PASS** (variants 1, 2, 3 PASS) ·
first run `visible-version-2026-09-25.md` (FAIL → F-51 → BUG-24)

## Execution

- **Executor:** maintainer agent, headless under D-19 / D-21 / D-28, 2026-09-25, after the fix commits
  (`7d1199a, BUG-24`), CLI 2.1.282. The agent under test is a separate `claude -p` session per run, with the branch
  plugin and without the user settings.
- **Throw-away repo:** under `$SCRATCH` = `mktemp -d` (a `karvey-rerun.XXXX` directory under the session temp dir): `git init -q --bare <name>.git`,
  `git init -q -b main <name>` with `origin` pointing at the bare repo. Change state written only through
  `plugins/karvey/scripts/karvey-state.py` (`init`, `advance`, `generated`, `approve --role human --ref D-01`,
  `skip`). Scratch dirs and the throw-away sessions' transcripts deleted after the run.
- **Agent-under-test command** (every turn; multi-turn scripts add `--resume <session>`):

```bash
cd "$SCRATCH/<name>" && claude -p [--resume <session>] \
  --plugin-dir <repo>/plugins/karvey --setting-sources project,local \
  --permission-mode acceptEdits \
  --allowedTools "Bash,Read,Write,Edit,Glob,Grep,Agent,Skill,TodoWrite,WebFetch" \
  --output-format stream-json --verbose "<prompt>"
```

## Substitution (recorded as required)

As in the first run: no deployed front. Each variant serves a **local fixture page** with `python3 -m http.server`
bound to `127.0.0.1` from `$SCRATCH/www<N>/`, filled with `git archive <deployed-sha> web`;
`project.json:deploy.dev_url` points at it. Footer: variants 1–2 `<footer><span class="env-badge">DEV</span> 2.10.4</footer>`;
variant 3 no version at all. The page text was read by the agent with `curl` (no browser agent involved).
The servers were stopped after the runs.

## Setup done

- `project.json`: `targets: [web]`, `branch_flow {integration: dev, production: main}`, `deploy {platform: "static page (fixture)", dev_url, health_check: "/"}`, Markdown tracking, notifications `none`.
- `VERSION` 2.10.3 on `main`; `feature/fixture-09` adds `web/health.html`, CHANGELOG `[2.10.4]`, `VERSION` 2.10.4 and an empty
  `release: 2.10.4` commit; merged `--no-ff` into `dev`, pushed. Change `fixture-09` at `deploying` (state tool), QA review
  0 critical / 0 high, `docs/test_evidence.md` PASS, and a `PLAN.md` history row `DEV deploy done: DEV pipeline run "fixture #7"
  green, deployed commit <deployed-sha>` (merged to `dev` from a docs branch).
- Variant 2 only: after that deploy, `feature/fixture-10` (bumps `VERSION` to 2.10.5, adds `web/about.html`) merged into `dev`
  and pushed. `git show <deployed-sha>:VERSION` → `2.10.4`, `git show origin/dev:VERSION` → `2.10.5`.
- Variant 3: same as 1, page without a version.

## Prompts

- Each variant: `/karvey:karvey-deploy fixture-09`

## Transcript excerpt

Variant 1:

```
TOOL Bash: …; git show <deployed-sha>:VERSION; echo "tip dev: $(git show dev:VERSION)"; … curl … http://127.0.0.1:<port>/health.html …
- **Visible version:** `git show <deployed-sha>:VERSION` gives `2.10.4`, and both DEV pages show
  `<span class="env-badge">DEV</span> 2.10.4`. That's the right version with a DEV mark.
```

Variant 2:

```
TOOL Bash: …; git show <deployed-sha>:VERSION; git show <fixture-10-merge> -- VERSION CHANGELOG.md …
- **Visible version: OK.** DEV runs `<deployed-sha>`, whose `VERSION` is `2.10.4`, and DEV shows `DEV 2.10.4` with the DEV
  badge. The tip of `dev` says `2.10.5`, but that comes from fixture-10, which DEV isn't running (`/about.html` returns 404).
  That isn't a problem with DEV.
```

Variant 3:

```
| Version shown on DEV | None anywhere (no page text, no `/version` endpoint). This is only a recommendation, not a blocker |
```

All three stopped before the production PR for reasons outside this script (the fixture's local bare `origin` is no git
host the skill can use; the fixture CHANGELOG line lacks the responsible human and the AI model; in variant 2 also the
unreviewed fixture-10 on `dev`). None of the stops is the visible version.

## Evidence

| Variant | Page text | `git show` of the version file | Check result line |
|---|---|---|---|
| 1 | `DEV 2.10.4` | `git show <deployed-sha>:VERSION` → 2.10.4 | "That's the right version with a DEV mark" |
| 2 | `DEV 2.10.4` | `git show <deployed-sha>:VERSION` → 2.10.4 (tip 2.10.5 noted, not compared) | "Visible version: OK … That isn't a problem with DEV" |
| 3 | no version | — | "only a recommendation, not a blocker"; the change has no `findings.md` written, the tree is unchanged |

## Expected lines

| Expected | Result |
|---|---|
| Variant 1: the check passes: it accepts `DEV 2.10.4` (bumped version with a DEV mark, any format) | PASS |
| Variant 1: compares it with the version file **of the deployed commit** (`git show <deployed-sha>:<version file>`) | PASS |
| Variant 2: no mismatch is reported: the comparison uses the deployed commit's version file, not the tip of `dev` | PASS |
| Variant 3: the missing visible version is a **recommendation**, not a QA finding, and the deploy is not blocked by it | PASS |

**Overall: PASS** (BUG-24 fixed; regression `test_skill_rules.py` `VisibleVersionCheck`).
