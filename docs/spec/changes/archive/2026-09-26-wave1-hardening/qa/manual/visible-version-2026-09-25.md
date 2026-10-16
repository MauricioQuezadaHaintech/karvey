# Manual script: visible-version — 2026-09-25

**Script:** `plugins/karvey/tests/manual/visible-version.md` (REQ-W1-041) · **Result: FAIL** (variants 1 and 2 FAIL → F-51; variant 3 PASS)

## Execution

- **Executor:** maintainer agent, headless under D-19 / D-28, 2026-09-25. The agent under test is a separate
  `claude -p` session per run, with the branch plugin and without the user settings.
- **Throw-away repo:** `git init -q --bare "$SCRATCH/<name>.git"`, `git init -q -b main "$SCRATCH/<name>"` with
  `origin` pointing at the bare repo. The fixture change state was written only through
  `plugins/karvey/scripts/karvey-state.py` (`init`, `advance`, `generated`, `approve --role human --ref D-01`,
  `skip`), never by hand. `$SCRATCH` is a `mktemp -d` directory, deleted after the run.
- **Agent-under-test command** (every turn; multi-turn scripts add `--resume <session>`):

```bash
cd "$SCRATCH/<name>" && claude -p [--resume <session>] \
  --plugin-dir <repo>/plugins/karvey --setting-sources project,local \
  --permission-mode acceptEdits \
  --allowedTools "Bash,Read,Write,Edit,Glob,Grep,Agent,Skill,TodoWrite,WebFetch" \
  --output-format stream-json --verbose "<prompt>"
```

## Substitution (recorded as required)

No deployed front was used. Each variant serves a **local fixture page** with `python3 -m http.server` bound to
`127.0.0.1` from `$SCRATCH/www<N>/`, filled with `git archive <deployed-sha> web`, and the scratch project's
`project.json:deploy.dev_url` points at `http://127.0.0.1:<port>/`. Footer: variants 1–2
`<footer><span class="env-badge">DEV</span> 2.10.4</footer>`; variant 3 no version at all. The page text was read
by the agent with `curl` (no browser agent involved). A first attempt served only `index.html`, so the agent
correctly reported the change's page as 404; discarded as a fixture error and re-run with the page served.

## Setup done

- `project.json`: `targets: [web]`, `branch_flow {integration: dev, production: main}`, `deploy {platform: "static page (fixture)", dev_url, health_check: "/"}`, Markdown tracking, notifications `none`.
- `VERSION` 2.10.3 on `main`; `feature/fixture-09` adds `web/health.html`, CHANGELOG `[2.10.4]`, `VERSION` 2.10.4 and an empty `release: 2.10.4` commit; merged `--no-ff` into `dev`, pushed.
  Change `fixture-09` at `deploying` (state tool), QA review with 0 critical / 0 high, `docs/test_evidence.md`
  PASS, and a `PLAN.md` history row `DEV deploy done: DEV pipeline run "fixture #7" green, deployed commit <deployed-sha>`.
- Variant 2 only: after that deploy, `feature/fixture-10` (bumps `VERSION` to 2.10.5, adds `web/about.html`)
  merged into `dev` and pushed. `git show <deployed-sha>:VERSION` → `2.10.4`, `git show origin/dev:VERSION` → `2.10.5`.
- Variant 3: same as 1, page without a version.

## Prompts

- Each variant: `/karvey:karvey-deploy fixture-09`

## Transcript excerpt

Variant 1:

```
**Why I stopped** The DEV page footer shows `<span class="env-badge">DEV</span> 2.10.4`. The versioning rule says
DEV must show the dev version (`2.10.4-dev.{build}+{sha}`), and a mismatch counts as a finding. …
Send the version-label issue to `/karvey-iterate fixture-09` as a bug.
```

`git show` commands run: `<sha> --stat`, `dev:web/index.html`, `<sha>:web/index.html`; none of the version file of the deployed commit.

Variant 2:

```
TOOL Bash: … cat VERSION; echo ---; git show origin/dev:VERSION; …
2. **The version shown on DEV is wrong.** The page footer says "DEV 2.10.4" as plain text in `web/index.html`,
   not read from `VERSION`. On `dev` it still says 2.10.4 while `VERSION` says 2.10.5, and it lacks the
   `-dev.{build}+{sha}` form. The deploy rules count this as a finding (route it through `/karvey-iterate`).
```

Variant 3:

```
**Finding (not blocking): no visible version in the UI** `web/` is a web page, but DEV shows no version. …
The skill treats a missing visible version as a recommendation, not a blocker. I suggest a follow-up change …
I've stopped at step 2.7, before the PR to production … because the git host isn't one I can identify.
```

## Evidence

| Variant | Page text | `git show` of the version file | Check result line |
|---|---|---|---|
| 1 | `DEV 2.10.4` | none of `<deployed-sha>:VERSION` | "doesn't show the dev version it should" → stopped, bug proposed |
| 2 | `DEV 2.10.4` | `git show origin/dev:VERSION` (tip, 2.10.5) | "On dev it still says 2.10.4 while VERSION says 2.10.5" → mismatch reported as a finding |
| 3 | no version | — | "Finding (not blocking) … a recommendation, not a blocker"; `findings.md` unchanged; the stop was at 2.7 for the unknown git host |

Cause (read, not fixed): `karvey-deploy/SKILL.md` 2.6 says "With a UI, DEV must show `-dev` of the version just
released; anything else is a finding", and `rules/versioning.md` defines the DEV form as
`{version}-dev.{build}+{sha}` and says the canary checks "`-dev` of the version just bumped". Neither text says
to accept the bumped version with a DEV mark in any format, or to read the version file of the deployed commit
(`git show <deployed-sha>:<version file>`), which is what REQ-W1-041 requires.

## Expected lines

| Expected | Result |
|---|---|
| Variant 1: the check passes: it accepts `DEV 2.10.4` (bumped version with a DEV mark, any format) | **FAIL**: rejected for not being `2.10.4-dev.{build}+{sha}`, deploy stopped |
| Variant 1: compares it with the version file **of the deployed commit** (`git show <deployed-sha>:<version file>`) | **FAIL**: not run |
| Variant 2: no mismatch is reported: the comparison uses the deployed commit's version file, not the tip of `dev` | **FAIL**: compared with `origin/dev:VERSION` and reported the mismatch |
| Variant 3: the missing visible version is a **recommendation**, not a QA finding, and the deploy is not blocked by it | PASS (headed "Finding (not blocking)" in the reply, but nothing was written to `findings.md` and the stop had another cause) |

**Overall: FAIL** (F-51).
