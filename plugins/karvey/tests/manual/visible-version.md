# Visible-version check after a DEV deploy (REQ-W1-041)

> Manual agent-behaviour script (AC-7, architecture §6.5, E1.F14.T4). Run it in a real session started with
> the branch plugin, `claude --plugin-dir ~/Dev/karvey/plugins/karvey`, inside a throw-away repo under
> `$SCRATCH` (`git init -q -b main "$SCRATCH/<name>"` plus a bare `origin`), never in this repo or `~/.claude/`.
> It FAILS if any line under **Expected:** is not observed: file the evidence under
> `docs/spec/changes/<change>/qa/manual/<script>-<date>.md` with PASS/FAIL and log a failure as a finding;
> never edit the script to match what happened.

## Setup
- A project whose DEV front shows its version (e.g. `DEV 2.10.4` in the footer) and whose deployed commit's
  version file says `2.10.4`. The change `fixture-09` is at phase `deploying` with the dev deploy done.
- Second variant: two changes merged to `dev`; the second one bumped the version file to `2.10.5` after the
  first one's commit was deployed.
- Third variant: a DEV front that shows no version at all.

## Prompt
`/karvey:karvey-deploy fixture-09` and let it reach the post-deploy check.

## Expected:
- Variant 1: the check passes: it accepts `DEV 2.10.4` (the bumped version with a DEV mark, in any format) and
  compares it with the version file **of the deployed commit** (`git show <deployed-sha>:<version file>`).
- Variant 2: no mismatch is reported: the comparison uses the deployed commit's version file, not the tip of `dev`.
- Variant 3: the missing visible version is reported as a **recommendation**, not as a QA finding, and the
  deploy is not blocked by it.

## Evidence
- The screenshot or text of the DEV page version (via the browser agent), the `git show` command the agent ran,
  and the check's result line for each variant.
