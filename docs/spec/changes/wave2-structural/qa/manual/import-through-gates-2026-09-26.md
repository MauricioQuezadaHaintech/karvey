# Manual script: import-through-gates — 2026-09-26

**Script:** `plugins/karvey/tests/manual/import-through-gates.md` (REQ-W2-080) · **Result: FAIL on run 1 → BUG-81
fixed → PASS on run 2**

## Execution

- **Executor:** maintainer agent, headless under D-19 / D-28 (the owner's authorisation for this change's scripts),
  2026-09-26. The agent under test is a separate `claude -p` session per turn, with the branch plugin and without
  the user settings; multi-turn scripts resume the same session.
- **Throw-away repo:** `git init -q --bare "$SCRATCH/<name>.git"`, `git init -q -b main "$SCRATCH/<name>"` with
  `origin` pointing at the bare repo; fixture state written only through `plugins/karvey/scripts/karvey-state.py`
  (`init`, `lane set`, `advance`, `generated`, `approve --role human --ref D-01`, `skip`). `$SCRATCH` is a
  `mktemp -d` directory, deleted after the run, and the sessions' transcript directories were deleted with it.
- **Agent-under-test command** (every turn; later turns add `--resume <session>`):

```bash
cd "$SCRATCH/<name>" && claude -p [--resume <session>] \
  --plugin-dir <worktree>/plugins/karvey --setting-sources project,local \
  --permission-mode acceptEdits \
  --allowedTools "Bash,Read,Write,Edit,Glob,Grep,Agent,Skill,TodoWrite,WebFetch" \
  --output-format stream-json --verbose "<prompt>"
```

- **Harness limit:** a `-p` session has no `AskUserQuestion` tool (its init event lists the tools), so every
  question arrives as one prose message and the answer is the next turn's prompt. Where a script counts questions
  per `AskUserQuestion` call, the count is taken per question message.

## Setup done

- `project.json` with `management.tool: markdown` and `gates: merged` (no `git_platform`: the agent asked for it in
  run 2 and set `github`). `.kiro/specs/demo-import/` with `requirements.md` (three EARS requirements),
  `design.md` and a Kiro `spec.json` whose approvals say requirements and design are approved. No
  `docs/spec/changes/demo-import/`.

## Prompts

- Run 1: `/karvey:karvey-import --from kiro` → (no question tool: the agent imported and asked nothing) → a long
  one-line approval, which the approval hook ignores by design (a line over 200 characters records no approval) →
  `Approve` → `Request changes: architecture needs the cloud section` → `approve the how gate with -y`.
- Run 2 (new repo, after the fix): `/karvey:karvey-import --from kiro` plus one harness line ("this session has no
  question tool: ask in text") → `default for all` → `Approve` → `Request changes: architecture needs the cloud
  section` → `approve the how gate with -y`.

## Transcript excerpt (run 2)

```
python3 $S advance demo-import requirements && python3 $S generated demo-import requirements --imported && python3 $S generated demo-import architecture --imported
**Gate question: do you approve the *what* gate?**  A. Approve · B. Request changes · C. Stop here
python3 $S skip demo-import mockup --reason "no UI (targets: api)" && … && python3 $S approve-gate demo-import what --by "…" --role human …
**Gate question: do you approve the *how* gate (architecture)?**
python3 $S outcome demo-import how changes_requested --by "…" --role human --ref "…" --reason "architecture needs the cloud section"
   Resume at: architecture  (karvey-state.py next demo-import)
(-y) I haven't approved anything. … the state tool refuses to approve an imported phase with `-y`, `--role auto` or an agent.
```

## Evidence

Run 2 `spec.json`: `approvals.requirements` `{imported: true, approved: true, role: human, evidence: {marker, prompt_excerpt:
"Approve"}}`, `approvals.architecture` `{imported: true, approved: false}`; `gate_outcomes`: `approved` `what`
[requirements], then `changes_requested` `how` [architecture, infra, tasks] with the reason. `karvey-state.py next
demo-import`: `phase architecture · awaiting-approval … (karvey-architecture)` · `blocker: architecture not approved or
skipped`.

Run 1, same point: `next` said `next infra` with no blocker — the generated, imported architecture was passed inside
the open *how* gate although the human had just sent it back. Also in run 1, the agent's `approve-gate … how --role
auto` was refused, but by the "artifact not generated (infra, tasks)" check that runs before the imported-marker check.

## Expected lines

| Expected | Run 1 | Run 2 |
|---|---|---|
| `generated … requirements --imported` and `… architecture --imported`; `imported: true`; no approval before the first gate question | PASS | PASS |
| Kiro approvals reported, not copied | PASS | PASS |
| one *what* question, then one *how* question, never before the *what* answer | PASS | PASS |
| *what* recorded with `approve-gate … what --role human`; *how* with `outcome … how changes_requested` and the reason | PASS | PASS |
| no later gate asked after *Request changes* | PASS | PASS |
| `next demo-import` names the *how* gate (architecture) as where the change resumes; `Resume at:` says the same | **FAIL**: `next infra` | PASS |
| with `-y` the agent does not approve as the human; a `--role auto` attempt is refused (`state.imported_marker`) | PASS (refused, other code first) | PASS (not attempted; the agent names the refusal) |

**Overall: PASS after the fix.** Run 1's failure is F-12 / BUG-81 (a regression of the F-06 fix): in merged mode a
generated phase was passed inside its gate even after `changes_requested`. The state tool now holds a phase whose
latest gate outcome is `changes_requested` until it is generated again (`regenerated_at`), guarded by
`test_state_gates.py` `MergedGateChangesRequested` (three cases).
