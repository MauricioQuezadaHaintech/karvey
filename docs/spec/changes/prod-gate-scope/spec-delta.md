# Spec Delta: prod-gate-scope

Against the living spec `docs/spec/specs/method/spec.md` (capability `method`). Scenarios for every block are
in `requirements.md`; the living spec keeps the compact form. The 3.12.0 requirements this change amends
(REQ-W1-017, 018, 023, 024) reach the living spec through `wave1-hardening`'s spec-delta, which is not merged
yet; they are cited as *amends* here and the amendment is ADDED, so the merge order of the two changes does
not matter.

Summary: **ADDED 36** (REQ-HF-001..036; revision 4, D-47: REQ-HF-032..036; revision 3, D-46: REQ-HF-031; revision 1, D-45: REQ-HF-020..030 added, REQ-HF-014/017/018 revised) · **MODIFIED 0** · **REMOVED 0**.

## ADDED Requirements

### ADDED by `prod-gate-scope` (3.12.1)

Traced to `docs/spec/changes/prod-gate-scope/prd.md`.

### The prod approval is bound to the change the phrase names (F-01, BUG-138)
- **REQ-HF-001** — A named change wins over the active change. WHEN the human's prompt is a production approval and names exactly one change id that exists in the working tree where the approval hook runs, the approval hook SHALL record the prod marker for that change, whatever change is active there. *(Traces: O-1, S-1, AC-1 · F-01 · BUG-138 · D-43 · amends REQ-W1-017)*
- **REQ-HF-002** — A named change that is not in this tree records nothing. IF a production approval names a change id that does not exist in the working tree where the approval hook runs, THEN the approval hook SHALL record no marker and SHALL print that the change is not in this tree and how to fix it (the local worktree that holds it, else the branch that holds it, else open the session where the change lives). *(Traces: O-1, S-1, AC-1 · F-01 · BUG-138 · D-43)*
- **REQ-HF-003** — No change named: the single active change, said out loud. WHEN a production approval names no change id, the approval hook SHALL record the prod marker for the active change only when exactly one change is active, and SHALL say so in the hook line; IF none or several are active, THEN it SHALL record no marker and print the candidates. *(Traces: O-1, S-1 · F-01 · BUG-138 · D-43)*
- **REQ-HF-004** — Several named changes record nothing. IF a production approval names more than one change id, THEN the approval hook SHALL record no marker and ask for one message per change. *(Traces: O-1, S-1 · F-01 · BUG-138 · D-37, D-43)*

### Multi-repo release under the owning repo's approval (F-02)
- **REQ-HF-005** — A change declares the repos it releases in `spec.json:repos` (repo names); the state tool validates it as a list of non-empty names. *(Traces: O-2, S-2 · F-02 · D-43)*
- **REQ-HF-006** — The owning repo binds each declared repo's release commit into the change's existing production approval, keeping its expiry; it refuses an undeclared repo, a missing, incomplete or expired approval, a non-full commit id, or a repo already bound to another commit. *(Traces: O-2, S-2, AC-2 · F-02 · D-35, D-43)*
- **REQ-HF-007** — A declared repo's `[Deploy] <id>` PR is allowed only when the owning repo's local clone holds the change, the change declares this repo, and the owning repo's production approval is complete, unexpired and binds this repo to the commit being released; otherwise it is blocked. *(Traces: O-2, S-2, AC-2 · F-02 · D-34, D-35, D-43 · amends REQ-W1-023)*
- **REQ-HF-008** — The BLOCK message names the owning repo and its path when found, the human's step and the state tool commands to run there; when the owning clone is not found, where the gate looked and how to make it findable. *(Traces: O-2, S-2, AC-2 · F-02 · D-43)*
- **REQ-HF-009** — The state tool answers the prod-gate's question for a declared repo (`check-prod <id> --repo <name> --sha <commit>`). *(Traces: O-2, S-2 · F-02)*

### REST and outside-a-repo coverage (F-03)
- **REQ-HF-010** — REST PR completions (Azure Repos PATCH to status completed or auto-complete; GitHub PUT merge; GitLab PUT merge) are production merge candidates with the same SHA-bound check; a commit the request binds must be the approved one for a deferred completion. *(Traces: O-3, S-3, AC-3 · F-03 · D-35, D-43 · amends REQ-W1-023)*
- **REQ-HF-011** — REST writes of a production branch (refs, merges endpoints) are blocked with "merge through a PR". *(Traces: O-3, S-3 · F-03 · BUG-28)*
- **REQ-HF-012** — REST approvals of a waiting pipeline run are resolved to the run's branch and commit; a production run is allowed only when the change's approval covers its commit (the approved head or a merge commit with it as a parent); what cannot be resolved is blocked with the reason. *(Traces: O-3, S-3, AC-3 · F-03 · D-35, D-43)*
- **REQ-HF-013** — Reads, non-completing updates and rejections pass silently. *(Traces: O-3, S-3, AC-3 · F-03)*
- **REQ-HF-014** — A candidate that runs outside a Karvey project is tied to a local clone by the repository it names (session project, worktrees, repos named by `project.json` and `spec.json:repos`, the command's directory); a Karvey clone gets the full check; a non-Karvey target passes with a warning (REQ-HF-026); a named Karvey repo with no local clone passes only into the project's integration branch, else it is blocked with "run it from the clone" (rev 2). *(Traces: O-3, O-6, S-3, S-7, AC-3, AC-7 · F-03, F-10 · D-43, D-45 · amends REQ-W1-024)*
- **REQ-HF-015** — Unreadable bodies, variable-built URLs or bodies and inline scripts that call completion or approval endpoints are blocked with the reason; the gate never sends a credential found in the command. *(Traces: O-3, S-3 · F-03 · D-43 · amends REQ-W1-024)*

### Read-only listings of the protected paths (F-04, BL-64, BUG-139)
- **REQ-HF-016** — A call whose commands only read a protected path, together with commands that neither take paths from it nor write, passes protect-paths; any command that could write a protected path keeps it blocked. *(Traces: O-4, S-4, AC-4 · F-04 · BL-64 · BUG-139 · amends REQ-W1-018)*

### Regression, security and release (hotfix lane)
- **REQ-HF-017** — BUG-138 .. BUG-144 ship with regression tests in the same PR. *(Traces: S-5, AC-5)*
- **REQ-HF-018** — The prod-gate and protect-paths stay fail-closed, the approval hook fail-open (its line says it did not record because of an error), the session hook never blocks and injects no profile content on an error, lookups stay within the pre-bash budget, and no guard logs or forwards a credential found in a command. *(Traces: Constraints, S-3, S-6, S-8 · Security Tier 2 · amends REQ-W1-024)*
- **REQ-HF-019** — Release 3.12.1: versions agree, CHANGELOG `[3.12.1]` with the behaviour changes, empty `[Unreleased]`, full gate and CI green. *(Traces: S-5, AC-5 · D-43)*

### The agent profile comes from the working repo only (F-05, BUG-140)
- **REQ-HF-020** — The session hook injects a profile only when the working repo (git top level of the session's directory) holds it or a team configuration maps that repo by exact name to a role; no walk past the repo's top level, no default role; otherwise nothing is injected and one line says why. *(Traces: O-5, S-6, AC-6 · F-05 · BUG-140 · D-45)*
- **REQ-HF-021** — When the starting and current directories resolve to different working repos, or several profiles are candidates, nothing is injected and one line names the candidates and the explicit restore command. *(Traces: O-5, S-6, AC-6 · F-05 · BUG-140 · D-45)*
- **REQ-HF-022** — A handoff marked `sensitive: true` is shown only in a session whose working repo is the profile's own repo; elsewhere its body is withheld with one line naming that repo. *(Traces: O-5, S-6, AC-6 · F-05 · BUG-140 · D-45)*
- **REQ-HF-023** — `/karvey-checkpoint restore --profile <role|path>` restores a named profile explicitly and says which; an unknown one restores nothing and lists the profiles found. *(Traces: O-5, S-6, AC-6 · F-05 · BUG-140 · D-45)*

### The prod-gate decides on the PR's repo and base (F-06, F-10, BUG-141)
- **REQ-HF-024** — The target repo of a merge candidate is the repo it names (`--repo`/`-R`, PR URL, `--repository`, REST URL, host answer); flow, production set and ledger are read from that repo's local clone, never from the session's directory when they differ; a disagreement is blocked. *(Traces: O-6, S-7, AC-7 · F-06 · BUG-141 · D-45 · amends REQ-W1-023)*
- **REQ-HF-025** — Only a base in the target repo's production set (`branch_flow.production`, `main`/`master` per D-15, minus a differing integration branch) is gated; any other base passes silently; an unresolved base is blocked. *(Traces: O-6, S-7, AC-7 · F-06 · BUG-141 · D-15, D-45)*
- **REQ-HF-026** — A production merge or pipeline approval whose target is not a Karvey repo passes with exactly one warning line; a local Karvey clone answering to the name always wins, and in a Karvey context the host's answer (canonical repo, PR head commit) decides, a failed lookup blocking (rev 2); an unidentifiable target keeps REQ-HF-015. *(Traces: O-6, S-7, AC-7 · F-10 · D-45 · amends REQ-W1-024)*

### The production OK is typed by the owner (F-07, BUG-142)
- **REQ-HF-027** — Skills and rules ask for the production OK in plain text, showing the exact phrase (change id, PR, version) and the head commit; never through a question tool. *(Traces: O-7, S-8, AC-8 · F-07 · BUG-142 · D-10, D-45)*
- **REQ-HF-028** — Lint reports an error when a skill or rule instructs a question tool for the production OK; other questions may use it. *(Traces: O-7, S-8, AC-8 · F-07 · BUG-142 · D-45)*

### One answer line for a production-shaped phrase (F-08, BUG-143)
- **REQ-HF-029** — A prompt with approval and production words (outside quotes) gets exactly one hook line: recorded (kind, change, expiry) or NOT recorded with the reason and the phrase to type; a plan marker from such a phrase is said to be a plan approval. *(Traces: O-7, S-8, AC-8 · F-08 · BUG-143 · D-45 · amends REQ-W1-017)*

### The `approve … prod` refusal names what it found (F-09, BUG-144)
- **REQ-HF-030** — A refused `approve <id> prod` lists each marker considered (kind, change, age, expired) or none, names the missing piece and ends with the phrase to type. *(Traces: O-8, S-9, AC-9 · F-09 · BUG-144 · D-45)*

### A checkpoint save needs no plan approval (F-22, BUG-154)
- **REQ-HF-031** — The plan-gate allows, with no marker, a call that writes only checkpoint/handoff state files (change and project `checkpoint.md`, the resolved profile's `handoff.md`, `state.json`, board), named directly (no symlink, no `..`); any other write, destructive command or protected path in the call keeps the marker requirement. *(Traces: O-5, S-6 · F-22 · BUG-154 · D-46)*

### Approval model (D-47, F-23)
- **REQ-HF-032** — The plan-gate gates only consequential actions (deleting tracked files, discarding or rewriting history, database writes, software changes, PRs/merges to production, deploys, infrastructure); reads, queries, scripts, redirections and edits are free; edits are gated only with `enforcement.plan_gate_edits: true`. *(Traces: O-7, S-8 · F-23 · D-47 · amends REQ-W1-014, 016)*
- **REQ-HF-033** — A plan approval has no time limit: it ends when its phase closes or the human says stop (the hook withdraws it and says so); a production approval keeps D-35's 24 h. *(Traces: O-7, S-8 · F-23 · D-47, D-35)*
- **REQ-HF-034** — A plan approval with a production word naming the change is also the production OK; recording it keeps the plan approval; the deploy skill asks only when `approve … prod` refuses. *(Traces: O-7, S-8 · F-23 · D-47, D-10)*
- **REQ-HF-035** — Skills never ask approval for investigation or housekeeping, never re-ask, and proceed inside an approved plan; lint flags instructions to ask approval before reading or investigating. *(Traces: O-7, S-8 · F-23 · D-47)*
- **REQ-HF-036** — The owner's personal files are aligned by a diff the owner applies. *(Traces: O-7 · F-23 · D-47, D-01, D-11)*
