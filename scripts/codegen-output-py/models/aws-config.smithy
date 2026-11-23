$version: "2.0"

namespace example.awsconfig

use aws.api#service
use smithy.protocols#rpcv2Cbor
use smithy.rules#endpointRuleSet

/// An AWS service that reads its config from the environment and profiles.
@service(sdkId: "Weather Station")
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
service WeatherStation {
    version: "2026-11-19"
    operations: [GetForecast]
}

/// Gets the forecast for a city.
operation GetForecast {
    input := {
        city: String
    }
    output := {
        summary: String
    }
}
