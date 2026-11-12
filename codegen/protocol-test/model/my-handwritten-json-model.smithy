$version: "2.0"

namespace smithy.python.tests.handwritten.json

use smithy.protocols#rpcv2Json

/// The rpcv2Json counterpart of smithy.python.tests.handwritten#MyHandwrittenModel,
/// used to drive the duplex event-stream integration test over rpcv2Json. Shapes
/// are local copies (not shared with the CBOR service) so each service's shape
/// closure, default namespace, and generated client stay independent.
@rpcv2Json(
    http: ["h2", "http/1.1"]
    eventStreamHttp: ["h2"]
)
@title("My Handwritten JSON Model")
service MyHandwrittenJsonModel {
    version: "2020-07-14"
    operations: [
        TradeEventStream
    ]
}

/// Bidirectional (duplex) stream. The non-stream members (sessionId, greeting) are
/// carried as the initial-request and initial-response messages.
operation TradeEventStream {
    input := {
        sessionId: String
        events: TradeEvents
    }
    output := {
        greeting: String
        events: TradeEvents
    }
    errors: [
        StreamServiceError
    ]
}

@streaming
union TradeEvents {
    alpha: Alpha

    beta: Unit

    gamma: Gamma

    // The :event-type header must use the member name `delta`, not the shape name.
    delta: DifferentShapeName

    throttle: ThrottlingEvent
}

structure Alpha {
    id: String
    timestamp: Timestamp
}

structure Gamma {
    @eventHeader
    sequenceNumber: Integer

    @eventPayload
    payload: GammaPayload
}

structure GammaPayload {
    message: String
    values: IntegerList
}

structure DifferentShapeName {
    name: String
    number: Integer
}

@error("client")
@retryable(throttling: true)
structure ThrottlingEvent {
    message: String
}

list IntegerList {
    member: Integer
}

@error("server")
structure StreamServiceError {
    message: String
}
