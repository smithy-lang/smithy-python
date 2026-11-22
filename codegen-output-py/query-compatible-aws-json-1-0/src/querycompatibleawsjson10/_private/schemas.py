from types import MappingProxyType

from smithy_core._schema_compact import StaticSchema

n0 = "aws.protocoltests.json10"
_s0 = "CustomCodeError"
_s1 = "aws.protocols#awsQueryError"
_s2 = "smithy.api#error"
_s3 = "client"
_s4 = "message"
_s5 = "NoCustomCodeError"

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
