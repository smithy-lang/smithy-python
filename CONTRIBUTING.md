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
   [PR template](.github/PULL_REQUEST_TEMPLATE.md).
6. Report the checks you ran and their results, including failures or checks you
   could not run. Address CI failures and stay involved in the review.

## Development setup

Install [uv](https://docs.astral.sh/uv/), JDK 17 or newer, `make`, and
[pandoc](https://pandoc.org/installing.html). The
[README](README.md#how-do-i-use-this-to-create-a-client) also covers generating
clients with the Smithy CLI.

From the repository root, run:

```sh
make install
source .venv/bin/activate
```

`make install` sets up the uv workspace with all packages and extras, and
initializes Gradle. A plain `uv sync` does not include all workspace packages
and extras. Use `uv run` for Python tools.

Use Python 3.12, the default in [`.python-version`](.python-version), to match
CI's formatting, lint, and type checks. CI also runs tests and builds on other
Python versions; pyright results can differ when using another version locally.

Run `make install` in each new worktree. When switching checkouts, deactivate
the previous environment, activate the checkout's `.venv`, and verify that
runtime imports resolve to the checkout being tested.

Keep the repository's `.venv` active when running Gradle codegen. The generator
uses `python3` from `PATH` to run ruff and pyright; if either is unavailable, it
skips that check with a warning.

## Code organization

- `packages/` contains the Python uv workspace.
- `codegen/` contains the Java/Gradle generator used to build clients in
  [aws-sdk-python](https://github.com/aws/aws-sdk-python). See the
  [codegen guide](codegen/README.md) for generator development.
- `packages/smithy-python` is an experimental Python-native generator scaffold
  that does not generate code yet. Implement codegen features in the Java
  generator unless the task specifically concerns this package; do not implement
  the same feature in both.
- `codegen-output/` contains committed snapshots of protocol-test clients.
  Regenerate them using the [validation workflow](#validation), rather than
  editing them by hand.
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

## Validation

Run commands from the repository root with the development environment active.
The checks below correspond to the [CI workflow](.github/workflows/ci.yml).
For local validation, run the baseline checks for code changes and the
additional checks applicable to the change:

| Change | Required checks |
| --- | --- |
| Any code change | `make check-py`, `make test-py`, and `make build-py` |
| Java or Gradle changes | Also run `make format-java`, then `make build-java` |
| Codegen, protocol, codec, or serde changes | Also run `make generate-protocol-tests`, then `make test-protocols` |

`make check-py` checks Python formatting, lint, and types. Use `make lint-py`
to apply formatting and lint fixes. `make build-java` checks Java/Gradle
formatting as part of the build; `make check-java` runs that formatting check
on its own.

`make test-py` tests the Python workspace packages; it does not run protocol tests.
To run one test while developing, use:

```sh
uv run pytest <path>::<test> --no-cov
```

Coverage is enabled by default. A focused test run does not replace the
applicable checks above before submitting the change.

### Generated clients and protocol tests

`make generate-protocol-tests` regenerates the committed `codegen-output/`
snapshot and fails if it differs from the committed version. When the difference
is intended, review it, include it in the same PR, and still run
`make test-protocols`. Run these commands separately so an expected snapshot
failure does not prevent the protocol tests from running.

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
- Keep PR descriptions and commit bodies focused on why the change is needed
  and what a reviewer should look at. Avoid listing every change or what stayed
  the same.
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
