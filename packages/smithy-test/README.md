# smithy-test

Test-support helpers shared by generated Smithy clients, kept out of the runtime
packages. Currently provides `deep_equal`, a structural equality check used by the
generated protocol tests that treats `NaN == NaN`.
