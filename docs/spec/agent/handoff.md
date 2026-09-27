# Handoff — agente-karvey

## 0. Verified state — 2026-09-27 (UTC)
Captured with commands. If this does not match on startup, this handoff has aged: believe the commands.

| Repo / worktree | Branch | Uncommitted | Last commit | Published? |
|---|---|---|---|---|
| ~/Dev/karvey | docs/archive-wave1-hardening | 0 | 3caa33b | PR #26 open (archive of wave1), needs the owner's prod OK |
| karvey-wt-project-upgrade | feature/project-upgrade | 0 | 6379986 | PR #25 = 3.13.0, CI 7/7 green, QA approved, **waits for the owner's prod OK** |
| karvey-wt-wave2 | feature/wave2-structural | 0 | e2fa853 | QA approved (D-21); release after 3.13.0 |
| karvey-wt-wave3 | feature/wave3-optimization | 0 | ac2717a | QA approved (D-21); release after wave2 |
| karvey-wt-living-docs | feature/living-docs | 0 | 3fa85ad | spec done (what+how approved); impl after 3.13.0 is on main (needs the upgrade engine) |
| karvey-wt-mockup | feature/mockup-conformance | 0 | dab6d20 | spec done (what+how approved); impl after living-docs (D-40) |

`main` = **3.12.0** (merge e2acfab, CI 7/7), installed 3.12.0 (`claude plugin list`). `feature/wave1-hardening` deleted (absorbed).

## 1. Blocking right now
- **The owner's production OK for 3.13.0** (PR #25), typed in a session that loads 3.12.0 (any new session in ~/Dev/karvey): e.g. «ok, merge a prod project-upgrade 3.13.0». Then: `karvey-state.py approve project-upgrade prod --by … --role human --ref D-41 --sha <PR head>` → `check-prod` → `gh pr merge 25 --merge` → CI on main → `claude plugin update` → verify. D-NN is written at archive (D-03), never before the merge (it would change the approved SHA).
- PR #26 (wave1 archive) also needs a prod OK (touches two tests).

## 2. Who I am
Maintainer agent of the Karvey plugin. `manifest.md` · `board.md` · `checklist.md`. Owner approves every gate; D-21 is his standing instruction: finish every wave without stopping unless blocked; non-prod gates recorded with ref D-21; prod never delegated (D-10, D-34/35/36).

## 3. Rules I work under
`manifest.md` + the owner's global CLAUDE.md + `plugins/karvey/skills/karvey/rules/`. The owner's plan-gate hook needs a plan approval younger than 12 h: renew with `touch` only after his explicit approval in THIS session.

## 4. Board — open, in one place
`board.md`. Release chain: 3.13.0 → merge main into wave2 → wave2 release (one manifest OK, D-37) → merge into wave3 → wave3 release → living-docs impl/test/QA/release → mockup-conformance impl/test/QA/release. Version numbers: proposed by release order (3.13 project-upgrade, 3.14 wave2, 3.15 wave3, 3.16 living-docs, 3.17 mockup-conformance; 4.0 reserved for defaults turning blocking, D-24) — **confirm with the owner at the wave2 release**.

## 5. Closing checklist
`checklist.md`.

## 6. Standing decisions that affect me
`docs/spec/decisions.md` D-01..D-40 (D-21 standing instruction; D-22..D-32 Wave 2/3 owner decisions; D-33 subagent-prompt guard; D-34..D-36 prod approval = hook audit record + head SHA + 24 h + reopen invalidates; D-37 one bound OK per release manifest; D-38 living-docs; D-39 prod OK of 3.12.0; D-40 mockup-conformance).

## 7. In flight, and what I am waiting for
- Owner: prod OK 3.13.0 (PR #25) and PR #26; `main` branch protection (E1.F16.T3: command in /tmp/claude-1002/w1rel.VVJT/protection.cmd.txt); apply the global-config diff (E1.F16.T7: /tmp/claude-1002/w1rel.VVJT/global-config.diff) — both scratch files may be gone after a reboot: regenerate from wave1 architecture §7.3.
- A peer agent waits for the version that ships mockup-conformance to apply it in its next change with a mockup.
- For the owner's final review list: wave2 open points 1–13 and architect decisions A-01..; wave3 open points 1–14; living-docs open points 1–10 + A-01..A-22; mockup-conformance open points + thresholds; F-85 resolution; `team-adapters` cannot be archived (its old gates never approved — owner decision); graphify full semantic update pending (the fast pass destroyed the curated graph, reverted); browser-only QA checks of wave3 (sponsor page 360/1440, method page 9 languages) — delegate to a browser agent or leave to the owner.

## 8. What a new session CANNOT derive from the repo
- **Public repo, neutral method** (owner, 2026-09-25): no secrets, no organisation/product/client names, no people as actors in method text (roles only); names in authorship records are fine. Existing leaks are NOT to be corrected until the end (owner: «no corrijas nada de eso hasta el final»); then clean + report what remains in git history (rewrite only with his decision).
- Subagents' reviewers sometimes report to the orchestrator: relay to the owning subagent.
- Throw-away `claude -p` sessions write transcripts under ~/.claude/projects/-tmp-claude-1002-*: delete them after manual-script runs.
- Estimates run high; actuals recorded in each PLAN.md.

## 9. Scheduled tasks — with their full prompt
None.

## 10. Last updated
2026-09-27 · agente-karvey · 3.12.0 released; project-upgrade/wave2/wave3 QA approved; living-docs and mockup-conformance specs approved; waiting on the owner's prod OK for 3.13.0.
