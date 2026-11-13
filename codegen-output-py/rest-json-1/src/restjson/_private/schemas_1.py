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
_s70 = "smithy.api#jsonName"
_s73 = "smithy.api#error"
_s74 = "client"
_s75 = "smithy.api#httpError"
_s77 = "smithy.api#httpHeader"
_s82 = "baz"
_s88 = "smithy.api#output"
_s90 = "smithy.api#timestampFormat"
_s91 = "date-time"
_s123 = ""
_s143 = "greeting"
_s172 = "header"
_s187 = "stream"
_s195 = "initialRequestMember"
_s196 = "initial-request-member"
_s197 = "smithy.api#required"
_s217 = "foo"
_s220 = "prefixHeaders"
_s221 = "smithy.api#httpPrefixHeaders"
_s225 = "X-Foo"
_s226 = "blob"
_s228 = "smithy.api#mediaType"
_s230 = "HttpPayloadTraitsWithMediaTypeInputOutput"
_s231 = "NestedPayload"
_s232 = "name"
_s233 = "HttpPayloadWithStructureInputOutput"
_s234 = "nested"
_s235 = "UnionPayload"
_s236 = "HttpPayloadWithUnionInputOutput"
_s237 = "HttpPrefixHeadersInResponseInput"
_s238 = "HttpPrefixHeadersInResponseOutput"
_s239 = "HttpPrefixHeadersInput"
_s240 = "x-foo"
_s241 = "fooMap"
_s242 = "x-foo-"
_s243 = "HttpPrefixHeadersOutput"
_s244 = "QueryMap"
_s245 = "HttpQueryParamsOnlyInput"
_s246 = "queryMap"
_s247 = "HttpRequestWithFloatLabelsInput"
_s248 = "float"
_s249 = "double"
_s250 = "HttpRequestWithGreedyLabelInPathInput"
_s251 = "EpochSeconds"
_s252 = "epoch-seconds"
_s253 = "HttpDate"
_s254 = "http-date"
_s255 = "HttpRequestWithLabelsAndTimestampFormatInput"
_s256 = "memberEpochSeconds"
_s257 = "smithy.api#httpLabel"
_s258 = "memberHttpDate"
_s259 = "memberDateTime"
_s260 = "defaultFormat"
_s261 = "targetEpochSeconds"
_s262 = "targetHttpDate"
_s263 = "targetDateTime"
_s264 = "HttpRequestWithLabelsInput"
_s265 = "string"
_s266 = "short"
_s267 = "integer"
_s268 = "long"
_s269 = "boolean"
_s270 = "timestamp"
_s271 = "HttpRequestWithRegexLiteralInput"
_s272 = "str"
_s273 = "HttpResponseCodeOutput"
_s274 = "Status"
_s275 = "IgnoreQueryParamsInResponseOutput"
_s276 = "InputAndOutputWithHeadersIO"
_s277 = "headerString"
_s278 = "X-String"
_s279 = "headerByte"
_s280 = "X-Byte"
_s281 = "headerShort"
_s282 = "X-Short"
_s283 = "headerInteger"
_s284 = "X-Integer"
_s285 = "headerLong"
_s286 = "X-Long"
_s287 = "headerFloat"
_s288 = "X-Float"
_s289 = "headerDouble"
_s290 = "X-Double"
_s291 = "headerTrueBool"
_s292 = "X-Boolean1"
_s293 = "headerFalseBool"
_s294 = "X-Boolean2"
_s295 = "headerStringList"
_s296 = "X-StringList"
_s297 = "headerStringSet"
_s298 = "X-StringSet"
_s299 = "headerIntegerList"
_s300 = "X-IntegerList"
_s301 = "headerBooleanList"
_s302 = "X-BooleanList"
_s303 = "headerTimestampList"
_s304 = "X-TimestampList"
_s305 = "headerEnum"
_s306 = "X-Enum"
_s307 = "headerEnumList"
_s308 = "X-EnumList"
_s309 = "headerIntegerEnum"
_s310 = "X-IntegerEnum"
_s311 = "headerIntegerEnumList"
_s312 = "X-IntegerEnumList"
_s313 = "InputStreamInput"
_s314 = "InputStreamWithInitialRequestInput"
_s315 = "InvalidGreeting"
_s316 = "Message"
_s317 = "JsonBlobsInputOutput"
_s318 = "data"
_s319 = "FooEnumSet"
_s320 = "FooEnumMap"
_s321 = "JsonEnumsInputOutput"
_s322 = "fooEnum1"
_s323 = "fooEnum2"
_s324 = "fooEnum3"
_s325 = "fooEnumList"
_s326 = "fooEnumSet"
_s327 = "fooEnumMap"
_s328 = "JsonHeaderString"
_s329 = "application/json"
_s330 = "IntegerEnumSet"
_s331 = "IntegerEnumMap"
_s332 = "JsonIntEnumsInputOutput"
_s333 = "integerEnum1"
_s334 = "integerEnum2"
_s335 = "integerEnum3"
_s336 = "integerEnumList"
_s337 = "integerEnumSet"
_s338 = "integerEnumMap"
_s339 = "NestedStringList"
_s340 = "StructureListMember"
_s341 = "a"
_s342 = "b"
_s343 = "other"
_s344 = "StructureList"
_s345 = "JsonListsInputOutput"
_s346 = "stringList"
_s347 = "stringSet"
_s348 = "integerList"
_s349 = "booleanList"
_s350 = "timestampList"
_s351 = "enumList"
_s352 = "intEnumList"
_s353 = "nestedStringList"
_s354 = "structureList"
_s355 = "myStructureList"
_s356 = "JsonMapsInputOutput"
_s357 = "denseStructMap"
_s358 = "denseNumberMap"
_s359 = "denseBooleanMap"
_s360 = "denseStringMap"
_s361 = "denseSetMap"
_s362 = "JsonTimestampsInputOutput"
_s363 = "normal"
_s364 = "dateTime"
_s365 = "dateTimeOnTarget"
_s366 = "epochSeconds"
_s367 = "epochSecondsOnTarget"
_s368 = "httpDate"
_s369 = "httpDateOnTarget"
_s370 = "JsonValue"
_s371 = "MalformedAcceptWithGenericStringOutput"
_s372 = "JpegBlob"
_s373 = "image/jpeg"
_s374 = "MalformedAcceptWithPayloadOutput"
_s375 = "MalformedBlobInput"
_s376 = "MalformedBooleanInput"
_s377 = "booleanInBody"
_s378 = "booleanInPath"
_s379 = "booleanInQuery"
_s380 = "booleanInHeader"
_s381 = "MalformedByteInput"
_s382 = "byteInBody"
_s383 = "byteInPath"
_s384 = "byteInQuery"
_s385 = "byteInHeader"
_s386 = "MalformedContentTypeWithGenericStringInput"
_s387 = "MalformedContentTypeWithPayloadInput"
_s388 = "MalformedContentTypeWithoutBodyEmptyInputInput"
_s389 = "MalformedDoubleInput"
_s390 = "doubleInBody"
_s391 = "doubleInPath"
_s392 = "doubleInQuery"
_s393 = "doubleInHeader"
_s394 = "MalformedFloatInput"
_s395 = "floatInBody"
_s396 = "floatInPath"
_s397 = "floatInQuery"
_s398 = "floatInHeader"
_s399 = "MalformedIntegerInput"
_s400 = "integerInBody"
_s401 = "integerInPath"
_s402 = "integerInQuery"
_s403 = "integerInHeader"
_s404 = "SimpleList"
_s405 = "MalformedListInput"
_s406 = "bodyList"
_s407 = "MalformedLongInput"
_s408 = "longInBody"
_s409 = "longInPath"
_s410 = "longInQuery"
_s411 = "longInHeader"
_s412 = "SimpleMap"
_s413 = "MalformedMapInput"
_s414 = "bodyMap"
_s415 = "MalformedRequestBodyInput"
_s416 = "int"
_s417 = "MalformedShortInput"
_s418 = "shortInBody"
_s419 = "shortInPath"
_s420 = "shortInQuery"
_s421 = "shortInHeader"
_s422 = "MalformedStringInput"
_s423 = "amz-media-typed-header"
_s424 = "MalformedTimestampBodyDateTimeInput"
_s425 = "MalformedTimestampBodyDefaultInput"
_s426 = "MalformedTimestampBodyHttpDateInput"
_s427 = "MalformedTimestampHeaderDateTimeInput"
_s428 = "MalformedTimestampHeaderDefaultInput"
_s429 = "MalformedTimestampHeaderEpochInput"
_s430 = "MalformedTimestampPathDefaultInput"

HTTP_PAYLOAD_TRAITS_WITH_MEDIA_TYPE_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s230,
    {_s30: None, _s88: None},
    (
        _s217,
        _s226,
    ),
    (
        (3, {_s77: _s225}),
        (lambda: schemas.TEXT_PLAIN_BLOB, 16),
    ),
)

NESTED_PAYLOAD: StaticSchema = (
    18,
    n1,
    _s231,
    0,
    (
        _s143,
        _s232,
    ),
    (
        (3, 0),
        (3, 0),
    ),
)

HTTP_PAYLOAD_WITH_STRUCTURE_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s233,
    {_s30: None, _s88: None},
    (_s234,),
    ((NESTED_PAYLOAD, 16),),
)

UNION_PAYLOAD: StaticSchema = (
    19,
    n1,
    _s235,
    0,
    (_s143,),
    ((3, 0),),
)

HTTP_PAYLOAD_WITH_UNION_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s236,
    {_s30: None, _s88: None},
    (_s234,),
    ((UNION_PAYLOAD, 16),),
)

HTTP_PREFIX_HEADERS_IN_RESPONSE_INPUT: StaticSchema = (
    18,
    n1,
    _s237,
    {_s30: None},
)

HTTP_PREFIX_HEADERS_IN_RESPONSE_OUTPUT: StaticSchema = (
    18,
    n1,
    _s238,
    {_s88: None},
    (_s220,),
    ((lambda: schemas.STRING_MAP, {_s221: _s123}),),
)

HTTP_PREFIX_HEADERS_INPUT: StaticSchema = (
    18,
    n1,
    _s239,
    {_s30: None},
    (
        _s217,
        _s241,
    ),
    (
        (3, {_s77: _s240}),
        (lambda: schemas.STRING_MAP, {_s221: _s242}),
    ),
)

HTTP_PREFIX_HEADERS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s243,
    {_s88: None},
    (
        _s217,
        _s241,
    ),
    (
        (3, {_s77: _s240}),
        (lambda: schemas.STRING_MAP, {_s221: _s242}),
    ),
)

QUERY_MAP: StaticSchema = (
    17,
    n1,
    _s244,
    0,
    (
        _s27,
        _s28,
    ),
    (
        (3, 0),
        (3, 0),
    ),
)

HTTP_QUERY_PARAMS_ONLY_INPUT: StaticSchema = (
    18,
    n1,
    _s245,
    {_s30: None},
    (_s246,),
    ((QUERY_MAP, 1024),),
)

HTTP_REQUEST_WITH_FLOAT_LABELS_INPUT: StaticSchema = (
    18,
    n1,
    _s247,
    {_s30: None},
    (
        _s248,
        _s249,
    ),
    (
        (9, 9),
        (10, 9),
    ),
)

HTTP_REQUEST_WITH_GREEDY_LABEL_IN_PATH_INPUT: StaticSchema = (
    18,
    n1,
    _s250,
    {_s30: None},
    (
        _s217,
        _s82,
    ),
    (
        (3, 9),
        (3, 9),
    ),
)

EPOCH_SECONDS: StaticSchema = (
    4,
    n0,
    _s251,
    {_s90: _s252},
)

HTTP_DATE: StaticSchema = (
    4,
    n0,
    _s253,
    {_s90: _s254},
)

HTTP_REQUEST_WITH_LABELS_AND_TIMESTAMP_FORMAT_INPUT: StaticSchema = (
    18,
    n1,
    _s255,
    {_s30: None},
    (
        _s256,
        _s258,
        _s259,
        _s260,
        _s261,
        _s262,
        _s263,
    ),
    (
        (4, {_s90: _s252, _s257: None, _s197: None}),
        (4, {_s90: _s254, _s257: None, _s197: None}),
        (4, {_s90: _s91, _s257: None, _s197: None}),
        (4, 9),
        (EPOCH_SECONDS, 9),
        (HTTP_DATE, 9),
        (lambda: schemas.DATE_TIME, 9),
    ),
)

HTTP_REQUEST_WITH_LABELS_INPUT: StaticSchema = (
    18,
    n1,
    _s264,
    {_s30: None},
    (
        _s265,
        _s266,
        _s267,
        _s268,
        _s248,
        _s249,
        _s269,
        _s270,
    ),
    (
        (3, 9),
        (6, 9),
        (7, 9),
        (8, 9),
        (9, 9),
        (10, 9),
        (2, 9),
        (4, 9),
    ),
)

HTTP_REQUEST_WITH_REGEX_LITERAL_INPUT: StaticSchema = (
    18,
    n1,
    _s271,
    {_s30: None},
    (_s272,),
    ((3, 9),),
)

HTTP_RESPONSE_CODE_OUTPUT: StaticSchema = (
    18,
    n1,
    _s273,
    {_s88: None},
    (_s274,),
    ((7, 128),),
)

IGNORE_QUERY_PARAMS_IN_RESPONSE_OUTPUT: StaticSchema = (
    18,
    n1,
    _s275,
    {_s88: None},
    (_s82,),
    ((3, {_s32: _s82}),),
)

INPUT_AND_OUTPUT_WITH_HEADERS_IO: StaticSchema = (
    18,
    n1,
    _s276,
    {_s30: None, _s88: None},
    (
        _s277,
        _s279,
        _s281,
        _s283,
        _s285,
        _s287,
        _s289,
        _s291,
        _s293,
        _s295,
        _s297,
        _s299,
        _s301,
        _s303,
        _s305,
        _s307,
        _s309,
        _s311,
    ),
    (
        (3, {_s77: _s278}),
        (5, {_s77: _s280}),
        (6, {_s77: _s282}),
        (7, {_s77: _s284}),
        (8, {_s77: _s286}),
        (9, {_s77: _s288}),
        (10, {_s77: _s290}),
        (2, {_s77: _s292}),
        (2, {_s77: _s294}),
        (lambda: schemas.STRING_LIST, {_s77: _s296}),
        (lambda: schemas.STRING_SET, {_s77: _s298}),
        (lambda: schemas.INTEGER_LIST, {_s77: _s300}),
        (lambda: schemas.BOOLEAN_LIST, {_s77: _s302}),
        (lambda: schemas.TIMESTAMP_LIST, {_s77: _s304}),
        (lambda: schemas.FOO_ENUM, {_s77: _s306}),
        (lambda: schemas.FOO_ENUM_LIST, {_s77: _s308}),
        (lambda: schemas.INTEGER_ENUM, {_s77: _s310}),
        (lambda: schemas.INTEGER_ENUM_LIST, {_s77: _s312}),
    ),
)

INPUT_STREAM_INPUT: StaticSchema = (
    18,
    n1,
    _s313,
    {_s30: None},
    (_s187,),
    ((lambda: schemas.EVENT_STREAM, 16),),
)

INPUT_STREAM_WITH_INITIAL_REQUEST_INPUT: StaticSchema = (
    18,
    n1,
    _s314,
    {_s30: None},
    (
        _s195,
        _s187,
    ),
    (
        (3, {_s77: _s196, _s197: None}),
        (lambda: schemas.EVENT_STREAM, 16),
    ),
)

INVALID_GREETING: StaticSchema = (
    18,
    n1,
    _s315,
    {_s73: _s74, _s75: 400},
    (_s316,),
    ((3, 0),),
)

JSON_BLOBS_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s317,
    {_s30: None, _s88: None},
    (_s318,),
    ((1, 0),),
)

FOO_ENUM_SET: StaticSchema = (
    16,
    n0,
    _s319,
    0,
    (_s1,),
    ((lambda: schemas.FOO_ENUM, 0),),
)

FOO_ENUM_MAP: StaticSchema = (
    17,
    n0,
    _s320,
    0,
    (
        _s27,
        _s28,
    ),
    (
        (3, 0),
        (lambda: schemas.FOO_ENUM, 0),
    ),
)

JSON_ENUMS_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s321,
    {_s30: None, _s88: None},
    (
        _s322,
        _s323,
        _s324,
        _s325,
        _s326,
        _s327,
    ),
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
    _s328,
    {_s228: _s329},
)

INTEGER_ENUM_SET: StaticSchema = (
    16,
    n0,
    _s330,
    0,
    (_s1,),
    ((lambda: schemas.INTEGER_ENUM, 0),),
)

INTEGER_ENUM_MAP: StaticSchema = (
    17,
    n0,
    _s331,
    0,
    (
        _s27,
        _s28,
    ),
    (
        (3, 0),
        (lambda: schemas.INTEGER_ENUM, 0),
    ),
)

JSON_INT_ENUMS_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s332,
    {_s30: None, _s88: None},
    (
        _s333,
        _s334,
        _s335,
        _s336,
        _s337,
        _s338,
    ),
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
    _s339,
    0,
    (_s1,),
    ((lambda: schemas.STRING_LIST, 0),),
)

STRUCTURE_LIST_MEMBER: StaticSchema = (
    18,
    n1,
    _s340,
    0,
    (
        _s341,
        _s342,
    ),
    (
        (3, {_s70: _s28}),
        (3, {_s70: _s343}),
    ),
)

STRUCTURE_LIST: StaticSchema = (
    16,
    n1,
    _s344,
    0,
    (_s1,),
    ((STRUCTURE_LIST_MEMBER, 0),),
)

JSON_LISTS_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s345,
    {_s30: None, _s88: None},
    (
        _s346,
        _s347,
        _s348,
        _s349,
        _s350,
        _s351,
        _s352,
        _s353,
        _s354,
    ),
    (
        (lambda: schemas.STRING_LIST, 0),
        (lambda: schemas.STRING_SET, 0),
        (lambda: schemas.INTEGER_LIST, 0),
        (lambda: schemas.BOOLEAN_LIST, 0),
        (lambda: schemas.TIMESTAMP_LIST, 0),
        (lambda: schemas.FOO_ENUM_LIST, 0),
        (lambda: schemas.INTEGER_ENUM_LIST, 0),
        (NESTED_STRING_LIST, 0),
        (STRUCTURE_LIST, {_s70: _s355}),
    ),
)

JSON_MAPS_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s356,
    {_s30: None, _s88: None},
    (
        _s357,
        _s358,
        _s359,
        _s360,
        _s361,
    ),
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
    _s362,
    {_s30: None, _s88: None},
    (
        _s363,
        _s364,
        _s365,
        _s366,
        _s367,
        _s368,
        _s369,
    ),
    (
        (4, 0),
        (4, {_s90: _s91}),
        (lambda: schemas.DATE_TIME, 0),
        (4, {_s90: _s252}),
        (EPOCH_SECONDS, 0),
        (4, {_s90: _s254}),
        (HTTP_DATE, 0),
    ),
)

JSON_VALUE: StaticSchema = (
    3,
    n1,
    _s370,
    {_s228: _s329},
)

MALFORMED_ACCEPT_WITH_GENERIC_STRING_OUTPUT: StaticSchema = (
    18,
    n1,
    _s371,
    {_s88: None},
    (_s65,),
    ((3, 16),),
)

JPEG_BLOB: StaticSchema = (
    1,
    n0,
    _s372,
    {_s228: _s373},
)

MALFORMED_ACCEPT_WITH_PAYLOAD_OUTPUT: StaticSchema = (
    18,
    n1,
    _s374,
    {_s88: None},
    (_s65,),
    ((JPEG_BLOB, 16),),
)

MALFORMED_BLOB_INPUT: StaticSchema = (
    18,
    n1,
    _s375,
    {_s30: None},
    (_s226,),
    ((1, 0),),
)

MALFORMED_BOOLEAN_INPUT: StaticSchema = (
    18,
    n1,
    _s376,
    {_s30: None},
    (
        _s377,
        _s378,
        _s379,
        _s380,
    ),
    (
        (2, 0),
        (2, 9),
        (2, {_s32: _s379}),
        (2, {_s77: _s380}),
    ),
)

MALFORMED_BYTE_INPUT: StaticSchema = (
    18,
    n1,
    _s381,
    {_s30: None},
    (
        _s382,
        _s383,
        _s384,
        _s385,
    ),
    (
        (5, 0),
        (5, 9),
        (5, {_s32: _s384}),
        (5, {_s77: _s385}),
    ),
)

MALFORMED_CONTENT_TYPE_WITH_GENERIC_STRING_INPUT: StaticSchema = (
    18,
    n1,
    _s386,
    {_s30: None},
    (_s65,),
    ((3, 16),),
)

MALFORMED_CONTENT_TYPE_WITH_PAYLOAD_INPUT: StaticSchema = (
    18,
    n1,
    _s387,
    {_s30: None},
    (_s65,),
    ((JPEG_BLOB, 16),),
)

MALFORMED_CONTENT_TYPE_WITHOUT_BODY_EMPTY_INPUT_INPUT: StaticSchema = (
    18,
    n1,
    _s388,
    {_s30: None},
    (_s172,),
    ((3, {_s77: _s172}),),
)

MALFORMED_DOUBLE_INPUT: StaticSchema = (
    18,
    n1,
    _s389,
    {_s30: None},
    (
        _s390,
        _s391,
        _s392,
        _s393,
    ),
    (
        (10, 0),
        (10, 9),
        (10, {_s32: _s392}),
        (10, {_s77: _s393}),
    ),
)

MALFORMED_FLOAT_INPUT: StaticSchema = (
    18,
    n1,
    _s394,
    {_s30: None},
    (
        _s395,
        _s396,
        _s397,
        _s398,
    ),
    (
        (9, 0),
        (9, 9),
        (9, {_s32: _s397}),
        (9, {_s77: _s398}),
    ),
)

MALFORMED_INTEGER_INPUT: StaticSchema = (
    18,
    n1,
    _s399,
    {_s30: None},
    (
        _s400,
        _s401,
        _s402,
        _s403,
    ),
    (
        (7, 0),
        (7, 9),
        (7, {_s32: _s402}),
        (7, {_s77: _s403}),
    ),
)

SIMPLE_LIST: StaticSchema = (
    16,
    n1,
    _s404,
    0,
    (_s1,),
    ((3, 0),),
)

MALFORMED_LIST_INPUT: StaticSchema = (
    18,
    n1,
    _s405,
    {_s30: None},
    (_s406,),
    ((SIMPLE_LIST, 0),),
)

MALFORMED_LONG_INPUT: StaticSchema = (
    18,
    n1,
    _s407,
    {_s30: None},
    (
        _s408,
        _s409,
        _s410,
        _s411,
    ),
    (
        (8, 0),
        (8, 9),
        (8, {_s32: _s410}),
        (8, {_s77: _s411}),
    ),
)

SIMPLE_MAP: StaticSchema = (
    17,
    n1,
    _s412,
    0,
    (
        _s27,
        _s28,
    ),
    (
        (3, 0),
        (3, 0),
    ),
)

MALFORMED_MAP_INPUT: StaticSchema = (
    18,
    n1,
    _s413,
    {_s30: None},
    (_s414,),
    ((SIMPLE_MAP, 0),),
)

MALFORMED_REQUEST_BODY_INPUT: StaticSchema = (
    18,
    n1,
    _s415,
    {_s30: None},
    (
        _s416,
        _s248,
    ),
    (
        (7, 0),
        (9, 0),
    ),
)

MALFORMED_SHORT_INPUT: StaticSchema = (
    18,
    n1,
    _s417,
    {_s30: None},
    (
        _s418,
        _s419,
        _s420,
        _s421,
    ),
    (
        (6, 0),
        (6, 9),
        (6, {_s32: _s420}),
        (6, {_s77: _s421}),
    ),
)

MALFORMED_STRING_INPUT: StaticSchema = (
    18,
    n1,
    _s422,
    {_s30: None},
    (_s226,),
    ((JSON_HEADER_STRING, {_s77: _s423}),),
)

MALFORMED_TIMESTAMP_BODY_DATE_TIME_INPUT: StaticSchema = (
    18,
    n1,
    _s424,
    {_s30: None},
    (_s270,),
    ((4, {_s90: _s91, _s197: None}),),
)

MALFORMED_TIMESTAMP_BODY_DEFAULT_INPUT: StaticSchema = (
    18,
    n1,
    _s425,
    {_s30: None},
    (_s270,),
    ((4, 1),),
)

MALFORMED_TIMESTAMP_BODY_HTTP_DATE_INPUT: StaticSchema = (
    18,
    n1,
    _s426,
    {_s30: None},
    (_s270,),
    ((4, {_s90: _s254, _s197: None}),),
)

MALFORMED_TIMESTAMP_HEADER_DATE_TIME_INPUT: StaticSchema = (
    18,
    n1,
    _s427,
    {_s30: None},
    (_s270,),
    ((4, {_s77: _s270, _s90: _s91, _s197: None}),),
)

MALFORMED_TIMESTAMP_HEADER_DEFAULT_INPUT: StaticSchema = (
    18,
    n1,
    _s428,
    {_s30: None},
    (_s270,),
    ((4, {_s77: _s270, _s197: None}),),
)

MALFORMED_TIMESTAMP_HEADER_EPOCH_INPUT: StaticSchema = (
    18,
    n1,
    _s429,
    {_s30: None},
    (_s270,),
    ((4, {_s77: _s270, _s90: _s252, _s197: None}),),
)

MALFORMED_TIMESTAMP_PATH_DEFAULT_INPUT: StaticSchema = (
    18,
    n1,
    _s430,
    {_s30: None},
    (_s270,),
    ((4, 9),),
)
