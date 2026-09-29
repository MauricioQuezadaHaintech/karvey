# Requirements: prod-gate-scope

## Project description

Hotfix 3.12.1 (D-43). Real use of 3.12.0 showed a prod approval bound to a change the human did not name
(F-01), a multi-repo change that cannot be released from the repos it does not live in (F-02), REST and
outside-a-repo release forms the prod-gate does not see (F-03), and a read-only listing blocked by
protect-paths (F-04, BL-64). North star (PRD): *a production approval reaches exactly the change and the
commits the human approved, whatever repo, working tree or command form the release goes through.*

## Conventions

- **IDs.** `REQ-HF-NNN`, contiguous; the heading also carries the numeric EARS id.
- **Trace line.** PRD objective `O-n` / scope `S-n` / acceptance `AC-n`, finding `F-NN`, incident `BUG-NN`,
  backlog `BL-NN`, decision `D-NN`, and the 3.12.0 requirement it amends (`AMENDS REQ-W1-0NN`, from
  `wave1-hardening`, not yet in the living spec).
- **Roles.** the *approval hook* (runs on the human's prompt), the *state tool* (`karvey-state.py`), the
  *prod-gate* and *protect-paths* (pre-execution guards), the *release ledger* (machine-local approval record
  of a clone), the *owning repo* (the repo whose `docs/spec/changes/` holds the change), a *declared repo*
  (a repo the change lists as released with it). Examples use the fictional repos `app-web`, `app-api`,
  `app-db`.
- **Production approval** = the ledger record of D-34/D-35: human, evidence of the approval hook's audit
  line, bound to an approved head commit, valid 24 h after the human's OK.

---

## Requirement 1: The prod approval is bound to the change the phrase names (F-01, BUG-53)

### 1.1 REQ-HF-001 — A named change wins over the active change
WHEN the human's prompt is a production approval (D-10) and names exactly one change id that exists in the
working tree where the approval hook runs, the approval hook SHALL record the prod marker for that change,
whatever change is active there.

Traces to PRD: O-1, S-1, AC-1 · F-01 · BUG-53 · Decision: D-43 · AMENDS REQ-W1-017

#### Scenario: Success
GIVEN a tree holding `team-adapters` (active) and `project-upgrade`
WHEN the human writes «aprobado para producción project-upgrade 3.13.0»
THEN the marker is recorded for `project-upgrade` and the hook line says `(prod, project-upgrade, …)`.

#### Scenario: Error
GIVEN the same tree
WHEN the human writes «aprobado para producción project-upgrade» inside a quoted or fenced block only
THEN no prod marker is recorded (quoted material is not the human's approval, REQ-W1-019 unchanged).

### 1.2 REQ-HF-002 — A named change that is not in this tree records nothing
IF a production approval names a change id that does not exist in the working tree where the approval hook
runs, THEN the approval hook SHALL record no marker and SHALL print that the change is not in this tree and
how to fix it: the path of the local worktree that holds it when `git worktree list` finds one, otherwise the
branch that holds it when one does, otherwise "open the session in the tree or branch that holds the change".

Traces to PRD: O-1, S-1, AC-1 · F-01 · BUG-53 · Decision: D-43

#### Scenario: Success (the fix is named)
GIVEN a tree where only `team-adapters` is open, and a second worktree `../app-web-wt-upgrade` of the same
clone that holds `project-upgrade`
WHEN the human writes «aprobado para producción project-upgrade 3.13.0»
THEN no marker is written, and the hook line says `prod approval NOT recorded: change project-upgrade is not
in this working tree` and names `../app-web-wt-upgrade` as the place to approve it.

#### Scenario: Error (nowhere to be found)
GIVEN no worktree or branch of the clone holds `proyect-upgrade` (a typo)
WHEN the human writes «aprobado para producción proyect-upgrade»
THEN no marker is written and the line says the change is not in this tree and no worktree or branch holds it.

### 1.3 REQ-HF-003 — No change named: the single active change, said out loud
WHEN a production approval names no change id, the approval hook SHALL record the prod marker for the active
change only when exactly one change is active (by branch, or the only open one) and SHALL say in the hook line
that the change was taken as the active one because the message named none; IF no change or several changes
are active, THEN it SHALL record no marker and SHALL print the candidates and ask to name one.

Traces to PRD: O-1, S-1 · F-01 · BUG-53 · Decision: D-43

#### Scenario: Success
GIVEN only `team-adapters` is active
WHEN the human writes «aprobado para producción»
THEN the marker is recorded for `team-adapters` and the line says `(prod, team-adapters — the only active
change; your message named none, …)`.

#### Scenario: Error
GIVEN `team-adapters` and `wave-a` are both active
WHEN the human writes «ok, pasa a producción»
THEN no marker is written and the line lists `team-adapters, wave-a` and asks to name the change.

### 1.4 REQ-HF-004 — Several named changes record nothing
IF a production approval names more than one change id, THEN the approval hook SHALL record no marker and
SHALL say that one production approval covers one change (BUG-41) and ask for one message per change.

Traces to PRD: O-1, S-1 · F-01 · BUG-53 · Decision: D-37 (manifest path unchanged), D-43

#### Scenario: Success
GIVEN changes `app-login` and `app-search` in the tree
WHEN the human writes «aprobado para producción app-login» and, in a second message, «aprobado para
producción app-search»
THEN one marker is recorded for each change.

#### Scenario: Error
GIVEN the same tree
WHEN the human writes «aprobado para producción app-login y app-search»
THEN no marker is written and the line asks for one message per change.

---

## Requirement 2: Multi-repo release under the owning repo's approval (F-02)

### 2.1 REQ-HF-005 — A change declares the repos it releases
The method SHALL let a change declare, in its `spec.json`, the list of repos it releases (by repo name), and
the state tool SHALL validate it as a list of non-empty names.

Traces to PRD: O-2, S-2 · F-02 · Decision: D-43

#### Scenario: Success
GIVEN a change in `app-web` with `"repos": ["app-web", "app-api", "app-db"]`
WHEN `validate` runs
THEN it reports no error.

#### Scenario: Error
GIVEN `"repos": "app-api"` or `"repos": [""]`
WHEN `validate` runs
THEN it reports an error on `$.repos`.

### 2.2 REQ-HF-006 — The owning repo binds each declared repo's release commit
WHEN the state tool is asked, in the owning repo, to bind a declared repo's release commit to a change's
production approval, it SHALL record that repo's approved head commit inside the existing production approval
of the change, and SHALL refuse, recording nothing, IF the repo is not declared by the change, IF there is no
production approval that is complete and unexpired, IF the commit is not a full commit id, or IF that repo is
already bound to a different commit (a new commit needs a new OK, D-35). The binding SHALL keep the
approval's expiry.

Traces to PRD: O-2, S-2, AC-2 · F-02 · Decision: D-35, D-43

#### Scenario: Success
GIVEN `app-web` holds a live production approval of `project-upgrade` that declares `app-api`
WHEN `approve project-upgrade prod --repo app-api --sha <40-hex head of the app-api PR>` runs in `app-web`
THEN the ledger's approval lists `app-api` bound to that commit, with the same `expires_at`.

#### Scenario: Error
GIVEN the same approval
WHEN the command names `--repo app-mobile` (not declared), or runs after the approval expired, or names another
commit after `app-api` was already bound
THEN it is refused with the reason and the ledger is unchanged.

### 2.3 REQ-HF-007 — A declared repo's `[Deploy] <id>` PR is released under the owning repo's approval
WHEN the prod-gate evaluates a production merge in a repo that does not hold the change the PR names (branch
`<feature prefix><id>` or title `[Deploy] <id>`), it SHALL look for the owning repo's local clone and SHALL
allow the merge only if that clone holds the change, the change declares this repo, and the owning repo's
production approval is complete, unexpired and binds this repo to the commit being released; otherwise it
SHALL block.

Traces to PRD: O-2, S-2, AC-2 · F-02 · Decision: D-34, D-35, D-43 · AMENDS REQ-W1-023

#### Scenario: Success
GIVEN `app-api` and its sibling clone `app-web` holding `project-upgrade` with `app-api` bound to `abc…`
WHEN `gh pr merge 12` runs in `app-api` on the PR `[Deploy] project-upgrade` whose head is `abc…`
THEN it is allowed and the ALLOW line names the owning repo.

#### Scenario: Error
GIVEN the same, but the PR head is a newer commit, or `app-api` is not bound, or not declared
WHEN the merge runs
THEN it is blocked with the reason.

### 2.4 REQ-HF-008 — The BLOCK message says where to approve and what to run
WHEN the prod-gate blocks a production merge because the change is not in this repo or its approval does not
cover this repo, the message SHALL name the owning repo (and its local path when found), the human's step
(approve production in their own message, naming the change, in a session of the owning repo) and the state
tool commands to run there (the approval, then the binding of this repo to its PR head commit); IF the owning
clone cannot be found, the message SHALL say where the gate looked and how to make it findable.

Traces to PRD: O-2, S-2, AC-2 · F-02 · Decision: D-43

#### Scenario: Success
GIVEN `app-api` is not bound
WHEN the merge is blocked
THEN the message contains `approve project-upgrade prod --repo app-api --sha <head>` and the path of `app-web`.

#### Scenario: Error
GIVEN no clone of the owning repo is found
WHEN the merge is blocked
THEN the message lists the places looked at and says to clone the owning repo next to this one or to name its
path in this repo's `project.json` repos.

### 2.5 REQ-HF-009 — The check is available to the agent
The state tool SHALL answer the prod-gate's question for a declared repo (`check-prod <id> --repo <name>
--sha <commit>`) with the same result the prod-gate uses.

Traces to PRD: O-2, S-2 · F-02

#### Scenario: Success
GIVEN a binding of `app-api` to `abc…`
WHEN `check-prod project-upgrade --repo app-api --sha abc…` runs in `app-web`
THEN it exits 0.

#### Scenario: Error
GIVEN no binding
WHEN the same check runs
THEN it exits with findings and names `repo` as missing.

---

## Requirement 3: REST and outside-a-repo coverage (F-03)

### 3.1 REQ-HF-010 — REST PR completions need the same approval
WHEN a command sends, through an HTTP client or a host CLI's raw API command, a request that completes a pull
request (Azure Repos `PATCH …/pullrequests/<n>` with status `completed` or an auto-complete setter; GitHub
`PUT …/pulls/<n>/merge`; GitLab `PUT …/merge_requests/<n>/merge`), the prod-gate SHALL treat it as a production
merge candidate of that PR and SHALL apply the same SHA-bound check as the CLI forms; a commit the request
binds (Azure `lastMergeSourceCommit`, GitHub/GitLab `sha`) SHALL be the approved one for a deferred completion.

Traces to PRD: O-3, S-3, AC-3 · F-03 · Decision: D-35, D-43 · AMENDS REQ-W1-023

#### Scenario: Success
GIVEN a live approval of `app-login` bound to the PR head `abc…`
WHEN `curl -X PATCH https://dev.azure.com/org/proj/_apis/git/repositories/app-web/pullrequests/7 -d
'{"status":"completed","lastMergeSourceCommit":{"commitId":"abc…"}}'` runs in the clone
THEN it is allowed.

#### Scenario: Error
GIVEN no approval
WHEN the same request, or `curl -X PUT https://api.github.com/repos/org/app-web/pulls/7/merge`, runs
THEN it is blocked like `az repos pr update --status completed` / `gh pr merge`.

### 3.2 REQ-HF-011 — REST branch writes into production are blocked
IF a command writes a production branch through a REST ref or merges endpoint (GitHub `…/git/refs/…`,
`…/merges`; Azure `…/refs` update), THEN the prod-gate SHALL block it and say to merge through a PR, as it does
for `gh api`.

Traces to PRD: O-3, S-3 · F-03 · BUG-28 (same rule for `gh api`)

#### Scenario: Success
GIVEN any repo
WHEN `curl -X PATCH …/repos/org/app-web/git/refs/heads/feature-x` runs
THEN it is not gated.

#### Scenario: Error
GIVEN any repo
WHEN `curl -X PATCH …/repos/org/app-web/git/refs/heads/main` runs
THEN it is blocked.

### 3.3 REQ-HF-012 — Production pipeline approvals need the same approval
WHEN a command approves a waiting pipeline run through the REST API (Azure Pipelines approvals with status
`approved`; GitHub Actions pending deployments with state `approved`), the prod-gate SHALL resolve the run's
branch and commit and SHALL allow it only when the run is not of a production branch, or when the change's
production approval covers the run's commit (the approved head commit, or a merge commit that has it as a
parent); IF the run, its branch or its commit cannot be resolved, or the approval form names no run (classic
release approvals, deployment approvals of other hosts), THEN it SHALL block with the reason.

Traces to PRD: O-3, S-3, AC-3 · F-03 · Decision: D-35, D-43

#### Scenario: Success
GIVEN a run of `main` whose commit is the merge of the approved head `abc…`, and a live approval
WHEN `curl -X PATCH https://dev.azure.com/org/proj/_apis/pipelines/approvals -d
'[{"approvalId":"<id>","status":"approved"}]'` runs
THEN it is allowed; a run of the integration branch is allowed without an approval.

#### Scenario: Error
GIVEN no approval, or the run's commit is neither the approved head nor a merge of it
WHEN the same request runs
THEN it is blocked with the reason.

### 3.4 REQ-HF-013 — Read-only and non-completing requests pass
WHILE a request to these endpoints is a read (GET/HEAD or no method and no body), a PR update that does not
complete it (title, reviewers, `status: abandoned`/`active`), or a rejection of an approval, the prod-gate SHALL
allow it silently.

Traces to PRD: O-3, S-3, AC-3 · F-03

#### Scenario: Success
GIVEN no approval
WHEN `curl -s https://dev.azure.com/org/proj/_apis/git/repositories/app-web/pullrequests/7` or a PATCH that
sets only the title runs
THEN it is allowed and prints nothing.

#### Scenario: Error
GIVEN no approval
WHEN the PATCH also carries `"status": "completed"`
THEN it is blocked.

### 3.5 REQ-HF-014 — Commands outside a repository are tied to the repo they name
WHEN a production merge candidate (CLI or REST) runs in a directory that is not inside a Karvey project (for
example after `cd /tmp`), the prod-gate SHALL tie it to a local clone by the repository the command names (its
repo option or variable, the PR the host reports, the URL) among the session's project, its worktrees and the
command's directory; a Karvey clone SHALL get the full check; a clone that is not a Karvey project SHALL not be
gated; IF no local clone matches and the PR's base is a production-named branch or cannot be determined, THEN
the prod-gate SHALL block with the reason and say to run the command from the repo's clone.

Traces to PRD: O-3, S-3, AC-3 · F-03 · Decision: D-43 · AMENDS REQ-W1-024

#### Scenario: Success
GIVEN a session in the clone `app-web` (Karvey) with a live approval bound to the PR head
WHEN `cd /tmp && gh pr merge 7 -R org/app-web` runs
THEN it is checked against `app-web`'s ledger and allowed; a PR into `dev` from `/tmp` is not gated.

#### Scenario: Error
GIVEN a session outside any repo and no local clone of `org/app-web`
WHEN `cd /tmp && az repos pr update --id 7 --status completed` runs on a PR into `main`
THEN it is blocked with "cannot tie … to a local clone; run it from the clone".

### 3.6 REQ-HF-015 — What the gate cannot read is blocked with the reason
IF a production merge or pipeline approval request cannot be read — its body comes from a file the hook cannot
read or from stdin, its URL or body is built from variables, or an inline script (`python -c`, `node -e`, a
PowerShell web request) calls a PR completion or approval endpoint — THEN the prod-gate SHALL block it with the
reason and the form to use instead; the gate SHALL NOT send any credential found in the command.

Traces to PRD: O-3, S-3 · F-03 · Decision: D-43 · AMENDS REQ-W1-024

#### Scenario: Success
GIVEN a readable body file with a non-completing update
WHEN `curl -X PATCH … -d @body.json` runs
THEN it is allowed.

#### Scenario: Error
GIVEN `curl -X PATCH "$URL" -d "$BODY"` or `python3 -c "requests.patch('…/pullrequests/7', json={'status':
'completed'})"`
WHEN it runs
THEN it is blocked with the reason.

---

## Requirement 4: Read-only listings of the protected paths (F-04, BL-64, BUG-54)

### 4.1 REQ-HF-016 — A read-only listing passes; writes stay blocked
WHEN every command of a Bash call that names a protected path (approval markers, release ledger, the Karvey
state directories, the compat marker) only reads it, and the other commands of the call neither take paths
from it nor write (text output, formatters, read-only `git` subcommands in a command substitution), protect-paths
SHALL allow the call; IF any command could write a protected path — a mutating command, a redirection into it,
a pipe into a command that runs its input (`xargs`, a shell, `tee`) — THEN it SHALL keep blocking.

Traces to PRD: O-4, S-4, AC-4 · F-04 · BL-64 · BUG-54 · AMENDS REQ-W1-018

#### Scenario: Success
GIVEN a Karvey project
WHEN `ls -la .git/karvey/approvals/ 2>/dev/null; echo done`, `cat .git/karvey/ledger/x.json | python3 -m
json.tool`, `ls "$(git rev-parse --git-common-dir)/karvey/approvals/"` or `ls /tmp/claude-plan-approved-*`
runs
THEN it is allowed.

#### Scenario: Error
GIVEN the same project
WHEN `ls .git/karvey/approvals | xargs rm`, `ls .git/karvey/approvals > .git/karvey/approvals/x` or `ls
.git/karvey/ledger && touch .git/karvey/ledger/x.json` runs
THEN it is blocked.

---

## Requirement 5: Regression, security and release (hotfix lane)

### 5.1 REQ-HF-017 — Each incident ships with its regression test
The change SHALL record BUG-53 (F-01) and BUG-54 (F-04) in the incident tracker and index, each with a
regression test that fails on 3.12.0 and passes with the fix, in the same PR (`rules/multi-agent.md` §7).

Traces to PRD: S-5, AC-5 · BUG-53, BUG-54

#### Scenario: Success
GIVEN the fix
WHEN the regression suite runs
THEN the BUG-53 and BUG-54 tests pass; on 3.12.0 they fail.

#### Scenario: Error
GIVEN an incident without a regression test
WHEN the release gate runs
THEN the incident is not `RESUELTO`.

### 5.2 REQ-HF-018 — The guards stay fail-closed and within budget
The prod-gate and protect-paths SHALL stay fail-closed (an error or a timeout blocks), the approval hook SHALL
stay fail-open (no marker), every network lookup SHALL stay within the pre-bash budget, and no guard SHALL log
or forward a credential found in a command.

Traces to PRD: Constraints, S-3 · Security Tier 2 · AMENDS REQ-W1-024

#### Scenario: Success
GIVEN a host CLI that answers in time
WHEN the gate resolves a REST candidate
THEN the decision arrives within the hook timeout and the audit record holds no token.

#### Scenario: Error
GIVEN a host CLI that hangs
WHEN a production candidate is evaluated
THEN it is blocked with the time-out reason.

### 5.3 REQ-HF-019 — Release 3.12.1
The release SHALL carry version 3.12.1 in the plugin manifest, the marketplace entry and `project.json`, a
CHANGELOG `[3.12.1]` section with the behaviour changes (new blocked forms, how to release a multi-repo change)
and an empty `[Unreleased]`, and SHALL pass the full gate and CI before the PR to `main` is merged.

Traces to PRD: S-5, AC-5 · Decision: D-43

#### Scenario: Success
GIVEN the implementation and QA are done
WHEN the release gate runs
THEN every suite passes and the versions agree.

#### Scenario: Error
GIVEN one version string still says 3.12.0
WHEN lint runs
THEN it reports the mismatch.

## Explicit exclusions

- Plan-kind approvals keep the 3.12.0 scope rule (named change in this tree, else active, else `_project`).
- The release manifest (D-37) and "one approval, one change" (BUG-41) are unchanged; a multi-repo binding is
  part of one change's single approval.
- No remote probing of a repository's contents to learn whether it is a Karvey project: the gate decides from
  local clones only, and blocks production-shaped requests it cannot tie to one.
- No reuse of credentials from the command (headers, tokens, `user:pass@` URLs); lookups use the host CLIs'
  own login.
- Classic release approvals and deployment approvals of other hosts are blocked, not resolved.
- Lanes stay recorded data only (Wave 2).
