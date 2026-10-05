# Code Review — prod-gate-scope: hotfix/3.12.1-prod-gate → main

## General Information

| Item | Value |
|---|---|
| Change | `prod-gate-scope` (hotfix lane, Security Tier 2), release 3.12.1 |
| Source → target | `hotfix/3.12.1-prod-gate` → `main` (PR not opened yet: opened at release prep) |
| Reviewed range | `e2acfab..8d6c361` |
| Date | 2026-10-05 |
| Reviewers | main QA (dimensions 5, 6, 9); security reviewer (D1); code reviewer (D2, D3, D4, D9); D7 second opinion — an independent agent of the same model family (intra-model), fresh context |
| Requirements | REQ-HF-001..030 (revision 2 tightens REQ-HF-014, REQ-HF-026) |

## Executive Summary

**Verdict: PASS (security gate passes, no open Critical/High).** The first QA round failed: the review found the
new "not a Karvey repo" warning reachable for Karvey targets, several REST evasions, a token echoed by a
fail-closed message, approval-scope gaps, L-80 errors and a worktree identity error. Three QA loops fixed them
(BUG-145..153, each with a regression test red on the commit before its fix). The final re-checks pass: security
gate PASS at `8d6c361`, code review PASS at `434c307` (later commits only touch the REST parser and the switch-off
rule, re-checked by security), D7 PASS WITH FINDINGS at `bd81fae`, both findings since fixed (wrapper-folder
search, L-80 wording). Known limits are recorded in BL-67.

## Findings by Dimension

### 1. Security
- Round 1 (`297c7ac`): FAIL — C1 look-alike clone → warning allow (Critical, regression); H1 renamed repo; H2
  REST parser evasions; M1 token in a fail-closed message; M2 other write endpoints; M3 here-documents, httpx;
  M4 encoded paths → BUG-145, 146, 147.
- Round 2 (`bd81fae`): FAIL — N1 fake Karvey clone decides and switches the gate off (Critical); N2 curl globs;
  N3 dot segments; raw HTTP → BUG-151.
- Round 3 (`434c307`): FAIL — `--request-target`, `--variable/--expand-*` (High); named fake clone switch-off
  without a Karvey session (Medium) → BUG-152.
- Round 4 (`a5ad33f`): FAIL — scheme-less URLs (High) → BUG-153.
- Round 5 (`8d6c361`): **PASS**. OWASP: A01 (access control: the prod-gate) and A08 (integrity of approvals) were
  the focus; A03 injection: no shell=True, argv lists only; A09: the audit log no longer receives exception text.
  STRIDE: spoofing (fake clones, question-tool approvals) and information disclosure (profiles, sensitive
  handoffs, tokens) addressed.
- Residual (accepted, BL-67): an agent-made Karvey clone entered with `cd`, merged without naming a repo, in a
  session whose project is not a Karvey project, can switch the gate off (same as 3.12.0); scripts that build
  URLs by string concatenation; raw HTTP not sent through a socket tool.

### 2. Code errors
Round 1: Azure host check dead, glab without web URL, budget per pipeline approval, error line without phrase →
fixed (BUG-145, 148). Final: PASS.

### 3. Consistency
Dead code removed (`resolve_profile`, `_legacy_kv`, `restcalls.target_of`); `clones.read_spec` /
`project_paths` public. PASS.

### 4. Impact on existing modules
Behaviour changes listed in CHANGELOG `[Unreleased]`: production approvals bound to the named change; session
profile only from the working repo (no default `ceo` role); prod-gate decides on the PR's repo; REST forms gated;
non-Karvey targets warn; a switch-off only from the session project; L-80. Existing table rows adjusted with the
reason in their notes (pg1-05/10/14/15, pg4-11/12, ap-19/21, ss-08, test-hooks.sh fixtures). PASS.

### 5. Environment variables
No new variables; `CLAUDE_PROJECT_DIR` (existing) now also decides the trusted roots. PASS.

### 6. Versioning
`[Unreleased]` has one line per commit with the why and the owner/AI trace block; no version bump in the diff
(bump at release prep); versions agree at 3.12.0. PASS.

### 7. Second opinion (D7, intra-model)
Round 1: FAIL (2 Critical, 3 High, 3 Medium). Re-check at `bd81fae`: PASS WITH FINDINGS (wrapper folders Medium,
L-80 Low) → fixed in `434c307`. Discrepancies: the reviewer suggested blocking unknown repos with a production
base in a Karvey session; the main QA kept D-45 (warning) and widened the clone search instead.

### 8. Visual audit
Not applicable: no UI (mockup and design skipped).

### 9. Standards conformance
Engineering standards: stdlib only, argv subprocesses with timeouts, tests red first, public text neutral. No
deviation requests needed. PASS.

## Summary Table by Severity

| Severity | Found | Fixed | Open |
|---|---|---|---|
| Critical | 4 | 4 | 0 |
| High | 10 | 10 | 0 |
| Medium | 9 | 8 | 1 (BL-67 item 5, pre-existing, accepted) |
| Low | 6 | 3 | 3 (BL-67) |

## Pre-merge checklist

- [x] Security gate PASS, no open Critical/High
- [x] Every bug fixed with a regression test red first (BUG-138..153), indexed in `test_incidents.py`
- [x] Unit, regression, guard tables, hook tests, page tests, lint, validate green
- [x] CHANGELOG `[Unreleased]` with why and owner/AI
- [ ] Version 3.12.1 and CHANGELOG `[3.12.1]` (release prep)
- [ ] CI green on the PR to `main`
- [ ] Human QA approval; requirements revision 2 confirmed
- [ ] Human production OK (typed phrase)

## Areas requiring manual testing

- A live `gh pr merge --repo` and an Azure REST completion against real hosts (the gate's host lookups were
  exercised with stubs): first real release of 3.12.1.
- A session started in one repo and resumed in another, in a real Claude Code session (hook cwd semantics).

## Addendum — D1 on the BUG-154 delta (`50b2d0d`), 2026-10-05

Security review of the plan-gate checkpoint exemption only. **Gate PASS** (no Critical/High).
- Blocked as intended: extra redirections, second writes (`;`, `&&`, `>|`, `&>`), `tee` with a second file or a
  process substitution, `cd` tricks, `..`, case changes, approvals/spec.json paths, `sed -i`, symlinked profile
  folder or file, another agent's handoff; the no-python branch blocks symlinked folders, files and changes.
- M1 (Medium): a `team.json` role or `ops_repo` that is a path could exempt code files → fixed: a role must be a
  plain name, an ops area inside the code repo other than `docs/spec` exempts nothing, and an exempt file must sit
  directly in the profile folder or the ops board folder (`test_plangate_checkpoint.py`
  test_d1_role_or_ops_that_points_into_code_exempts_nothing, red on 50b2d0d).
- L1 (Low): `ops_repo` naming the code repo → covered by the same fix.
- L2 (Low, pre-existing, not widened by the exemption): the plan-gate never classified `cp` or `python -c` writes;
  superseded by D-47 (the plan-gate is re-scoped to consequential actions).
