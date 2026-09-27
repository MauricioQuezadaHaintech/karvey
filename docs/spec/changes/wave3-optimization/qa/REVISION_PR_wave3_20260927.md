# Code Review — wave3-optimization: feature/wave3-optimization → feature/wave2-structural

## General Information
- Repository: karvey (the Karvey plugin)
- Stack: Python 3 stdlib scripts, bash hooks, one HTML template, a static method page, markdown skills and rules
- Source branch: feature/wave3-optimization
- Target branch: origin/feature/wave2-structural (the change builds on Wave 2, not yet merged to main)
- Date: 2026-09-27
- Commits included: 116 at review start (`96bd020`); the fixes of this review add three commits
- Files modified: 227 at review start (33,231 insertions, 984 deletions); code under `plugins/karvey/scripts`,
  `hooks`, `templates`: 36 files, 6,559 insertions

## Executive Summary
The change is functionally complete (REQ-W3-001..080: 80 PASS). The review found **2 High** defects in the
implementation — writing tools that created a second spec root in a `spec/` project (BUG-105) and a risk move that
half-applied when a backlog existed (BUG-114) — and the adversarial second opinion found **2 High** more: the
contract-coverage check could pass with a contract gone (BUG-128) and webhook URLs with a secret path passed the leak
check (BUG-129). The five manual agent-behaviour scripts, run headless for the first time, failed at first on nine
plugin defects (the close skipped or losing the leak detail, QA/deploy writing outside the Epic items, the browse
session fetching an undeclared URL, `observed` blind to Skill and shell reads) and all pass on the rerun. Every
defect is fixed with a regression test (red before, green after) and indexed as a `BUG-NN`; low-value improvements are
deferred with their reason in `findings.md`. **No Critical or High finding is open.**

## Findings by Dimension

### 1. Security
*Tools* (`karvey-security-scan.py run`, cited as printed):
- secrets — gitleaks 8.30.1: 0 findings · `gitleaks detect --no-banner --source . …` · evidence.jsonl:50
- sast — bandit 1.9.4 (installed in a scratch virtualenv for this run): medium 7, low 118 · `bandit -r . -f json …` ·
  evidence.jsonl:51. Triage: every item is a false positive recorded in `qa/suppressions.json` with its reason and
  scope (`validate-suppressions`: 6 suppressions, 0 problems) — B314/B405 on the size-capped local JUnit parse, B108/B103
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
`default-src 'none'`, no script, no external request (L-64, page tests) · A06 not applicable (stdlib only, no
dependency) · A07 not applicable (no authentication in the plugin) · A08 covered — CI actions pinned by SHA, the
workflow has no `${{ }}` of untrusted input in `run:` · A09 finding 9 · A10 not applicable (no server-side fetch; the
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
| 3 | release gate `spec_merged` | info | conflict in `docs/spec/specs/method/spec.md` on requirements Wave 2 also modifies: expected until wave2-structural is archived first (merge order) | no finding — checked again at archive |

A 4.0 project with none of the new keys: `validate` 0 errors (test_compat_w3, 70 `compat41-` table replays).

### 5. Environment variables
No new variable read from the environment. `KARVEY_DEFAULTS_JSON` is internal (set and exported by
`karvey-statusline.sh` for its own python, fallback `''`). No Dockerfile or pipeline variable involved.

### 6. Versioning
- `unreleased-section`: `CHANGELOG.md` `[Unreleased]` names wave3-optimization; release gate `changelog: pass`.
- `one-bump-per-release`: no version bump in the diff; `version_match: pass` (3.11.4 everywhere; the 4.1.0 bump happens
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

Discrepancies: none — the second model confirmed the preliminary findings it re-checked.

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

Conforms: section order (Waiting for you first), four-fact row, 880 px column, 4→2 steps under 520 px, print hides only
navigation and opens every `details`, no external request, status pill and "your approval" tag, colour tokens =
design-delta (27 pairs, 0 below, `contrast.json`), method-page select under 720 px, system fonts only.

### 9. Standards conformance (golden path)
**Not evaluated** — the project declares no standards (`project.json:standards` absent, no `docs/spec/standards/`,
no `deviations.md`). Not evaluated is not conformance. What the repository enforces instead ran green: `lint-plugin.py`
72 checks, 0 errors.

## Summary Table by Severity
| Severity | Found | Fixed | Deferred | Open |
|-----------|---------|-------|----------|------|
| Critical | 0 | 0 | 0 | 0 |
| High | 4 | 4 | 0 | 0 |
| Medium | 22 | 22 | 0 | 0 |
| Low | 17 | 12 | 5 | 0 |

(Review and second opinion, plus the manual-script defects BUG-95..BUG-104, BUG-126, BUG-127.)

## Pre-merge checklist
- [x] All critical findings resolved (none)
- [x] All high findings resolved (BUG-105, BUG-114, BUG-128, BUG-129)
- [x] Security gate passed (OWASP Top 10 + STRIDE with no criticals/highs)
- [x] Second opinion cross-model executed and integrated (intra-model, declared)
- [x] Visual audit vs design-spec with no blocking deviations (static; rendered checks not run: no browser here)
- [x] Standards conformance: not evaluated (no standards declared)
- [x] Environment variables verified
- [x] Tests: pass — {EVIDENCE_TESTS}
- [x] Coverage: {COVERAGE} (karvey-trace.py --check); not green: REQ-W3-064, REQ-W3-065, REQ-W3-073 (change-scoped, verified by inspection in test_evidence.md)
- [x] Production build: not applicable (no build step; the plugin ships as files)

## Areas requiring manual testing
- Sponsor page in a real browser: 360/1440 px, light/dark, print preview, offline network panel (`sponsor-at-gate.md` step 2).
- `browse.via: agent:<name>` with a real browser agent: the message sent and the capture recorded (`browse-via-agent.md` steps 1, 3).
- The method page in nine languages in a browser (CJK rendering on three platforms — design-spec score note).
