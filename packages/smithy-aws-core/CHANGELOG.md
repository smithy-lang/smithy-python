# Changelog

## v0.13.0

### Breaking Changes
* `smithy_aws_core.identity.EnvironmentCredentialsResolver` is now the synchronous resolver. Async code uses `smithy_aws_core.aio.identity.AsyncEnvironmentCredentialsResolver`.
* Declared explicit `__all__` exports on all public modules. Names that were previously importable only incidentally (via `from module import *` or as un-annotated module attributes) are no longer part of the public API; import public symbols by name from their documented module.
* Removed `AsyncStandardRegionalEndpointsResolver` and its `smithy_aws_core.aio.endpoints` module, along with `smithy_aws_core.endpoints.RegionalEndpointConfig` and `REGIONAL_ENDPOINT_CONFIG`. Generated AWS clients now resolve endpoints from the service's endpoint rules with `smithy_core.endpoints.BddEndpointResolver` and `smithy_aws_core.endpoints.AWS_RULES_EXTENSION`.
* Removed `smithy_aws_core.aio.config.resolvers`. The resolvers in `smithy_aws_core.config.resolvers` have `*_program` forms, such as `resolve_use_fips_endpoint_program` and `EndpointUriResolver(...).program`, that serve as sync and async config field resolvers.
* Added the `Async` prefix to async helpers: `smithy_aws_core.aio.auth.sigv4.SigV4Config` is now `AsyncSigV4Config`, and `ContainerMetadataClient`, `TokenCache` and `EC2Metadata` are now `AsyncContainerMetadataClient`, `AsyncTokenCache` and `AsyncEC2Metadata`. The IMDS `Config` moved to `smithy_aws_core.identity.imds`.
* Moved async implementations to `smithy_aws_core.aio` and added the `Async` prefix to their names, for example `AsyncAwsJson10ClientProtocol`, `AsyncSigV4AuthScheme`, `AsyncIdentityChain`, `AsyncAwsConfig` and the credential resolvers (`AsyncContainerCredentialsResolver`, `AsyncIMDSCredentialsResolver`, `AsyncProcessCredentialsResolver`). The unprefixed names are reserved for sync implementations, and some, like `StaticCredentialsResolver`, are already sync. Update imports to the `aio` paths.
* Async AWS protocols now compose an event stream mixin with the sync protocol. Removed `AsyncAwsQueryClientProtocol` and `AsyncEc2QueryClientProtocol`, which have no event streams; async clients use `AwsQueryClientProtocol` and `Ec2QueryClientProtocol`.
* Renamed `smithy_aws_core.aio.config.AwsConfigOverrides` to `AsyncAwsConfigOverrides`, and the async chain types `ChainSetup`, `NamedResolver` and `ChainIdentityProvider` to `AsyncChainSetup`, `AsyncNamedResolver` and `AsyncChainIdentityProvider`. Removed the `Async*Provider` chain providers; the built-in providers in `smithy_aws_core.identity.chain.providers` serve both chains.

### Features
* Track the credential source (code, environment variables, profile, credential process) and resolved account ID in the User Agent business metrics (`m/`) of sync and async clients.
* Added synchronous AWS support: `AwsConfig`, the protocols in `smithy_aws_core.protocols`, `SigV4AuthScheme`, `IdentityChain`, `StandardRegionalEndpointsResolver` and the sync credentials resolvers.
* Added request checksum calculation for operations with the `httpChecksum` trait, configured with the new `request_checksum_calculation` setting (`AWS_REQUEST_CHECKSUM_CALCULATION`). Checksums default to CRC64NVME, are sent in a header, and are reused on retries. A checksum set on the request is sent as is. Choosing an algorithm the SDK can't calculate raises `UnsupportedChecksumAlgorithmError`.
* Add User Agent business metrics to the `User-Agent` header (`m/`), tracking the retry mode and endpoint override.
* Added client-side event stream support for the awsJson1.0 and awsJson1.1 protocols.
* Added `HTTPChecksumTrait` for the `aws.protocols#httpChecksum` trait.
* Added response checksum validation for operations with the `httpChecksum` trait, for sync and async clients, configured with the new `response_checksum_validation` setting (`AWS_RESPONSE_CHECKSUM_VALIDATION`). Validation happens when the response payload is read to the end, through `smithy_aws_core.checksums.ChecksumStream` or `smithy_aws_core.aio.checksums.AsyncChecksumStream`, and a mismatch raises `ChecksumMismatchError`.
* Added `smithy_aws_core.endpoints.AWS_RULES_EXTENSION`, which adds AWS support to endpoint rules resolution. It provides the `aws.partition`, `aws.parseArn` and `aws.isVirtualHostableS3Bucket` functions, binds the AWS built-ins to client config, turns the endpoint's `sigv4` auth scheme into signer property overrides, and maps `sigv4a` and `sigv4-s3express` to their scheme IDs.

### Enhancements
* The `AWS_RETRY_MODE` environment variable and `retry_mode` config setting now accept `adaptive` instead of falling back to `standard` with a warning.
* Add the `exec-env/` field to the User-Agent header from the `AWS_EXECUTION_ENV` environment variable, and log a warning when `sdk_ua_app_id` is longer than 50 characters.
* Reused parsed XML response trees across AWS Query and Rest XML metadata, error identification, and shape deserialization.
* Added support for Python 3.15.

### Bug fixes
* `AWSCredentialsIdentity` no longer includes `secret_access_key` or `session_token` in its repr, which keeps them out of debug logs.

### Dependencies
* Added a `checksums` extra that installs `smithy-aws-checksums`.
* Bump `smithy-core` from `~=0.9.0` to `~=0.10.0`.
* Bump `smithy-http` from `~=0.6.0` to `~=0.7.0`.
* Bump `aws-sdk-signers` from `~=0.4.0` to `~=0.5.0`.
* Bump `smithy-aws-checksums` from `~=0.0.0` to `~=0.1.0`.
* Bump `smithy-aws-event-stream` from `~=0.3.0` to `~=0.4.0`.
* Bump `smithy-json` from `~=0.3.0` to `~=0.4.0`.
* Bump `smithy-xml` from `~=0.2.0` to `~=0.3.0`.

## v0.12.0

### Breaking Changes
* Make runtime protocol configuration user-friendly by not requiring protocol metadata

### Features
* Added `RestXmlClientProtocol`, an implementation of the `aws.protocols#restXml` protocol.
* Added client support for the aws.protocols#ec2Query protocol, including request serialization and modeled response and error deserialization.
* AWS protocols now report request identifiers on operation outputs and errors, read from the `x-amzn-requestid`, `x-amz-request-id`, and `x-amz-id-2` headers. awsQuery reads them from the response body.

### Enhancements
* Update identity chain validation to use case-insensitive comparisons for provider names.
* restXml errors fall back to the `<Message>` element when the modeled message member is empty, since some models name it `message` while services send `Message`.

### Dependencies
* Bump `smithy-core` from `~=0.8.0` to `~=0.9.0`.
* Bump `smithy-http` from `~=0.5.0` to `~=0.6.0`.
* Bump `aws-sdk-signers` from `~=0.3.0` to `~=0.4.0`.
* Bump `smithy-xml` from `~=0.1.0` to `~=0.2.0`.

## v0.11.0

### Enhancements
* Aligned with service client minor version

### Dependencies
* Bump `smithy-http` from `~=0.4.0` to `~=0.5.0`.

## v0.10.0

### Breaking Changes
* Updated the credential chain precedence so assume role credentials are resolved before session and static profile keys.

### Features
* Added client support for the `awsJson1_0` and `awsJson1_1` protocols, including request serialization and modeled response and error deserialization.
* Implement async config resolution mechanism that supports multiple config sources. Replaces the traditional Config class with Async<ServiceId>Config for AWS services.

### Enhancements
* Updated `SharedConfigContext` to track the source of the active profile as a `ConfigSource`.
* Deprecated the built-in IMDS and container credentials resolvers in favor of the resolvers provided by the `aws-credentials-imds` and `aws-credentials-http` packages.
* Updated profile session and static key providers to defer when the selected profile declares an assume-role configuration.
* Updated environment credentials provider to defer when `profile_name` is passed to `IdentityChain.create()`.

### Dependencies
* Bump `smithy-json` from `~=0.2.0` to `~=0.3.0`.

## v0.9.0

### Features
* Added process credentials support to the default AWS identity chain through the active profile's `credential_process` setting.

### Enhancements
* Added support for the `x-amz-retry-after` response header.

### Dependencies
* Bump `smithy-core` from `~=0.7.0` to `~=0.8.0`.

## v0.8.0

### Features
* Add utilities for parsing and merging shared AWS configuration and credentials files. These utilities are not yet integrated into generated clients.
* Added a modular credential chain for AWS identity resolution. `IdentityChain.create()` discovers installed chain providers via entry points, orders them by precedence, and assembles a resolver chain. Initially ships with the Environment, SharedConfig, ProfileSessionKeys, and ProfileStaticKeys providers.

### Bug fixes
* Fixed REST JSON modeled error resolution by matching error identifiers by shape name when wire and modeled namespaces differ. ([#742](https://github.com/smithy-lang/smithy-python/pull/742))

### Dependencies
* Bump `smithy-core` from `~=0.6.0` to `~=0.7.0`.

## v0.7.0

### Bug fixes
* Fixed awsQuery response deserialization for operations with no output members.

### Dependencies
* Bump `smithy-core` from `~=0.5.0` to `~=0.6.0`.

## v0.6.0

### Dependencies
* Bump `smithy-core` from `~=0.4.0` to `~=0.5.0`.
* Bump `aws-sdk-signers` from `~=0.2.0` to `~=0.3.0`.
* Bump `smithy-aws-event-stream` from `~=0.2.0` to `~=0.3.0`.

## v0.5.0

### Features
* Add `awsQuery` protocol support for Smithy clients.

### Dependencies
* Bump `smithy-core` from `~=0.3.0` to `~=0.4.0`.
* Bump `smithy-http` from `~=0.3.0` to `~=0.4.0`.
* Bump `aws-sdk-signers` from `~=0.1.0` to `~=0.2.0`.
* Bump `smithy-xml` from `~=0.0.0` to `~=0.1.0`.

## v0.4.0

### Enhancements
* Aligned with service client minor version

## v0.3.0

### Dependencies
* Bump `smithy-core` from `~=0.2.0` to `~=0.3.0`.

## v0.2.0

### Dependencies
* Bump `smithy-json` from `~=0.1.0` to `~=0.2.0`.
* Bump `smithy-core` from `~=0.1.0` to `~=0.2.0`.
* Bump `smithy-aws-event-stream` from `~=0.1.0` to `~=0.2.0`.
* Bump `smithy-http` from `~=0.2.0` to `~=0.3.0`.

## v0.1.1

### Dependencies
* Bump `smithy-http` from `~=0.1.0` to `~=0.2.0`.

## v0.1.0

### Breaking Changes
* Updated sigv4 auth resolution and identity providers to the new transport-agnostic interfaces.

### Features
* Added a hand-written implementation for the `restJson1` protocol.

## v0.0.3

### Bug fixes
* Rename `ContainerCredentialResolver` to `ContainerCredentialsResolver` to match new naming standard.

## v0.0.2

### Features
* Added support for Container credential resolution, commonly used with ECS/EKS.

## v0.0.1

### Features
* Added support for Instance Metadata Service (IMDS) credential resolution.
* Added basic endpoint support.
* Added basic User Agent support.
* Added basic AWS specific protocol support for RestJson1 and HTTP bindings.
