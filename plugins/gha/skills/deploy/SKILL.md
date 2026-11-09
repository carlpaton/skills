---
name: deploy
description: Create the GitHub Actions workflows that build a container image and deploy it to an Azure Container App. A pull request builds and deploys to UAT, merging to main deploys to prod, with no approval step (the pull request is the gate). Writes ci.yml, deploy.yml, deploy-environment.yml, a Dockerfile if missing and docs/github-actions.md listing the secrets and variables needed. Use when the user wants CI/CD for a web app or console worker, then run secrets.
argument-hint: [web|worker]
---

# GitHub Actions: deploy a container app

Create the pipeline for one service. Follow [../_shared/github-actions.md](../_shared/github-actions.md) for the inputs, the contract with the infrastructure, the flow and the rules.

## Steps

1. Read the shared doc, then the repo's `CLAUDE.md` and deployment conventions. If they describe a flow other than the one in the shared doc (for example an approval before prod), tell the person now and carry on with the shared doc's flow. Collect the inputs. The first argument, if given, is the `service`. If `.github/workflows/deploy-environment.yml` already exists and was made by this skill, this is a re-run: go to [Re-run](#re-run-add-change-or-remove-app-settings) instead of the steps below. If any other file with a target name exists, stop and ask: never overwrite.
2. Find the infrastructure Terraform for this service, if any (this repo, or a sibling `*.infra` repo), and read `prefix` and the deploy target names from it. Otherwise derive them.
3. Detect the .NET pieces:
   - the host project: the `.csproj` using `Microsoft.NET.Sdk.Web` for `web`, or the worker or console host for `worker`. Ask if there is more than one candidate.
   - the assembly name (`AssemblyName` in the csproj, else the csproj file name) and the major version from `global.json` or `TargetFramework`.
   - an existing `Dockerfile`. If there is none, offer to create one from [Dockerfile.dotnet.tmpl](Dockerfile.dotnet.tmpl): `{{runtime_image}}` is `aspnet` for web and `runtime` for worker, and `{{expose}}` is `EXPOSE 8080` plus a blank line for web, empty for worker.
4. Ask for the app settings (see the shared doc). Offer the likely ones from the infra add-ons, and read `appsettings.json` to suggest the config keys. An empty list is fine. Add `ASPNETCORE_ENVIRONMENT` and `DOTNET_ENVIRONMENT` as literals, `Staging` for uat and `Production` for prod, unless the app already says otherwise.
5. **Confirm** before writing: the files, the derived deploy targets, the app settings, and the flow (PR to UAT, merge to prod, no approval).
6. Render the templates in this directory into the repo:

   | Template | Writes to |
   |----------|-----------|
   | `ci.yml.tmpl` | `.github/workflows/ci.yml` |
   | `deploy.yml.tmpl` | `.github/workflows/deploy.yml` |
   | `deploy-environment.yml.tmpl` | `.github/workflows/deploy-environment.yml` |
   | `Dockerfile.dotnet.tmpl` | `Dockerfile`, only if missing and agreed |
   | `github-actions.md.tmpl` | `docs/github-actions.md` |

   Rendering rules:
   - `{{dotnet_setup}}`: `global-json-file: global.json` if the file exists, else `dotnet-version: '<major>.0.x'`, indented 10 spaces.
   - `{{check_steps}}`: one step per check command, named for what it does, for example `- name: Format check` then `run: dotnet format --verify-no-changes`, indented 6 spaces. Keep the order build, format, test.
   - `{{image_name}}`: `<prefix>-<service>`. `{{dockerfile}}`: the Dockerfile path.
   - `{{ingress}}` is for web only: `targetPort: 8080` (the port the app listens on) and `ingress: external`, each indented 10 spaces. For worker leave it out entirely, a worker has no ingress.
   - `{{app_env}}` and `{{env_vars}}`: put each secret or variable setting in an `env:` block on the deploy step (8 spaces) as `NAME: ${{ secrets.NAME }}` or `${{ vars.NAME }}`, and build `environmentVariables: |` as one line of space separated `Key=$NAME` or `Key=literal` pairs (10 spaces). With no secret or variable settings still emit `environmentVariables` for the literals. Values with spaces are not supported by the action. A literal that differs per environment is an expression, for example `${{ inputs.environment == 'prod' && 'Production' || 'Staging' }}`, so there is still one workflow file.
   - Both `{{...}}` blocks above keep the trailing newline so the YAML lines stay separate.
   - In `github-actions.md`, fill the tables from the same data. `{{secret_rows}}` lists the four fixed names and every app setting.
7. Validate: parse each workflow as YAML (`python3 -c "import yaml,sys; yaml.safe_load(open(sys.argv[1]))" <file>`), and run `actionlint` if it is installed. Check that every `secrets.` and `vars.` name in the workflows is in `docs/github-actions.md`. Report failures with their output.
8. Report what was written, the deploy targets, and the next steps: run `/gha:secrets`, then open a PR to see it deploy to UAT. Warn that merging deploys straight to prod with no approval. Mention what is a placeholder or assumption (port, `Staging` name, build once per environment) and any repo docs that describe a different flow.

## Re-run: add, change or remove app settings

Use this when the pipeline exists and the app gains a setting (a database connection, a storage account, an AI endpoint). The workflows are one set of files for both environments, so a setting is added once in the workflow and its value is then set on both `uat` and `prod`.

1. Read the current settings from `deploy-environment.yml`: the `env:` block on the deploy step (secrets and variables) and the pairs in `environmentVariables`. Show them as a table of config key, name, secret, variable or literal.
2. Ask what to add, change or remove, in the same `ConfigKey=NAME` form as the first run, and whether each new name is a secret or a variable. Offer likely names from new infra files (`pgsql.tf`, `blob-storage*.tf`, `foundry.tf`) and from `appsettings.json` keys not yet mapped.
3. **Confirm** the change, then edit only those two places in `deploy-environment.yml`, keeping everything else byte for byte. Do not re-render the other files, and do not touch a customised `ci.yml`, `deploy.yml` or `Dockerfile`.
4. Update `docs/github-actions.md`: its secrets table gets the new rows, and removed names go. Run the validation in step 7 above.
5. Finish by offering to run `/gha:secrets`, which finds the new names as missing on both environments and sets them. For a removed name, say that the old secret or variable is still on GitHub and must be deleted by the person, because the skills never delete them.

## Notes

- Each environment builds and pushes its own image to its own registry. The tag is the short SHA. A prod image is built from the merge commit, which differs from the PR head that UAT ran, so UAT tested the branch and not the exact merge result.
- Prod is deployed by the merge itself. Branch protection on `main` (required review and checks) is what makes that safe, and it is a repo setting this skill does not change, so mention it in the report.
- To support a stack other than .NET, add a new set of detection rules and a Dockerfile template. The deploy workflows are stack independent.
