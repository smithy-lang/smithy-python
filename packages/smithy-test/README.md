# smithy-test

Test-support helpers shared by generated Smithy clients, kept out of the runtime
packages. Currently provides `deep_equal`, a structural equality check used by the
generated protocol tests that treats `NaN == NaN`, and `xml_equal`, a semantic XML
equality check. It also provides `verify_models` and `ConformanceError` for
generated conformance tests, `check_rules_case` for endpoint rule tests, and
`mock` with `HTTPMockController`, `HTTPMockExpectation`, `HTTPMockError` and
`HTTPMockMismatchError` for answering a sync client's requests without sending them.
