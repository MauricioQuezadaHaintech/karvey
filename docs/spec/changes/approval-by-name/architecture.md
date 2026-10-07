# Architecture: approval-by-name (hotfix 3.13.1)

**Lane:** hotfix · **Security Tier:** 2 · **Requirements:** REQ-AN-001..007, 010..012 · **Decisions:** D-10, D-34,
D-35, D-47 · **Skipped:** mockup and design_graphic (no UI), infra (no cloud, no pipeline change).

## Summary

Two areas, both inside existing components; no new process, no new dependency (Python 3 stdlib).

| Area | Component | Requirements | Incident |
|---|---|---|---|
| A. Approval by named change across clones | `karvey_lib/approval.py` (`resolve_prod_scope`, new `clones_holding`, `phrase_change`), `karvey_lib/guards.py` (`approval_hook`) | AN-001..007 | BUG-158 |
| B. Minimal phrase | `karvey-state.py` (`marker_report`), `karvey-deploy` SKILL, `rules/enforcement.md`, `hooks/README.md`, `lint-plugin.py` (L-82) | AN-010..012 | BUG-159 |

Fail modes unchanged: the approval hook fails open (no marker) with its one line (REQ-HF-018).

## Engineering-standards conformance gate

Stdlib only; every git call through `project.git` (timeouts, no shell); the clone search reuses
`clones.search_dirs` (bounded: `SIBLINGS_MAX`, two folder levels) — no second discovery; public text
company-neutral; every new branch has a unit test or guard-table row written red first.

## 1. Components and boundaries

### 1.1 A — `approval.clones_holding(anchors, ids)`

`{id: {repo_id: top}}` for the given ids: for each folder of `clones.search_dirs(anchors)`, its git top level; if
it is a Karvey project and `docs/spec/changes/<id>/spec.json` is a file, it is recorded under the clone's
`repo_id` (git common dir realpath). The first top seen for a clone is kept (worktrees of one clone count once).
Only the words of the prompt are looked up (no directory listing beyond `is_file` per candidate id).

### 1.2 A — `approval.resolve_prod_scope(root, cleaned, ids, active, anchors=None)`

Returns `{scope, why, implicit, candidates, owner}`; `owner` (new) is the top level where the marker is written
(None = the working tree). Order:

1. Ids of this tree named (unchanged): one → scope here; several → refuse (REQ-AN-005).
2. **New (REQ-AN-001..003)** — with `anchors`, the change-like words of the prompt (the same word list already
   built for BUG-148) are looked up with `clones_holding`. Several distinct ids found → refuse ("one message per
   change"). One id: one owning clone → `scope = id`, `owner = top`, `why = "held by clone <top>"`; two or more →
   refuse, `why` lists the tops, `candidates = [id]`.
3. Branch of this clone (unchanged message, REQ-HF-002), still `candidates = [tok]`.
4. Unknown word (**fixed**, REQ-AN-004): `candidates = []` so the phrase is `<change-id>`; `why` says no worktree,
   branch or local clone holds it (and how many clones were searched).
5. No change named: the single active change (unchanged).

`approval.phrase_change(cleaned, ids, active)` (REQ-AN-004) — for the production-shaped non-approval line: the one
id of this tree named, else `None` when the prompt carries any change-like word, else the active change.

### 1.3 A — `guards.approval_hook`

- Karvey project: `anchors = [root, payload.cwd, CLAUDE_PROJECT_DIR]` passed to `resolve_prod_scope`. With an
  `owner`, the marker is written with `approval.write_marker(owner, …)` and the TTL read for that clone
  (`ttl_min(ctx, owner)`), so the marker and its D-34 audit line live in the owning clone; the line reads
  `approval recorded (prod, <id>, clone <owner>, expires …)`.
- Outside a Karvey project (REQ-AN-006): only when the prompt classifies as a production approval (default
  vocabulary) — `approval.resolve_named_elsewhere(cleaned, anchors)` (step 2 alone). Found in one clone → marker
  there and the line; several clones or several ids → the not-recorded line; nothing found → silent (as before).
- The `elif shaped` branch uses `phrase_change` instead of the active change.

### 1.4 B — phrase

`marker_report` (state tool): «aprobado para producción <id>» and "(a PR number or version is optional)". The
deploy skill 2.9 shows the minimal phrase and the head SHA separately, and says the OK binds to the SHA passed
with `--sha`. `rules/enforcement.md` and `hooks/README.md` gain one sentence each. L-82 scans skill and rule
paragraphs for `(aprobado para producci[oó]n|approved for production)` followed, before the closing `»`/backtick/
quote, by `PR #`/`#{`/`#<` or a version token (`v<`, `v{`, `vN.N`).

## 2. Data model

Unchanged: marker, audit and ledger formats are the same; only the clone that receives them changes.

## 3. Security (Tier 2)

| Threat | Control |
|---|---|
| A marker written in a clone the human did not mean (look-alike, fork, copy) | Two or more owning clones → nothing recorded (AN-003); the working tree keeps precedence for its own ids (AN-005); the hook prints the path so the human sees where it went. |
| An agent creating a fake clone with the named id to divert the marker | The marker only authorises that clone's own `approve … prod`; the real clone then makes the id ambiguous (refused). No marker is ever written in the working tree's clone for an id it does not hold. |
| Agent-authored approval | Unchanged: only the UserPromptSubmit payload (human's own words) reaches the hook (D-01). |
| Cost / hang in the prompt hook | Search only for a production approval naming an id absent here; bounded discovery; exceptions fail open with the line. |
| Paths in output | Local paths of the human's own machine, printed to the human's session only; nothing in public text. |

## 4. Diagram

```
prompt ──classify──▶ prod? ──no──▶ (plan path unchanged)
                        │yes
            id named in this tree? ──yes──▶ marker here
                        │no
       clones_holding(words) over search_dirs
          ├─ 1 id, 1 clone ──▶ marker + audit in that clone, line names it
          ├─ 1 id, ≥2 clones ─▶ NOT recorded, clones listed, phrase names the id
          ├─ ≥2 ids ─────────▶ NOT recorded, one message per change
          └─ none ──▶ branch of this clone? ─▶ message (unchanged)
                     unknown word? ─▶ NOT recorded, phrase «… <change-id>»
                     no word ─▶ single active change (said out loud)
```

## 5. Edge cases

- The named id is in this tree and in a sibling clone: this tree wins (AN-005).
- The id is in another worktree of this clone: one clone; marker written with that worktree as root (same state
  dir).
- The owning clone's state dir is not writable: exception → fail open, the not-recorded line.
- A word equal to a common hyphenated word or a version (`go-live`, `3.13-hotfix`): never a change (BUG-148).

## 6. Test coverage plan (contract for `karvey-test`)

| Requirement | Test |
|---|---|
| AN-001, 002 | unit `test_approval_by_name.py` (sibling clone, marker + audit there, none here, line names the path; worktree of the same clone; `approve … prod --sha` in the owner accepts it) · table `ap-an-01` |
| AN-003 | unit (two sibling clones) · table `ap-an-02` |
| AN-004 | unit (unknown word → `<change-id>`; negated phrase naming an id → never the active change) · table `ap-hf-03` updated |
| AN-005 | existing `test_approval_scope.py`, tables `ap-hf-01..09` |
| AN-006 | unit (session in a folder that is not a Karvey project) |
| AN-007 | unit (an error in the search → not recorded line, no marker) |
| AN-010, 011 | unit `test_state_repos.py` updated (refusal phrase) · L-82 on the shipped tree |
| AN-012 | unit `test_lint_plugin.py` (L-82 pass / fail cases, registry list) |

## 7. Migration and rollout

None: no stored format changes. Release 3.13.1 (rev bump); the CHANGELOG entry carries
`- No project upgrade needed: approval hook and text only.` if the upgrade surface moved.
