# Code Review — approval-by-name: hotfix/3.13.1-approval-by-name → main

## General Information

| Item | Value |
|---|---|
| Change | `approval-by-name` (hotfix lane, Security Tier 2), release 3.13.1 |
| Source → target | `hotfix/3.13.1-approval-by-name` → `main` (PR opened at release prep) |
| Reviewed range | `f1cf2f8..cb90ed4` |
| Date | 2026-10-07 |
| Reviewers | main QA (dimensions 2–6, 9); security reviewer (D1, blocking gate); D7 second opinion — an independent agent of the same model family (intra-model), fresh context |
| Requirements | REQ-AN-001..007, 010..012 (QA revisions 1–2 of REQ-AN-001, 005) |

## Executive Summary

**Verdict: PASS (security gate passes, no open Critical/High).** Round 1 failed: D1 and D7 found that any word of
a production approval, vocabulary words included, could route it to a change of another clone (High), plus an id
here + one elsewhere recorded, a suggestion still naming the active change and L-82 precision (BUG-160, BUG-161).
Round 2 (`952f858`): D7 PASS WITH FINDINGS; D1 FAIL — a decoy hyphenless id typed after the production term
(High) → refused (`5eb37ad`). Round 3 (`5eb37ad`): D1 PASS with one Medium (a hyphenated decoy phrase typed in
passing) → closed in `cb90ed4` (another clone only by the id right after the production term). Every fix has a
regression test red on the commit before it.

## Findings by Dimension

### 1. Security (D1)
- Round 1 (`f09725c`): FAIL — H1 any word routes the approval to a sibling clone (A, C, E repros); L1 decoy copy
  makes the id ambiguous (fails safe, accepted, F-06); L2 paths in local output (accepted).
- Round 2 (`952f858`): FAIL — H1b hyphenless decoy after the production term (A2–A6).
- Round 3 (`5eb37ad`): **PASS**; Medium B1 (hyphenated decoy phrase) fixed in `cb90ed4` (unit
  `test_d1_another_clone_is_reached_only_by_the_id_after_the_production_word`).
- OWASP A01/A08 (approval integrity), STRIDE spoofing (decoy clones), DoS (bounded discovery, ~0.6 s over 115
  clones, fails open), info disclosure (exception type only). The D-35 binding (`--sha`) is unchanged by the phrase.

### 2. Code errors
Search error path fails open with the line; the outside-a-project path classifies with the default vocabulary.
PASS.

### 3. Consistency
Cross-clone search reuses `clones.search_dirs`; candidates built once (`elsewhere_candidates`). PASS.

### 4. Impact on existing modules
Behaviour changes in CHANGELOG `[Unreleased]`: the unknown-word refusal no longer suggests the active change
(test_approval_scope, ap-hf-03 updated); the hook acts outside a Karvey project only for a production approval
naming one owned change. REQ-HF tables unchanged and green. PASS.

### 5. Environment variables
None new. PASS.

### 6. Versioning
`[Unreleased]` holds one line per impl/QA commit with the owner/model block; the bump to 3.13.1 happens at release
prep (L-37 warning expected until then). PASS.

### 7. Second opinion (D7)
Round 1: FAIL (F1 High, F2/F3 Medium, F4 Low). Round 2 (`952f858`): PASS WITH FINDINGS — R1 (word after the
production term) closed by `5eb37ad`/`cb90ed4`, R2 (uncommitted holder reason) fixed, Info (scenario wording)
fixed. No neutrality issues.

### 8. Tests
unit 1088 OK · regression 10 OK (BUG-158..161 indexed) · tables 518 cases / 615 runs passed · test-hooks 67 ·
page 22 · lint 0 errors · validate 0 errors.

### 9. Documentation
`rules/enforcement.md`, `hooks/README.md`, `karvey-deploy` 2.9, CHANGELOG, tracker and index agree. PASS.
