from types import MappingProxyType

from smithy_core._schema_compact import StaticOperationSchema, StaticSchema

from . import schemas

n0 = "aws.protocoltests.shared"
_s0 = "StringList"
_s1 = "member"
_s3 = "IntegerList"
_s5 = "DoubleList"
_s6 = "BooleanList"
_s7 = "TimestampList"
_s9 = "FOO"
_s10 = "smithy.api#enumValue"
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
_s68 = "smithy.api#default"
_s70 = "smithy.api#jsonName"
_s77 = "smithy.api#httpHeader"
_s79 = "TopLevel"
_s83 = "baz"
_s92 = "smithy.api#output"
_s100 = "Document"
_s106 = "defaultString"
_s107 = "hi"
_s108 = "defaultBoolean"
_s109 = "defaultList"
_s110 = "defaultDocumentMap"
_s111 = "defaultDocumentString"
_s112 = "defaultDocumentBoolean"
_s113 = "defaultDocumentList"
_s114 = "defaultNullDocument"
_s115 = "defaultTimestamp"
_s116 = "defaultBlob"
_s117 = "YWJj"
_s118 = "defaultByte"
_s119 = "defaultShort"
_s120 = "defaultInteger"
_s121 = "defaultLong"
_s122 = "defaultFloat"
_s123 = "defaultDouble"
_s124 = "defaultMap"
_s125 = "defaultEnum"
_s126 = "defaultIntEnum"
_s127 = "emptyString"
_s128 = ""
_s129 = "falseBoolean"
_s130 = "emptyBlob"
_s131 = "zeroByte"
_s132 = "zeroShort"
_s133 = "zeroInteger"
_s134 = "zeroLong"
_s135 = "zeroFloat"
_s136 = "zeroDouble"
_s148 = "greeting"
_s178 = "foo"
_s224 = "smithy.api#mediaType"
_s229 = "payload"
_s236 = "blob"
_s336 = "stringValue"
_s357 = "OmitsSerializingEmptyListsInput"
_s358 = "aws.protocoltests.restjson#OmitsSerializingEmptyListsInput"
_s359 = "OperationWithDefaultsInput"
_s360 = "aws.protocoltests.restjson#OperationWithDefaultsInput"
_s361 = "defaults"
_s362 = "clientOptionalDefaults"
_s363 = "topLevelDefault"
_s364 = "otherTopLevelDefault"
_s365 = "OperationWithDefaultsOutput"
_s366 = "aws.protocoltests.restjson#OperationWithDefaultsOutput"
_s367 = "dialog"
_s368 = "dialogList"
_s369 = "dialogMap"
_s370 = "OperationWithNestedStructureInput"
_s371 = "aws.protocoltests.restjson#OperationWithNestedStructureInput"
_s372 = "topLevel"
_s373 = "OperationWithNestedStructureOutput"
_s374 = "aws.protocoltests.restjson#OperationWithNestedStructureOutput"
_s375 = "PayloadConfig"
_s376 = "data"
_s377 = "PlayerAction"
_s378 = "quit"
_s379 = "PostPlayerActionInput"
_s380 = "aws.protocoltests.restjson#PostPlayerActionInput"
_s381 = "action"
_s382 = "PostPlayerActionOutput"
_s383 = "aws.protocoltests.restjson#PostPlayerActionOutput"
_s384 = "UnionWithJsonName"
_s385 = "bar"
_s386 = "_baz"
_s387 = "PostUnionWithJsonNameInput"
_s388 = "aws.protocoltests.restjson#PostUnionWithJsonNameInput"
_s389 = "PostUnionWithJsonNameOutput"
_s390 = "aws.protocoltests.restjson#PostUnionWithJsonNameOutput"
_s391 = "PutWithContentEncodingInput"
_s392 = "aws.protocoltests.restjson#PutWithContentEncodingInput"
_s393 = "encoding"
_s394 = "Content-Encoding"
_s395 = "QueryIdempotencyTokenAutoFillInput"
_s396 = "aws.protocoltests.restjson#QueryIdempotencyTokenAutoFillInput"
_s397 = "token"
_s398 = "smithy.api#idempotencyToken"
_s399 = "QueryMap"
_s400 = "QueryParamsAsStringListMapInput"
_s401 = "aws.protocoltests.restjson#QueryParamsAsStringListMapInput"
_s402 = "qux"
_s403 = "corge"
_s404 = "QueryPrecedenceInput"
_s405 = "aws.protocoltests.restjson#QueryPrecedenceInput"
_s406 = "ResponseCodeRequiredOutput"
_s407 = "aws.protocoltests.restjson#ResponseCodeRequiredOutput"
_s408 = "responseCode"
_s409 = "SparseBooleanMap"
_s410 = "SparseNumberMap"
_s411 = "SparseSetMap"
_s412 = "SparseStructMap"
_s413 = "StringEnum"
_s414 = "V"
_s415 = "enumvalue"
_s416 = "StructureListMember"
_s417 = "a"
_s418 = "b"
_s419 = "other"
_s420 = "StructureList"
_s421 = "TestConfig"
_s422 = "timeout"
_s423 = "UnionPayload"
_s424 = "FooEnumMap"
_s425 = "FooEnumSet"
_s426 = "IntegerEnumMap"
_s427 = "IntegerEnumSet"
_s428 = "NestedStringList"
_s429 = "SparseShortList"
_s430 = "SparseStringList"
_s431 = "SparseStringMap"
_s432 = "TextPlainBlob"
_s433 = "text/plain"
_s435 = "smithy.api#Unit"
_s439 = "DocumentTypeInput"
_s440 = "aws.protocoltests.restjson#DocumentTypeInputOutput"
_s441 = "documentValue"
_s442 = "DocumentTypeOutput"
_s443 = "DocumentTypeAsMapValueInput"
_s444 = "aws.protocoltests.restjson#DocumentTypeAsMapValueInputOutput"
_s445 = "docValuedMap"
_s446 = "DocumentTypeAsMapValueOutput"
_s447 = "DocumentTypeAsPayloadInput"
_s448 = "aws.protocoltests.restjson#DocumentTypeAsPayloadInputOutput"
_s449 = "DocumentTypeAsPayloadOutput"
_s450 = "EndpointOperationInput"
_s451 = "EndpointOperationOutput"
_s452 = "EndpointWithHostLabelOperationInput"
_s453 = "aws.protocoltests.restjson#HostLabelInput"
_s454 = "label"
_s455 = "EndpointWithHostLabelOperationOutput"
_s458 = "HostWithPathOperationInput"
_s459 = "HostWithPathOperationOutput"
_s460 = "HttpChecksumRequiredInput"
_s461 = "aws.protocoltests.restjson#HttpChecksumRequiredInputOutput"
_s462 = "HttpChecksumRequiredOutput"
_s463 = "HttpEnumPayloadInput"
_s464 = "aws.protocoltests.restjson#EnumPayloadInput"
_s465 = "HttpEnumPayloadOutput"
_s466 = "HttpPayloadTraitsInput"
_s467 = "aws.protocoltests.restjson#HttpPayloadTraitsInputOutput"
_s468 = "X-Foo"
_s469 = "HttpPayloadTraitsOutput"
_s470 = "HttpPayloadTraitsWithMediaTypeInput"
_s471 = "aws.protocoltests.restjson#HttpPayloadTraitsWithMediaTypeInputOutput"
_s472 = "HttpPayloadTraitsWithMediaTypeOutput"
_s473 = "HttpPayloadWithStructureInput"
_s474 = "aws.protocoltests.restjson#HttpPayloadWithStructureInputOutput"
_s475 = "nested"
_s476 = "HttpPayloadWithStructureOutput"
_s477 = "HttpPayloadWithUnionInput"
_s478 = "aws.protocoltests.restjson#HttpPayloadWithUnionInputOutput"
_s479 = "HttpPayloadWithUnionOutput"
_s480 = "HttpQueryParamsOnlyOperationInput"
_s481 = "aws.protocoltests.restjson#HttpQueryParamsOnlyInput"
_s482 = "queryMap"
_s483 = "HttpQueryParamsOnlyOperationOutput"
_s490 = "HttpStringPayloadInput"
_s491 = "aws.protocoltests.restjson#StringPayloadInput"
_s492 = "HttpStringPayloadOutput"
_s494 = "InputAndOutputWithHeadersInput"
_s495 = "aws.protocoltests.restjson#InputAndOutputWithHeadersIO"
_s496 = "headerString"
_s497 = "X-String"
_s498 = "headerByte"
_s499 = "X-Byte"
_s500 = "headerShort"
_s501 = "X-Short"
_s502 = "headerInteger"
_s503 = "X-Integer"
_s504 = "headerLong"
_s505 = "X-Long"
_s506 = "headerFloat"
_s507 = "X-Float"
_s508 = "headerDouble"
_s509 = "X-Double"
_s510 = "headerTrueBool"
_s511 = "X-Boolean1"
_s512 = "headerFalseBool"
_s513 = "X-Boolean2"
_s514 = "headerStringList"
_s515 = "X-StringList"
_s516 = "headerStringSet"
_s517 = "X-StringSet"
_s518 = "headerIntegerList"
_s519 = "X-IntegerList"
_s520 = "headerBooleanList"
_s521 = "X-BooleanList"
_s522 = "headerTimestampList"
_s523 = "X-TimestampList"
_s524 = "headerEnum"
_s525 = "X-Enum"
_s526 = "headerEnumList"
_s527 = "X-EnumList"
_s528 = "headerIntegerEnum"
_s529 = "X-IntegerEnum"
_s530 = "headerIntegerEnumList"
_s531 = "X-IntegerEnumList"
_s532 = "InputAndOutputWithHeadersOutput"
_s639 = "OmitsSerializingEmptyListsOutput"
_s640 = "PutWithContentEncodingOutput"
_s641 = "QueryIdempotencyTokenAutoFillOutput"
_s642 = "QueryParamsAsStringListMapOutput"
_s643 = "QueryPrecedenceOutput"
_s650 = "ResponseCodeRequiredInput"
_s714 = "smithy.api#http"
_s719 = "DocumentType"
_s720 = "DocumentTypeAsMapValue"
_s721 = "DocumentTypeAsPayload"
_s723 = "EndpointOperation"
_s724 = "smithy.api#endpoint"
_s725 = "EndpointWithHostLabelOperation"
_s728 = "HostWithPathOperation"
_s729 = "HttpChecksumRequired"
_s730 = "smithy.api#httpChecksumRequired"
_s732 = "HttpEnumPayload"
_s733 = "HttpPayloadTraits"
_s734 = "HttpPayloadTraitsWithMediaType"
_s735 = "HttpPayloadWithStructure"
_s736 = "HttpPayloadWithUnion"
_s739 = "HttpQueryParamsOnlyOperation"
_s746 = "HttpStringPayload"
_s748 = "InputAndOutputWithHeaders"
_s795 = "OmitsSerializingEmptyLists"
_s796 = "OperationWithDefaults"
_s797 = "OperationWithNestedStructure"
_s798 = "PostPlayerAction"
_s799 = "PostUnionWithJsonName"
_s800 = "PutWithContentEncoding"
_s801 = "smithy.api#requestCompression"
_s802 = "QueryIdempotencyTokenAutoFill"
_s803 = "QueryParamsAsStringListMap"
_s804 = "QueryPrecedence"
_s807 = "ResponseCodeRequired"

DOCUMENT: StaticSchema = (
    13,
    n1,
    _s100,
    0,
)

OMITS_SERIALIZING_EMPTY_LISTS_INPUT: StaticSchema = (
    18,
    n1,
    _s357,
    {_s30: _s358, _s32: None},
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
    _s639,
    {_s30: _s435, _s92: None},
)

OMITS_SERIALIZING_EMPTY_LISTS: StaticOperationSchema = (
    23,
    n1,
    _s795,
    {_s714: MappingProxyType({"uri": "/OmitsSerializingEmptyLists", "method": "POST"})},
    OMITS_SERIALIZING_EMPTY_LISTS_INPUT,
    OMITS_SERIALIZING_EMPTY_LISTS_OUTPUT,
    (),
)

OPERATION_WITH_DEFAULTS_INPUT: StaticSchema = (
    18,
    n1,
    _s359,
    {_s30: _s360, _s32: None},
    (_s361, _s362, _s363, _s364),
    (
        (lambda: schemas.DEFAULTS, 0),
        (lambda: schemas.CLIENT_OPTIONAL_DEFAULTS, 0),
        (3, {_s68: _s107}),
        (7, {_s68: 0}),
    ),
)

OPERATION_WITH_DEFAULTS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s365,
    {_s30: _s366, _s92: None},
    (
        _s106,
        _s108,
        _s109,
        _s110,
        _s111,
        _s112,
        _s113,
        _s114,
        _s115,
        _s116,
        _s118,
        _s119,
        _s120,
        _s121,
        _s122,
        _s123,
        _s124,
        _s125,
        _s126,
        _s127,
        _s129,
        _s130,
        _s131,
        _s132,
        _s133,
        _s134,
        _s135,
        _s136,
    ),
    (
        (3, {_s68: _s107}),
        (2, {_s68: True}),
        (lambda: schemas.TEST_STRING_LIST, {_s68: ()}),
        (DOCUMENT, {_s68: MappingProxyType[str, object]({})}),
        (DOCUMENT, {_s68: _s107}),
        (DOCUMENT, {_s68: True}),
        (DOCUMENT, {_s68: ()}),
        (DOCUMENT, {_s68: None}),
        (4, {_s68: 0}),
        (1, {_s68: _s117}),
        (5, {_s68: 1}),
        (6, {_s68: 1}),
        (7, {_s68: 10}),
        (8, {_s68: 100}),
        (9, {_s68: 1.0}),
        (10, {_s68: 1.0}),
        (lambda: schemas.TEST_STRING_MAP, {_s68: MappingProxyType[str, object]({})}),
        (lambda: schemas.TEST_ENUM, {_s68: _s9}),
        (lambda: schemas.TEST_INT_ENUM, {_s68: 1}),
        (3, {_s68: _s128}),
        (2, {_s68: False}),
        (1, {_s68: _s128}),
        (5, {_s68: 0}),
        (6, {_s68: 0}),
        (7, {_s68: 0}),
        (8, {_s68: 0}),
        (9, {_s68: 0.0}),
        (10, {_s68: 0.0}),
    ),
)

OPERATION_WITH_DEFAULTS: StaticOperationSchema = (
    23,
    n1,
    _s796,
    {_s714: MappingProxyType({"uri": "/OperationWithDefaults", "method": "POST"})},
    OPERATION_WITH_DEFAULTS_INPUT,
    OPERATION_WITH_DEFAULTS_OUTPUT,
    (),
)

TOP_LEVEL: StaticSchema = (
    18,
    n1,
    _s79,
    0,
    (_s367, _s368, _s369),
    (
        (lambda: schemas.DIALOG, 1),
        (lambda: schemas.DIALOG_LIST, {_s68: ()}),
        (lambda: schemas.DIALOG_MAP, {_s68: MappingProxyType[str, object]({})}),
    ),
)

OPERATION_WITH_NESTED_STRUCTURE_INPUT: StaticSchema = (
    18,
    n1,
    _s370,
    {_s30: _s371, _s32: None},
    (_s372,),
    ((TOP_LEVEL, 1),),
)

OPERATION_WITH_NESTED_STRUCTURE_OUTPUT: StaticSchema = (
    18,
    n1,
    _s373,
    {_s30: _s374, _s92: None},
    (_s367, _s368, _s369),
    (
        (lambda: schemas.DIALOG, 1),
        (lambda: schemas.DIALOG_LIST, {_s68: ()}),
        (lambda: schemas.DIALOG_MAP, {_s68: MappingProxyType[str, object]({})}),
    ),
)

OPERATION_WITH_NESTED_STRUCTURE: StaticOperationSchema = (
    23,
    n1,
    _s797,
    {
        _s714: MappingProxyType(
            {"uri": "/OperationWithNestedStructure", "method": "POST"}
        )
    },
    OPERATION_WITH_NESTED_STRUCTURE_INPUT,
    OPERATION_WITH_NESTED_STRUCTURE_OUTPUT,
    (),
)

PAYLOAD_CONFIG: StaticSchema = (
    18,
    n1,
    _s375,
    0,
    (_s376,),
    ((7, 0),),
)

PLAYER_ACTION: StaticSchema = (
    19,
    n1,
    _s377,
    0,
    (_s378,),
    ((-1, 0),),
)

POST_PLAYER_ACTION_INPUT: StaticSchema = (
    18,
    n1,
    _s379,
    {_s30: _s380, _s32: None},
    (_s381,),
    ((PLAYER_ACTION, 0),),
)

POST_PLAYER_ACTION_OUTPUT: StaticSchema = (
    18,
    n1,
    _s382,
    {_s30: _s383, _s92: None},
    (_s381,),
    ((PLAYER_ACTION, 1),),
)

POST_PLAYER_ACTION: StaticOperationSchema = (
    23,
    n1,
    _s798,
    {_s714: MappingProxyType({"uri": "/PostPlayerAction", "method": "POST"})},
    POST_PLAYER_ACTION_INPUT,
    POST_PLAYER_ACTION_OUTPUT,
    (),
)

UNION_WITH_JSON_NAME: StaticSchema = (
    19,
    n1,
    _s384,
    0,
    (_s178, _s385, _s83),
    ((3, {_s70: _s9}), (3, 0), (3, {_s70: _s386})),
)

POST_UNION_WITH_JSON_NAME_INPUT: StaticSchema = (
    18,
    n1,
    _s387,
    {_s30: _s388, _s32: None},
    (_s28,),
    ((UNION_WITH_JSON_NAME, 0),),
)

POST_UNION_WITH_JSON_NAME_OUTPUT: StaticSchema = (
    18,
    n1,
    _s389,
    {_s30: _s390, _s92: None},
    (_s28,),
    ((UNION_WITH_JSON_NAME, 1),),
)

POST_UNION_WITH_JSON_NAME: StaticOperationSchema = (
    23,
    n1,
    _s799,
    {_s714: MappingProxyType({"uri": "/PostUnionWithJsonName", "method": "POST"})},
    POST_UNION_WITH_JSON_NAME_INPUT,
    POST_UNION_WITH_JSON_NAME_OUTPUT,
    (),
)

PUT_WITH_CONTENT_ENCODING_INPUT: StaticSchema = (
    18,
    n1,
    _s391,
    {_s30: _s392, _s32: None},
    (_s393, _s376),
    ((3, {_s77: _s394}), (3, 0)),
)

PUT_WITH_CONTENT_ENCODING_OUTPUT: StaticSchema = (
    18,
    n1,
    _s640,
    {_s30: _s435, _s92: None},
)

PUT_WITH_CONTENT_ENCODING: StaticOperationSchema = (
    23,
    n1,
    _s800,
    {
        _s714: MappingProxyType(
            {"method": "POST", "uri": "/requestcompression/putcontentwithencoding"}
        ),
        _s801: MappingProxyType({"encodings": ("gzip",)}),
    },
    PUT_WITH_CONTENT_ENCODING_INPUT,
    PUT_WITH_CONTENT_ENCODING_OUTPUT,
    (),
)

QUERY_IDEMPOTENCY_TOKEN_AUTO_FILL_INPUT: StaticSchema = (
    18,
    n1,
    _s395,
    {_s30: _s396, _s32: None},
    (_s397,),
    ((3, {_s34: _s397, _s398: None}),),
)

QUERY_IDEMPOTENCY_TOKEN_AUTO_FILL_OUTPUT: StaticSchema = (
    18,
    n1,
    _s641,
    {_s30: _s435, _s92: None},
)

QUERY_IDEMPOTENCY_TOKEN_AUTO_FILL: StaticOperationSchema = (
    23,
    n1,
    _s802,
    {
        _s714: MappingProxyType(
            {"uri": "/QueryIdempotencyTokenAutoFill", "method": "POST"}
        )
    },
    QUERY_IDEMPOTENCY_TOKEN_AUTO_FILL_INPUT,
    QUERY_IDEMPOTENCY_TOKEN_AUTO_FILL_OUTPUT,
    (),
)

QUERY_MAP: StaticSchema = (
    17,
    n1,
    _s399,
    0,
    (_s27, _s28),
    ((3, 0), (3, 0)),
)

QUERY_PARAMS_AS_STRING_LIST_MAP_INPUT: StaticSchema = (
    18,
    n1,
    _s400,
    {_s30: _s401, _s32: None},
    (_s402, _s178),
    ((3, {_s34: _s403}), (lambda: schemas.STRING_LIST_MAP, 1024)),
)

QUERY_PARAMS_AS_STRING_LIST_MAP_OUTPUT: StaticSchema = (
    18,
    n1,
    _s642,
    {_s30: _s435, _s92: None},
)

QUERY_PARAMS_AS_STRING_LIST_MAP: StaticOperationSchema = (
    23,
    n1,
    _s803,
    {_s714: MappingProxyType({"uri": "/StringListMap", "method": "POST"})},
    QUERY_PARAMS_AS_STRING_LIST_MAP_INPUT,
    QUERY_PARAMS_AS_STRING_LIST_MAP_OUTPUT,
    (),
)

QUERY_PRECEDENCE_INPUT: StaticSchema = (
    18,
    n1,
    _s404,
    {_s30: _s405, _s32: None},
    (_s178, _s83),
    ((3, {_s34: _s385}), (lambda: schemas.STRING_MAP, 1024)),
)

QUERY_PRECEDENCE_OUTPUT: StaticSchema = (
    18,
    n1,
    _s643,
    {_s30: _s435, _s92: None},
)

QUERY_PRECEDENCE: StaticOperationSchema = (
    23,
    n1,
    _s804,
    {_s714: MappingProxyType({"uri": "/Precedence", "method": "POST"})},
    QUERY_PRECEDENCE_INPUT,
    QUERY_PRECEDENCE_OUTPUT,
    (),
)

RESPONSE_CODE_REQUIRED_OUTPUT: StaticSchema = (
    18,
    n1,
    _s406,
    {_s30: _s407, _s92: None},
    (_s408,),
    ((7, 129),),
)

RESPONSE_CODE_REQUIRED_INPUT: StaticSchema = (
    18,
    n1,
    _s650,
    {_s30: _s435, _s32: None},
)

RESPONSE_CODE_REQUIRED: StaticOperationSchema = (
    23,
    n1,
    _s807,
    {
        _s714: MappingProxyType(
            {"method": "GET", "uri": "/responseCodeRequired", "code": 200}
        )
    },
    RESPONSE_CODE_REQUIRED_INPUT,
    RESPONSE_CODE_REQUIRED_OUTPUT,
    (),
)

SPARSE_BOOLEAN_MAP: StaticSchema = (
    17,
    n1,
    _s409,
    64,
    (_s27, _s28),
    ((3, 0), (2, 0)),
)

SPARSE_NUMBER_MAP: StaticSchema = (
    17,
    n1,
    _s410,
    64,
    (_s27, _s28),
    ((3, 0), (7, 0)),
)

SPARSE_SET_MAP: StaticSchema = (
    17,
    n1,
    _s411,
    64,
    (_s27, _s28),
    ((3, 0), (lambda: schemas.STRING_SET, 0)),
)

SPARSE_STRUCT_MAP: StaticSchema = (
    17,
    n1,
    _s412,
    64,
    (_s27, _s28),
    ((3, 0), (lambda: schemas.GREETING_STRUCT, 0)),
)

STRING_ENUM: StaticSchema = (
    14,
    n1,
    _s413,
    0,
    (_s414,),
    ((-1, {_s10: _s415}),),
)

STRUCTURE_LIST_MEMBER: StaticSchema = (
    18,
    n1,
    _s416,
    0,
    (_s417, _s418),
    ((3, {_s70: _s28}), (3, {_s70: _s419})),
)

STRUCTURE_LIST: StaticSchema = (
    16,
    n1,
    _s420,
    0,
    (_s1,),
    ((STRUCTURE_LIST_MEMBER, 0),),
)

TEST_CONFIG: StaticSchema = (
    18,
    n1,
    _s421,
    0,
    (_s422,),
    ((7, 0),),
)

UNION_PAYLOAD: StaticSchema = (
    19,
    n1,
    _s423,
    0,
    (_s148,),
    ((3, 0),),
)

FOO_ENUM_MAP: StaticSchema = (
    17,
    n0,
    _s424,
    0,
    (_s27, _s28),
    ((3, 0), (lambda: schemas.FOO_ENUM, 0)),
)

FOO_ENUM_SET: StaticSchema = (
    16,
    n0,
    _s425,
    0,
    (_s1,),
    ((lambda: schemas.FOO_ENUM, 0),),
)

INTEGER_ENUM_MAP: StaticSchema = (
    17,
    n0,
    _s426,
    0,
    (_s27, _s28),
    ((3, 0), (lambda: schemas.INTEGER_ENUM, 0)),
)

INTEGER_ENUM_SET: StaticSchema = (
    16,
    n0,
    _s427,
    0,
    (_s1,),
    ((lambda: schemas.INTEGER_ENUM, 0),),
)

NESTED_STRING_LIST: StaticSchema = (
    16,
    n0,
    _s428,
    0,
    (_s1,),
    ((lambda: schemas.STRING_LIST, 0),),
)

SPARSE_SHORT_LIST: StaticSchema = (
    16,
    n0,
    _s429,
    64,
    (_s1,),
    ((6, 0),),
)

SPARSE_STRING_LIST: StaticSchema = (
    16,
    n0,
    _s430,
    64,
    (_s1,),
    ((3, 0),),
)

SPARSE_STRING_MAP: StaticSchema = (
    17,
    n0,
    _s431,
    64,
    (_s27, _s28),
    ((3, 0), (3, 0)),
)

TEXT_PLAIN_BLOB: StaticSchema = (
    1,
    n0,
    _s432,
    {_s224: _s433},
)

DOCUMENT_TYPE_INPUT: StaticSchema = (
    18,
    n1,
    _s439,
    {_s30: _s440, _s32: None},
    (_s336, _s441),
    ((3, 0), (DOCUMENT, 0)),
)

DOCUMENT_TYPE_OUTPUT: StaticSchema = (
    18,
    n1,
    _s442,
    {_s30: _s440, _s92: None},
    (_s336, _s441),
    ((3, 0), (DOCUMENT, 0)),
)

DOCUMENT_TYPE: StaticOperationSchema = (
    23,
    n1,
    _s719,
    {_s714: MappingProxyType({"uri": "/DocumentType", "method": "PUT"})},
    DOCUMENT_TYPE_INPUT,
    DOCUMENT_TYPE_OUTPUT,
    (),
)

DOCUMENT_TYPE_AS_MAP_VALUE_INPUT: StaticSchema = (
    18,
    n1,
    _s443,
    {_s30: _s444, _s32: None},
    (_s445,),
    ((lambda: schemas.DOCUMENT_VALUED_MAP, 0),),
)

DOCUMENT_TYPE_AS_MAP_VALUE_OUTPUT: StaticSchema = (
    18,
    n1,
    _s446,
    {_s30: _s444, _s92: None},
    (_s445,),
    ((lambda: schemas.DOCUMENT_VALUED_MAP, 0),),
)

DOCUMENT_TYPE_AS_MAP_VALUE: StaticOperationSchema = (
    23,
    n1,
    _s720,
    {_s714: MappingProxyType({"uri": "/DocumentTypeAsMapValue", "method": "PUT"})},
    DOCUMENT_TYPE_AS_MAP_VALUE_INPUT,
    DOCUMENT_TYPE_AS_MAP_VALUE_OUTPUT,
    (),
)

DOCUMENT_TYPE_AS_PAYLOAD_INPUT: StaticSchema = (
    18,
    n1,
    _s447,
    {_s30: _s448, _s32: None},
    (_s441,),
    ((DOCUMENT, 16),),
)

DOCUMENT_TYPE_AS_PAYLOAD_OUTPUT: StaticSchema = (
    18,
    n1,
    _s449,
    {_s30: _s448, _s92: None},
    (_s441,),
    ((DOCUMENT, 16),),
)

DOCUMENT_TYPE_AS_PAYLOAD: StaticOperationSchema = (
    23,
    n1,
    _s721,
    {_s714: MappingProxyType({"uri": "/DocumentTypeAsPayload", "method": "PUT"})},
    DOCUMENT_TYPE_AS_PAYLOAD_INPUT,
    DOCUMENT_TYPE_AS_PAYLOAD_OUTPUT,
    (),
)

ENDPOINT_OPERATION_INPUT: StaticSchema = (
    18,
    n1,
    _s450,
    {_s30: _s435, _s32: None},
)

ENDPOINT_OPERATION_OUTPUT: StaticSchema = (
    18,
    n1,
    _s451,
    {_s30: _s435, _s92: None},
)

ENDPOINT_OPERATION: StaticOperationSchema = (
    23,
    n1,
    _s723,
    {
        _s724: MappingProxyType({"hostPrefix": "foo."}),
        _s714: MappingProxyType({"uri": "/EndpointOperation", "method": "POST"}),
    },
    ENDPOINT_OPERATION_INPUT,
    ENDPOINT_OPERATION_OUTPUT,
    (),
)

ENDPOINT_WITH_HOST_LABEL_OPERATION_INPUT: StaticSchema = (
    18,
    n1,
    _s452,
    {_s30: _s453, _s32: None},
    (_s454,),
    ((3, 257),),
)

ENDPOINT_WITH_HOST_LABEL_OPERATION_OUTPUT: StaticSchema = (
    18,
    n1,
    _s455,
    {_s30: _s435, _s92: None},
)

ENDPOINT_WITH_HOST_LABEL_OPERATION: StaticOperationSchema = (
    23,
    n1,
    _s725,
    {
        _s724: MappingProxyType({"hostPrefix": "foo.{label}."}),
        _s714: MappingProxyType(
            {"uri": "/EndpointWithHostLabelOperation", "method": "POST"}
        ),
    },
    ENDPOINT_WITH_HOST_LABEL_OPERATION_INPUT,
    ENDPOINT_WITH_HOST_LABEL_OPERATION_OUTPUT,
    (),
)

HOST_WITH_PATH_OPERATION_INPUT: StaticSchema = (
    18,
    n1,
    _s458,
    {_s30: _s435, _s32: None},
)

HOST_WITH_PATH_OPERATION_OUTPUT: StaticSchema = (
    18,
    n1,
    _s459,
    {_s30: _s435, _s92: None},
)

HOST_WITH_PATH_OPERATION: StaticOperationSchema = (
    23,
    n1,
    _s728,
    {_s714: MappingProxyType({"uri": "/HostWithPathOperation", "method": "GET"})},
    HOST_WITH_PATH_OPERATION_INPUT,
    HOST_WITH_PATH_OPERATION_OUTPUT,
    (),
)

HTTP_CHECKSUM_REQUIRED_INPUT: StaticSchema = (
    18,
    n1,
    _s460,
    {_s30: _s461, _s32: None},
    (_s178,),
    ((3, 0),),
)

HTTP_CHECKSUM_REQUIRED_OUTPUT: StaticSchema = (
    18,
    n1,
    _s462,
    {_s30: _s461, _s92: None},
    (_s178,),
    ((3, 0),),
)

HTTP_CHECKSUM_REQUIRED: StaticOperationSchema = (
    23,
    n1,
    _s729,
    {
        _s714: MappingProxyType({"uri": "/HttpChecksumRequired", "method": "POST"}),
        _s730: None,
    },
    HTTP_CHECKSUM_REQUIRED_INPUT,
    HTTP_CHECKSUM_REQUIRED_OUTPUT,
    (),
)

HTTP_ENUM_PAYLOAD_INPUT: StaticSchema = (
    18,
    n1,
    _s463,
    {_s30: _s464, _s32: None},
    (_s229,),
    ((STRING_ENUM, 16),),
)

HTTP_ENUM_PAYLOAD_OUTPUT: StaticSchema = (
    18,
    n1,
    _s465,
    {_s30: _s464, _s92: None},
    (_s229,),
    ((STRING_ENUM, 16),),
)

HTTP_ENUM_PAYLOAD: StaticOperationSchema = (
    23,
    n1,
    _s732,
    {_s714: MappingProxyType({"uri": "/EnumPayload", "method": "POST"})},
    HTTP_ENUM_PAYLOAD_INPUT,
    HTTP_ENUM_PAYLOAD_OUTPUT,
    (),
)

HTTP_PAYLOAD_TRAITS_INPUT: StaticSchema = (
    18,
    n1,
    _s466,
    {_s30: _s467, _s32: None},
    (_s178, _s236),
    ((3, {_s77: _s468}), (1, 16)),
)

HTTP_PAYLOAD_TRAITS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s469,
    {_s30: _s467, _s92: None},
    (_s178, _s236),
    ((3, {_s77: _s468}), (1, 16)),
)

HTTP_PAYLOAD_TRAITS: StaticOperationSchema = (
    23,
    n1,
    _s733,
    {_s714: MappingProxyType({"uri": "/HttpPayloadTraits", "method": "POST"})},
    HTTP_PAYLOAD_TRAITS_INPUT,
    HTTP_PAYLOAD_TRAITS_OUTPUT,
    (),
)

HTTP_PAYLOAD_TRAITS_WITH_MEDIA_TYPE_INPUT: StaticSchema = (
    18,
    n1,
    _s470,
    {_s30: _s471, _s32: None},
    (_s178, _s236),
    ((3, {_s77: _s468}), (TEXT_PLAIN_BLOB, 16)),
)

HTTP_PAYLOAD_TRAITS_WITH_MEDIA_TYPE_OUTPUT: StaticSchema = (
    18,
    n1,
    _s472,
    {_s30: _s471, _s92: None},
    (_s178, _s236),
    ((3, {_s77: _s468}), (TEXT_PLAIN_BLOB, 16)),
)

HTTP_PAYLOAD_TRAITS_WITH_MEDIA_TYPE: StaticOperationSchema = (
    23,
    n1,
    _s734,
    {
        _s714: MappingProxyType(
            {"uri": "/HttpPayloadTraitsWithMediaType", "method": "POST"}
        )
    },
    HTTP_PAYLOAD_TRAITS_WITH_MEDIA_TYPE_INPUT,
    HTTP_PAYLOAD_TRAITS_WITH_MEDIA_TYPE_OUTPUT,
    (),
)

HTTP_PAYLOAD_WITH_STRUCTURE_INPUT: StaticSchema = (
    18,
    n1,
    _s473,
    {_s30: _s474, _s32: None},
    (_s475,),
    ((lambda: schemas.NESTED_PAYLOAD, 16),),
)

HTTP_PAYLOAD_WITH_STRUCTURE_OUTPUT: StaticSchema = (
    18,
    n1,
    _s476,
    {_s30: _s474, _s92: None},
    (_s475,),
    ((lambda: schemas.NESTED_PAYLOAD, 16),),
)

HTTP_PAYLOAD_WITH_STRUCTURE: StaticOperationSchema = (
    23,
    n1,
    _s735,
    {_s714: MappingProxyType({"uri": "/HttpPayloadWithStructure", "method": "PUT"})},
    HTTP_PAYLOAD_WITH_STRUCTURE_INPUT,
    HTTP_PAYLOAD_WITH_STRUCTURE_OUTPUT,
    (),
)

HTTP_PAYLOAD_WITH_UNION_INPUT: StaticSchema = (
    18,
    n1,
    _s477,
    {_s30: _s478, _s32: None},
    (_s475,),
    ((UNION_PAYLOAD, 16),),
)

HTTP_PAYLOAD_WITH_UNION_OUTPUT: StaticSchema = (
    18,
    n1,
    _s479,
    {_s30: _s478, _s92: None},
    (_s475,),
    ((UNION_PAYLOAD, 16),),
)

HTTP_PAYLOAD_WITH_UNION: StaticOperationSchema = (
    23,
    n1,
    _s736,
    {_s714: MappingProxyType({"uri": "/HttpPayloadWithUnion", "method": "PUT"})},
    HTTP_PAYLOAD_WITH_UNION_INPUT,
    HTTP_PAYLOAD_WITH_UNION_OUTPUT,
    (),
)

HTTP_QUERY_PARAMS_ONLY_OPERATION_INPUT: StaticSchema = (
    18,
    n1,
    _s480,
    {_s30: _s481, _s32: None},
    (_s482,),
    ((QUERY_MAP, 1024),),
)

HTTP_QUERY_PARAMS_ONLY_OPERATION_OUTPUT: StaticSchema = (
    18,
    n1,
    _s483,
    {_s30: _s435, _s92: None},
)

HTTP_QUERY_PARAMS_ONLY_OPERATION: StaticOperationSchema = (
    23,
    n1,
    _s739,
    {_s714: MappingProxyType({"uri": "/http-query-params-only", "method": "GET"})},
    HTTP_QUERY_PARAMS_ONLY_OPERATION_INPUT,
    HTTP_QUERY_PARAMS_ONLY_OPERATION_OUTPUT,
    (),
)

HTTP_STRING_PAYLOAD_INPUT: StaticSchema = (
    18,
    n1,
    _s490,
    {_s30: _s491, _s32: None},
    (_s229,),
    ((3, 16),),
)

HTTP_STRING_PAYLOAD_OUTPUT: StaticSchema = (
    18,
    n1,
    _s492,
    {_s30: _s491, _s92: None},
    (_s229,),
    ((3, 16),),
)

HTTP_STRING_PAYLOAD: StaticOperationSchema = (
    23,
    n1,
    _s746,
    {_s714: MappingProxyType({"uri": "/StringPayload", "method": "POST"})},
    HTTP_STRING_PAYLOAD_INPUT,
    HTTP_STRING_PAYLOAD_OUTPUT,
    (),
)

INPUT_AND_OUTPUT_WITH_HEADERS_INPUT: StaticSchema = (
    18,
    n1,
    _s494,
    {_s30: _s495, _s32: None},
    (
        _s496,
        _s498,
        _s500,
        _s502,
        _s504,
        _s506,
        _s508,
        _s510,
        _s512,
        _s514,
        _s516,
        _s518,
        _s520,
        _s522,
        _s524,
        _s526,
        _s528,
        _s530,
    ),
    (
        (3, {_s77: _s497}),
        (5, {_s77: _s499}),
        (6, {_s77: _s501}),
        (7, {_s77: _s503}),
        (8, {_s77: _s505}),
        (9, {_s77: _s507}),
        (10, {_s77: _s509}),
        (2, {_s77: _s511}),
        (2, {_s77: _s513}),
        (lambda: schemas.STRING_LIST, {_s77: _s515}),
        (lambda: schemas.STRING_SET, {_s77: _s517}),
        (lambda: schemas.INTEGER_LIST, {_s77: _s519}),
        (lambda: schemas.BOOLEAN_LIST, {_s77: _s521}),
        (lambda: schemas.TIMESTAMP_LIST, {_s77: _s523}),
        (lambda: schemas.FOO_ENUM, {_s77: _s525}),
        (lambda: schemas.FOO_ENUM_LIST, {_s77: _s527}),
        (lambda: schemas.INTEGER_ENUM, {_s77: _s529}),
        (lambda: schemas.INTEGER_ENUM_LIST, {_s77: _s531}),
    ),
)

INPUT_AND_OUTPUT_WITH_HEADERS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s532,
    {_s30: _s495, _s92: None},
    (
        _s496,
        _s498,
        _s500,
        _s502,
        _s504,
        _s506,
        _s508,
        _s510,
        _s512,
        _s514,
        _s516,
        _s518,
        _s520,
        _s522,
        _s524,
        _s526,
        _s528,
        _s530,
    ),
    (
        (3, {_s77: _s497}),
        (5, {_s77: _s499}),
        (6, {_s77: _s501}),
        (7, {_s77: _s503}),
        (8, {_s77: _s505}),
        (9, {_s77: _s507}),
        (10, {_s77: _s509}),
        (2, {_s77: _s511}),
        (2, {_s77: _s513}),
        (lambda: schemas.STRING_LIST, {_s77: _s515}),
        (lambda: schemas.STRING_SET, {_s77: _s517}),
        (lambda: schemas.INTEGER_LIST, {_s77: _s519}),
        (lambda: schemas.BOOLEAN_LIST, {_s77: _s521}),
        (lambda: schemas.TIMESTAMP_LIST, {_s77: _s523}),
        (lambda: schemas.FOO_ENUM, {_s77: _s525}),
        (lambda: schemas.FOO_ENUM_LIST, {_s77: _s527}),
        (lambda: schemas.INTEGER_ENUM, {_s77: _s529}),
        (lambda: schemas.INTEGER_ENUM_LIST, {_s77: _s531}),
    ),
)

INPUT_AND_OUTPUT_WITH_HEADERS: StaticOperationSchema = (
    23,
    n1,
    _s748,
    {_s714: MappingProxyType({"uri": "/InputAndOutputWithHeaders", "method": "POST"})},
    INPUT_AND_OUTPUT_WITH_HEADERS_INPUT,
    INPUT_AND_OUTPUT_WITH_HEADERS_OUTPUT,
    (),
)
