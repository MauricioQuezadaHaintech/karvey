# Plan: prod-gate-scope

**Capability:** method | **Security Tier:** 2 | **Layers:** Backend
**Created:** 2026-09-29 | **Status:** 🔄 in_progress
**Lane:** hotfix (`type: hotfix`; fix + BUG-NN + regression test in the same PR) · **Skipped:** mockup, design_graphic (no UI), infra (no cloud)
**Release target:** 3.12.1 · **Flow:** trunk (`hotfix/3.12.1-prod-gate` → PR → `main`) · **Decisions:** D-43, D-45 (D-34, D-35, D-36, D-37 unchanged)

---

## Epic: Prod-gate scope, multi-repo and REST coverage

### Description
Hotfix of the 3.12.0 approval hook and prod-gate from real use (findings F-01..F-04): the prod approval is
bound to the change the human names; an approval in the owning repo covers the `[Deploy] <id>` PRs of the
repos the change declares, bound to each PR head; REST completions, production pipeline approvals and
commands run outside a repo pass the same gate; read-only listings of the state paths are not blocked.
Widened by D-45 (F-05..F-10): the session hook loads only the working repo's profile and never leaks a sensitive
handoff; the prod-gate decides on the PR's own repo and base, and lets non-Karvey targets pass with a warning;
the production OK is always typed (never a question tool, enforced by lint); a production-shaped phrase always
gets one hook line; the `approve … prod` refusal says what it found.

### Strategic value
The prod-gate is the method's strongest promise. Each finding is a path where an approval reached the wrong
change or a merge reached production unseen.

### Design decisions
| Topic | Decision |
|------|----------|
| Ship as a hotfix before the rest of the release chain | D-43 |
| Widened scope; REST to non-Karvey repos warns; prod OK only as typed text | D-45 |

## Features

- F1 — Prod approval bound to the named change (REQ-HF-001..004) · BUG-138
- F2 — Multi-repo release under the owning repo's approval (REQ-HF-005..009)
- F3 — REST and outside-a-repo coverage (REQ-HF-010..015)
- F4 — Read-only listings of protected paths (REQ-HF-016) · BUG-139 (BL-64)
- F5 — Regression and release 3.12.1 (REQ-HF-017..019)
- F6 — Agent profile from the working repo only (REQ-HF-020..023) · BUG-140
- F7 — Prod-gate target repo and base; non-Karvey targets warn (REQ-HF-024..026, REQ-HF-014 revised) · BUG-141
- F8 — Production OK typed, lint against a question tool (REQ-HF-027..028) · BUG-142
- F9 — One hook line for a production-shaped phrase (REQ-HF-029) · BUG-143
- F10 — `approve … prod` refusal names what it found (REQ-HF-030) · BUG-144

## Tasks

See `tasks.md` (24 tasks, E1.F1..F9, 690 min). Status per task is updated here as impl closes them.

## History

- 2026-09-29 — change opened in the hotfix lane (D-43).
- 2026-10-05 — requirements revision 1 (D-45): F-05..F-11, REQ-HF-020..030 added, REQ-HF-014/017/018 revised,
  BUG-53/54 renumbered to BUG-138/139 (held by another branch).
