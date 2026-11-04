# AGENTS.md

<!-- Keep this entry point short. Shared contribution rules belong in
CONTRIBUTING.md; add reminders here only for recurring agent mistakes. -->

Follow [CONTRIBUTING.md](CONTRIBUTING.md). Read the sections relevant to the task:

- [Development setup](CONTRIBUTING.md#development-setup) when setting up or
  switching checkouts.
- [Code organization](CONTRIBUTING.md#code-organization) before choosing where
  to implement a change.
- [Validation](CONTRIBUTING.md#validation) and
  [Changelog and versioning](CONTRIBUTING.md#changelog-and-versioning) before
  handing off a change.
- [Writing and review](CONTRIBUTING.md#writing-and-review) when preparing or
  reviewing a contribution.

For generator changes, also read [codegen/README.md](codegen/README.md).
For protocol, codec, or serde changes, also read the
[protocol-test guide](codegen/protocol-test/README.md).

Remember that `make test-py` does not run protocol tests. Report the checks
actually run, including failures, skipped checks, and blockers.
