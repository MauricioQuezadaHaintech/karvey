# Plan: approval-by-name

**Capability:** method | **Security Tier:** 2 | **Layers:** Backend
**Created:** 2026-10-07 | **Status:** 🔄 in_progress
**Lane:** hotfix (`type: hotfix`; fix + BUG-NN + regression test in the same PR) · **Skipped:** mockup, design_graphic (no UI), infra (no cloud)
**Release target:** 3.13.1 · **Flow:** trunk (`hotfix/3.13.1-approval-by-name` → PR → `main`) · **Decisions:** D-47 (D-10, D-34, D-35 unchanged)

---

## Epic: Approval by named change

### Description
The approval hook records a production approval in the local clone that owns the change the human named, found
the way the prod-gate finds clones; it never suggests another change; the phrase shown is the minimal one.

| Task | Status |
|---|---|
| E1.F1.T1 red tests (by name) | ✅ |
| E1.F1.T2 approval hook across clones | ✅ |
| E1.F2.T1 red tests (phrase, L-82) | ✅ |
| E1.F2.T2 phrase text + L-82 | ✅ |
| E1.F3.T0 BUG records + regression index | ✅ |
| E1.F3.T1 release 3.13.1 | ✅ |
| E1.F3.T2 test plan / evidence | ✅ |
