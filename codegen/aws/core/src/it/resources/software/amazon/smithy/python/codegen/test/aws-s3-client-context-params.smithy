$version: "2.0"

namespace example.awss3ccp

use aws.api#service
use aws.auth#sigv4
use aws.protocols#restXml
use smithy.rules#clientContextParams
use smithy.rules#endpointRuleSet

@restXml
@sigv4(name: "s3")
@service(sdkId: "S3", endpointPrefix: "s3")
@clientContextParams(
    Accelerate: { type: "boolean", documentation: "Uses S3 Transfer Acceleration endpoints." }
    UseArnRegion: { type: "boolean", documentation: "Uses an ARN's region." }
)
@endpointRuleSet({
    version: "1.0"
    parameters: {
        Accelerate: {
            type: "boolean"
            required: true
            default: false
            builtIn: "AWS::S3::Accelerate"
            documentation: "Uses S3 Transfer Acceleration endpoints."
        }
        UseArnRegion: { type: "boolean", builtIn: "AWS::S3::UseArnRegion", documentation: "Uses an ARN's region." }
    }
    rules: [
        {
            conditions: [{ fn: "booleanEquals", argv: [{ ref: "Accelerate" }, true] }]
            endpoint: { url: "https://accelerate.example.com" }
            type: "endpoint"
        }
        {
            conditions: [{ fn: "isSet", argv: [{ ref: "UseArnRegion" }] }]
            endpoint: { url: "https://arn.example.com" }
            type: "endpoint"
        }
        { conditions: [], error: "No endpoint", type: "error" }
    ]
})
service S3ClientContextService {
    version: "2026-11-04"
    operations: [Ping]
}

@http(method: "POST", uri: "/ping")
operation Ping {}
