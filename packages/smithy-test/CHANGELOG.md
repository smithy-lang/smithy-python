# Changelog

## v0.2.0

### Features
* Added checks for client endpoint tests: `smithy_test.check_rules_case` resolves a case's parameter values with a client's endpoint resolver and `smithy_test.aio.check_client_case_async` calls a case's operation through a client.

### Enhancements
* Added support for Python 3.15.

## v0.1.0

### Features
* Added the `smithy-test` package providing `deep_equal`, a NaN-aware structural equality check for generated protocol tests.
* Added `xml_equal` for comparing XML documents in protocol tests.
