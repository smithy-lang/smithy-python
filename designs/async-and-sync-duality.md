# Async and sync duality

Smithy-Python generated clients export two different classes that run in Python's synchronous and asynchronous (aio, async/await) operation modes respectively. For example, the `aws_sdk_s3` package will export both the `S3Client` (synchronous) and `AsyncS3Client` (asynchronous) classes. This allows the customer to operate one or both modes depending on application requirements.

## Client mode extras

Generated HTTP clients expose a `sync` and an `async` extra that install each mode's default HTTP transport (urllib3 for `sync`, aiohttp for `async`):

```sh
pip install "aws_sdk_s3[sync]"
pip install "aws_sdk_s3[async]"
pip install "aws_sdk_s3[sync,async]"
```

- A bare install, without either extra, does not install aiohttp or urllib3. It supports the shared models, and either client with an explicitly configured custom transport. Constructing a missing default transport fails with a `MissingDependencyError`.
- Public import paths are unchanged.
- Other extras keep their meaning: protocol requirements stay in the base package, and the `awscrt` extra still opts into the CRT transport.

This describes the current single-distribution package. If the modes are ever split into separate distributions, how installs that use a custom transport migrate will be designed as part of that split.

## `make aio-check`

`make aio-check` is a verification step that runs as part of CI's static analysis suite. It detects simple mechanical violations of sync/async duality, such as placing a class in the wrong location or with the wrong name.

- Async code must be placed in the `aio` folder of a package's source code. Internal sync helpers may also exist there, but public components that are not async must _not_ be in the `aio` folder.
- Public classes that exist in both modes must be named `X` and `AsyncX`.
- Public functions that exist in both modes must be named `x()` and `x_async()`.
- Sync code modules must not import from async code modules (`*.aio.*`).

## Guidelines

For more complex changes, follow these guidelines:

- Product requirements and specifications logic must only exist in one place. Async and sync APIs which implement the same underlying feature must delegate "business rules" logic to a shared location. Do not implement two functions, but rather two adapters.
- To isolate logic from sync/async operation mode, use techniques such as state machines, program runners, and pure functions that take data the caller has already read.
- Everything must exist in the sync API by default. Then consider whether an async implementation should exist. If it relates to the clients' operation API, then the answer is likely "yes". If it relates to aio components like disk or network, then the answer is definitely "yes".
- Write tests for both modes when modifying something that touches the public API.
