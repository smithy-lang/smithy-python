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
_s68 = "smithy.api#default"
_s70 = "smithy.api#jsonName"
_s77 = "smithy.api#httpHeader"
_s79 = "TopLevel"
_s82 = "baz"
_s88 = "smithy.api#output"
_s90 = "smithy.api#timestampFormat"
_s91 = "date-time"
_s101 = "defaultString"
_s102 = "hi"
_s103 = "defaultBoolean"
_s104 = "defaultList"
_s105 = "defaultDocumentMap"
_s106 = "defaultDocumentString"
_s107 = "defaultDocumentBoolean"
_s108 = "defaultDocumentList"
_s109 = "defaultNullDocument"
_s110 = "defaultTimestamp"
_s111 = "defaultBlob"
_s112 = "YWJj"
_s113 = "defaultByte"
_s114 = "defaultShort"
_s115 = "defaultInteger"
_s116 = "defaultLong"
_s117 = "defaultFloat"
_s118 = "defaultDouble"
_s119 = "defaultMap"
_s120 = "defaultEnum"
_s121 = "defaultIntEnum"
_s122 = "emptyString"
_s123 = ""
_s124 = "falseBoolean"
_s125 = "emptyBlob"
_s126 = "zeroByte"
_s127 = "zeroShort"
_s128 = "zeroInteger"
_s129 = "zeroLong"
_s130 = "zeroFloat"
_s131 = "zeroDouble"
_s136 = "GreetingStruct"
_s153 = "stringValue"
_s177 = "smithy.api#streaming"
_s187 = "stream"
_s197 = "smithy.api#required"
_s199 = "initialResponseMember"
_s200 = "initial-response-member"
_s217 = "foo"
_s225 = "X-Foo"
_s226 = "blob"
_s228 = "smithy.api#mediaType"
_s229 = "text/plain"
_s234 = "nested"
_s252 = "epoch-seconds"
_s254 = "http-date"
_s256 = "memberEpochSeconds"
_s257 = "smithy.api#httpLabel"
_s258 = "memberHttpDate"
_s259 = "memberDateTime"
_s260 = "defaultFormat"
_s261 = "targetEpochSeconds"
_s262 = "targetHttpDate"
_s263 = "targetDateTime"
_s265 = "string"
_s270 = "timestamp"
_s318 = "data"
_s416 = "int"
_s431 = "MalformedTimestampPathEpochInput"
_s432 = "MalformedTimestampPathHttpDateInput"
_s433 = "MalformedTimestampQueryDefaultInput"
_s434 = "MalformedTimestampQueryEpochInput"
_s435 = "MalformedTimestampQueryHttpDateInput"
_s436 = "SimpleUnion"
_s437 = "MalformedUnionInput"
_s438 = "union"
_s439 = "MediaTypeHeaderInput"
_s440 = "json"
_s441 = "X-Json"
_s442 = "MediaTypeHeaderOutput"
n2 = "aws.protocoltests.restjson.nested"
_s443 = "salutation"
_s444 = "NestedUnion"
_s445 = "MyUnion"
_s446 = "booleanValue"
_s447 = "numberValue"
_s448 = "blobValue"
_s449 = "timestampValue"
_s450 = "enumValue"
_s451 = "listValue"
_s452 = "mapValue"
_s453 = "structureValue"
_s454 = "renamedStructureValue"
_s455 = "unionValue"
_s456 = "NoInputAndOutputOutput"
_s462 = "OmitsNullSerializesEmptyStringInput"
_s463 = "nullValue"
_s464 = "Null"
_s465 = "Empty"
_s466 = "OmitsSerializingEmptyListsInput"
_s467 = "OperationWithDefaultsInput"
_s468 = "defaults"
_s469 = "clientOptionalDefaults"
_s470 = "topLevelDefault"
_s471 = "otherTopLevelDefault"
_s472 = "OperationWithDefaultsOutput"
_s473 = "dialog"
_s474 = "dialogList"
_s475 = "dialogMap"
_s476 = "OperationWithNestedStructureInput"
_s477 = "topLevel"
_s478 = "OperationWithNestedStructureOutput"
_s479 = "OutputStreamOutput"
_s480 = "OutputStreamWithInitialResponseOutput"
_s481 = "PayloadConfig"
_s482 = "PlayerAction"
_s483 = "quit"
_s484 = "PostPlayerActionInput"
_s485 = "action"
_s486 = "PostPlayerActionOutput"
_s487 = "UnionWithJsonName"
_s488 = "bar"
_s489 = "_baz"
_s490 = "PostUnionWithJsonNameInput"
_s491 = "PostUnionWithJsonNameOutput"
_s492 = "PutWithContentEncodingInput"
_s493 = "encoding"
_s494 = "Content-Encoding"
_s495 = "QueryIdempotencyTokenAutoFillInput"
_s496 = "token"
_s497 = "smithy.api#idempotencyToken"
_s498 = "QueryParamsAsStringListMapInput"
_s499 = "qux"
_s500 = "corge"
_s501 = "QueryPrecedenceInput"
_s502 = "RecursiveShapesInputOutput"
_s503 = "ResponseCodeHttpFallbackInputOutput"
_s504 = "ResponseCodeRequiredOutput"
_s505 = "responseCode"
_s507 = "SimpleScalarPropertiesInputOutput"
_s508 = "trueBooleanValue"
_s509 = "falseBooleanValue"
_s510 = "byteValue"
_s511 = "shortValue"
_s512 = "integerValue"
_s513 = "longValue"
_s514 = "floatValue"
_s515 = "doubleValue"
_s516 = "DoubleDribble"
_s517 = "SparseBooleanMap"
_s518 = "SparseStringList"
_s519 = "SparseShortList"
_s520 = "SparseJsonListsInputOutput"
_s521 = "sparseStringList"
_s522 = "sparseShortList"
_s523 = "SparseStructMap"
_s524 = "SparseNumberMap"
_s525 = "SparseStringMap"
_s526 = "SparseSetMap"
_s527 = "SparseJsonMapsInputOutput"
_s528 = "sparseStructMap"
_s529 = "sparseNumberMap"
_s530 = "sparseBooleanMap"
_s531 = "sparseStringMap"
_s532 = "sparseSetMap"
_s533 = "StreamingBlob"
_s534 = "StreamingTextPlainBlob"
_s535 = "StreamingTraitsInputOutput"
_s536 = "smithy.api#httpPayload"
_s537 = "StreamingTraitsRequireLengthInput"
_s538 = "StreamingTraitsWithMediaTypeInputOutput"
_s539 = "StringPayloadInput"
_s540 = "TestConfig"
_s541 = "timeout"
_s542 = "TestBodyStructureInputOutput"
_s543 = "testId"
_s544 = "x-amz-test-id"
_s545 = "testConfig"
_s546 = "TestNoPayloadInputOutput"
_s547 = "X-Amz-Test-Id"
_s548 = "TestPayloadBlobInputOutput"
_s549 = "contentType"
_s550 = "Content-Type"
_s551 = "TestPayloadStructureInputOutput"
_s552 = "payloadConfig"
_s553 = "TimestampFormatHeadersIO"
_s554 = "X-memberEpochSeconds"
_s555 = "X-memberHttpDate"
_s556 = "X-memberDateTime"
_s557 = "X-defaultFormat"
_s558 = "X-targetEpochSeconds"
_s559 = "X-targetHttpDate"
_s560 = "X-targetDateTime"
_s561 = "UnionInputOutput"
_s562 = "contents"
_s563 = "RecursiveShapesInputOutputNested1"
_s564 = "RecursiveShapesInputOutputNested2"
_s565 = "recursiveMember"

MALFORMED_TIMESTAMP_PATH_EPOCH_INPUT: StaticSchema = (
    18,
    n1,
    _s431,
    {_s30: None},
    (_s270,),
    ((4, {_s90: _s252, _s257: None, _s197: None}),),
)

MALFORMED_TIMESTAMP_PATH_HTTP_DATE_INPUT: StaticSchema = (
    18,
    n1,
    _s432,
    {_s30: None},
    (_s270,),
    ((4, {_s90: _s254, _s257: None, _s197: None}),),
)

MALFORMED_TIMESTAMP_QUERY_DEFAULT_INPUT: StaticSchema = (
    18,
    n1,
    _s433,
    {_s30: None},
    (_s270,),
    ((4, {_s32: _s270, _s197: None}),),
)

MALFORMED_TIMESTAMP_QUERY_EPOCH_INPUT: StaticSchema = (
    18,
    n1,
    _s434,
    {_s30: None},
    (_s270,),
    ((4, {_s32: _s270, _s90: _s252, _s197: None}),),
)

MALFORMED_TIMESTAMP_QUERY_HTTP_DATE_INPUT: StaticSchema = (
    18,
    n1,
    _s435,
    {_s30: None},
    (_s270,),
    ((4, {_s32: _s270, _s90: _s254, _s197: None}),),
)

SIMPLE_UNION: StaticSchema = (
    19,
    n1,
    _s436,
    0,
    (
        _s416,
        _s265,
    ),
    (
        (7, 0),
        (3, 0),
    ),
)

MALFORMED_UNION_INPUT: StaticSchema = (
    18,
    n1,
    _s437,
    {_s30: None},
    (_s438,),
    ((SIMPLE_UNION, 0),),
)

MEDIA_TYPE_HEADER_INPUT: StaticSchema = (
    18,
    n1,
    _s439,
    {_s30: None},
    (_s440,),
    ((lambda: schemas.JSON_VALUE, {_s77: _s441}),),
)

MEDIA_TYPE_HEADER_OUTPUT: StaticSchema = (
    18,
    n1,
    _s442,
    {_s88: None},
    (_s440,),
    ((lambda: schemas.JSON_VALUE, {_s77: _s441}),),
)

RENAMED_GREETING: StaticSchema = (
    18,
    n2,
    _s136,
    0,
    (_s443,),
    ((3, 0),),
)

NESTED_UNION: StaticSchema = (
    19,
    n1,
    _s444,
    0,
    (_s153,),
    ((3, 0),),
)

MY_UNION: StaticSchema = (
    19,
    n1,
    _s445,
    0,
    (
        _s153,
        _s446,
        _s447,
        _s448,
        _s449,
        _s450,
        _s451,
        _s452,
        _s453,
        _s454,
        _s455,
    ),
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
    _s456,
    {_s88: None},
)

OMITS_NULL_SERIALIZES_EMPTY_STRING_INPUT: StaticSchema = (
    18,
    n1,
    _s462,
    {_s30: None},
    (
        _s463,
        _s122,
    ),
    (
        (3, {_s32: _s464}),
        (3, {_s32: _s465}),
    ),
)

OMITS_SERIALIZING_EMPTY_LISTS_INPUT: StaticSchema = (
    18,
    n1,
    _s466,
    {_s30: None},
    (
        _s34,
        _s42,
        _s50,
        _s53,
        _s56,
        _s59,
        _s62,
    ),
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
    _s467,
    {_s30: None},
    (
        _s468,
        _s469,
        _s470,
        _s471,
    ),
    (
        (lambda: schemas.DEFAULTS, 0),
        (lambda: schemas.CLIENT_OPTIONAL_DEFAULTS, 0),
        (3, {_s68: _s102}),
        (7, {_s68: 0}),
    ),
)

OPERATION_WITH_DEFAULTS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s472,
    {_s88: None},
    (
        _s101,
        _s103,
        _s104,
        _s105,
        _s106,
        _s107,
        _s108,
        _s109,
        _s110,
        _s111,
        _s113,
        _s114,
        _s115,
        _s116,
        _s117,
        _s118,
        _s119,
        _s120,
        _s121,
        _s122,
        _s124,
        _s125,
        _s126,
        _s127,
        _s128,
        _s129,
        _s130,
        _s131,
    ),
    (
        (3, {_s68: _s102}),
        (2, {_s68: True}),
        (lambda: schemas.TEST_STRING_LIST, {_s68: ()}),
        (lambda: schemas.DOCUMENT, {_s68: MappingProxyType[str, object]({})}),
        (lambda: schemas.DOCUMENT, {_s68: _s102}),
        (lambda: schemas.DOCUMENT, {_s68: True}),
        (lambda: schemas.DOCUMENT, {_s68: ()}),
        (lambda: schemas.DOCUMENT, {_s68: None}),
        (4, {_s68: 0}),
        (1, {_s68: _s112}),
        (5, {_s68: 1}),
        (6, {_s68: 1}),
        (7, {_s68: 10}),
        (8, {_s68: 100}),
        (9, {_s68: 1.0}),
        (10, {_s68: 1.0}),
        (lambda: schemas.TEST_STRING_MAP, {_s68: MappingProxyType[str, object]({})}),
        (lambda: schemas.TEST_ENUM, {_s68: _s9}),
        (lambda: schemas.TEST_INT_ENUM, {_s68: 1}),
        (3, {_s68: _s123}),
        (2, {_s68: False}),
        (1, {_s68: _s123}),
        (5, {_s68: 0}),
        (6, {_s68: 0}),
        (7, {_s68: 0}),
        (8, {_s68: 0}),
        (9, {_s68: 0.0}),
        (10, {_s68: 0.0}),
    ),
)

TOP_LEVEL: StaticSchema = (
    18,
    n1,
    _s79,
    0,
    (
        _s473,
        _s474,
        _s475,
    ),
    (
        (lambda: schemas.DIALOG, 1),
        (lambda: schemas.DIALOG_LIST, {_s68: ()}),
        (lambda: schemas.DIALOG_MAP, {_s68: MappingProxyType[str, object]({})}),
    ),
)

OPERATION_WITH_NESTED_STRUCTURE_INPUT: StaticSchema = (
    18,
    n1,
    _s476,
    {_s30: None},
    (_s477,),
    ((TOP_LEVEL, 1),),
)

OPERATION_WITH_NESTED_STRUCTURE_OUTPUT: StaticSchema = (
    18,
    n1,
    _s478,
    {_s88: None},
    (
        _s473,
        _s474,
        _s475,
    ),
    (
        (lambda: schemas.DIALOG, 1),
        (lambda: schemas.DIALOG_LIST, {_s68: ()}),
        (lambda: schemas.DIALOG_MAP, {_s68: MappingProxyType[str, object]({})}),
    ),
)

OUTPUT_STREAM_OUTPUT: StaticSchema = (
    18,
    n1,
    _s479,
    {_s88: None},
    (_s187,),
    ((lambda: schemas.EVENT_STREAM, 16),),
)

OUTPUT_STREAM_WITH_INITIAL_RESPONSE_OUTPUT: StaticSchema = (
    18,
    n1,
    _s480,
    {_s88: None},
    (
        _s199,
        _s187,
    ),
    (
        (3, {_s77: _s200, _s197: None}),
        (lambda: schemas.EVENT_STREAM, 16),
    ),
)

PAYLOAD_CONFIG: StaticSchema = (
    18,
    n1,
    _s481,
    0,
    (_s318,),
    ((7, 0),),
)

PLAYER_ACTION: StaticSchema = (
    19,
    n1,
    _s482,
    0,
    (_s483,),
    ((-1, 0),),
)

POST_PLAYER_ACTION_INPUT: StaticSchema = (
    18,
    n1,
    _s484,
    {_s30: None},
    (_s485,),
    ((PLAYER_ACTION, 0),),
)

POST_PLAYER_ACTION_OUTPUT: StaticSchema = (
    18,
    n1,
    _s486,
    {_s88: None},
    (_s485,),
    ((PLAYER_ACTION, 1),),
)

UNION_WITH_JSON_NAME: StaticSchema = (
    19,
    n1,
    _s487,
    0,
    (
        _s217,
        _s488,
        _s82,
    ),
    (
        (3, {_s70: _s9}),
        (3, 0),
        (3, {_s70: _s489}),
    ),
)

POST_UNION_WITH_JSON_NAME_INPUT: StaticSchema = (
    18,
    n1,
    _s490,
    {_s30: None},
    (_s28,),
    ((UNION_WITH_JSON_NAME, 0),),
)

POST_UNION_WITH_JSON_NAME_OUTPUT: StaticSchema = (
    18,
    n1,
    _s491,
    {_s88: None},
    (_s28,),
    ((UNION_WITH_JSON_NAME, 1),),
)

PUT_WITH_CONTENT_ENCODING_INPUT: StaticSchema = (
    18,
    n1,
    _s492,
    {_s30: None},
    (
        _s493,
        _s318,
    ),
    (
        (3, {_s77: _s494}),
        (3, 0),
    ),
)

QUERY_IDEMPOTENCY_TOKEN_AUTO_FILL_INPUT: StaticSchema = (
    18,
    n1,
    _s495,
    {_s30: None},
    (_s496,),
    ((3, {_s32: _s496, _s497: None}),),
)

QUERY_PARAMS_AS_STRING_LIST_MAP_INPUT: StaticSchema = (
    18,
    n1,
    _s498,
    {_s30: None},
    (
        _s499,
        _s217,
    ),
    (
        (3, {_s32: _s500}),
        (lambda: schemas.STRING_LIST_MAP, 1024),
    ),
)

QUERY_PRECEDENCE_INPUT: StaticSchema = (
    18,
    n1,
    _s501,
    {_s30: None},
    (
        _s217,
        _s82,
    ),
    (
        (3, {_s32: _s488}),
        (lambda: schemas.STRING_MAP, 1024),
    ),
)

RECURSIVE_SHAPES_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s502,
    {_s30: None, _s88: None},
    (_s234,),
    ((lambda: RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED1, 0),),
)

RESPONSE_CODE_HTTP_FALLBACK_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s503,
    {_s30: None, _s88: None},
)

RESPONSE_CODE_REQUIRED_OUTPUT: StaticSchema = (
    18,
    n1,
    _s504,
    {_s88: None},
    (_s505,),
    ((7, 129),),
)

SIMPLE_SCALAR_PROPERTIES_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s507,
    {_s30: None, _s88: None},
    (
        _s217,
        _s153,
        _s508,
        _s509,
        _s510,
        _s511,
        _s512,
        _s513,
        _s514,
        _s515,
    ),
    (
        (3, {_s77: _s225}),
        (3, 0),
        (2, 0),
        (2, 0),
        (5, 0),
        (6, 0),
        (7, 0),
        (8, 0),
        (9, 0),
        (10, {_s70: _s516}),
    ),
)

SPARSE_BOOLEAN_MAP: StaticSchema = (
    17,
    n1,
    _s517,
    64,
    (
        _s27,
        _s28,
    ),
    (
        (3, 0),
        (2, 0),
    ),
)

SPARSE_STRING_LIST: StaticSchema = (
    16,
    n0,
    _s518,
    64,
    (_s1,),
    ((3, 0),),
)

SPARSE_SHORT_LIST: StaticSchema = (
    16,
    n0,
    _s519,
    64,
    (_s1,),
    ((6, 0),),
)

SPARSE_JSON_LISTS_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s520,
    {_s30: None, _s88: None},
    (
        _s521,
        _s522,
    ),
    (
        (SPARSE_STRING_LIST, 0),
        (SPARSE_SHORT_LIST, 0),
    ),
)

SPARSE_STRUCT_MAP: StaticSchema = (
    17,
    n1,
    _s523,
    64,
    (
        _s27,
        _s28,
    ),
    (
        (3, 0),
        (lambda: schemas.GREETING_STRUCT, 0),
    ),
)

SPARSE_NUMBER_MAP: StaticSchema = (
    17,
    n1,
    _s524,
    64,
    (
        _s27,
        _s28,
    ),
    (
        (3, 0),
        (7, 0),
    ),
)

SPARSE_STRING_MAP: StaticSchema = (
    17,
    n0,
    _s525,
    64,
    (
        _s27,
        _s28,
    ),
    (
        (3, 0),
        (3, 0),
    ),
)

SPARSE_SET_MAP: StaticSchema = (
    17,
    n1,
    _s526,
    64,
    (
        _s27,
        _s28,
    ),
    (
        (3, 0),
        (lambda: schemas.STRING_SET, 0),
    ),
)

SPARSE_JSON_MAPS_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s527,
    {_s30: None, _s88: None},
    (
        _s528,
        _s529,
        _s530,
        _s531,
        _s532,
    ),
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
    _s533,
    {_s177: None},
)

STREAMING_TEXT_PLAIN_BLOB: StaticSchema = (
    1,
    n1,
    _s534,
    {_s228: _s229, _s177: None},
)

STREAMING_TRAITS_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s535,
    {_s30: None, _s88: None},
    (
        _s217,
        _s226,
    ),
    (
        (3, {_s77: _s225}),
        (STREAMING_BLOB, {_s68: _s123, _s536: None}),
    ),
)

STREAMING_TRAITS_REQUIRE_LENGTH_INPUT: StaticSchema = (
    18,
    n1,
    _s537,
    {_s30: None},
    (
        _s217,
        _s226,
    ),
    (
        (3, {_s77: _s225}),
        (lambda: schemas.FINITE_STREAMING_BLOB, {_s68: _s123, _s536: None}),
    ),
)

STREAMING_TRAITS_WITH_MEDIA_TYPE_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s538,
    {_s30: None, _s88: None},
    (
        _s217,
        _s226,
    ),
    (
        (3, {_s77: _s225}),
        (STREAMING_TEXT_PLAIN_BLOB, {_s68: _s123, _s536: None}),
    ),
)

STRING_PAYLOAD_INPUT: StaticSchema = (
    18,
    n1,
    _s539,
    {_s30: None, _s88: None},
    (_s65,),
    ((3, 16),),
)

TEST_CONFIG: StaticSchema = (
    18,
    n1,
    _s540,
    0,
    (_s541,),
    ((7, 0),),
)

TEST_BODY_STRUCTURE_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s542,
    {_s30: None, _s88: None},
    (
        _s543,
        _s545,
    ),
    (
        (3, {_s77: _s544}),
        (TEST_CONFIG, 0),
    ),
)

TEST_NO_PAYLOAD_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s546,
    {_s30: None, _s88: None},
    (_s543,),
    ((3, {_s77: _s547}),),
)

TEST_PAYLOAD_BLOB_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s548,
    {_s30: None, _s88: None},
    (
        _s549,
        _s318,
    ),
    (
        (3, {_s77: _s550}),
        (1, 16),
    ),
)

TEST_PAYLOAD_STRUCTURE_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s551,
    {_s30: None, _s88: None},
    (
        _s543,
        _s552,
    ),
    (
        (3, {_s77: _s544}),
        (PAYLOAD_CONFIG, 16),
    ),
)

TIMESTAMP_FORMAT_HEADERS_IO: StaticSchema = (
    18,
    n1,
    _s553,
    {_s30: None, _s88: None},
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
        (4, {_s77: _s554, _s90: _s252}),
        (4, {_s77: _s555, _s90: _s254}),
        (4, {_s77: _s556, _s90: _s91}),
        (4, {_s77: _s557}),
        (lambda: schemas.EPOCH_SECONDS, {_s77: _s558}),
        (lambda: schemas.HTTP_DATE, {_s77: _s559}),
        (lambda: schemas.DATE_TIME, {_s77: _s560}),
    ),
)

UNION_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s561,
    {_s30: None, _s88: None},
    (_s562,),
    ((MY_UNION, 0),),
)

RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED1: StaticSchema = (
    18,
    n1,
    _s563,
    0,
    (
        _s217,
        _s234,
    ),
    (
        (3, 0),
        (lambda: RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED2, 0),
    ),
)

RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED2: StaticSchema = (
    18,
    n1,
    _s564,
    0,
    (
        _s488,
        _s565,
    ),
    (
        (3, 0),
        (RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED1, 0),
    ),
)
