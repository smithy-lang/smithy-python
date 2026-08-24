# Change Log

## Unreleased

## v0.5.0

### Breaking Changes

* Removed the deprecated unprefixed aliases for generated AWS service clients.
  Imports such as `BedrockRuntimeClient` must now use the `Async`-prefixed name,
  such as `AsyncBedrockRuntimeClient`.
* Changed all generated AWS clients to use `AIOHTTPClient` as their default
  transport, including services configured for HTTP/2 or event streaming.
  Applications that require the CRT transport, such as those using
  bidirectional event streams, must install the generated client's `awscrt`
  extra and explicitly configure `AWSCRTHTTPClient`.
* Removed the legacy `Config` class from generated AWS clients in favor of the
  service-specific, async-resolved `Async<SdkId>Config` class, such as
  `AsyncBedrockRuntimeConfig`. Explicit configuration must now be resolved with
  `await Async<SdkId>Config.resolve(...)` before it is passed to the client.

## v0.4.0

### Breaking Changes

* Renamed generated AWS service clients to include `Async` (e.g.
  `BedrockRuntimeClient` is now `AsyncBedrockRuntimeClient`) to match the
  Python community convention for async clients. For clients that were already
  published under the unprefixed name, the old name remains available as a
  deprecated alias that emits a `DeprecationWarning` and will be removed in an
  upcoming release. The unprefixed name will later be reintroduced for
  synchronous clients.

<!--
TODO: Backfill pre-0.4.0 codegen releases into this file. Prior changes were
accumulated under "Unreleased" and never cut over per release, so the following
already shipped (in-tree as of the 0.3.0 codegen release) and need to be placed
under their correct version section:

* (Breaking) Removed the `http_client` config option in favor of the generic
  `transport`.
* (Feature) Removed code-generated protocol implementations in favor of
  hand-written implementations based on schemas.
* (Feature) Moved documentation for structure members into doc strings after
  the member's dataclass field declaration.
-->
