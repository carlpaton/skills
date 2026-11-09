# GHA

Claude Code skills that create the GitHub Actions pipeline for a containerised .NET app deployed to Azure Container Apps, and set up the secrets it needs. Two kinds of app are supported: a web app and a console worker. Only .NET is supported so far.

## Installation

```
claude plugin marketplace add carlpaton/skills
claude plugin install gha@carlpaton
```

Skills are then `/gha:deploy` and `/gha:secrets`.

## Skills

| Skill | Use it to |
|-------|-----------|
| `/gha:deploy [web\|worker]` | Create the workflows, a Dockerfile if there is none, and `docs/github-actions.md` listing every secret and variable |
| `/gha:secrets` | Set the repository secrets and variables the workflows use, with a `UAT_` or `PROD_` prefix |

Run `/gha:deploy` first, then `/gha:secrets`. When the app gains a setting such as a database connection, run `/gha:deploy` again: it adds the setting to the workflow once, and `/gha:secrets` then sets its value as `UAT_<name>` and `PROD_<name>`. `/gha:secrets` reads the workflows to build its list, so it always matches what they use.

## Flow

| Event | Runs | Deploys to |
|-------|------|------------|
| pull request to `main` | CI, then deploy | `uat` |
| push to `main` (a merged PR) | CI, then deploy | `prod` |

There is no approval step in the pipeline. The pull request is the gate, so protect `main` with required reviews and checks in the repo settings (the skills do not change that).

## Output

```
.github/workflows/ci.yml                  build, format check and tests, called by the deploy
.github/workflows/deploy.yml              picks the environment from the event
.github/workflows/deploy-environment.yml  build, push and deploy for one environment
Dockerfile                                only if the repo has none
docs/github-actions.md
```

The web and worker workflows differ only in ingress: a web app deploys with external ingress on port 8080, a worker has none.

## Secrets

Secrets and variables are repository level, not GitHub Environments, so this works on a private repo on a free plan. Each name is set twice, as `UAT_<name>` and `PROD_<name>`, and the workflow picks the one for its environment. The trade-off: any workflow in the repo can read the prod values, so protect `main`. Setting them needs the repo owner on a personal account.

| Name | Kind |
|------|------|
| `ACR_SERVER` | variable |
| `ACR_USERNAME`, `ACR_PASSWORD` | secret |
| `AZURE_CREDENTIALS` | secret |
| app settings you choose | secret or variable |

Secret values are never written to a file or shown. They are piped from a read-only Azure lookup into `gh secret set`, or typed by you at the `gh` prompt. The deploy service principal (`AZURE_CREDENTIALS`) is created by `/gha:secrets` after you confirm, and only if the active `az` subscription is the expected one, the resource group exists and no principal of that name exists yet.

## Adding settings later

When the app gains a setting (a database connection string, a storage key, an endpoint), add it in three steps. A Postgres connection string is the example.

1. Add the key to `appsettings.json` first, with an empty or placeholder value, for example `ConnectionStrings:Default`. Never commit the real value. The skill reads `appsettings.json` and any infra files such as `pgsql.tf`, `blob-storage*.tf` and `foundry.tf`, and offers the keys it has not mapped yet.
2. Run `/gha:deploy` again. It asks what to add, change or remove, in the form `ConfigKey=NAME`, for example `ConnectionStrings__Default=PG_CONNECTION_STRING`. For .NET the key is the `Section__Key` form of the setting the app reads. For each name it asks whether it is a **secret** (connection strings, keys) or a **variable** (endpoints, hosts, deployment names). It then updates the workflows and `docs/github-actions.md`.
3. Run `/gha:secrets`. It reads the workflows, shows the new names as missing, and sets `UAT_PG_CONNECTION_STRING` and `PROD_PG_CONNECTION_STRING`. If the value comes from a read-only Azure lookup it pipes it straight in. Otherwise run `gh secret set UAT_PG_CONNECTION_STRING --repo <owner>/<repo>` and type the value at the prompt. A name that is already set is only overwritten when you say you are rotating it.

The setting key must match what the app reads, or the deploy succeeds and the app fails at runtime. A value that is the same in every environment and not sensitive is written into the workflow as a literal instead.

## Deploy targets

The workflows deploy into an existing Container App named `<prefix>-<service>-<env>` in resource group `<prefix>-<service>-<env>-rg`, with registry `<prefix><service>registry<env>`. These are the names the `infra` plugin's `tf-web` and `tf-worker` create, but this plugin does not need it: the skill reads the names from your Terraform if it can find it, and otherwise derives or asks.

## Safety

The skills only write files and call `gh` and `az`. They never run a workflow, create or change Azure infrastructure, or delete secrets or environments. The one thing created in Azure is the deploy service principal, with your confirmation and under the checks above.
