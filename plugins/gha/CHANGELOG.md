# Changelog

Changes to the `gha` plugin. Versions follow `version` in `.claude-plugin/plugin.json`.

## 0.2.0

- Changed: no GitHub Environments. Secrets and variables are repository level with a `UAT_` or `PROD_` prefix, so the pipeline works on a private repo on a free plan. `deploy.yml` passes a `secret_prefix` input and `deploy-environment.yml` picks the matching secret. `/gha:secrets` sets the prefixed names and no longer creates environments. Existing pipelines must be regenerated, and their secrets renamed.

## 0.1.0

- First release: `/gha:deploy` writes the CI and deploy workflows for a .NET web app or worker, and `/gha:secrets` sets up the GitHub Environments, secrets and variables.
