# Manual run: one-phase-per-session — 2026-09-27

- **Script:** `plugins/karvey/tests/manual/one-phase-per-session.md` (REQ-W3-013)
- **Run by:** the maintainer agent, headless (`claude -p` with the branch plugin, `--setting-sources project,local`;
  steps 1-2 in one session, steps 3-4 in a second one, each multi-turn by resuming), owner-authorised pattern
  (D-19, D-21, D-28).
- **Setup:** a throw-away repo under the scratch dir (`git init -b main` + a bare origin), seeded with
  `plugins/karvey/tests/unit/fixtures/sponsor/` and a minimal `architecture.md`. Two setup corrections were needed
  (see *Fixture*): the infra skip reason and the fixture's future dates. The statusline does not run in headless
  mode: for step 2 a capture was produced by piping a synthetic status payload (context at 62%) into
  `hooks/karvey-statusline.sh` for the session, which is what the installed statusline does; steps 1 and 5 ran with
  no capture.
- **Overall verdict:** **PASS** on the fourth rerun (step 4, BUG-127 fixed): steps 1–3 and 5 passed in the earlier reruns (BUG-100, BUG-103 fixed), step 4 now lists the skill and every rule it read with nothing outside the load list. Earlier: first run FAIL; reruns 1–3 FAIL on step 4 (BUG-101, BUG-104, BUG-126). Previous bullet: **FAIL** on the third rerun: step 4 FAIL on one line (`opened:` misses the rules the session read with `cd` into the rules folder and relative names; nothing is flagged outside the load list, so BUG-126 holds); steps 1–3 and 5 passed in the earlier runs. Earlier: **FAIL** on the second rerun: step 1 PASS (3 of 3 fresh sessions ran `karvey-close.py` after recording the approval, BUG-103 fixed), step 4 FAIL on one line (the Markdown adapter is flagged outside the load list, a new defect; the brace list of BUG-104 is fixed); steps 2, 3 and 5 PASS earlier.
- **First rerun:** FAIL (step 2 PASS incl. the continue-here branch, step 3 PASS, step 4 FAIL on a shell brace list counted as one file; step 1 skipped the close on the first attempt).
- **First run:** FAIL (step 1 PASS on retry, step 2 PASS, step 3 FAIL on one Expected line, step 4 FAIL,
  step 5 PASS).

## Step 1 — new session: "Close the how gate of sample-change: I approve the architecture."

| Expected | Observed | Verdict |
|---|---|---|
| close step 5 prints the offer and `continuing in this session is allowed` | `"lines": ["offer /karvey-checkpoint save: the next phase can start in a fresh session (one phase per session)", "context reading unavailable", "continuing in this session is allowed"]` | PASS |
| the agent relays the offer and does not end the session | "I stopped here instead of starting `/karvey-tasks`. It can run in this session or a fresh one after `/karvey-checkpoint save`." | PASS |

Flaky: in the first fresh attempt (same prompt, valid state) the agent recorded the approval and **did not run
`karvey-close.py` at all**; the retry ran it. An earlier attempt on the unmodified fixture also stopped before the
close (state invalid, `--ref` missing).

## Step 2 — context above `context_pct.red` (50): "Re-run the close … with changes requested."

| Expected | Observed | Verdict |
|---|---|---|
| step 5 prints `recommend: checkpoint + fresh session before the next skill` with reading and threshold | `recommend: checkpoint + fresh session before the next skill — context at 62% (threshold 50%)`; no "continuing … allowed" line | PASS |
| the agent recommends saving and a new session before loading the next skill | "context is at 62%, so karvey recommends `/karvey-checkpoint save` and a fresh session before the next skill" | PASS |
| still proceeds if the user says to continue here | not asked in this run | not run: the continue-here branch was not exercised |

Also observed: after `approve` then `outcome … changes_requested` on the same phase, `approvals.architecture.approved`
stays `true` and `karvey-state.py next` reports `ready · next tasks` (the agent flagged this itself; the sponsor
script saw the same). Reported as D6.

## Step 3 — save the checkpoint, new session: "What's next in karvey?"

| Expected | Observed | Verdict |
|---|---|---|
| the session hook's context names the change **and its next skill (from `karvey-state.py next`)** | the hook names the change (`Run /karvey-checkpoint restore BEFORE anything else (active change: sample-change)`); the next skill appears only inside the handoff text the previous session wrote — the hook itself prints no `next` line | **FAIL** |
| resumes from the checkpoint without re-asking decisions it holds | ran `/karvey-checkpoint restore`, checked git against the handoff, did not re-ask the recorded answers; it asked only for a new decision (withdrawing the approval, D6) | PASS |

## Step 4 — `observed` on the new session's transcript after the next phase skill ran

| Expected | Observed | Verdict |
|---|---|---|
| `opened:` lists the phase skill and the rules of its `Load:` line; `outside the load list:` empty | after `/karvey-tasks` ran in the new session: `karvey-context-budget.py observed --transcript … --skill karvey-tasks` → **`opened: no plugin text`**. The session loaded the skill through the Skill tool and read `rules/management-adapters.md` and `rules/adapters/markdown.md` through shell commands (`sed -n`, `grep`); `observed` counts only `Read` tool calls | **FAIL** |

## Step 5 — step 2 without a statusline capture

| Expected | Observed | Verdict |
|---|---|---|
| `context reading unavailable` and the checkpoint still offered | step 1's close (no capture): `"context reading unavailable"` with the offer line | PASS |

## Fixture

`tests/unit/fixtures/sponsor/…/spec.json` fails `validate` (`skipped.infra = "lane:feature-ui"` for a phase that
lane makes optional) and its dates (October 2026) lie after the run date, so `advance` to tasks fails
(`exited_at is before entered_at`). The run changed both in the throw-away repo only.

## Defects (plugin)

**D6 — changes requested after an approval leaves the phase approved.** `karvey-state.py outcome <change> <phase>
changes_requested` appends to `gate_outcomes` only; `approvals.<phase>.approved` stays `true` and `next` says
`ready`. `rules/gates.md` says "*Request changes* → … the phase stays". Proposed fix: `outcome … changes_requested`
on an approved phase moves that approval to `revision_history` (as `reopen` does), or `next` treats a later
`changes_requested` outcome as a blocker. Regression test idea (`test_state_*`): approve → outcome
changes_requested → `next` not `ready`.

**D7 — `observed` is blind to Skill-tool loads and shell reads.** `plugins/karvey/scripts/karvey-context-budget.py`
`opened_files` (lines 481-497) counts only `Read` tool calls. Proposed fix: also count `Skill` tool calls
(`skills/<name>/SKILL.md`) and `Bash` commands that `cat`/`sed`/`head`/`grep` a plugin `skills/**.md` path
(literal, or through a variable assigned in the same command). Regression test idea (`test_context_budget.py`): a
synthetic transcript with one `Skill` call and one `sed -n 1,5p $R/management-adapters.md` (`R=…/rules`) →
`opened` lists both.

**D8 (Low) — the session hook does not print the next skill.** `plugins/karvey/scripts/karvey_lib/karvey_hooks.py`
`session_text` (the *First action* block) names the active change but not `karvey-state.py next`'s skill. Proposed
fix: append `next: {phase} ({skill})` for the active change; regression: a session table case with an active change
expects that line.

## Rerun after the fixes (2026-09-27)

Fresh throw-away repo seeded from the fixed sponsor fixture (validates; October dates shifted to September in the
throw-away copy so `reopen`/`advance` can record today), a minimal `architecture.md`. Statusline: a synthetic
payload (context 62%) piped into `hooks/karvey-statusline.sh` for the session before step 2, as in the first run.

| Expected | Observed | Verdict |
|---|---|---|
| step 1 (setup for the rest): approval, then `karvey-close.py` once | the agent recorded the approval and **did not run the close**; asked "Did the gate close finish?", it read `gates.md`, said the close had not run and ran it (offer + `continuing in this session is allowed`). Same flake as the first run | FAIL (flaky, see defect A) |
| step 2: `outcome` on the approved phase is refused, the agent reopens first (BUG-100) | it first declined to run the close with changes requested over a recorded approval (records would contradict); on the person's go-ahead: `outcome` refused → `reopen` → `outcome` → close | PASS |
| step 2: `recommend: checkpoint + fresh session before the next skill` with the reading | printed; the agent relayed "this session is 62% full … saving a checkpoint and starting a fresh session" | PASS |
| step 2: still proceeds if the user says to continue here | "Continue here" → it advanced into the architecture rework in the same session | PASS |
| step 3: the hook names the active change and asks for `/karvey-checkpoint restore`; resumes without re-asking | hook: "Run `/karvey-checkpoint restore` BEFORE anything else (active change: sample-change)"; the agent ran the restore, checked `next` against the handoff and asked nothing it already held | PASS |
| step 4: `opened:` lists the phase skill and its `Load:` rules; `outside the load list:` empty (BUG-101) | `opened:` now lists `skills/karvey-architecture/SKILL.md` and `_core`, `engineering-standards`, `gates`, `judges`, `security-tiers` (loaded through the Skill tool and shell reads); but also the literal `skills/karvey/rules/{_core,gates,engineering-standards,security-tiers,judges}.md`, reported **outside the load list** | FAIL (defect B) |

Also seen: the checkpoint's `state.json` capture looked for the repository under `…/repo/sample-repo` (the
fixture's `repos: ["sample-repo"]` does not match the throw-away directory name) — a fixture/harness artefact.

### Remaining defects

**A — the phase skill's close paragraph does not name `karvey-close.py`.** `skills/karvey-architecture/SKILL.md`
line 319 (*Advance to the next phase*) says how the answer is recorded but not that the close steps run next; the
close lives only in `rules/gates.md` (~line 47) and `_core.md` line 28. In 2 of 3 fresh attempts across both runs
the agent recorded the approval and stopped. Proposed fix: one sentence in every phase skill's *Advance* paragraph
("then run `karvey-close.py {change} {phase} --outcome …` once"), guarded by a lint phrase; rerun step 1.

**B — `observed` counts a shell brace list as one file.** `scripts/karvey-context-budget.py` `_bash_paths` /
`_MD_PATH`: `wc -l $R/{_core,gates}.md` yields the literal `rules/{_core,gates}.md`, listed as opened and outside
the load list. Proposed fix: expand `{a,b,…}` lists (or drop tokens containing `{`/`}` after variable expansion);
regression test in `test_close.py` Observed with that command → the individual files, nothing outside.

## Second rerun (2026-09-27)

After BUG-103 (every gated phase skill's *Advance* paragraph names `karvey-close.py`, never skipped) and BUG-104
(`observed` expands `{a,b}` lists). Three throw-away repos under the scratch dir, seeded from the sponsor fixture
(October dates shifted to September, as before) with a minimal `architecture.md`; one fresh headless session each.

### Step 1 — three fresh sessions: "Close the how gate of sample-change: I approve the architecture."

| Session | Expected | Observed | Verdict |
|---|---|---|---|
| 1 | approval recorded, then `karvey-close.py … --outcome approved` once | approval recorded; `karvey-close.py sample-change architecture --outcome approved` ran; `sponsor.html` and one history line written; `effort` 3 → 4 entries | PASS |
| 2 | same | same: the close ran in the same command as the approval; page, history line and effort entry written | PASS |
| 3 | same | the agent first asked before recording anything (the decision reference could clash with ids the fixture cites, the minimal architecture lacks sections); nothing written. After the answer "use the next free decision number and go ahead" it recorded the approval and ran `karvey-close.py sample-change architecture --outcome approved` | PASS (asked first; no approval without the close) |

3 of 3 sessions ran the close after the approval (first run and first rerun: 1 of 3).

### Step 4 — `observed` after `/karvey-tasks` in a fresh session

| Expected | Observed | Verdict |
|---|---|---|
| `opened:` lists the phase skill and the rules of its `Load:` line | `skills/karvey-tasks/SKILL.md`, `rules/_core.md`, `rules/gates.md`, `rules/management-adapters.md`, `rules/adapters/markdown.md` (Skill load and shell reads now counted) | PASS |
| `outside the load list:` empty | `outside the load list: skills/karvey/rules/adapters/markdown.md` — the Markdown adapter is the `adapters/{tool}.md` entry of the skill's `Load:` line for this project's tracker | **FAIL** |

### Defect (plugin)

**D9 — `observed` allows only the largest alternative of a `{tool}` entry.** `plugins/karvey/scripts/karvey-context-budget.py`
line 556 builds the allowed set from `closure_max_files`, which keeps only the largest alternative of
`adapters/{tool}.md` (the ClickUp adapter), so any other tracker's adapter read by the skill is reported outside the
load list. Proposed fix: allow every alternative of each `Load:` entry (the refs' `alternatives` from
`karvey_lib/loadlist.py`), not only the maximum-size closure. Regression test idea (`test_close.py`, `Observed`): a
transcript reading `rules/adapters/markdown.md` with `--skill karvey-tasks` → `outside_load_list` empty.

## Third rerun (2026-09-27)

After BUG-126 (`observed` allows every alternative of a `{tool}` load entry). A throw-away repo under the scratch dir
(`git init -b main` + a bare origin), seeded from the sponsor fixture with the dates shifted to September, a minimal
`architecture.md` and the architecture approved; one fresh headless session: "Run /karvey-tasks for sample-change …
stop at the gate question". The session generated `tasks.md` and `PLAN.md` (2 Features, E1.QA and E1.DEPLOY, `--wbs`
0 issues) and asked the gate question. Then `karvey-context-budget.py observed --transcript {the session} --skill
karvey-tasks`.

### Step 4 — `observed` after `/karvey-tasks` in a fresh session

| Expected | Observed | Verdict |
|---|---|---|
| `opened:` lists the phase skill and the rules of its `Load:` line | `opened: skills/karvey-tasks/SKILL.md` only. The session loaded the skill (Skill tool) and read `rules/_core.md`, `rules/gates.md`, `rules/adapters/markdown.md` and `rules/management-adapters.md` with shell commands of the form `cd {plugin}/skills/karvey/rules; cat _core.md gates.md adapters/markdown.md; grep … management-adapters.md` and `cd {plugin}; cat rules/adapters/markdown.md` (paths relative to a `cd`, no `skills/` in the token) | **FAIL** |
| `outside the load list:` empty | empty (the Markdown adapter is no longer flagged: BUG-126 fixed) | PASS |

### Defect (plugin)

**D10 — `observed` misses shell reads by a path relative to a `cd`.** `plugins/karvey/scripts/karvey-context-budget.py`
`_bash_paths` matches only tokens that contain `skills/…/*.md` after the command's own variable assignments are
expanded; a command that first does `cd {plugin}/skills/karvey/rules` (or `cd {plugin}`) and then names `gates.md` or
`rules/gates.md` is not counted. Proposed fix: track the directory of a leading `cd DIR` (also `cd DIR &&`, `;`) in the
same command and resolve the relative `*.md` tokens of read verbs against it before `_plugin_rel`; a `cd` into
`{plugin}` with `rules/…` tokens needs the `skills/karvey/` segment the older layout omits, so only count paths that
exist relative to that directory (the observed run also tried `rules/…` directly under the plugin root, which does
not exist). Regression test idea (`test_close.py`, `Observed`): `cd /work/plugin/skills/karvey/rules; cat _core.md
gates.md adapters/markdown.md` → `opened` lists the three rules.

## Fourth rerun (2026-09-27)

After BUG-127 (`observed` resolves paths relative to a `cd` in the same shell command). A throw-away repo under the
scratch dir (`git init -b main` + a bare origin), seeded with the same state as the third rerun (sponsor fixture,
dates shifted to September, minimal `architecture.md`, architecture approved; `next` → `tasks`); one fresh headless
session: "Run /karvey-tasks for sample-change (Markdown tracker) … stop at the gate question". The session loaded the
skill, generated `tasks.md` and `PLAN.md` and asked the gate question, recording nothing. Then
`karvey-context-budget.py observed --transcript {the session} --skill karvey-tasks`.

### Step 4 — `observed` after `/karvey-tasks` in a fresh session

| Expected | Observed | Verdict |
|---|---|---|
| `opened:` lists the phase skill and the rules of its `Load:` line | `skills/karvey-tasks/SKILL.md`, `rules/_core.md`, `rules/adapters/markdown.md`, `rules/gates.md`, `rules/management-adapters.md` — the Skill load and every shell read (`cat`/`grep` through a variable holding the rules folder) | PASS |
| `outside the load list:` empty | empty (`outside_load_list: []`) | PASS |

This session read the rules through a variable, not after a `cd`; the `cd`-relative form of the third rerun is covered
by the unit test `Observed.test_BUG_101_skill_loads_and_shell_reads_count_as_opened` (BUG-127 case).

