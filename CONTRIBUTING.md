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
6. When handing off a change, report the checks you ran and their results,
   including failures and checks you skipped or could not run, and why. Keep
   these results out of the PR description. Address CI failures and stay
   involved in the review.

## Development setup

Install [uv](https://docs.astral.sh/uv/), JDK 17 or newer, `make`, and
[pandoc](https://pandoc.org/installing.html). The
[README](README.md#how-do-i-use-this-to-create-a-client) also covers generating
clients with the Smithy CLI.

`smithy-checksums` includes a Rust extension. Without `cargo` on `PATH`, it
builds as pure Python; see its [README](packages/smithy-checksums/README.md#building).
To build the extension or run the Rust checks, install
[rustup](https://rustup.rs/); it uses the toolchain pinned in
[`rust-toolchain.toml`](rust-toolchain.toml). `make check-rust` also needs
`cargo-deny` and `cargo-about`; CI pins their versions in the
[CI workflow](.github/workflows/ci.yml).

From the repository root, run:

```sh
make install
source .venv/bin/activate
```

`make install` sets up the uv workspace with all packages and extras, and
initializes Gradle. A plain `uv sync` does not include all workspace packages
and extras. Use `uv run` for Python tools.

Use Python 3.12, the default in [`.python-version`](.python-version). CI runs
static analysis and Rust checks on 3.12 only, and runs tests and builds on
every Python version in its matrix. Pyright results can differ on other
versions.

Run `make install` in each new worktree. When switching checkouts, deactivate
the previous environment, activate the checkout's `.venv`, and verify that
runtime imports resolve to the checkout being tested.

Keep the repository's `.venv` active when running Gradle codegen. The generator
uses `python3` from `PATH` to run ruff and pyright; if either is unavailable, it
skips that check with a warning.

## Code organization

- `packages/` contains the Python uv workspace: the runtime packages and the
  native generator.
- `codegen/` contains the Java/Gradle generator. It generates service clients,
  including those in [aws-sdk-python](https://github.com/aws/aws-sdk-python),
  and remains the authoritative implementation. See the
  [codegen guide](codegen/README.md) for generator development.
- `packages/smithy-python` is the experimental Python-native generator. It
  reads a Smithy JSON AST model. `smithy-python generate types` generates
  standalone types packages; client generation is still under development. See
  its [README](packages/smithy-python/README.md) and the
  [codegen design](designs/codegen/index.md). It must not depend on Java,
  Gradle, or the Java generator.
- Implement client generation features in the Java generator unless the task
  specifically concerns the native generator. Do not implement the same feature
  in both.
- `codegen-output/` contains committed snapshots of the Java-generated
  protocol-test clients.
- `codegen-output-py/` contains a committed snapshot of native types output,
  generated from [`scripts/codegen-output-py/model.json`](scripts/codegen-output-py/model.json).
- `scripts/api-snapshot/api.json` records the public API surface of the
  workspace packages.
- Do not edit these snapshots by hand. Regenerate them as described in
  [Generated output and snapshots](#generated-output-and-snapshots).
- `designs/` contains design documents.

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
`make help` lists all targets.

### CI checks

The main job in the [CI workflow](.github/workflows/ci.yml) runs `make install`
and then these targets on each Python version in its matrix. `make ci` runs the
same sequence locally and stops at the first failure.

| Target | What it runs |
| --- | --- |
| `make static-analysis` | `make check-py` (ruff lint and format checks, pyright on `packages/`), `make typecheck-protocols` (pyright on the type fixtures in `codegen-output/`), and `make api-snapshot`. CI runs it on 3.12 only. |
| `make check-rust` | `cargo fmt`, `clippy`, `cargo deny`, and a third-party license check for each package with a `Cargo.toml`. CI runs it on 3.12 only. |
| `make test-unit` | The unit tests in `packages/*/tests/unit`. |
| `make test-functional` | `make test-protocols`, then the functional and integration tests in `packages/*/tests`. The integration tests use in-process servers, not live services. |
| `make build-py` | Builds every workspace package. |
| `make test-integration` | `make build-java` (builds and tests the Java generator), then `make generate-protocol-tests` and `make generate-codegen-output-py`. |

Other CI jobs build and test the native extension wheels on several platforms;
`make ci` does not cover them.

### Choosing checks

While developing, run focused tests:

```sh
uv run pytest <path>::<test> --no-cov
```

Coverage is enabled by default; `--no-cov` turns it off. A focused run does not
replace the checks below. Before handing off a change, run the checks for each
area it touches. `make ci` runs every check in the main CI job, and needs JDK,
Rust, `cargo-deny`, and `cargo-about`.

| Change | Checks |
| --- | --- |
| Documentation only | No build or test target. Check changed links, and check any changed commands or facts against the source. |
| Python runtime packages | `make check-py`, `make test-unit`, and `make api-snapshot`. Add `make test-functional` for HTTP, protocol, codec, serde, or generated-client behavior, and `make build-py` for packaging changes. |
| Rust extensions | `make check-rust` and `make test-unit`. `make lint-rust` applies formatting and lint fixes; run `make third-party-licenses` after Rust dependency changes. |
| Java generator or Gradle | `make format-java`, `make build-java`, `make generate-protocol-tests`, `make typecheck-protocols`, and `make test-protocols`. |
| Native generator (`packages/smithy-python`) | `make check-py`, `make test-unit`, `make api-snapshot`, and `make generate-codegen-output-py`. |

`make lint-py` applies Python formatting and lint fixes. `make build-java`
checks Java/Gradle formatting as part of the build; `make check-java` runs that
formatting check on its own. `make test-py` runs pytest on all of `packages/`
but is not part of CI. Neither `make test-py` nor `make test-unit` runs
protocol tests.

### Generated output and snapshots

Three targets regenerate committed output in the working tree, then fail if it
differs from the git index:

- `make generate-protocol-tests` builds the protocol-test clients with the Java
  generator and copies them to `codegen-output/`.
- `make generate-codegen-output-py` runs the native generator into
  `codegen-output-py/`.
- `make api-snapshot` writes `scripts/api-snapshot/api.json`.

`make typecheck-protocols` and `make test-protocols` install and test whatever
is in `codegen-output/`; they do not regenerate it. After a Java generator
change, run `make generate-protocol-tests` first.

When a snapshot change is intended, the target fails and prints the diff.
Review the diff and include it in the same PR. Then either run the remaining
checks as separate commands, or stage the reviewed output (for example,
`git add codegen-output`) so that a rerun passes. Do not rely on a composite
target such as `make test-integration` or `make ci` while a snapshot differs;
it stops at the failing target and skips the later checks. For a Java generator
change, the separate commands are:

```sh
make build-java
make generate-protocol-tests  # fails while codegen-output/ differs
make typecheck-protocols
make test-protocols
```

Skip the generation targets when a change cannot affect generated output, such
as a documentation-only change.

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

The fragment type controls the version bump. `feature` and `breaking` cause a
minor bump. A package without pending fragments is released only when a
dependency pinned with a compatible (`~=`) constraint gets a minor bump. These
bumps cascade: a minor bump of `smithy-http` also minor-bumps `smithy-aws-core`,
and through it the AWS SDK packages.

When a change alters generated clients, bump `version` in
[`codegen/build.gradle.kts`](codegen/build.gradle.kts) in the same PR: patch for
fixes, minor for breaking changes. The version bump triggers client regeneration
during release and carries through to the AWS clients. Record breaking changes
under a new `## vX.Y.Z` heading in the root [CHANGELOG.md](CHANGELOG.md).

Do not hand-edit `packages/*/CHANGELOG.md`, run `new-release.py`, or bump runtime
package versions as part of a contribution. The release process does that.

## Writing and review

- Before adding a helper or abstraction, check nearby code and shared utilities
  for an existing solution. Prefer the smallest change that handles the required
  behavior.
- Write commit messages with a short summary line. Use the body, when needed,
  to explain why the change is needed, not to list every edit.
- In the PR description, explain why the change is needed and what reviewers
  should focus on. Do not include test results, test summaries, or a Testing
  section that repeats CI; the PR's CI checks already show them.
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
