# PRD: approval-by-name (hotfix 3.13.1)

## Executive summary

Real use of 3.13.0 found two defects in how the human's production OK is taken. The approval hook resolves the
change only inside the session's current working tree: the owner typed «aprobado para producción change-a» in a
session whose directory was another repo holding `change-b`; the hook refused, saying that `change-a` is held by
no worktree or branch, and suggested typing «aprobado para producción change-b», a change the owner had not
named. Second, the phrase the hook, the state tool and the deploy skill show («aprobado para producción <id>
PR #<n> v<version>») reads as a mandatory format, while only the approval word, the production word and the
change id are required (D-10). The owner decided (D-47) to ship both fixes as hotfix 3.13.1.

## Goal (the change's north star)

The human's production OK reaches the change the human named, wherever the session runs, and the phrase shown
asks for nothing more than the approval word, the production word and the change id.

## Problem and context

1. **Approval by name (bug).** `approval.resolve_prod_scope` looks for the named id in the working tree, in the
   other worktrees of the same clone and in its branches. A change that lives in another local clone (the
   usual case when one session releases several repos) is "found nowhere", and the refusal suggests the active
   change of the session's tree: the opposite of what the human asked. The prod-gate already knows how to find
   the clone that owns a change (`clones.search_dirs` / `find_owner`, 3.12.1); the approval hook does not use it.
2. **Phrase format (bug).** `marker_report` in the state tool and step 2.9 of `karvey-deploy` show
   «aprobado para producción {id} PR #{n} v{version}». The approval is bound to the head commit the agent passes
   with `approve … --sha` (D-35); the PR number and the version are never read. A human who reads the phrase as a
   template retypes it when a PR is recreated with the same head, or thinks an OK without them does not count.

## Users

- The **owner / release approver** who types the production OK in whatever session they are in.
- The **orchestrating agent** that relays the phrase to type and records `approve … prod --sha`.

## Objectives

- **O-1** A production approval that names one change is recorded in the one local clone that owns it, and the
  hook line says which clone.
- **O-2** No suggestion ever names a change other than the one the human named.
- **O-3** The phrase shown everywhere is «aprobado para producción <change-id>»; PR and version are informational.

## Scope

- **S-1** Approval hook: resolution of a named change across the local clones (same discovery as the prod-gate),
  marker and audit in the owning clone, ambiguity refused, suggestion fixed; outside a Karvey project, a named
  change owned by exactly one clone is recorded there.
- **S-2** Phrase text in the state tool refusal, the hook, `karvey-deploy`, `rules/enforcement.md`,
  `hooks/README.md`; lint check that keeps PR/version out of the phrase.

Out of scope: the prod-gate itself (unchanged), the ledger format (unchanged), branch-only changes of this clone
(their message is unchanged, REQ-HF-002).

## Acceptance criteria

- **AC-1** Session in repo `app-web` (active change `web-search`); sibling clone `app-api` holds `api-rate-limit`.
  «aprobado para producción api-rate-limit» records `(prod, api-rate-limit)` in `app-api`'s approvals and audit,
  none in `app-web`, and the line names `app-api`'s path.
- **AC-2** Two clones hold `api-rate-limit`: nothing recorded, both paths listed, the phrase names
  `api-rate-limit`.
- **AC-3** A named id held nowhere: nothing recorded; the phrase is «aprobado para producción <change-id>», never
  `web-search`.
- **AC-4** No change named: unchanged — the single active change of the working tree, said out loud.
- **AC-5** The state tool refusal, the hook and `karvey-deploy` show «aprobado para producción <change-id>»; PR and
  version are described as optional; L-82 fails a skill or rule that puts `PR #` or a version inside the phrase.

## Risks

- A look-alike clone (fork, copy) holding the same id: covered by AC-2 (refuse, list) — a marker is never
  written in a clone the human did not unambiguously name.
- Cost on every prompt: the clone search runs only for a production approval that names an id not found in the
  working tree (rare), bounded as the prod-gate's search is.
