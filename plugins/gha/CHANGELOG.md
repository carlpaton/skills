# Changelog

Changes to the `gha` plugin. Versions follow `version` in `.claude-plugin/plugin.json`.

## 0.3.1

- Changed: the README now explains how to add settings later, such as a Postgres connection string: add the key to `appsettings.json`, re-run `/gha:deploy` with `ConfigKey=NAME`, then run `/gha:secrets`.

## 0.3.0

- Changed: `/gha:secrets` now creates the deploy service principal and sets `AZURE_CREDENTIALS` itself, after the person confirms. It only does so when the active `az` subscription matches the expected one, the resource group exists, no service principal of that name exists and the secret is not already set. The principal is scoped to the resource group, the secret is piped straight in, and the role assignment is checked afterwards. It never resets or deletes an existing principal.

## 0.2.0

- Changed: no GitHub Environments. Secrets and variables are repository level with a `UAT_` or `PROD_` prefix, so the pipeline works on a private repo on a free plan. `deploy.yml` passes a `secret_prefix` input and `deploy-environment.yml` picks the matching secret. `/gha:secrets` sets the prefixed names and no longer creates environments. Existing pipelines must be regenerated, and their secrets renamed.

## 0.1.0

- First release: `/gha:deploy` writes the CI and deploy workflows for a .NET web app or worker, and `/gha:secrets` sets up the GitHub Environments, secrets and variables.
