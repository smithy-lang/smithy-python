from types import MappingProxyType

from smithy_core._schema_compact import StaticOperationSchema, StaticSchema

n0 = "aws.protocoltests.json10"
_s0 = "CustomCodeError"
_s1 = "aws.protocols#awsQueryError"
_s2 = "smithy.api#error"
_s3 = "client"
_s4 = "message"
_s5 = "NoCustomCodeError"
_s6 = "QueryCompatibleOperationInput"
_s7 = "smithy.synthetic#originalShapeId"
_s8 = "smithy.api#Unit"
_s9 = "smithy.api#input"
_s10 = "QueryCompatibleOperationOutput"
_s11 = "smithy.api#output"
_s12 = "QueryCompatibleOperation"
_s13 = "QueryCompatibleJsonRpc10"
_s14 = "aws.api#service"
_s15 = "aws.auth#sigv4"
_s16 = "aws.protocols#awsJson1_0"
_s17 = "aws.protocols#awsQueryCompatible"

CUSTOM_CODE_ERROR: StaticSchema = (
    18,
    n0,
    _s0,
    {_s1: MappingProxyType({"code": "Customized", "httpResponseCode": 402}), _s2: _s3},
    (_s4,),
    ((3, 0),),
)

NO_CUSTOM_CODE_ERROR: StaticSchema = (
    18,
    n0,
    _s5,
    {_s2: _s3},
    (_s4,),
    ((3, 0),),
)

QUERY_COMPATIBLE_OPERATION_INPUT: StaticSchema = (
    18,
    n0,
    _s6,
    {_s7: _s8, _s9: None},
)

QUERY_COMPATIBLE_OPERATION_OUTPUT: StaticSchema = (
    18,
    n0,
    _s10,
    {_s7: _s8, _s11: None},
)

QUERY_COMPATIBLE_OPERATION: StaticOperationSchema = (
    23,
    n0,
    _s12,
    0,
    QUERY_COMPATIBLE_OPERATION_INPUT,
    QUERY_COMPATIBLE_OPERATION_OUTPUT,
    (CUSTOM_CODE_ERROR, NO_CUSTOM_CODE_ERROR),
)

QUERY_COMPATIBLE_JSON_RPC10: StaticSchema = (
    21,
    n0,
    _s13,
    {
        _s14: MappingProxyType({"sdkId": "Query Compatible JSON RPC 10"}),
        _s15: MappingProxyType({"name": "querycompatiblejsonrpc10"}),
        _s16: None,
        _s17: None,
    },
)
