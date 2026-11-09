---
name: secrets
description: Set up the GitHub Environments (uat, prod) and the secrets and variables that the workflows from deploy use. Reads the list from the workflows, fills values from read-only Azure lookups or the person's own terminal, and never shows a secret. Use after deploy, or when a secret or variable is missing or has been rotated.
argument-hint: [env]
---

# GitHub Actions: environments, secrets and variables

Make the repo ready to run the workflows. Follow [../_shared/github-actions.md](../_shared/github-actions.md), especially its Rules: a secret value must never appear in a file, in chat, or in a command argument.

## Steps

1. Check `gh auth status` and find the repo with `gh repo view --json nameWithOwner`. Stop with a clear message if `gh` is missing or not logged in. The `az` CLI is only needed for the lookups in step 4.
2. Build the list from the workflows in `.github/workflows/`: every `secrets.NAME` and `vars.NAME` except `GITHUB_TOKEN`. A setting added later by a `/gha:deploy` re-run is picked up here, as missing on both environments. Compare it to `docs/github-actions.md` and flag any difference. For each environment (the argument, else `uat` and `prod`), read what is already set with `gh secret list --env <env>` and `gh variable list --env <env>`. Show a table of name, kind and set or missing. Do not overwrite a name that is set unless the person says it is being rotated.
3. **Confirm** the plan, then create the environments with `gh api --method PUT repos/<owner>/<repo>/environments/<env>`. Create them plain: no required reviewers, no wait timer and no branch rules, as the pipeline has no approval step and a PR deploys to `uat` from a feature branch.
4. Fill the missing values, per name:
   - **Variables** are not secret, so set them directly: `gh variable set ACR_SERVER --env <env> --body <registry>.azurecr.io`. Look up the registry with `az acr show` when logged in, else derive it.
   - **ACR credentials** can be read from Azure without changing it, and piped straight in:

     ```
     az acr credential show -n <registry> --query username -o tsv | gh secret set ACR_USERNAME --env <env>
     az acr credential show -n <registry> --query "passwords[0].value" -o tsv | gh secret set ACR_PASSWORD --env <env>
     ```

     Use the same pipe form so the value never prints. Ask before running these, as they write a secret to GitHub.
   - **`AZURE_CREDENTIALS`** needs a service principal, which creates something in Azure. Do not run it. Give the person this command to run themselves, once per environment, which pipes the JSON straight into the secret:

     ```
     az ad sp create-for-rbac --name <prefix>-<service>-<env>-github --role contributor \
       --scopes /subscriptions/<subscription-id>/resourceGroups/<prefix>-<service>-<env>-rg \
       --sdk-auth | gh secret set AZURE_CREDENTIALS --env <env> --repo <owner>/<repo>
     ```

     Use the subscription id the person gives or `az account show`, and scope it to the resource group only.
   - **App settings** (connection strings, keys): ask where each comes from. If it comes from Azure and the lookup is read-only, offer the pipe form. Otherwise tell the person to run `gh secret set <NAME> --env <env> --repo <owner>/<repo>`, which prompts for the value. Never ask them to paste a secret into the chat.
5. Re-list what is set and report: what was set, what the person still has to do themselves, and anything flagged. Remind them that a PR now deploys to UAT and a merge deploys to prod, so branch protection on `main` is the gate.

## Notes

- Rotating a value is the same command again, with the person's say-so.
- This skill never deletes secrets, environments or service principals.
