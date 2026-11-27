from types import MappingProxyType

from smithy_core._schema_compact import StaticOperationSchema, StaticSchema

n0 = "example.features"
_s0 = "DescribeNoteInput"
_s1 = "smithy.synthetic#originalShapeId"
_s2 = "example.features#DescribeNoteInput"
_s3 = "smithy.api#input"
_s4 = "id"
_s5 = "NoteState"
_s6 = "DRAFT"
_s7 = "smithy.api#enumValue"
_s8 = "SAVED"
_s9 = "REJECTED"
_s10 = "DescribeNoteOutput"
_s11 = "example.features#DescribeNoteOutput"
_s12 = "smithy.api#output"
_s13 = "state"
_s14 = "reason"
_s15 = "GetNoteInput"
_s16 = "example.features#GetNoteInput"
_s17 = "GetNoteOutput"
_s18 = "example.features#GetNoteOutput"
_s19 = "text"
_s20 = "GetThingInput"
_s21 = "example.features#GetThingInput"
_s22 = "name"
_s23 = "GetThingOutput"
_s24 = "example.features#GetThingOutput"
_s25 = "value"
_s26 = "ListNotesInput"
_s27 = "example.features#ListNotesInput"
_s28 = "nextToken"
_s29 = "pageSize"
_s30 = "NoteList"
_s31 = "member"
_s32 = "ListNotesOutput"
_s33 = "example.features#ListNotesOutput"
_s34 = "items"
_s35 = "NoteNotFound"
_s36 = "smithy.api#error"
_s37 = "client"
_s38 = "message"
_s39 = "PluginNames"
_s40 = "PutNoteInput"
_s41 = "example.features#PutNoteInput"
_s42 = "PutNoteOutput"
_s43 = "example.features#PutNoteOutput"
_s44 = "ThingTag"
_s45 = "key"
_s46 = "PutThingInput"
_s47 = "example.features#PutThingInput"
_s48 = "smithy.rules#contextParam"
_s49 = "smithy.api#required"
_s50 = "tag"
_s51 = "plugins"
_s52 = "EchoInput"
_s53 = "smithy.api#Unit"
_s54 = "EchoOutput"
_s55 = "PingInput"
_s56 = "PingOutput"
_s57 = "PutThingOutput"
_s58 = "DescribeNote"
_s59 = "smithy.waiters#waitable"
_s60 = "Echo"
_s61 = "GetNote"
_s62 = "GetThing"
_s63 = "ListNotes"
_s64 = "smithy.rules#staticContextParams"
_s65 = "Ping"
_s66 = "PutNote"
_s67 = "PutThing"
_s68 = "FieldNotes"
_s69 = "aws.api#service"
_s70 = "smithy.protocols#rpcv2Cbor"

DESCRIBE_NOTE_INPUT: StaticSchema = (
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

DESCRIBE_NOTE_OUTPUT: StaticSchema = (
    18,
    n0,
    _s10,
    {_s1: _s11, _s12: None},
    (_s4, _s13, _s14),
    ((3, 0), (NOTE_STATE, 0), (3, 0)),
)

GET_NOTE_INPUT: StaticSchema = (
    18,
    n0,
    _s15,
    {_s1: _s16, _s3: None},
    (_s4,),
    ((3, 0),),
)

GET_NOTE_OUTPUT: StaticSchema = (
    18,
    n0,
    _s17,
    {_s1: _s18, _s12: None},
    (_s19,),
    ((3, 0),),
)

GET_THING_INPUT: StaticSchema = (
    18,
    n0,
    _s20,
    {_s1: _s21, _s3: None},
    (_s22,),
    ((3, 0),),
)

GET_THING_OUTPUT: StaticSchema = (
    18,
    n0,
    _s23,
    {_s1: _s24, _s12: None},
    (_s25,),
    ((3, 0),),
)

LIST_NOTES_INPUT: StaticSchema = (
    18,
    n0,
    _s26,
    {_s1: _s27, _s3: None},
    (_s28, _s29),
    ((3, 0), (7, 0)),
)

NOTE_LIST: StaticSchema = (
    16,
    n0,
    _s30,
    0,
    (_s31,),
    ((3, 0),),
)

LIST_NOTES_OUTPUT: StaticSchema = (
    18,
    n0,
    _s32,
    {_s1: _s33, _s12: None},
    (_s34, _s28),
    ((NOTE_LIST, 0), (3, 0)),
)

NOTE_NOT_FOUND: StaticSchema = (
    18,
    n0,
    _s35,
    {_s36: _s37},
    (_s38,),
    ((3, 0),),
)

PLUGIN_NAMES: StaticSchema = (
    16,
    n0,
    _s39,
    0,
    (_s31,),
    ((3, 0),),
)

PUT_NOTE_INPUT: StaticSchema = (
    18,
    n0,
    _s40,
    {_s1: _s41, _s3: None},
    (_s19,),
    ((3, 0),),
)

PUT_NOTE_OUTPUT: StaticSchema = (
    18,
    n0,
    _s42,
    {_s1: _s43, _s12: None},
    (_s4,),
    ((3, 0),),
)

THING_TAG: StaticSchema = (
    18,
    n0,
    _s44,
    0,
    (_s45, _s25),
    ((3, 0), (3, 0)),
)

PUT_THING_INPUT: StaticSchema = (
    18,
    n0,
    _s46,
    {_s1: _s47, _s3: None},
    (_s22, _s50, _s51),
    (
        (3, {_s48: MappingProxyType({"name": "Name"}), _s49: None}),
        (THING_TAG, 0),
        (PLUGIN_NAMES, 0),
    ),
)

ECHO_INPUT: StaticSchema = (
    18,
    n0,
    _s52,
    {_s1: _s53, _s3: None},
)

ECHO_OUTPUT: StaticSchema = (
    18,
    n0,
    _s54,
    {_s1: _s53, _s12: None},
)

PING_INPUT: StaticSchema = (
    18,
    n0,
    _s55,
    {_s1: _s53, _s3: None},
)

PING_OUTPUT: StaticSchema = (
    18,
    n0,
    _s56,
    {_s1: _s53, _s12: None},
)

PUT_THING_OUTPUT: StaticSchema = (
    18,
    n0,
    _s57,
    {_s1: _s53, _s12: None},
)

DESCRIBE_NOTE: StaticOperationSchema = (
    23,
    n0,
    _s58,
    {
        _s59: MappingProxyType(
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
    DESCRIBE_NOTE_INPUT,
    DESCRIBE_NOTE_OUTPUT,
    (NOTE_NOT_FOUND,),
)

ECHO: StaticOperationSchema = (
    23,
    n0,
    _s60,
    0,
    ECHO_INPUT,
    ECHO_OUTPUT,
    (),
)

GET_NOTE: StaticOperationSchema = (
    23,
    n0,
    _s61,
    0,
    GET_NOTE_INPUT,
    GET_NOTE_OUTPUT,
    (),
)

GET_THING: StaticOperationSchema = (
    23,
    n0,
    _s62,
    0,
    GET_THING_INPUT,
    GET_THING_OUTPUT,
    (),
)

LIST_NOTES: StaticOperationSchema = (
    23,
    n0,
    _s63,
    {_s64: MappingProxyType({"Kind": MappingProxyType({"value": "list"})})},
    LIST_NOTES_INPUT,
    LIST_NOTES_OUTPUT,
    (),
)

PING: StaticOperationSchema = (
    23,
    n0,
    _s65,
    {_s64: MappingProxyType({"Kind": MappingProxyType({"value": "ping"})})},
    PING_INPUT,
    PING_OUTPUT,
    (),
)

PUT_NOTE: StaticOperationSchema = (
    23,
    n0,
    _s66,
    0,
    PUT_NOTE_INPUT,
    PUT_NOTE_OUTPUT,
    (),
)

PUT_THING: StaticOperationSchema = (
    23,
    n0,
    _s67,
    {_s64: MappingProxyType({"Kind": MappingProxyType({"value": "put"})})},
    PUT_THING_INPUT,
    PUT_THING_OUTPUT,
    (),
)

FIELD_NOTES: StaticSchema = (
    21,
    n0,
    _s68,
    {_s69: MappingProxyType({"sdkId": "Field Notes"}), _s70: None},
)
