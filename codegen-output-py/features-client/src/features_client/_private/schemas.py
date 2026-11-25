from types import MappingProxyType

from smithy_core._schema_compact import StaticOperationSchema, StaticSchema

n0 = "example.features"
_s0 = "GetNoteInput"
_s1 = "smithy.synthetic#originalShapeId"
_s2 = "example.features#GetNoteInput"
_s3 = "smithy.api#input"
_s4 = "id"
_s5 = "NoteState"
_s6 = "DRAFT"
_s7 = "smithy.api#enumValue"
_s8 = "SAVED"
_s9 = "REJECTED"
_s10 = "GetNoteOutput"
_s11 = "example.features#GetNoteOutput"
_s12 = "smithy.api#output"
_s13 = "state"
_s14 = "reason"
_s15 = "GetThingInput"
_s16 = "example.features#GetThingInput"
_s17 = "name"
_s18 = "GetThingOutput"
_s19 = "example.features#GetThingOutput"
_s20 = "value"
_s21 = "ListNotesInput"
_s22 = "example.features#ListNotesInput"
_s23 = "nextToken"
_s24 = "pageSize"
_s25 = "NoteList"
_s26 = "member"
_s27 = "ListNotesOutput"
_s28 = "example.features#ListNotesOutput"
_s29 = "items"
_s30 = "NoteNotFound"
_s31 = "smithy.api#error"
_s32 = "client"
_s33 = "message"
_s34 = "PluginNames"
_s35 = "PutNoteInput"
_s36 = "example.features#PutNoteInput"
_s37 = "text"
_s38 = "PutNoteOutput"
_s39 = "example.features#PutNoteOutput"
_s40 = "ThingTag"
_s41 = "key"
_s42 = "PutThingInput"
_s43 = "example.features#PutThingInput"
_s44 = "smithy.rules#contextParam"
_s45 = "smithy.api#required"
_s46 = "tag"
_s47 = "plugins"
_s48 = "EchoInput"
_s49 = "smithy.api#Unit"
_s50 = "EchoOutput"
_s51 = "PingInput"
_s52 = "PingOutput"
_s53 = "PutThingOutput"
_s54 = "Echo"
_s55 = "GetNote"
_s56 = "smithy.waiters#waitable"
_s57 = "GetThing"
_s58 = "ListNotes"
_s59 = "smithy.rules#staticContextParams"
_s60 = "Ping"
_s61 = "PutNote"
_s62 = "PutThing"
_s63 = "FieldNotes"
_s64 = "aws.api#service"
_s65 = "smithy.protocols#rpcv2Cbor"

GET_NOTE_INPUT: StaticSchema = (
    18,
    n0,
    _s0,
    {_s1: _s2, _s3: None},
    (_s4,),
    ((3, 1),),
)

NOTE_STATE: StaticSchema = (
    14,
    n0,
    _s5,
    0,
    (_s6, _s8, _s9),
    ((-1, {_s7: _s6}), (-1, {_s7: _s8}), (-1, {_s7: _s9})),
)

GET_NOTE_OUTPUT: StaticSchema = (
    18,
    n0,
    _s10,
    {_s1: _s11, _s12: None},
    (_s4, _s13, _s14),
    ((3, 0), (NOTE_STATE, 0), (3, 0)),
)

GET_THING_INPUT: StaticSchema = (
    18,
    n0,
    _s15,
    {_s1: _s16, _s3: None},
    (_s17,),
    ((3, 0),),
)

GET_THING_OUTPUT: StaticSchema = (
    18,
    n0,
    _s18,
    {_s1: _s19, _s12: None},
    (_s20,),
    ((3, 0),),
)

LIST_NOTES_INPUT: StaticSchema = (
    18,
    n0,
    _s21,
    {_s1: _s22, _s3: None},
    (_s23, _s24),
    ((3, 0), (7, 0)),
)

NOTE_LIST: StaticSchema = (
    16,
    n0,
    _s25,
    0,
    (_s26,),
    ((3, 0),),
)

LIST_NOTES_OUTPUT: StaticSchema = (
    18,
    n0,
    _s27,
    {_s1: _s28, _s12: None},
    (_s29, _s23),
    ((NOTE_LIST, 0), (3, 0)),
)

NOTE_NOT_FOUND: StaticSchema = (
    18,
    n0,
    _s30,
    {_s31: _s32},
    (_s33,),
    ((3, 0),),
)

PLUGIN_NAMES: StaticSchema = (
    16,
    n0,
    _s34,
    0,
    (_s26,),
    ((3, 0),),
)

PUT_NOTE_INPUT: StaticSchema = (
    18,
    n0,
    _s35,
    {_s1: _s36, _s3: None},
    (_s37,),
    ((3, 0),),
)

PUT_NOTE_OUTPUT: StaticSchema = (
    18,
    n0,
    _s38,
    {_s1: _s39, _s12: None},
    (_s4,),
    ((3, 0),),
)

THING_TAG: StaticSchema = (
    18,
    n0,
    _s40,
    0,
    (_s41, _s20),
    ((3, 0), (3, 0)),
)

PUT_THING_INPUT: StaticSchema = (
    18,
    n0,
    _s42,
    {_s1: _s43, _s3: None},
    (_s17, _s46, _s47),
    (
        (3, {_s44: MappingProxyType({"name": "Name"}), _s45: None}),
        (THING_TAG, 0),
        (PLUGIN_NAMES, 0),
    ),
)

ECHO_INPUT: StaticSchema = (
    18,
    n0,
    _s48,
    {_s1: _s49, _s3: None},
)

ECHO_OUTPUT: StaticSchema = (
    18,
    n0,
    _s50,
    {_s1: _s49, _s12: None},
)

PING_INPUT: StaticSchema = (
    18,
    n0,
    _s51,
    {_s1: _s49, _s3: None},
)

PING_OUTPUT: StaticSchema = (
    18,
    n0,
    _s52,
    {_s1: _s49, _s12: None},
)

PUT_THING_OUTPUT: StaticSchema = (
    18,
    n0,
    _s53,
    {_s1: _s49, _s12: None},
)

ECHO: StaticOperationSchema = (
    23,
    n0,
    _s54,
    0,
    ECHO_INPUT,
    ECHO_OUTPUT,
    (),
)

GET_NOTE: StaticOperationSchema = (
    23,
    n0,
    _s55,
    {
        _s56: MappingProxyType(
            {
                "NoteSaved": MappingProxyType(
                    {
                        "documentation": "Waits until the note is saved.",
                        "minDelay": 1,
                        "maxDelay": 4,
                        "acceptors": (
                            MappingProxyType(
                                {
                                    "state": "success",
                                    "matcher": MappingProxyType(
                                        {
                                            "output": MappingProxyType(
                                                {
                                                    "path": "state",
                                                    "expected": "SAVED",
                                                    "comparator": "stringEquals",
                                                }
                                            )
                                        }
                                    ),
                                }
                            ),
                            MappingProxyType(
                                {
                                    "state": "failure",
                                    "matcher": MappingProxyType(
                                        {
                                            "output": MappingProxyType(
                                                {
                                                    "path": "state",
                                                    "expected": "REJECTED",
                                                    "comparator": "stringEquals",
                                                }
                                            )
                                        }
                                    ),
                                    "message": "reason",
                                }
                            ),
                            MappingProxyType(
                                {
                                    "state": "retry",
                                    "matcher": MappingProxyType(
                                        {"errorType": "NoteNotFound"}
                                    ),
                                }
                            ),
                        ),
                    }
                ),
                "NoteDeleted": MappingProxyType(
                    {
                        "acceptors": (
                            MappingProxyType(
                                {
                                    "state": "success",
                                    "matcher": MappingProxyType(
                                        {"errorType": "NoteNotFound"}
                                    ),
                                }
                            ),
                        )
                    }
                ),
            }
        )
    },
    GET_NOTE_INPUT,
    GET_NOTE_OUTPUT,
    (NOTE_NOT_FOUND,),
)

GET_THING: StaticOperationSchema = (
    23,
    n0,
    _s57,
    0,
    GET_THING_INPUT,
    GET_THING_OUTPUT,
    (),
)

LIST_NOTES: StaticOperationSchema = (
    23,
    n0,
    _s58,
    {_s59: MappingProxyType({"Kind": MappingProxyType({"value": "list"})})},
    LIST_NOTES_INPUT,
    LIST_NOTES_OUTPUT,
    (),
)

PING: StaticOperationSchema = (
    23,
    n0,
    _s60,
    {_s59: MappingProxyType({"Kind": MappingProxyType({"value": "ping"})})},
    PING_INPUT,
    PING_OUTPUT,
    (),
)

PUT_NOTE: StaticOperationSchema = (
    23,
    n0,
    _s61,
    0,
    PUT_NOTE_INPUT,
    PUT_NOTE_OUTPUT,
    (),
)

PUT_THING: StaticOperationSchema = (
    23,
    n0,
    _s62,
    {_s59: MappingProxyType({"Kind": MappingProxyType({"value": "put"})})},
    PUT_THING_INPUT,
    PUT_THING_OUTPUT,
    (),
)

FIELD_NOTES: StaticSchema = (
    21,
    n0,
    _s63,
    {_s64: MappingProxyType({"sdkId": "Field Notes"}), _s65: None},
)
