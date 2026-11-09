# Profile: .NET

Questions to ask and defaults to offer when setting up a .NET (C#) project. Offer the default, record the user's choice.

## Architecture

Ask:

1. **Deployment style.** Single deployable (monolith), modular monolith, or microservices? If microservices, how do services communicate (HTTP, messaging) and where does each one's data live?
2. **Domain-driven design.** Is DDD used? If so, what are the bounded contexts, and are aggregates and domain events in use?
3. **Layering.** How is each deployable structured, and which direction may dependencies point? Offer the alternatives (single project with folders, vertical slices) and record the one chosen and why, with its trade-off.

Defaults:

- Modular monolith until a service boundary is justified.
- Layers `Domain`, `Application`, `Infrastructure` and a host project (`Api` or `Web`). Dependencies point inward: `Domain` references nothing, `Application` references `Domain`, `Infrastructure` references `Application`.
- One solution, one project per layer, a `.Tests` project per layer under test.
- This layering is Clean Architecture (close to Onion). Name it in the architecture convention. The trade-off is more projects and ceremony in return for compiler-enforced boundaries and easy unit testing, which is heavy for a small app.
- Layer responsibilities to record:
  - `Domain`: business types and rules. References nothing.
  - `Application`: use cases. Defines the interfaces it needs (ports), such as repositories or email.
  - `Infrastructure`: implements those interfaces (database, external APIs). This is how dependencies point inward.
  - Host (`Api` or `Web`): HTTP and UI, and the dependency-injection wiring. It may reference `Infrastructure` only as the composition root.
- Add a "where does new code go?" rule of thumb: business rule to `Domain`, use case or new port to `Application`, port implementation to `Infrastructure`, endpoint, page or view to the host.

## Testing

Ask:

1. **Test framework.** xUnit, NUnit or MSTest?
2. **Test levels.** Which exist: unit, integration, end-to-end?
3. **Integration tests.** Real dependencies (such as a database in a container) or fakes?
4. **Naming and layout.** Where do test projects live and how are tests named?
5. **Assertions and mocking.** Which libraries, if any?

Defaults:

- xUnit. Single cases use `[Fact]`, and tables of cases use `[Theory]` with `[InlineData]`. If another framework is chosen, record its equivalents (`[Test]` and `[TestCase]` for NUnit, `[TestMethod]` and `[DataRow]` for MSTest).
- Test projects named `<Project>.Tests`, mirroring the namespace of the code under test.
- Test names read `Method_Scenario_ExpectedResult`.
- Arrange, act, assert, with one behaviour per test.
- Domain and application logic covered by fast unit tests with no I/O. Infrastructure covered by integration tests against real dependencies.
- Run all tests with `dotnet test`. Run one with `dotnet test --filter "FullyQualifiedName~<TestName>"`.

## Conventions

Ask:

1. **Target framework and language version.**
2. **Formatting and analysis.** `.editorconfig`, analyzers, warnings as errors?
3. **Branching and CI.** Branch naming, PR rules, what CI runs.

Defaults:

- Latest LTS .NET, nullable reference types enabled.
- `dotnet format` for formatting, with the rules in `.editorconfig`.
- CI runs build, format check and tests on every PR.

## Deployment

Record in `docs/conventions/deployment.md`. Ask:

1. **Environments.** Which exist and in what order does a release move through them?
2. **Route.** Does a pipeline deploy, or does a person? What triggers it?
3. **Approval.** Who approves each environment, and how is production gated?
4. **Pre-flight.** What must be true before a release: green checks, migrations ready, configuration and secrets in place?
5. **Post-deploy checks.** How is a release confirmed healthy (health endpoint, smoke test, logs)?
6. **Rollback.** How is a bad release undone, and which changes (such as database migrations) cannot be reversed?
7. **Versioning and changelog.** How is a release numbered and described?

Defaults:

- Deploy to a pre-production environment first and confirm it before production.
- Production requires a named human approval enforced by the pipeline, not only by convention.
- Rollback means redeploying the previous version. Database changes are written to be backward compatible with it.
- Each release has a health check and a smoke test, and the release record keeps their output.

## Operations

Record in `docs/conventions/operations.md`. Ask:

1. **Observability.** Where do logs, metrics and traces go, and who can read them?
2. **Normal and thresholds.** What does healthy look like (error rate, latency, queue depth, resource use), and which values should raise an alert?
3. **Severity tiers.** How are issues graded, and what response does each tier need?
4. **Ownership.** Who triages, who is on call, and how are they reached?
5. **Live-system access.** What may be read, and what may never be changed without going through a release?
6. **Scheduled checks.** Which run on a schedule: dependency and security scans, health checks, backup restores?

Defaults:

- Structured logs with a correlation id, health endpoints, and alerts on error rate and latency.
- Three tiers: service down or data loss, degraded, and minor. The first needs an immediate response.
- Read access to logs and metrics is open to the team. Changes to a live system go through a release.
- A scheduled dependency and security scan, with findings raised as issues.

## Enforcement ideas

Not applied by `/setup` in v1. Note them in the conventions so they can be added later:

- Architecture tests (for example with NetArchTest) that fail the build when a layer references one it should not.
- A hook that runs `dotnet format` after edits.
- A hook or CI check that blocks changes to test files during a fix task.
