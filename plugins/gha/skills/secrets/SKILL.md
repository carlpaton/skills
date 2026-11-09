---
name: secrets
description: Set the repository secrets and variables that the workflows from deploy use, once per environment with a UAT_ or PROD_ prefix (no GitHub Environments, so it works on a private repo on a free plan). Reads the list from the workflows, fills values from read-only Azure lookups or the person's own terminal, and never shows a secret. Use after deploy, or when a secret or variable is missing or has been rotated.
argument-hint: [env]
---

# GitHub Actions: secrets and variables

Make the repo ready to run the workflows. Follow [../_shared/github-actions.md](../_shared/github-actions.md), especially its Rules: a secret value must never appear in a file, in chat, or in a command argument.

The values are repository secrets and variables, not GitHub Environments. Each name is set once per environment with a prefix: `UAT_<NAME>` and `PROD_<NAME>`. Never create environments.

## Steps

1. Check `gh auth status` and find the repo with `gh repo view --json nameWithOwner`. Stop with a clear message if `gh` is missing or not logged in. The `az` CLI is only needed for the lookups in step 4.
2. Build the list from the workflows in `.github/workflows/`: every `NAME` in `secrets[format('{0}_NAME', ...)]` and `vars[format('{0}_NAME', ...)]`. A setting added later by a `/gha:deploy` re-run is picked up here, as missing. Compare it to `docs/github-actions.md` and flag any difference. For each environment (the argument, else `uat` and `prod`, with prefix `UAT` or `PROD`), read what is already set with `gh secret list` and `gh variable list`. Show a table of prefixed name, kind and set or missing. Do not overwrite a name that is set unless the person says it is being rotated.
3. **Confirm** the plan. If `gh secret list` or `gh variable list` fails with 404 or 403, the person's account cannot manage secrets here. On a personal account's repo only the owner can, and collaborators cannot, whatever their role. Do not retry. Tell the person to ask the owner to do it, or to sign in as the owner (for example `gh auth login`), and give them the table of names to set in the repo's Settings, Secrets and variables, Actions page.
4. Fill the missing values, per name, always with the prefix:
   - **Variables** are not secret, so set them directly: `gh variable set UAT_ACR_SERVER --body <registry>.azurecr.io`. Look up the registry with `az acr show` when logged in, else derive it.
   - **ACR credentials** can be read from Azure without changing it, and piped straight in:

     ```
     az acr credential show -n <registry> --query username -o tsv | gh secret set UAT_ACR_USERNAME
     az acr credential show -n <registry> --query "passwords[0].value" -o tsv | gh secret set UAT_ACR_PASSWORD
     ```

     Use the same pipe form so the value never prints. Ask before running these, as they write a secret to GitHub.
   - **`AZURE_CREDENTIALS`** needs a service principal, which creates something in Azure. Do not run it. Give the person this command to run themselves, once per environment, which pipes the JSON straight into the secret:

     ```
     az ad sp create-for-rbac --name <prefix>-<service>-<env>-github --role contributor \
       --scopes /subscriptions/<subscription-id>/resourceGroups/<prefix>-<service>-<env>-rg \
       --sdk-auth | gh secret set UAT_AZURE_CREDENTIALS --repo <owner>/<repo>
     ```

     Use the subscription id the person gives or `az account show`, and scope it to the resource group only. For prod the secret is `PROD_AZURE_CREDENTIALS`.
   - **App settings** (connection strings, keys): ask where each comes from. If it comes from Azure and the lookup is read-only, offer the pipe form. Otherwise tell the person to run `gh secret set UAT_<NAME> --repo <owner>/<repo>`, which prompts for the value. Never ask them to paste a secret into the chat.
5. Re-list what is set and report: what was set, what the person still has to do themselves, and anything flagged. Remind them that a PR now deploys to UAT and a merge to prod, that the prod secrets are repository level so any workflow in the repo can read them, and that branch protection on `main` is the gate.

## Notes

- Rotating a value is the same command again, with the person's say-so.
- This skill never deletes secrets or service principals, and never creates GitHub Environments.
