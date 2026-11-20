from types import MappingProxyType

from smithy_core._schema_compact import StaticOperationSchema, StaticSchema

n0 = "example.sigv4"
_s0 = "PutNoteInput"
_s1 = "smithy.synthetic#originalShapeId"
_s2 = "example.sigv4#PutNoteInput"
_s3 = "smithy.api#input"
_s4 = "text"
_s5 = "PutNoteOutput"
_s6 = "example.sigv4#PutNoteOutput"
_s7 = "smithy.api#output"
_s8 = "id"
_s9 = "HealthInput"
_s10 = "smithy.api#Unit"
_s11 = "HealthOutput"
_s12 = "Health"
_s13 = "PutNote"
_s14 = "FieldNotes"
_s15 = "aws.api#service"
_s16 = "smithy.protocols#rpcv2Cbor"

PUT_NOTE_INPUT: StaticSchema = (
    18,
    n0,
    _s0,
    {_s1: _s2, _s3: None},
    (_s4,),
    ((3, 0),),
)

PUT_NOTE_OUTPUT: StaticSchema = (
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

HEALTH: StaticOperationSchema = (
    23,
    n0,
    _s12,
    0,
    HEALTH_INPUT,
    HEALTH_OUTPUT,
    (),
)

PUT_NOTE: StaticOperationSchema = (
    23,
    n0,
    _s13,
    0,
    PUT_NOTE_INPUT,
    PUT_NOTE_OUTPUT,
    (),
)

FIELD_NOTES: StaticSchema = (
    21,
    n0,
    _s14,
    {_s15: MappingProxyType({"sdkId": "Field Notes"}), _s16: None},
)
