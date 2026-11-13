from smithy_core._schema_compact import StaticSchema

n0 = "aws.protocoltests.rpcv2cbor"
_s0 = "CustomCodeError"
_s1 = "smithy.api#error"
_s2 = "client"
_s3 = "message"
_s4 = "NoCustomCodeError"

CUSTOM_CODE_ERROR: StaticSchema = (
    18,
    n0,
    _s0,
    {_s1: _s2},
    (_s3,),
    ((3, 0),),
)

NO_CUSTOM_CODE_ERROR: StaticSchema = (
    18,
    n0,
    _s4,
    {_s1: _s2},
    (_s3,),
    ((3, 0),),
)
