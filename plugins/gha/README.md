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
| `/gha:secrets` | Create the GitHub Environments and set the secrets and variables the workflows use |

Run `/gha:deploy` first, then `/gha:secrets`. When the app gains a setting such as a database connection, run `/gha:deploy` again: it adds the setting to the workflow once, and `/gha:secrets` then sets its value on both `uat` and `prod`. `/gha:secrets` reads the workflows to build its list, so it always matches what they use.

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

Secrets and variables live on GitHub Environments `uat` and `prod` with the same names in each, so the workflows have no environment prefixes.

| Name | Kind |
|------|------|
| `ACR_SERVER` | variable |
| `ACR_USERNAME`, `ACR_PASSWORD` | secret |
| `AZURE_CREDENTIALS` | secret |
| app settings you choose | secret or variable |

Secret values are never written to a file or shown. They are piped from a read-only Azure lookup into `gh secret set`, or typed by you at the `gh` prompt. Creating the deploy service principal is a command you run yourself.

## Deploy targets

The workflows deploy into an existing Container App named `<prefix>-<service>-<env>` in resource group `<prefix>-<service>-<env>-rg`, with registry `<prefix><service>registry<env>`. These are the names the `infra` plugin's `tf-web` and `tf-worker` create, but this plugin does not need it: the skill reads the names from your Terraform if it can find it, and otherwise derives or asks.

## Safety

The skills only write files and call `gh`. They never run a workflow, create or change Azure resources, or delete secrets or environments.
