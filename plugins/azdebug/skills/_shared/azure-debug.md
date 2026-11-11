# Shared rules for azdebug skills

These apply to every skill in the plugin. They exist so the same skill works in any client's tenant.

## Read-only

Investigate, do not change. Allowed: `az account show|list`, `az ... list|show`, `az monitor metrics list`, `az monitor metrics list-definitions`, `az monitor diagnostic-settings list`, `az monitor log-analytics query`. Not allowed without an explicit request and a confirmation of the target: anything that creates, updates, deletes, restarts, scales or logs in or out.

## Tenant and subscription

1. Run `az account show --query "{name:name, id:id, tenant:tenantId, user:user.name}" -o json`.
2. If it fails, nobody is signed in. Ask the user to run `az login --tenant <id>` (it opens a browser, so they may prefer `! az login --tenant <id>` in the prompt). Do not guess a tenant.
3. Tell the user which tenant and subscription you are about to query, and check it is the right client before running anything else. The default subscription after login is often not the one wanted, so list with `az account list -o table` if there is any doubt.
4. Switching is the user's decision: `az account set --subscription <name-or-id>`.

## Not every tenant has every service

Discover what exists with `list` commands. If the service the skill covers is missing from this subscription, say so and stop rather than hunting through other subscriptions. Web apps and workers often have Log Analytics and a Container App but no Foundry.

## Facts and guesses

Report what the data shows, then label hypotheses as hypotheses. If a metric or log is empty or unavailable, say so. A gap in data is a finding, not something to fill in. Do not claim a root cause that no log confirms.

## Privacy

Do not print prompts, responses, keys, connection strings or tokens from logs. Summarise instead. Do not put the user's email or client names into any request outside Azure.

## Helper

[metrics.py](metrics.py) wraps `az monitor metrics list` and prints non-empty buckets as a table. Run it with `python3 -I`.
