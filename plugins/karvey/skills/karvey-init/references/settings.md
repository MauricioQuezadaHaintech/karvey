# Init reference: settings-only mode (`--settings`)

Loaded by `karvey-init` only when it runs with `--settings` (or the user only asks to configure the team). It
creates no change: no change-id, no `docs/spec/changes/…`, no `spec.json`, no tracker item.

1. Pre-fill every question of the team settings with the current values of `project.json` and ask them as the
   team-settings reference says (`references/team-settings.md`, loaded with this one).
2. Merge the answers without dropping untouched keys (`events`, `location`, custom keys).
3. Write `project.json` on a docs branch, as a reviewed change (team-settings reference, *Write the settings*).
4. Print the `Settings:` line and **STOP**.

If `project.json` does not exist, say so and ask whether to create a minimal one (the Step 3 fields of the skill)
— nothing else.
