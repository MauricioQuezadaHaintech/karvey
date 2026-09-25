---
name: karvey-upgrade
description: Karvey support — project upgrade after a plugin update: state-based plan, dry-run, picked steps on a branch, one PR — when offered or any time. Triggers include "karvey upgrade", "actualizar proyecto karvey", "plan de actualización karvey".
allowed-tools: Read, Bash, AskUserQuestion
argument-hint: (none)
---

# Karvey Upgrade

A **cross-cutting** skill of the Karvey Method: a support layer, **NOT a phase**. It does not advance or modify any change's lifecycle and never touches `spec.json:phase`.

## Purpose

Updating the plugin never changed the project by itself. After an update, the first session in a Karvey project asks once (per clone) whether to build a **project upgrade plan**. This skill turns a "yes" into one reviewable pull request: the plan is computed from the project's state by the upgrade tool, the person picks the steps, sees the exact diff, and only the picked steps are applied on an upgrade branch, in one commit that names them and who picked them.

The skill **relays the tool**. It never computes, adds, reorders or skips a step, and never edits a project file itself: every write goes through `karvey-upgrade.py` (the engine confines, previews and writes). If the tool is missing, the skill says so and stops; it never does the steps by hand.

It is invocable at any time and behaves the same with or without an offer.

## The tool

```bash
UP="${CLAUDE_PLUGIN_ROOT}/scripts/karvey-upgrade.py"
test -f "$UP" || echo "karvey-upgrade.py not found in this plugin: stop, nothing is done by hand"
```

Subcommands: `plan` · `branch` · `apply` · `commit` · `seen` (each with `--json`). Exit codes: 0 ok · 1 a check failed / a step failed · 2 usage · 3 refused (nothing changed) · 4 not found.

## Steps

### 1. Locate the tool

Run the block above. Missing → tell the person "the upgrade tool is not in this Karvey install; update the plugin" and **stop**.

### 2. Compute the plan (writes nothing)

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/karvey-upgrade.py" plan --json
```

- Exit 3 (not a Karvey project) → say so and **stop** without writing anything.
- Exit 4 (the step catalogue is unreadable) → relay the message and stop.
- Every step `nothing` ("nothing to do") → run `seen --empty`, tell the person the project is already current, and stop:
  ```bash
  python3 "${CLAUDE_PLUGIN_ROOT}/scripts/karvey-upgrade.py" seen --empty
  ```

### 3. Show the table exactly as returned

One row per step that is not `nothing`: step · what changes (`summary`) · dry-run · risk · needs human. List the satisfied steps on one line and relay the `warnings`. Do not reword the summaries into promises. When `computed_on` is not the integration branch, add one line: "the plan is recomputed on the upgrade branch".

### 4. One question: which steps

One multi-select question (AskUserQuestion, the person's language). Every listed step is an option; the steps with `risk: low` that are not human are marked **(Recommended)**; human and report steps are labelled **"shown, not applied"** (they print instructions or a diff; nothing is performed, and no answer changes that).

- The person picks **none** → record the decline and stop (no branch, no commit):
  ```bash
  python3 "${CLAUDE_PLUGIN_ROOT}/scripts/karvey-upgrade.py" seen --decline
  ```
- The person picks **one or more** →
  ```bash
  python3 "${CLAUDE_PLUGIN_ROOT}/scripts/karvey-upgrade.py" seen --accept
  ```

### 5. Values for `needs-input` steps

For each picked step whose status is `needs-input`, ask its `inputs_needed` (one question per step). Put the answers in a values file **outside the repository** (the session's scratch or temp dir), shaped `{"<step-id>": {"<key>": "<value>"}}`; the tool checks every value through its safe-value rules and refuses an unsafe one naming the key:

```bash
VALUES="$(mktemp "${TMPDIR:-/tmp}/karvey-upgrade-values.XXXXXX")"
printf '%s\n' '{"team-settings": {"notifications.channel": "slack", "notifications.target": "#team-channel"}}' > "$VALUES"
```

A step handed to `/karvey:karvey-init --settings` (no `project.json`) is not answered here: tell the person to run that skill first.

### 6. The upgrade branch

Fetch the integration branch when a remote exists (the tool itself never fetches), then create or switch to the upgrade branch:

```bash
INTEG=$(python3 "${CLAUDE_PLUGIN_ROOT}/scripts/karvey-config.py" get branch_flow.integration --shell) || exit 1
git remote get-url origin >/dev/null 2>&1 && git fetch origin "$INTEG"
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/karvey-upgrade.py" branch --json
```

A dirty tree or an undeclared integration branch is refused by the tool with the paths / the key to set: relay it and stop.

### 7. Dry-run: show every diff

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/karvey-upgrade.py" apply --steps "a,b" --dry-run --json
```

Show each step's unified diff and the human and report output as returned. A step with `dry_run: false` has no preview: it gets **its own confirmation question**. Then **one** confirmation question: "Apply these changes?". No → stop (the branch stays, without commits). Keep the returned `preview` id.

### 8. Apply exactly what was previewed

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/karvey-upgrade.py" apply --steps "a,b" --preview "<preview id>" --json
```

Add `--values "$VALUES"` when step 5 wrote one, and `--confirm-no-preview <id>` for each step confirmed on its own. Exit 3 "the tree changed since the preview" → run the dry-run again (step 7). Exit 1 → relay `applied` / `failed` / `not_run` and stop: the person decides whether to fix and re-run (`plan` then lists only what is left).

### 9. One commit, written by the tool

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/karvey-upgrade.py" commit --picked-by "<the person>" --answer "<their words, short>" \
  --trailer "Co-Authored-By=<the session's attribution line>" --json
```

The tool stages exactly the files it wrote and writes the message (`chore(karvey): project upgrade <from> → <to>`, `Steps`, `Picked-by`, `Picked-at`, `Answer`, the trailers). It prints `pr_title` and `pr_body`.

### 10. Push and open one PR — never merge

```bash
UB=$(git symbolic-ref --short HEAD)
git push -u origin "$UB"
```

Open **one** PR from the upgrade branch to the integration branch with `pr_title` / `pr_body`, using the repository's host (`project.json:git_platform`, or the `origin` URL): `gh pr create --base "$INTEG" --head "$UB" --title … --body …` · `az repos pr create --target-branch "$INTEG" --source-branch "$UB" …` · `glab mr create --target-branch "$INTEG" --source-branch "$UB" …`. No PR tooling or no remote → print the exact commands for the person. A rejected push → report it with the retry command; the commit stays local. **Never merge**: the PR goes through the project's normal review.

## What this skill never does

- Compute, add, reorder or skip a step, or edit a project file by hand.
- Write under the user's home: human steps print the stable statusline command or a diff for the person to apply.
- Record a decline or an acceptance the person did not give (an unanswered question records nothing; the offer comes back next session).
- Merge the upgrade PR.

---
*Part of the Karvey™ Method · Apache 2.0 · see `karvey/LICENSE` and `../karvey/TRADEMARK.md`.*
