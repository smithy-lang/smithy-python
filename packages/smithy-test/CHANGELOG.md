# Changelog

## v0.3.0

### Features
* Add HTTP mocking API

### Enhancements
* Support model conformance checks for partitioned stub re-exports.
* Resolve generated union variant names correctly when constructing serde conformance values.
* `check_client_case_async` now expects the request host to start with the operation's expanded host prefix.
* Support event stream operations, including duplex, in mock_async.
* Added docstrings to the public API and ordered public definitions first.

### Bug fixes
* `xml_equal` now compares empty bodies instead of failing to parse them.

### Dependencies
* Bump `smithy-core` from `~=0.10.0` to `~=0.11.0`.
* Bump `smithy-http` from `~=0.7.0` to `~=0.8.0`.
* Bump `smithy-aws-core` from `~=0.13.0` to `~=0.14.0`.

## v0.2.0

### Features
* Added checks for client endpoint tests: `smithy_test.check_rules_case` resolves a case's parameter values with a client's endpoint resolver and `smithy_test.aio.check_client_case_async` calls a case's operation through a client.

### Enhancements
* Added support for Python 3.15.

## v0.1.0

### Features
* Added the `smithy-test` package providing `deep_equal`, a NaN-aware structural equality check for generated protocol tests.
* Added `xml_equal` for comparing XML documents in protocol tests.
