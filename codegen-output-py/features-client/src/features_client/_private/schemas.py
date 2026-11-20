from types import MappingProxyType

from smithy_core._schema_compact import StaticOperationSchema, StaticSchema

n0 = "example.features"
_s0 = "GetThingInput"
_s1 = "smithy.synthetic#originalShapeId"
_s2 = "example.features#GetThingInput"
_s3 = "smithy.api#input"
_s4 = "name"
_s5 = "GetThingOutput"
_s6 = "example.features#GetThingOutput"
_s7 = "smithy.api#output"
_s8 = "value"
_s9 = "PluginNames"
_s10 = "member"
_s11 = "PutNoteInput"
_s12 = "example.features#PutNoteInput"
_s13 = "text"
_s14 = "PutNoteOutput"
_s15 = "example.features#PutNoteOutput"
_s16 = "id"
_s17 = "ThingTag"
_s18 = "key"
_s19 = "PutThingInput"
_s20 = "example.features#PutThingInput"
_s21 = "smithy.rules#contextParam"
_s22 = "smithy.api#required"
_s23 = "tag"
_s24 = "plugins"
_s25 = "EchoInput"
_s26 = "smithy.api#Unit"
_s27 = "EchoOutput"
_s28 = "PingInput"
_s29 = "PingOutput"
_s30 = "PutThingOutput"
_s31 = "Echo"
_s32 = "GetThing"
_s33 = "Ping"
_s34 = "smithy.rules#staticContextParams"
_s35 = "PutNote"
_s36 = "PutThing"
_s37 = "FieldNotes"
_s38 = "aws.api#service"
_s39 = "smithy.protocols#rpcv2Cbor"

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

PLUGIN_NAMES: StaticSchema = (
    16,
    n0,
    _s9,
    0,
    (_s10,),
    ((3, 0),),
)

PUT_NOTE_INPUT: StaticSchema = (
    18,
    n0,
    _s11,
    {_s1: _s12, _s3: None},
    (_s13,),
    ((3, 0),),
)

PUT_NOTE_OUTPUT: StaticSchema = (
    18,
    n0,
    _s14,
    {_s1: _s15, _s7: None},
    (_s16,),
    ((3, 0),),
)

THING_TAG: StaticSchema = (
    18,
    n0,
    _s17,
    0,
    (_s18, _s8),
    ((3, 0), (3, 0)),
)

PUT_THING_INPUT: StaticSchema = (
    18,
    n0,
    _s19,
    {_s1: _s20, _s3: None},
    (_s4, _s23, _s24),
    (
        (3, {_s21: MappingProxyType({"name": "Name"}), _s22: None}),
        (THING_TAG, 0),
        (PLUGIN_NAMES, 0),
    ),
)

ECHO_INPUT: StaticSchema = (
    18,
    n0,
    _s25,
    {_s1: _s26, _s3: None},
)

ECHO_OUTPUT: StaticSchema = (
    18,
    n0,
    _s27,
    {_s1: _s26, _s7: None},
)

PING_INPUT: StaticSchema = (
    18,
    n0,
    _s28,
    {_s1: _s26, _s3: None},
)

PING_OUTPUT: StaticSchema = (
    18,
    n0,
    _s29,
    {_s1: _s26, _s7: None},
)

PUT_THING_OUTPUT: StaticSchema = (
    18,
    n0,
    _s30,
    {_s1: _s26, _s7: None},
)

ECHO: StaticOperationSchema = (
    23,
    n0,
    _s31,
    0,
    ECHO_INPUT,
    ECHO_OUTPUT,
    (),
)

GET_THING: StaticOperationSchema = (
    23,
    n0,
    _s32,
    0,
    GET_THING_INPUT,
    GET_THING_OUTPUT,
    (),
)

PING: StaticOperationSchema = (
    23,
    n0,
    _s33,
    {_s34: MappingProxyType({"Kind": MappingProxyType({"value": "ping"})})},
    PING_INPUT,
    PING_OUTPUT,
    (),
)

PUT_NOTE: StaticOperationSchema = (
    23,
    n0,
    _s35,
    0,
    PUT_NOTE_INPUT,
    PUT_NOTE_OUTPUT,
    (),
)

PUT_THING: StaticOperationSchema = (
    23,
    n0,
    _s36,
    {_s34: MappingProxyType({"Kind": MappingProxyType({"value": "put"})})},
    PUT_THING_INPUT,
    PUT_THING_OUTPUT,
    (),
)

FIELD_NOTES: StaticSchema = (
    21,
    n0,
    _s37,
    {_s38: MappingProxyType({"sdkId": "Field Notes"}), _s39: None},
)
