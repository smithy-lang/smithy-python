$version: "2"

namespace smithy.python.test

use aws.auth#sigv4
use aws.protocols#restJson1
use smithy.api#retryable


@restJson1
@sigv4(name: "awskitchensink")
service AwsKitchenSink {
    version: "2025-10-31"
    operations: [
        CreateItem
        GetItem
    ]
}

@http(code: 201, method: "POST", uri: "/items")
operation CreateItem {
    input := {
        @required
        name: String
    }
    output := {
        id: String
        name: String
    }
}

@http(code: 200, method: "GET", uri: "/items/{id}")
@readonly
operation GetItem {
    input := {
        @required
        @httpLabel
        id: String
    }
    output := {
        message: String
    }
    errors: [
        ItemNotFound
        ThrottlingError
        InternalError
        ServiceUnavailableError
    ]
}

@error("client")
@httpError(400)
structure ItemNotFound {
    message: String
}

@error("client")
@retryable(throttling: true)
@httpError(429)
structure ThrottlingError {
    message: String
}

@error("server")
@retryable
@httpError(500)
structure InternalError {
    message: String
}

@error("server")
@retryable
@httpError(503)
structure ServiceUnavailableError {
    message: String
}
