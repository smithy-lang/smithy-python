$version: "2.0"

namespace example.endpoints

use smithy.protocols#rpcv2Cbor
use smithy.rules#clientContextParams
use smithy.rules#contextParam
use smithy.rules#endpointRuleSet
use smithy.rules#endpointTests
use smithy.rules#staticContextParams

/// A service whose endpoint rules read config, input, and operation values.
@rpcv2Cbor
@clientContextParams(
    Stage: { type: "string", documentation: "The deployment stage." }
    ForcePathStyle: { type: "boolean", documentation: "Forces path-style addressing." }
)
@endpointRuleSet({
    version: "1.0"
    parameters: {
        Endpoint: { type: "string", builtIn: "SDK::Endpoint", documentation: "A custom endpoint." }
        Region: { type: "string", builtIn: "AWS::Region", documentation: "The region." }
        Stage: { type: "string", documentation: "The deployment stage." }
        ForcePathStyle: { type: "boolean", required: true, default: false, documentation: "Forces path-style addressing." }
        Name: { type: "string", documentation: "The thing name." }
        Kind: { type: "string", documentation: "The operation kind." }
    }
    rules: [
        {
            conditions: [{ fn: "isSet", argv: [{ ref: "Endpoint" }] }]
            endpoint: { url: { ref: "Endpoint" } }
            type: "endpoint"
        }
        {
            conditions: [{ fn: "isSet", argv: [{ ref: "Region" }] }]
            endpoint: { url: "https://{Region}.example.com" }
            type: "endpoint"
        }
        {
            conditions: [{ fn: "booleanEquals", argv: [{ ref: "ForcePathStyle" }, true] }]
            endpoint: { url: "https://path.example.com" }
            type: "endpoint"
        }
        {
            conditions: [
                { fn: "isSet", argv: [{ ref: "Stage" }] }
                { fn: "isSet", argv: [{ ref: "Name" }] }
                { fn: "isValidHostLabel", argv: [{ ref: "Name" }, false] }
                { fn: "isSet", argv: [{ ref: "Kind" }] }
            ]
            endpoint: {
                url: "https://{Name}.{Stage}.example.com"
                headers: { "x-kind": ["{Kind}"] }
            }
            type: "endpoint"
        }
        {
            conditions: [
                { fn: "isSet", argv: [{ ref: "Stage" }] }
                { fn: "isSet", argv: [{ ref: "Kind" }] }
            ]
            endpoint: { url: "https://{Stage}.example.com", properties: { kind: "{Kind}" } }
            type: "endpoint"
        }
        { conditions: [], error: "No stage", type: "error" }
    ]
})
@endpointTests({
    version: "1.0"
    testCases: [
        {
            documentation: "Stage from config"
            params: { Stage: "beta", Kind: "ping" }
            expect: {
                endpoint: { url: "https://beta.example.com", properties: { kind: "ping" } }
            }
            operationInputs: [
                { operationName: "Ping", clientParams: { Stage: "beta" } }
            ]
        }
        {
            documentation: "Name from input"
            params: { Stage: "beta", Name: "thing", Kind: "put" }
            expect: {
                endpoint: { url: "https://thing.beta.example.com", headers: { "x-kind": ["put"] } }
            }
            operationInputs: [
                {
                    operationName: "PutThing"
                    clientParams: { Stage: "beta" }
                    operationParams: {
                        name: "thing"
                        tag: { key: "k", value: "v" }
                        plugins: ["p"]
                    }
                }
            ]
        }
        {
            documentation: "Invalid name falls back to the stage"
            params: { Stage: "beta", Name: "not a label", Kind: "put" }
            expect: {
                endpoint: { url: "https://beta.example.com", properties: { kind: "put" } }
            }
            operationInputs: [
                {
                    operationName: "PutThing"
                    clientParams: { Stage: "beta" }
                    operationParams: { name: "not a label" }
                }
            ]
        }
        {
            documentation: "Path style from config"
            params: { ForcePathStyle: true }
            expect: {
                endpoint: { url: "https://path.example.com" }
            }
            operationInputs: [
                { operationName: "Ping", clientParams: { ForcePathStyle: true } }
            ]
        }
        {
            documentation: "Custom endpoint"
            params: { Endpoint: "https://custom.example.com", Stage: "beta" }
            expect: {
                endpoint: { url: "https://custom.example.com" }
            }
            operationInputs: [
                {
                    operationName: "Ping"
                    builtInParams: { "SDK::Endpoint": "https://custom.example.com" }
                    clientParams: { Stage: "beta" }
                }
            ]
        }
        {
            documentation: "Region from the built-in"
            params: { Region: "us-west-2" }
            expect: {
                endpoint: { url: "https://us-west-2.example.com" }
            }
            operationInputs: [
                { operationName: "Ping", builtInParams: { "AWS::Region": "us-west-2" } }
            ]
        }
        {
            documentation: "Missing stage"
            params: {}
            expect: { error: "No stage" }
            operationInputs: [
                { operationName: "Ping" }
            ]
        }
        {
            documentation: "Missing stage"
            params: { Kind: "put" }
            expect: { error: "No stage" }
        }
    ]
})
service EndpointService {
    version: "2026-11-20"
    operations: [Ping, PutThing]
}

@staticContextParams(Kind: { value: "ping" })
operation Ping {}

@staticContextParams(Kind: { value: "put" })
operation PutThing {
    input := {
        @required
        @contextParam(name: "Name")
        name: String

        tag: ThingTag

        plugins: PluginNames
    }
}

structure ThingTag {
    key: String
    value: String
}

list PluginNames {
    member: String
}
