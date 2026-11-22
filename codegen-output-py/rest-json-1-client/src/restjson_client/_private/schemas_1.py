from types import MappingProxyType

from smithy_core._schema_compact import StaticOperationSchema, StaticSchema

from . import schemas

n0 = "aws.protocoltests.shared"
_s1 = "member"
_s27 = "key"
_s28 = "value"
n1 = "aws.protocoltests.restjson"
_s30 = "smithy.synthetic#originalShapeId"
_s32 = "smithy.api#input"
_s34 = "smithy.api#httpQuery"
_s77 = "smithy.api#httpHeader"
_s92 = "smithy.api#output"
_s94 = "smithy.api#timestampFormat"
_s95 = "date-time"
_s127 = "emptyString"
_s141 = "GreetingStruct"
_s148 = "greeting"
_s186 = "float"
_s191 = "epoch-seconds"
_s193 = "http-date"
_s197 = "smithy.api#httpLabel"
_s198 = "smithy.api#required"
_s207 = "string"
_s212 = "timestamp"
_s224 = "smithy.api#mediaType"
_s229 = "payload"
_s230 = "JpegBlob"
_s231 = "image/jpeg"
_s232 = "MalformedAcceptWithPayloadOutput"
_s233 = "aws.protocoltests.restjson#MalformedAcceptWithPayloadOutput"
_s234 = "MalformedBlobInput"
_s235 = "aws.protocoltests.restjson#MalformedBlobInput"
_s236 = "blob"
_s237 = "MalformedBooleanInput"
_s238 = "aws.protocoltests.restjson#MalformedBooleanInput"
_s239 = "booleanInBody"
_s240 = "booleanInPath"
_s241 = "booleanInQuery"
_s242 = "booleanInHeader"
_s243 = "MalformedByteInput"
_s244 = "aws.protocoltests.restjson#MalformedByteInput"
_s245 = "byteInBody"
_s246 = "byteInPath"
_s247 = "byteInQuery"
_s248 = "byteInHeader"
_s249 = "MalformedContentTypeWithGenericStringInput"
_s250 = "aws.protocoltests.restjson#MalformedContentTypeWithGenericStringInput"
_s251 = "MalformedContentTypeWithPayloadInput"
_s252 = "aws.protocoltests.restjson#MalformedContentTypeWithPayloadInput"
_s253 = "MalformedContentTypeWithoutBodyEmptyInputInput"
_s254 = "aws.protocoltests.restjson#MalformedContentTypeWithoutBodyEmptyInputInput"
_s255 = "header"
_s256 = "MalformedDoubleInput"
_s257 = "aws.protocoltests.restjson#MalformedDoubleInput"
_s258 = "doubleInBody"
_s259 = "doubleInPath"
_s260 = "doubleInQuery"
_s261 = "doubleInHeader"
_s262 = "MalformedFloatInput"
_s263 = "aws.protocoltests.restjson#MalformedFloatInput"
_s264 = "floatInBody"
_s265 = "floatInPath"
_s266 = "floatInQuery"
_s267 = "floatInHeader"
_s268 = "MalformedIntegerInput"
_s269 = "aws.protocoltests.restjson#MalformedIntegerInput"
_s270 = "integerInBody"
_s271 = "integerInPath"
_s272 = "integerInQuery"
_s273 = "integerInHeader"
_s274 = "SimpleList"
_s275 = "MalformedListInput"
_s276 = "aws.protocoltests.restjson#MalformedListInput"
_s277 = "bodyList"
_s278 = "MalformedLongInput"
_s279 = "aws.protocoltests.restjson#MalformedLongInput"
_s280 = "longInBody"
_s281 = "longInPath"
_s282 = "longInQuery"
_s283 = "longInHeader"
_s284 = "SimpleMap"
_s285 = "MalformedMapInput"
_s286 = "aws.protocoltests.restjson#MalformedMapInput"
_s287 = "bodyMap"
_s288 = "MalformedRequestBodyInput"
_s289 = "aws.protocoltests.restjson#MalformedRequestBodyInput"
_s290 = "int"
_s291 = "MalformedShortInput"
_s292 = "aws.protocoltests.restjson#MalformedShortInput"
_s293 = "shortInBody"
_s294 = "shortInPath"
_s295 = "shortInQuery"
_s296 = "shortInHeader"
_s297 = "MalformedStringInput"
_s298 = "aws.protocoltests.restjson#MalformedStringInput"
_s299 = "amz-media-typed-header"
_s300 = "MalformedTimestampBodyDateTimeInput"
_s301 = "aws.protocoltests.restjson#MalformedTimestampBodyDateTimeInput"
_s302 = "MalformedTimestampBodyDefaultInput"
_s303 = "aws.protocoltests.restjson#MalformedTimestampBodyDefaultInput"
_s304 = "MalformedTimestampBodyHttpDateInput"
_s305 = "aws.protocoltests.restjson#MalformedTimestampBodyHttpDateInput"
_s306 = "MalformedTimestampHeaderDateTimeInput"
_s307 = "aws.protocoltests.restjson#MalformedTimestampHeaderDateTimeInput"
_s308 = "MalformedTimestampHeaderDefaultInput"
_s309 = "aws.protocoltests.restjson#MalformedTimestampHeaderDefaultInput"
_s310 = "MalformedTimestampHeaderEpochInput"
_s311 = "aws.protocoltests.restjson#MalformedTimestampHeaderEpochInput"
_s312 = "MalformedTimestampPathDefaultInput"
_s313 = "aws.protocoltests.restjson#MalformedTimestampPathDefaultInput"
_s314 = "MalformedTimestampPathEpochInput"
_s315 = "aws.protocoltests.restjson#MalformedTimestampPathEpochInput"
_s316 = "MalformedTimestampPathHttpDateInput"
_s317 = "aws.protocoltests.restjson#MalformedTimestampPathHttpDateInput"
_s318 = "MalformedTimestampQueryDefaultInput"
_s319 = "aws.protocoltests.restjson#MalformedTimestampQueryDefaultInput"
_s320 = "MalformedTimestampQueryEpochInput"
_s321 = "aws.protocoltests.restjson#MalformedTimestampQueryEpochInput"
_s322 = "MalformedTimestampQueryHttpDateInput"
_s323 = "aws.protocoltests.restjson#MalformedTimestampQueryHttpDateInput"
_s324 = "SimpleUnion"
_s325 = "MalformedUnionInput"
_s326 = "aws.protocoltests.restjson#MalformedUnionInput"
_s327 = "union"
_s328 = "MediaTypeHeaderInput"
_s329 = "aws.protocoltests.restjson#MediaTypeHeaderInput"
_s330 = "json"
_s331 = "X-Json"
_s332 = "MediaTypeHeaderOutput"
_s333 = "aws.protocoltests.restjson#MediaTypeHeaderOutput"
n2 = "aws.protocoltests.restjson.nested"
_s334 = "salutation"
_s335 = "NestedUnion"
_s336 = "stringValue"
_s337 = "MyUnion"
_s338 = "booleanValue"
_s339 = "numberValue"
_s340 = "blobValue"
_s341 = "timestampValue"
_s342 = "enumValue"
_s343 = "listValue"
_s344 = "mapValue"
_s345 = "structureValue"
_s346 = "renamedStructureValue"
_s347 = "unionValue"
_s348 = "NestedPayload"
_s349 = "name"
_s350 = "NoInputAndOutputOutput"
_s351 = "aws.protocoltests.restjson#NoInputAndOutputOutput"
_s352 = "OmitsNullSerializesEmptyStringInput"
_s353 = "aws.protocoltests.restjson#OmitsNullSerializesEmptyStringInput"
_s354 = "nullValue"
_s355 = "Null"
_s356 = "Empty"
_s435 = "smithy.api#Unit"
_s593 = "MalformedAcceptWithPayloadInput"
_s594 = "MalformedBlobOutput"
_s595 = "MalformedBooleanOutput"
_s596 = "MalformedByteOutput"
_s599 = "MalformedContentTypeWithGenericStringOutput"
_s600 = "MalformedContentTypeWithPayloadOutput"
_s603 = "MalformedContentTypeWithoutBodyEmptyInputOutput"
_s604 = "MalformedDoubleOutput"
_s605 = "MalformedFloatOutput"
_s606 = "MalformedIntegerOutput"
_s607 = "MalformedListOutput"
_s608 = "MalformedLongOutput"
_s609 = "MalformedMapOutput"
_s610 = "MalformedRequestBodyOutput"
_s611 = "MalformedShortOutput"
_s612 = "MalformedStringOutput"
_s613 = "MalformedTimestampBodyDateTimeOutput"
_s614 = "MalformedTimestampBodyDefaultOutput"
_s615 = "MalformedTimestampBodyHttpDateOutput"
_s616 = "MalformedTimestampHeaderDateTimeOutput"
_s617 = "MalformedTimestampHeaderDefaultOutput"
_s618 = "MalformedTimestampHeaderEpochOutput"
_s619 = "MalformedTimestampPathDefaultOutput"
_s620 = "MalformedTimestampPathEpochOutput"
_s621 = "MalformedTimestampPathHttpDateOutput"
_s622 = "MalformedTimestampQueryDefaultOutput"
_s623 = "MalformedTimestampQueryEpochOutput"
_s624 = "MalformedTimestampQueryHttpDateOutput"
_s625 = "MalformedUnionOutput"
_s628 = "NoInputAndOutputInput"
_s638 = "OmitsNullSerializesEmptyStringOutput"
_s714 = "smithy.api#http"
_s758 = "MalformedAcceptWithPayload"
_s759 = "MalformedBlob"
_s760 = "MalformedBoolean"
_s761 = "MalformedByte"
_s763 = "MalformedContentTypeWithGenericString"
_s764 = "MalformedContentTypeWithPayload"
_s766 = "MalformedContentTypeWithoutBodyEmptyInput"
_s767 = "MalformedDouble"
_s768 = "MalformedFloat"
_s769 = "MalformedInteger"
_s770 = "MalformedList"
_s771 = "MalformedLong"
_s772 = "MalformedMap"
_s773 = "MalformedRequestBody"
_s774 = "MalformedShort"
_s775 = "MalformedString"
_s776 = "MalformedTimestampBodyDateTime"
_s777 = "MalformedTimestampBodyDefault"
_s778 = "MalformedTimestampBodyHttpDate"
_s779 = "MalformedTimestampHeaderDateTime"
_s780 = "MalformedTimestampHeaderDefault"
_s781 = "MalformedTimestampHeaderEpoch"
_s782 = "MalformedTimestampPathDefault"
_s783 = "MalformedTimestampPathEpoch"
_s784 = "MalformedTimestampPathHttpDate"
_s785 = "MalformedTimestampQueryDefault"
_s786 = "MalformedTimestampQueryEpoch"
_s787 = "MalformedTimestampQueryHttpDate"
_s788 = "MalformedUnion"
_s789 = "MediaTypeHeader"
_s791 = "NoInputAndOutput"
_s794 = "OmitsNullSerializesEmptyString"

JPEG_BLOB: StaticSchema = (
    1,
    n0,
    _s230,
    {_s224: _s231},
)

MALFORMED_ACCEPT_WITH_PAYLOAD_OUTPUT: StaticSchema = (
    18,
    n1,
    _s232,
    {_s30: _s233, _s92: None},
    (_s229,),
    ((JPEG_BLOB, 16),),
)

MALFORMED_ACCEPT_WITH_PAYLOAD_INPUT: StaticSchema = (
    18,
    n1,
    _s593,
    {_s30: _s435, _s32: None},
)

MALFORMED_ACCEPT_WITH_PAYLOAD: StaticOperationSchema = (
    23,
    n1,
    _s758,
    {_s714: MappingProxyType({"method": "POST", "uri": "/MalformedAcceptWithPayload"})},
    MALFORMED_ACCEPT_WITH_PAYLOAD_INPUT,
    MALFORMED_ACCEPT_WITH_PAYLOAD_OUTPUT,
    (),
)

MALFORMED_BLOB_INPUT: StaticSchema = (
    18,
    n1,
    _s234,
    {_s30: _s235, _s32: None},
    (_s236,),
    ((1, 0),),
)

MALFORMED_BLOB_OUTPUT: StaticSchema = (
    18,
    n1,
    _s594,
    {_s30: _s435, _s92: None},
)

MALFORMED_BLOB: StaticOperationSchema = (
    23,
    n1,
    _s759,
    {_s714: MappingProxyType({"uri": "/MalformedBlob", "method": "POST"})},
    MALFORMED_BLOB_INPUT,
    MALFORMED_BLOB_OUTPUT,
    (),
)

MALFORMED_BOOLEAN_INPUT: StaticSchema = (
    18,
    n1,
    _s237,
    {_s30: _s238, _s32: None},
    (_s239, _s240, _s241, _s242),
    ((2, 0), (2, 9), (2, {_s34: _s241}), (2, {_s77: _s242})),
)

MALFORMED_BOOLEAN_OUTPUT: StaticSchema = (
    18,
    n1,
    _s595,
    {_s30: _s435, _s92: None},
)

MALFORMED_BOOLEAN: StaticOperationSchema = (
    23,
    n1,
    _s760,
    {
        _s714: MappingProxyType(
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
    _s243,
    {_s30: _s244, _s32: None},
    (_s245, _s246, _s247, _s248),
    ((5, 0), (5, 9), (5, {_s34: _s247}), (5, {_s77: _s248})),
)

MALFORMED_BYTE_OUTPUT: StaticSchema = (
    18,
    n1,
    _s596,
    {_s30: _s435, _s92: None},
)

MALFORMED_BYTE: StaticOperationSchema = (
    23,
    n1,
    _s761,
    {_s714: MappingProxyType({"uri": "/MalformedByte/{byteInPath}", "method": "POST"})},
    MALFORMED_BYTE_INPUT,
    MALFORMED_BYTE_OUTPUT,
    (),
)

MALFORMED_CONTENT_TYPE_WITH_GENERIC_STRING_INPUT: StaticSchema = (
    18,
    n1,
    _s249,
    {_s30: _s250, _s32: None},
    (_s229,),
    ((3, 16),),
)

MALFORMED_CONTENT_TYPE_WITH_GENERIC_STRING_OUTPUT: StaticSchema = (
    18,
    n1,
    _s599,
    {_s30: _s435, _s92: None},
)

MALFORMED_CONTENT_TYPE_WITH_GENERIC_STRING: StaticOperationSchema = (
    23,
    n1,
    _s763,
    {
        _s714: MappingProxyType(
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
    _s251,
    {_s30: _s252, _s32: None},
    (_s229,),
    ((JPEG_BLOB, 16),),
)

MALFORMED_CONTENT_TYPE_WITH_PAYLOAD_OUTPUT: StaticSchema = (
    18,
    n1,
    _s600,
    {_s30: _s435, _s92: None},
)

MALFORMED_CONTENT_TYPE_WITH_PAYLOAD: StaticOperationSchema = (
    23,
    n1,
    _s764,
    {
        _s714: MappingProxyType(
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
    _s253,
    {_s30: _s254, _s32: None},
    (_s255,),
    ((3, {_s77: _s255}),),
)

MALFORMED_CONTENT_TYPE_WITHOUT_BODY_EMPTY_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s603,
    {_s30: _s435, _s92: None},
)

MALFORMED_CONTENT_TYPE_WITHOUT_BODY_EMPTY_INPUT: StaticOperationSchema = (
    23,
    n1,
    _s766,
    {
        _s714: MappingProxyType(
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
    _s256,
    {_s30: _s257, _s32: None},
    (_s258, _s259, _s260, _s261),
    ((10, 0), (10, 9), (10, {_s34: _s260}), (10, {_s77: _s261})),
)

MALFORMED_DOUBLE_OUTPUT: StaticSchema = (
    18,
    n1,
    _s604,
    {_s30: _s435, _s92: None},
)

MALFORMED_DOUBLE: StaticOperationSchema = (
    23,
    n1,
    _s767,
    {
        _s714: MappingProxyType(
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
    _s262,
    {_s30: _s263, _s32: None},
    (_s264, _s265, _s266, _s267),
    ((9, 0), (9, 9), (9, {_s34: _s266}), (9, {_s77: _s267})),
)

MALFORMED_FLOAT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s605,
    {_s30: _s435, _s92: None},
)

MALFORMED_FLOAT: StaticOperationSchema = (
    23,
    n1,
    _s768,
    {
        _s714: MappingProxyType(
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
    _s268,
    {_s30: _s269, _s32: None},
    (_s270, _s271, _s272, _s273),
    ((7, 0), (7, 9), (7, {_s34: _s272}), (7, {_s77: _s273})),
)

MALFORMED_INTEGER_OUTPUT: StaticSchema = (
    18,
    n1,
    _s606,
    {_s30: _s435, _s92: None},
)

MALFORMED_INTEGER: StaticOperationSchema = (
    23,
    n1,
    _s769,
    {
        _s714: MappingProxyType(
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
    _s274,
    0,
    (_s1,),
    ((3, 0),),
)

MALFORMED_LIST_INPUT: StaticSchema = (
    18,
    n1,
    _s275,
    {_s30: _s276, _s32: None},
    (_s277,),
    ((SIMPLE_LIST, 0),),
)

MALFORMED_LIST_OUTPUT: StaticSchema = (
    18,
    n1,
    _s607,
    {_s30: _s435, _s92: None},
)

MALFORMED_LIST: StaticOperationSchema = (
    23,
    n1,
    _s770,
    {_s714: MappingProxyType({"uri": "/MalformedList", "method": "POST"})},
    MALFORMED_LIST_INPUT,
    MALFORMED_LIST_OUTPUT,
    (),
)

MALFORMED_LONG_INPUT: StaticSchema = (
    18,
    n1,
    _s278,
    {_s30: _s279, _s32: None},
    (_s280, _s281, _s282, _s283),
    ((8, 0), (8, 9), (8, {_s34: _s282}), (8, {_s77: _s283})),
)

MALFORMED_LONG_OUTPUT: StaticSchema = (
    18,
    n1,
    _s608,
    {_s30: _s435, _s92: None},
)

MALFORMED_LONG: StaticOperationSchema = (
    23,
    n1,
    _s771,
    {_s714: MappingProxyType({"uri": "/MalformedLong/{longInPath}", "method": "POST"})},
    MALFORMED_LONG_INPUT,
    MALFORMED_LONG_OUTPUT,
    (),
)

SIMPLE_MAP: StaticSchema = (
    17,
    n1,
    _s284,
    0,
    (_s27, _s28),
    ((3, 0), (3, 0)),
)

MALFORMED_MAP_INPUT: StaticSchema = (
    18,
    n1,
    _s285,
    {_s30: _s286, _s32: None},
    (_s287,),
    ((SIMPLE_MAP, 0),),
)

MALFORMED_MAP_OUTPUT: StaticSchema = (
    18,
    n1,
    _s609,
    {_s30: _s435, _s92: None},
)

MALFORMED_MAP: StaticOperationSchema = (
    23,
    n1,
    _s772,
    {_s714: MappingProxyType({"uri": "/MalformedMap", "method": "POST"})},
    MALFORMED_MAP_INPUT,
    MALFORMED_MAP_OUTPUT,
    (),
)

MALFORMED_REQUEST_BODY_INPUT: StaticSchema = (
    18,
    n1,
    _s288,
    {_s30: _s289, _s32: None},
    (_s290, _s186),
    ((7, 0), (9, 0)),
)

MALFORMED_REQUEST_BODY_OUTPUT: StaticSchema = (
    18,
    n1,
    _s610,
    {_s30: _s435, _s92: None},
)

MALFORMED_REQUEST_BODY: StaticOperationSchema = (
    23,
    n1,
    _s773,
    {_s714: MappingProxyType({"uri": "/MalformedRequestBody", "method": "POST"})},
    MALFORMED_REQUEST_BODY_INPUT,
    MALFORMED_REQUEST_BODY_OUTPUT,
    (),
)

MALFORMED_SHORT_INPUT: StaticSchema = (
    18,
    n1,
    _s291,
    {_s30: _s292, _s32: None},
    (_s293, _s294, _s295, _s296),
    ((6, 0), (6, 9), (6, {_s34: _s295}), (6, {_s77: _s296})),
)

MALFORMED_SHORT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s611,
    {_s30: _s435, _s92: None},
)

MALFORMED_SHORT: StaticOperationSchema = (
    23,
    n1,
    _s774,
    {
        _s714: MappingProxyType(
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
    _s297,
    {_s30: _s298, _s32: None},
    (_s236,),
    ((lambda: schemas.JSON_HEADER_STRING, {_s77: _s299}),),
)

MALFORMED_STRING_OUTPUT: StaticSchema = (
    18,
    n1,
    _s612,
    {_s30: _s435, _s92: None},
)

MALFORMED_STRING: StaticOperationSchema = (
    23,
    n1,
    _s775,
    {_s714: MappingProxyType({"uri": "/MalformedString", "method": "POST"})},
    MALFORMED_STRING_INPUT,
    MALFORMED_STRING_OUTPUT,
    (),
)

MALFORMED_TIMESTAMP_BODY_DATE_TIME_INPUT: StaticSchema = (
    18,
    n1,
    _s300,
    {_s30: _s301, _s32: None},
    (_s212,),
    ((4, {_s94: _s95, _s198: None}),),
)

MALFORMED_TIMESTAMP_BODY_DATE_TIME_OUTPUT: StaticSchema = (
    18,
    n1,
    _s613,
    {_s30: _s435, _s92: None},
)

MALFORMED_TIMESTAMP_BODY_DATE_TIME: StaticOperationSchema = (
    23,
    n1,
    _s776,
    {
        _s714: MappingProxyType(
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
    _s302,
    {_s30: _s303, _s32: None},
    (_s212,),
    ((4, 1),),
)

MALFORMED_TIMESTAMP_BODY_DEFAULT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s614,
    {_s30: _s435, _s92: None},
)

MALFORMED_TIMESTAMP_BODY_DEFAULT: StaticOperationSchema = (
    23,
    n1,
    _s777,
    {
        _s714: MappingProxyType(
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
    _s304,
    {_s30: _s305, _s32: None},
    (_s212,),
    ((4, {_s94: _s193, _s198: None}),),
)

MALFORMED_TIMESTAMP_BODY_HTTP_DATE_OUTPUT: StaticSchema = (
    18,
    n1,
    _s615,
    {_s30: _s435, _s92: None},
)

MALFORMED_TIMESTAMP_BODY_HTTP_DATE: StaticOperationSchema = (
    23,
    n1,
    _s778,
    {
        _s714: MappingProxyType(
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
    _s306,
    {_s30: _s307, _s32: None},
    (_s212,),
    ((4, {_s77: _s212, _s94: _s95, _s198: None}),),
)

MALFORMED_TIMESTAMP_HEADER_DATE_TIME_OUTPUT: StaticSchema = (
    18,
    n1,
    _s616,
    {_s30: _s435, _s92: None},
)

MALFORMED_TIMESTAMP_HEADER_DATE_TIME: StaticOperationSchema = (
    23,
    n1,
    _s779,
    {
        _s714: MappingProxyType(
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
    _s308,
    {_s30: _s309, _s32: None},
    (_s212,),
    ((4, {_s77: _s212, _s198: None}),),
)

MALFORMED_TIMESTAMP_HEADER_DEFAULT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s617,
    {_s30: _s435, _s92: None},
)

MALFORMED_TIMESTAMP_HEADER_DEFAULT: StaticOperationSchema = (
    23,
    n1,
    _s780,
    {
        _s714: MappingProxyType(
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
    _s310,
    {_s30: _s311, _s32: None},
    (_s212,),
    ((4, {_s77: _s212, _s94: _s191, _s198: None}),),
)

MALFORMED_TIMESTAMP_HEADER_EPOCH_OUTPUT: StaticSchema = (
    18,
    n1,
    _s618,
    {_s30: _s435, _s92: None},
)

MALFORMED_TIMESTAMP_HEADER_EPOCH: StaticOperationSchema = (
    23,
    n1,
    _s781,
    {
        _s714: MappingProxyType(
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
    _s312,
    {_s30: _s313, _s32: None},
    (_s212,),
    ((4, 9),),
)

MALFORMED_TIMESTAMP_PATH_DEFAULT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s619,
    {_s30: _s435, _s92: None},
)

MALFORMED_TIMESTAMP_PATH_DEFAULT: StaticOperationSchema = (
    23,
    n1,
    _s782,
    {
        _s714: MappingProxyType(
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
    _s314,
    {_s30: _s315, _s32: None},
    (_s212,),
    ((4, {_s94: _s191, _s197: None, _s198: None}),),
)

MALFORMED_TIMESTAMP_PATH_EPOCH_OUTPUT: StaticSchema = (
    18,
    n1,
    _s620,
    {_s30: _s435, _s92: None},
)

MALFORMED_TIMESTAMP_PATH_EPOCH: StaticOperationSchema = (
    23,
    n1,
    _s783,
    {
        _s714: MappingProxyType(
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
    _s316,
    {_s30: _s317, _s32: None},
    (_s212,),
    ((4, {_s94: _s193, _s197: None, _s198: None}),),
)

MALFORMED_TIMESTAMP_PATH_HTTP_DATE_OUTPUT: StaticSchema = (
    18,
    n1,
    _s621,
    {_s30: _s435, _s92: None},
)

MALFORMED_TIMESTAMP_PATH_HTTP_DATE: StaticOperationSchema = (
    23,
    n1,
    _s784,
    {
        _s714: MappingProxyType(
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
    _s318,
    {_s30: _s319, _s32: None},
    (_s212,),
    ((4, {_s34: _s212, _s198: None}),),
)

MALFORMED_TIMESTAMP_QUERY_DEFAULT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s622,
    {_s30: _s435, _s92: None},
)

MALFORMED_TIMESTAMP_QUERY_DEFAULT: StaticOperationSchema = (
    23,
    n1,
    _s785,
    {
        _s714: MappingProxyType(
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
    _s320,
    {_s30: _s321, _s32: None},
    (_s212,),
    ((4, {_s34: _s212, _s94: _s191, _s198: None}),),
)

MALFORMED_TIMESTAMP_QUERY_EPOCH_OUTPUT: StaticSchema = (
    18,
    n1,
    _s623,
    {_s30: _s435, _s92: None},
)

MALFORMED_TIMESTAMP_QUERY_EPOCH: StaticOperationSchema = (
    23,
    n1,
    _s786,
    {
        _s714: MappingProxyType(
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
    _s322,
    {_s30: _s323, _s32: None},
    (_s212,),
    ((4, {_s34: _s212, _s94: _s193, _s198: None}),),
)

MALFORMED_TIMESTAMP_QUERY_HTTP_DATE_OUTPUT: StaticSchema = (
    18,
    n1,
    _s624,
    {_s30: _s435, _s92: None},
)

MALFORMED_TIMESTAMP_QUERY_HTTP_DATE: StaticOperationSchema = (
    23,
    n1,
    _s787,
    {
        _s714: MappingProxyType(
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
    _s324,
    0,
    (_s290, _s207),
    ((7, 0), (3, 0)),
)

MALFORMED_UNION_INPUT: StaticSchema = (
    18,
    n1,
    _s325,
    {_s30: _s326, _s32: None},
    (_s327,),
    ((SIMPLE_UNION, 0),),
)

MALFORMED_UNION_OUTPUT: StaticSchema = (
    18,
    n1,
    _s625,
    {_s30: _s435, _s92: None},
)

MALFORMED_UNION: StaticOperationSchema = (
    23,
    n1,
    _s788,
    {_s714: MappingProxyType({"uri": "/MalformedUnion", "method": "POST"})},
    MALFORMED_UNION_INPUT,
    MALFORMED_UNION_OUTPUT,
    (),
)

MEDIA_TYPE_HEADER_INPUT: StaticSchema = (
    18,
    n1,
    _s328,
    {_s30: _s329, _s32: None},
    (_s330,),
    ((lambda: schemas.JSON_VALUE, {_s77: _s331}),),
)

MEDIA_TYPE_HEADER_OUTPUT: StaticSchema = (
    18,
    n1,
    _s332,
    {_s30: _s333, _s92: None},
    (_s330,),
    ((lambda: schemas.JSON_VALUE, {_s77: _s331}),),
)

MEDIA_TYPE_HEADER: StaticOperationSchema = (
    23,
    n1,
    _s789,
    {_s714: MappingProxyType({"uri": "/MediaTypeHeader", "method": "GET"})},
    MEDIA_TYPE_HEADER_INPUT,
    MEDIA_TYPE_HEADER_OUTPUT,
    (),
)

RENAMED_GREETING: StaticSchema = (
    18,
    n2,
    _s141,
    0,
    (_s334,),
    ((3, 0),),
)

NESTED_UNION: StaticSchema = (
    19,
    n1,
    _s335,
    0,
    (_s336,),
    ((3, 0),),
)

MY_UNION: StaticSchema = (
    19,
    n1,
    _s337,
    0,
    (_s336, _s338, _s339, _s340, _s341, _s342, _s343, _s344, _s345, _s346, _s347),
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
    _s348,
    0,
    (_s148, _s349),
    ((3, 0), (3, 0)),
)

NO_INPUT_AND_OUTPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s350,
    {_s30: _s351, _s92: None},
)

NO_INPUT_AND_OUTPUT_INPUT: StaticSchema = (
    18,
    n1,
    _s628,
    {_s30: _s435, _s32: None},
)

NO_INPUT_AND_OUTPUT: StaticOperationSchema = (
    23,
    n1,
    _s791,
    {_s714: MappingProxyType({"uri": "/NoInputAndOutputOutput", "method": "POST"})},
    NO_INPUT_AND_OUTPUT_INPUT,
    NO_INPUT_AND_OUTPUT_OUTPUT,
    (),
)

OMITS_NULL_SERIALIZES_EMPTY_STRING_INPUT: StaticSchema = (
    18,
    n1,
    _s352,
    {_s30: _s353, _s32: None},
    (_s354, _s127),
    ((3, {_s34: _s355}), (3, {_s34: _s356})),
)

OMITS_NULL_SERIALIZES_EMPTY_STRING_OUTPUT: StaticSchema = (
    18,
    n1,
    _s638,
    {_s30: _s435, _s92: None},
)

OMITS_NULL_SERIALIZES_EMPTY_STRING: StaticOperationSchema = (
    23,
    n1,
    _s794,
    {
        _s714: MappingProxyType(
            {"uri": "/OmitsNullSerializesEmptyString", "method": "GET"}
        )
    },
    OMITS_NULL_SERIALIZES_EMPTY_STRING_INPUT,
    OMITS_NULL_SERIALIZES_EMPTY_STRING_OUTPUT,
    (),
)
