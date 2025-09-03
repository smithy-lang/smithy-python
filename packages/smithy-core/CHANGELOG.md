# Changelog

## Unreleased

### Breaking Changes

* Replaced `Exception` suffix with `Error` to follow PEP8 conventions.
* Introduced transport-agnostic interfaces for identiy and auth, replacing the
  existing interfaces that were coupled to HTTP requests and responses.
* Updated retry interfaces to pull information from exceptions instead of requriing
  a separate classification step.

### Features

* Introduced a hand-written request pipeline to replace the one that was code-generated
  in Java.
* Updated schema members to preserve their ordering from the model using dict ordering,
  which significantly cuts back the amount of code that must be generated.
* Updated exceptions to embed retryablity information.
* Introduced the `ClientProtocol` interface to allow for hand-written protocol
  implementations and protocol swapping at runtime.

### Typing

* Added usages of `TypeForm` from PEP747 via `typing_extensions` to better support
  typing for event streams and typed properties.

## v0.0.2

### Bugfixes

* Fixed incorrect interceptors for `modify_before_signing` and `modify_before_transmit`.

## v0.0.1

### Features

* Added support for minimal components required for SDK generation.
