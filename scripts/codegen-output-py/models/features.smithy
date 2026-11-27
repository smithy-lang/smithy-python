$version: "2.0"

namespace example.features

use aws.api#service
use aws.auth#sigv4
use aws.protocols#httpChecksum
use smithy.protocols#rpcv2Cbor
use smithy.rules#clientContextParams
use smithy.rules#contextParam
use smithy.rules#endpointRuleSet
use smithy.rules#endpointTests
use smithy.rules#staticContextParams
use smithy.waiters#waitable

/// An AWS service that uses every client feature the generator supports.
///
/// Its endpoint rules read config, input, and operation values. Its operations
/// use SigV4, bearer token auth, API key auth, optional auth, and no auth.
@service(sdkId: "Field Notes")
@sigv4(name: "fieldnotes")
@rpcv2Cbor
@httpApiKeyAuth(name: "Authorization", in: "header", scheme: "ApiKey")
@httpBearerAuth
@clientContextParams(
    Stage: { type: "string", documentation: "The deployment stage." }
    ForcePathStyle: { type: "boolean", documentation: "Forces path-style addressing." }
)
@endpointRuleSet({
    version: "1.0"
    parameters: {
        Endpoint: { type: "string", builtIn: "SDK::Endpoint", documentation: "A custom endpoint." }
        Region: { type: "string", builtIn: "AWS::Region", documentation: "The region." }
        UseFIPS: { type: "boolean", builtIn: "AWS::UseFIPS", required: true, default: false, documentation: "Whether to use a FIPS endpoint." }
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
        {
            conditions: [
                { fn: "isSet", argv: [{ ref: "Region" }] }
                { fn: "aws.partition", argv: [{ ref: "Region" }], assign: "PartitionResult" }
            ]
            rules: [
                {
                    conditions: [{ fn: "booleanEquals", argv: [{ ref: "UseFIPS" }, true] }]
                    endpoint: { url: "https://fieldnotes-fips.{Region}.{PartitionResult#dnsSuffix}" }
                    type: "endpoint"
                }
                {
                    conditions: []
                    endpoint: {
                        url: "https://fieldnotes.{Region}.{PartitionResult#dnsSuffix}"
                        properties: {
                            authSchemes: [{ name: "sigv4", signingName: "fieldnotes", signingRegion: "{Region}" }]
                        }
                    }
                    type: "endpoint"
                }
            ]
            type: "tree"
        }
        { conditions: [], error: "No region or stage", type: "error" }
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
                endpoint: {
                    url: "https://fieldnotes.us-west-2.amazonaws.com"
                    properties: {
                        authSchemes: [{ name: "sigv4", signingName: "fieldnotes", signingRegion: "us-west-2" }]
                    }
                }
            }
            operationInputs: [
                { operationName: "PutNote", builtInParams: { "AWS::Region": "us-west-2" } }
            ]
        }
        {
            documentation: "Partition from the region"
            params: { Region: "cn-north-1" }
            expect: {
                endpoint: {
                    url: "https://fieldnotes.cn-north-1.amazonaws.com.cn"
                    properties: {
                        authSchemes: [{ name: "sigv4", signingName: "fieldnotes", signingRegion: "cn-north-1" }]
                    }
                }
            }
            operationInputs: [
                { operationName: "Ping", builtInParams: { "AWS::Region": "cn-north-1" } }
            ]
        }
        {
            documentation: "FIPS from the built-in"
            params: { Region: "us-east-1", UseFIPS: true }
            expect: {
                endpoint: { url: "https://fieldnotes-fips.us-east-1.amazonaws.com" }
            }
            operationInputs: [
                {
                    operationName: "Ping"
                    builtInParams: { "AWS::Region": "us-east-1", "AWS::UseFIPS": true }
                }
            ]
        }
        {
            documentation: "No region or stage"
            params: {}
            expect: { error: "No region or stage" }
        }
    ]
})
service FieldNotes {
    version: "2026-11-20"
    operations: [DescribeNote, Echo, GetNote, GetThing, ListNotes, Ping, PutNote, PutThing]
}

/// Describes a note and its state. Needs no auth.
@auth([])
@readonly
@waitable(
    NoteSaved: {
        documentation: "Waits until the note is saved."
        minDelay: 1
        maxDelay: 4
        acceptors: [
            {
                state: "success"
                matcher: { output: { path: "state", expected: "SAVED", comparator: "stringEquals" } }
            }
            {
                state: "failure"
                matcher: { output: { path: "state", expected: "REJECTED", comparator: "stringEquals" } }
                message: "reason"
            }
            {
                state: "retry"
                matcher: { errorType: "NoteNotFound" }
            }
        ]
    }
    NoteDeleted: {
        acceptors: [
            {
                state: "success"
                matcher: { errorType: "NoteNotFound" }
            }
        ]
    }
)
operation DescribeNote {
    input := {
        @required
        id: String
    }
    output := {
        id: String
        state: NoteState
        reason: String
    }
    errors: [
        NoteNotFound
    ]
}

enum NoteState {
    DRAFT
    SAVED
    REJECTED
}

@error("client")
structure NoteNotFound {
    message: String
}

/// Uses API key auth, but sends no key when it has none.
@auth([httpApiKeyAuth])
@optionalAuth
operation Echo {}

/// Reads a note, with a bearer token.
@auth([httpBearerAuth])
@httpChecksum(requestValidationModeMember: "checksumMode", responseAlgorithms: ["CRC32"])
operation GetNote {
    input := {
        id: String
        checksumMode: ChecksumMode
    }
    output := {
        text: String
    }
}

/// Uses API key auth.
@auth([httpApiKeyAuth])
operation GetThing {
    input := {
        name: String
    }
    output := {
        value: String
    }
}

/// Lists notes a page at a time. Needs no auth.
@auth([])
@paginated(inputToken: "nextToken", outputToken: "nextToken", items: "items", pageSize: "pageSize")
@staticContextParams(Kind: { value: "list" })
operation ListNotes {
    input := {
        nextToken: String
        pageSize: Integer
    }
    output := {
        items: NoteList
        nextToken: String
    }
}

list NoteList {
    member: String
}

/// Needs no auth.
@auth([])
@staticContextParams(Kind: { value: "ping" })
operation Ping {}

/// Saves a note, signed with SigV4.
@httpChecksum(requestChecksumRequired: true, requestAlgorithmMember: "checksumAlgorithm")
operation PutNote {
    input := {
        text: String
        checksumAlgorithm: ChecksumAlgorithm
    }
    output := {
        id: String
    }
}

/// Needs no auth.
@auth([])
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

enum ChecksumAlgorithm {
    CRC32
    SHA256
}

enum ChecksumMode {
    ENABLED
}
