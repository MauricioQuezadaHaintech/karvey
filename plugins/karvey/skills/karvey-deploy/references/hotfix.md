# Deploy reference: `patch` and `hotfix` lanes

Loaded by `karvey-deploy` only when `spec.json:lane` is `patch` or `hotfix`.

- **The lane triplet** (`lane_triplet` of the release gate; the lanes rule[^r-lanes]): the PR carries **fix +
  `BUG-NN` (tracker + `findings.md`) + regression test**, all three, recorded with `karvey-state.py lane-evidence`,
  the test green in CI. Missing any → stop and name what is missing.
- **Fast, not unrecorded:** the same ordered flow as any change (feature branch → PR → pipeline), the same prod OK
  from the human and the same post-deploy verification; only the phases the lane skips are skipped.
- **One PR:** the fix, the incident and the regression test travel together; a hotfix merged into production is
  also brought back into the integration branch through a PR when the two differ.

[^r-lanes]: ../../karvey/rules/lanes.md — context only, not opened.
