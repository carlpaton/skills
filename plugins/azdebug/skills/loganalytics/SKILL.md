---
name: loganalytics
description: Query Azure Log Analytics with the Azure CLI to debug a web app or worker running on Container Apps (console logs, failed requests, exceptions, restarts and scaling events), and Foundry request logs once diagnostic settings send them there. Finds the workspace, runs canned or custom read-only KQL, and reports counts and timings without printing raw message bodies. Use when the user wants to see what an app logged, why requests failed, or when failures happened.
argument-hint: [tenant-id] [workspace] [window e.g. 24h or 7d] [preset | KQL]
---

# Query Log Analytics

Reads logs from a Log Analytics workspace from the outside with `az`. It works the same in every tenant. Follow [../_shared/azure-debug.md](../_shared/azure-debug.md) for sign-in, safety and facts versus guesses. All steps use the helper [../_shared/loganalytics.py](../_shared/loganalytics.py), run as `python3 -I ../_shared/loganalytics.py` from this skill's folder or with the full path.

## Inputs

| Input | Notes |
|-------|-------|
| tenant | Optional. If the signed-in tenant is not the one wanted, the user runs `az login --tenant <id>`. |
| workspace | Workspace name or id. If unknown, list them (step 2). |
| window | Look-back period, default `7d`. Use `24h` for a recent incident. |
| what to look at | A preset name, or a question to turn into KQL. If the user did not say, start with `tables` then `console-levels`. |

## Steps

1. **Context.** Follow the shared doc: `az account show`, state the tenant and subscription and confirm they are right. Never log in or switch subscription unasked.
2. **Find the workspace.**

   ```
   python3 -I loganalytics.py workspaces
   ```

   Several are normal: a web app and a worker each have one per environment, for example `chatbot-web-prodanz` and `chatbot-worker-prodanz`. Match the environment and the role to what the user is investigating, or ask. Use the `workspaceId` GUID, not the name. If none fit, say so and stop.
3. **See what has data.**

   ```
   python3 -I loganalytics.py run --workspace <guid> --preset tables --window 7d
   ```

   Report the tables with rows, and the oldest and newest time. The oldest time is the real limit of the investigation: retention is 30 days here and a new workspace may hold only a few days. An empty workspace or a missing table is a finding, so say so.
4. **Run presets.** List them with `python3 -I loganalytics.py presets`.

   | Preset | Answers |
   |--------|---------|
   | `console-levels` | How many info, warn and fail lines, and from which logger |
   | `app-failures` | When each `fail:` line happened, and its logger |
   | `exceptions` | The exception type and first line, counted. This is usually the cause. |
   | `failures-by-hour` | When failures cluster |
   | `system-events` | Platform events: scaling, revisions, warnings |
   | `restarts` | Revision and replica lifecycle in time order |

   ```
   python3 -I loganalytics.py run --workspace <guid> --preset exceptions --window 7d
   ```

5. **Custom KQL** when no preset fits.

   ```
   python3 -I loganalytics.py query --workspace <guid> --kql "<KQL>" [--max-rows 50] [--width 160]
   ```

   Read-only only: control commands starting with `.` are refused. Always bound by time, for example `where TimeGenerated > ago(24h)`. Avoid these KQL words as column names, because they cause parse errors: `time`, `first`, `last`, `count` unquoted in some positions. Use `at`, `oldest`, `newest` instead.
6. **Report.** Fill in [report.md.tmpl](report.md.tmpl) and give the result to the user as the whole answer. Run `tables`, `console-levels`, `failures-by-hour`, `exceptions` and `system-events` first, because each fills one table. See the rules below.

## Report rules

The template is mandatory. Do not reorder, rename, merge or drop sections, and do not add prose outside it.

- Replace every `{{placeholder}}` and delete the `<!-- ... -->` hints. Leave no placeholder behind.
- Keep every table even when it has no data. Give one row of `none` (or `n/a` in each cell) rather than removing the table.
- Table rows are one per line, taken from the helper output with the columns in the template's order. Do not round counts. Times are UTC.
- Map the presets to tables: `tables` to Tables with data, `console-levels` to Console log levels, `failures-by-hour` to Failures over time, `exceptions` to Causes, `system-events` to Platform events.
- A section the data could not fill, such as request durations, is listed under **Not visible**, not skipped. Console logs usually do not record successful requests, so they cannot give a success rate. Say so.
- Add extra detail as more rows or more findings, not as new sections. If a new section is truly needed, it goes after Recommendations under the heading `### Appendix`. Output from custom KQL goes there.
- **Findings** are what the data shows. Evidence names the table and row it came from. Confidence is `high` for a direct measurement, `medium` for a pattern that fits, `low` for a hypothesis. A match with another source, such as app traces, goes in the evidence.
- Do not print message bodies, only counts, times, loggers and exception headers.

## Reading ASP.NET console logs

Container Apps console logs land in `ContainerAppConsoleLogs_CL`, one row per line, with the message in `Log_s`. .NET writes a header line such as `fail: Namespace.Class[0]` and then the message and stack trace on following lines, which are separate rows. The presets use the header lines and exception lines, so they find failures without printing message bodies.

- Rows from one request are not linked by an id. Join by time: a `fail:` line is written when the request ends, so it falls at the request's start time plus its duration.
- If the app has a trace store (for example debug traces in blobs), match the failure times against it. See `/azdebug:blobs`.

## Foundry request logs

When a Foundry account has a diagnostic setting sending `RequestResponse`, `AzureOpenAIRequestUsage` and `Audit` to a workspace, those arrive in `AzureDiagnostics` or in resource-specific tables, depending on the setting's destination type. Run `tables` first and look at what is there before writing KQL, and use `query` for it. Canned Foundry presets are not included yet because they need real data to test against. Add them to the helper once the logs exist.

## Privacy and limits

- Do not print log message bodies, prompts, responses, tokens or connection strings. Count and summarise. The presets already follow this. In custom queries, project only the columns you need and truncate with `substring`.
- Rows shown are capped by `--max-rows`, and cells by `--width`. Say when output was truncated.
- The first use may make `az` install the preview `log-analytics` extension. Tell the user if that happens.
- Needs the `Log Analytics Reader` role on the workspace. If access is refused, ask the user to grant it. Do not try another route.
