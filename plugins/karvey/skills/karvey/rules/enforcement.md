# Rule: Hook-based enforcement

A skill is guidance the model follows voluntarily. What must hold regardless is enforced by the plugin's
hooks: `${CLAUDE_PLUGIN_ROOT}/hooks/hooks.json` routes every event to one dispatcher (`${CLAUDE_PLUGIN_ROOT}/hooks/karvey-hook.sh`),
which runs the guards registered in `karvey_lib/karvey_hooks.py`. Each promise below is pinned to a case of
`${CLAUDE_PLUGIN_ROOT}/tests/hooks/tables/`; a promise without a case is not made.

## Switches (reviewed line)

Switches live in `project.json:enforcement` and are read from the working copy **and** from
`origin/{production}` (`karvey-guard` changes them on a docs branch; they take effect after merge).

| Guard | Default | Switch |
|---|---|---|
| protect-paths | always on | none |
| approval hook | on in a Karvey project | vocabulary and TTL from the reviewed line |
| prod-gate | **on** (D-02) | `enforcement.prod_gate_hook: false` in the working copy **and** on `origin/{production}` |
| git-flow | off | `enforcement.git_flow_hook: true` |
| plan-gate | off | `enforcement.plan_gate_hook: true` |
| spec-write validator | on | `schema_mode` (advisory / strict) |
| subagent-prompt | on in a Karvey project (fail open) | none |

- An opt-in guard left off blocks nothing. <!-- guard-case: gf-56-disabled-by-default, pg-59-disabled-by-default -->
- Enabling it only on the reviewed line is enough: the guard blocks. <!-- guard-case: gf-57-on-in-reviewed-line-only, pg-61-on-in-reviewed-line-only -->
- Setting `prod_gate_hook: false` only in the working copy still blocks the merge. <!-- guard-case: pg2-03-false-only-in-working-copy-blocks -->
- `false` in both places disables it and prints the notice. <!-- guard-case: pg2-02-false-in-both-disabled -->

## protect-paths (always on)

The approval markers, the release ledger, the `.git/karvey` state dir, the compatibility marker (D-11) and
the plugin's own files are never written by the agent.

- Blocks `touch`, redirections, `cp`/`mv` and interpreter writes that name them. <!-- guard-case: pp-01-touch-marker, pp-02-echo-redirect-into-marker, pp-04-mv-ledger, pp-05-python-writes-marker -->
- Blocks Write/Edit on a marker, the ledger or a plugin file. <!-- guard-case: pp-07-write-tool-on-marker, pp-08-edit-tool-on-ledger-relative, pp-10-edit-plugin-hook -->
- Blocks writing the notification confirmation (`approvals/notify/`) or the notify record (`notify-last.json`). <!-- guard-case: nc-10-protect-paths-blocks-writing-the-confirmation, nc-11-protect-paths-blocks-editing-the-confirmation, nc-12-protect-paths-blocks-writing-the-notify-record -->
- Allows running the plugin's scripts and reading the audit log. <!-- guard-case: pp-14-running-plugin-script-allowed, pp-16-reading-the-audit-log-allowed -->
- Blocks a glob or a shell variable that could expand to those directories (`.git/kar?ey/ledger`, `cd kar*ey`, `D=karvey; .git/$D/…`) and a redirection into them. <!-- guard-case: pp-18-glob-in-state-dir-path-blocked, pp-19-cd-chain-glob-then-mkdir-blocked, pp-20-variable-path-component-blocked, pp-21-bare-wildcard-under-git-into-ledger-blocked, pp-27-echo-into-the-ledger-still-blocked -->
- Allows globs and variables elsewhere, and text that only mentions the paths (echo/printf arguments, a commit message). <!-- guard-case: pp-23-globs-elsewhere-allowed, pp-24-variables-elsewhere-allowed, pp-25-commit-message-mentioning-the-path-allowed, pp-26-echo-text-mentioning-the-record-allowed -->

## Approval hook (UserPromptSubmit, D-01, D-10)

An approval exists only when the human types it. The hook reads the human's prompt, strips quoted material
(code, `>` lines, pasted logs), applies negation and question precedence, and records a marker under
`<git-common-dir>/karvey/approvals/` with kind, scope (the active change) and a TTL
(`plan_marker_ttl_min`, default from `karvey_lib/defaults.json`). `karvey-state.py advance` consumes it when
the phase it approved closes.

- An approval word prints `[karvey] approval recorded (<kind>, <scope>, expires hh:mm)`. <!-- guard-case: ap-01-approval-aprobado, ap-02-approval-ok -->
- A negation, a question or quoted text records nothing and prints nothing. <!-- guard-case: ap-08-negation-or-question, ap-15-quoted-code-fence, ap-16-quoted-blockquote -->
- A prod-kind marker needs an approval word **and** a production word naming the change (D-10). <!-- guard-case: ap-19-prod-kind-d10, ap-22-prod-word-with-negation -->
- With `KARVEY_COMPAT_MARKER` set, the hook also writes that path (D-11). <!-- guard-case: ap-32-compat-marker-written-d11 -->
- An empty file created by hand is not a marker: plan-gate still blocks. <!-- guard-case: pg-51-touch-empty-file-is-forged -->
- A changed notification destination is confirmed only by the human typing `confirmo notificacion <code>` (or `confirm notification <code>`; the 8-hex code `notify-check` prints): the hook records it for this project and that destination, with the same TTL, and prints `[karvey] notification destination confirmation recorded (<code>, expires hh:mm)` (D-16). <!-- guard-case: nc-01-human-phrase-records-the-confirmation, nc-02-english-phrase-and-approval-together -->
- `karvey-config.py notify-check --confirm` without that confirmation (the agent alone), or with one for another destination or project, or an expired one, prints `NOT CONFIRMED` with the phrase to type and returns status 10; the destination stays unconfirmed. <!-- guard-case: nc-05-agent-alone-cannot-confirm, nc-07-marker-for-another-destination-does-not-count, nc-08-marker-for-another-project-does-not-count, nc-09-expired-marker-does-not-count -->

Approval delegation (multi-agent): a coordinating agent may record a non-prod phase approval with
`karvey-state.py approve … --role ceo-delegate --ref D-NN` when the human delegated it (`multi-agent.md` §4).
The production approval is never delegated: it needs a prod-kind marker from the human's own prompt.

## prod-gate (PreToolUse on Bash, on by default, D-02)

Merges and pushes into production need a human prod approval in the release ledger
(`karvey-state.py approve {change-id} prod`, D-03). The approval counts only when the approval hook's audit
line of its prod marker exists (prompt hash, session, time; D-34), for the head commit the human approved,
and for 24 h after the OK (D-35). A `reopen` of the change supersedes it (D-36).

- Blocks `gh pr merge`, `az repos pr update --status completed`, `glab mr merge` and `git push` into production without it. <!-- guard-case: pg1-01-gh-merge-admin-no-approval, pg1-18-az-complete-no-approval, pg1-22-glab-merge-no-approval, pg1-25-git-push-main-no-approval, pg3-03-pr-into-master-default-dev-gated, pg3-06-integration-named-main-still-gated -->
- Allows the same command once the ledger holds the approval. <!-- guard-case: pg1-02-gh-merge-with-ledger, pg1-20-az-complete-with-ledger -->
- A merge into the integration branch stays silent, also when the remote default branch is the integration branch (D-15); `main` and `master` are always gated. <!-- guard-case: pg1-06-gh-merge-into-dev-silent, pg3-01-pr-into-dev-default-dev-not-gated, pg3-02-merge-into-dev-default-dev-not-gated -->
- Blocks when the change cannot be determined, the CLI fails or times out, or the files are corrupt (fails closed). <!-- guard-case: pg1-08-change-cannot-be-determined, pg1-12-gh-timeout-fails-closed, pg2-05-corrupt-spec-json, pg2-08-corrupt-ledger -->
- A hand-edited `approvals.prod` without the ledger still blocks. <!-- guard-case: pg2-07-hand-edited-approvals-prod-without-ledger -->
- A ledger entry without the approval hook's audit line of its marker blocks. <!-- guard-case: pg5-01-ledger-without-the-hook-audit-record -->
- The released commit must be the approved one: a commit made after the OK, another branch pushed as the change, a PR head that moved, or an approval older than 24 h blocks. <!-- guard-case: pg5-02-commit-after-the-approval, pg5-03-other-commit-pushed-as-the-change, pg5-04-pr-head-is-not-the-approved-commit, pg5-11-az-pr-source-commit-differs, pg5-06-approval-older-than-24h -->
- It blocks when it cannot tell which commit is released: a PR answer without its head commit, `--all`/`--mirror`/a delete, or an earlier command in the same call that can move the branch (run the merge or push on its own). <!-- guard-case: pg5-05-pr-answer-without-head-commit, pg5-09-push-all-cannot-name-the-commit, pg5-07-earlier-command-moves-the-released-branch, pg5-08-push-then-merge-in-one-call -->
- Without python it blocks every production merge or push (fail closed, unchanged by D-35): it never reads the ledger. <!-- guard-case: pg5-02-commit-after-the-approval -->
- The push destination comes from the repository too: aliases (`-c alias.X=push`, configured, shell), `-c` push settings, a configured upstream or push refspec, `send-pack` and `@` count, and a push or merge run through `xargs` or `find -exec` cannot be verified. <!-- guard-case: pg4-01-inline-alias-to-push-main, pg4-02-configured-alias-to-push-main, pg4-03-inline-remote-push-refspec, pg4-05-configured-upstream-bare-push, pg4-06-configured-remote-push-refspec, pg4-07-send-pack-into-main, pg4-08-xargs-git-push, pg4-19-push-at-sign-from-main, pg4-22-shell-alias-push-into-main -->
- gh aliases and `gh api` writes to a production branch (the merges endpoint, `git/refs`, `mergeBranch`) are gated; a ref write to another branch is not. <!-- guard-case: pg4-10-gh-alias-to-pr-merge, pg4-11-gh-api-merges-endpoint-into-main, pg4-12-gh-api-ref-update-of-main, pg4-13-gh-api-graphql-merge-branch, pg4-14-gh-api-delete-feature-ref-allowed -->
- `git push --tags` pushes no branch and is not gated. <!-- guard-case: pg4-17-push-tags-from-main-allowed -->
- The block says how to record the approval, or names the switch when the change is unknown. <!-- guard-case: pg4-23-block-says-how-to-record-the-approval, pg4-24-unknown-change-names-the-switch -->

## git-flow (PreToolUse on Bash, opt-in)

Resolves the target repository per segment (`cd`, `git -C`, `GIT_DIR`, `bash -c`, aliases) and matches
branch names whole.

- Blocks `git commit`, `merge`, `cherry-pick`, `revert` and `am` on the integration or production branch. <!-- guard-case: gf-01-commit-on-master, gf-02-commit-on-dev, gf-28-merge-on-master, gf-30-cherry-pick-on-dev -->
- Blocks pushes into production, force pushes, `--all`, `--mirror` and deletes of protected branches. <!-- guard-case: gf-12-push-master-from-feature, gf-22-force-push-dev, gf-17-push-all, gf-15-push-delete-master -->
- Blocks manual deploys (`func … publish`, `az webapp up`, `vercel --prod`, `firebase deploy`, `gcloud run deploy`). <!-- guard-case: gf-34-manual-deploy-func-publish, gf-35-manual-deploy-az-webapp-up, gf-37-manual-deploy-vercel-prod, gf-39-manual-deploy-firebase-deploy -->
- Allows commits and pushes on a feature branch and a merge on the integration branch. <!-- guard-case: gf-03-commit-on-feature, gf-11-bare-push-on-feature, gf-29-merge-on-dev-allowed -->
- Trunk flow: blocks commits and direct pushes on `main`. <!-- guard-case: gf-50-trunk-commit-on-main, gf-52-trunk-bare-push-on-main -->

## plan-gate (PreToolUse on Bash and Edit/Write, opt-in)

- Blocks Edit/Write and the write and destructive shell classes (redirections, `tee`, `rm`, `git clean`, `find -delete`, `sed -i` …) without a valid marker. <!-- guard-case: pg-43-edit-without-marker, pg-09-write, pg-15-destructive -->
- Allows read-only commands and `2>/dev/null`. <!-- guard-case: pg-01-not-a-write, pg-37-allowed -->
- A marker of another project or change, expired or consumed, still blocks. <!-- guard-case: pg-48-marker-of-another-project, pg-49-marker-121-min-old, pg-50-consumed-marker, pg-52-marker-of-another-change -->
- A valid marker of the active change allows the write. <!-- guard-case: pg-47-valid-project-marker-10min, pg-53-marker-of-the-active-change -->
- Limitation: a write done inside an interpreter (`python -c`, `node -e`) is allowed; the gate does not parse programs. <!-- guard-case: pg-57-interpreter-write-python, pg-58-interpreter-write-node -->

## subagent-prompt (PreToolUse on Agent/Task, BUG-25)

A subagent never writes `docs/spec/project.json` (`management-adapters.md` rule 5). The rule in the skill
text does not reach a session that writes a subagent prompt before it loads any skill, so the prompt is
checked when the tool is called.

- A prompt with a sentence that lets the subagent write the settings (a write, persist or authorise verb followed within a few words by `docs/spec/project.json`, the tracker or team settings or a status map, not negated just before the verb) and without the ban on `docs/spec/project.json` itself is blocked; the message gives the line to add. <!-- guard-case: sp-01-rerun-prompt-persist-settings-blocked, sp-02-first-run-prompt-persist-map-blocked, sp-07-task-tool-name-blocked, sp-13-ban-like-sentence-does-not-excuse-a-write-blocked -->
- A settings page, an editor's `settings.json`, tests for a status-mapping function and another tool's `project.json` are not the project settings. <!-- guard-case: sp-08-settings-page-component-allowed, sp-09-editor-settings-file-allowed, sp-10-tests-for-a-status-mapping-function-allowed, sp-12-another-tools-project-json-allowed, sp-11-typographic-apostrophe-ban-allowed -->
- The ban line, a prompt that does not touch the settings, a negated sentence and any prompt outside a Karvey project are allowed. <!-- guard-case: sp-03-ban-line-present-allowed, sp-04-no-settings-talk-allowed, sp-05-negated-settings-sentence-allowed, sp-06-outside-a-karvey-project-allowed -->
- Fail open: without python the call goes through, and the text rule still applies.

## spec-write validator (PostToolUse on Edit/Write)

Every written `docs/spec/**/spec.json` and `docs/spec/project.json` is validated in-process by
`karvey-state.py validate`.

- A valid file stays silent. <!-- guard-case: sw-01-valid-spec-silent, sw-02-valid-project-json-silent -->
- A violation (enum, prod without `ref`, broken JSON) exits 2 with the list, which the session sees. <!-- guard-case: sw-03-enum-violation-qa-approved, sw-05-prod-ref-missing, sw-09-invalid-json -->

## Legacy templates (deprecated, removed in 4.0.0)

`../hooks/git-flow-guard.sh` and `../hooks/plan-gate.sh` are shims kept for projects that copied the 3.11
templates into `settings.json`; they call the dispatcher, so they enforce the same rules.
`karvey-guard` detects those entries and offers to remove them.

- The git-flow shim blocks a commit on the production branch. <!-- guard-case: shim-01-git-flow-commit-on-master-blocks -->
- The plan-gate shim blocks a write without a marker. <!-- guard-case: shim-03-plan-gate-write-without-marker-blocks -->
