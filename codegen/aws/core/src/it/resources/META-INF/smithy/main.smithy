$version: "2.0"

namespace example.aws

use aws.protocols#restJson1
use aws.api#service

/// A test service that renders a restJson1 service with AWS traits
@restJson1(
    http: ["h2", "http/1.1"]
    eventStreamHttp: ["h2"]
)
@service(
    sdkId: "REST JSON",
    endpointPrefix: "rest-json-1"
)
@title("AWS REST JSON Service")
@paginated(inputToken: "nextToken", outputToken: "nextToken", pageSize: "pageSize")
@httpApiKeyAuth(name: "weather-auth", in: "header")
service RestJsonService {
    version: "2006-03-01"
    operations: [
        BasicOperation
    ]
}

@http(code: 200, method: "POST", uri: "/basic-operation")
operation BasicOperation {
    input := {
        message: String
    }
    output := {
        message: String
    }
}

@http(code: 200, method: "POST", uri: "/input-stream")
operation InputStream {
    input := {
        stream: EventStream
    }
}

@http(code: 200, method: "POST", uri: "/output-stream")
operation OutputStream {
    output := {
        stream: EventStream
    }
}

@http(code: 200, method: "POST", uri: "/duplex-stream")
operation DuplexStream {
    input := {
        stream: EventStream
    }
    output := {
        stream: EventStream
    }
}


@streaming
union EventStream {
    message: MessageEvent
}

structure MessageEvent {
    message: String
}

