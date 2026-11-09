---
name: release
description: Release a plugin in this repo (sdlc, infra or gha). Bump the version, update the changelog, validate, commit, push, create the GitHub release, then update the locally installed plugin. Use when plugin changes are ready to ship, or to get the latest installed version after a release. Local to this repo.
argument-hint: <plugin> [patch|minor]
---

# Release a plugin

Follows [docs/release.md](../../../docs/release.md), which is the source of truth for version rules. Each plugin under `plugins/<name>/` is versioned and released on its own.

## Steps

1. **Pick the plugin and bump.** Use `$ARGUMENTS`, or infer the plugin from `git status`. Ask if it is unclear. Choose patch for a fix or wording change, minor for a new skill or a breaking change while on `0.x`. Never reuse or move an existing tag.
2. **Check the tree.** Run `git status`. Only the plugin's changes should be pending. Stop and ask if unrelated changes are mixed in.
3. **Bump the version.** Edit `version` in `plugins/<name>/.claude-plugin/plugin.json`. Do not add a version to `marketplace.json`.
4. **Update the changelog.** Add an entry at the top of `plugins/<name>/CHANGELOG.md` (create it if missing, in the style of `plugins/infra/CHANGELOG.md`), under Fixed, Changed or Added.
5. **Validate.** Run `claude plugin validate plugins/<name>`. Stop on failure.
6. **Commit.** Stage `plugins/<name>`. Message: `Release <name> vX.Y.Z`, a one-line summary, and the attribution line for this session.
7. **Confirm before publishing.** Pushing and releasing are outward-facing. Show the commit and ask for a yes, unless the user already said to go ahead.
8. **Push and release.**

   ```
   git push origin main
   gh release create <name>-vX.Y.Z --title "<name> vX.Y.Z" --generate-notes --prerelease
   ```

   Keep `--prerelease` while the project is on `0.x`. The tag is the plugin name, `-v`, and the version.
9. **Update locally.** So this machine gets the new version:

   ```
   claude plugin marketplace update carlpaton
   claude plugin update <name>@carlpaton
   ```

   Confirm the output says the plugin was updated from the old version to the new one. Tell the user to restart Claude Code to apply it.

## Mistakes

- Wrong notes: `gh release edit <name>-vX.Y.Z --notes "..."`.
- Wrong version released: bump the patch and release again. Do not move the tag.
- Release made by accident: `gh release delete <name>-vX.Y.Z --cleanup-tag`, only if nobody has installed it.
