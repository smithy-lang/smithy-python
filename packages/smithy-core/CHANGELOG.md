# Changelog

## v0.1.0

### Breaking Changes
* Introduced transport-agnostic interfaces for identity and auth, replacing the existing interfaces that were coupled to HTTP requests and responses.
* Updated retry interfaces to pull information from exceptions instead of requiring a separate classification step.
* Replaced `Exception` suffix with `Error` to follow PEP8 conventions.

### Features
* Updated schema members to preserve their ordering from the model using dict ordering, which significantly cuts back the amount of code that must be generated.
* Introduced the `ClientProtocol` interface to allow for hand-written protocol implementations and protocol swapping at runtime.
* Introduced a hand-written request pipeline to replace the one that was code-generated in Java.
* Updated exceptions to embed retryablity information.

### Enhancements
* Added usages of `TypeForm` from PEP747 via `typing_extensions` to better support typing for event streams and typed properties.

### Bug fixes
* Fix broken initializer for `HTTPAPIKeyAuthTrait`. ([#533](https://github.com/smithy-lang/smithy-python/pull/553))

## v0.0.2

### Bug fixes
* Fixed incorrect interceptors for `modify_before_signing` and `modify_before_transmit`.

## v0.0.1

### Features
* Added support for minimal components required for SDK generation.
