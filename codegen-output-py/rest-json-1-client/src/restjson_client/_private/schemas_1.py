from types import MappingProxyType

from smithy_core._schema_compact import StaticOperationSchema, StaticSchema

from . import schemas

_s0 = "StringList"
_s1 = "member"
_s3 = "IntegerList"
_s5 = "DoubleList"
_s6 = "BooleanList"
_s7 = "TimestampList"
_s25 = "IntegerEnumList"
_s27 = "key"
_s28 = "value"
n1 = "aws.protocoltests.restjson"
_s30 = "smithy.synthetic#originalShapeId"
_s32 = "smithy.api#input"
_s34 = "smithy.api#httpQuery"
_s36 = "queryStringList"
_s44 = "queryIntegerList"
_s52 = "queryDoubleList"
_s55 = "queryBooleanList"
_s58 = "queryTimestampList"
_s61 = "queryEnumList"
_s62 = "EnumList"
_s64 = "queryIntegerEnumList"
_s77 = "smithy.api#httpHeader"
_s92 = "smithy.api#output"
_s94 = "smithy.api#timestampFormat"
_s95 = "date-time"
_s127 = "emptyString"
_s141 = "GreetingStruct"
_s148 = "greeting"
_s189 = "float"
_s194 = "epoch-seconds"
_s196 = "http-date"
_s200 = "smithy.api#httpLabel"
_s201 = "smithy.api#required"
_s210 = "string"
_s215 = "timestamp"
_s232 = "payload"
_s237 = "MalformedBlobInput"
_s238 = "aws.protocoltests.restjson#MalformedBlobInput"
_s239 = "blob"
_s240 = "MalformedBooleanInput"
_s241 = "aws.protocoltests.restjson#MalformedBooleanInput"
_s242 = "booleanInBody"
_s243 = "booleanInPath"
_s244 = "booleanInQuery"
_s245 = "booleanInHeader"
_s246 = "MalformedByteInput"
_s247 = "aws.protocoltests.restjson#MalformedByteInput"
_s248 = "byteInBody"
_s249 = "byteInPath"
_s250 = "byteInQuery"
_s251 = "byteInHeader"
_s252 = "MalformedContentTypeWithGenericStringInput"
_s253 = "aws.protocoltests.restjson#MalformedContentTypeWithGenericStringInput"
_s254 = "MalformedContentTypeWithPayloadInput"
_s255 = "aws.protocoltests.restjson#MalformedContentTypeWithPayloadInput"
_s256 = "MalformedContentTypeWithoutBodyEmptyInputInput"
_s257 = "aws.protocoltests.restjson#MalformedContentTypeWithoutBodyEmptyInputInput"
_s258 = "header"
_s259 = "MalformedDoubleInput"
_s260 = "aws.protocoltests.restjson#MalformedDoubleInput"
_s261 = "doubleInBody"
_s262 = "doubleInPath"
_s263 = "doubleInQuery"
_s264 = "doubleInHeader"
_s265 = "MalformedFloatInput"
_s266 = "aws.protocoltests.restjson#MalformedFloatInput"
_s267 = "floatInBody"
_s268 = "floatInPath"
_s269 = "floatInQuery"
_s270 = "floatInHeader"
_s271 = "MalformedIntegerInput"
_s272 = "aws.protocoltests.restjson#MalformedIntegerInput"
_s273 = "integerInBody"
_s274 = "integerInPath"
_s275 = "integerInQuery"
_s276 = "integerInHeader"
_s277 = "SimpleList"
_s278 = "MalformedListInput"
_s279 = "aws.protocoltests.restjson#MalformedListInput"
_s280 = "bodyList"
_s281 = "MalformedLongInput"
_s282 = "aws.protocoltests.restjson#MalformedLongInput"
_s283 = "longInBody"
_s284 = "longInPath"
_s285 = "longInQuery"
_s286 = "longInHeader"
_s287 = "SimpleMap"
_s288 = "MalformedMapInput"
_s289 = "aws.protocoltests.restjson#MalformedMapInput"
_s290 = "bodyMap"
_s291 = "MalformedRequestBodyInput"
_s292 = "aws.protocoltests.restjson#MalformedRequestBodyInput"
_s293 = "int"
_s294 = "MalformedShortInput"
_s295 = "aws.protocoltests.restjson#MalformedShortInput"
_s296 = "shortInBody"
_s297 = "shortInPath"
_s298 = "shortInQuery"
_s299 = "shortInHeader"
_s300 = "MalformedStringInput"
_s301 = "aws.protocoltests.restjson#MalformedStringInput"
_s302 = "amz-media-typed-header"
_s303 = "MalformedTimestampBodyDateTimeInput"
_s304 = "aws.protocoltests.restjson#MalformedTimestampBodyDateTimeInput"
_s305 = "MalformedTimestampBodyDefaultInput"
_s306 = "aws.protocoltests.restjson#MalformedTimestampBodyDefaultInput"
_s307 = "MalformedTimestampBodyHttpDateInput"
_s308 = "aws.protocoltests.restjson#MalformedTimestampBodyHttpDateInput"
_s309 = "MalformedTimestampHeaderDateTimeInput"
_s310 = "aws.protocoltests.restjson#MalformedTimestampHeaderDateTimeInput"
_s311 = "MalformedTimestampHeaderDefaultInput"
_s312 = "aws.protocoltests.restjson#MalformedTimestampHeaderDefaultInput"
_s313 = "MalformedTimestampHeaderEpochInput"
_s314 = "aws.protocoltests.restjson#MalformedTimestampHeaderEpochInput"
_s315 = "MalformedTimestampPathDefaultInput"
_s316 = "aws.protocoltests.restjson#MalformedTimestampPathDefaultInput"
_s317 = "MalformedTimestampPathEpochInput"
_s318 = "aws.protocoltests.restjson#MalformedTimestampPathEpochInput"
_s319 = "MalformedTimestampPathHttpDateInput"
_s320 = "aws.protocoltests.restjson#MalformedTimestampPathHttpDateInput"
_s321 = "MalformedTimestampQueryDefaultInput"
_s322 = "aws.protocoltests.restjson#MalformedTimestampQueryDefaultInput"
_s323 = "MalformedTimestampQueryEpochInput"
_s324 = "aws.protocoltests.restjson#MalformedTimestampQueryEpochInput"
_s325 = "MalformedTimestampQueryHttpDateInput"
_s326 = "aws.protocoltests.restjson#MalformedTimestampQueryHttpDateInput"
_s327 = "SimpleUnion"
_s328 = "MalformedUnionInput"
_s329 = "aws.protocoltests.restjson#MalformedUnionInput"
_s330 = "union"
_s331 = "MediaTypeHeaderInput"
_s332 = "aws.protocoltests.restjson#MediaTypeHeaderInput"
_s333 = "json"
_s334 = "X-Json"
_s335 = "MediaTypeHeaderOutput"
_s336 = "aws.protocoltests.restjson#MediaTypeHeaderOutput"
n2 = "aws.protocoltests.restjson.nested"
_s337 = "salutation"
_s338 = "NestedUnion"
_s339 = "stringValue"
_s340 = "MyUnion"
_s341 = "booleanValue"
_s342 = "numberValue"
_s343 = "blobValue"
_s344 = "timestampValue"
_s345 = "enumValue"
_s346 = "listValue"
_s347 = "mapValue"
_s348 = "structureValue"
_s349 = "renamedStructureValue"
_s350 = "unionValue"
_s351 = "NestedPayload"
_s352 = "name"
_s353 = "NoInputAndOutputOutput"
_s354 = "aws.protocoltests.restjson#NoInputAndOutputOutput"
_s355 = "OmitsNullSerializesEmptyStringInput"
_s356 = "aws.protocoltests.restjson#OmitsNullSerializesEmptyStringInput"
_s357 = "nullValue"
_s358 = "Null"
_s359 = "Empty"
_s360 = "OmitsSerializingEmptyListsInput"
_s361 = "aws.protocoltests.restjson#OmitsSerializingEmptyListsInput"
_s444 = "smithy.api#Unit"
_s602 = "MalformedBlobOutput"
_s603 = "MalformedBooleanOutput"
_s604 = "MalformedByteOutput"
_s607 = "MalformedContentTypeWithGenericStringOutput"
_s608 = "MalformedContentTypeWithPayloadOutput"
_s611 = "MalformedContentTypeWithoutBodyEmptyInputOutput"
_s612 = "MalformedDoubleOutput"
_s613 = "MalformedFloatOutput"
_s614 = "MalformedIntegerOutput"
_s615 = "MalformedListOutput"
_s616 = "MalformedLongOutput"
_s617 = "MalformedMapOutput"
_s618 = "MalformedRequestBodyOutput"
_s619 = "MalformedShortOutput"
_s620 = "MalformedStringOutput"
_s621 = "MalformedTimestampBodyDateTimeOutput"
_s622 = "MalformedTimestampBodyDefaultOutput"
_s623 = "MalformedTimestampBodyHttpDateOutput"
_s624 = "MalformedTimestampHeaderDateTimeOutput"
_s625 = "MalformedTimestampHeaderDefaultOutput"
_s626 = "MalformedTimestampHeaderEpochOutput"
_s627 = "MalformedTimestampPathDefaultOutput"
_s628 = "MalformedTimestampPathEpochOutput"
_s629 = "MalformedTimestampPathHttpDateOutput"
_s630 = "MalformedTimestampQueryDefaultOutput"
_s631 = "MalformedTimestampQueryEpochOutput"
_s632 = "MalformedTimestampQueryHttpDateOutput"
_s633 = "MalformedUnionOutput"
_s636 = "NoInputAndOutputInput"
_s646 = "OmitsNullSerializesEmptyStringOutput"
_s647 = "OmitsSerializingEmptyListsOutput"
_s729 = "smithy.api#http"
_s774 = "MalformedBlob"
_s775 = "MalformedBoolean"
_s776 = "MalformedByte"
_s778 = "MalformedContentTypeWithGenericString"
_s779 = "MalformedContentTypeWithPayload"
_s781 = "MalformedContentTypeWithoutBodyEmptyInput"
_s782 = "MalformedDouble"
_s783 = "MalformedFloat"
_s784 = "MalformedInteger"
_s785 = "MalformedList"
_s786 = "MalformedLong"
_s787 = "MalformedMap"
_s788 = "MalformedRequestBody"
_s789 = "MalformedShort"
_s790 = "MalformedString"
_s791 = "MalformedTimestampBodyDateTime"
_s792 = "MalformedTimestampBodyDefault"
_s793 = "MalformedTimestampBodyHttpDate"
_s794 = "MalformedTimestampHeaderDateTime"
_s795 = "MalformedTimestampHeaderDefault"
_s796 = "MalformedTimestampHeaderEpoch"
_s797 = "MalformedTimestampPathDefault"
_s798 = "MalformedTimestampPathEpoch"
_s799 = "MalformedTimestampPathHttpDate"
_s800 = "MalformedTimestampQueryDefault"
_s801 = "MalformedTimestampQueryEpoch"
_s802 = "MalformedTimestampQueryHttpDate"
_s803 = "MalformedUnion"
_s804 = "MediaTypeHeader"
_s806 = "NoInputAndOutput"
_s809 = "OmitsNullSerializesEmptyString"
_s810 = "OmitsSerializingEmptyLists"

MALFORMED_BLOB_INPUT: StaticSchema = (
    18,
    n1,
    _s237,
    {_s30: _s238, _s32: None},
    (_s239,),
    ((1, 0),),
)

MALFORMED_BLOB_OUTPUT: StaticSchema = (
    18,
    n1,
    _s602,
    {_s30: _s444, _s92: None},
)

MALFORMED_BLOB: StaticOperationSchema = (
    23,
    n1,
    _s774,
    {_s729: MappingProxyType({"uri": "/MalformedBlob", "method": "POST"})},
    MALFORMED_BLOB_INPUT,
    MALFORMED_BLOB_OUTPUT,
    (),
)

MALFORMED_BOOLEAN_INPUT: StaticSchema = (
    18,
    n1,
    _s240,
    {_s30: _s241, _s32: None},
    (_s242, _s243, _s244, _s245),
    ((2, 0), (2, 9), (2, {_s34: _s244}), (2, {_s77: _s245})),
)

MALFORMED_BOOLEAN_OUTPUT: StaticSchema = (
    18,
    n1,
    _s603,
    {_s30: _s444, _s92: None},
)

MALFORMED_BOOLEAN: StaticOperationSchema = (
    23,
    n1,
    _s775,
    {
        _s729: MappingProxyType(
            {"uri": "/MalformedBoolean/{booleanInPath}", "method": "POST"}
        )
    },
    MALFORMED_BOOLEAN_INPUT,
    MALFORMED_BOOLEAN_OUTPUT,
    (),
)

MALFORMED_BYTE_INPUT: StaticSchema = (
    18,
    n1,
    _s246,
    {_s30: _s247, _s32: None},
    (_s248, _s249, _s250, _s251),
    ((5, 0), (5, 9), (5, {_s34: _s250}), (5, {_s77: _s251})),
)

MALFORMED_BYTE_OUTPUT: StaticSchema = (
    18,
    n1,
    _s604,
    {_s30: _s444, _s92: None},
)

MALFORMED_BYTE: StaticOperationSchema = (
    23,
    n1,
    _s776,
    {_s729: MappingProxyType({"uri": "/MalformedByte/{byteInPath}", "method": "POST"})},
    MALFORMED_BYTE_INPUT,
    MALFORMED_BYTE_OUTPUT,
    (),
)

MALFORMED_CONTENT_TYPE_WITH_GENERIC_STRING_INPUT: StaticSchema = (
    18,
    n1,
    _s252,
    {_s30: _s253, _s32: None},
    (_s232,),
    ((3, 16),),
)

MALFORMED_CONTENT_TYPE_WITH_GENERIC_STRING_OUTPUT: StaticSchema = (
    18,
    n1,
    _s607,
    {_s30: _s444, _s92: None},
)

MALFORMED_CONTENT_TYPE_WITH_GENERIC_STRING: StaticOperationSchema = (
    23,
    n1,
    _s778,
    {
        _s729: MappingProxyType(
            {"method": "POST", "uri": "/MalformedContentTypeWithGenericString"}
        )
    },
    MALFORMED_CONTENT_TYPE_WITH_GENERIC_STRING_INPUT,
    MALFORMED_CONTENT_TYPE_WITH_GENERIC_STRING_OUTPUT,
    (),
)

MALFORMED_CONTENT_TYPE_WITH_PAYLOAD_INPUT: StaticSchema = (
    18,
    n1,
    _s254,
    {_s30: _s255, _s32: None},
    (_s232,),
    ((lambda: schemas.JPEG_BLOB, 16),),
)

MALFORMED_CONTENT_TYPE_WITH_PAYLOAD_OUTPUT: StaticSchema = (
    18,
    n1,
    _s608,
    {_s30: _s444, _s92: None},
)

MALFORMED_CONTENT_TYPE_WITH_PAYLOAD: StaticOperationSchema = (
    23,
    n1,
    _s779,
    {
        _s729: MappingProxyType(
            {"method": "POST", "uri": "/MalformedContentTypeWithPayload"}
        )
    },
    MALFORMED_CONTENT_TYPE_WITH_PAYLOAD_INPUT,
    MALFORMED_CONTENT_TYPE_WITH_PAYLOAD_OUTPUT,
    (),
)

MALFORMED_CONTENT_TYPE_WITHOUT_BODY_EMPTY_INPUT_INPUT: StaticSchema = (
    18,
    n1,
    _s256,
    {_s30: _s257, _s32: None},
    (_s258,),
    ((3, {_s77: _s258}),),
)

MALFORMED_CONTENT_TYPE_WITHOUT_BODY_EMPTY_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s611,
    {_s30: _s444, _s92: None},
)

MALFORMED_CONTENT_TYPE_WITHOUT_BODY_EMPTY_INPUT: StaticOperationSchema = (
    23,
    n1,
    _s781,
    {
        _s729: MappingProxyType(
            {"method": "POST", "uri": "/MalformedContentTypeWithoutBodyEmptyInput"}
        )
    },
    MALFORMED_CONTENT_TYPE_WITHOUT_BODY_EMPTY_INPUT_INPUT,
    MALFORMED_CONTENT_TYPE_WITHOUT_BODY_EMPTY_INPUT_OUTPUT,
    (),
)

MALFORMED_DOUBLE_INPUT: StaticSchema = (
    18,
    n1,
    _s259,
    {_s30: _s260, _s32: None},
    (_s261, _s262, _s263, _s264),
    ((10, 0), (10, 9), (10, {_s34: _s263}), (10, {_s77: _s264})),
)

MALFORMED_DOUBLE_OUTPUT: StaticSchema = (
    18,
    n1,
    _s612,
    {_s30: _s444, _s92: None},
)

MALFORMED_DOUBLE: StaticOperationSchema = (
    23,
    n1,
    _s782,
    {
        _s729: MappingProxyType(
            {"uri": "/MalformedDouble/{doubleInPath}", "method": "POST"}
        )
    },
    MALFORMED_DOUBLE_INPUT,
    MALFORMED_DOUBLE_OUTPUT,
    (),
)

MALFORMED_FLOAT_INPUT: StaticSchema = (
    18,
    n1,
    _s265,
    {_s30: _s266, _s32: None},
    (_s267, _s268, _s269, _s270),
    ((9, 0), (9, 9), (9, {_s34: _s269}), (9, {_s77: _s270})),
)

MALFORMED_FLOAT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s613,
    {_s30: _s444, _s92: None},
)

MALFORMED_FLOAT: StaticOperationSchema = (
    23,
    n1,
    _s783,
    {
        _s729: MappingProxyType(
            {"uri": "/MalformedFloat/{floatInPath}", "method": "POST"}
        )
    },
    MALFORMED_FLOAT_INPUT,
    MALFORMED_FLOAT_OUTPUT,
    (),
)

MALFORMED_INTEGER_INPUT: StaticSchema = (
    18,
    n1,
    _s271,
    {_s30: _s272, _s32: None},
    (_s273, _s274, _s275, _s276),
    ((7, 0), (7, 9), (7, {_s34: _s275}), (7, {_s77: _s276})),
)

MALFORMED_INTEGER_OUTPUT: StaticSchema = (
    18,
    n1,
    _s614,
    {_s30: _s444, _s92: None},
)

MALFORMED_INTEGER: StaticOperationSchema = (
    23,
    n1,
    _s784,
    {
        _s729: MappingProxyType(
            {"uri": "/MalformedInteger/{integerInPath}", "method": "POST"}
        )
    },
    MALFORMED_INTEGER_INPUT,
    MALFORMED_INTEGER_OUTPUT,
    (),
)

SIMPLE_LIST: StaticSchema = (
    16,
    n1,
    _s277,
    0,
    (_s1,),
    ((3, 0),),
)

MALFORMED_LIST_INPUT: StaticSchema = (
    18,
    n1,
    _s278,
    {_s30: _s279, _s32: None},
    (_s280,),
    ((SIMPLE_LIST, 0),),
)

MALFORMED_LIST_OUTPUT: StaticSchema = (
    18,
    n1,
    _s615,
    {_s30: _s444, _s92: None},
)

MALFORMED_LIST: StaticOperationSchema = (
    23,
    n1,
    _s785,
    {_s729: MappingProxyType({"uri": "/MalformedList", "method": "POST"})},
    MALFORMED_LIST_INPUT,
    MALFORMED_LIST_OUTPUT,
    (),
)

MALFORMED_LONG_INPUT: StaticSchema = (
    18,
    n1,
    _s281,
    {_s30: _s282, _s32: None},
    (_s283, _s284, _s285, _s286),
    ((8, 0), (8, 9), (8, {_s34: _s285}), (8, {_s77: _s286})),
)

MALFORMED_LONG_OUTPUT: StaticSchema = (
    18,
    n1,
    _s616,
    {_s30: _s444, _s92: None},
)

MALFORMED_LONG: StaticOperationSchema = (
    23,
    n1,
    _s786,
    {_s729: MappingProxyType({"uri": "/MalformedLong/{longInPath}", "method": "POST"})},
    MALFORMED_LONG_INPUT,
    MALFORMED_LONG_OUTPUT,
    (),
)

SIMPLE_MAP: StaticSchema = (
    17,
    n1,
    _s287,
    0,
    (_s27, _s28),
    ((3, 0), (3, 0)),
)

MALFORMED_MAP_INPUT: StaticSchema = (
    18,
    n1,
    _s288,
    {_s30: _s289, _s32: None},
    (_s290,),
    ((SIMPLE_MAP, 0),),
)

MALFORMED_MAP_OUTPUT: StaticSchema = (
    18,
    n1,
    _s617,
    {_s30: _s444, _s92: None},
)

MALFORMED_MAP: StaticOperationSchema = (
    23,
    n1,
    _s787,
    {_s729: MappingProxyType({"uri": "/MalformedMap", "method": "POST"})},
    MALFORMED_MAP_INPUT,
    MALFORMED_MAP_OUTPUT,
    (),
)

MALFORMED_REQUEST_BODY_INPUT: StaticSchema = (
    18,
    n1,
    _s291,
    {_s30: _s292, _s32: None},
    (_s293, _s189),
    ((7, 0), (9, 0)),
)

MALFORMED_REQUEST_BODY_OUTPUT: StaticSchema = (
    18,
    n1,
    _s618,
    {_s30: _s444, _s92: None},
)

MALFORMED_REQUEST_BODY: StaticOperationSchema = (
    23,
    n1,
    _s788,
    {_s729: MappingProxyType({"uri": "/MalformedRequestBody", "method": "POST"})},
    MALFORMED_REQUEST_BODY_INPUT,
    MALFORMED_REQUEST_BODY_OUTPUT,
    (),
)

MALFORMED_SHORT_INPUT: StaticSchema = (
    18,
    n1,
    _s294,
    {_s30: _s295, _s32: None},
    (_s296, _s297, _s298, _s299),
    ((6, 0), (6, 9), (6, {_s34: _s298}), (6, {_s77: _s299})),
)

MALFORMED_SHORT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s619,
    {_s30: _s444, _s92: None},
)

MALFORMED_SHORT: StaticOperationSchema = (
    23,
    n1,
    _s789,
    {
        _s729: MappingProxyType(
            {"uri": "/MalformedShort/{shortInPath}", "method": "POST"}
        )
    },
    MALFORMED_SHORT_INPUT,
    MALFORMED_SHORT_OUTPUT,
    (),
)

MALFORMED_STRING_INPUT: StaticSchema = (
    18,
    n1,
    _s300,
    {_s30: _s301, _s32: None},
    (_s239,),
    ((lambda: schemas.JSON_HEADER_STRING, {_s77: _s302}),),
)

MALFORMED_STRING_OUTPUT: StaticSchema = (
    18,
    n1,
    _s620,
    {_s30: _s444, _s92: None},
)

MALFORMED_STRING: StaticOperationSchema = (
    23,
    n1,
    _s790,
    {_s729: MappingProxyType({"uri": "/MalformedString", "method": "POST"})},
    MALFORMED_STRING_INPUT,
    MALFORMED_STRING_OUTPUT,
    (),
)

MALFORMED_TIMESTAMP_BODY_DATE_TIME_INPUT: StaticSchema = (
    18,
    n1,
    _s303,
    {_s30: _s304, _s32: None},
    (_s215,),
    ((4, {_s94: _s95, _s201: None}),),
)

MALFORMED_TIMESTAMP_BODY_DATE_TIME_OUTPUT: StaticSchema = (
    18,
    n1,
    _s621,
    {_s30: _s444, _s92: None},
)

MALFORMED_TIMESTAMP_BODY_DATE_TIME: StaticOperationSchema = (
    23,
    n1,
    _s791,
    {
        _s729: MappingProxyType(
            {"uri": "/MalformedTimestampBodyDateTime", "method": "POST"}
        )
    },
    MALFORMED_TIMESTAMP_BODY_DATE_TIME_INPUT,
    MALFORMED_TIMESTAMP_BODY_DATE_TIME_OUTPUT,
    (),
)

MALFORMED_TIMESTAMP_BODY_DEFAULT_INPUT: StaticSchema = (
    18,
    n1,
    _s305,
    {_s30: _s306, _s32: None},
    (_s215,),
    ((4, 1),),
)

MALFORMED_TIMESTAMP_BODY_DEFAULT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s622,
    {_s30: _s444, _s92: None},
)

MALFORMED_TIMESTAMP_BODY_DEFAULT: StaticOperationSchema = (
    23,
    n1,
    _s792,
    {
        _s729: MappingProxyType(
            {"uri": "/MalformedTimestampBodyDefault", "method": "POST"}
        )
    },
    MALFORMED_TIMESTAMP_BODY_DEFAULT_INPUT,
    MALFORMED_TIMESTAMP_BODY_DEFAULT_OUTPUT,
    (),
)

MALFORMED_TIMESTAMP_BODY_HTTP_DATE_INPUT: StaticSchema = (
    18,
    n1,
    _s307,
    {_s30: _s308, _s32: None},
    (_s215,),
    ((4, {_s94: _s196, _s201: None}),),
)

MALFORMED_TIMESTAMP_BODY_HTTP_DATE_OUTPUT: StaticSchema = (
    18,
    n1,
    _s623,
    {_s30: _s444, _s92: None},
)

MALFORMED_TIMESTAMP_BODY_HTTP_DATE: StaticOperationSchema = (
    23,
    n1,
    _s793,
    {
        _s729: MappingProxyType(
            {"uri": "/MalformedTimestampBodyHttpDate", "method": "POST"}
        )
    },
    MALFORMED_TIMESTAMP_BODY_HTTP_DATE_INPUT,
    MALFORMED_TIMESTAMP_BODY_HTTP_DATE_OUTPUT,
    (),
)

MALFORMED_TIMESTAMP_HEADER_DATE_TIME_INPUT: StaticSchema = (
    18,
    n1,
    _s309,
    {_s30: _s310, _s32: None},
    (_s215,),
    ((4, {_s77: _s215, _s94: _s95, _s201: None}),),
)

MALFORMED_TIMESTAMP_HEADER_DATE_TIME_OUTPUT: StaticSchema = (
    18,
    n1,
    _s624,
    {_s30: _s444, _s92: None},
)

MALFORMED_TIMESTAMP_HEADER_DATE_TIME: StaticOperationSchema = (
    23,
    n1,
    _s794,
    {
        _s729: MappingProxyType(
            {"uri": "/MalformedTimestampHeaderDateTime", "method": "POST"}
        )
    },
    MALFORMED_TIMESTAMP_HEADER_DATE_TIME_INPUT,
    MALFORMED_TIMESTAMP_HEADER_DATE_TIME_OUTPUT,
    (),
)

MALFORMED_TIMESTAMP_HEADER_DEFAULT_INPUT: StaticSchema = (
    18,
    n1,
    _s311,
    {_s30: _s312, _s32: None},
    (_s215,),
    ((4, {_s77: _s215, _s201: None}),),
)

MALFORMED_TIMESTAMP_HEADER_DEFAULT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s625,
    {_s30: _s444, _s92: None},
)

MALFORMED_TIMESTAMP_HEADER_DEFAULT: StaticOperationSchema = (
    23,
    n1,
    _s795,
    {
        _s729: MappingProxyType(
            {"uri": "/MalformedTimestampHeaderDefault", "method": "POST"}
        )
    },
    MALFORMED_TIMESTAMP_HEADER_DEFAULT_INPUT,
    MALFORMED_TIMESTAMP_HEADER_DEFAULT_OUTPUT,
    (),
)

MALFORMED_TIMESTAMP_HEADER_EPOCH_INPUT: StaticSchema = (
    18,
    n1,
    _s313,
    {_s30: _s314, _s32: None},
    (_s215,),
    ((4, {_s77: _s215, _s94: _s194, _s201: None}),),
)

MALFORMED_TIMESTAMP_HEADER_EPOCH_OUTPUT: StaticSchema = (
    18,
    n1,
    _s626,
    {_s30: _s444, _s92: None},
)

MALFORMED_TIMESTAMP_HEADER_EPOCH: StaticOperationSchema = (
    23,
    n1,
    _s796,
    {
        _s729: MappingProxyType(
            {"uri": "/MalformedTimestampHeaderEpoch", "method": "POST"}
        )
    },
    MALFORMED_TIMESTAMP_HEADER_EPOCH_INPUT,
    MALFORMED_TIMESTAMP_HEADER_EPOCH_OUTPUT,
    (),
)

MALFORMED_TIMESTAMP_PATH_DEFAULT_INPUT: StaticSchema = (
    18,
    n1,
    _s315,
    {_s30: _s316, _s32: None},
    (_s215,),
    ((4, 9),),
)

MALFORMED_TIMESTAMP_PATH_DEFAULT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s627,
    {_s30: _s444, _s92: None},
)

MALFORMED_TIMESTAMP_PATH_DEFAULT: StaticOperationSchema = (
    23,
    n1,
    _s797,
    {
        _s729: MappingProxyType(
            {"uri": "/MalformedTimestampPathDefault/{timestamp}", "method": "POST"}
        )
    },
    MALFORMED_TIMESTAMP_PATH_DEFAULT_INPUT,
    MALFORMED_TIMESTAMP_PATH_DEFAULT_OUTPUT,
    (),
)

MALFORMED_TIMESTAMP_PATH_EPOCH_INPUT: StaticSchema = (
    18,
    n1,
    _s317,
    {_s30: _s318, _s32: None},
    (_s215,),
    ((4, {_s94: _s194, _s200: None, _s201: None}),),
)

MALFORMED_TIMESTAMP_PATH_EPOCH_OUTPUT: StaticSchema = (
    18,
    n1,
    _s628,
    {_s30: _s444, _s92: None},
)

MALFORMED_TIMESTAMP_PATH_EPOCH: StaticOperationSchema = (
    23,
    n1,
    _s798,
    {
        _s729: MappingProxyType(
            {"uri": "/MalformedTimestampPathEpoch/{timestamp}", "method": "POST"}
        )
    },
    MALFORMED_TIMESTAMP_PATH_EPOCH_INPUT,
    MALFORMED_TIMESTAMP_PATH_EPOCH_OUTPUT,
    (),
)

MALFORMED_TIMESTAMP_PATH_HTTP_DATE_INPUT: StaticSchema = (
    18,
    n1,
    _s319,
    {_s30: _s320, _s32: None},
    (_s215,),
    ((4, {_s94: _s196, _s200: None, _s201: None}),),
)

MALFORMED_TIMESTAMP_PATH_HTTP_DATE_OUTPUT: StaticSchema = (
    18,
    n1,
    _s629,
    {_s30: _s444, _s92: None},
)

MALFORMED_TIMESTAMP_PATH_HTTP_DATE: StaticOperationSchema = (
    23,
    n1,
    _s799,
    {
        _s729: MappingProxyType(
            {"uri": "/MalformedTimestampPathHttpDate/{timestamp}", "method": "POST"}
        )
    },
    MALFORMED_TIMESTAMP_PATH_HTTP_DATE_INPUT,
    MALFORMED_TIMESTAMP_PATH_HTTP_DATE_OUTPUT,
    (),
)

MALFORMED_TIMESTAMP_QUERY_DEFAULT_INPUT: StaticSchema = (
    18,
    n1,
    _s321,
    {_s30: _s322, _s32: None},
    (_s215,),
    ((4, {_s34: _s215, _s201: None}),),
)

MALFORMED_TIMESTAMP_QUERY_DEFAULT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s630,
    {_s30: _s444, _s92: None},
)

MALFORMED_TIMESTAMP_QUERY_DEFAULT: StaticOperationSchema = (
    23,
    n1,
    _s800,
    {
        _s729: MappingProxyType(
            {"uri": "/MalformedTimestampQueryDefault", "method": "POST"}
        )
    },
    MALFORMED_TIMESTAMP_QUERY_DEFAULT_INPUT,
    MALFORMED_TIMESTAMP_QUERY_DEFAULT_OUTPUT,
    (),
)

MALFORMED_TIMESTAMP_QUERY_EPOCH_INPUT: StaticSchema = (
    18,
    n1,
    _s323,
    {_s30: _s324, _s32: None},
    (_s215,),
    ((4, {_s34: _s215, _s94: _s194, _s201: None}),),
)

MALFORMED_TIMESTAMP_QUERY_EPOCH_OUTPUT: StaticSchema = (
    18,
    n1,
    _s631,
    {_s30: _s444, _s92: None},
)

MALFORMED_TIMESTAMP_QUERY_EPOCH: StaticOperationSchema = (
    23,
    n1,
    _s801,
    {
        _s729: MappingProxyType(
            {"uri": "/MalformedTimestampQueryEpoch", "method": "POST"}
        )
    },
    MALFORMED_TIMESTAMP_QUERY_EPOCH_INPUT,
    MALFORMED_TIMESTAMP_QUERY_EPOCH_OUTPUT,
    (),
)

MALFORMED_TIMESTAMP_QUERY_HTTP_DATE_INPUT: StaticSchema = (
    18,
    n1,
    _s325,
    {_s30: _s326, _s32: None},
    (_s215,),
    ((4, {_s34: _s215, _s94: _s196, _s201: None}),),
)

MALFORMED_TIMESTAMP_QUERY_HTTP_DATE_OUTPUT: StaticSchema = (
    18,
    n1,
    _s632,
    {_s30: _s444, _s92: None},
)

MALFORMED_TIMESTAMP_QUERY_HTTP_DATE: StaticOperationSchema = (
    23,
    n1,
    _s802,
    {
        _s729: MappingProxyType(
            {"uri": "/MalformedTimestampQueryHttpDate", "method": "POST"}
        )
    },
    MALFORMED_TIMESTAMP_QUERY_HTTP_DATE_INPUT,
    MALFORMED_TIMESTAMP_QUERY_HTTP_DATE_OUTPUT,
    (),
)

SIMPLE_UNION: StaticSchema = (
    19,
    n1,
    _s327,
    0,
    (_s293, _s210),
    ((7, 0), (3, 0)),
)

MALFORMED_UNION_INPUT: StaticSchema = (
    18,
    n1,
    _s328,
    {_s30: _s329, _s32: None},
    (_s330,),
    ((SIMPLE_UNION, 0),),
)

MALFORMED_UNION_OUTPUT: StaticSchema = (
    18,
    n1,
    _s633,
    {_s30: _s444, _s92: None},
)

MALFORMED_UNION: StaticOperationSchema = (
    23,
    n1,
    _s803,
    {_s729: MappingProxyType({"uri": "/MalformedUnion", "method": "POST"})},
    MALFORMED_UNION_INPUT,
    MALFORMED_UNION_OUTPUT,
    (),
)

MEDIA_TYPE_HEADER_INPUT: StaticSchema = (
    18,
    n1,
    _s331,
    {_s30: _s332, _s32: None},
    (_s333,),
    ((lambda: schemas.JSON_VALUE, {_s77: _s334}),),
)

MEDIA_TYPE_HEADER_OUTPUT: StaticSchema = (
    18,
    n1,
    _s335,
    {_s30: _s336, _s92: None},
    (_s333,),
    ((lambda: schemas.JSON_VALUE, {_s77: _s334}),),
)

MEDIA_TYPE_HEADER: StaticOperationSchema = (
    23,
    n1,
    _s804,
    {_s729: MappingProxyType({"uri": "/MediaTypeHeader", "method": "GET"})},
    MEDIA_TYPE_HEADER_INPUT,
    MEDIA_TYPE_HEADER_OUTPUT,
    (),
)

RENAMED_GREETING: StaticSchema = (
    18,
    n2,
    _s141,
    0,
    (_s337,),
    ((3, 0),),
)

NESTED_UNION: StaticSchema = (
    19,
    n1,
    _s338,
    0,
    (_s339,),
    ((3, 0),),
)

MY_UNION: StaticSchema = (
    19,
    n1,
    _s340,
    0,
    (_s339, _s341, _s342, _s343, _s344, _s345, _s346, _s347, _s348, _s349, _s350),
    (
        (3, 0),
        (2, 0),
        (7, 0),
        (1, 0),
        (4, 0),
        (lambda: schemas.FOO_ENUM, 0),
        (lambda: schemas.STRING_LIST, 0),
        (lambda: schemas.STRING_MAP, 0),
        (lambda: schemas.GREETING_STRUCT, 0),
        (RENAMED_GREETING, 0),
        (NESTED_UNION, 0),
    ),
)

NESTED_PAYLOAD: StaticSchema = (
    18,
    n1,
    _s351,
    0,
    (_s148, _s352),
    ((3, 0), (3, 0)),
)

NO_INPUT_AND_OUTPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s353,
    {_s30: _s354, _s92: None},
)

NO_INPUT_AND_OUTPUT_INPUT: StaticSchema = (
    18,
    n1,
    _s636,
    {_s30: _s444, _s32: None},
)

NO_INPUT_AND_OUTPUT: StaticOperationSchema = (
    23,
    n1,
    _s806,
    {_s729: MappingProxyType({"uri": "/NoInputAndOutputOutput", "method": "POST"})},
    NO_INPUT_AND_OUTPUT_INPUT,
    NO_INPUT_AND_OUTPUT_OUTPUT,
    (),
)

OMITS_NULL_SERIALIZES_EMPTY_STRING_INPUT: StaticSchema = (
    18,
    n1,
    _s355,
    {_s30: _s356, _s32: None},
    (_s357, _s127),
    ((3, {_s34: _s358}), (3, {_s34: _s359})),
)

OMITS_NULL_SERIALIZES_EMPTY_STRING_OUTPUT: StaticSchema = (
    18,
    n1,
    _s646,
    {_s30: _s444, _s92: None},
)

OMITS_NULL_SERIALIZES_EMPTY_STRING: StaticOperationSchema = (
    23,
    n1,
    _s809,
    {
        _s729: MappingProxyType(
            {"uri": "/OmitsNullSerializesEmptyString", "method": "GET"}
        )
    },
    OMITS_NULL_SERIALIZES_EMPTY_STRING_INPUT,
    OMITS_NULL_SERIALIZES_EMPTY_STRING_OUTPUT,
    (),
)

OMITS_SERIALIZING_EMPTY_LISTS_INPUT: StaticSchema = (
    18,
    n1,
    _s360,
    {_s30: _s361, _s32: None},
    (_s36, _s44, _s52, _s55, _s58, _s61, _s64),
    (
        (lambda: schemas.STRING_LIST, {_s34: _s0}),
        (lambda: schemas.INTEGER_LIST, {_s34: _s3}),
        (lambda: schemas.DOUBLE_LIST, {_s34: _s5}),
        (lambda: schemas.BOOLEAN_LIST, {_s34: _s6}),
        (lambda: schemas.TIMESTAMP_LIST, {_s34: _s7}),
        (lambda: schemas.FOO_ENUM_LIST, {_s34: _s62}),
        (lambda: schemas.INTEGER_ENUM_LIST, {_s34: _s25}),
    ),
)

OMITS_SERIALIZING_EMPTY_LISTS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s647,
    {_s30: _s444, _s92: None},
)

OMITS_SERIALIZING_EMPTY_LISTS: StaticOperationSchema = (
    23,
    n1,
    _s810,
    {_s729: MappingProxyType({"uri": "/OmitsSerializingEmptyLists", "method": "POST"})},
    OMITS_SERIALIZING_EMPTY_LISTS_INPUT,
    OMITS_SERIALIZING_EMPTY_LISTS_OUTPUT,
    (),
)
