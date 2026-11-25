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
_s16 = "GetItemInput"
_s17 = "smithy.api#input"
_s18 = "ItemStatus"
_s19 = "PENDING"
_s20 = "smithy.api#enumValue"
_s21 = "READY"
_s22 = "FAILED"
_s23 = "GetItemOutput"
_s24 = "smithy.api#output"
_s25 = "status"
_s26 = "reason"
_s27 = "HeartbeatEvent"
_s28 = "ItemList"
_s29 = "ItemNotFound"
_s30 = "smithy.api#error"
_s31 = "client"
_s32 = "ListItemsInput"
_s33 = "nextToken"
_s34 = "pageSize"
_s35 = "ListItemsOutput"
_s36 = "items"
_s37 = "LogEvent"
_s38 = "level"
_s39 = "MetricEvent"
_s40 = "value"
_s41 = "NotificationEvent"
_s42 = "topic"
_s43 = "PublishEventStream"
_s44 = "smithy.api#streaming"
_s45 = "log"
_s46 = "metric"
_s47 = "PublishEventsInput"
_s48 = "channel"
_s49 = "events"
_s50 = "PublishEventsOutput"
_s51 = "eventCount"
_s52 = "StreamServiceError"
_s53 = "server"
_s54 = "SubscribeEventStream"
_s55 = "notification"
_s56 = "heartbeat"
_s57 = "SubscribeToEventsInput"
_s58 = "maxEvents"
_s59 = "SubscribeToEventsOutput"
_s60 = "subscriptionId"
_s61 = "ThrottlingEvent"
_s62 = "smithy.api#retryable"
_s63 = "TradeEvents"
_s64 = "alpha"
_s65 = "beta"
_s66 = "gamma"
_s67 = "delta"
_s68 = "throttle"
_s69 = "TradeEventStreamInput"
_s70 = "sessionId"
_s71 = "TradeEventStreamOutput"
_s72 = "greeting"

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

GET_ITEM_INPUT: StaticSchema = (
    18,
    n0,
    _s16,
    {_s17: None},
    (_s1,),
    ((3, 1),),
)

ITEM_STATUS: StaticSchema = (
    14,
    n0,
    _s18,
    0,
    (_s19, _s21, _s22),
    ((-1, {_s20: _s19}), (-1, {_s20: _s21}), (-1, {_s20: _s22})),
)

GET_ITEM_OUTPUT: StaticSchema = (
    18,
    n0,
    _s23,
    {_s24: None},
    (_s1, _s25, _s26),
    ((3, 0), (ITEM_STATUS, 0), (3, 0)),
)

HEARTBEAT_EVENT: StaticSchema = (
    18,
    n0,
    _s27,
    0,
    (_s2,),
    ((4, 0),),
)

ITEM_LIST: StaticSchema = (
    16,
    n0,
    _s28,
    0,
    (_s7,),
    ((3, 0),),
)

ITEM_NOT_FOUND: StaticSchema = (
    18,
    n0,
    _s29,
    {_s30: _s31},
    (_s9,),
    ((3, 0),),
)

LIST_ITEMS_INPUT: StaticSchema = (
    18,
    n0,
    _s32,
    {_s17: None},
    (_s33, _s34),
    ((3, 0), (7, 0)),
)

LIST_ITEMS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s35,
    {_s24: None},
    (_s36, _s33),
    ((ITEM_LIST, 0), (3, 0)),
)

LOG_EVENT: StaticSchema = (
    18,
    n0,
    _s37,
    0,
    (_s38, _s9),
    ((3, 0), (3, 0)),
)

METRIC_EVENT: StaticSchema = (
    18,
    n0,
    _s39,
    0,
    (_s4, _s40),
    ((3, 0), (10, 0)),
)

NOTIFICATION_EVENT: StaticSchema = (
    18,
    n0,
    _s41,
    0,
    (_s42, _s14),
    ((3, 0), (3, 0)),
)

PUBLISH_EVENT_STREAM: StaticSchema = (
    19,
    n0,
    _s43,
    {_s44: None},
    (_s45, _s46),
    ((LOG_EVENT, 0), (METRIC_EVENT, 0)),
)

PUBLISH_EVENTS_INPUT: StaticSchema = (
    18,
    n0,
    _s47,
    {_s17: None},
    (_s48, _s49),
    ((3, 0), (PUBLISH_EVENT_STREAM, 0)),
)

PUBLISH_EVENTS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s50,
    {_s24: None},
    (_s51, _s9),
    ((7, 0), (3, 0)),
)

STREAM_SERVICE_ERROR: StaticSchema = (
    18,
    n0,
    _s52,
    {_s30: _s53},
    (_s9,),
    ((3, 0),),
)

SUBSCRIBE_EVENT_STREAM: StaticSchema = (
    19,
    n0,
    _s54,
    {_s44: None},
    (_s55, _s56),
    ((NOTIFICATION_EVENT, 0), (HEARTBEAT_EVENT, 0)),
)

SUBSCRIBE_TO_EVENTS_INPUT: StaticSchema = (
    18,
    n0,
    _s57,
    {_s17: None},
    (_s48, _s58),
    ((3, 0), (7, 0)),
)

SUBSCRIBE_TO_EVENTS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s59,
    {_s24: None},
    (_s60, _s49),
    ((3, 0), (SUBSCRIBE_EVENT_STREAM, 0)),
)

THROTTLING_EVENT: StaticSchema = (
    18,
    n0,
    _s61,
    {_s30: _s31, _s62: MappingProxyType({"throttling": True})},
    (_s9,),
    ((3, 0),),
)

TRADE_EVENTS: StaticSchema = (
    19,
    n0,
    _s63,
    {_s44: None},
    (_s64, _s65, _s66, _s67, _s68),
    ((ALPHA, 0), (-1, 0), (GAMMA, 0), (DIFFERENT_SHAPE_NAME, 0), (THROTTLING_EVENT, 0)),
)

TRADE_EVENT_STREAM_INPUT: StaticSchema = (
    18,
    n0,
    _s69,
    {_s17: None},
    (_s70, _s49),
    ((3, 0), (TRADE_EVENTS, 0)),
)

TRADE_EVENT_STREAM_OUTPUT: StaticSchema = (
    18,
    n0,
    _s71,
    {_s24: None},
    (_s72, _s49),
    ((3, 0), (TRADE_EVENTS, 0)),
)
