---
name: setup
description: Step 0 of the SDLC, run once per project. Bootstrap the foundations later steps rely on by recording how the code will be built (architecture, testing, conventions) as committed files, for a new or an existing code base. Use when starting a project, adopting the SDLC in a repo, or when those foundational decisions need to change.
argument-hint: [profile]
---

# Setup

Record how this project is built, so every later SDLC step works from written decisions instead of guesses. This skill decides and records. It does not scaffold code.

## Mode

Check whether the repo has source code beyond docs and config.

- No source code: **greenfield mode**.
- Source code present: **existing mode**.
- If `docs/conventions/` already exists, say so and ask whether to revise it or stop.

## Profile

A profile is a markdown file in [profiles/](profiles/) holding the questions to ask and the default conventions for one stack. If `$ARGUMENTS` names one, use it. Otherwise list the available profiles and ask which fits, or whether to build a custom one. Do not assume a stack the user has not chosen.

## Greenfield mode

1. Read the chosen profile.
2. Interview the user through its questions, one topic at a time (architecture, testing, conventions). Offer the profile's default for each, and record the user's choice. Do not decide on the user's behalf.
3. Record each significant choice with its reason (see Outputs).

## Existing mode

1. Use a subagent to survey the code base against the profile's topics (structure, layering, test projects and style, tooling), so the bulk of the reading stays out of this session. Ask it for a summary of what exists, not file dumps.
2. Present what was found, topic by topic. Confirm or correct each with the user. Ask for the reason behind a choice only when it is not evident, and do not invent reasons.
3. Document what exists. Do not flag gaps or propose changes unless the user asks.

## Outputs

Write these in the project, show the user the result, and get a yes before committing.

- `docs/conventions/architecture.md`: the architecture style and structure.
- `docs/conventions/testing.md`: what tests look like, where they live, and how to run all of them and a single one.
- `docs/conventions/deployment.md`: the environments and their order, how a release is made (pipeline or manual), who approves each environment, the pre-flight list, the post-deploy checks, and the rollback. `/deploy` depends on it.
- `docs/conventions/operations.md`: what is monitored and where logs and metrics live, what normal looks like and the thresholds that matter, the severity tiers, who owns triage, and what may be read or changed in a live system. `/maintain` depends on it.
- `docs/conventions/<other>.md`: any further topic the profile covers, such as language, branching or CI.
- `docs/decisions/NNNN-<slug>.md`: a short decision record (context, decision, alternatives considered, consequences including trade-offs) for each significant choice, so it is not reversed without knowing why.
- `CLAUDE.md`: create it, or add to it if it exists. Import the conventions with `@docs/conventions/<file>.md` and list the build, lint and test commands. Keep it short and do not duplicate the conventions.

## Rules

- Do not mention a specific project in this skill or in the profiles. Project detail belongs in the project's own files.
- When a convention names an architecture, name the pattern (so it can be looked up) and state what each part is responsible for, not only how the parts reference each other.
- Record decisions as plain statements others can follow or check. Prefer wording that a test or hook could later enforce.
- Do not create labels, forms, projects or other GitHub setup here.
