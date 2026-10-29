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
its `spec.json` is committed on that clone's HEAD (QA revision 1, F-03). Another clone is reached only by the id typed right after
the production term; a change-like word elsewhere in the message refuses with the phrase. A change id without a hyphen found only in
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
number and no version inside it. *Revision 4 (D-50): this phrase is the optional alternative; the hook, the
refusal and `karvey-deploy` lead with the release proposal and a plain approval (REQ-AN-024).*

*Trace: O-3, S-2, AC-5 · F-02 · BUG-159 · D-10*

### 2.2 REQ-AN-011 — PR and version are informational; the commit is the binding
`rules/enforcement.md`, `hooks/README.md` and `karvey-deploy` SHALL state that a production OK needs only an
approval word, a production word and the change id; that a PR number or a version the human adds is informational;
and that the approval binds to the head commit the agent passes with `approve … prod --sha`, so a PR recreated
with the same head stays approved and a new commit needs a new OK. *Revision 4 (D-50): a production OK is also —
and by default — a plain approval of the release proposal (REQ-AN-017); naming the change stays an alternative.*

*Trace: O-3, S-2, AC-5 · F-02 · BUG-159 · D-10, D-35*

### 2.3 REQ-AN-012 — Lint keeps the phrase minimal
The plugin linter SHALL fail (check L-82) when a skill or rule shows the production phrase («aprobado para
producción …» / «approved for production …») with a PR number or a version inside it.

*Trace: O-3, S-2, AC-5 · F-02 · BUG-159*

---

## Requirement 3: A plan or gate approval is a short reply (F-10, D-47 — requirements revision 3)

### 3.1 REQ-AN-013 — Short replies approve a plan
WHEN the human replies to a plan or a phase the agent presented with a short approval reply («apruebo», «ok»,
«dale», «aprobado», «sí»), the approval hook SHALL record a plan approval and print
`approval recorded (plan, …)`; such a reply SHALL never record a production approval.

*Trace: F-10 · D-01, D-10, D-47*

### 3.2 REQ-AN-014 — No composed phrase for a plan or gate
The rules (`enforcement.md`, `phase-close.md`, `state-machine.md`, `verification.md`) and the skills that ask for an
approval SHALL say that a plan or gate approval is any short reply and SHALL never instruct the agent to give the
human a composed sentence to type. *Revision 4 (D-50): the production OK is a plain approval too, of the release
proposal the agent showed; «aprobado para producción <change-id>» stays only as an optional alternative.*

*Trace: F-10 · D-47*

### 3.3 REQ-AN-015 — Lint keeps it so
The plugin linter SHALL fail (check L-83) when a skill or rule gives the human a quoted phrase of more than two words
that starts with an approval word to type or reply for an approval, unless it is the production phrase.

*Trace: F-10 · D-47*

---

## Requirement 4: Production approval by a listed proposal and a bare «apruebo» (F-11, D-50 — requirements revision 4)

`reopen` was refused by the state tool (`reopen is allowed up to qa; approval-by-name is in deploying`), so the
owner's decision is folded into the open hotfix as revision 4, like revision 3 (D-47).

### 4.1 REQ-AN-016 — The agent lists what the approval carries out
WHEN the agent is about to ask for a production OK, the state tool SHALL offer `propose-release --change <id>
[--repo <path|name>] --pr <n> --sha <rev> [--effect <text>]`, repeatable for several changes across local clones
(found by clone discovery; `--repo` picks one; a change held by two clones, absent, or a `--sha` that is not a
commit of its clone is refused), SHALL write ONE pending proposal for the session's project in the clone-local
state dir (`approvals/proposals/`, a protected path written only by the tool; a newer proposal replaces it), whose
id is the sha256 of its content and which expires after 60 min (5..240), and SHALL print the block «Esta
aprobación implica:» with one numbered line per change — change · clone · PR · commit (7) · effect — and the
proposal id, for the agent to show the human verbatim.

*Trace: F-11 · D-50 · D-35*

### 4.2 REQ-AN-017 — A bare approval word approves every listed change
WHEN a live proposal exists for the session's project and the human's own message is an approval (an approval
word in position, no negation, no question, no stop; no production word and no change id required), the approval
hook SHALL write a prod marker for EVERY listed change, in the clone that holds it, carrying its listed commit and
the proposal id (valid 24 h, D-35), with the approval hook's audit line in that clone, and SHALL mark the proposal
approved.

*Trace: F-11 · D-50 · D-10, D-34, D-35*

### 4.3 REQ-AN-018 — The echo lists exactly what was recorded
WHEN the hook records from a proposal, it SHALL print one line `[karvey] production approval recorded:
<id>@<sha7>, <id>@<sha7> (expires …)` listing exactly the markers it wrote, and a second line `production
approval NOT recorded: <id> (<why>)` for any listed change it could not record.

*Trace: F-11 · D-50*

### 4.4 REQ-AN-019 — Pending, cancelled, and the named form
WHILE a proposal is pending, a message that is not an approval SHALL leave it pending and print nothing; a stop
word SHALL cancel it (`[karvey] release proposal cancelled (stop)`); a message that names production and a change
SHALL keep the D-10 path for that change and leave the proposal pending (backward compatible).

*Trace: F-11 · D-50 · D-47*

### 4.5 REQ-AN-020 — The agent can only propose
The agent SHALL NOT be able to approve its own proposal: only the approval hook, on the human's prompt, records
from it; `approve … prod` without that marker SHALL be refused and say to run `propose-release` and ask.

*Trace: F-11 · D-50 · D-01 (security D1)*

### 4.6 REQ-AN-021 — Integrity, freshness, display
IF the proposal's id is not the hash of its content (changed after it was shown), it was created after the
human's message, it is older than its expiry, it belongs to another session tree, or — with a readable transcript —
the agent's own text never showed its id, THEN the hook SHALL record no production approval and SHALL print
`[karvey] release proposal <id> NOT approved: <why>`; the message still counts as a plan approval.

*Trace: F-11 · D-50 (security D1, D7)*

### 4.7 REQ-AN-022 — The state tool binds the listed commit
WHEN `approve <id> prod` finds a marker from a proposal, it SHALL bind the listed commit (default `--sha`) and
SHALL carry a later commit of the same change into it as a follow-up (REQ-AN-025, superseding the refusal of
3.13.1); `check-prod` SHALL accept the ledger approval
it writes and SHALL refuse one whose approved commit differs from the proposal's.

*Trace: F-11 · D-50 · D-35*

### 4.8 REQ-AN-023 — Talk about approvals is silent (BUG-162)
The approval hook SHALL print a `prod approval NOT recorded` line only for a production approval attempt: an
approval word opening the message or a clause, followed (at most three connector words apart) by a production
word. A message that only discusses approvals SHALL print nothing.

*Trace: F-12 · BUG-162 · REQ-HF-029*

### 4.9 REQ-AN-024 — Rules, skill and lint ask for a plain approval
`karvey-deploy` 2.9 and the rules SHALL run `propose-release`, show its block and ask for a plain approval
(«apruebo»), one approval for every listed change; they SHALL NOT instruct the human to type the exact
production phrase, which stays documented only as an optional alternative. Lint check L-82 SHALL fail a skill or
rule that instructs the exact phrase (unless marked optional / alternative) and a deploy skill without
`propose-release`; L-80's message points to the proposal.

*Trace: F-11 · D-50 · L-80, L-82*

## Requirement 5: The human approves a change once (BUG-163, D-52, hotfix 3.13.2)

### 5.1 REQ-AN-025 — A follow-up commit is carried, not asked again
WHILE a change's production approval is complete, unexpired (24 h) and the change is not archived, WHEN the agent
runs `approve <id> prod --sha <new head>` (or `--repo <r> --sha <new head>`) for another commit of that change, the
state tool SHALL move the approval to that commit without a new marker, keep the move in `followups`
(`from`, `to`, `at`, `by`, `repo`) and write an audit line `prod-followup`; `check-prod` SHALL accept the new
commit. An expired approval, an archived change or a `reopen` SHALL still need the human (D-35, D-36).

*Trace: F-13 · BUG-163 · D-52 · D-35*

### 5.2 REQ-AN-026 — A summary that names the change shows the proposal
The proposal-shown check SHALL count the agent's text that carries the proposal id, or that names a change the
proposal lists in a message written after the proposal was created (5 s clock grain). A message naming neither
SHALL still refuse the approval.

*Trace: F-13 · BUG-163 · D-50*

### 5.3 REQ-AN-027 — A session told when it runs an older Karvey
WHEN the prompt hook runs from a cached Karvey older than the installed one, it SHALL say so once per session and
installed version; WHEN a Karvey script starts from an older cached copy, it SHALL re-run itself from the installed
version (never from a development checkout, never twice).

*Trace: F-13 · BUG-163*

### 5.4 REQ-AN-028 — Rules never ask twice; lint L-84
The rules and `karvey-deploy` SHALL say the production OK is of the change and that a follow-up commit is carried
by the agent; lint check L-84 SHALL fail a skill or rule saying a new commit needs a new OK, approval or proposal.

*Trace: F-13 · BUG-163 · L-84*

## Requirement 6: One approval, the plan's; no clock (BUG-164, BUG-165, D-54, hotfix 3.13.3)

### 6.1 REQ-AN-029 — The approved plan is the production approval
WHEN `approve <id> prod` finds no production marker but a live plan approval of that change or of the project, it
SHALL record the production approval from it (bound to `--sha`, evidence = the plan marker) and SHALL NOT consume
the plan approval; `check-prod` SHALL accept it when the approval hook's audit line of that plan marker exists.

*Trace: F-14 · BUG-164 · D-54 (supersedes the plan ≠ production split of D-10)*

### 6.2 REQ-AN-030 — No clock on an approval
A release proposal SHALL stay approvable until it is approved, cancelled or replaced (no deadline in its block); a
production approval SHALL stay valid until its change is archived or reopened; a legacy `expires_at` SHALL be
ignored. This supersedes the 24 h of REQ-AN-025 and D-35 and the 60 min of REQ-AN-017.

*Trace: F-14 · BUG-164 · D-54*

### 6.3 REQ-AN-031 — An answer is never lost
A short affirmative (up to three words before «si»: «te dije si») SHALL approve. A proposal refused only because
the agent never showed it SHALL stay pending; the hook line SHALL tell the agent to show that block once and wait,
never to regenerate it or to ask in other words.

*Trace: F-14 · BUG-164*

### 6.4 REQ-AN-032 — Reading is never blocked (BUG-165)
protect-paths SHALL treat `find` as read-only unless it carries a writing action (`-delete`, `-exec`, `-execdir`,
`-ok`, `-okdir`, `-fprint*`, `-fls`).

*Trace: F-14 · BUG-165 · D-47*

### 6.5 REQ-AN-033 — The pipeline-approval lookup authenticates (BUG-166)
WHEN the prod-gate resolves the run of an Azure Pipelines approval it SHALL call `az rest` with `--resource
499b84ac-1321-427f-aa17-267ca6975798`, so Azure DevOps answers with JSON instead of its sign-in page.

*Trace: F-15 · BUG-166 · REQ-HF-012*

## Requirement 7: No production without QA (BUG-167, D-55, hotfix 3.13.4)

### 7.1 REQ-AN-034 — The released commit is covered by a QA review
`check-prod` SHALL refuse a release (missing `qa`) unless the release ledger holds a QA review recorded with `qa-pass`
for the released commit, or for an ancestor of it whose delta touches only `docs/**`, `*.md` or `spec.json`. `qa-pass`
SHALL refuse a review outside `docs/spec/changes/<id>/qa/`, one that does not name the commit, and one with open
blocking findings. Carrying or binding a production approval SHALL NOT ask for QA. The refusal SHALL name the
`qa-pass` command and say the human is not asked.

*Trace: F-16 · BUG-167 · D-55*

