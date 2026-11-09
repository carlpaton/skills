# Step 0: Setup

Runs once per project, before the loop of [Plan](../plan/README.md) onwards, and again when the foundational decisions change. It records how the code will be built so every later step works from written decisions instead of guesses.

## Use

Run `/setup`, optionally with a profile name (for example `/setup dotnet`). The skill:

1. Detects the mode: **greenfield** if there is no source code, **existing** if there is.
2. Loads a profile, or asks which fits.
3. Greenfield: interviews you topic by topic (architecture, testing, conventions), offering the profile's default for each.
4. Existing: has a subagent survey the code base, then confirms what it found with you. It documents what exists and does not flag gaps unless you ask.
5. Writes the outputs below, shows them, and waits for your yes before committing.

It decides and records. It does not scaffold code.

## Outputs

| File | Holds |
|------|-------|
| `docs/conventions/architecture.md` | Architecture style, structure, and what each part is responsible for |
| `docs/conventions/testing.md` | What tests look like, where they live, how to run all and one |
| `docs/conventions/deployment.md` | Environments and order, how a release is made, approvals, pre-flight, post-deploy checks, rollback |
| `docs/conventions/operations.md` | What is monitored, normal and thresholds, severity tiers, triage owner, read and change limits on live systems |
| `docs/conventions/<other>.md` | Other topics the profile covers |
| `docs/decisions/NNNN-<slug>.md` | A short record of each significant choice and why |
| `CLAUDE.md` | Imports the conventions and lists the build, lint and test commands |

Later steps read these: Design is constrained by the architecture, and Build and Test follow the testing conventions.

## Profiles

A profile in [profiles/](profiles/) holds the questions and default conventions for one stack, so the steps stay stack-agnostic. Adding a stack means adding a profile.

- [dotnet.md](profiles/dotnet.md): .NET (C#), with the test framework as a question (xUnit by default)
- [infra.md](profiles/infra.md): infrastructure as code (Terraform) and SQL scripts. There is no test suite, so verification (format, validate, plan review, SQL against a throwaway database) takes its place.

## Later

Not in v1. Conventions that must always hold should be enforced rather than only written down: architecture tests for layering, hooks for formatting and tests. Each profile lists ideas under "Enforcement ideas". Scaffolding a solution, and applying the template to a project (GitHub labels, forms, board), are also left for later.

## Files

- [SKILL.md](SKILL.md): the skill's instructions for Claude
- [profiles/](profiles/): stack profiles
