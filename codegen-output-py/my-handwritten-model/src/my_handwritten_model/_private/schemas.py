from smithy_core._schema_compact import StaticSchema

n0 = "smithy.python.tests.handwritten"
_s0 = "Alpha"
_s1 = "id"
_s2 = "timestamp"
_s3 = "DifferentShapeName"
_s4 = "name"
_s5 = "number"
_s6 = "IntegerList"
_s7 = "member"
_s8 = "GammaPayload"
_s9 = "message"
_s10 = "values"
_s11 = "Gamma"
_s12 = "sequenceNumber"
_s13 = "smithy.api#eventHeader"
_s14 = "payload"
_s15 = "smithy.api#eventPayload"
_s16 = "HeartbeatEvent"
_s17 = "LogEvent"
_s18 = "level"
_s19 = "MetricEvent"
_s20 = "value"
_s21 = "NotificationEvent"
_s22 = "topic"
_s23 = "PublishEventStream"
_s24 = "smithy.api#streaming"
_s25 = "log"
_s26 = "metric"
_s27 = "PublishEventsInput"
_s28 = "smithy.api#input"
_s29 = "channel"
_s30 = "events"
_s31 = "PublishEventsOutput"
_s32 = "smithy.api#output"
_s33 = "eventCount"
_s34 = "StreamServiceError"
_s35 = "smithy.api#error"
_s36 = "server"
_s37 = "SubscribeEventStream"
_s38 = "notification"
_s39 = "heartbeat"
_s40 = "SubscribeToEventsInput"
_s41 = "maxEvents"
_s42 = "SubscribeToEventsOutput"
_s43 = "subscriptionId"
_s44 = "ThrottlingEvent"
_s45 = "client"
_s46 = "TradeEvents"
_s47 = "alpha"
_s48 = "beta"
_s49 = "gamma"
_s50 = "delta"
_s51 = "throttle"
_s52 = "TradeEventStreamInput"
_s53 = "sessionId"
_s54 = "TradeEventStreamOutput"
_s55 = "greeting"

ALPHA: StaticSchema = (
    18,
    n0,
    _s0,
    0,
    (
        _s1,
        _s2,
    ),
    (
        (3, 0),
        (4, 0),
    ),
)

DIFFERENT_SHAPE_NAME: StaticSchema = (
    18,
    n0,
    _s3,
    0,
    (
        _s4,
        _s5,
    ),
    (
        (3, 0),
        (7, 0),
    ),
)

INTEGER_LIST: StaticSchema = (
    16,
    n0,
    _s6,
    0,
    (_s7,),
    ((7, 0),),
)

GAMMA_PAYLOAD: StaticSchema = (
    18,
    n0,
    _s8,
    0,
    (
        _s9,
        _s10,
    ),
    (
        (3, 0),
        (INTEGER_LIST, 0),
    ),
)

GAMMA: StaticSchema = (
    18,
    n0,
    _s11,
    0,
    (
        _s12,
        _s14,
    ),
    (
        (7, {_s13: None}),
        (GAMMA_PAYLOAD, {_s15: None}),
    ),
)

HEARTBEAT_EVENT: StaticSchema = (
    18,
    n0,
    _s16,
    0,
    (_s2,),
    ((4, 0),),
)

LOG_EVENT: StaticSchema = (
    18,
    n0,
    _s17,
    0,
    (
        _s18,
        _s9,
    ),
    (
        (3, 0),
        (3, 0),
    ),
)

METRIC_EVENT: StaticSchema = (
    18,
    n0,
    _s19,
    0,
    (
        _s4,
        _s20,
    ),
    (
        (3, 0),
        (10, 0),
    ),
)

NOTIFICATION_EVENT: StaticSchema = (
    18,
    n0,
    _s21,
    0,
    (
        _s22,
        _s14,
    ),
    (
        (3, 0),
        (3, 0),
    ),
)

PUBLISH_EVENT_STREAM: StaticSchema = (
    19,
    n0,
    _s23,
    {_s24: None},
    (
        _s25,
        _s26,
    ),
    (
        (LOG_EVENT, 0),
        (METRIC_EVENT, 0),
    ),
)

PUBLISH_EVENTS_INPUT: StaticSchema = (
    18,
    n0,
    _s27,
    {_s28: None},
    (
        _s29,
        _s30,
    ),
    (
        (3, 0),
        (PUBLISH_EVENT_STREAM, 0),
    ),
)

PUBLISH_EVENTS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s31,
    {_s32: None},
    (
        _s33,
        _s9,
    ),
    (
        (7, 0),
        (3, 0),
    ),
)

STREAM_SERVICE_ERROR: StaticSchema = (
    18,
    n0,
    _s34,
    {_s35: _s36},
    (_s9,),
    ((3, 0),),
)

SUBSCRIBE_EVENT_STREAM: StaticSchema = (
    19,
    n0,
    _s37,
    {_s24: None},
    (
        _s38,
        _s39,
    ),
    (
        (NOTIFICATION_EVENT, 0),
        (HEARTBEAT_EVENT, 0),
    ),
)

SUBSCRIBE_TO_EVENTS_INPUT: StaticSchema = (
    18,
    n0,
    _s40,
    {_s28: None},
    (
        _s29,
        _s41,
    ),
    (
        (3, 0),
        (7, 0),
    ),
)

SUBSCRIBE_TO_EVENTS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s42,
    {_s32: None},
    (
        _s43,
        _s30,
    ),
    (
        (3, 0),
        (SUBSCRIBE_EVENT_STREAM, 0),
    ),
)

THROTTLING_EVENT: StaticSchema = (
    18,
    n0,
    _s44,
    {_s35: _s45},
    (_s9,),
    ((3, 0),),
)

TRADE_EVENTS: StaticSchema = (
    19,
    n0,
    _s46,
    {_s24: None},
    (
        _s47,
        _s48,
        _s49,
        _s50,
        _s51,
    ),
    (
        (ALPHA, 0),
        (-1, 0),
        (GAMMA, 0),
        (DIFFERENT_SHAPE_NAME, 0),
        (THROTTLING_EVENT, 0),
    ),
)

TRADE_EVENT_STREAM_INPUT: StaticSchema = (
    18,
    n0,
    _s52,
    {_s28: None},
    (
        _s53,
        _s30,
    ),
    (
        (3, 0),
        (TRADE_EVENTS, 0),
    ),
)

TRADE_EVENT_STREAM_OUTPUT: StaticSchema = (
    18,
    n0,
    _s54,
    {_s32: None},
    (
        _s55,
        _s30,
    ),
    (
        (3, 0),
        (TRADE_EVENTS, 0),
    ),
)
