$version: "2.0"

namespace smithy.python.tests.handwritten

use smithy.protocols#rpcv2Cbor

@rpcv2Cbor(
    http: ["h2", "http/1.1"]
    eventStreamHttp: ["h2"]
)
@title("My Handwritten Model")
service MyHandwrittenModel {
    version: "2020-07-14"
    operations: [
        TradeEventStream
        PublishEvents
        SubscribeToEvents
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

/// Input-only stream: the client sends events, the server returns a summary.
operation PublishEvents {
    input := {
        channel: String
        events: PublishEventStream
    }
    output := {
        eventCount: Integer
        message: String
    }
}

@streaming
union PublishEventStream {
    log: LogEvent
    metric: MetricEvent
}

structure LogEvent {
    level: String
    message: String
}

structure MetricEvent {
    name: String
    value: Double
}

/// Output-only stream: the client subscribes, the server streams events.
operation SubscribeToEvents {
    input := {
        channel: String
        maxEvents: Integer
    }
    output := {
        subscriptionId: String
        events: SubscribeEventStream
    }
}

@streaming
union SubscribeEventStream {
    notification: NotificationEvent
    heartbeat: HeartbeatEvent
}

structure NotificationEvent {
    topic: String
    payload: String
}

structure HeartbeatEvent {
    timestamp: Timestamp
}

list IntegerList {
    member: Integer
}

@error("server")
structure StreamServiceError {
    message: String
}
