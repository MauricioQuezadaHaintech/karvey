# Deploy reference: branch hygiene

Loaded by `karvey-deploy` after the production merge (step 2.11). The full rule is *Branch hygiene* of the deploy
workflow, on the skill's `Load:` line.

Delete what production absorbed; never delete what it did not:
```bash
git fetch origin --prune
git branch -r --merged "origin/$P"             # + the cherry / tree checks of the rule
git push origin --delete "feature/{change-id}"   # only if absorbed
git branch -d "feature/{change-id}"
```
Absorbed non-protected branches are deleted (closing their PR with a comment); **not absorbed ones are listed** with their unique commits and PR for the human. Report the counts.
