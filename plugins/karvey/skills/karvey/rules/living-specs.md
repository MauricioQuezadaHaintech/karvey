# Living Specs — Structure and Protocol

## Directory structure

```
docs/spec/
├── backlog.md                      # Discovery backlog (emergent → future change-ids) — see backlog.md
├── incidents-index.md              # Global index of all BUG-NN across repos + state — see incident-tracking.md
├── specs/                          # Living specs (cumulative source of truth)
│   └── {capability}/
│       └── spec.md                 # Master spec of the capability (grows over time)
└── changes/                        # Changes in progress
    ├── {change-id}/
    │   ├── spec.json               # Change metadata and state (state written by karvey-state.py)
    │   ├── prd.md                  # Why, what and the impact
    │   ├── requirements.md         # EARS requirements of the change
    │   ├── spec-delta.md           # ADDED/MODIFIED/REMOVED over the living specs
    │   ├── design-spec.md          # Graphic design specification
    │   ├── architecture.md         # Technical design and architecture
    │   ├── tasks.md                # Implementation task plan
    │   ├── findings.md             # Triage inbox (bug/spec-gap/emergent) — see iteration-loop.md
    │   ├── PLAN.md                 # (Markdown tracker only) Plan and checklist
    │   ├── mockup/                 # Navigable HTML mockup
    │   ├── qa/                     # QA review documents (REVISION_PR_*.md)
    │   └── IMPLEMENTED             # Empty file that marks: deployed to production
    └── archive/                    # Completed and archived changes
        └── {YYYY-MM-DD}-{change-id}/
            └── (same files as the change)
```

> The per-repo incident tracker `docs/bugs_dev_testing.md` lives in **each repo** (not under `docs/spec/`); `incidents-index.md` aggregates them. See `incident-tracking`[^r-incident-tracking].

## spec.json — structure

Machine-readable contract: `${CLAUDE_PLUGIN_ROOT}/schemas/spec.schema.json`. The state fields — `phase`,
`phase_history`, `approvals`, `skipped` — are written **only** by `karvey-state.py` (`init`, `generated`,
`approve`, `advance`, `skip`, `reopen`; see `state-machine`[^r-state-machine]); skills never edit them by hand. The rest is
descriptive metadata the skills fill in.

```json
{
  "schema_version": 1,
  "change_id": "add-feature-name",
  "capability": "capability-name",
  "created_at": "2026-05-31T00:00:00Z",
  "updated_at": "2026-05-31T00:00:00Z",
  "language": "es",
  "management": "{tool, or an override {tool, location, statuses, sprints}}",
  "security_tier": 2,
  "phase": "requirements",
  "phase_history": [
    { "phase": "init", "entered_at": "2026-05-31T00:00:00Z", "exited_at": "2026-05-31T00:10:00Z" },
    { "phase": "requirements", "entered_at": "2026-05-31T00:10:00Z" }
  ],
  "skipped": { "mockup": "no UI" },
  "lane": "standard",
  "type": "feature",
  "links": { "parent": "", "children": [] },
  "decisions": [],
  "inputs": {},
  "iteration_count": 0,
  "revision_history": [],
  "seed_backlog_id": "",
  "clickup": {
    "epic_id": "",
    "feature_ids": [],
    "task_ids": {},
    "backlog_list_id": "",
    "client_tag": ""
  },
  "approvals": {
    "requirements": { "generated": true, "approved": true, "by": "{name}", "role": "human", "date": "2026-05-31T12:00:00-04:00", "ref": "D-12" }
  }
}
```

### Tracker fields (see `management-adapters`[^r-management-adapters])

- `management` — the tracker **tool** of this change, or an override `{tool, location, statuses, sprints}` that
  wins over `project.json:management` (resolution order in `management-adapters`[^r-management-adapters]). `none` is a legacy
  alias of `markdown`.
- `clickup` — the change's **tracker ids** (`epic_id`, `feature_ids`, `task_ids`, `backlog_list_id`,
  `client_tag`). The key keeps its historical name; it holds the ids of whichever tracker the team uses.

### Multi-agent / multi-repo fields (see `multi-agent`[^r-multi-agent])

- `type` — `feature` (default) · `ops` (no application code: IAM, DNS, secrets, console config — short pipeline) · `hotfix` (fast lane: fix + `BUG-NN` + regression test in the same PR).
- `links.parent` / `links.children` — `"{change-id}@{repo}"` references between a parent change (operations repo) and its per-repo children.
- `decisions` — business decisions this change depends on, `"D-NN@{repo}"`. Requirements cite them.
- `inputs` — pinned work from other agents: `design`, `design_system`, `copy`, `legal`, each `"{repo} {path} @{commit}"`. Only the applicable keys are present.
- `approvals.<phase>` — `generated`, `approved`, and on approval `by`, `role` (`human` | `ceo-delegate`),
  `date` (ISO 8601 with zone) and `ref` (a `D-NN` or a URL).
- `approvals.prod` — `{ by, role: human, date, ref }`; never delegated to an agent. At deploy the human's OK is
  a `D-NN`, in the PR and in the release ledger; it is copied here only at archive (`approve … prod
  --write-spec`, D-03).
- `skipped` — `{phase: reason}` for `mockup`, `design_graphic`, `infra` only; a skipped phase satisfies the
  next phase's precondition.
- `phase_history` — one entry per phase entered (`phase`, `entered_at`, `exited_at`, optional `by`, `ref`,
  `evidence`).
- `lane` — recorded only (Wave 1); lanes are not enforced yet.
- `schema_version` — `1`; a file with a higher version stops the tool (upgrade Karvey).

### Iteration fields

- `iteration_count` — how many times this change went through a feedback loop (incremented by `karvey-iterate` on a `spec-gap` re-open). A high count is a signal the spec was weak — useful for the retro.
- `revision_history` — append-only log of spec-revision sub-cycles: `[{ "date", "finding": "F-NN", "reason", "ripple": ["mockup","tasks"] }]`. Records *why* requirements were re-opened and which downstream phases were rippled. Hotfix entries also carry `"bug": "BUG-NN"` and `"release": "x.y.z"`; an input re-pin carries `"input": "design"` and the old/new commit.
- `seed_backlog_id` — if this change was promoted from a discovery backlog item (`BL-NN`), its id, for traceability (see `backlog`[^r-backlog]).

> `karvey-iterate` re-opens a phase with `karvey-state.py reopen`, which moves the approvals of the affected phases to `revision_history`.

## spec-delta.md — format

```markdown
# Spec Delta: {change-id}

## ADDED Requirements

### Requirement: {Name}
WHEN {event},
the system SHALL {behavior}.

#### Scenario: {case}
GIVEN ...
WHEN ...
THEN ...

## MODIFIED Requirements

### Requirement: {Existing name}
<!-- COMPLETELY replaces the requirement in docs/spec/specs/{capability}/spec.md -->
WHEN {new behavior},
the system SHALL {new result}.

## REMOVED Requirements

### Requirement: {Name to remove}
<!-- Reason: {why it is removed} -->
```

## Archiving protocol

Run by `karvey-archive` on `chore/archive-{change-id}` (never on the integration or production branch):
the spec-delta is merged into `docs/spec/specs/{capability}/spec.md` by
`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/karvey-spec-merge.py" {change-id} --dry-run` (review the diff), then
without `--dry-run`; the change folder moves to `docs/spec/changes/archive/{YYYY-MM-DD}-{change-id}/`, and
the work lands through a docs-only PR.

## Capabilities convention

Capabilities represent functional domains of the product, not individual features.
Valid examples: `authentication`, `call-management`, `contact-search`, `notifications`, `tenant-config`
Avoid: `fix-bug-123`, `add-button`, `update-sp` (too granular)

[^r-backlog]: backlog.md — context only, not opened.
[^r-incident-tracking]: incident-tracking.md — context only, not opened.
[^r-management-adapters]: management-adapters.md — context only, not opened.
[^r-multi-agent]: multi-agent.md — context only, not opened.
[^r-state-machine]: state-machine.md — context only, not opened.
