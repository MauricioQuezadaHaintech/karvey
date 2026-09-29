# Spec Delta: prod-gate-scope

Against the living spec `docs/spec/specs/method/spec.md` (capability `method`). Scenarios for every block are
in `requirements.md`; the living spec keeps the compact form. The 3.12.0 requirements this change amends
(REQ-W1-017, 018, 023, 024) reach the living spec through `wave1-hardening`'s spec-delta, which is not merged
yet; they are cited as *amends* here and the amendment is ADDED, so the merge order of the two changes does
not matter.

Summary: **ADDED 19** (REQ-HF-001..019) · **MODIFIED 0** · **REMOVED 0**.

## ADDED Requirements

### ADDED by `prod-gate-scope` (3.12.1)

Traced to `docs/spec/changes/prod-gate-scope/prd.md`.

### The prod approval is bound to the change the phrase names (F-01, BUG-53)
- **REQ-HF-001** — A named change wins over the active change. WHEN the human's prompt is a production approval and names exactly one change id that exists in the working tree where the approval hook runs, the approval hook SHALL record the prod marker for that change, whatever change is active there. *(Traces: O-1, S-1, AC-1 · F-01 · BUG-53 · D-43 · amends REQ-W1-017)*
- **REQ-HF-002** — A named change that is not in this tree records nothing. IF a production approval names a change id that does not exist in the working tree where the approval hook runs, THEN the approval hook SHALL record no marker and SHALL print that the change is not in this tree and how to fix it (the local worktree that holds it, else the branch that holds it, else open the session where the change lives). *(Traces: O-1, S-1, AC-1 · F-01 · BUG-53 · D-43)*
- **REQ-HF-003** — No change named: the single active change, said out loud. WHEN a production approval names no change id, the approval hook SHALL record the prod marker for the active change only when exactly one change is active, and SHALL say so in the hook line; IF none or several are active, THEN it SHALL record no marker and print the candidates. *(Traces: O-1, S-1 · F-01 · BUG-53 · D-43)*
- **REQ-HF-004** — Several named changes record nothing. IF a production approval names more than one change id, THEN the approval hook SHALL record no marker and ask for one message per change. *(Traces: O-1, S-1 · F-01 · BUG-53 · D-37, D-43)*

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
- **REQ-HF-014** — A candidate that runs outside a Karvey project is tied to a local clone by the repository it names; a Karvey clone gets the full check, a non-Karvey clone is not gated, and no match with a production or unknown base is blocked with "run it from the clone". *(Traces: O-3, S-3, AC-3 · F-03 · D-43 · amends REQ-W1-024)*
- **REQ-HF-015** — Unreadable bodies, variable-built URLs or bodies and inline scripts that call completion or approval endpoints are blocked with the reason; the gate never sends a credential found in the command. *(Traces: O-3, S-3 · F-03 · D-43 · amends REQ-W1-024)*

### Read-only listings of the protected paths (F-04, BL-64, BUG-54)
- **REQ-HF-016** — A call whose commands only read a protected path, together with commands that neither take paths from it nor write, passes protect-paths; any command that could write a protected path keeps it blocked. *(Traces: O-4, S-4, AC-4 · F-04 · BL-64 · BUG-54 · amends REQ-W1-018)*

### Regression, security and release (hotfix lane)
- **REQ-HF-017** — BUG-53 and BUG-54 ship with regression tests in the same PR. *(Traces: S-5, AC-5)*
- **REQ-HF-018** — The prod-gate and protect-paths stay fail-closed, the approval hook fail-open, lookups within the pre-bash budget, and no guard logs or forwards a credential found in a command. *(Traces: Constraints, S-3 · Security Tier 2 · amends REQ-W1-024)*
- **REQ-HF-019** — Release 3.12.1: versions agree, CHANGELOG `[3.12.1]` with the behaviour changes, empty `[Unreleased]`, full gate and CI green. *(Traces: S-5, AC-5 · D-43)*
