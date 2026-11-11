# Azdebug

Claude Code skills that debug Azure services from the outside, using only the Azure CLI. They are read-only and need no Terraform, so they work in any client's tenant, including tenants that have a web app or worker but no Foundry.

## Installation

```
claude plugin marketplace add carlpaton/skills
claude plugin install azdebug@carlpaton
```

Skills are then `/azdebug:foundry` and so on.

## Skills

| Skill | Use it to |
|-------|-----------|
| `/foundry [tenant] [account] [window]` | Debug failing or slow Foundry / Azure OpenAI deployments: status codes, when failures happened, token usage, quota |
| `/blobs [tenant] [account] [container] [prefix] [pull\|show]` | Find files in a storage account and pull them to local disk, or read them into context as a structure summary or capped excerpt |

Planned: Log Analytics queries for web apps and workers (Container Apps console and system logs), and more as they come up.

## Using it

1. Sign in to the client's tenant: `az login --tenant <tenant-id>`.
2. Run `/azdebug:foundry`. It states the tenant and subscription it found and checks they are right, then finds the account, so you do not need to know resource names.

## Output

A structured report, always in the same order, with tables: deployments, status codes (with the share per deployment), failures over time, usage, then findings with evidence and confidence, and recommendations. Gaps in the data, such as no request logs, are reported as findings.

## Safety

Only `list`, `show`, metrics, log queries and blob list and download. Blob access uses your own login first. The account key is used only if you agree, and is never printed. The skills never create, change or delete anything in Azure, including diagnostic settings, which they recommend rather than create. They do not print prompt or response bodies from logs.

## Layout

Shared rules, the metrics helper and the blob helper (`blobs.py`) are in [skills/_shared](skills/_shared). Each skill has its own `SKILL.md`. The report every skill must fill in is a template next to it, for Foundry [skills/foundry/report.md.tmpl](skills/foundry/report.md.tmpl).
