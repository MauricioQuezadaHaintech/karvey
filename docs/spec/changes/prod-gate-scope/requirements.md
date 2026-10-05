# Requirements: prod-gate-scope

## Project description

Hotfix 3.12.1 (D-43). Real use of 3.12.0 showed a prod approval bound to a change the human did not name
(F-01), a multi-repo change that cannot be released from the repos it does not live in (F-02), REST and
outside-a-repo release forms the prod-gate does not see (F-03), and a read-only listing blocked by
protect-paths (F-04, BL-64). Revision 1 (D-45) adds the defects found in use since: another agent's profile
injected by the session hook (F-05), the prod-gate deciding by the session's directory instead of the PR's
repo (F-06), a prod OK asked through a question tool that never reaches the approval hook (F-07), a silent hook
on a production-shaped phrase (F-08) and an opaque `approve … prod` error (F-09); and it lets production calls
to non-Karvey repos pass with a warning (F-10). North star (PRD): *a production approval reaches exactly the change and the
commits the human approved, whatever repo, working tree or command form the release goes through.*

## Conventions

- **IDs.** `REQ-HF-NNN`, contiguous; the heading also carries the numeric EARS id.
- **Trace line.** PRD objective `O-n` / scope `S-n` / acceptance `AC-n`, finding `F-NN`, incident `BUG-NN`,
  backlog `BL-NN`, decision `D-NN`, and the 3.12.0 requirement it amends (`AMENDS REQ-W1-0NN`, from
  `wave1-hardening`, not yet in the living spec).
- **Roles.** the *session hook* (runs at session start, resume, clear and compact), the *approval hook* (runs
  on the human's prompt), the *state tool* (`karvey-state.py`), the
  *prod-gate* and *protect-paths* (pre-execution guards), the *release ledger* (machine-local approval record
  of a clone), the *owning repo* (the repo whose `docs/spec/changes/` holds the change), a *declared repo*
  (a repo the change lists as released with it), the *working repo* (the git top level of the session's
  directory; for a linked worktree, that worktree), a *Karvey repo* (a local clone that is a Karvey project:
  `docs/spec/project.json` or `docs/spec/changes/`), the *target repo* (the repo a PR or REST call acts on).
  Examples use the fictional repos `app-web`, `app-api`,
  `app-db`.
- **Production approval** = the ledger record of D-34/D-35: human, evidence of the approval hook's audit
  line, bound to an approved head commit, valid 24 h after the human's OK.

---

## Requirement 1: The prod approval is bound to the change the phrase names (F-01, BUG-138)

### 1.1 REQ-HF-001 — A named change wins over the active change
WHEN the human's prompt is a production approval (D-10) and names exactly one change id that exists in the
working tree where the approval hook runs, the approval hook SHALL record the prod marker for that change,
whatever change is active there.

Traces to PRD: O-1, S-1, AC-1 · F-01 · BUG-138 · Decision: D-43 · AMENDS REQ-W1-017

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

Traces to PRD: O-1, S-1, AC-1 · F-01 · BUG-138 · Decision: D-43

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

Traces to PRD: O-1, S-1 · F-01 · BUG-138 · Decision: D-43

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

Traces to PRD: O-1, S-1 · F-01 · BUG-138 · Decision: D-37 (manifest path unchanged), D-43

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

### 3.5 REQ-HF-014 — Commands outside a repository are tied to the repo they name *(revised, rev 1, D-45; rev 2)*
WHEN a production merge candidate (CLI or REST) runs in a directory that is not inside a Karvey project (for
example after `cd /tmp`), the prod-gate SHALL tie it to a local clone by the repository the command names (its
repo option, the PR URL, the request URL, the PR the host reports) among the session's project, its worktrees,
the repos its `project.json` and its changes' `spec.json:repos` name, and the command's directory; a Karvey
clone SHALL get the full check (REQ-HF-024, 025); a target that is not a Karvey repo SHALL pass with the warning
of REQ-HF-026; IF the command names a Karvey repo (by `project.json` or a change's `spec.json:repos`) of which no
local clone is found, THEN the prod-gate SHALL allow it only when the host reports the PR's base as the project's
integration branch, and otherwise (any other base, or one that cannot be determined) SHALL block with the reason
and say to run the command from the repo's clone. The search also covers the folders below a session directory
that is not a repo. *(rev 2, QA F-12: a production branch not named main/master was let through.)*

Traces to PRD: O-3, O-6, S-3, S-7, AC-3, AC-7 · F-03, F-10, F-12 · Decision: D-43, D-45 · AMENDS REQ-W1-024

#### Scenario: Success
GIVEN a session in the clone `app-web` (Karvey) with a live approval bound to the PR head
WHEN `cd /tmp && gh pr merge 7 -R org/app-web` runs
THEN it is checked against `app-web`'s ledger and allowed; a PR into `dev` from `/tmp` is not gated.

#### Scenario: Error
GIVEN a session in `app-api`, whose `project.json` names `app-web` as a repo, and no local clone of `org/app-web`
WHEN `cd /tmp && az repos pr update --id 7 --repository app-web --status completed` runs on a PR into `main`
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

## Requirement 4: Read-only listings of the protected paths (F-04, BL-64, BUG-139)

### 4.1 REQ-HF-016 — A read-only listing passes; writes stay blocked
WHEN every command of a Bash call that names a protected path (approval markers, release ledger, the Karvey
state directories, the compat marker) only reads it, and the other commands of the call neither take paths
from it nor write (text output, formatters, read-only `git` subcommands in a command substitution), protect-paths
SHALL allow the call; IF any command could write a protected path — a mutating command, a redirection into it,
a pipe into a command that runs its input (`xargs`, a shell, `tee`) — THEN it SHALL keep blocking.

Traces to PRD: O-4, S-4, AC-4 · F-04 · BL-64 · BUG-139 · AMENDS REQ-W1-018

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
The change SHALL record BUG-138 (F-01), BUG-139 (F-04), BUG-140 (F-05), BUG-141 (F-06), BUG-142 (F-07),
BUG-143 (F-08) and BUG-144 (F-09) in the incident tracker and index, each with a regression test (unit test or
guard-table row) that fails on 3.12.0 and passes with the fix, in the same PR (`rules/multi-agent.md` §7).
*(revised, rev 1: BUG-140..144 added; BUG-53/54 renumbered, F-11)*

Traces to PRD: S-5, AC-5 · BUG-138 .. BUG-144

#### Scenario: Success
GIVEN the fix
WHEN the regression suite runs
THEN the BUG-138 .. BUG-144 tests pass; on 3.12.0 they fail.

#### Scenario: Error
GIVEN an incident without a regression test
WHEN the release gate runs
THEN the incident is not `RESUELTO`.

### 5.2 REQ-HF-018 — The guards stay fail-closed and within budget
The prod-gate and protect-paths SHALL stay fail-closed (an error or a timeout blocks), the approval hook SHALL
stay fail-open (no marker, and its one line says the approval was not recorded because of an error), the session
hook SHALL never block a session and, on any error while resolving the profile, SHALL inject no profile content
(an error never discloses a manifest, board or handoff), every network lookup SHALL stay within the pre-bash
budget, and no guard SHALL log or forward a credential found in a command. *(revised, rev 1: session hook and
the approval hook's error line)*

Traces to PRD: Constraints, S-3, S-6, S-8 · Security Tier 2 · AMENDS REQ-W1-024

#### Scenario: Success
GIVEN a host CLI that answers in time
WHEN the gate resolves a REST candidate
THEN the decision arrives within the hook timeout and the audit record holds no token.

#### Scenario: Error
GIVEN a host CLI that hangs, or a team configuration that cannot be parsed
WHEN a production candidate is evaluated, or a session starts
THEN the candidate is blocked with the time-out reason, and the session gets no profile content and one line
with the reason.

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

---

## Requirement 6: The agent profile comes from the working repo only (F-05, BUG-140)

### 6.1 REQ-HF-020 — The profile is resolved from the working repo, never from an ancestor folder
WHEN the session hook runs, it SHALL take the working repo as the git top level of the session's directory and
SHALL inject a profile only when that repo holds it (`docs/spec/agent/` at its top level) or a team configuration
maps that repo, by its exact name (a linked worktree by the name of its main clone), to a role; it SHALL NOT walk
up past the working repo's top level to find a profile, SHALL NOT fall back to a default role for an unmapped repo,
and IF the session's directory is not inside a git repo or the repo is not mapped, THEN it SHALL inject no
manifest, board or handoff and SHALL print one line saying why and how to restore explicitly (REQ-HF-023).

Traces to PRD: O-5, S-6, AC-6 · F-05 · BUG-140 · Decision: D-45

#### Scenario: Success
GIVEN a team folder holding the repos `app-web` and `app-api`, with a team configuration that maps `app-web` to
the role `web` and `app-api` to the role `api`
WHEN a session starts in `app-web/src/`
THEN it receives the `web` profile only.

#### Scenario: Error
GIVEN the same team folder and a session that starts (or resumes) in the team folder itself, in a folder of the
`api` agent's profile area that is not inside `app-api`, or in an unmapped repo `app-tools`
WHEN the session hook runs
THEN no profile is injected and one line says `profile not loaded: <reason>` with the explicit restore command.

### 6.2 REQ-HF-021 — An ambiguous identity injects nothing
IF the directory the session started in and its current directory resolve to different working repos (the
directory changed, for example on resume), or more than one profile is a candidate for the working repo (the repo
holds its own profile and a team configuration maps it too, or two roles map it), THEN the session hook SHALL
inject no manifest, board or handoff and SHALL print exactly one line naming the candidate profiles and the
command to restore one explicitly.

Traces to PRD: O-5, S-6, AC-6 · F-05 · BUG-140 · Decision: D-45

#### Scenario: Success
GIVEN a session started in `app-web` and resumed in `app-web`
WHEN the session hook runs
THEN the `web` profile is injected as before.

#### Scenario: Error
GIVEN a session started in `app-web` and resumed with its directory in `app-api`
WHEN the session hook runs
THEN nothing is injected and the line reads `profile not loaded: candidates web (app-web), api (app-api) — run
/karvey-checkpoint restore --profile <role|path> in the repo you work in`.

### 6.3 REQ-HF-022 — A sensitive handoff never leaves its repo
WHERE a handoff is marked sensitive (front matter `sensitive: true`, which `/karvey-checkpoint save --sensitive`
writes), the session hook and `/karvey-checkpoint restore` SHALL show its body only in a session whose working repo
is the profile's own repo (the repo the team configuration maps to the role, or the repo that holds
`docs/spec/agent/`); IF the working repo differs or cannot be determined, THEN they SHALL withhold the body and
print one line saying a sensitive handoff was withheld and in which repo it can be restored.

Traces to PRD: O-5, S-6, AC-6 · F-05 · BUG-140 · Decision: D-45

#### Scenario: Success
GIVEN the `ops` profile with a handoff marked sensitive, mapped to the repo `app-ops`
WHEN a session starts in `app-ops`
THEN the handoff is injected.

#### Scenario: Error
GIVEN the same handoff
WHEN a session in `app-web` runs `/karvey-checkpoint restore --profile ops`
THEN the manifest and board may be shown, the handoff body is not, and the line names `app-ops`.

### 6.4 REQ-HF-023 — Restoring a profile explicitly
WHEN the human or the agent runs `/karvey-checkpoint restore --profile <role|path>`, the skill SHALL restore that
profile (manifest, board, handoff under REQ-HF-022, live-state comparison) in the current session and SHALL say
which profile it restored; IF the role or path names no profile, THEN it SHALL restore nothing and list the
profiles it found.

Traces to PRD: O-5, S-6, AC-6 · F-05 · BUG-140 · Decision: D-45

#### Scenario: Success
GIVEN the ambiguity line of REQ-HF-021
WHEN `/karvey-checkpoint restore --profile web` runs in `app-web`
THEN the `web` profile is restored and the reply names it.

#### Scenario: Error
GIVEN no role `mobile`
WHEN `/karvey-checkpoint restore --profile mobile` runs
THEN nothing is restored and the reply lists `web`, `api`.

---

## Requirement 7: The prod-gate decides on the PR's repo and base (F-06, BUG-141)

### 7.1 REQ-HF-024 — The target repo is the PR's repo, not the session's directory
WHEN a production merge candidate names its repo — `--repo`/`-R`, a PR URL as the selector, `az … --repository`
(with `--org`/`--project`), a REST URL — or the host's answer for the PR names it, the prod-gate SHALL take that
repo as the target repo, SHALL find its local clone (REQ-HF-014's search), and SHALL read the branch flow, the
production set and the release ledger from that clone, never from the clone of the session's directory when the
two differ; IF the named repo and the host's answer disagree, THEN it SHALL block with the reason.

Traces to PRD: O-6, S-7, AC-7 · F-06 · BUG-141 · Decision: D-45 · AMENDS REQ-W1-023

#### Scenario: Success
GIVEN a session in `app-web` and a local clone `app-api` with a live approval of `api-login` bound to the PR head
WHEN `gh pr merge 12 --repo org/app-api` runs on the PR `[Deploy] api-login` into `main`
THEN it is checked against `app-api`'s ledger and allowed.

#### Scenario: Error
GIVEN the same, but the approval lives only in `app-web`'s ledger
WHEN the merge runs
THEN it is blocked; the message names `app-api` as the repo whose approval is missing.

### 7.2 REQ-HF-025 — Only a production branch of the target repo is gated
WHEN the prod-gate has resolved the target repo and the PR's base branch from the host's answer, it SHALL gate the
merge only if the base is in the target repo's production set (its `branch_flow.production`, plus `main`/`master`
per D-15, minus its integration branch when that differs); a merge into any other branch, including the target's
integration branch, SHALL pass silently; IF the base cannot be resolved, THEN it SHALL block with the reason.

Traces to PRD: O-6, S-7, AC-7 · F-06 · BUG-141 · Decision: D-15, D-45

#### Scenario: Success
GIVEN a session in `app-web` (trunk flow, production `main`) and `app-api` with integration `dev`, production `main`
WHEN `gh pr merge 30 --repo org/app-api` runs on a PR into `dev`
THEN it passes and prints nothing.

#### Scenario: Error
GIVEN the same, but the PR's base is `main` and no approval exists in `app-api`
WHEN the merge runs
THEN it is blocked.

### 7.3 REQ-HF-026 — A target that is not a Karvey repo passes with a warning *(revised, rev 2)*
WHEN a production merge candidate or a production pipeline approval (CLI or REST) targets a repo that is not a
Karvey repo — its local clone is not a Karvey project, or no local clone exists and neither the session's
`project.json` nor any change's `spec.json:repos` names it — the prod-gate SHALL allow it and SHALL print exactly
one warning line naming the target repo and saying it is not gated because it is not a Karvey repo; a target the
gate cannot identify at all keeps REQ-HF-015. *(rev 2, QA F-12)* Every local clone that answers to the name is
considered and a Karvey one always wins (a look-alike clone never decides). WHEN the call runs in a Karvey
context (its directory, the payload's cwd or the session project is a Karvey project) and no local Karvey clone
answers to the name, the prod-gate SHALL ask the host for the PR and SHALL treat the target as that Karvey repo
when the host's canonical repo answers to a local Karvey clone or the PR head commit is in one (renames, forks,
repo GUIDs); IF the host lookup fails, THEN it SHALL block. The warning applies only when the host shows another
repo.

Traces to PRD: O-6, S-7, AC-7 · F-10, F-12 · Decision: D-45 · AMENDS REQ-W1-024

#### Scenario: Success
GIVEN a session in `app-web` and no local clone of `org/static-site`, not named by `project.json` or any change
WHEN `curl -X PUT https://api.github.com/repos/org/static-site/pulls/3/merge` runs
THEN it passes with `[karvey] prod-gate WARNING: org/static-site is not a Karvey repo — not gated`.

#### Scenario: Error
GIVEN `project.json` names `app-api` and no local clone of it exists
WHEN `curl -X PUT https://api.github.com/repos/org/app-api/pulls/3/merge` runs into `main`
THEN it is blocked (REQ-HF-014), not warned.

---

## Requirement 8: The production OK is typed by the owner (F-07, BUG-142)

### 8.1 REQ-HF-027 — The agent shows the exact phrase to type
WHEN a skill or rule asks the human for the production OK, it SHALL ask in plain text and SHALL show the exact
phrase for the human to type, built from the project's approval vocabulary and naming the change id, the PR and
the version (for example «aprobado para producción app-login PR #42 v2.3.0»), together with the PR head commit;
it SHALL NOT ask for the production OK through a question tool (a tool whose answer does not pass through the
prompt hook), because that answer never reaches the approval hook.

Traces to PRD: O-7, S-8, AC-8 · F-07 · BUG-142 · Decision: D-45, D-10

#### Scenario: Success
GIVEN `karvey-deploy` at the production OK step for `app-login`, PR 42, version 2.3.0
WHEN it asks for the OK
THEN its message shows «aprobado para producción app-login PR #42 v2.3.0» and the head commit, and the human's
typed phrase records `(prod, app-login, …)`.

#### Scenario: Error
GIVEN a skill text that says to ask for the production OK with a question tool
WHEN lint runs
THEN it fails (REQ-HF-028).

### 8.2 REQ-HF-028 — Lint forbids a question tool for the production OK
The plugin linter SHALL report an error for any skill or rule text that instructs a question tool (by name, such
as `AskUserQuestion`, or as "question tool") in the same step or paragraph as the production OK (production
approval, prod OK, prod marker), and SHALL accept question tools for other questions.

Traces to PRD: O-7, S-8, AC-8 · F-07 · BUG-142 · Decision: D-45

#### Scenario: Success
GIVEN `karvey-deploy` step 2.9 rewritten to show the phrase, and `karvey-architecture` using a question tool for a
design choice
WHEN lint runs
THEN it reports 0 errors.

#### Scenario: Error
GIVEN a fixture skill whose production step says "Ask with `AskUserQuestion` for the production OK"
WHEN lint runs
THEN it reports one error naming the file and line.

---

## Requirement 9: A production-shaped phrase always gets one answer line (F-08, BUG-143)

### 9.1 REQ-HF-029 — Exactly one line: recorded, or not recorded with the reason and the phrase
WHEN the human's prompt holds an approval word and a production word (D-10) outside quoted or fenced material, the
approval hook SHALL print exactly one line: either `approval recorded (<kind>, <change>, expires <hh:mm>)`, or
`prod approval NOT recorded: <reason>` followed, on the same line, by the phrase to type (change id from the
candidates when there is exactly one, otherwise `<change-id>`); the reasons SHALL cover at least: no change named
and none or several active (REQ-HF-003), a named change not in this tree (REQ-HF-002), several changes named
(REQ-HF-004), the phrase classified as a plan approval, and an internal error (REQ-HF-018); a plan marker recorded
from such a phrase SHALL be said to be a plan approval and not a production one, on that same line.

Traces to PRD: O-7, S-8, AC-8 · F-08 · BUG-143 · Decision: D-45 · AMENDS REQ-W1-017

#### Scenario: Success
GIVEN only `app-login` active
WHEN the human writes «ok, aprobado para producción app-login»
THEN the hook prints one line `[karvey] approval recorded (prod, app-login, expires 15:40)`.

#### Scenario: Error
GIVEN `app-login` and `app-search` active
WHEN the human writes «dale, sube a producción»
THEN the hook prints one line `[karvey] prod approval NOT recorded: no change named and 2 active (app-login,
app-search) — type: «aprobado para producción <change-id>»`, and no prod marker is written.

---

## Requirement 10: The `approve … prod` refusal names what it found (F-09, BUG-144)

### 10.1 REQ-HF-030 — The refusal lists the markers found and the missing piece
IF `approve <id> prod` is refused, THEN the state tool SHALL print each approval marker it considered (kind,
change, age in minutes, expired or not) — or that it found none — and SHALL name the missing piece: no marker, a
marker of another kind, a marker of another change, an expired marker, no audit line, or a missing or unbound
commit; it SHALL end with the phrase the human types to fix it.

Traces to PRD: O-8, S-9, AC-9 · F-09 · BUG-144 · Decision: D-45

#### Scenario: Success
GIVEN a live prod marker of `app-login`
WHEN `approve app-login prod --by "<human>" --role human --ref D-12 --sha <head>` runs
THEN it records the approval (no refusal text).

#### Scenario: Error
GIVEN only a plan marker of `app-login` 12 minutes old and an expired prod marker of `app-search`
WHEN `approve app-login prod …` runs
THEN it is refused with `found: plan app-login 12 min (live); prod app-search 95 min (expired) — missing: a live
prod marker for app-login; the human types «aprobado para producción app-login PR #<n> v<version>»`.

---

## Requirement 11: A checkpoint save needs no plan approval (F-22, BUG-154)

### 11.1 REQ-HF-031 — The plan-gate exempts the checkpoint and handoff files only
WHEN the plan-gate is on and a tool call writes only checkpoint or handoff state files — `docs/spec/changes/<id>/checkpoint.md`,
`docs/spec/checkpoint.md`, and the resolved profile's `handoff.md`, `state.json` and board (solo:
`docs/spec/agent/`; team: `{ops_repo}/agents/<role>/` and `{ops_repo}/board/<role>.md`) — named directly (no
symlink on the way, no `..`, no variable or glob), the plan-gate SHALL allow it without an approval marker; IF the
same call writes or destroys anything else, or the path is an approval marker, the ledger, a `spec.json`,
`decisions.md`, another agent's profile, or code, THEN the plan-gate SHALL keep requiring the marker. Committing
those files is not gated by the plan-gate (it never gates commits); the checkpoint skill commits them by explicit
path, alone, and says that a save never needs a plan approval.

Traces to PRD: O-5, S-6 · F-22 · BUG-154 · Decision: D-46 (owner, verbatim: «los save de checkpoint no pueden estar sujetos a aprobación, eso es totalmente ridículo»)

#### Scenario: Success
GIVEN `enforcement.plan_gate_hook: true` and a plan marker that expired 200 minutes ago
WHEN `/karvey-checkpoint save` writes `docs/spec/agent/handoff.md` (Write tool or a here-document)
THEN it is allowed with no approval.

#### Scenario: Error
GIVEN the same project
WHEN the call writes `docs/spec/changes/feat-a/spec.json`, `docs/spec/agent/../../../src/a.py`, a `handoff.md` that is
a symlink to code, another agent's handoff, or the handoff together with `echo y > src/a.py` or `rm -rf src`
THEN it is blocked as before.

---

## Requirement 12: Approval model — investigation is free, an approved plan runs to the end (D-47, F-23)

### 12.1 REQ-HF-032 — The plan-gate gates only consequential actions
WHILE the plan-gate is on, it SHALL require an approved plan only for consequential actions: deleting tracked
files or folders (`rm -r`/`rm -rf`, `rm`, `mv`, `truncate`, `shred` over a tracked file, `git rm`, `find -delete`,
`git clean`), discarding or rewriting history (`git reset --hard`, `git checkout --`/`git restore` of the work
tree, force pushes, `filter-branch`/`filter-repo`), database statements that write data or schema (`INSERT`,
`UPDATE`, `DELETE`, `MERGE`, `DROP`, `TRUNCATE`, `ALTER`, `CREATE`, `GRANT`, `REVOKE`, `EXEC` through `sqlcmd`,
`psql`, `mysql`, `sqlite3` and the other SQL clients), installing, removing or upgrading software (`apt`,
`dnf`, `yum`, `pip`/`pipx` outside a virtual environment, `npm`/`yarn`/`pnpm` global, `brew`, `winget`,
`choco`, `snap`, `cargo install`, `go install`, `gem install`, `az`/`gh` extensions), a PR to or a merge into a
production branch, deploys (`func … publish`, `az webapp`/`functionapp`/`containerapp` deploys, `kubectl
apply`, `helm install|upgrade`, `docker push`, `vercel --prod`, `netlify deploy --prod`, `firebase deploy`,
`gcloud app|run deploy`), and infrastructure changes (`terraform`/`tofu` `apply|destroy|import`, `az deployment`,
`az … create|delete|update`, `gcloud … create|delete|update`, `aws … create-|delete-|update-|put-`, `kubectl
delete|patch|scale`, `pulumi up|destroy`); IF a command cannot be parsed and its text matches one of these
classes, THEN it SHALL be gated. Everything else SHALL NOT be gated: reads, searches, read-only queries
(`SELECT`), running bash or python, creating and running scratch scripts, writing files with redirections,
`sed -i`, and the checkpoint/handoff files (REQ-HF-031). File edits (Edit/Write tools and write redirections)
SHALL be gated only when the project opts in with `enforcement.plan_gate_edits: true` (default off).

Traces to PRD: O-7, S-8 · F-23 · Decision: D-47 · AMENDS REQ-W1-014, REQ-W1-016

#### Scenario: Success
GIVEN `plan_gate_hook: true`, no plan approval
WHEN the agent runs `python3 scratch.py > out.txt`, `psql -c 'SELECT * FROM t'`, `sed -i s/a/b/ notes.md`, or
edits `src/a.py`
THEN nothing is gated.

#### Scenario: Error
GIVEN the same project
WHEN the agent runs `rm src/a.py` (tracked), `sqlcmd -Q "UPDATE t SET a=1 WHERE id=2"`, `pip install requests`,
`kubectl apply -f k.yaml` or `gh pr create --base main`
THEN each is blocked until the human approves the plan.

### 12.2 REQ-HF-033 — A plan approval lasts until the plan ends or the human says stop
WHEN the human approves a plan, the approval SHALL stay valid with no time limit until the phase it was given for
closes (the state tool consumes it) or the human says stop in their own message (`detente`, `para`, `stop`,
`alto`, `basta`, `cancela`, alone or opening the message); THEN the approval hook SHALL withdraw every live plan
approval of the clone and print one line saying so. A production approval keeps D-35: the release ledger binds it
for 24 h after the human's OK, and a prod marker counts for `approve … prod` for those 24 h.

Traces to PRD: O-7, S-8 · F-23 · Decision: D-47, D-35 · AMENDS REQ-W1-016

#### Scenario: Success
GIVEN a plan approved three days ago and its phase still open
WHEN the agent runs a consequential action of the plan
THEN it is allowed.

#### Scenario: Error
GIVEN the same approval
WHEN the human writes «detente»
THEN the hook prints `[karvey] plan approval withdrawn (stop)` and the next consequential action is blocked.

### 12.3 REQ-HF-034 — One message approves the plan and production
WHEN the human's approval of a plan holds a production word and names the change (D-10), the approval hook SHALL
record a prod marker that is also the plan approval; recording it with `approve … prod` SHALL keep it as the plan
approval for the rest of the plan; the deploy skill SHALL record an existing prod marker with `approve … prod`
and SHALL ask for the production OK only when that command refuses.

Traces to PRD: O-7, S-8 · F-23 · Decision: D-47, D-10, D-45

#### Scenario: Success
GIVEN «aprobado el plan de release de app-login, incluido el paso a producción»
WHEN the deploy skill reaches the production step
THEN `approve app-login prod …` succeeds without asking again, and later consequential steps of the plan pass.

#### Scenario: Error
GIVEN a plan approval without a production word
WHEN the deploy skill reaches the production step
THEN `approve … prod` refuses and the skill shows the phrase to type (REQ-HF-027).

### 12.4 REQ-HF-035 — Skills never ask approval for investigation or housekeeping, nor re-ask
The skills and rules SHALL state that investigation (reads, searches, read-only queries, scratch scripts) and
housekeeping (checkpoint, handoff, board, notes, scratch) never need an approval, that an approval already given
is never asked again, that pending work is not re-explained as a way to ask again, and that inside an approved
plan the agent proceeds until a real blocker; the linter SHALL report an error for a skill or rule that instructs
asking for approval, permission or confirmation before reading, searching, investigating or running a read-only
query.

Traces to PRD: O-7, S-8 · F-23 · Decision: D-47

#### Scenario: Success
GIVEN the plugin's skills and rules
WHEN lint runs
THEN it reports no such instruction.

#### Scenario: Error
GIVEN a skill that says "ask the user for approval before searching the repository"
WHEN lint runs
THEN it reports an error with file and line.

### 12.5 REQ-HF-036 — The owner's personal files are aligned by a diff the owner applies
The change SHALL prepare, without applying it, a diff of the owner's personal instructions and plan hook aligned
with D-47 (investigation free, consequential actions need an approved plan, the approval lasts until the plan ends
or the owner says stop), kept outside the repository (D-01, D-11).

Traces to PRD: O-7 · F-23 · Decision: D-47, D-01, D-11

#### Scenario: Success
GIVEN the hotfix release
WHEN the report is given
THEN it names the diff's path and the files are unchanged.

#### Scenario: Error
GIVEN any step of the change
WHEN a write to the owner's personal files is attempted
THEN it is not done (the diff is the deliverable).

## Explicit exclusions

- Plan-kind approvals keep the 3.12.0 scope rule (named change in this tree, else active, else `_project`); what they gate and how long they last change with REQ-HF-032, 033 (D-47).
- The release manifest (D-37) and "one approval, one change" (BUG-41) are unchanged; a multi-repo binding is
  part of one change's single approval.
- No remote probing of a repository's contents to learn whether it is a Karvey project: the gate decides from
  local clones only, and blocks production-shaped requests it cannot tie to one.
- No reuse of credentials from the command (headers, tokens, `user:pass@` URLs); lookups use the host CLIs'
  own login.
- Classic release approvals and deployment approvals of other hosts are blocked, not resolved.
- Lanes stay recorded data only (Wave 2).
- A team folder that is not itself a git repo gets no automatic profile; `/karvey-checkpoint restore --profile`
  restores one explicitly (REQ-HF-020, 023).
- Question tools stay allowed for every question other than the production OK; whether a plan-kind gate approval
  answered through a question tool should also be typed is not decided here.
- No remote probing to learn whether a target is a Karvey repo (REQ-HF-026 decides from local clones and the
  repos the project and its changes name).

## Revision history

| Rev | Date | Ref | Requirements | Why |
|---|---|---|---|---|
| 4 | 2026-10-05 | D-47 · F-23 | ADDED REQ-HF-032..036 | Owner instruction: investigation is free, only consequential actions need an approved plan, the approval lasts until the plan ends or the human says stop, one message approves the plan and production. |
| 3 | 2026-10-05 | D-46 · F-22 | ADDED REQ-HF-031 | The owner reported that a checkpoint save was blocked by the plan-gate (D-46); routed through karvey-iterate as BUG-154. |
| 2 | 2026-10-05 | QA F-12..F-17 | REVISED REQ-HF-014 (a Karvey repo with no clone passes only into the integration branch; folders below a non-repo session directory searched), REQ-HF-026 (a Karvey clone wins over look-alikes; in a Karvey context the host's answer decides; a failed lookup blocks) | The QA review (security, code, D7 second opinion) found the warning path reachable for Karvey targets. Tightened in place in the QA loop (stricter, fail closed); the owner confirms it with the QA approval. |
| 1 | 2026-10-05 | D-45 · F-05..F-11 | ADDED REQ-HF-020..030; REVISED REQ-HF-014 (non-Karvey targets warn), REQ-HF-017 (BUG-138..144), REQ-HF-018 (session hook, approval-hook error line); BUG-53/54 renumbered to BUG-138/139 | The owner widened the hotfix with the defects found in use (D-45). BUG-53/54 were already used by another unmerged branch (F-11). Ripple: prd.md (problems 5-9, O-5..O-8, S-6..S-9, AC-6..AC-9), findings.md, spec-delta.md, PLAN.md, spec.json, backlog BL-64. Revised in place while requirements are generated and not approved. |
