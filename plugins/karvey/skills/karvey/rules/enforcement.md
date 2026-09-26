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
`karvey-state.py approve … --role ceo-delegate --ref D-NN` when the human delegated it (`multi-agent`[^r-multi-agent] §4).
The production approval is never delegated: it needs a prod-kind marker from the human's own prompt.

## prod-gate (PreToolUse on Bash, on by default, D-02)

Merges and pushes into production need a human prod approval in the release ledger
(`karvey-state.py approve {change-id} prod`, D-03).

- Blocks `gh pr merge`, `az repos pr update --status completed`, `glab mr merge` and `git push` into production without it. <!-- guard-case: pg1-01-gh-merge-admin-no-approval, pg1-18-az-complete-no-approval, pg1-22-glab-merge-no-approval, pg1-25-git-push-main-no-approval, pg3-03-pr-into-master-default-dev-gated, pg3-06-integration-named-main-still-gated -->
- Allows the same command once the ledger holds the approval. <!-- guard-case: pg1-02-gh-merge-with-ledger, pg1-20-az-complete-with-ledger -->
- A merge into the integration branch stays silent, also when the remote default branch is the integration branch (D-15); `main` and `master` are always gated. <!-- guard-case: pg1-06-gh-merge-into-dev-silent, pg3-01-pr-into-dev-default-dev-not-gated, pg3-02-merge-into-dev-default-dev-not-gated -->
- Blocks when the change cannot be determined, the CLI fails or times out, or the files are corrupt (fails closed). <!-- guard-case: pg1-08-change-cannot-be-determined, pg1-12-gh-timeout-fails-closed, pg2-05-corrupt-spec-json, pg2-08-corrupt-ledger -->
- A hand-edited `approvals.prod` without the ledger still blocks. <!-- guard-case: pg2-07-hand-edited-approvals-prod-without-ledger -->

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

[^r-multi-agent]: multi-agent.md — context only, not opened.
