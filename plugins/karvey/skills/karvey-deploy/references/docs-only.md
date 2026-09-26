# Deploy reference: documentation-only PRs

Loaded by `karvey-deploy` only when the change's lane is `docs` or its diff touches only docs and specs.

If the diff touches only docs/specs (`git diff --name-only "origin/$I"...HEAD`), it follows the **docs-only lane** (the multi-agent rule §8[^r-multi-agent]): light CI only (the plugin linter / spec validation), merged by `project.json:docs_pr.merged_by`, no version bump, no deploy, no prod approval. If code sneaks in, it is not docs-only.

[^r-multi-agent]: ../../karvey/rules/multi-agent.md — context only, not opened.
