$version: "2.0"

namespace example.ccp

use aws.protocols#restJson1
use smithy.rules#clientContextParams
use smithy.rules#endpointRuleSet

@restJson1
@clientContextParams(
    ForcePathStyle: { type: "boolean", documentation: "Forces path-style addressing." }
    DisableS3ExpressSessionAuth: { type: "boolean" }
    Stage: { type: "string", documentation: "The deployment stage." }
)
@endpointRuleSet({
    version: "1.0"
    parameters: {
        ForcePathStyle: { type: "boolean", required: true, default: false, documentation: "Forces path-style addressing." }
        DisableS3ExpressSessionAuth: { type: "boolean", documentation: "Disables session auth." }
        Stage: { type: "string", documentation: "The deployment stage." }
    }
    rules: [
        {
            conditions: [{ fn: "isSet", argv: [{ ref: "Stage" }] }]
            endpoint: { url: "https://{Stage}.example.com" }
            type: "endpoint"
        }
        {
            conditions: [{ fn: "booleanEquals", argv: [{ ref: "ForcePathStyle" }, true] }]
            endpoint: { url: "https://path.example.com" }
            type: "endpoint"
        }
        { conditions: [], error: "No stage", type: "error" }
    ]
})
service ClientContextService {
    version: "2026-10-21"
    operations: [Ping]
}

@http(method: "POST", uri: "/ping")
operation Ping {}
