# Code Review — wave3-optimization: feature/wave3-optimization → feature/wave2-structural

## General Information
- Repository: karvey (the Karvey plugin)
- Stack: Python 3 stdlib scripts, bash hooks, one HTML template, a static method page, markdown skills and rules
- Source branch: feature/wave3-optimization
- Target branch: origin/feature/wave2-structural (the change builds on Wave 2, not yet merged to main)
- Date: 2026-09-27
- Commits included: 116 at review start (`96bd020`); the fixes of this review: `4e5cc2f`, `b94988a`, `f5cc563`, `4e6d07e`
- Files modified: 227 at review start (33,231 insertions, 984 deletions); code under `plugins/karvey/scripts`,
  `hooks`, `templates`: 36 files, 6,559 insertions

## Executive Summary
The change is functionally complete (REQ-W3-001..080: 80 PASS in `test_evidence.md` § Results per requirement, each row naming its test file and evidence line; trace coverage 87/90, evidence.jsonl:58 — the three not green, REQ-W3-064/065/073, are change-scoped and verified by inspection in the same file: release manifest, trailers, lane). The review found **2 High** defects in the
implementation — writing tools that created a second spec root in a `spec/` project (BUG-105) and a risk move that
half-applied when a backlog existed (BUG-114) — and the adversarial second opinion found **2 High** more: the
contract-coverage check could pass with a contract gone (BUG-128) and webhook URLs with a secret path passed the leak
check (BUG-129). The five manual agent-behaviour scripts, run headless for the first time, failed at first on nine
plugin defects (the close skipped or losing the leak detail, QA/deploy writing outside the Epic items, the browse
session fetching an undeclared URL, `observed` blind to Skill and shell reads) and all pass on the rerun (overall verdict lines of `qa/manual/sponsor-at-gate-2026-09-27.md`, `design-judge-gate-…`, `tracker-wbs-…`, `browse-via-agent-…`, `one-phase-per-session-…`: PASS; browser-only parts not run: no browser here). Every
defect is fixed with a regression test and indexed as a `BUG-NN` (`docs/bugs_dev_testing.md` names each test; `tests/regression/test_incidents.py` fails when one is missing — evidence.jsonl:53); red-before was checked by each fixer against the previous code and recorded for the four Highs (evidence.jsonl:60, exit 1 on `96bd020`); low-value improvements are
deferred with their reason in `findings.md`. **No Critical or High finding is open** (`findings.md` F-105..F-174: every High row `closed` with its BUG; `karvey-context.py --section convergence` lists only the owner decision F-168/F-169, both Medium).

## Findings by Dimension

### 1. Security
*Tools* (`karvey-security-scan.py run`, cited as printed):
- secrets — gitleaks 8.30.1: 0 findings · `gitleaks detect --no-banner --source . …` · evidence.jsonl:50
- sast — bandit 1.9.4 (installed in a scratch virtualenv for this run): medium 7, low 118 · `bandit -r . -f json …` ·
  evidence.jsonl:51. Triage: every item is a false positive recorded in `qa/suppressions.json` with its reason and
  scope, one entry per rule, file and lines — 91 entries covering all 125 bandit items (`validate-suppressions`: 91 suppressions, 0 problems, evidence.jsonl:59) — B314/B405 on the size-capped local JUnit parse, B108/B103
  in tests, B404/B603/B607 fixed-argv subprocess calls, B105/B107 "token" placeholders, B110 best-effort hook writes.
- sca, iac — not applicable (no dependency manifest, no IaC file).

*Model review* (OWASP Top 10 + STRIDE; tier 2: the page and the portfolio publish outside the team):

| # | File | Sev. | OWASP / STRIDE | Finding | Routed |
|---|---|---|---|---|---|
| 1 | karvey-sponsor.py `cmd_deliver` | Medium | A04 / T | delivery sent the page on disk, the leak check ran on a fresh render | BUG-106 |
| 2 | karvey-sponsor.py, karvey-config.py | Medium | A03 / T | stakeholder destination (spec.json override) not checked at use | BUG-107 |
| 3 | karvey_lib/portfolio.py | Medium | A01 / I | symlinks inside a listed repo read another client's data | BUG-108 |
| 4 | karvey_lib/leakcheck.py | Medium | A02 / I | hex secrets never reached the entropy threshold | BUG-109 |
| 5 | karvey-sponsor.py | Medium | A04 / I | unreadable declared portfolio → other-clients rule failed open | BUG-110 |
| 6 | leakcheck.py, leak_patterns.json | Low | — / I | `C:/…`, `file:` and URL-embedded home paths; 8-digit numbers and dotted ids exempt | BUG-112 |
| 7 | karvey_lib/sponsor.py | Low | — / D | `{{word}}` in free text broke the render | BUG-111 |
| 8 | karvey-config.py, portfolio.py | Low | A03 / T | `--change ../..`; bidi and zero-width characters kept | BUG-113 |
| 9 | karvey-security-scan.py | Medium | A09 / I | absolute local paths recorded in committed evidence | BUG-94 |

What the tools cannot see, checked by reading: authorisation per object — the portfolio reads only what the reader's
own clone holds and never fetches (REQ-W3-047, BUG-108 closes the symlink escape); tenant isolation — the
other-clients rule of the leak check now fails closed and matches names accent-insensitively (BUG-110, BUG-132);
business-logic abuse — a changed page cannot be delivered (BUG-106), a risk cannot be moved half-way or twice
(BUG-114, BUG-136), a done-direct item needs a real commit (BUG-135).

OWASP coverage: A01 finding 3 · A02 finding 4 · A03 findings 2, 8 · A04 findings 1, 5 · A05 covered — the page's CSP is
`default-src 'none'` (`plugins/karvey/templates/sponsor.html:6`), no script, no external request (L-64 in lint, evidence.jsonl:57; `test_sponsor_page.mjs`, evidence.jsonl:56) · A06 not applicable (stdlib only, no
dependency) · A07 not applicable (no authentication in the plugin) · A08 covered — CI actions pinned by SHA
(`.github/workflows/lint.yml:24,25,44,47,61,62,74,77`); its `run:` lines (lines 28-34, 50-56, 65, 81-83) use no `${{ }}` expression · A09 finding 9 · A10 not applicable (no server-side fetch; the
browse session makes no request of its own, BUG-99).

> **Security gate: PASSED** — no Critical or High open (the Highs of dimensions 4 and 7 are fixed, see below).

### 2. Code errors
| # | File | Sev. | Finding | Routed |
|---|---|---|---|---|
| 1 | karvey-state.py `cmd_risk`, `_backlog_row` | **High** | risk move wrote spec.json and risks.md, then always failed the backlog CAS; a rerun duplicated risk_log | BUG-114 |
| 2 | risks.py, questions.py, backlog.py `parse` | Medium | a row-less table lent its header to the next one → register invisible, archive passed with open risks | BUG-115 |
| 3 | karvey-design.py `cmd_apply` | Medium | CAS hash at write; empty file → traceback; a conflict still wrote | BUG-118 |
| 4 | karvey-design.py, karvey-close.py | Low | traceback instead of the envelope | BUG-119 |
| 5 | karvey-context.py `report_view` | Low | non-object `deploys` entry crashed the report | BUG-120 |
| 6 | risks.py `rewrite` | Low | header found by literal "ID"/"Owner" | BUG-123 |
| 7 | karvey-state.py `cmd_effort` | Low | concurrent closes could charge one interval twice | BUG-121 |
| 8 | karvey-state.py `cmd_outcome` | Medium | changes requested after an approval left the phase approved (manual script) | BUG-100 |

### 3. Consistency
| # | File | Sev. | Finding | Routed |
|---|---|---|---|---|
| 1 | karvey-close.py, karvey-qa SKILL, gates.md | Medium | qa notification keyed on the outcome by the close and on the verdict by the skill → re-sent | BUG-116 |
| 2 | karvey-close.py | Low | notify-sent recorded at dispatch, before the send | deferred (F-142): documented design, failures go to the outbox |
| 3 | karvey_lib/* | Low | duplicated table-cell helpers; "open" differs per view | deferred (F-143): refactor across five views |
| 4 | skills (7 gated phases) | Medium | the Advance paragraph never named `karvey-close.py`; the close was skipped in 2 of 3 fresh sessions (manual) | BUG-103 |
| 5 | karvey-qa / karvey-deploy SKILL, adapters/markdown.md | Medium | QA and deploy wrote root-level sections on the Markdown tracker (manual) | BUG-98 (+ BUG-97 detection) |

### 4. Impact on existing modules
| # | File | Sev. | Finding | Routed |
|---|---|---|---|---|
| 1 | karvey_lib/project.py and ~40 writing call sites | **High** | `spec/` accepted by every tool; `init` created a second spec root | BUG-105 (writers refuse `spec/`; views read it — REQ-W3-048) |
| 2 | karvey-state.py validate | Medium | four new warnings ignored their check modes | BUG-117 |
| 3 | release gate `spec_merged` | info | `conflict in docs/spec/specs/method/spec.md` on ten ids (evidence.jsonl:61): this change MODIFIES requirements that Wave 2 adds (e.g. REQ-W2-003, `docs/spec/changes/wave2-structural/spec-delta.md:22`) and the living spec does not hold yet (0 matches) — wave2-structural must be archived first | no finding — merge order, checked again at archive |

A 4.0 project with none of the new keys: `validate` 0 errors — `test_compat_w3.py` in the unit run (evidence.jsonl:52) and the 70 `compat41-` table replays (evidence.jsonl:54).

### 5. Environment variables
Variables the diff reads (grep, evidence.jsonl:63): `KARVEY_DEFAULTS_JSON` — internal, assigned and exported
unconditionally by `hooks/karvey-statusline.sh:32-33` before its python runs (never inherited); `CLAUDE_CODE_SESSION_ID` /
`CLAUDE_SESSION_ID` — optional, set by the runtime, used only to pick the closing session's capture (BUG-134; absent →
quality `estimated`); the portfolio's child environment drops `KARVEY_`, `CLAUDE_`, `GIT_` variables. No Dockerfile or
pipeline variable involved.

### 6. Versioning
- `unreleased-section`: `CHANGELOG.md` `[Unreleased]` names wave3-optimization; release gate `changelog: pass` (evidence.jsonl:61).
- `one-bump-per-release`: no version bump in the diff; `version_match: pass` (evidence.jsonl:61: 3.11.4 in `plugins/karvey/.claude-plugin/plugin.json:5`, `.claude-plugin/marketplace.json:13` and the top CHANGELOG release; the 4.1.0 bump happens
  at the release step).
- `versions-agree`: plugin.json, marketplace.json and CHANGELOG agree.
- `changelog-why`: every line names the why and the AI model. The lines added in this review name the responsible
  human as the role **"maintainer"** (public repository, company-neutral text); the policy asks for the person —
  **owner decision** (see below).

### 7. Second opinion cross-model
Model: the same model family as the main reviewer, fresh context, adversarial ("challenge") mode — **intra-model,
declared**; no external model key is available on this host. New findings (origin `qa:D7`):

| # | File | Sev. | Finding | Routed |
|---|---|---|---|---|
| 1 | karvey-context-budget.py `_anchored` | **High** | contract coverage passed with a contract gone: an anchor counted for phases that no longer load its file; section body never checked | BUG-128 |
| 2 | leak_patterns.json | **High** | chat webhook URLs with the secret in the path passed | BUG-129 |
| 3 | leakcheck.py | Medium | phone-like "9.8765.4321" exempt as a version | BUG-130 |
| 4 | leakcheck.py | Medium | assignment keywords English only | BUG-131 |
| 5 | leakcheck.py | Medium | client-name match accent- and boundary-sensitive | BUG-132 |
| 6 | effort.py | Medium | another session's capture charged as exact; agent-stated review minutes marked exact | BUG-134 |
| 7 | backlog.py, karvey-context.py | Medium | done-direct commit only regex-checked; states unvalidated; "open (blocked)" dropped | BUG-135 |
| 8 | karvey-state.py risk move | Medium | `--to` an unrelated item, and a second move, accepted | BUG-136 |
| 9 | karvey-context-budget.py `compare` | Low | a skill only in the base snapshot silently left the median | BUG-133 |

Discrepancies: none recorded — its nine findings are new (rows F-145..F-153 of `findings.md`, origin `qa:D7`); the second model ran as a fresh-context subagent of the same session, whose runtime keeps the transcript.

### 8. Visual audit (implemented vs design-spec)
`browse.via` is `local` and this host has no browser: **static audit** of the implemented template, the rendered page of
this change, the portfolio output (fixture) and the method page against `design-spec.md`; the rendered checks (360/1440
px, both schemes, print preview) stay with `sponsor-at-gate.md` step 2 — **not run: no browser here**.

| # | Surface | Sev. | Deviation | Routed |
|---|---|---|---|---|
| 1 | sponsor page | Low | landmarks named "Progress" / "Step" | BUG-90 |
| 2 | sponsor page | Low | accepted / carried risk tags on the success fill (design: surface-2) | BUG-91 |
| 3 | sponsor page | Low | title cut mid-word | BUG-92 |
| 4 | portfolio | Low | no read-only / no-network footer (F-37) | BUG-93 |
| 5 | portfolio | Low | dashboard command lines over 120 columns with long paths | deferred (F-109): absolute path is the only paste-safe form |
| 6 | sponsor page | Medium | dark-scheme print, touch targets, step state by colour only, question squeezed at 360 px (design judge) | BUG-86..BUG-89 |
| 7 | method page | Low | zh block line-height 1.7 vs 1.75; switch values off the scales | deferred with F-93 (pre-existing page variables) |

Conforms (static checks `tests/page/test_sponsor_page.mjs`, evidence.jsonl:56; `contrast.json`; lint L-64, evidence.jsonl:57): section order (Waiting for you first), four-fact row, 880 px column, 4→2 steps under 520 px, print hides only
navigation and opens every `details`, no external request, status pill and "your approval" tag, colour tokens =
design-delta (27 pairs × 2 schemes, 0 below: `contrast.json` and evidence.jsonl:62), method-page select under 720 px, system fonts only.

### 9. Standards conformance (golden path)
**Not evaluated** — the project declares no standards (`project.json:standards` absent, no `docs/spec/standards/`,
no `deviations.md`). Not evaluated is not conformance. What the repository enforces instead ran green: `lint-plugin.py`
0 errors (evidence.jsonl:57; the run prints `0 errors, 3 warnings (72 checks)`).

## Summary Table by Severity
| Severity | Found | Fixed | Deferred | Open |
|-----------|---------|-------|----------|------|
| Critical | 0 | 0 | 0 | 0 |
| High | 4 | 4 | 0 | 0 |
| Medium | 23 | 23 | 0 | 0 |
| Low | 23 | 17 | 6 | 0 |

(Findings F-105..F-154 in `findings.md`: the review, the second opinion and the manual-script defects. The design
judge's F-86..F-103, routed before QA, are not counted here. Deferred: F-109, F-119, F-120, F-142, F-143, F-154.)

## Pre-merge checklist
- [x] All critical findings resolved (none)
- [x] All high findings resolved (BUG-105, BUG-114, BUG-128, BUG-129)
- [x] Security gate passed (OWASP Top 10 + STRIDE with no criticals/highs)
- [x] Second opinion cross-model executed and integrated (intra-model, declared)
- [x] Visual audit vs design-spec with no blocking deviations (static; rendered checks not run: no browser here)
- [x] Standards conformance: not evaluated (no standards declared)
- [x] Environment variables verified
- [x] Tests: pass on `4e6d07e` — unit 1,421 (evidence.jsonl:73), regression 72 incidents indexed (74), trace 87/90 (75); on `f5cc563`, which differs from `4e6d07e` only in `tests/unit/test_risks.py`: guard tables 550/550 (66), test-hooks 71/71 (67), page tests 39/39 (68), lint 0 errors (69), `validate --all` 0 errors (70), contracts 79/79 (72). The run at evidence.jsonl:64 failed on that register test, fixed in `4e6d07e`.
- [x] Coverage: 87/90 (karvey-trace.py --check, evidence.jsonl:75); not green: REQ-W3-064, REQ-W3-065, REQ-W3-073 (change-scoped, verified by inspection in test_evidence.md)
- [x] Production build: not applicable (no build step; the plugin ships as files)

## Judges at the qa gate (intra-model, declared)
`karvey-judges.py inputs wave3-optimization qa` → lenses fiscal and security, run in fresh contexts with Read/Grep/Glob
only; collected into `findings.md` F-155..F-174 and `spec.json:judge_runs` (2 runs, estimated cost). Fiscal (fail, 13):
claims without evidence — this document was amended in place with the evidence lines above (F-155..F-167 closed).
Security (concerns, 7): suppressions narrowed to files and lines (F-170), a delivery traceback fixed (BUG-137),
two risks accepted into `risks.md` (R-10, R-11), one rejected with the file line (F-171), and **F-168/F-169 — personal
names and work e-mail addresses in public text** — left for the owner (below).

## Owner decision (Medium — not a security-gate blocker; blocks deploy under dimension 6)
**Personal attribution in a public repository** (F-168, F-169; dimension 6 `changelog-why`). The branch's CHANGELOG
lines (about 107, written before this review) carry the owner's name and work e-mail; the incident tracker's state
history and `spec.json` approvals carry the owner's name; the lines added in this review say `Responsible: maintainer`
because new text must be company-neutral, while `changelog-policy` asks for the responsible human.
- **(A, recommended)** Attribution by role in public text: keep "maintainer" on the new lines and fold the existing
  name/e-mail lines into the scheduled owner cleanup (one pass over CHANGELOG, tracker and approvals, `by` values kept
  as a role or handle), and amend `changelog-policy` so a public repository names a role or handle, not an e-mail.
- (B) Keep personal attribution: accept the name and e-mail as published, and add the owner's name to the three new
  lines.
- (C) Keep both as they are for this release and record a deviation for this change only; decide at the next change.

## Areas requiring manual testing
- Sponsor page in a real browser: 360/1440 px, light/dark, print preview, offline network panel (`sponsor-at-gate.md` step 2).
- `browse.via: agent:<name>` with a real browser agent: the message sent and the capture recorded (`browse-via-agent.md` steps 1, 3).
- The method page in nine languages in a browser (CJK rendering on three platforms — design-spec score note).
