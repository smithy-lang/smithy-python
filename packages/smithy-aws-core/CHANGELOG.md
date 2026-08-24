# Changelog

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
