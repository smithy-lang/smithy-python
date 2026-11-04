# AGENTS.md

<!-- Keep this file short. Shared procedures and explanations belong in
CONTRIBUTING.md; add reminders here only for recurring, costly agent mistakes. -->

[CONTRIBUTING.md](CONTRIBUTING.md) holds this repository's contribution rules.
Before you implement a change, read the sections that apply to it:

- [Development setup](CONTRIBUTING.md#development-setup) when setting up or
  switching checkouts.
- [Code organization](CONTRIBUTING.md#code-organization) before choosing where
  a change belongs.
- [Validation](CONTRIBUTING.md#validation) to choose the checks for the change.
- [Changelog and versioning](CONTRIBUTING.md#changelog-and-versioning) for
  changes under `packages/` or to generated code.
- [Writing and review](CONTRIBUTING.md#writing-and-review) before writing
  commits or reviewing a change.

For Java generator changes, also read [codegen/README.md](codegen/README.md).
For protocol, codec, or serde changes, also read the
[protocol-test guide](codegen/protocol-test/README.md).

## Reminders

- Change the package or generator that owns the behavior. The Java generator in
  `codegen/` generates service clients. The native generator in
  `packages/smithy-python` generates standalone types only, and must not depend
  on Java or Gradle.
- Avoid unnecessary third-party dependencies. Generated clients must depend
  only on the runtime packages their model, traits, and protocol need. See
  [Dependencies](CONTRIBUTING.md#dependencies).
- Do not hand-edit `codegen-output/`, `codegen-output-py/`, or
  `scripts/api-snapshot/api.json`. Regenerate them with their `make` targets
  and review the diff.
- `make test-py` and `make test-unit` do not run protocol tests. After a Java
  generator change, run `make generate-protocol-tests` before
  `make typecheck-protocols` and `make test-protocols`, which check whatever is
  currently in `codegen-output/`.
- Snapshot targets fail when their output changes. If the change is intended,
  follow [the snapshot update steps](CONTRIBUTING.md#generated-output-and-snapshots)
  so the remaining checks still run.
- Add one changelog fragment per affected package for each user-visible change
  under `packages/`. When generated clients change, also bump the generator
  version in `codegen/build.gradle.kts`.
- In your handoff, report only the checks you actually ran and their results.
  Name any checks that failed, were skipped, or could not run, and why.
- When asked only to review, report findings. Do not edit files, commit, push,
  or post comments unless asked.
- When asked to draft a PR description, explain why the change is needed and
  what reviewers should focus on. Leave out test results and Testing sections;
  CI already shows the checks.
