# Manual run: sponsor-at-gate — 2026-09-27

- **Script:** `plugins/karvey/tests/manual/sponsor-at-gate.md` (REQ-W3-022, REQ-W3-023, REQ-W3-024)
- **Run by:** the maintainer agent, headless (`claude -p` with the branch plugin, `--setting-sources project,local`,
  multi-turn by resuming the same session), owner-authorised pattern (D-19, D-21, D-28).
- **Setup:** a throw-away repo under the scratch dir (`git init -b main` + a bare origin), seeded with
  `plugins/karvey/tests/unit/fixtures/sponsor/` and a minimal `architecture.md` for `sample-change`, committed.
  No statusline runs in headless mode, so effort reads `n/a — statusline not installed`. No browser on this host.
- **Overall verdict:** **PASS** on the rerun of step 3 (BUG-96, BUG-100, BUG-102 fixed); step 2's rendered checks remain not run (no browser here); step 4 passed in the first run and was not rerun.
- **First run:** FAIL (1 step FAIL, 2 PASS, 1 partly not run). Details and the defect below.

## Step 1 — "Close the how gate of sample-change: I approve the architecture."

| Expected | Observed | Verdict |
|---|---|---|
| approval recorded first | `karvey-state.py approve sample-change architecture --by … --role human --ref "chat …"` before the close (the gate check allows `approve` for a phase-granular close; `approve-gate … how` was not needed) | PASS |
| `karvey-close.py sample-change architecture --outcome approved` once | run once; `"order": ["sponsor", "events", "risks", "effort", "checkpoint"]`, `"failures": []` | PASS |
| sends the payload as printed, composes no message of its own | the close printed `send the sponsor payload as printed, then record a failure with outbox add --op deliver_sponsor` and the payload (channel email). The agent composed no message of its own; it did **not** send and did **not** queue to the outbox — it asked first ("it goes to someone outside this session") | not run: no email adapter on this host and the host's own instructions require a person's confirmation for outward sends (harness) |
| `sponsor-history.jsonl` gains one line, `outcome: approved`, sha256 | `{"gate": "how", "outcome": "approved", "sha256": "ec3d…"}` | PASS |
| `spec.json:effort` gains one `architecture` entry | one entry `phase: architecture`, `usd.quality: n/a` ("statusline not installed") | PASS |

Setup note: the fixture's `spec.json` fails `validate` (`skipped.infra = "lane:feature-ui"`, but infra is optional,
not skipped, in that lane; the error prints `expected lane:feature-ui, got lane:feature-ui`). The close still ran;
`next` refused. Reported below as a fixture defect.

## Step 2 — the page in a browser offline, 360/1440 px, light/dark, print

| Expected | Observed | Verdict |
|---|---|---|
| every section, Waiting for you first | static read of the written page: sections in order `waiting` (card emph), `scope`, `progress`, `cost`, `risks`, `released`, `history`; the open question with its "needed by" tag and its options in `details` | PASS (static) |
| no external request | 0 matches for `https?://`, `src=`, `@import` in the page | PASS (static) |
| rendered 360/1440 px, both schemes, print preview, network panel | — | not run: no browser here (the static CSS checks are `tests/page/test_sponsor_page.mjs`) |

The question is not shown as overdue: the fixture's dates are in October 2026 and the run date is earlier (fixture
data, not a defect of the page).

## Step 3 — risk text quotes a made-up connection string; close with changes requested

| Expected | Observed | Verdict |
|---|---|---|
| close reports `leak check: FAIL — page not written, not delivered`, naming the field `risks.items[…].description` and the rule `secret` without the value | the close output carries only `"error": "sponsor build: leak check: FAIL — page not written, not delivered"`; **no field and no rule** appear in the close's output (`karvey-sponsor.py build` prints them, but `karvey-close.py` keeps only the first line) | **FAIL** |
| `sponsor.html` byte-identical to step 1 | `cmp` of the page before and after: identical | PASS |
| `sponsor-refusals.jsonl` has field and rule, not the string | `{"field": "page", "rule": "secret"}`, `{"field": "risks.items[0].description", "rule": "secret"}`; the string occurs 0 times | PASS |
| the effort step still ran | effort step `ok: true`; a fifth `effort` entry | PASS |

Also observed (not an Expected line): lacking the field/rule from the close, the agent re-read `risks.md` itself and
**quoted the made-up credential** in its reply; it also noted the session-start context lists open risks verbatim,
so the same text reaches the model there.

## Step 4 — risk restored, destination switched to an unreachable webhook; close again

| Expected | Observed | Verdict |
|---|---|---|
| page regenerated | the agent first asked which outcome to record ("Close again" is ambiguous) — the person answered "Approve"; then `approve` + `karvey-close.py … --outcome approved`; the page differs from step 3; a second `approved` line in `sponsor-history.jsonl` | PASS |
| the send fails and the agent says so | "nothing was sent, because the webhook address … is still the placeholder" | PASS |
| recorded with `karvey-config.py outbox add sample-change --op deliver_sponsor …` | `outbox add sample-change --op deliver_sponsor --key "sample-change:how:sponsor" … --failed "sponsor webhook target not configured (…)"` → entry `state: ready`, `attempts: 1` | PASS |
| the gate stays closed | approval kept, no reopen | PASS |

## Defect (plugin)

**D1 — the close drops the leak-check detail.** `plugins/karvey/scripts/karvey-close.py` `step_sponsor` (lines
84–86): on a non-zero exit of `karvey-sponsor.py build` it stores only `_errors(env, err)`, i.e. the first message
(`kl.issue("sponsor.leak", lines[0])` in `karvey-sponsor.py:166`); the per-field lines (`field … rule: … (value not
shown)`) and `result.hits` are lost. Reproduction: the sponsor fixture, a risk description containing
`Password=NotReal-123`, `karvey-close.py sample-change architecture --outcome changes_requested --json`.
Expected: the sponsor step names each field and rule (never the value). Proposed fix: on a refusal copy
`result.hits` as `[{field, rule}]` (and the rendered lines) into the step. Regression test idea (`test_close.py`):
the step's JSON contains `risks.items[0].description` and `secret` and does not contain the value.

**Fixture — `tests/unit/fixtures/sponsor/docs/spec/changes/sample-change/spec.json`:** `skipped.infra =
"lane:feature-ui"` is invalid for an optional phase (validate error, confusing `expected == got` message in
`karvey-state.py:372-375`), and its dates lie after 2026-09-27, so `advance` from it fails
(`exited_at is before entered_at`). Proposed fix: a plain reason for the optional skip and past dates; regression
test idea: every fixture `spec.json` validates with 0 errors.

## Rerun after the fixes (2026-09-27)

Fresh throw-away repo seeded from the fixed sponsor fixture (it now validates). Step 1 was repeated to reach the
gate (a minimal `architecture.md` added as in the first run; approval and close ran, page written). For the reopen
the fixture's October dates were shifted to September in the throw-away copy only (they lie after the run date,
and `reopen` records today's time); the unit tests keep them on purpose.

| Expected (step 3) | Observed | Verdict |
|---|---|---|
| the agent withdraws the approval before recording the outcome (BUG-100) | its first `outcome … changes_requested` was refused (`state.outcome_after_approval`, naming `reopen`); it then ran `reopen sample-change architecture` and `outcome`; `next` shows architecture awaiting approval | PASS |
| the close names each field and rule, never the value (BUG-96) | sponsor step: `leak check: page — rule secret (value not shown)`, `leak check: risks.items[0].description — rule secret (value not shown)`, `the last written page is unchanged and nothing was delivered`; `refused: [{field, rule}, …]` | PASS |
| `sponsor.html` byte-identical to step 1 | `cmp` identical | PASS |
| `sponsor-refusals.jsonl` has field and rule, not the string | two lines (`page`, `risks.items[0].description`, rule `secret`); the string occurs 0 times | PASS |
| the effort step still ran | effort step ran (`n/a`, no statusline in headless mode) | PASS |

The agent's reply named where the leak was found and never quoted the value (in the first run it re-read the
risk and quoted it). It did type the made-up value once inside its own `grep` check command.
