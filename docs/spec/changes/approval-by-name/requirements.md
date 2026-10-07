# Requirements: approval-by-name

## Project description

Hotfix 3.13.1 (D-47). The approval hook resolved a production approval's change only inside the session's
working tree, so a change named by the human but owned by another local clone was refused and the hook suggested
the session's active change instead (F-01, BUG-158). The phrase shown to the human carried a PR number and a
version that read as mandatory while only the approval word, the production word and the change id are required
(F-02, BUG-159). North star (PRD): *the human's production OK reaches the change the human named, wherever the
session runs, and the phrase shown asks for nothing more than the approval word, the production word and the
change id.*

## Conventions

- **IDs.** `REQ-AN-NNN`; the heading carries the numeric EARS id.
- **Trace line.** PRD objective `O-n` / scope `S-n` / acceptance `AC-n`, finding `F-NN`, incident `BUG-NN`,
  decision `D-NN`, the 3.12.1 requirement it amends (`AMENDS REQ-HF-0NN`, change `prod-gate-scope`).
- **Roles.** the *approval hook* (runs on the human's prompt), the *state tool* (`karvey-state.py`), the
  *prod-gate*, the *working tree* (the git top level of the session's directory), a *clone* (a local repository,
  identified by its git common dir: its worktrees are the same clone), the *owning clone* (the clone whose working
  tree, or one of its worktrees, holds `docs/spec/changes/<id>/spec.json`), *clone discovery* (the bounded search
  the prod-gate uses, `clones.search_dirs`: the working tree and its worktrees, the paths `project.json:repos`
  lists, the folders next to the session's directory and repo, and repos up to two folders below a session
  directory that is not a repo). Examples use the fictional repos `app-web` and `app-api`.

---

## Requirement 1: A production approval is recorded in the clone that owns the named change (F-01, BUG-158)

### 1.1 REQ-AN-001 — A named change is looked up across the known clones
WHEN the human's prompt is a production approval (D-10) and names a change id that does not exist in the working
tree where the approval hook runs, the approval hook SHALL look for that id in the clones found by clone
discovery, anchored at the working tree, the session's directory and the session project, counting a clone once
whatever number of its worktrees hold the change. A word *names* a change of another clone only when it looks like a change id
(hyphenated, not a version, not a common hyphenated word) or is the word typed right after the production term
(«… producción <id>»), and never when it is an approval, production or negation word; the change counts only when
its `spec.json` is committed on that clone's HEAD (QA revision 1, F-03). A change id without a hyphen found only in
another clone is never recorded from the session: the hook refuses and names the clone to approve it from (QA
revision 2, F-07); a change present there but not committed is named as such.

*Trace: O-1, S-1, AC-1 · F-01 · BUG-158 · D-47 · AMENDS REQ-HF-002*

**Scenarios**
- Given a session in `app-web` (active change `web-search`) and a sibling clone `app-api` holding `api-rate-limit`,
  when the human types «aprobado para producción api-rate-limit», then the hook finds `app-api`.
- Given the id committed in a second worktree of the working tree's clone, then that clone is the owner (one clone).

### 1.2 REQ-AN-002 — One owning clone: the marker and its audit line are written there
WHEN exactly one clone owns the named change, the approval hook SHALL write the production marker in that clone's
state (its `approvals/` and its audit log), SHALL write no marker in the working tree's clone (unless it is the
same clone), and SHALL print `[karvey] approval recorded (prod, <id>, clone <path>, expires …)` naming the path of
the owning clone.

*Trace: O-1, S-1, AC-1 · F-01 · BUG-158 · D-34, D-47*

**Scenarios**
- Given AC-1, then `app-api` holds the marker `api-rate-limit` of kind `prod` and an audit line `marker recorded`;
  `app-web` holds no marker; the line names `app-api`'s path; `approve api-rate-limit prod --sha <head>` run in
  `app-api` accepts it.

### 1.3 REQ-AN-003 — Two or more owning clones: nothing is recorded, the clones are listed
IF two or more clones own the named change, THEN the approval hook SHALL record no marker in any of them and SHALL
print `prod approval NOT recorded` with the path of every owning clone and the phrase naming that change.

*Trace: O-1, S-1, AC-2 · F-01 · BUG-158 · D-47*

### 1.4 REQ-AN-004 — The suggestion never names another change
WHEN the approval hook prints `prod approval NOT recorded` for a prompt that names a change (an id of this tree,
an id of another clone or branch, or a change-like word found nowhere), the phrase it suggests SHALL name that
change when it was found, else `<change-id>`; it SHALL never name the working tree's active change or any change
other than the one named. This also holds for a production-shaped prompt that is not an approval (a negation, a
question).

*Trace: O-2, S-1, AC-3 · F-01 · BUG-158 · AMENDS REQ-HF-029*

### 1.5 REQ-AN-005 — The working tree and the active change keep their precedence
WHEN the named id exists in the working tree, the approval hook SHALL record it there without searching other
clones (REQ-HF-001); WHEN the prompt names no change, it SHALL keep the fallback to the working tree's single
active change, said out loud (REQ-HF-003); several ids named (here, in another clone or on a branch) SHALL record nothing, also when one of them is
in this tree (REQ-HF-004, F-04);
an id held only by a branch of this clone keeps its message (REQ-HF-002).

*Trace: O-1, S-1, AC-4 · F-01 · AMENDS REQ-HF-001..004*

### 1.6 REQ-AN-006 — A session outside a Karvey project
WHEN the session's directory is not inside a Karvey project and the human's prompt is a production approval that
names a change owned by exactly one clone found by clone discovery, the approval hook SHALL record the marker in
that clone as in REQ-AN-002; IF two or more clones own it, THEN it SHALL print the line of REQ-AN-003; otherwise
it SHALL stay silent as before.

*Trace: O-1, S-1 · F-01 · BUG-158 · D-47*

### 1.7 REQ-AN-007 — Bounded and fail-open
The clone search SHALL run only for a production approval whose named id is not in the working tree, SHALL use the
prod-gate's bounded discovery (no network), and any error in it SHALL record no marker and print the
`prod approval NOT recorded` line (REQ-HF-018).

*Trace: O-1, S-1 · F-01 · AMENDS REQ-HF-018*

---

## Requirement 2: The phrase asks only for what counts (F-02, BUG-159)

### 2.1 REQ-AN-010 — One phrase everywhere
The phrase the approval hook, the state tool's `approve … prod` refusal and `karvey-deploy` show to the human
SHALL be «aprobado para producción <change-id>» (English: «approved for production <change-id>»), with no PR
number and no version inside it.

*Trace: O-3, S-2, AC-5 · F-02 · BUG-159 · D-10*

### 2.2 REQ-AN-011 — PR and version are informational; the commit is the binding
`rules/enforcement.md`, `hooks/README.md` and `karvey-deploy` SHALL state that a production OK needs only an
approval word, a production word and the change id; that a PR number or a version the human adds is informational;
and that the approval binds to the head commit the agent passes with `approve … prod --sha`, so a PR recreated
with the same head stays approved and a new commit needs a new OK.

*Trace: O-3, S-2, AC-5 · F-02 · BUG-159 · D-10, D-35*

### 2.3 REQ-AN-012 — Lint keeps the phrase minimal
The plugin linter SHALL fail (check L-82) when a skill or rule shows the production phrase («aprobado para
producción …» / «approved for production …») with a PR number or a version inside it.

*Trace: O-3, S-2, AC-5 · F-02 · BUG-159*
