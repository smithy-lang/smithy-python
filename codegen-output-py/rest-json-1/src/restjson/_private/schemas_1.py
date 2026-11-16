from smithy_core._schema_compact import StaticSchema

from . import schemas

n0 = "aws.protocoltests.shared"
_s1 = "member"
_s27 = "key"
_s28 = "value"
n1 = "aws.protocoltests.restjson"
_s30 = "smithy.api#input"
_s32 = "smithy.api#httpQuery"
_s65 = "payload"
_s71 = "smithy.api#jsonName"
_s74 = "smithy.api#error"
_s75 = "client"
_s76 = "smithy.api#httpError"
_s78 = "smithy.api#httpHeader"
_s83 = "baz"
_s89 = "smithy.api#output"
_s91 = "smithy.api#timestampFormat"
_s92 = "date-time"
_s124 = ""
_s144 = "greeting"
_s173 = "header"
_s188 = "stream"
_s196 = "initialRequestMember"
_s197 = "initial-request-member"
_s198 = "smithy.api#required"
_s218 = "foo"
_s221 = "prefixHeaders"
_s222 = "smithy.api#httpPrefixHeaders"
_s226 = "X-Foo"
_s227 = "blob"
_s229 = "smithy.api#mediaType"
_s231 = "HttpPayloadTraitsWithMediaTypeInputOutput"
_s232 = "NestedPayload"
_s233 = "name"
_s234 = "HttpPayloadWithStructureInputOutput"
_s235 = "nested"
_s236 = "UnionPayload"
_s237 = "HttpPayloadWithUnionInputOutput"
_s238 = "HttpPrefixHeadersInResponseInput"
_s239 = "HttpPrefixHeadersInResponseOutput"
_s240 = "HttpPrefixHeadersInput"
_s241 = "x-foo"
_s242 = "fooMap"
_s243 = "x-foo-"
_s244 = "HttpPrefixHeadersOutput"
_s245 = "QueryMap"
_s246 = "HttpQueryParamsOnlyInput"
_s247 = "queryMap"
_s248 = "HttpRequestWithFloatLabelsInput"
_s249 = "float"
_s250 = "double"
_s251 = "HttpRequestWithGreedyLabelInPathInput"
_s252 = "EpochSeconds"
_s253 = "epoch-seconds"
_s254 = "HttpDate"
_s255 = "http-date"
_s256 = "HttpRequestWithLabelsAndTimestampFormatInput"
_s257 = "memberEpochSeconds"
_s258 = "smithy.api#httpLabel"
_s259 = "memberHttpDate"
_s260 = "memberDateTime"
_s261 = "defaultFormat"
_s262 = "targetEpochSeconds"
_s263 = "targetHttpDate"
_s264 = "targetDateTime"
_s265 = "HttpRequestWithLabelsInput"
_s266 = "string"
_s267 = "short"
_s268 = "integer"
_s269 = "long"
_s270 = "boolean"
_s271 = "timestamp"
_s272 = "HttpRequestWithRegexLiteralInput"
_s273 = "str"
_s274 = "HttpResponseCodeOutput"
_s275 = "Status"
_s276 = "IgnoreQueryParamsInResponseOutput"
_s277 = "InputAndOutputWithHeadersIO"
_s278 = "headerString"
_s279 = "X-String"
_s280 = "headerByte"
_s281 = "X-Byte"
_s282 = "headerShort"
_s283 = "X-Short"
_s284 = "headerInteger"
_s285 = "X-Integer"
_s286 = "headerLong"
_s287 = "X-Long"
_s288 = "headerFloat"
_s289 = "X-Float"
_s290 = "headerDouble"
_s291 = "X-Double"
_s292 = "headerTrueBool"
_s293 = "X-Boolean1"
_s294 = "headerFalseBool"
_s295 = "X-Boolean2"
_s296 = "headerStringList"
_s297 = "X-StringList"
_s298 = "headerStringSet"
_s299 = "X-StringSet"
_s300 = "headerIntegerList"
_s301 = "X-IntegerList"
_s302 = "headerBooleanList"
_s303 = "X-BooleanList"
_s304 = "headerTimestampList"
_s305 = "X-TimestampList"
_s306 = "headerEnum"
_s307 = "X-Enum"
_s308 = "headerEnumList"
_s309 = "X-EnumList"
_s310 = "headerIntegerEnum"
_s311 = "X-IntegerEnum"
_s312 = "headerIntegerEnumList"
_s313 = "X-IntegerEnumList"
_s314 = "InputStreamInput"
_s315 = "InputStreamWithInitialRequestInput"
_s316 = "InvalidGreeting"
_s317 = "Message"
_s318 = "JsonBlobsInputOutput"
_s319 = "data"
_s320 = "FooEnumSet"
_s321 = "FooEnumMap"
_s322 = "JsonEnumsInputOutput"
_s323 = "fooEnum1"
_s324 = "fooEnum2"
_s325 = "fooEnum3"
_s326 = "fooEnumList"
_s327 = "fooEnumSet"
_s328 = "fooEnumMap"
_s329 = "JsonHeaderString"
_s330 = "application/json"
_s331 = "IntegerEnumSet"
_s332 = "IntegerEnumMap"
_s333 = "JsonIntEnumsInputOutput"
_s334 = "integerEnum1"
_s335 = "integerEnum2"
_s336 = "integerEnum3"
_s337 = "integerEnumList"
_s338 = "integerEnumSet"
_s339 = "integerEnumMap"
_s340 = "NestedStringList"
_s341 = "StructureListMember"
_s342 = "a"
_s343 = "b"
_s344 = "other"
_s345 = "StructureList"
_s346 = "JsonListsInputOutput"
_s347 = "stringList"
_s348 = "stringSet"
_s349 = "integerList"
_s350 = "booleanList"
_s351 = "timestampList"
_s352 = "enumList"
_s353 = "intEnumList"
_s354 = "nestedStringList"
_s355 = "structureList"
_s356 = "myStructureList"
_s357 = "JsonMapsInputOutput"
_s358 = "denseStructMap"
_s359 = "denseNumberMap"
_s360 = "denseBooleanMap"
_s361 = "denseStringMap"
_s362 = "denseSetMap"
_s363 = "JsonTimestampsInputOutput"
_s364 = "normal"
_s365 = "dateTime"
_s366 = "dateTimeOnTarget"
_s367 = "epochSeconds"
_s368 = "epochSecondsOnTarget"
_s369 = "httpDate"
_s370 = "httpDateOnTarget"
_s371 = "JsonValue"
_s372 = "MalformedAcceptWithGenericStringOutput"
_s373 = "JpegBlob"
_s374 = "image/jpeg"
_s375 = "MalformedAcceptWithPayloadOutput"
_s376 = "MalformedBlobInput"
_s377 = "MalformedBooleanInput"
_s378 = "booleanInBody"
_s379 = "booleanInPath"
_s380 = "booleanInQuery"
_s381 = "booleanInHeader"
_s382 = "MalformedByteInput"
_s383 = "byteInBody"
_s384 = "byteInPath"
_s385 = "byteInQuery"
_s386 = "byteInHeader"
_s387 = "MalformedContentTypeWithGenericStringInput"
_s388 = "MalformedContentTypeWithPayloadInput"
_s389 = "MalformedContentTypeWithoutBodyEmptyInputInput"
_s390 = "MalformedDoubleInput"
_s391 = "doubleInBody"
_s392 = "doubleInPath"
_s393 = "doubleInQuery"
_s394 = "doubleInHeader"
_s395 = "MalformedFloatInput"
_s396 = "floatInBody"
_s397 = "floatInPath"
_s398 = "floatInQuery"
_s399 = "floatInHeader"
_s400 = "MalformedIntegerInput"
_s401 = "integerInBody"
_s402 = "integerInPath"
_s403 = "integerInQuery"
_s404 = "integerInHeader"
_s405 = "SimpleList"
_s406 = "MalformedListInput"
_s407 = "bodyList"
_s408 = "MalformedLongInput"
_s409 = "longInBody"
_s410 = "longInPath"
_s411 = "longInQuery"
_s412 = "longInHeader"
_s413 = "SimpleMap"
_s414 = "MalformedMapInput"
_s415 = "bodyMap"
_s416 = "MalformedRequestBodyInput"
_s417 = "int"
_s418 = "MalformedShortInput"
_s419 = "shortInBody"
_s420 = "shortInPath"
_s421 = "shortInQuery"
_s422 = "shortInHeader"
_s423 = "MalformedStringInput"
_s424 = "amz-media-typed-header"
_s425 = "MalformedTimestampBodyDateTimeInput"
_s426 = "MalformedTimestampBodyDefaultInput"
_s427 = "MalformedTimestampBodyHttpDateInput"
_s428 = "MalformedTimestampHeaderDateTimeInput"
_s429 = "MalformedTimestampHeaderDefaultInput"
_s430 = "MalformedTimestampHeaderEpochInput"
_s431 = "MalformedTimestampPathDefaultInput"

HTTP_PAYLOAD_TRAITS_WITH_MEDIA_TYPE_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s231,
    {_s30: None, _s89: None},
    (_s218, _s227),
    ((3, {_s78: _s226}), (lambda: schemas.TEXT_PLAIN_BLOB, 16)),
)

NESTED_PAYLOAD: StaticSchema = (
    18,
    n1,
    _s232,
    0,
    (_s144, _s233),
    ((3, 0), (3, 0)),
)

HTTP_PAYLOAD_WITH_STRUCTURE_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s234,
    {_s30: None, _s89: None},
    (_s235,),
    ((NESTED_PAYLOAD, 16),),
)

UNION_PAYLOAD: StaticSchema = (
    19,
    n1,
    _s236,
    0,
    (_s144,),
    ((3, 0),),
)

HTTP_PAYLOAD_WITH_UNION_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s237,
    {_s30: None, _s89: None},
    (_s235,),
    ((UNION_PAYLOAD, 16),),
)

HTTP_PREFIX_HEADERS_IN_RESPONSE_INPUT: StaticSchema = (
    18,
    n1,
    _s238,
    {_s30: None},
)

HTTP_PREFIX_HEADERS_IN_RESPONSE_OUTPUT: StaticSchema = (
    18,
    n1,
    _s239,
    {_s89: None},
    (_s221,),
    ((lambda: schemas.STRING_MAP, {_s222: _s124}),),
)

HTTP_PREFIX_HEADERS_INPUT: StaticSchema = (
    18,
    n1,
    _s240,
    {_s30: None},
    (_s218, _s242),
    ((3, {_s78: _s241}), (lambda: schemas.STRING_MAP, {_s222: _s243})),
)

HTTP_PREFIX_HEADERS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s244,
    {_s89: None},
    (_s218, _s242),
    ((3, {_s78: _s241}), (lambda: schemas.STRING_MAP, {_s222: _s243})),
)

QUERY_MAP: StaticSchema = (
    17,
    n1,
    _s245,
    0,
    (_s27, _s28),
    ((3, 0), (3, 0)),
)

HTTP_QUERY_PARAMS_ONLY_INPUT: StaticSchema = (
    18,
    n1,
    _s246,
    {_s30: None},
    (_s247,),
    ((QUERY_MAP, 1024),),
)

HTTP_REQUEST_WITH_FLOAT_LABELS_INPUT: StaticSchema = (
    18,
    n1,
    _s248,
    {_s30: None},
    (_s249, _s250),
    ((9, 9), (10, 9)),
)

HTTP_REQUEST_WITH_GREEDY_LABEL_IN_PATH_INPUT: StaticSchema = (
    18,
    n1,
    _s251,
    {_s30: None},
    (_s218, _s83),
    ((3, 9), (3, 9)),
)

EPOCH_SECONDS: StaticSchema = (
    4,
    n0,
    _s252,
    {_s91: _s253},
)

HTTP_DATE: StaticSchema = (
    4,
    n0,
    _s254,
    {_s91: _s255},
)

HTTP_REQUEST_WITH_LABELS_AND_TIMESTAMP_FORMAT_INPUT: StaticSchema = (
    18,
    n1,
    _s256,
    {_s30: None},
    (_s257, _s259, _s260, _s261, _s262, _s263, _s264),
    (
        (4, {_s91: _s253, _s258: None, _s198: None}),
        (4, {_s91: _s255, _s258: None, _s198: None}),
        (4, {_s91: _s92, _s258: None, _s198: None}),
        (4, 9),
        (EPOCH_SECONDS, 9),
        (HTTP_DATE, 9),
        (lambda: schemas.DATE_TIME, 9),
    ),
)

HTTP_REQUEST_WITH_LABELS_INPUT: StaticSchema = (
    18,
    n1,
    _s265,
    {_s30: None},
    (_s266, _s267, _s268, _s269, _s249, _s250, _s270, _s271),
    ((3, 9), (6, 9), (7, 9), (8, 9), (9, 9), (10, 9), (2, 9), (4, 9)),
)

HTTP_REQUEST_WITH_REGEX_LITERAL_INPUT: StaticSchema = (
    18,
    n1,
    _s272,
    {_s30: None},
    (_s273,),
    ((3, 9),),
)

HTTP_RESPONSE_CODE_OUTPUT: StaticSchema = (
    18,
    n1,
    _s274,
    {_s89: None},
    (_s275,),
    ((7, 128),),
)

IGNORE_QUERY_PARAMS_IN_RESPONSE_OUTPUT: StaticSchema = (
    18,
    n1,
    _s276,
    {_s89: None},
    (_s83,),
    ((3, {_s32: _s83}),),
)

INPUT_AND_OUTPUT_WITH_HEADERS_IO: StaticSchema = (
    18,
    n1,
    _s277,
    {_s30: None, _s89: None},
    (
        _s278,
        _s280,
        _s282,
        _s284,
        _s286,
        _s288,
        _s290,
        _s292,
        _s294,
        _s296,
        _s298,
        _s300,
        _s302,
        _s304,
        _s306,
        _s308,
        _s310,
        _s312,
    ),
    (
        (3, {_s78: _s279}),
        (5, {_s78: _s281}),
        (6, {_s78: _s283}),
        (7, {_s78: _s285}),
        (8, {_s78: _s287}),
        (9, {_s78: _s289}),
        (10, {_s78: _s291}),
        (2, {_s78: _s293}),
        (2, {_s78: _s295}),
        (lambda: schemas.STRING_LIST, {_s78: _s297}),
        (lambda: schemas.STRING_SET, {_s78: _s299}),
        (lambda: schemas.INTEGER_LIST, {_s78: _s301}),
        (lambda: schemas.BOOLEAN_LIST, {_s78: _s303}),
        (lambda: schemas.TIMESTAMP_LIST, {_s78: _s305}),
        (lambda: schemas.FOO_ENUM, {_s78: _s307}),
        (lambda: schemas.FOO_ENUM_LIST, {_s78: _s309}),
        (lambda: schemas.INTEGER_ENUM, {_s78: _s311}),
        (lambda: schemas.INTEGER_ENUM_LIST, {_s78: _s313}),
    ),
)

INPUT_STREAM_INPUT: StaticSchema = (
    18,
    n1,
    _s314,
    {_s30: None},
    (_s188,),
    ((lambda: schemas.EVENT_STREAM, 16),),
)

INPUT_STREAM_WITH_INITIAL_REQUEST_INPUT: StaticSchema = (
    18,
    n1,
    _s315,
    {_s30: None},
    (_s196, _s188),
    ((3, {_s78: _s197, _s198: None}), (lambda: schemas.EVENT_STREAM, 16)),
)

INVALID_GREETING: StaticSchema = (
    18,
    n1,
    _s316,
    {_s74: _s75, _s76: 400},
    (_s317,),
    ((3, 0),),
)

JSON_BLOBS_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s318,
    {_s30: None, _s89: None},
    (_s319,),
    ((1, 0),),
)

FOO_ENUM_SET: StaticSchema = (
    16,
    n0,
    _s320,
    0,
    (_s1,),
    ((lambda: schemas.FOO_ENUM, 0),),
)

FOO_ENUM_MAP: StaticSchema = (
    17,
    n0,
    _s321,
    0,
    (_s27, _s28),
    ((3, 0), (lambda: schemas.FOO_ENUM, 0)),
)

JSON_ENUMS_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s322,
    {_s30: None, _s89: None},
    (_s323, _s324, _s325, _s326, _s327, _s328),
    (
        (lambda: schemas.FOO_ENUM, 0),
        (lambda: schemas.FOO_ENUM, 0),
        (lambda: schemas.FOO_ENUM, 0),
        (lambda: schemas.FOO_ENUM_LIST, 0),
        (FOO_ENUM_SET, 0),
        (FOO_ENUM_MAP, 0),
    ),
)

JSON_HEADER_STRING: StaticSchema = (
    3,
    n1,
    _s329,
    {_s229: _s330},
)

INTEGER_ENUM_SET: StaticSchema = (
    16,
    n0,
    _s331,
    0,
    (_s1,),
    ((lambda: schemas.INTEGER_ENUM, 0),),
)

INTEGER_ENUM_MAP: StaticSchema = (
    17,
    n0,
    _s332,
    0,
    (_s27, _s28),
    ((3, 0), (lambda: schemas.INTEGER_ENUM, 0)),
)

JSON_INT_ENUMS_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s333,
    {_s30: None, _s89: None},
    (_s334, _s335, _s336, _s337, _s338, _s339),
    (
        (lambda: schemas.INTEGER_ENUM, 0),
        (lambda: schemas.INTEGER_ENUM, 0),
        (lambda: schemas.INTEGER_ENUM, 0),
        (lambda: schemas.INTEGER_ENUM_LIST, 0),
        (INTEGER_ENUM_SET, 0),
        (INTEGER_ENUM_MAP, 0),
    ),
)

NESTED_STRING_LIST: StaticSchema = (
    16,
    n0,
    _s340,
    0,
    (_s1,),
    ((lambda: schemas.STRING_LIST, 0),),
)

STRUCTURE_LIST_MEMBER: StaticSchema = (
    18,
    n1,
    _s341,
    0,
    (_s342, _s343),
    ((3, {_s71: _s28}), (3, {_s71: _s344})),
)

STRUCTURE_LIST: StaticSchema = (
    16,
    n1,
    _s345,
    0,
    (_s1,),
    ((STRUCTURE_LIST_MEMBER, 0),),
)

JSON_LISTS_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s346,
    {_s30: None, _s89: None},
    (_s347, _s348, _s349, _s350, _s351, _s352, _s353, _s354, _s355),
    (
        (lambda: schemas.STRING_LIST, 0),
        (lambda: schemas.STRING_SET, 0),
        (lambda: schemas.INTEGER_LIST, 0),
        (lambda: schemas.BOOLEAN_LIST, 0),
        (lambda: schemas.TIMESTAMP_LIST, 0),
        (lambda: schemas.FOO_ENUM_LIST, 0),
        (lambda: schemas.INTEGER_ENUM_LIST, 0),
        (NESTED_STRING_LIST, 0),
        (STRUCTURE_LIST, {_s71: _s356}),
    ),
)

JSON_MAPS_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s357,
    {_s30: None, _s89: None},
    (_s358, _s359, _s360, _s361, _s362),
    (
        (lambda: schemas.DENSE_STRUCT_MAP, 0),
        (lambda: schemas.DENSE_NUMBER_MAP, 0),
        (lambda: schemas.DENSE_BOOLEAN_MAP, 0),
        (lambda: schemas.DENSE_STRING_MAP, 0),
        (lambda: schemas.DENSE_SET_MAP, 0),
    ),
)

JSON_TIMESTAMPS_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s363,
    {_s30: None, _s89: None},
    (_s364, _s365, _s366, _s367, _s368, _s369, _s370),
    (
        (4, 0),
        (4, {_s91: _s92}),
        (lambda: schemas.DATE_TIME, 0),
        (4, {_s91: _s253}),
        (EPOCH_SECONDS, 0),
        (4, {_s91: _s255}),
        (HTTP_DATE, 0),
    ),
)

JSON_VALUE: StaticSchema = (
    3,
    n1,
    _s371,
    {_s229: _s330},
)

MALFORMED_ACCEPT_WITH_GENERIC_STRING_OUTPUT: StaticSchema = (
    18,
    n1,
    _s372,
    {_s89: None},
    (_s65,),
    ((3, 16),),
)

JPEG_BLOB: StaticSchema = (
    1,
    n0,
    _s373,
    {_s229: _s374},
)

MALFORMED_ACCEPT_WITH_PAYLOAD_OUTPUT: StaticSchema = (
    18,
    n1,
    _s375,
    {_s89: None},
    (_s65,),
    ((JPEG_BLOB, 16),),
)

MALFORMED_BLOB_INPUT: StaticSchema = (
    18,
    n1,
    _s376,
    {_s30: None},
    (_s227,),
    ((1, 0),),
)

MALFORMED_BOOLEAN_INPUT: StaticSchema = (
    18,
    n1,
    _s377,
    {_s30: None},
    (_s378, _s379, _s380, _s381),
    ((2, 0), (2, 9), (2, {_s32: _s380}), (2, {_s78: _s381})),
)

MALFORMED_BYTE_INPUT: StaticSchema = (
    18,
    n1,
    _s382,
    {_s30: None},
    (_s383, _s384, _s385, _s386),
    ((5, 0), (5, 9), (5, {_s32: _s385}), (5, {_s78: _s386})),
)

MALFORMED_CONTENT_TYPE_WITH_GENERIC_STRING_INPUT: StaticSchema = (
    18,
    n1,
    _s387,
    {_s30: None},
    (_s65,),
    ((3, 16),),
)

MALFORMED_CONTENT_TYPE_WITH_PAYLOAD_INPUT: StaticSchema = (
    18,
    n1,
    _s388,
    {_s30: None},
    (_s65,),
    ((JPEG_BLOB, 16),),
)

MALFORMED_CONTENT_TYPE_WITHOUT_BODY_EMPTY_INPUT_INPUT: StaticSchema = (
    18,
    n1,
    _s389,
    {_s30: None},
    (_s173,),
    ((3, {_s78: _s173}),),
)

MALFORMED_DOUBLE_INPUT: StaticSchema = (
    18,
    n1,
    _s390,
    {_s30: None},
    (_s391, _s392, _s393, _s394),
    ((10, 0), (10, 9), (10, {_s32: _s393}), (10, {_s78: _s394})),
)

MALFORMED_FLOAT_INPUT: StaticSchema = (
    18,
    n1,
    _s395,
    {_s30: None},
    (_s396, _s397, _s398, _s399),
    ((9, 0), (9, 9), (9, {_s32: _s398}), (9, {_s78: _s399})),
)

MALFORMED_INTEGER_INPUT: StaticSchema = (
    18,
    n1,
    _s400,
    {_s30: None},
    (_s401, _s402, _s403, _s404),
    ((7, 0), (7, 9), (7, {_s32: _s403}), (7, {_s78: _s404})),
)

SIMPLE_LIST: StaticSchema = (
    16,
    n1,
    _s405,
    0,
    (_s1,),
    ((3, 0),),
)

MALFORMED_LIST_INPUT: StaticSchema = (
    18,
    n1,
    _s406,
    {_s30: None},
    (_s407,),
    ((SIMPLE_LIST, 0),),
)

MALFORMED_LONG_INPUT: StaticSchema = (
    18,
    n1,
    _s408,
    {_s30: None},
    (_s409, _s410, _s411, _s412),
    ((8, 0), (8, 9), (8, {_s32: _s411}), (8, {_s78: _s412})),
)

SIMPLE_MAP: StaticSchema = (
    17,
    n1,
    _s413,
    0,
    (_s27, _s28),
    ((3, 0), (3, 0)),
)

MALFORMED_MAP_INPUT: StaticSchema = (
    18,
    n1,
    _s414,
    {_s30: None},
    (_s415,),
    ((SIMPLE_MAP, 0),),
)

MALFORMED_REQUEST_BODY_INPUT: StaticSchema = (
    18,
    n1,
    _s416,
    {_s30: None},
    (_s417, _s249),
    ((7, 0), (9, 0)),
)

MALFORMED_SHORT_INPUT: StaticSchema = (
    18,
    n1,
    _s418,
    {_s30: None},
    (_s419, _s420, _s421, _s422),
    ((6, 0), (6, 9), (6, {_s32: _s421}), (6, {_s78: _s422})),
)

MALFORMED_STRING_INPUT: StaticSchema = (
    18,
    n1,
    _s423,
    {_s30: None},
    (_s227,),
    ((JSON_HEADER_STRING, {_s78: _s424}),),
)

MALFORMED_TIMESTAMP_BODY_DATE_TIME_INPUT: StaticSchema = (
    18,
    n1,
    _s425,
    {_s30: None},
    (_s271,),
    ((4, {_s91: _s92, _s198: None}),),
)

MALFORMED_TIMESTAMP_BODY_DEFAULT_INPUT: StaticSchema = (
    18,
    n1,
    _s426,
    {_s30: None},
    (_s271,),
    ((4, 1),),
)

MALFORMED_TIMESTAMP_BODY_HTTP_DATE_INPUT: StaticSchema = (
    18,
    n1,
    _s427,
    {_s30: None},
    (_s271,),
    ((4, {_s91: _s255, _s198: None}),),
)

MALFORMED_TIMESTAMP_HEADER_DATE_TIME_INPUT: StaticSchema = (
    18,
    n1,
    _s428,
    {_s30: None},
    (_s271,),
    ((4, {_s78: _s271, _s91: _s92, _s198: None}),),
)

MALFORMED_TIMESTAMP_HEADER_DEFAULT_INPUT: StaticSchema = (
    18,
    n1,
    _s429,
    {_s30: None},
    (_s271,),
    ((4, {_s78: _s271, _s198: None}),),
)

MALFORMED_TIMESTAMP_HEADER_EPOCH_INPUT: StaticSchema = (
    18,
    n1,
    _s430,
    {_s30: None},
    (_s271,),
    ((4, {_s78: _s271, _s91: _s253, _s198: None}),),
)

MALFORMED_TIMESTAMP_PATH_DEFAULT_INPUT: StaticSchema = (
    18,
    n1,
    _s431,
    {_s30: None},
    (_s271,),
    ((4, 9),),
)
