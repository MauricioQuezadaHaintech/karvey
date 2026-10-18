# Handoff — agente-karvey

## 0. Verified state — 2026-10-16 (UTC)
Captured with commands (`git worktree list`, `git status`, `gh pr list`, `claude plugin list`). If this
does not match on startup, this handoff has aged: believe the commands.

`main` = **3.13.0** (merge f1cf2f8, CI green). Installed 3.13.0 in the accounts `mauricio-haintech` and
`mauricio-m15` (the `haintech-lab` account has no Karvey). Released this cycle: 3.12.0 (wave1), 3.12.1
(prod-gate-scope hotfix), 3.13.0 (project-upgrade).

| Worktree | Branch | Uncommitted | Last commit | Published? |
|---|---|---|---|---|
| ~/Dev/karvey | fix/bug53-az-pr-org | 0 | 99a30ec BUG-52 az --org | **not mine** — PR #27 by another session; do not touch |
| karvey-wt-hf2 | hotfix/3.13.1-approval-by-name | **16 + .graph-pending** | 876e770 release 3.13.1 | PR #30, CI green on 876e770, but **WIP uncommitted** (the "no crafted plan-approval phrases" rule + lint) |
| karvey-wt-wave2 | feature/wave2-structural | 4 | d1c6adb living-spec merge | **50 commits ahead, NOT pushed**; release prep 3.14.0 was in progress |
| karvey-wt-mockup | feature/mockup-conformance | **157 staged (merge in progress)** | d53dff6 | merge of main/wave3 resolved but **not concluded** (`git commit` pending) |
| karvey-wt-wave3 | feature/wave3-optimization | 0 | ac2717a QA approved | QA approved; release after wave2 |
| karvey-wt-living-docs | feature/living-docs | 0 | 3fa85ad how approved | spec only; impl after mockup-conformance (D-44) |
| karvey-wt-project-upgrade | feature/project-upgrade | 0 | e56c133 | merged (3.13.0) — remove worktree + branch (hygiene) |
| karvey-wt-archive-hf | docs/archive-prod-gate-scope | 0 | 545d86f | PR #29, needs owner prod OK |
| karvey-wt-archive-w1 | docs/archive-wave1-hardening | 0 | 7c28526 | PR #26, needs owner prod OK |

## 1. Blocking right now
Nothing external. The three background subagents (3.13.1 release, wave2 release prep, mockup impl)
died with the previous session; their worktrees hold partial work (table above). Next session:
1. hf2: review the 16 uncommitted files (the crafted-phrase rule + lint), finish tests, commit, push → CI
   green on the new PR #30 head → owner phrase «aprobado para producción approval-by-name».
2. wave2: commit the 4 files, push the 50 commits, finish release prep 3.14.0 (PR, CI) → owner phrase
   «aprobado para producción wave2-structural».
3. mockup: conclude the merge (`git commit`), then impl (D-44: before living-docs).

## 2. Who I am
Maintainer agent of the Karvey plugin (`manifest.md`, `board.md`, `checklist.md` in this folder). Owner
approves the plan; inside an approved plan nothing is asked again (D-47). Production OK is the owner's
typed phrase «aprobado para producción <change-id>», hook-recorded, SHA-bound 24 h (D-10, D-34..D-36).

## 3. Rules I work under
`manifest.md` + the owner's global CLAUDE.md (now D-47-aligned: investigation free; consequential actions
need an approved plan; approval lasts until the plan ends or «detente») + `plugins/karvey/skills/karvey/rules/`.

## 4. Board — open, in one place
`board.md`. Release chain: 3.13.1 → 3.14.0 (wave2) → 3.15.0 (wave3) → mockup-conformance → living-docs.
Then: final neutrality cleanup of the public repo + git-history exposure report (owner decides rewrite).

## 5. Closing checklist
`checklist.md`, plus: at every release update the plugin in **every account of the machine**
(`sudo -n -u mauricio-m15 -H bash -lc 'claude plugin update karvey@karvey-methods'`) and tell open
sessions to restart (running sessions keep the plugin they loaded).

## 6. Standing decisions that affect me
`docs/spec/decisions.md` up to D-47 (+ D-48, D-49 written at archive of 3.12.1 / 3.13.0). Most
load-bearing: D-47 (approval model), D-45 (prod OK only as typed text, never a question tool),
D-44 (mockup before living-docs), D-42 (built UI equal-or-better than the approved mockup, never different).

## 7. In flight, and what I am waiting for
- Owner: prod OK for PR #30 (after the WIP lands), #26 and #29 (docs archives), then each release.
- Peer agents told to restart for 3.13.0 (2026-10-07). agente-claro-mediacion and agente-KH-ceo know the
  phrase format.
- Owner's personal D-47 diff applied 2026-10-07 (backup in the session scratchpad `backup-d47-*`).

## 8. What a new session CANNOT derive from the repo
- Each OS account has its own plugin install; a session keeps the version it loaded until restarted.
- The approval hook resolves the change from the session's working tree (fixed by-name in 3.13.1, not
  yet released): until then, put the session's cwd in the change's own worktree before asking the phrase.
- A merge command must run alone (`gh pr merge N --merge`); chaining with `gh run watch` is blocked.
- Public repo, neutral method; names allowed only in authorship records. Cleanup scheduled at the end.
- macOS CI jobs sometimes get cancelled by the runner: `gh run rerun <id> --failed` once.

## 9. Scheduled tasks — with their full prompt
None.

## 10. Last updated
2026-10-16 · agente-karvey · save after 3.13.0; three subagents lost with the session; partial work listed in §0/§1.
