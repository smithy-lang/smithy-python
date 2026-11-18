$version: "2.0"

namespace example.apikey

use smithy.protocols#rpcv2Cbor

/// A service that authenticates with an API key.
@rpcv2Cbor
@httpApiKeyAuth(name: "Authorization", in: "header", scheme: "ApiKey")
service ApiKeyService {
    version: "2026-11-17"
    operations: [GetThing, Health, Ping]
}

/// Uses the service's API key auth.
operation GetThing {
    input := {
        name: String
    }
    output := {
        value: String
    }
}

/// Needs no auth.
@auth([])
operation Health {}

/// Sends the API key when it has one.
@optionalAuth
operation Ping {}
