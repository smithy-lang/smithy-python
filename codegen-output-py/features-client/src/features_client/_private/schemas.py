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
_s9 = "ListNotesInput"
_s10 = "example.features#ListNotesInput"
_s11 = "nextToken"
_s12 = "pageSize"
_s13 = "NoteList"
_s14 = "member"
_s15 = "ListNotesOutput"
_s16 = "example.features#ListNotesOutput"
_s17 = "items"
_s18 = "PluginNames"
_s19 = "PutNoteInput"
_s20 = "example.features#PutNoteInput"
_s21 = "text"
_s22 = "PutNoteOutput"
_s23 = "example.features#PutNoteOutput"
_s24 = "id"
_s25 = "ThingTag"
_s26 = "key"
_s27 = "PutThingInput"
_s28 = "example.features#PutThingInput"
_s29 = "smithy.rules#contextParam"
_s30 = "smithy.api#required"
_s31 = "tag"
_s32 = "plugins"
_s33 = "EchoInput"
_s34 = "smithy.api#Unit"
_s35 = "EchoOutput"
_s36 = "PingInput"
_s37 = "PingOutput"
_s38 = "PutThingOutput"
_s39 = "Echo"
_s40 = "GetThing"
_s41 = "ListNotes"
_s42 = "smithy.rules#staticContextParams"
_s43 = "Ping"
_s44 = "PutNote"
_s45 = "PutThing"
_s46 = "FieldNotes"
_s47 = "aws.api#service"
_s48 = "smithy.protocols#rpcv2Cbor"

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

LIST_NOTES_INPUT: StaticSchema = (
    18,
    n0,
    _s9,
    {_s1: _s10, _s3: None},
    (_s11, _s12),
    ((3, 0), (7, 0)),
)

NOTE_LIST: StaticSchema = (
    16,
    n0,
    _s13,
    0,
    (_s14,),
    ((3, 0),),
)

LIST_NOTES_OUTPUT: StaticSchema = (
    18,
    n0,
    _s15,
    {_s1: _s16, _s7: None},
    (_s17, _s11),
    ((NOTE_LIST, 0), (3, 0)),
)

PLUGIN_NAMES: StaticSchema = (
    16,
    n0,
    _s18,
    0,
    (_s14,),
    ((3, 0),),
)

PUT_NOTE_INPUT: StaticSchema = (
    18,
    n0,
    _s19,
    {_s1: _s20, _s3: None},
    (_s21,),
    ((3, 0),),
)

PUT_NOTE_OUTPUT: StaticSchema = (
    18,
    n0,
    _s22,
    {_s1: _s23, _s7: None},
    (_s24,),
    ((3, 0),),
)

THING_TAG: StaticSchema = (
    18,
    n0,
    _s25,
    0,
    (_s26, _s8),
    ((3, 0), (3, 0)),
)

PUT_THING_INPUT: StaticSchema = (
    18,
    n0,
    _s27,
    {_s1: _s28, _s3: None},
    (_s4, _s31, _s32),
    (
        (3, {_s29: MappingProxyType({"name": "Name"}), _s30: None}),
        (THING_TAG, 0),
        (PLUGIN_NAMES, 0),
    ),
)

ECHO_INPUT: StaticSchema = (
    18,
    n0,
    _s33,
    {_s1: _s34, _s3: None},
)

ECHO_OUTPUT: StaticSchema = (
    18,
    n0,
    _s35,
    {_s1: _s34, _s7: None},
)

PING_INPUT: StaticSchema = (
    18,
    n0,
    _s36,
    {_s1: _s34, _s3: None},
)

PING_OUTPUT: StaticSchema = (
    18,
    n0,
    _s37,
    {_s1: _s34, _s7: None},
)

PUT_THING_OUTPUT: StaticSchema = (
    18,
    n0,
    _s38,
    {_s1: _s34, _s7: None},
)

ECHO: StaticOperationSchema = (
    23,
    n0,
    _s39,
    0,
    ECHO_INPUT,
    ECHO_OUTPUT,
    (),
)

GET_THING: StaticOperationSchema = (
    23,
    n0,
    _s40,
    0,
    GET_THING_INPUT,
    GET_THING_OUTPUT,
    (),
)

LIST_NOTES: StaticOperationSchema = (
    23,
    n0,
    _s41,
    {_s42: MappingProxyType({"Kind": MappingProxyType({"value": "list"})})},
    LIST_NOTES_INPUT,
    LIST_NOTES_OUTPUT,
    (),
)

PING: StaticOperationSchema = (
    23,
    n0,
    _s43,
    {_s42: MappingProxyType({"Kind": MappingProxyType({"value": "ping"})})},
    PING_INPUT,
    PING_OUTPUT,
    (),
)

PUT_NOTE: StaticOperationSchema = (
    23,
    n0,
    _s44,
    0,
    PUT_NOTE_INPUT,
    PUT_NOTE_OUTPUT,
    (),
)

PUT_THING: StaticOperationSchema = (
    23,
    n0,
    _s45,
    {_s42: MappingProxyType({"Kind": MappingProxyType({"value": "put"})})},
    PUT_THING_INPUT,
    PUT_THING_OUTPUT,
    (),
)

FIELD_NOTES: StaticSchema = (
    21,
    n0,
    _s46,
    {_s47: MappingProxyType({"sdkId": "Field Notes"}), _s48: None},
)
