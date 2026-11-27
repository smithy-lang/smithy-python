from types import MappingProxyType

from smithy_core._schema_compact import StaticOperationSchema, StaticSchema

n0 = "example.features"
_s0 = "ChecksumAlgorithm"
_s1 = "CRC32"
_s2 = "smithy.api#enumValue"
_s3 = "SHA256"
_s4 = "ChecksumMode"
_s5 = "ENABLED"
_s6 = "DescribeNoteInput"
_s7 = "smithy.synthetic#originalShapeId"
_s8 = "example.features#DescribeNoteInput"
_s9 = "smithy.api#input"
_s10 = "id"
_s11 = "NoteState"
_s12 = "DRAFT"
_s13 = "SAVED"
_s14 = "REJECTED"
_s15 = "DescribeNoteOutput"
_s16 = "example.features#DescribeNoteOutput"
_s17 = "smithy.api#output"
_s18 = "state"
_s19 = "reason"
_s20 = "GetNoteInput"
_s21 = "example.features#GetNoteInput"
_s22 = "checksumMode"
_s23 = "GetNoteOutput"
_s24 = "example.features#GetNoteOutput"
_s25 = "text"
_s26 = "GetThingInput"
_s27 = "example.features#GetThingInput"
_s28 = "name"
_s29 = "GetThingOutput"
_s30 = "example.features#GetThingOutput"
_s31 = "value"
_s32 = "ListNotesInput"
_s33 = "example.features#ListNotesInput"
_s34 = "nextToken"
_s35 = "pageSize"
_s36 = "NoteList"
_s37 = "member"
_s38 = "ListNotesOutput"
_s39 = "example.features#ListNotesOutput"
_s40 = "items"
_s41 = "NoteNotFound"
_s42 = "smithy.api#error"
_s43 = "client"
_s44 = "message"
_s45 = "PluginNames"
_s46 = "PutNoteInput"
_s47 = "example.features#PutNoteInput"
_s48 = "checksumAlgorithm"
_s49 = "PutNoteOutput"
_s50 = "example.features#PutNoteOutput"
_s51 = "ThingTag"
_s52 = "key"
_s53 = "PutThingInput"
_s54 = "example.features#PutThingInput"
_s55 = "smithy.rules#contextParam"
_s56 = "smithy.api#required"
_s57 = "tag"
_s58 = "plugins"
_s59 = "EchoInput"
_s60 = "smithy.api#Unit"
_s61 = "EchoOutput"
_s62 = "PingInput"
_s63 = "PingOutput"
_s64 = "PutThingOutput"
_s65 = "DescribeNote"
_s66 = "smithy.waiters#waitable"
_s67 = "Echo"
_s68 = "GetNote"
_s69 = "aws.protocols#httpChecksum"
_s70 = "GetThing"
_s71 = "ListNotes"
_s72 = "smithy.rules#staticContextParams"
_s73 = "Ping"
_s74 = "PutNote"
_s75 = "PutThing"
_s76 = "FieldNotes"
_s77 = "aws.api#service"
_s78 = "smithy.protocols#rpcv2Cbor"

CHECKSUM_ALGORITHM: StaticSchema = (
    14,
    n0,
    _s0,
    0,
    (_s1, _s3),
    ((-1, {_s2: _s1}), (-1, {_s2: _s3})),
)

CHECKSUM_MODE: StaticSchema = (
    14,
    n0,
    _s4,
    0,
    (_s5,),
    ((-1, {_s2: _s5}),),
)

DESCRIBE_NOTE_INPUT: StaticSchema = (
    18,
    n0,
    _s6,
    {_s7: _s8, _s9: None},
    (_s10,),
    ((3, 1),),
)

NOTE_STATE: StaticSchema = (
    14,
    n0,
    _s11,
    0,
    (_s12, _s13, _s14),
    ((-1, {_s2: _s12}), (-1, {_s2: _s13}), (-1, {_s2: _s14})),
)

DESCRIBE_NOTE_OUTPUT: StaticSchema = (
    18,
    n0,
    _s15,
    {_s7: _s16, _s17: None},
    (_s10, _s18, _s19),
    ((3, 0), (NOTE_STATE, 0), (3, 0)),
)

GET_NOTE_INPUT: StaticSchema = (
    18,
    n0,
    _s20,
    {_s7: _s21, _s9: None},
    (_s10, _s22),
    ((3, 0), (CHECKSUM_MODE, 0)),
)

GET_NOTE_OUTPUT: StaticSchema = (
    18,
    n0,
    _s23,
    {_s7: _s24, _s17: None},
    (_s25,),
    ((3, 0),),
)

GET_THING_INPUT: StaticSchema = (
    18,
    n0,
    _s26,
    {_s7: _s27, _s9: None},
    (_s28,),
    ((3, 0),),
)

GET_THING_OUTPUT: StaticSchema = (
    18,
    n0,
    _s29,
    {_s7: _s30, _s17: None},
    (_s31,),
    ((3, 0),),
)

LIST_NOTES_INPUT: StaticSchema = (
    18,
    n0,
    _s32,
    {_s7: _s33, _s9: None},
    (_s34, _s35),
    ((3, 0), (7, 0)),
)

NOTE_LIST: StaticSchema = (
    16,
    n0,
    _s36,
    0,
    (_s37,),
    ((3, 0),),
)

LIST_NOTES_OUTPUT: StaticSchema = (
    18,
    n0,
    _s38,
    {_s7: _s39, _s17: None},
    (_s40, _s34),
    ((NOTE_LIST, 0), (3, 0)),
)

NOTE_NOT_FOUND: StaticSchema = (
    18,
    n0,
    _s41,
    {_s42: _s43},
    (_s44,),
    ((3, 0),),
)

PLUGIN_NAMES: StaticSchema = (
    16,
    n0,
    _s45,
    0,
    (_s37,),
    ((3, 0),),
)

PUT_NOTE_INPUT: StaticSchema = (
    18,
    n0,
    _s46,
    {_s7: _s47, _s9: None},
    (_s25, _s48),
    ((3, 0), (CHECKSUM_ALGORITHM, 0)),
)

PUT_NOTE_OUTPUT: StaticSchema = (
    18,
    n0,
    _s49,
    {_s7: _s50, _s17: None},
    (_s10,),
    ((3, 0),),
)

THING_TAG: StaticSchema = (
    18,
    n0,
    _s51,
    0,
    (_s52, _s31),
    ((3, 0), (3, 0)),
)

PUT_THING_INPUT: StaticSchema = (
    18,
    n0,
    _s53,
    {_s7: _s54, _s9: None},
    (_s28, _s57, _s58),
    (
        (3, {_s55: MappingProxyType({"name": "Name"}), _s56: None}),
        (THING_TAG, 0),
        (PLUGIN_NAMES, 0),
    ),
)

ECHO_INPUT: StaticSchema = (
    18,
    n0,
    _s59,
    {_s7: _s60, _s9: None},
)

ECHO_OUTPUT: StaticSchema = (
    18,
    n0,
    _s61,
    {_s7: _s60, _s17: None},
)

PING_INPUT: StaticSchema = (
    18,
    n0,
    _s62,
    {_s7: _s60, _s9: None},
)

PING_OUTPUT: StaticSchema = (
    18,
    n0,
    _s63,
    {_s7: _s60, _s17: None},
)

PUT_THING_OUTPUT: StaticSchema = (
    18,
    n0,
    _s64,
    {_s7: _s60, _s17: None},
)

DESCRIBE_NOTE: StaticOperationSchema = (
    23,
    n0,
    _s65,
    {
        _s66: MappingProxyType(
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
    _s67,
    0,
    ECHO_INPUT,
    ECHO_OUTPUT,
    (),
)

GET_NOTE: StaticOperationSchema = (
    23,
    n0,
    _s68,
    {
        _s69: MappingProxyType(
            {
                "requestValidationModeMember": "checksumMode",
                "responseAlgorithms": ("CRC32",),
            }
        )
    },
    GET_NOTE_INPUT,
    GET_NOTE_OUTPUT,
    (),
)

GET_THING: StaticOperationSchema = (
    23,
    n0,
    _s70,
    0,
    GET_THING_INPUT,
    GET_THING_OUTPUT,
    (),
)

LIST_NOTES: StaticOperationSchema = (
    23,
    n0,
    _s71,
    {_s72: MappingProxyType({"Kind": MappingProxyType({"value": "list"})})},
    LIST_NOTES_INPUT,
    LIST_NOTES_OUTPUT,
    (),
)

PING: StaticOperationSchema = (
    23,
    n0,
    _s73,
    {_s72: MappingProxyType({"Kind": MappingProxyType({"value": "ping"})})},
    PING_INPUT,
    PING_OUTPUT,
    (),
)

PUT_NOTE: StaticOperationSchema = (
    23,
    n0,
    _s74,
    {
        _s69: MappingProxyType(
            {
                "requestChecksumRequired": True,
                "requestAlgorithmMember": "checksumAlgorithm",
            }
        )
    },
    PUT_NOTE_INPUT,
    PUT_NOTE_OUTPUT,
    (),
)

PUT_THING: StaticOperationSchema = (
    23,
    n0,
    _s75,
    {_s72: MappingProxyType({"Kind": MappingProxyType({"value": "put"})})},
    PUT_THING_INPUT,
    PUT_THING_OUTPUT,
    (),
)

FIELD_NOTES: StaticSchema = (
    21,
    n0,
    _s76,
    {_s77: MappingProxyType({"sdkId": "Field Notes"}), _s78: None},
)
