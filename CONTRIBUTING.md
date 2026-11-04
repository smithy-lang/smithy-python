# Contributing Guidelines

Thank you for your interest in contributing to Smithy Python. Bug reports,
features, fixes, and documentation improvements are welcome.

This guide contains the shared contribution rules for people and coding agents.
[AGENTS.md](AGENTS.md) directs agents to the sections relevant to their task.

## Reporting bugs and requesting features

Use the GitHub issue tracker to report bugs or suggest features. Check existing
open and recently closed issues first. For a bug report, include:

- A reproducible test case or steps to reproduce the problem.
- The package version and any local modifications.
- Relevant details about your environment or deployment.

Open an issue to discuss significant work before starting it. Existing issues,
especially those labeled `help wanted`, are a good place to find contributions.

## Contributing via pull requests

1. Work against the latest source on `develop`. Check open and recently merged
   pull requests to avoid duplicating work.
2. Fork the repository and follow the [development setup](#development-setup).
3. Keep the change focused. Put unrelated fixes and formatting in separate PRs.
4. Run the applicable [validation](#validation) and add any required
   [changelog entries and version changes](#changelog-and-versioning).
5. Commit with clear messages and open a PR using the repository's
   [PR template](.github/PULL_REQUEST_TEMPLATE.md). Write the description as
   described in [Writing and review](#writing-and-review).
6. Address CI failures and stay involved in the review.

## Development setup

Install [uv](https://docs.astral.sh/uv/), JDK 17 or newer, `make`, and
[pandoc](https://pandoc.org/installing.html). The
[README](README.md#how-do-i-use-this-to-create-a-client) also covers generating
clients with the Smithy CLI.

To build the `smithy-checksums` Rust extension or run the Rust checks,
install [rustup](https://rustup.rs/), which uses the toolchain pinned in
[`rust-toolchain.toml`](rust-toolchain.toml). `make check-rust` also needs
`cargo-deny` and `cargo-about`, at the versions pinned in the
[CI workflow](.github/workflows/ci.yml). See the package's
[build notes](packages/smithy-checksums/README.md#building) for building
without Rust.

From the repository root, and in each new worktree, run:

```sh
make install
source .venv/bin/activate
```

`make install` sets up the uv workspace with all packages and extras, which a
plain `uv sync` does not, and initializes Gradle. Use `uv run` for Python tools.

Use Python 3.12, the default in [`.python-version`](.python-version). CI runs
static analysis and Rust checks on 3.12 only, and runs tests and builds on
every Python version in its matrix. Pyright results can differ on other
versions.

Keep the repository's `.venv` active when running Gradle codegen. The generator
uses `python3` from `PATH` to run ruff and pyright; if either is unavailable, it
skips that check with a warning.

## Code organization

- `packages/`: the Python uv workspace, with the runtime packages and the native
  generator.
- `codegen/`: the Java/Gradle generator, which generates service clients,
  including those in [aws-sdk-python](https://github.com/aws/aws-sdk-python),
  and remains the authoritative implementation. See the
  [codegen guide](codegen/README.md).
- `packages/smithy-python`: the experimental Python-native generator. It
  generates standalone types packages from a Smithy JSON AST model; client
  generation is still under development. It must not depend on Java, Gradle,
  or the Java generator. See its [README](packages/smithy-python/README.md) and
  the [codegen design](designs/codegen/index.md).
- Implement client generation features in the Java generator unless the task
  concerns the native generator, and not in both.
- Committed generated output: `codegen-output/` (Java-generated protocol-test
  clients), `codegen-output-py/` (native types output), and
  `scripts/api-snapshot/api.json` (the public API surface of the workspace
  packages). Do not edit these by hand; regenerate them as described in
  [Generated output and snapshots](#generated-output-and-snapshots).
- `designs/`: design documents.

### Package boundaries

`smithy-core` imports no other workspace package. The generic packages
(`smithy-http`, `smithy-json`, `smithy-xml`, and `smithy-cbor`) must not import
`smithy_aws_*`. AWS-specific runtime logic belongs in the `smithy_aws_*` packages,
except SigV4 signing, which lives in `aws-sdk-signers`.

Keep AWS-specific codegen logic out of `codegen/core`; add it through an
integration in `codegen/aws`. The [AWS codegen guide](codegen/aws/README.md)
explains this separation. Generate service-specific customizations, such as the
API Gateway `Accept` header, into that service's client instead of adding them
to `smithy-aws-core`.

Fix behavior in the package that owns it. Add a public API there instead of
reaching into another package's private attributes. In packages with a
`_private/` directory, keep internals there. Put logic shared by all generated
clients in a runtime package, and do not emit helpers that nothing calls.

### Dependencies

Avoid unnecessary dependencies on third-party packages that we do not own.
Where practical, reuse existing project code or the standard library instead.
This is not a ban: add a third-party dependency when it provides clear value.

A generated client should depend only on the runtime packages that its service
model, the model's traits, and its protocol need. For example, a client should
depend on `smithy-checksums` only if it uses the related checksum traits or
features, and on `smithy-json` only if it uses a JSON-based protocol. Do not
introduce unrelated runtime dependencies transitively through a shared package
or a broad extra.

When you change how dependencies are selected, inspect the generated package
metadata, including transitive dependencies, for a model that needs the feature
and for one that does not.

## Validation

Run commands from the repository root with the development environment active.
`make help` lists all targets, and the [Makefile](Makefile) shows what each
composite target runs. `make ci` runs the main job of the
[CI workflow](.github/workflows/ci.yml) locally on your current Python version,
stops at the first failure, and needs JDK, Rust, `cargo-deny`, and
`cargo-about`. It does not cover the workflow's other jobs, such as the native
wheel builds on other platforms.

### Choosing checks

While developing, run focused tests with
`uv run pytest <path>::<test> --no-cov` (coverage is on by default). Focused
runs do not replace the checks below. Before handing off a change, run the
checks for each area it touches.

| Change | Checks |
| --- | --- |
| Documentation only | No build or test target. Check changed links, and check any changed commands or facts against the source. |
| Python runtime packages | `make check-py`, `make test-unit`, and `make api-snapshot`. Add `make test-functional` for HTTP, protocol, codec, serde, or generated-client behavior, and `make build-py` for packaging changes. |
| Rust extensions | `make check-rust` and `make test-unit`. `make lint-rust` applies formatting and lint fixes; run `make third-party-licenses` after Rust dependency changes. |
| Java generator or Gradle | `make format-java`, `make build-java`, `make generate-protocol-tests`, `make typecheck-protocols`, and `make test-protocols`. |
| Native generator (`packages/smithy-python`) | `make check-py`, `make test-unit`, `make api-snapshot`, and `make generate-codegen-output-py`. |

`make lint-py` applies Python formatting and lint fixes. `make build-java`
includes the Java/Gradle formatting check, which `make check-java` runs alone.
`make test-py` runs pytest on all of `packages/` but is not part of CI. Neither
`make test-py` nor `make test-unit` runs protocol tests.

### Generated output and snapshots

These targets regenerate committed output, then fail if it differs from the
git index:

- `make generate-protocol-tests`: Java-generated protocol-test clients in
  `codegen-output/`.
- `make generate-codegen-output-py`: native generator output in
  `codegen-output-py/`.
- `make api-snapshot`: `scripts/api-snapshot/api.json`.

`make typecheck-protocols` and `make test-protocols` test whatever is in
`codegen-output/` without regenerating it, so after a Java generator change,
run `make generate-protocol-tests` first.

When a snapshot change is intended, the target fails and prints the diff.
Review the diff and include it in the same PR. Composite targets such as
`make test-integration` and `make ci` stop at that failure, so run the
remaining relevant checks, such as `make typecheck-protocols` and
`make test-protocols`, as separate commands. Skip the generation targets when a
change cannot affect generated output.

### Protocol tests and generated clients

For protocol behavior fixes, use the Smithy protocol tests rather than adding
unit tests to `test_protocols.py`. If the upstream test is new, bump `smithy` in
[`codegen/gradle/libs.versions.toml`](codegen/gradle/libs.versions.toml) to pick
it up. See the [protocol-test guide](codegen/protocol-test/README.md) for adding
upstream tests or support for a new protocol.

For codegen changes affecting naming, imports, or type annotations, also generate
clients for real AWS service models and run ruff and pyright on the output.
Protocol-test models alone do not provide enough coverage for these changes.
Start with the models in
[`aws-sdk-python/codegen/aws-models/`](https://github.com/aws/aws-sdk-python/tree/develop/codegen/aws-models).
For wider coverage, use [api-models-aws](https://github.com/aws/api-models-aws).
Keep temporary generated clients and reproduction scripts outside this checkout,
in a temporary directory or a separate worktree.

## Changelog and versioning

Every user-visible change under `packages/` needs one changelog fragment per
affected package. Create each fragment with:

```sh
uv run python scripts/changelog/new-entry.py -p <package> -t <type> -d "..."
```

Choose from `feature`, `enhancement`, `bugfix`, `breaking`, or `dependency`.
Use `breaking` when removing or changing public API. Write the description as
one past-tense, customer-facing sentence.

The fragment type controls the version bump: `feature` and `breaking` cause a
minor bump.

When a change alters generated clients, bump `version` in
[`codegen/build.gradle.kts`](codegen/build.gradle.kts) in the same PR: patch for
fixes, minor for breaking changes. Record breaking changes under a new
`## vX.Y.Z` heading in the root [CHANGELOG.md](CHANGELOG.md).

Do not hand-edit `packages/*/CHANGELOG.md`, run `new-release.py`, or bump runtime
package versions as part of a contribution. The release process does that.

## Writing and review

- Before adding a helper or abstraction, check nearby code and shared utilities
  for an existing solution. Prefer the smallest change that handles the required
  behavior.
- Write commit messages with a short summary line. Use the body, when needed,
  to explain why the change is needed, not to list every edit.
- In the PR description, explain why the change is needed and what reviewers
  should focus on. Leave out test results and Testing sections; CI already
  shows the checks.
- Add comments that explain behavior or rationale, rather than restating code.
- Verify factual claims in PRs, reviews, and changelog entries: check current
  behavior on `develop`, actual test results, and measured performance. Identify
  inferences and reproduce suspected bugs before reporting them.
- Address review feedback in new commits so reviewers can see what changed.
  Do not amend or squash fixes into earlier commits. To pick up `develop`,
  either rebase or merge it in.
- When reviewing, label findings as introduced by the change or already on
  `develop`, and lead with the new ones.

Every new `.py` file, including tests and fixtures, must start with this header
(after the shebang in executable scripts):

```python
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
```

## Code of Conduct

This project has adopted the
[Amazon Open Source Code of Conduct](https://aws.github.io/code-of-conduct).
See the [Code of Conduct FAQ](https://aws.github.io/code-of-conduct-faq) or contact
opensource-codeofconduct@amazon.com with questions or comments.

## Security issue notifications

Report potential security issues through the
[AWS/Amazon vulnerability reporting page](https://aws.amazon.com/security/vulnerability-reporting/).
Please do not create a public GitHub issue for a security vulnerability.

## Licensing

See [LICENSE](LICENSE) for the project's licensing. We will ask you to confirm
the licensing of your contribution.
