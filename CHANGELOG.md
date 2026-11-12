# Change Log

## v0.7.0

### Breaking Changes

* Generated client operations take the members of their input as keyword-only
  parameters instead of an input object: `client.assume_role(role_arn="...",
  role_session_name="...")` rather than `client.assume_role(AssumeRoleInput(...))`.
  An operation without input members is called with no arguments. Interceptors
  still receive the input model, which the client builds from the keyword
  arguments before any other client setup.
* Members marked `@required` are required keyword parameters, including members
  of input structures and `@clientOptional` members. A member with a default may
  be omitted, and so may an idempotency token. Passing `None` is the same as
  omitting a member: a member with a modeled default is sent with that default,
  and any other is not sent. A call that leaves a required member unset raises a
  `TypeError` before the request is sent.
* A member of an operation input whose Python name is `plugins` or `self` is
  generated as `plugins_` or `self_`, because it would collide with a parameter
  every client method already declares. Only the Python name changes, not the
  wire representation, and members of nested structures are not affected.

### Features

* Nested structures and unions in a request may be written as dictionaries, as
  generated models, or as a mix of both. A union is a dictionary with exactly one
  key, the Python name of the variant being set, and a value that is not `None`.
  Unknown keys, missing required members, malformed unions, and a `str` passed
  for a list raise a `TypeError` that gives the path to the problem and never
  includes a value. Under a `@sensitive` shape it does not include the keys the
  caller wrote either.
* A model passed in a request is used as it is, never copied or changed, so a
  model from a response can be sent back. It is still checked before the request
  is sent: a required member that is `None`, an unknown union variant, or a
  dictionary inside a model raises the same `TypeError`. A dictionary is only
  converted outside a model. A member a model sets to `None` stays unset, even if
  it has a default.
* An operation's idempotency token is generated when it is omitted or `None`. It
  is generated once per call, after every interceptor's
  `modify_before_serialization` hook has run and before the request is
  serialized, so every retry sends the same token. A token the caller passes is
  sent unchanged, even an empty one.
* Every structure and union reachable from an operation input has a `TypedDict`
  form named with a `Params` suffix, such as `AssumeRoleInputParams`, declared in
  the generated model stubs. At runtime the name is plain `dict`, so importing it
  builds nothing. List and map members are typed `Sequence` and `Mapping`, which
  accept a collection of models, of dictionaries, or of both.
* An operation input with a streaming body has two dictionary forms, because the
  sync and async clients accept different bodies. The plain form, such as
  `PutObjectInputParams`, takes the bodies a sync client can send, so it can be
  unpacked into either client. The form with an `Async` prefix, such as
  `AsyncPutObjectInputParams`, also takes async streams, and only the async
  client accepts it.
* Generated client packages include a `py.typed` marker, so type checkers use
  the types of an installed client.

* Generated AWS clients validate the checksums of response payloads for operations with the `aws.protocols#httpChecksum` trait, such as Amazon S3's `GetObject`. These clients depend on the `checksums` extra of `smithy-aws-core`.
* Generated AWS clients calculate checksums of request payloads for operations with the `aws.protocols#httpChecksum` trait, which fixes Amazon S3 operations that require one, such as `PutBucketPolicy` and `DeleteObjects`.

## v0.6.0

### Breaking Changes

* Generated operation outputs and modeled errors now reserve a
  `response_metadata` attribute, carrying the request ID, extended request ID,
  and HTTP status code of the response that produced them. A modeled member
  named `responseMetadata` on an output or error is now generated as
  `response_metadata_` to avoid the collision; only the Python attribute name
  changes, not the wire representation.

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
