$version: "2.0"

namespace example.sigv4

use aws.api#service
use aws.auth#sigv4
use smithy.protocols#rpcv2Cbor
use smithy.rules#endpointRuleSet

/// An AWS service that signs requests with SigV4.
@service(sdkId: "Field Notes")
@sigv4(name: "fieldnotes")
@rpcv2Cbor
@endpointRuleSet({
    version: "1.0"
    parameters: {
        Endpoint: { type: "string", builtIn: "SDK::Endpoint", documentation: "A custom endpoint." }
    }
    rules: [
        {
            conditions: [{ fn: "isSet", argv: [{ ref: "Endpoint" }] }]
            endpoint: { url: { ref: "Endpoint" } }
            type: "endpoint"
        }
        { conditions: [], error: "Endpoint is not set", type: "error" }
    ]
})
service FieldNotes {
    version: "2026-11-20"
    operations: [PutNote, Health]
}

/// Saves a note, signed with SigV4.
operation PutNote {
    input := {
        text: String
    }
    output := {
        id: String
    }
}

/// Needs no auth.
@auth([])
operation Health {}
