# Closing checklist — agente-karvey

Before reporting anything as done (`plugins/karvey/skills/karvey/rules/verification.md`):
- [ ] Full suite green: `python3 -m unittest discover -s plugins/karvey/tests/unit` · regression suite · `bash plugins/karvey/hooks/tests/test-hooks.sh` · `python3 plugins/karvey/tests/hooks/run_tables.py` · `node --test plugins/karvey/tests/page/`.
- [ ] `python3 plugins/karvey/scripts/lint-plugin.py` and `karvey-state.py validate --all --root .` — report the real totals.
- [ ] Hook commands verified **as declared in hooks.json** (BUG-18: a test that runs the script directly proved nothing).
- [ ] No absolute paths in `graphify-out/` (only `.graphify_python`, git-ignored).
- [ ] Released = merged to `main` **and** `claude plugin update` shows the version; never claim "published" from the branch.
- [ ] Branch hygiene after every merge: absorbed branches deleted remote + local; worktrees removed.
- [ ] Every approval recorded with the owner's verbatim words (decisions.md D-NN); never paraphrase an approval.
- [ ] Estimates kept, actuals recorded (PLAN.md) — never overwrite the estimate.
