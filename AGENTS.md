# AGENTS.md

<!-- Guidance for AI coding agents. Keep it short: add a line only after agents
get the same thing wrong more than once. Review edits like code. -->

Python packages live in `packages/` (a uv workspace). The Java/Gradle client
code generator lives in `codegen/`. Design docs are in `designs/`.

## Setup and commands

- Set up with `make install`. A plain `uv sync` skips the workspace packages
  and extras. In a new git worktree, run `make install` there too and call
  tools through `uv run`.
- When switching worktrees, deactivate the previous environment and verify
  that runtime imports resolve to the checkout under test.
- Run a single test: `uv run pytest <path>::<test> --no-cov` (coverage is on
  by default).
- Run Gradle codegen with the repo's `.venv` activated. It uses `python3` from
  PATH for ruff and pyright, and skips them with only a warning if they're
  missing.

## Before calling a change done

Run what CI runs and report the actual results:

- Always run `make check-py`, `make test-py`, and `make build-py`. CI runs
  `check-py` on Python 3.12 only (the `.python-version` default). If your
  `.venv` uses another version, pyright results can differ from CI.
- If you changed Java or Gradle files, run `make format-java`, then `make build-java`.
- If you changed codegen, protocols, codecs or serde, also run
  `make generate-protocol-tests`, then `make test-protocols`. If generation
  fails only because an intended snapshot changed, review the diff and still
  run the protocol tests. `make test-py` doesn't run protocol tests.
- For codegen changes that affect naming, imports or type annotations,
  protocol-test models aren't enough. Also generate clients for real AWS
  service models and run ruff and pyright on the output. Start with the models
  we ship in `codegen/aws-models/` of
  [aws-sdk-python](https://github.com/awslabs/aws-sdk-python). For wider
  coverage, use [api-models-aws](https://github.com/aws/api-models-aws), which
  has every AWS service.

## Code generation

- The Java generator in `codegen/` is the one in use. It generates the
  clients in [aws-sdk-python](https://github.com/awslabs/aws-sdk-python).
- `packages/smithy-python` is an experimental scaffold for a Python-native
  code generator. It doesn't generate code yet and will eventually replace the
  Java one. Put codegen features in the Java generator unless the task is
  specifically about `packages/smithy-python`. Don't implement the same
  feature in both.
- `codegen-output/` is a committed snapshot of the protocol-test clients.
  Don't hand-edit it. When generated code changes, regenerate it with
  `make generate-protocol-tests` and commit the result in the same PR. That
  target fails whenever the output differs from the snapshot, so a failure is
  expected after an intended change.

## Package boundaries

- `smithy-core` imports no other workspace package. The generic packages
  (`smithy-http`, `smithy-json`, `smithy-xml`, `smithy-cbor`) never import
  `smithy_aws_*`. AWS-specific logic belongs in the `smithy_aws_*` packages,
  except SigV4 signing, which lives in `aws-sdk-signers`.
- Fix behavior in the package that owns it. Add a public API there instead of
  reaching into another package's private attributes. In packages that have a
  `_private/` directory, keep internals there.

## CI checks that are easy to miss

- Every new `.py` file, including tests and fixtures, starts with this header
  (after the shebang line in executable scripts):
  ```
  # Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
  # SPDX-License-Identifier: Apache-2.0
  ```
- Keep repro scripts and throwaway generated clients outside the repo, in a
  temp dir or a separate worktree.

## Changelog

- IMPORTANT: every user-visible change under `packages/` needs one fragment per
  package it touches:
  `uv run python scripts/changelog/new-entry.py -p <package> -t <feature|enhancement|bugfix|breaking|dependency> -d "..."`
  Use `breaking` when you remove or change public API. Write the description as
  one past-tense, customer-facing sentence.
- The fragment type drives the version bump, so choose it deliberately. A
  package with no pending fragments is only released when a dependency it
  pins with a compatible (`~=`) constraint gets a minor bump. `feature` and
  `breaking` cause a minor bump, and that cascades: a minor bump of
  `smithy-http` also minor-bumps `smithy-aws-core`, and through it the AWS SDK
  packages. Java code generator version bumps also carry through to the AWS
  clients (a patch bump gives a patch bump, a minor bump gives a minor bump).
- Changes to generated clients go under `## Unreleased` in the root `CHANGELOG.md`.
- Don't hand-edit `packages/*/CHANGELOG.md`, run `new-release.py`, or bump
  versions. The release process does that.

## Writing and review

- Change only what the task needs. Put unrelated fixes in a separate PR.
- Before adding a helper or abstraction, check nearby code and shared
  utilities for an existing solution. Prefer the smallest change that handles
  the required behavior.
- Keep PR descriptions and commit bodies to why the change is needed and what
  a reviewer should look at. Don't list every change or what stayed the same.
- Don't add code comments that restate the code.
- Address review feedback in new commits so reviewers can see what changed.
  Don't amend or squash fixes into earlier commits. To pick up `develop`,
  either rebase or merge it in.
- Verify factual claims in PRs, reviews and changelog entries before you write
  them: current behavior (check `develop`), test results, and performance
  numbers. Say when something is inferred rather than verified.
- Reproduce a suspected bug before you report it.
- When reviewing, label each finding as introduced by the change or already
  on `develop`, and lead with the new ones.
