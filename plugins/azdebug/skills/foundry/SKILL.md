---
name: foundry
description: Debug failing or slow Azure AI Foundry / Azure OpenAI model deployments (chat or embeddings) in any tenant, using only the Azure CLI. Finds the account, checks whether request logs exist, and reports status codes, failure timing, token usage and quota as a structured report with tables. Read-only; needs no Terraform. Use when model calls return 408, 429, 5xx or are intermittently failing.
argument-hint: [tenant-id] [account-name] [window e.g. 24h or 7d]
---

# Debug Foundry model deployments

Investigates an Azure OpenAI or AI Services account from the outside with `az`. It works the same in every tenant, so do not rely on a Terraform folder or on names from a repo. Follow [../_shared/azure-debug.md](../_shared/azure-debug.md) for sign-in, safety and how to separate facts from guesses.

## Inputs

| Input | Notes |
|-------|-------|
| tenant | Optional. If the signed-in tenant is not the one wanted, the user runs `az login --tenant <id>`. |
| account | Optional account name. Otherwise list candidates and ask. |
| window | Look-back period, default `7d`. Use `24h` with `PT1H` for a recent incident. |

## Steps

1. **Context.** Follow the shared doc: `az account show`, state the tenant and subscription, and confirm they are right before querying. Never log in or switch subscription for the user without being asked.
2. **Find the account.**

   ```
   az cognitiveservices account list --query "[?kind=='OpenAI' || kind=='AIServices'].{name:name, rg:resourceGroup, kind:kind, loc:location, id:id}" -o table
   ```

   None found: say there is no Foundry here and stop. Several: ask which one. Keep the account `id` for the later steps.
3. **Deployments.**

   ```
   az cognitiveservices account deployment list -g <rg> -n <account> --query "[].{name:name, model:properties.model.name, ver:properties.model.version, sku:sku.name, cap:sku.capacity, state:properties.provisioningState}" -o table
   ```

   Capacity is in thousands of tokens per minute, so `50` means 50K TPM. A state other than `Succeeded` is a finding on its own.
4. **Are request logs collected?**

   ```
   az monitor diagnostic-settings list --resource <id> -o json
   ```

   - **Empty:** there are no request logs. Say so in the report and continue with metrics. Do not create a setting; offer it as a recommendation (see Recommendations).
   - **Has a Log Analytics workspace:** note its `workspaceId` and go to step 6 as well.
5. **Metrics (always available).** Run the helper with `python3 -I ../_shared/metrics.py`, from this skill's folder or with the full path:

   | Question | Command arguments |
   |----------|-------------------|
   | Status codes per deployment | `--metric AzureOpenAIRequests --split ModelDeploymentName StatusCode --interval P1D` |
   | When the failures happened | the same, with `--interval PT1H --exclude StatusCode=200` |
   | Token volume | `--metric ProcessedPromptTokens` and `--metric GeneratedTokens`, `--split ModelDeploymentName`, `--interval PT1H`, `--aggregation Total Maximum` |
   | Speed | `--metric AzureOpenAITokenPerSecond --split ModelDeploymentName --aggregation Average Maximum` |

   Other metrics vary by model and region, so list them with `az monitor metrics list-definitions --resource <id> --query "[].name.value" -o tsv` rather than assuming. If a metric returns no data, say so and do not infer a value for it.
6. **Request logs, when a workspace exists.** Needs the extension: `az extension add -n log-analytics` (ask first if it is missing). Look up the workspace guid, then query. Newly enabled logs take a few minutes to appear and hold nothing from before they were turned on.

   ```
   az monitor log-analytics workspace show --ids <workspace-resource-id> --query customerId -o tsv
   az monitor log-analytics query -w <customerId> --analytics-query "<KQL>" -o table
   ```

   Start with failures by hour. The table depends on the destination mode, so try `AzureDiagnostics` first and the resource-specific tables if it is empty:

   ```
   AzureDiagnostics
   | where ResourceProvider == "MICROSOFT.COGNITIVESERVICES" and TimeGenerated > ago(7d)
   | where Category == "RequestResponse" and httpStatusCode_s != "200"
   | summarize count() by bin(TimeGenerated, 1h), httpStatusCode_s, OperationName
   | order by TimeGenerated asc
   ```

   Look at `DurationMs_s`, `properties_s` and the caller address for the failing rows. Never print prompt or response bodies. Summarise them.
7. **Quota, if 429s appear.**

   ```
   az cognitiveservices usage list -l <location> --query "[?contains(name.value,'OpenAI')].{name:name.value, used:currentValue, limit:limit}" -o table
   ```

8. **Report.** Fill in [report.md.tmpl](report.md.tmpl) and give the result to the user as the whole answer. See the rules below.

## Report rules

The template is mandatory. Do not reorder, rename, merge or drop sections, and do not add prose outside it.

- Replace every `{{placeholder}}` and delete the `<!-- ... -->` hints. Leave no placeholder behind.
- Keep every table even when it has no data. Give one row of `none` (or `n/a` in each cell) rather than removing the table.
- Table rows are one per line, filled from the helper output. Do not round counts. Percentages have one decimal place.
- A section the data could not fill, such as request durations without logs, is listed under **Not visible**, not skipped.
- Add extra detail as more rows or more findings, not as new sections. If a new section is truly needed, it goes after Recommendations under the heading `### Appendix`.
- **Findings** are what the data shows. Evidence names the table and row it came from. Confidence is `high` for a direct measurement, `medium` for a pattern that fits, `low` for a hypothesis. Always say what could not be seen, for example "no request logs, so error bodies and durations are unknown".
- **Share of deployment** is the status count divided by that deployment's total, as a percentage, so a 5% timeout rate is visible at a glance.
- Meanings to use: `408` request timeout (long generations or reasoning, or a client timeout), `429` throttled for tokens or requests per minute, `400` bad request or content filter, `401`/`403` credentials or network rules, `500`/`503` service side, retry with backoff.

## Recommendations to offer, not do

- No diagnostic setting: enable `RequestResponse`, `AzureOpenAIRequestUsage` and `Audit` to a Log Analytics workspace. If the user manages the account with Terraform, offer the `azurerm_monitor_diagnostic_setting` resource. Creating it changes Azure, so only do it when asked and confirm the target first.
- `408` on a reasoning model: compare the client timeout with generation time, and consider a lower reasoning effort or streaming.
- `429`: raise capacity if quota allows, add retry with backoff, or spread load across deployments.

## Notes

- Everything here is read-only. Use only `list`, `show`, `metrics`, `log-analytics query` and `usage list`.
- Metric buckets are in UTC. Say so when giving times to the user.
