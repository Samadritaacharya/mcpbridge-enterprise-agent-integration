# Recommended main-branch protection

After the first green pull request, protect `main` with a GitHub ruleset requiring:

- pull requests before merge;
- required status checks **Python verification** and **Web verification**;
- branches up to date before merge;
- conversation resolution;
- block force pushes;
- restrict deletions;
- no bypass actors for normal portfolio development.

For a solo portfolio repository, requiring a PR with `0` mandatory external approvals preserves the review/CI boundary without making the owner depend on a second maintainer.
