from types import MappingProxyType

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
_s17 = "ItemList"
_s18 = "ListItemsInput"
_s19 = "smithy.api#input"
_s20 = "nextToken"
_s21 = "pageSize"
_s22 = "ListItemsOutput"
_s23 = "smithy.api#output"
_s24 = "items"
_s25 = "LogEvent"
_s26 = "level"
_s27 = "MetricEvent"
_s28 = "value"
_s29 = "NotificationEvent"
_s30 = "topic"
_s31 = "PublishEventStream"
_s32 = "smithy.api#streaming"
_s33 = "log"
_s34 = "metric"
_s35 = "PublishEventsInput"
_s36 = "channel"
_s37 = "events"
_s38 = "PublishEventsOutput"
_s39 = "eventCount"
_s40 = "StreamServiceError"
_s41 = "smithy.api#error"
_s42 = "server"
_s43 = "SubscribeEventStream"
_s44 = "notification"
_s45 = "heartbeat"
_s46 = "SubscribeToEventsInput"
_s47 = "maxEvents"
_s48 = "SubscribeToEventsOutput"
_s49 = "subscriptionId"
_s50 = "ThrottlingEvent"
_s51 = "client"
_s52 = "smithy.api#retryable"
_s53 = "TradeEvents"
_s54 = "alpha"
_s55 = "beta"
_s56 = "gamma"
_s57 = "delta"
_s58 = "throttle"
_s59 = "TradeEventStreamInput"
_s60 = "sessionId"
_s61 = "TradeEventStreamOutput"
_s62 = "greeting"

ALPHA: StaticSchema = (
    18,
    n0,
    _s0,
    0,
    (_s1, _s2),
    ((3, 0), (4, 0)),
)

DIFFERENT_SHAPE_NAME: StaticSchema = (
    18,
    n0,
    _s3,
    0,
    (_s4, _s5),
    ((3, 0), (7, 0)),
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
    (_s9, _s10),
    ((3, 0), (INTEGER_LIST, 0)),
)

GAMMA: StaticSchema = (
    18,
    n0,
    _s11,
    0,
    (_s12, _s14),
    ((7, {_s13: None}), (GAMMA_PAYLOAD, {_s15: None})),
)

HEARTBEAT_EVENT: StaticSchema = (
    18,
    n0,
    _s16,
    0,
    (_s2,),
    ((4, 0),),
)

ITEM_LIST: StaticSchema = (
    16,
    n0,
    _s17,
    0,
    (_s7,),
    ((3, 0),),
)

LIST_ITEMS_INPUT: StaticSchema = (
    18,
    n0,
    _s18,
    {_s19: None},
    (_s20, _s21),
    ((3, 0), (7, 0)),
)

LIST_ITEMS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s22,
    {_s23: None},
    (_s24, _s20),
    ((ITEM_LIST, 0), (3, 0)),
)

LOG_EVENT: StaticSchema = (
    18,
    n0,
    _s25,
    0,
    (_s26, _s9),
    ((3, 0), (3, 0)),
)

METRIC_EVENT: StaticSchema = (
    18,
    n0,
    _s27,
    0,
    (_s4, _s28),
    ((3, 0), (10, 0)),
)

NOTIFICATION_EVENT: StaticSchema = (
    18,
    n0,
    _s29,
    0,
    (_s30, _s14),
    ((3, 0), (3, 0)),
)

PUBLISH_EVENT_STREAM: StaticSchema = (
    19,
    n0,
    _s31,
    {_s32: None},
    (_s33, _s34),
    ((LOG_EVENT, 0), (METRIC_EVENT, 0)),
)

PUBLISH_EVENTS_INPUT: StaticSchema = (
    18,
    n0,
    _s35,
    {_s19: None},
    (_s36, _s37),
    ((3, 0), (PUBLISH_EVENT_STREAM, 0)),
)

PUBLISH_EVENTS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s38,
    {_s23: None},
    (_s39, _s9),
    ((7, 0), (3, 0)),
)

STREAM_SERVICE_ERROR: StaticSchema = (
    18,
    n0,
    _s40,
    {_s41: _s42},
    (_s9,),
    ((3, 0),),
)

SUBSCRIBE_EVENT_STREAM: StaticSchema = (
    19,
    n0,
    _s43,
    {_s32: None},
    (_s44, _s45),
    ((NOTIFICATION_EVENT, 0), (HEARTBEAT_EVENT, 0)),
)

SUBSCRIBE_TO_EVENTS_INPUT: StaticSchema = (
    18,
    n0,
    _s46,
    {_s19: None},
    (_s36, _s47),
    ((3, 0), (7, 0)),
)

SUBSCRIBE_TO_EVENTS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s48,
    {_s23: None},
    (_s49, _s37),
    ((3, 0), (SUBSCRIBE_EVENT_STREAM, 0)),
)

THROTTLING_EVENT: StaticSchema = (
    18,
    n0,
    _s50,
    {_s41: _s51, _s52: MappingProxyType({"throttling": True})},
    (_s9,),
    ((3, 0),),
)

TRADE_EVENTS: StaticSchema = (
    19,
    n0,
    _s53,
    {_s32: None},
    (_s54, _s55, _s56, _s57, _s58),
    ((ALPHA, 0), (-1, 0), (GAMMA, 0), (DIFFERENT_SHAPE_NAME, 0), (THROTTLING_EVENT, 0)),
)

TRADE_EVENT_STREAM_INPUT: StaticSchema = (
    18,
    n0,
    _s59,
    {_s19: None},
    (_s60, _s37),
    ((3, 0), (TRADE_EVENTS, 0)),
)

TRADE_EVENT_STREAM_OUTPUT: StaticSchema = (
    18,
    n0,
    _s61,
    {_s23: None},
    (_s62, _s37),
    ((3, 0), (TRADE_EVENTS, 0)),
)
