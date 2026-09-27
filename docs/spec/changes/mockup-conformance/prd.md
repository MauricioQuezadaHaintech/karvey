# PRD: mockup-conformance

## 1. Executive summary
The method asks the owner to approve a navigable mockup before anything is built, and then lets the build drift
from it. Implementation works from the requirements, the architecture and the tasks; the approved mockup is not a
mandatory input, so the UI is rebuilt from memory and from text. Mockup and requirements are compared only before
implementing; after implementing, the only check is QA's visual audit, which compares the build with the design
specification — not with the mockup — and is settled by a glance. Decisions taken while iterating the mockup do not
always return to the requirements. The owner found this gap in three applications built with the method and paid it
in rework. This change (D-40) makes the mockup a contract: stable element ids tied to requirements, decisions written
back before approval, the approved mockup as a mandatory input of implementation, a blocking conformance gate with
side-by-side captures and owner-approved deviations, and a traceability matrix from requirement to evidence before
release. Target release **4.3.0**, a backward-compatible minor on top of 4.2.0; implementation starts after
`living-docs`' implementation.

## 2. 🎯 Goal (the change's north star)
> **The UI a change ships is the UI the owner approved in its mockup: every approved mockup element is present in the
> build under the same element id, every visible difference between mockup and build at the same viewport and state
> has been either fixed or recorded as a deviation the owner approved through the hook, and every UI requirement is
> traced to its mockup elements, tests and evidence before the release gate opens.**

This goal is the north star that all Karvey phases pursue: each phase re-reads it on start to advance toward the
result without stopping until it is achieved, respecting the plan and security gates.

## 3. Problem and context
- **Who has it:** the owner of a UI change (approves a mockup and receives something else), the agents that
  implement it (they have no structured link from a requirement to the screen element that realises it), QA and the
  judges (they compare the build with a design text, not with what was approved), and whoever maintains the UI later
  (nothing says which element came from which requirement).
- **Current situation:**
  - **Mockup** (D-40 part 1): the mockup skill validates the mockup against the requirements before presenting it
    (spec-gaps are fixed or routed), but its elements carry no stable identity, nothing links an element to the
    requirement it covers, and a decision taken in an iteration ("the filter goes above the table", "the empty state
    offers an import") can be approved in the mockup without ever reaching `requirements.md`.
  - **Implementation** (D-40 part 2): the implementation skill reads spec, tasks, architecture, requirements,
    deviations, pinned inputs and standards; the approved mockup is not among its inputs. The UI is rebuilt from the
    requirements' text and from memory of the mockup.
  - **After implementing** (D-40 part 3): the test phase reads the mockup only to derive end-to-end flows; QA's
    Dimension 8 audits the build against the design specification, in the real runtime, with no element-by-element
    check, no capture of the mockup at the same viewport and state, no measured difference and no owner decision per
    difference. The existing `deviations.md` records departures from engineering standards approved at design time,
    not visual departures from the mockup.
  - **Traceability** (D-40 part 4): the script-generated matrix maps requirements to tasks, commits and tests; it
    knows nothing of mockup elements or visual evidence.
  - **Existing projects:** a new gate no project has configured helps nobody; the project-upgrade plan (D-20) is the
    path by which method features reach a project.
- **Impact:** rework after release; approvals that do not bind what ships; spec drift hidden inside the mockup; a
  visual audit whose pass means only that somebody looked.

## 4. Objectives and success metrics
| # | Objective | Metric |
|---|---|---|
| O-1 | Every mockup element is identifiable and traced | 100% of the elements the element rules require in an approved mockup carry a unique, stable element id and at least one existing requirement id (or a recorded spec-gap); 100% of the change's UI requirements are covered by at least one element |
| O-2 | No decision stays only in the mockup | 0 mockups approved while an iteration decision is unrecorded or cites a requirement revision that does not exist |
| O-3 | The approved mockup is what gets built | the implementation phase cannot start on a UI change without the approved mockup (verified by its hash); 100% of the approved element ids are assigned to a task and present in the built UI |
| O-4 | Differences are measured, not glanced at | every capture pair of the conformance plan is taken at the same viewport and state, with the difference marked and, where the target allows, a pixel difference against a threshold |
| O-5 | Every difference is the owner's decision | 0 releases of a UI change while a difference has no deviation entry or an entry lacks an approval written by the hook from the owner's own message; 0 approvals written by the agent |
| O-6 | Traced end to end before release | the traceability matrix of every UI change lists requirement → element → test → evidence with no empty cell (or an approved deviation) when the release gate opens |
| O-7 | Honest across targets | web, mobile, desktop and CLI define what an element id and a capture are; every other target is declared out of scope by name, and the gate says `not applicable` for it instead of passing silently |
| O-8 | Existing projects get it | the upgrade catalogue has one step per part that needs one; each is dry-run first and applied only when picked |
| O-9 | Cheap to carry | the new rule is loaded only by the phases that act on it; no phase's closure grows by more than 10% |

## 5. User stories / main use cases
- As the **owner of a UI change**, I want every element of the mockup I approve to be named and tied to a requirement,
  so that approving the mockup approves something the build can be checked against.
- As the **owner**, I want what I decide while iterating the mockup to be written into the requirements before I
  approve it, so that the requirements never say less than the mockup.
- As an **implementing agent**, I want the approved mockup, its element map and the tasks that name each element, so
  that I build the approved structure and styles instead of re-creating them from text.
- As the **owner at release**, I want to see the mockup and the build side by side at the same size and state, with
  the differences marked, and to decide each difference myself, so that nothing ships different from what I
  approved without my word.
- As a **reviewer or judge**, I want a conformance report and a traceability matrix with evidence per element, so
  that I check facts rather than impressions.
- As a **team with a mobile or desktop app or a command-line tool**, I want the method to say what an element id and a capture
  are for my target, or to say plainly that my target is not covered.
- As a **team adopting the release on an existing project**, I want upgrade steps that add the settings and bring a
  change in flight to the new rules without rewriting what is already approved.

## 6. Scope (in scope)
| # | Area | Part of D-40 |
|---|---|---|
| S-1 | Element ids in the mockup: which elements need one, id format and uniqueness, the requirement each covers, stability across iterations, preserved by design-graphic; an element check tool | 1 |
| S-2 | Decisions written back: each mockup iteration's decisions recorded and resolved into a requirement revision (revision history) or a reasoned no-impact; mockup approval refused otherwise; the approved mockup frozen by hash | 1 |
| S-3 | Implementation from the mockup: approved mockup as a mandatory input verified by hash; tasks name the element ids they build; structure, copy and design-system tokens taken from the mockup; the same element ids in the built UI | 2 |
| S-4 | Conformance gate: presence check of every element; a conformance plan (screen and state recipes, viewports); side-by-side captures at the same viewport and state with the difference marked, pixel difference with a threshold where the target allows; captures through the project's browse settings; evidence stored in the change, bound to the commit | 3 |
| S-5 | Visual deviations: every difference recorded in `deviations.md`; approval only from the owner's own message through the hook (D-01); QA approval, release gate and deploy refused otherwise | 3 |
| S-6 | Traceability matrix requirement → element → test → evidence, complete before release | 4 |
| S-7 | Targets: web, mobile, desktop and CLI defined; API, embedded and every other target scoped out by name | all |
| S-8 | Integration: lanes (only lanes that run the mockup) and merged gates of Wave 2; design system, design delta, design judge, load lists and size budget of Wave 3; frontend-module sheets of `living-docs`; check-mode registry; upgrade steps; dogfooding on a fixture project | all |

## 7. Out of scope
- **Changes without a mockup**: lanes that skip the mockup, and UI touched by a `patch` or `hotfix` change, are not
  checked against a mockup (there is none for that change); they keep today's visual audit.
- **Retroactive conformance** of UI shipped before the release, or of mockups approved before it.
- **Targets other than web, mobile, desktop and CLI** (API/backend, embedded, game, data, library): no element id, no capture;
  the gate reports `not applicable: target <t>`.
- **Pixel-exact equality**: the gate measures and marks differences against a threshold and asks the owner; it never
  requires identical pixels, and it never "fixes" a difference by itself.
- **Capturing a production environment** or production data.
- **Choosing or shipping a specific browser automation or image-diff product** as a requirement (architecture picks
  adapters; any vendor appears only as one example among several).
- **Editing the owner's personal global instructions** or anything under the user's home (D-01, D-11).

## 8. Stakeholders
- **Requests and approves:** the method's owner (approves the gates of this change and production — `role: human`);
  D-40 records the request and the routing answer verbatim, D-21 the standing instruction to proceed with
  recommended defaults, listed as open points.
- **Impacted:** every project using the method with a UI (owners, implementing agents, reviewers and judges, the
  agent that runs the browser when browsing is delegated).
- **Sources:** D-40; the mockup, design-graphic, tasks, impl, test, qa and deploy skills; `deviations.md` and the
  engineering-standards rule; the approval hook and confirm-phrase pattern (D-01, REQ-W1-017, REQ-LD-063); Wave 2
  lanes, gates and traceability (REQ-W2-011, 034, 060, 062); Wave 3 design system, load lists and `browse.via`
  (REQ-W3-004, 035–039, 054, 061); `living-docs` frontend-module sheets (REQ-LD-022); project-upgrade (D-20,
  REQ-UP-008).

## 9. Constraints
- **Security Tier: 3** — a deviation approval releases a blocking gate, so it is a trust boundary: approvals come only
  from the owner's own message, written by the hook, verified by the state tool against a store the agent cannot
  write (D-01); captures of a running build enter tracked files of a repository that may be public, so they are taken
  only from a non-production target with fixture data, and the gate refuses a target declared as production;
  browsing delegated to another agent returns captures that are verified (hash, viewport, state, commit), never
  taken on trust; nothing an agent sends to a browsing agent carries a secret.
- **Backward compatible** (minor release 4.3.0): checks start blocking only for UI changes whose mockup is approved
  under 4.3.0; a change whose mockup was approved earlier gets the checks as warn; `validate` accepts every 4.2.0
  shape; a project with no UI change behaves as in 4.2.0.
- **Public, organisation-neutral text:** no rule, skill, template or example names a company, product, client,
  person, internal URL or personal path; tools and vendors appear only as one example among several; examples are
  fictional.
- **Sequencing:** requirements through tasks now; implementation after `living-docs`' implementation (both edit the
  same skills, the state tool, the hooks and the linter).
- **Dogfooding:** this repository has no UI, so the change is built in the `standard` lane and proves itself on a
  fixture UI project inside the method's tests; trunk flow, Markdown tracker; every commit carries
  `Karvey-Change: mockup-conformance`.
- **Decisions this change depends on:** D-40; D-01 (approval only from the human's message), D-20 (project-upgrade),
  D-21, D-22 (merged gates), D-24 (strictness per release), D-30 (cost measured, never capped), D-38 (living-docs).

## 10. Acceptance criteria
- **AC-1** A fixture mockup whose required elements all carry unique `data-mk` ids and requirement ids passes the
  element check; a duplicate id, a required element without an id, an unknown requirement id, and a UI requirement no
  element covers are each reported by name, and the mockup approval is refused while any is open.
- **AC-2** A mockup iteration that records a decision without a requirement revision or a reasoned no-impact blocks
  the mockup approval, naming the decision; with the revision recorded in `revision_history`, it passes.
- **AC-3** Editing the mockup after its approval makes `validate` report it and `advance … impl` refuse until the
  mockup is re-approved.
- **AC-4** On a fixture UI change, implementation cannot start without the approved mockup; every element id is
  assigned to a task; the built fixture carries the same ids.
- **AC-5** The conformance run over the fixture produces, per plan entry, a mockup capture, a build capture at the same
  viewport and state, a marked side-by-side image and, for web, a pixel-difference ratio against the threshold; a
  removed element and a moved element are reported with their ids.
- **AC-6** A difference without an approved deviation keeps QA approval, the release gate and deploy refused; a
  deviation marked approved by the agent (no hook marker) is reported as tampered; the owner's confirm phrase makes
  the hook write the marker and the gate passes.
- **AC-7** A conformance run whose commit is older than the last UI commit of the change is reported stale and does not
  count.
- **AC-8** The traceability matrix of the fixture lists, per UI requirement, its element ids, tests and conformance
  evidence; an empty cell blocks the release gate.
- **AC-9** A CLI fixture passes with named output blocks and a transcript comparison; an API target reports
  `not applicable: target api`.
- **AC-10** The upgrade plan lists the steps of this change with their seven fields; dry-run writes nothing.
- **AC-11** The size tool shows each phase's closure growth ≤ 10%; the plugin linter and the neutrality lint are
  green; a project that passes under 4.2.0 passes under 4.3.0 with the defaults.
