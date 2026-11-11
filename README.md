# Skills

Carl Paton's Claude Code skills, grouped into plugins and published through one marketplace, `carlpaton`.

| Plugin | What it is for | Docs |
|--------|----------------|------|
| `sdlc` | An AI-first software development lifecycle: setup, plan, design, build, test, deploy, maintain | [plugins/sdlc](plugins/sdlc/README.md) |
| `infra` | Scaffolding Azure Terraform for a container web app or console worker, with optional add-ons | [plugins/infra](plugins/infra/README.md) |
| `azdebug` | Read-only debugging of Azure services in any tenant with the Azure CLI, starting with Foundry model deployments | [plugins/azdebug](plugins/azdebug/README.md) |
| `gha` | GitHub Actions for a container web app or console worker: a PR deploys to UAT, a merge to `main` deploys to prod | [plugins/gha](plugins/gha/README.md) |

## Installation

In Claude Code (2.1.275 or later):

```
/plugin install <plugin> --marketplace carlpaton/skills
```

Or in two steps, on any version:

```
claude plugin marketplace add carlpaton/skills
claude plugin install <plugin>@carlpaton
```

Update with `claude plugin update <plugin>@carlpaton`. Skills are namespaced by plugin, for example `/infra:tf-web` or `/gha:deploy`.

## Layout

```
.claude-plugin/marketplace.json   lists every plugin
plugins/<name>/
  .claude-plugin/plugin.json      name and version, bumped per plugin
  README.md
  skills/<skill>/SKILL.md
  skills/_shared/                 files used by several skills in that plugin
docs/release.md                   how to release a plugin
.github/ISSUE_TEMPLATE/           issue forms the sdlc skills expect
```

## Adding a group of skills

1. Create `plugins/<name>/.claude-plugin/plugin.json` (copy another and change `name`, `description`, `keywords`) and `plugins/<name>/skills/<skill>/SKILL.md`.
2. Add an entry to `.claude-plugin/marketplace.json` with `"source": "./plugins/<name>"`.
3. Add a row to the table above and a `README.md` in the plugin.
4. Run `claude plugin validate plugins/<name>`, then release it as in [docs/release.md](docs/release.md).

Each plugin is versioned and installed on its own, and its skills cannot read another plugin's files, so share nothing across plugins.
