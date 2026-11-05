$version: "2.0"

namespace example.accountid

use aws.api#service
use aws.auth#sigv4
use aws.protocols#restJson1
use smithy.rules#endpointRuleSet

@restJson1
@sigv4(name: "account-id")
@service(sdkId: "Account Id", endpointPrefix: "account-id")
@suppress(["RuleSetAwsBuiltIn.AWS::Auth::AccountIdEndpointMode"])
@endpointRuleSet({
    version: "1.0"
    parameters: {
        Region: { type: "string", builtIn: "AWS::Region", documentation: "The region." }
        AccountIdEndpointMode: {
            type: "string"
            builtIn: "AWS::Auth::AccountIdEndpointMode"
            documentation: "The account ID endpoint mode."
        }
    }
    rules: [
        {
            conditions: [
                { fn: "isSet", argv: [{ ref: "AccountIdEndpointMode" }] }
                { fn: "isSet", argv: [{ ref: "Region" }] }
            ]
            endpoint: { url: "https://{AccountIdEndpointMode}.{Region}.example.com" }
            type: "endpoint"
        }
        { conditions: [], error: "No mode", type: "error" }
    ]
})
service AccountIdService {
    version: "2026-10-22"
    operations: [Ping]
}

@http(method: "POST", uri: "/ping")
operation Ping {}
