from smithy_core._schema_compact import StaticOperationSchema, StaticSchema

n0 = "example.apikey"
_s0 = "GetThingInput"
_s1 = "smithy.synthetic#originalShapeId"
_s2 = "example.apikey#GetThingInput"
_s3 = "smithy.api#input"
_s4 = "name"
_s5 = "GetThingOutput"
_s6 = "example.apikey#GetThingOutput"
_s7 = "smithy.api#output"
_s8 = "value"
_s9 = "HealthInput"
_s10 = "smithy.api#Unit"
_s11 = "HealthOutput"
_s12 = "PingInput"
_s13 = "PingOutput"
_s14 = "GetThing"
_s15 = "Health"
_s16 = "Ping"
_s17 = "ApiKeyService"
_s18 = "smithy.protocols#rpcv2Cbor"

GET_THING_INPUT: StaticSchema = (
    18,
    n0,
    _s0,
    {_s1: _s2, _s3: None},
    (_s4,),
    ((3, 0),),
)

GET_THING_OUTPUT: StaticSchema = (
    18,
    n0,
    _s5,
    {_s1: _s6, _s7: None},
    (_s8,),
    ((3, 0),),
)

HEALTH_INPUT: StaticSchema = (
    18,
    n0,
    _s9,
    {_s1: _s10, _s3: None},
)

HEALTH_OUTPUT: StaticSchema = (
    18,
    n0,
    _s11,
    {_s1: _s10, _s7: None},
)

PING_INPUT: StaticSchema = (
    18,
    n0,
    _s12,
    {_s1: _s10, _s3: None},
)

PING_OUTPUT: StaticSchema = (
    18,
    n0,
    _s13,
    {_s1: _s10, _s7: None},
)

GET_THING: StaticOperationSchema = (
    23,
    n0,
    _s14,
    0,
    GET_THING_INPUT,
    GET_THING_OUTPUT,
    (),
)

HEALTH: StaticOperationSchema = (
    23,
    n0,
    _s15,
    0,
    HEALTH_INPUT,
    HEALTH_OUTPUT,
    (),
)

PING: StaticOperationSchema = (
    23,
    n0,
    _s16,
    0,
    PING_INPUT,
    PING_OUTPUT,
    (),
)

API_KEY_SERVICE: StaticSchema = (
    21,
    n0,
    _s17,
    {_s18: None},
)
