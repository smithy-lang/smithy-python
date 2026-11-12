from smithy_core._schema_compact import StaticSchema

n0 = "smithy.python.tests.handwritten.json"
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
_s16 = "StreamServiceError"
_s17 = "smithy.api#error"
_s18 = "server"
_s19 = "ThrottlingEvent"
_s20 = "client"
_s21 = "TradeEvents"
_s22 = "smithy.api#streaming"
_s23 = "alpha"
_s24 = "beta"
_s25 = "gamma"
_s26 = "delta"
_s27 = "throttle"
_s28 = "TradeEventStreamInput"
_s29 = "smithy.api#input"
_s30 = "sessionId"
_s31 = "events"
_s32 = "TradeEventStreamOutput"
_s33 = "smithy.api#output"
_s34 = "greeting"

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

STREAM_SERVICE_ERROR: StaticSchema = (
    18,
    n0,
    _s16,
    {_s17: _s18},
    (_s9,),
    ((3, 0),),
)

THROTTLING_EVENT: StaticSchema = (
    18,
    n0,
    _s19,
    {_s17: _s20},
    (_s9,),
    ((3, 0),),
)

TRADE_EVENTS: StaticSchema = (
    19,
    n0,
    _s21,
    {_s22: None},
    (
        _s23,
        _s24,
        _s25,
        _s26,
        _s27,
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
    _s28,
    {_s29: None},
    (
        _s30,
        _s31,
    ),
    (
        (3, 0),
        (TRADE_EVENTS, 0),
    ),
)

TRADE_EVENT_STREAM_OUTPUT: StaticSchema = (
    18,
    n0,
    _s32,
    {_s33: None},
    (
        _s34,
        _s31,
    ),
    (
        (3, 0),
        (TRADE_EVENTS, 0),
    ),
)
