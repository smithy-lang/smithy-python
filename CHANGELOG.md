# Change Log

## Unreleased

## v0.4.0

### Breaking Changes

* Renamed generated AWS service clients to include `Async` (e.g.
  `BedrockRuntimeClient` is now `AsyncBedrockRuntimeClient`) to match the
  Python community convention for async clients. The old name is still
  available as a deprecated alias that emits a `DeprecationWarning`, and will
  be removed in an upcoming release. The unprefixed name will later be
  reintroduced for synchronous clients.

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
