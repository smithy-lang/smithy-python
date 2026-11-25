from types import MappingProxyType

from smithy_core._schema_compact import StaticOperationSchema, StaticSchema

n0 = "example.features"
_s0 = "GetNoteInput"
_s1 = "smithy.synthetic#originalShapeId"
_s2 = "example.features#GetNoteInput"
_s3 = "smithy.api#input"
_s4 = "id"
_s5 = "GetNoteOutput"
_s6 = "example.features#GetNoteOutput"
_s7 = "smithy.api#output"
_s8 = "text"
_s9 = "GetThingInput"
_s10 = "example.features#GetThingInput"
_s11 = "name"
_s12 = "GetThingOutput"
_s13 = "example.features#GetThingOutput"
_s14 = "value"
_s15 = "ListNotesInput"
_s16 = "example.features#ListNotesInput"
_s17 = "nextToken"
_s18 = "pageSize"
_s19 = "NoteList"
_s20 = "member"
_s21 = "ListNotesOutput"
_s22 = "example.features#ListNotesOutput"
_s23 = "items"
_s24 = "PluginNames"
_s25 = "PutNoteInput"
_s26 = "example.features#PutNoteInput"
_s27 = "PutNoteOutput"
_s28 = "example.features#PutNoteOutput"
_s29 = "ThingTag"
_s30 = "key"
_s31 = "PutThingInput"
_s32 = "example.features#PutThingInput"
_s33 = "smithy.rules#contextParam"
_s34 = "smithy.api#required"
_s35 = "tag"
_s36 = "plugins"
_s37 = "EchoInput"
_s38 = "smithy.api#Unit"
_s39 = "EchoOutput"
_s40 = "PingInput"
_s41 = "PingOutput"
_s42 = "PutThingOutput"
_s43 = "Echo"
_s44 = "GetNote"
_s45 = "GetThing"
_s46 = "ListNotes"
_s47 = "smithy.rules#staticContextParams"
_s48 = "Ping"
_s49 = "PutNote"
_s50 = "PutThing"
_s51 = "FieldNotes"
_s52 = "aws.api#service"
_s53 = "smithy.protocols#rpcv2Cbor"

GET_NOTE_INPUT: StaticSchema = (
    18,
    n0,
    _s0,
    {_s1: _s2, _s3: None},
    (_s4,),
    ((3, 0),),
)

GET_NOTE_OUTPUT: StaticSchema = (
    18,
    n0,
    _s5,
    {_s1: _s6, _s7: None},
    (_s8,),
    ((3, 0),),
)

GET_THING_INPUT: StaticSchema = (
    18,
    n0,
    _s9,
    {_s1: _s10, _s3: None},
    (_s11,),
    ((3, 0),),
)

GET_THING_OUTPUT: StaticSchema = (
    18,
    n0,
    _s12,
    {_s1: _s13, _s7: None},
    (_s14,),
    ((3, 0),),
)

LIST_NOTES_INPUT: StaticSchema = (
    18,
    n0,
    _s15,
    {_s1: _s16, _s3: None},
    (_s17, _s18),
    ((3, 0), (7, 0)),
)

NOTE_LIST: StaticSchema = (
    16,
    n0,
    _s19,
    0,
    (_s20,),
    ((3, 0),),
)

LIST_NOTES_OUTPUT: StaticSchema = (
    18,
    n0,
    _s21,
    {_s1: _s22, _s7: None},
    (_s23, _s17),
    ((NOTE_LIST, 0), (3, 0)),
)

PLUGIN_NAMES: StaticSchema = (
    16,
    n0,
    _s24,
    0,
    (_s20,),
    ((3, 0),),
)

PUT_NOTE_INPUT: StaticSchema = (
    18,
    n0,
    _s25,
    {_s1: _s26, _s3: None},
    (_s8,),
    ((3, 0),),
)

PUT_NOTE_OUTPUT: StaticSchema = (
    18,
    n0,
    _s27,
    {_s1: _s28, _s7: None},
    (_s4,),
    ((3, 0),),
)

THING_TAG: StaticSchema = (
    18,
    n0,
    _s29,
    0,
    (_s30, _s14),
    ((3, 0), (3, 0)),
)

PUT_THING_INPUT: StaticSchema = (
    18,
    n0,
    _s31,
    {_s1: _s32, _s3: None},
    (_s11, _s35, _s36),
    (
        (3, {_s33: MappingProxyType({"name": "Name"}), _s34: None}),
        (THING_TAG, 0),
        (PLUGIN_NAMES, 0),
    ),
)

ECHO_INPUT: StaticSchema = (
    18,
    n0,
    _s37,
    {_s1: _s38, _s3: None},
)

ECHO_OUTPUT: StaticSchema = (
    18,
    n0,
    _s39,
    {_s1: _s38, _s7: None},
)

PING_INPUT: StaticSchema = (
    18,
    n0,
    _s40,
    {_s1: _s38, _s3: None},
)

PING_OUTPUT: StaticSchema = (
    18,
    n0,
    _s41,
    {_s1: _s38, _s7: None},
)

PUT_THING_OUTPUT: StaticSchema = (
    18,
    n0,
    _s42,
    {_s1: _s38, _s7: None},
)

ECHO: StaticOperationSchema = (
    23,
    n0,
    _s43,
    0,
    ECHO_INPUT,
    ECHO_OUTPUT,
    (),
)

GET_NOTE: StaticOperationSchema = (
    23,
    n0,
    _s44,
    0,
    GET_NOTE_INPUT,
    GET_NOTE_OUTPUT,
    (),
)

GET_THING: StaticOperationSchema = (
    23,
    n0,
    _s45,
    0,
    GET_THING_INPUT,
    GET_THING_OUTPUT,
    (),
)

LIST_NOTES: StaticOperationSchema = (
    23,
    n0,
    _s46,
    {_s47: MappingProxyType({"Kind": MappingProxyType({"value": "list"})})},
    LIST_NOTES_INPUT,
    LIST_NOTES_OUTPUT,
    (),
)

PING: StaticOperationSchema = (
    23,
    n0,
    _s48,
    {_s47: MappingProxyType({"Kind": MappingProxyType({"value": "ping"})})},
    PING_INPUT,
    PING_OUTPUT,
    (),
)

PUT_NOTE: StaticOperationSchema = (
    23,
    n0,
    _s49,
    0,
    PUT_NOTE_INPUT,
    PUT_NOTE_OUTPUT,
    (),
)

PUT_THING: StaticOperationSchema = (
    23,
    n0,
    _s50,
    {_s47: MappingProxyType({"Kind": MappingProxyType({"value": "put"})})},
    PUT_THING_INPUT,
    PUT_THING_OUTPUT,
    (),
)

FIELD_NOTES: StaticSchema = (
    21,
    n0,
    _s51,
    {_s52: MappingProxyType({"sdkId": "Field Notes"}), _s53: None},
)
