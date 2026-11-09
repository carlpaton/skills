# GitHub Actions base (shared by the gha skills)

The common path for building a container image and deploying it to an Azure Container App. `/gha:deploy` writes the workflows and `/gha:secrets` sets the secrets and variables they use.

## The contract with the infrastructure

The pipeline never creates infrastructure. It deploys into an existing Container App, and by convention (the one the `infra` plugin's `tf-web` and `tf-worker` skills use, though this plugin does not depend on it) the names are derived like this. Never invent a name:

| Pipeline value | Derived as |
|----------------|------------|
| resource group | `<prefix>-<service>-<env>-rg` |
| container app | `<prefix>-<service>-<env>` |
| container apps environment | `<prefix>-<service>-<env>-cae` |
| registry name | `<prefix><service>registry<env>` |
| registry server | `<registry name>.azurecr.io` |

`env` is `uat` or `prod`. If the repo (or a sibling `*.infra` repo) has Terraform for this service, read `prefix`, `service` and the names from it and prefer what is there over the derivation. If the names cannot be found, ask.

## Inputs

Ask only for what is missing. Never invent a value, and never put a secret in a file.

| Input | Notes |
|-------|-------|
| `service` | `web` or `worker`, from the argument or asked. |
| `prefix` | Short project prefix, for example `ao`, `resolv`, `onepic`. Lowercase letters and digits. |
| `envs` | Default `uat` and `prod`. |
| `root` | The repo to write into. Default the current directory. |
| stack | Detect it. Only .NET is supported so far (`*.sln`, `*.slnx` or `*.csproj`). If it is anything else, say so and stop. |
| checks | The build, format and test commands. Read them from `CLAUDE.md` or `README.md`, else use `dotnet build`, `dotnet format --verify-no-changes` and `dotnet test`. |
| app settings | Environment variables the app needs at runtime, see below. |

Read the repo's own conventions first (`CLAUDE.md`, `docs/conventions/deployment.md`). They decide the language version and the commands. The flow below is fixed by this skill: if the repo's docs describe a different one (for example a required approval before prod), say so in the report and do not silently change them.

## Flow

| Event | Runs | Deploys to |
|-------|------|------------|
| pull request to `main` (opened, updated, reopened) | CI, then deploy | `uat` |
| push to `main` (a merged PR) | CI, then deploy | `prod` |

- There is no approval step in the pipeline. The gate is the pull request: review and green checks before merge. Do not add required reviewers, wait timers or manual approvals to the environments or workflows.
- CI (build, format check and tests) must pass before any deploy.
- No GitHub Environments. On a private repo they need a paid plan, and creating them needs admin rights. Secrets and variables are repository level, and the environment is a name prefix: `UAT_` and `PROD_`. `deploy.yml` passes `secret_prefix: UAT` or `PROD` and `deploy-environment.yml` picks the secret with `secrets[format('{0}_NAME', inputs.secret_prefix)]` (and `vars[...]` for variables). One set of workflow files serves both environments.
- Because the secrets are repository level, any workflow in the repo can read the prod ones, and a PR branch that edits a workflow could too. Branch protection on `main` is the only guard. Mention this in the report.
- Deploys to the same environment run one at a time and are never cancelled part way through, because several open PRs share one UAT.
- Pull requests from forks get no secrets, so their deploy fails. That is expected.

## Secrets and variables

Fixed names. Each is set once per environment as `UAT_<name>` and `PROD_<name>`, for example `UAT_ACR_SERVER` and `PROD_ACR_SERVER`:

| Name | Kind | Source |
|------|------|--------|
| `ACR_SERVER` | variable | `<registry name>.azurecr.io` |
| `ACR_USERNAME` | secret | registry admin username (the registry has `admin_enabled`) |
| `ACR_PASSWORD` | secret | registry admin password |
| `AZURE_CREDENTIALS` | secret | JSON of a service principal that can deploy to the resource group |

App settings are extra names chosen with the user, one line each as `ConfigKey=NAME`, with `NAME` (set as `UAT_NAME` and `PROD_NAME`) a secret (connection strings, keys) or a variable (endpoints, deployment names, urls). If the infrastructure Terraform has add-ons, offer the likely ones: `pgsql.tf` (a connection string), `blob-storage*.tf` (a connection string each), `foundry.tf` (key, endpoint, deployments). Use the names the app's `appsettings.json` implies, for .NET `Section__Key`. Values that are the same in every environment and not sensitive (for example a container name) are written into the workflow as literals.

## Rules

- Write files only. Do not commit unless asked. The workflows are not run by these skills.
- Secret values never go in a file, in chat, or in a command line argument. They move from their source to `gh secret set` over a pipe or the prompt `gh` shows the user.
- The skills never create or change Azure resources. Creating the service principal is a command the person runs.
- Pin actions to the major versions in the templates. Do not use `pull_request_target`, and do not echo secrets.
