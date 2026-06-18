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
    │   ├── spec.json               # Change metadata (incl. iteration_count, revision_history)
    │   ├── proposal.md             # Why, what and the impact
    │   ├── requirements.md         # EARS requirements of the change
    │   ├── spec-delta.md           # ADDED/MODIFIED/REMOVED over the living specs
    │   ├── design-spec.md          # Graphic design specification
    │   ├── architecture.md         # Technical design and architecture
    │   ├── tasks.md                # Implementation task plan
    │   ├── findings.md             # Triage inbox (bug/spec-gap/emergent) — see iteration-loop.md
    │   ├── PLAN.md                 # (only if management=markdown) Plan and checklist
    │   ├── mockup.html             # Navigable HTML mockup
    │   └── IMPLEMENTED             # Empty file that marks: deployed to production
    └── archive/                    # Completed and archived changes
        └── {YYYY-MM-DD}-{change-id}/
            └── (same files as the change)
```

> The per-repo incident tracker `docs/bugs_dev_testing.md` lives in **each repo** (not under `docs/spec/`); `incidents-index.md` aggregates them. See `incident-tracking.md`.

## spec.json — structure

```json
{
  "change_id": "add-feature-name",
  "capability": "capability-name",
  "created_at": "2026-05-31T00:00:00Z",
  "updated_at": "2026-05-31T00:00:00Z",
  "language": "es",
  "management": "clickup",
  "security_tier": 2,
  "phase": "requirements",
  "iteration_count": 0,
  "revision_history": [],
  "seed_backlog_id": "",
  "clickup": {
    "epic_id": "",
    "feature_ids": [],
    "backlog_list_id": "",
    "client_tag": ""
  },
  "approvals": {
    "requirements": { "generated": false, "approved": false },
    "mockup": { "generated": false, "approved": false },
    "design_graphic": { "generated": false, "approved": false },
    "architecture": { "generated": false, "approved": false },
    "infra": { "generated": false, "approved": false },
    "tasks": { "generated": false, "approved": false },
    "qa": { "approved": false },
    "deploy": { "approved": false }
  }
}
```

### Iteration fields

- `iteration_count` — how many times this change went through a feedback loop (incremented by `karvey-iterate` on a `spec-gap` re-open). A high count is a signal the spec was weak — useful for the retro.
- `revision_history` — append-only log of spec-revision sub-cycles: `[{ "date", "finding": "F-NN", "reason", "ripple": ["mockup","tasks"] }]`. Records *why* requirements were re-opened and which downstream phases were rippled.
- `seed_backlog_id` — if this change was promoted from a discovery backlog item (`BL-NN`), its id, for traceability (see `backlog.md`).

> The `qa` and `deploy` approvals were already used by the qa/deploy skills; they are made explicit in the schema here. `infra` likewise. The `approvals.*.approved` flags are what `karvey-iterate` resets (only for the affected phases) during a spec-revision ripple.

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

When completing and implementing a change:

1. Verify that `IMPLEMENTED` exists in the change's directory
2. For each operation in spec-delta.md:
   - **ADDED**: append to the end of `docs/spec/specs/{capability}/spec.md`
   - **MODIFIED**: replace the full block of the requirement by name
   - **REMOVED**: remove the block + add a deprecation comment
3. Git commit: "Merge spec deltas from {change-id}"
4. Move folder: `mv docs/spec/changes/{change-id} docs/spec/changes/archive/{date}-{change-id}`
5. Git commit: "Archive {change-id}"

## Capabilities convention

Capabilities represent functional domains of the product, not individual features.
Valid examples: `authentication`, `call-management`, `contact-search`, `notifications`, `tenant-config`
Avoid: `fix-bug-123`, `add-button`, `update-sp` (too granular)
