from types import MappingProxyType

from smithy_core._schema_compact import StaticSchema

from . import schemas

n0 = "aws.protocoltests.shared"
_s0 = "StringList"
_s1 = "member"
_s3 = "IntegerList"
_s5 = "DoubleList"
_s6 = "BooleanList"
_s7 = "TimestampList"
_s9 = "FOO"
_s25 = "IntegerEnumList"
_s27 = "key"
_s28 = "value"
n1 = "aws.protocoltests.restjson"
_s30 = "smithy.api#input"
_s32 = "smithy.api#httpQuery"
_s34 = "queryStringList"
_s42 = "queryIntegerList"
_s50 = "queryDoubleList"
_s53 = "queryBooleanList"
_s56 = "queryTimestampList"
_s59 = "queryEnumList"
_s60 = "EnumList"
_s62 = "queryIntegerEnumList"
_s65 = "payload"
_s69 = "smithy.api#default"
_s71 = "smithy.api#jsonName"
_s78 = "smithy.api#httpHeader"
_s80 = "TopLevel"
_s83 = "baz"
_s89 = "smithy.api#output"
_s91 = "smithy.api#timestampFormat"
_s92 = "date-time"
_s102 = "defaultString"
_s103 = "hi"
_s104 = "defaultBoolean"
_s105 = "defaultList"
_s106 = "defaultDocumentMap"
_s107 = "defaultDocumentString"
_s108 = "defaultDocumentBoolean"
_s109 = "defaultDocumentList"
_s110 = "defaultNullDocument"
_s111 = "defaultTimestamp"
_s112 = "defaultBlob"
_s113 = "YWJj"
_s114 = "defaultByte"
_s115 = "defaultShort"
_s116 = "defaultInteger"
_s117 = "defaultLong"
_s118 = "defaultFloat"
_s119 = "defaultDouble"
_s120 = "defaultMap"
_s121 = "defaultEnum"
_s122 = "defaultIntEnum"
_s123 = "emptyString"
_s124 = ""
_s125 = "falseBoolean"
_s126 = "emptyBlob"
_s127 = "zeroByte"
_s128 = "zeroShort"
_s129 = "zeroInteger"
_s130 = "zeroLong"
_s131 = "zeroFloat"
_s132 = "zeroDouble"
_s137 = "GreetingStruct"
_s154 = "stringValue"
_s178 = "smithy.api#streaming"
_s188 = "stream"
_s198 = "smithy.api#required"
_s200 = "initialResponseMember"
_s201 = "initial-response-member"
_s218 = "foo"
_s226 = "X-Foo"
_s227 = "blob"
_s229 = "smithy.api#mediaType"
_s230 = "text/plain"
_s235 = "nested"
_s253 = "epoch-seconds"
_s255 = "http-date"
_s257 = "memberEpochSeconds"
_s258 = "smithy.api#httpLabel"
_s259 = "memberHttpDate"
_s260 = "memberDateTime"
_s261 = "defaultFormat"
_s262 = "targetEpochSeconds"
_s263 = "targetHttpDate"
_s264 = "targetDateTime"
_s266 = "string"
_s271 = "timestamp"
_s319 = "data"
_s417 = "int"
_s432 = "MalformedTimestampPathEpochInput"
_s433 = "MalformedTimestampPathHttpDateInput"
_s434 = "MalformedTimestampQueryDefaultInput"
_s435 = "MalformedTimestampQueryEpochInput"
_s436 = "MalformedTimestampQueryHttpDateInput"
_s437 = "SimpleUnion"
_s438 = "MalformedUnionInput"
_s439 = "union"
_s440 = "MediaTypeHeaderInput"
_s441 = "json"
_s442 = "X-Json"
_s443 = "MediaTypeHeaderOutput"
n2 = "aws.protocoltests.restjson.nested"
_s444 = "salutation"
_s445 = "NestedUnion"
_s446 = "MyUnion"
_s447 = "booleanValue"
_s448 = "numberValue"
_s449 = "blobValue"
_s450 = "timestampValue"
_s451 = "enumValue"
_s452 = "listValue"
_s453 = "mapValue"
_s454 = "structureValue"
_s455 = "renamedStructureValue"
_s456 = "unionValue"
_s457 = "NoInputAndOutputOutput"
_s463 = "OmitsNullSerializesEmptyStringInput"
_s464 = "nullValue"
_s465 = "Null"
_s466 = "Empty"
_s467 = "OmitsSerializingEmptyListsInput"
_s468 = "OperationWithDefaultsInput"
_s469 = "defaults"
_s470 = "clientOptionalDefaults"
_s471 = "topLevelDefault"
_s472 = "otherTopLevelDefault"
_s473 = "OperationWithDefaultsOutput"
_s474 = "dialog"
_s475 = "dialogList"
_s476 = "dialogMap"
_s477 = "OperationWithNestedStructureInput"
_s478 = "topLevel"
_s479 = "OperationWithNestedStructureOutput"
_s480 = "OutputStreamOutput"
_s481 = "OutputStreamWithInitialResponseOutput"
_s482 = "PayloadConfig"
_s483 = "PlayerAction"
_s484 = "quit"
_s485 = "PostPlayerActionInput"
_s486 = "action"
_s487 = "PostPlayerActionOutput"
_s488 = "UnionWithJsonName"
_s489 = "bar"
_s490 = "_baz"
_s491 = "PostUnionWithJsonNameInput"
_s492 = "PostUnionWithJsonNameOutput"
_s493 = "PutWithContentEncodingInput"
_s494 = "encoding"
_s495 = "Content-Encoding"
_s496 = "QueryIdempotencyTokenAutoFillInput"
_s497 = "token"
_s498 = "smithy.api#idempotencyToken"
_s499 = "QueryParamsAsStringListMapInput"
_s500 = "qux"
_s501 = "corge"
_s502 = "QueryPrecedenceInput"
_s503 = "RecursiveShapesInputOutput"
_s504 = "ResponseCodeHttpFallbackInputOutput"
_s505 = "ResponseCodeRequiredOutput"
_s506 = "responseCode"
_s508 = "SimpleScalarPropertiesInputOutput"
_s509 = "trueBooleanValue"
_s510 = "falseBooleanValue"
_s511 = "byteValue"
_s512 = "shortValue"
_s513 = "integerValue"
_s514 = "longValue"
_s515 = "floatValue"
_s516 = "doubleValue"
_s517 = "DoubleDribble"
_s518 = "SparseBooleanMap"
_s519 = "SparseStringList"
_s520 = "SparseShortList"
_s521 = "SparseJsonListsInputOutput"
_s522 = "sparseStringList"
_s523 = "sparseShortList"
_s524 = "SparseStructMap"
_s525 = "SparseNumberMap"
_s526 = "SparseStringMap"
_s527 = "SparseSetMap"
_s528 = "SparseJsonMapsInputOutput"
_s529 = "sparseStructMap"
_s530 = "sparseNumberMap"
_s531 = "sparseBooleanMap"
_s532 = "sparseStringMap"
_s533 = "sparseSetMap"
_s534 = "StreamingBlob"
_s535 = "StreamingTextPlainBlob"
_s536 = "StreamingTraitsInputOutput"
_s537 = "smithy.api#httpPayload"
_s538 = "StreamingTraitsRequireLengthInput"
_s539 = "StreamingTraitsWithMediaTypeInputOutput"
_s540 = "StringPayloadInput"
_s541 = "TestConfig"
_s542 = "timeout"
_s543 = "TestBodyStructureInputOutput"
_s544 = "testId"
_s545 = "x-amz-test-id"
_s546 = "testConfig"
_s547 = "TestNoPayloadInputOutput"
_s548 = "X-Amz-Test-Id"
_s549 = "TestPayloadBlobInputOutput"
_s550 = "contentType"
_s551 = "Content-Type"
_s552 = "TestPayloadStructureInputOutput"
_s553 = "payloadConfig"
_s554 = "TimestampFormatHeadersIO"
_s555 = "X-memberEpochSeconds"
_s556 = "X-memberHttpDate"
_s557 = "X-memberDateTime"
_s558 = "X-defaultFormat"
_s559 = "X-targetEpochSeconds"
_s560 = "X-targetHttpDate"
_s561 = "X-targetDateTime"
_s562 = "UnionInputOutput"
_s563 = "contents"
_s564 = "RecursiveShapesInputOutputNested1"
_s565 = "RecursiveShapesInputOutputNested2"
_s566 = "recursiveMember"

MALFORMED_TIMESTAMP_PATH_EPOCH_INPUT: StaticSchema = (
    18,
    n1,
    _s432,
    {_s30: None},
    (_s271,),
    ((4, {_s91: _s253, _s258: None, _s198: None}),),
)

MALFORMED_TIMESTAMP_PATH_HTTP_DATE_INPUT: StaticSchema = (
    18,
    n1,
    _s433,
    {_s30: None},
    (_s271,),
    ((4, {_s91: _s255, _s258: None, _s198: None}),),
)

MALFORMED_TIMESTAMP_QUERY_DEFAULT_INPUT: StaticSchema = (
    18,
    n1,
    _s434,
    {_s30: None},
    (_s271,),
    ((4, {_s32: _s271, _s198: None}),),
)

MALFORMED_TIMESTAMP_QUERY_EPOCH_INPUT: StaticSchema = (
    18,
    n1,
    _s435,
    {_s30: None},
    (_s271,),
    ((4, {_s32: _s271, _s91: _s253, _s198: None}),),
)

MALFORMED_TIMESTAMP_QUERY_HTTP_DATE_INPUT: StaticSchema = (
    18,
    n1,
    _s436,
    {_s30: None},
    (_s271,),
    ((4, {_s32: _s271, _s91: _s255, _s198: None}),),
)

SIMPLE_UNION: StaticSchema = (
    19,
    n1,
    _s437,
    0,
    (_s417, _s266),
    ((7, 0), (3, 0)),
)

MALFORMED_UNION_INPUT: StaticSchema = (
    18,
    n1,
    _s438,
    {_s30: None},
    (_s439,),
    ((SIMPLE_UNION, 0),),
)

MEDIA_TYPE_HEADER_INPUT: StaticSchema = (
    18,
    n1,
    _s440,
    {_s30: None},
    (_s441,),
    ((lambda: schemas.JSON_VALUE, {_s78: _s442}),),
)

MEDIA_TYPE_HEADER_OUTPUT: StaticSchema = (
    18,
    n1,
    _s443,
    {_s89: None},
    (_s441,),
    ((lambda: schemas.JSON_VALUE, {_s78: _s442}),),
)

RENAMED_GREETING: StaticSchema = (
    18,
    n2,
    _s137,
    0,
    (_s444,),
    ((3, 0),),
)

NESTED_UNION: StaticSchema = (
    19,
    n1,
    _s445,
    0,
    (_s154,),
    ((3, 0),),
)

MY_UNION: StaticSchema = (
    19,
    n1,
    _s446,
    0,
    (_s154, _s447, _s448, _s449, _s450, _s451, _s452, _s453, _s454, _s455, _s456),
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

NO_INPUT_AND_OUTPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s457,
    {_s89: None},
)

OMITS_NULL_SERIALIZES_EMPTY_STRING_INPUT: StaticSchema = (
    18,
    n1,
    _s463,
    {_s30: None},
    (_s464, _s123),
    ((3, {_s32: _s465}), (3, {_s32: _s466})),
)

OMITS_SERIALIZING_EMPTY_LISTS_INPUT: StaticSchema = (
    18,
    n1,
    _s467,
    {_s30: None},
    (_s34, _s42, _s50, _s53, _s56, _s59, _s62),
    (
        (lambda: schemas.STRING_LIST, {_s32: _s0}),
        (lambda: schemas.INTEGER_LIST, {_s32: _s3}),
        (lambda: schemas.DOUBLE_LIST, {_s32: _s5}),
        (lambda: schemas.BOOLEAN_LIST, {_s32: _s6}),
        (lambda: schemas.TIMESTAMP_LIST, {_s32: _s7}),
        (lambda: schemas.FOO_ENUM_LIST, {_s32: _s60}),
        (lambda: schemas.INTEGER_ENUM_LIST, {_s32: _s25}),
    ),
)

OPERATION_WITH_DEFAULTS_INPUT: StaticSchema = (
    18,
    n1,
    _s468,
    {_s30: None},
    (_s469, _s470, _s471, _s472),
    (
        (lambda: schemas.DEFAULTS, 0),
        (lambda: schemas.CLIENT_OPTIONAL_DEFAULTS, 0),
        (3, {_s69: _s103}),
        (7, {_s69: 0}),
    ),
)

OPERATION_WITH_DEFAULTS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s473,
    {_s89: None},
    (
        _s102,
        _s104,
        _s105,
        _s106,
        _s107,
        _s108,
        _s109,
        _s110,
        _s111,
        _s112,
        _s114,
        _s115,
        _s116,
        _s117,
        _s118,
        _s119,
        _s120,
        _s121,
        _s122,
        _s123,
        _s125,
        _s126,
        _s127,
        _s128,
        _s129,
        _s130,
        _s131,
        _s132,
    ),
    (
        (3, {_s69: _s103}),
        (2, {_s69: True}),
        (lambda: schemas.TEST_STRING_LIST, {_s69: ()}),
        (lambda: schemas.DOCUMENT, {_s69: MappingProxyType[str, object]({})}),
        (lambda: schemas.DOCUMENT, {_s69: _s103}),
        (lambda: schemas.DOCUMENT, {_s69: True}),
        (lambda: schemas.DOCUMENT, {_s69: ()}),
        (lambda: schemas.DOCUMENT, {_s69: None}),
        (4, {_s69: 0}),
        (1, {_s69: _s113}),
        (5, {_s69: 1}),
        (6, {_s69: 1}),
        (7, {_s69: 10}),
        (8, {_s69: 100}),
        (9, {_s69: 1.0}),
        (10, {_s69: 1.0}),
        (lambda: schemas.TEST_STRING_MAP, {_s69: MappingProxyType[str, object]({})}),
        (lambda: schemas.TEST_ENUM, {_s69: _s9}),
        (lambda: schemas.TEST_INT_ENUM, {_s69: 1}),
        (3, {_s69: _s124}),
        (2, {_s69: False}),
        (1, {_s69: _s124}),
        (5, {_s69: 0}),
        (6, {_s69: 0}),
        (7, {_s69: 0}),
        (8, {_s69: 0}),
        (9, {_s69: 0.0}),
        (10, {_s69: 0.0}),
    ),
)

TOP_LEVEL: StaticSchema = (
    18,
    n1,
    _s80,
    0,
    (_s474, _s475, _s476),
    (
        (lambda: schemas.DIALOG, 1),
        (lambda: schemas.DIALOG_LIST, {_s69: ()}),
        (lambda: schemas.DIALOG_MAP, {_s69: MappingProxyType[str, object]({})}),
    ),
)

OPERATION_WITH_NESTED_STRUCTURE_INPUT: StaticSchema = (
    18,
    n1,
    _s477,
    {_s30: None},
    (_s478,),
    ((TOP_LEVEL, 1),),
)

OPERATION_WITH_NESTED_STRUCTURE_OUTPUT: StaticSchema = (
    18,
    n1,
    _s479,
    {_s89: None},
    (_s474, _s475, _s476),
    (
        (lambda: schemas.DIALOG, 1),
        (lambda: schemas.DIALOG_LIST, {_s69: ()}),
        (lambda: schemas.DIALOG_MAP, {_s69: MappingProxyType[str, object]({})}),
    ),
)

OUTPUT_STREAM_OUTPUT: StaticSchema = (
    18,
    n1,
    _s480,
    {_s89: None},
    (_s188,),
    ((lambda: schemas.EVENT_STREAM, 16),),
)

OUTPUT_STREAM_WITH_INITIAL_RESPONSE_OUTPUT: StaticSchema = (
    18,
    n1,
    _s481,
    {_s89: None},
    (_s200, _s188),
    ((3, {_s78: _s201, _s198: None}), (lambda: schemas.EVENT_STREAM, 16)),
)

PAYLOAD_CONFIG: StaticSchema = (
    18,
    n1,
    _s482,
    0,
    (_s319,),
    ((7, 0),),
)

PLAYER_ACTION: StaticSchema = (
    19,
    n1,
    _s483,
    0,
    (_s484,),
    ((-1, 0),),
)

POST_PLAYER_ACTION_INPUT: StaticSchema = (
    18,
    n1,
    _s485,
    {_s30: None},
    (_s486,),
    ((PLAYER_ACTION, 0),),
)

POST_PLAYER_ACTION_OUTPUT: StaticSchema = (
    18,
    n1,
    _s487,
    {_s89: None},
    (_s486,),
    ((PLAYER_ACTION, 1),),
)

UNION_WITH_JSON_NAME: StaticSchema = (
    19,
    n1,
    _s488,
    0,
    (_s218, _s489, _s83),
    ((3, {_s71: _s9}), (3, 0), (3, {_s71: _s490})),
)

POST_UNION_WITH_JSON_NAME_INPUT: StaticSchema = (
    18,
    n1,
    _s491,
    {_s30: None},
    (_s28,),
    ((UNION_WITH_JSON_NAME, 0),),
)

POST_UNION_WITH_JSON_NAME_OUTPUT: StaticSchema = (
    18,
    n1,
    _s492,
    {_s89: None},
    (_s28,),
    ((UNION_WITH_JSON_NAME, 1),),
)

PUT_WITH_CONTENT_ENCODING_INPUT: StaticSchema = (
    18,
    n1,
    _s493,
    {_s30: None},
    (_s494, _s319),
    ((3, {_s78: _s495}), (3, 0)),
)

QUERY_IDEMPOTENCY_TOKEN_AUTO_FILL_INPUT: StaticSchema = (
    18,
    n1,
    _s496,
    {_s30: None},
    (_s497,),
    ((3, {_s32: _s497, _s498: None}),),
)

QUERY_PARAMS_AS_STRING_LIST_MAP_INPUT: StaticSchema = (
    18,
    n1,
    _s499,
    {_s30: None},
    (_s500, _s218),
    ((3, {_s32: _s501}), (lambda: schemas.STRING_LIST_MAP, 1024)),
)

QUERY_PRECEDENCE_INPUT: StaticSchema = (
    18,
    n1,
    _s502,
    {_s30: None},
    (_s218, _s83),
    ((3, {_s32: _s489}), (lambda: schemas.STRING_MAP, 1024)),
)

RECURSIVE_SHAPES_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s503,
    {_s30: None, _s89: None},
    (_s235,),
    ((lambda: RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED1, 0),),
)

RESPONSE_CODE_HTTP_FALLBACK_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s504,
    {_s30: None, _s89: None},
)

RESPONSE_CODE_REQUIRED_OUTPUT: StaticSchema = (
    18,
    n1,
    _s505,
    {_s89: None},
    (_s506,),
    ((7, 129),),
)

SIMPLE_SCALAR_PROPERTIES_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s508,
    {_s30: None, _s89: None},
    (_s218, _s154, _s509, _s510, _s511, _s512, _s513, _s514, _s515, _s516),
    (
        (3, {_s78: _s226}),
        (3, 0),
        (2, 0),
        (2, 0),
        (5, 0),
        (6, 0),
        (7, 0),
        (8, 0),
        (9, 0),
        (10, {_s71: _s517}),
    ),
)

SPARSE_BOOLEAN_MAP: StaticSchema = (
    17,
    n1,
    _s518,
    64,
    (_s27, _s28),
    ((3, 0), (2, 0)),
)

SPARSE_STRING_LIST: StaticSchema = (
    16,
    n0,
    _s519,
    64,
    (_s1,),
    ((3, 0),),
)

SPARSE_SHORT_LIST: StaticSchema = (
    16,
    n0,
    _s520,
    64,
    (_s1,),
    ((6, 0),),
)

SPARSE_JSON_LISTS_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s521,
    {_s30: None, _s89: None},
    (_s522, _s523),
    ((SPARSE_STRING_LIST, 0), (SPARSE_SHORT_LIST, 0)),
)

SPARSE_STRUCT_MAP: StaticSchema = (
    17,
    n1,
    _s524,
    64,
    (_s27, _s28),
    ((3, 0), (lambda: schemas.GREETING_STRUCT, 0)),
)

SPARSE_NUMBER_MAP: StaticSchema = (
    17,
    n1,
    _s525,
    64,
    (_s27, _s28),
    ((3, 0), (7, 0)),
)

SPARSE_STRING_MAP: StaticSchema = (
    17,
    n0,
    _s526,
    64,
    (_s27, _s28),
    ((3, 0), (3, 0)),
)

SPARSE_SET_MAP: StaticSchema = (
    17,
    n1,
    _s527,
    64,
    (_s27, _s28),
    ((3, 0), (lambda: schemas.STRING_SET, 0)),
)

SPARSE_JSON_MAPS_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s528,
    {_s30: None, _s89: None},
    (_s529, _s530, _s531, _s532, _s533),
    (
        (SPARSE_STRUCT_MAP, 0),
        (SPARSE_NUMBER_MAP, 0),
        (SPARSE_BOOLEAN_MAP, 0),
        (SPARSE_STRING_MAP, 0),
        (SPARSE_SET_MAP, 0),
    ),
)

STREAMING_BLOB: StaticSchema = (
    1,
    n1,
    _s534,
    {_s178: None},
)

STREAMING_TEXT_PLAIN_BLOB: StaticSchema = (
    1,
    n1,
    _s535,
    {_s229: _s230, _s178: None},
)

STREAMING_TRAITS_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s536,
    {_s30: None, _s89: None},
    (_s218, _s227),
    ((3, {_s78: _s226}), (STREAMING_BLOB, {_s69: _s124, _s537: None})),
)

STREAMING_TRAITS_REQUIRE_LENGTH_INPUT: StaticSchema = (
    18,
    n1,
    _s538,
    {_s30: None},
    (_s218, _s227),
    (
        (3, {_s78: _s226}),
        (lambda: schemas.FINITE_STREAMING_BLOB, {_s69: _s124, _s537: None}),
    ),
)

STREAMING_TRAITS_WITH_MEDIA_TYPE_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s539,
    {_s30: None, _s89: None},
    (_s218, _s227),
    ((3, {_s78: _s226}), (STREAMING_TEXT_PLAIN_BLOB, {_s69: _s124, _s537: None})),
)

STRING_PAYLOAD_INPUT: StaticSchema = (
    18,
    n1,
    _s540,
    {_s30: None, _s89: None},
    (_s65,),
    ((3, 16),),
)

TEST_CONFIG: StaticSchema = (
    18,
    n1,
    _s541,
    0,
    (_s542,),
    ((7, 0),),
)

TEST_BODY_STRUCTURE_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s543,
    {_s30: None, _s89: None},
    (_s544, _s546),
    ((3, {_s78: _s545}), (TEST_CONFIG, 0)),
)

TEST_NO_PAYLOAD_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s547,
    {_s30: None, _s89: None},
    (_s544,),
    ((3, {_s78: _s548}),),
)

TEST_PAYLOAD_BLOB_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s549,
    {_s30: None, _s89: None},
    (_s550, _s319),
    ((3, {_s78: _s551}), (1, 16)),
)

TEST_PAYLOAD_STRUCTURE_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s552,
    {_s30: None, _s89: None},
    (_s544, _s553),
    ((3, {_s78: _s545}), (PAYLOAD_CONFIG, 16)),
)

TIMESTAMP_FORMAT_HEADERS_IO: StaticSchema = (
    18,
    n1,
    _s554,
    {_s30: None, _s89: None},
    (_s257, _s259, _s260, _s261, _s262, _s263, _s264),
    (
        (4, {_s78: _s555, _s91: _s253}),
        (4, {_s78: _s556, _s91: _s255}),
        (4, {_s78: _s557, _s91: _s92}),
        (4, {_s78: _s558}),
        (lambda: schemas.EPOCH_SECONDS, {_s78: _s559}),
        (lambda: schemas.HTTP_DATE, {_s78: _s560}),
        (lambda: schemas.DATE_TIME, {_s78: _s561}),
    ),
)

UNION_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s562,
    {_s30: None, _s89: None},
    (_s563,),
    ((MY_UNION, 0),),
)

RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED1: StaticSchema = (
    18,
    n1,
    _s564,
    0,
    (_s218, _s235),
    ((3, 0), (lambda: RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED2, 0)),
)

RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED2: StaticSchema = (
    18,
    n1,
    _s565,
    0,
    (_s489, _s566),
    ((3, 0), (RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED1, 0)),
)
