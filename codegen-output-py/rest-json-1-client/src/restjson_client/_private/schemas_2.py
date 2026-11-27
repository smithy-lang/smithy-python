from types import MappingProxyType

from smithy_core._schema_compact import StaticOperationSchema, StaticSchema

from . import schemas

n0 = "aws.protocoltests.shared"
_s1 = "member"
_s9 = "FOO"
_s10 = "smithy.api#enumValue"
_s27 = "key"
_s28 = "value"
n1 = "aws.protocoltests.restjson"
_s30 = "smithy.synthetic#originalShapeId"
_s32 = "smithy.api#input"
_s34 = "smithy.api#httpQuery"
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
_s158 = "smithy.api#streaming"
_s181 = "foo"
_s227 = "smithy.api#mediaType"
_s232 = "payload"
_s239 = "blob"
_s339 = "stringValue"
_s362 = "OperationWithDefaultsInput"
_s363 = "aws.protocoltests.restjson#OperationWithDefaultsInput"
_s364 = "defaults"
_s365 = "clientOptionalDefaults"
_s366 = "topLevelDefault"
_s367 = "otherTopLevelDefault"
_s368 = "OperationWithDefaultsOutput"
_s369 = "aws.protocoltests.restjson#OperationWithDefaultsOutput"
_s370 = "dialog"
_s371 = "dialogList"
_s372 = "dialogMap"
_s373 = "OperationWithNestedStructureInput"
_s374 = "aws.protocoltests.restjson#OperationWithNestedStructureInput"
_s375 = "topLevel"
_s376 = "OperationWithNestedStructureOutput"
_s377 = "aws.protocoltests.restjson#OperationWithNestedStructureOutput"
_s378 = "PayloadConfig"
_s379 = "data"
_s380 = "PlayerAction"
_s381 = "quit"
_s382 = "PostPlayerActionInput"
_s383 = "aws.protocoltests.restjson#PostPlayerActionInput"
_s384 = "action"
_s385 = "PostPlayerActionOutput"
_s386 = "aws.protocoltests.restjson#PostPlayerActionOutput"
_s387 = "UnionWithJsonName"
_s388 = "bar"
_s389 = "_baz"
_s390 = "PostUnionWithJsonNameInput"
_s391 = "aws.protocoltests.restjson#PostUnionWithJsonNameInput"
_s392 = "PostUnionWithJsonNameOutput"
_s393 = "aws.protocoltests.restjson#PostUnionWithJsonNameOutput"
_s394 = "PutWithContentEncodingInput"
_s395 = "aws.protocoltests.restjson#PutWithContentEncodingInput"
_s396 = "encoding"
_s397 = "Content-Encoding"
_s398 = "QueryIdempotencyTokenAutoFillInput"
_s399 = "aws.protocoltests.restjson#QueryIdempotencyTokenAutoFillInput"
_s400 = "token"
_s401 = "smithy.api#idempotencyToken"
_s402 = "QueryMap"
_s403 = "QueryParamsAsStringListMapInput"
_s404 = "aws.protocoltests.restjson#QueryParamsAsStringListMapInput"
_s405 = "qux"
_s406 = "corge"
_s407 = "QueryPrecedenceInput"
_s408 = "aws.protocoltests.restjson#QueryPrecedenceInput"
_s409 = "ResponseCodeRequiredOutput"
_s410 = "aws.protocoltests.restjson#ResponseCodeRequiredOutput"
_s411 = "responseCode"
_s412 = "SparseBooleanMap"
_s413 = "SparseNumberMap"
_s414 = "SparseSetMap"
_s415 = "SparseStructMap"
_s416 = "StreamingBlob"
_s417 = "StreamingTextPlainBlob"
_s418 = "text/plain"
_s419 = "StreamingTraitsRequireLengthInput"
_s420 = "aws.protocoltests.restjson#StreamingTraitsRequireLengthInput"
_s421 = "X-Foo"
_s422 = "smithy.api#httpPayload"
_s423 = "StringEnum"
_s424 = "V"
_s425 = "enumvalue"
_s426 = "StructureListMember"
_s427 = "a"
_s428 = "b"
_s429 = "other"
_s430 = "StructureList"
_s431 = "TestConfig"
_s432 = "timeout"
_s433 = "UnionPayload"
_s434 = "FooEnumMap"
_s435 = "FooEnumSet"
_s436 = "IntegerEnumMap"
_s437 = "IntegerEnumSet"
_s438 = "NestedStringList"
_s439 = "SparseShortList"
_s440 = "SparseStringList"
_s441 = "SparseStringMap"
_s442 = "TextPlainBlob"
_s444 = "smithy.api#Unit"
_s448 = "DocumentTypeInput"
_s449 = "aws.protocoltests.restjson#DocumentTypeInputOutput"
_s450 = "documentValue"
_s451 = "DocumentTypeOutput"
_s452 = "DocumentTypeAsMapValueInput"
_s453 = "aws.protocoltests.restjson#DocumentTypeAsMapValueInputOutput"
_s454 = "docValuedMap"
_s455 = "DocumentTypeAsMapValueOutput"
_s456 = "DocumentTypeAsPayloadInput"
_s457 = "aws.protocoltests.restjson#DocumentTypeAsPayloadInputOutput"
_s458 = "DocumentTypeAsPayloadOutput"
_s459 = "EndpointOperationInput"
_s460 = "EndpointOperationOutput"
_s461 = "EndpointWithHostLabelOperationInput"
_s462 = "aws.protocoltests.restjson#HostLabelInput"
_s463 = "label"
_s464 = "EndpointWithHostLabelOperationOutput"
_s467 = "HostWithPathOperationInput"
_s468 = "HostWithPathOperationOutput"
_s469 = "HttpChecksumRequiredInput"
_s470 = "aws.protocoltests.restjson#HttpChecksumRequiredInputOutput"
_s471 = "HttpChecksumRequiredOutput"
_s472 = "HttpEnumPayloadInput"
_s473 = "aws.protocoltests.restjson#EnumPayloadInput"
_s474 = "HttpEnumPayloadOutput"
_s475 = "HttpPayloadTraitsInput"
_s476 = "aws.protocoltests.restjson#HttpPayloadTraitsInputOutput"
_s477 = "HttpPayloadTraitsOutput"
_s478 = "HttpPayloadTraitsWithMediaTypeInput"
_s479 = "aws.protocoltests.restjson#HttpPayloadTraitsWithMediaTypeInputOutput"
_s480 = "HttpPayloadTraitsWithMediaTypeOutput"
_s481 = "HttpPayloadWithStructureInput"
_s482 = "aws.protocoltests.restjson#HttpPayloadWithStructureInputOutput"
_s483 = "nested"
_s484 = "HttpPayloadWithStructureOutput"
_s485 = "HttpPayloadWithUnionInput"
_s486 = "aws.protocoltests.restjson#HttpPayloadWithUnionInputOutput"
_s487 = "HttpPayloadWithUnionOutput"
_s488 = "HttpQueryParamsOnlyOperationInput"
_s489 = "aws.protocoltests.restjson#HttpQueryParamsOnlyInput"
_s490 = "queryMap"
_s491 = "HttpQueryParamsOnlyOperationOutput"
_s498 = "HttpStringPayloadInput"
_s499 = "aws.protocoltests.restjson#StringPayloadInput"
_s500 = "HttpStringPayloadOutput"
_s502 = "InputAndOutputWithHeadersInput"
_s503 = "aws.protocoltests.restjson#InputAndOutputWithHeadersIO"
_s504 = "headerString"
_s505 = "X-String"
_s506 = "headerByte"
_s507 = "X-Byte"
_s508 = "headerShort"
_s509 = "X-Short"
_s510 = "headerInteger"
_s511 = "X-Integer"
_s512 = "headerLong"
_s513 = "X-Long"
_s514 = "headerFloat"
_s515 = "X-Float"
_s516 = "headerDouble"
_s517 = "X-Double"
_s518 = "headerTrueBool"
_s519 = "X-Boolean1"
_s520 = "headerFalseBool"
_s521 = "X-Boolean2"
_s522 = "headerStringList"
_s523 = "X-StringList"
_s524 = "headerStringSet"
_s525 = "X-StringSet"
_s526 = "headerIntegerList"
_s527 = "X-IntegerList"
_s528 = "headerBooleanList"
_s529 = "X-BooleanList"
_s530 = "headerTimestampList"
_s531 = "X-TimestampList"
_s532 = "headerEnum"
_s533 = "X-Enum"
_s534 = "headerEnumList"
_s535 = "X-EnumList"
_s536 = "headerIntegerEnum"
_s537 = "X-IntegerEnum"
_s538 = "headerIntegerEnumList"
_s539 = "X-IntegerEnumList"
_s540 = "InputAndOutputWithHeadersOutput"
_s648 = "PutWithContentEncodingOutput"
_s649 = "QueryIdempotencyTokenAutoFillOutput"
_s650 = "QueryParamsAsStringListMapOutput"
_s651 = "QueryPrecedenceOutput"
_s658 = "ResponseCodeRequiredInput"
_s687 = "StreamingTraitsRequireLengthOutput"
_s729 = "smithy.api#http"
_s734 = "DocumentType"
_s735 = "DocumentTypeAsMapValue"
_s736 = "DocumentTypeAsPayload"
_s738 = "EndpointOperation"
_s739 = "smithy.api#endpoint"
_s740 = "EndpointWithHostLabelOperation"
_s743 = "HostWithPathOperation"
_s744 = "HttpChecksumRequired"
_s745 = "smithy.api#httpChecksumRequired"
_s747 = "HttpEnumPayload"
_s748 = "HttpPayloadTraits"
_s749 = "HttpPayloadTraitsWithMediaType"
_s750 = "HttpPayloadWithStructure"
_s751 = "HttpPayloadWithUnion"
_s754 = "HttpQueryParamsOnlyOperation"
_s761 = "HttpStringPayload"
_s763 = "InputAndOutputWithHeaders"
_s811 = "OperationWithDefaults"
_s812 = "OperationWithNestedStructure"
_s813 = "PostPlayerAction"
_s814 = "PostUnionWithJsonName"
_s815 = "PutWithContentEncoding"
_s816 = "smithy.api#requestCompression"
_s817 = "QueryIdempotencyTokenAutoFill"
_s818 = "QueryParamsAsStringListMap"
_s819 = "QueryPrecedence"
_s822 = "ResponseCodeRequired"
_s827 = "StreamingTraitsRequireLength"

DOCUMENT: StaticSchema = (
    13,
    n1,
    _s100,
    0,
)

OPERATION_WITH_DEFAULTS_INPUT: StaticSchema = (
    18,
    n1,
    _s362,
    {_s30: _s363, _s32: None},
    (_s364, _s365, _s366, _s367),
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
    _s368,
    {_s30: _s369, _s92: None},
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
    _s811,
    {_s729: MappingProxyType({"uri": "/OperationWithDefaults", "method": "POST"})},
    OPERATION_WITH_DEFAULTS_INPUT,
    OPERATION_WITH_DEFAULTS_OUTPUT,
    (),
)

TOP_LEVEL: StaticSchema = (
    18,
    n1,
    _s79,
    0,
    (_s370, _s371, _s372),
    (
        (lambda: schemas.DIALOG, 1),
        (lambda: schemas.DIALOG_LIST, {_s68: ()}),
        (lambda: schemas.DIALOG_MAP, {_s68: MappingProxyType[str, object]({})}),
    ),
)

OPERATION_WITH_NESTED_STRUCTURE_INPUT: StaticSchema = (
    18,
    n1,
    _s373,
    {_s30: _s374, _s32: None},
    (_s375,),
    ((TOP_LEVEL, 1),),
)

OPERATION_WITH_NESTED_STRUCTURE_OUTPUT: StaticSchema = (
    18,
    n1,
    _s376,
    {_s30: _s377, _s92: None},
    (_s370, _s371, _s372),
    (
        (lambda: schemas.DIALOG, 1),
        (lambda: schemas.DIALOG_LIST, {_s68: ()}),
        (lambda: schemas.DIALOG_MAP, {_s68: MappingProxyType[str, object]({})}),
    ),
)

OPERATION_WITH_NESTED_STRUCTURE: StaticOperationSchema = (
    23,
    n1,
    _s812,
    {
        _s729: MappingProxyType(
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
    _s378,
    0,
    (_s379,),
    ((7, 0),),
)

PLAYER_ACTION: StaticSchema = (
    19,
    n1,
    _s380,
    0,
    (_s381,),
    ((-1, 0),),
)

POST_PLAYER_ACTION_INPUT: StaticSchema = (
    18,
    n1,
    _s382,
    {_s30: _s383, _s32: None},
    (_s384,),
    ((PLAYER_ACTION, 0),),
)

POST_PLAYER_ACTION_OUTPUT: StaticSchema = (
    18,
    n1,
    _s385,
    {_s30: _s386, _s92: None},
    (_s384,),
    ((PLAYER_ACTION, 1),),
)

POST_PLAYER_ACTION: StaticOperationSchema = (
    23,
    n1,
    _s813,
    {_s729: MappingProxyType({"uri": "/PostPlayerAction", "method": "POST"})},
    POST_PLAYER_ACTION_INPUT,
    POST_PLAYER_ACTION_OUTPUT,
    (),
)

UNION_WITH_JSON_NAME: StaticSchema = (
    19,
    n1,
    _s387,
    0,
    (_s181, _s388, _s83),
    ((3, {_s70: _s9}), (3, 0), (3, {_s70: _s389})),
)

POST_UNION_WITH_JSON_NAME_INPUT: StaticSchema = (
    18,
    n1,
    _s390,
    {_s30: _s391, _s32: None},
    (_s28,),
    ((UNION_WITH_JSON_NAME, 0),),
)

POST_UNION_WITH_JSON_NAME_OUTPUT: StaticSchema = (
    18,
    n1,
    _s392,
    {_s30: _s393, _s92: None},
    (_s28,),
    ((UNION_WITH_JSON_NAME, 1),),
)

POST_UNION_WITH_JSON_NAME: StaticOperationSchema = (
    23,
    n1,
    _s814,
    {_s729: MappingProxyType({"uri": "/PostUnionWithJsonName", "method": "POST"})},
    POST_UNION_WITH_JSON_NAME_INPUT,
    POST_UNION_WITH_JSON_NAME_OUTPUT,
    (),
)

PUT_WITH_CONTENT_ENCODING_INPUT: StaticSchema = (
    18,
    n1,
    _s394,
    {_s30: _s395, _s32: None},
    (_s396, _s379),
    ((3, {_s77: _s397}), (3, 0)),
)

PUT_WITH_CONTENT_ENCODING_OUTPUT: StaticSchema = (
    18,
    n1,
    _s648,
    {_s30: _s444, _s92: None},
)

PUT_WITH_CONTENT_ENCODING: StaticOperationSchema = (
    23,
    n1,
    _s815,
    {
        _s729: MappingProxyType(
            {"method": "POST", "uri": "/requestcompression/putcontentwithencoding"}
        ),
        _s816: MappingProxyType({"encodings": ("gzip",)}),
    },
    PUT_WITH_CONTENT_ENCODING_INPUT,
    PUT_WITH_CONTENT_ENCODING_OUTPUT,
    (),
)

QUERY_IDEMPOTENCY_TOKEN_AUTO_FILL_INPUT: StaticSchema = (
    18,
    n1,
    _s398,
    {_s30: _s399, _s32: None},
    (_s400,),
    ((3, {_s34: _s400, _s401: None}),),
)

QUERY_IDEMPOTENCY_TOKEN_AUTO_FILL_OUTPUT: StaticSchema = (
    18,
    n1,
    _s649,
    {_s30: _s444, _s92: None},
)

QUERY_IDEMPOTENCY_TOKEN_AUTO_FILL: StaticOperationSchema = (
    23,
    n1,
    _s817,
    {
        _s729: MappingProxyType(
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
    _s402,
    0,
    (_s27, _s28),
    ((3, 0), (3, 0)),
)

QUERY_PARAMS_AS_STRING_LIST_MAP_INPUT: StaticSchema = (
    18,
    n1,
    _s403,
    {_s30: _s404, _s32: None},
    (_s405, _s181),
    ((3, {_s34: _s406}), (lambda: schemas.STRING_LIST_MAP, 1024)),
)

QUERY_PARAMS_AS_STRING_LIST_MAP_OUTPUT: StaticSchema = (
    18,
    n1,
    _s650,
    {_s30: _s444, _s92: None},
)

QUERY_PARAMS_AS_STRING_LIST_MAP: StaticOperationSchema = (
    23,
    n1,
    _s818,
    {_s729: MappingProxyType({"uri": "/StringListMap", "method": "POST"})},
    QUERY_PARAMS_AS_STRING_LIST_MAP_INPUT,
    QUERY_PARAMS_AS_STRING_LIST_MAP_OUTPUT,
    (),
)

QUERY_PRECEDENCE_INPUT: StaticSchema = (
    18,
    n1,
    _s407,
    {_s30: _s408, _s32: None},
    (_s181, _s83),
    ((3, {_s34: _s388}), (lambda: schemas.STRING_MAP, 1024)),
)

QUERY_PRECEDENCE_OUTPUT: StaticSchema = (
    18,
    n1,
    _s651,
    {_s30: _s444, _s92: None},
)

QUERY_PRECEDENCE: StaticOperationSchema = (
    23,
    n1,
    _s819,
    {_s729: MappingProxyType({"uri": "/Precedence", "method": "POST"})},
    QUERY_PRECEDENCE_INPUT,
    QUERY_PRECEDENCE_OUTPUT,
    (),
)

RESPONSE_CODE_REQUIRED_OUTPUT: StaticSchema = (
    18,
    n1,
    _s409,
    {_s30: _s410, _s92: None},
    (_s411,),
    ((7, 129),),
)

RESPONSE_CODE_REQUIRED_INPUT: StaticSchema = (
    18,
    n1,
    _s658,
    {_s30: _s444, _s32: None},
)

RESPONSE_CODE_REQUIRED: StaticOperationSchema = (
    23,
    n1,
    _s822,
    {
        _s729: MappingProxyType(
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
    _s412,
    64,
    (_s27, _s28),
    ((3, 0), (2, 0)),
)

SPARSE_NUMBER_MAP: StaticSchema = (
    17,
    n1,
    _s413,
    64,
    (_s27, _s28),
    ((3, 0), (7, 0)),
)

SPARSE_SET_MAP: StaticSchema = (
    17,
    n1,
    _s414,
    64,
    (_s27, _s28),
    ((3, 0), (lambda: schemas.STRING_SET, 0)),
)

SPARSE_STRUCT_MAP: StaticSchema = (
    17,
    n1,
    _s415,
    64,
    (_s27, _s28),
    ((3, 0), (lambda: schemas.GREETING_STRUCT, 0)),
)

STREAMING_BLOB: StaticSchema = (
    1,
    n1,
    _s416,
    {_s158: None},
)

STREAMING_TEXT_PLAIN_BLOB: StaticSchema = (
    1,
    n1,
    _s417,
    {_s227: _s418, _s158: None},
)

STREAMING_TRAITS_REQUIRE_LENGTH_INPUT: StaticSchema = (
    18,
    n1,
    _s419,
    {_s30: _s420, _s32: None},
    (_s181, _s239),
    (
        (3, {_s77: _s421}),
        (lambda: schemas.FINITE_STREAMING_BLOB, {_s68: _s128, _s422: None}),
    ),
)

STREAMING_TRAITS_REQUIRE_LENGTH_OUTPUT: StaticSchema = (
    18,
    n1,
    _s687,
    {_s30: _s444, _s92: None},
)

STREAMING_TRAITS_REQUIRE_LENGTH: StaticOperationSchema = (
    23,
    n1,
    _s827,
    {
        _s729: MappingProxyType(
            {"uri": "/StreamingTraitsRequireLength", "method": "POST"}
        )
    },
    STREAMING_TRAITS_REQUIRE_LENGTH_INPUT,
    STREAMING_TRAITS_REQUIRE_LENGTH_OUTPUT,
    (),
)

STRING_ENUM: StaticSchema = (
    14,
    n1,
    _s423,
    0,
    (_s424,),
    ((-1, {_s10: _s425}),),
)

STRUCTURE_LIST_MEMBER: StaticSchema = (
    18,
    n1,
    _s426,
    0,
    (_s427, _s428),
    ((3, {_s70: _s28}), (3, {_s70: _s429})),
)

STRUCTURE_LIST: StaticSchema = (
    16,
    n1,
    _s430,
    0,
    (_s1,),
    ((STRUCTURE_LIST_MEMBER, 0),),
)

TEST_CONFIG: StaticSchema = (
    18,
    n1,
    _s431,
    0,
    (_s432,),
    ((7, 0),),
)

UNION_PAYLOAD: StaticSchema = (
    19,
    n1,
    _s433,
    0,
    (_s148,),
    ((3, 0),),
)

FOO_ENUM_MAP: StaticSchema = (
    17,
    n0,
    _s434,
    0,
    (_s27, _s28),
    ((3, 0), (lambda: schemas.FOO_ENUM, 0)),
)

FOO_ENUM_SET: StaticSchema = (
    16,
    n0,
    _s435,
    0,
    (_s1,),
    ((lambda: schemas.FOO_ENUM, 0),),
)

INTEGER_ENUM_MAP: StaticSchema = (
    17,
    n0,
    _s436,
    0,
    (_s27, _s28),
    ((3, 0), (lambda: schemas.INTEGER_ENUM, 0)),
)

INTEGER_ENUM_SET: StaticSchema = (
    16,
    n0,
    _s437,
    0,
    (_s1,),
    ((lambda: schemas.INTEGER_ENUM, 0),),
)

NESTED_STRING_LIST: StaticSchema = (
    16,
    n0,
    _s438,
    0,
    (_s1,),
    ((lambda: schemas.STRING_LIST, 0),),
)

SPARSE_SHORT_LIST: StaticSchema = (
    16,
    n0,
    _s439,
    64,
    (_s1,),
    ((6, 0),),
)

SPARSE_STRING_LIST: StaticSchema = (
    16,
    n0,
    _s440,
    64,
    (_s1,),
    ((3, 0),),
)

SPARSE_STRING_MAP: StaticSchema = (
    17,
    n0,
    _s441,
    64,
    (_s27, _s28),
    ((3, 0), (3, 0)),
)

TEXT_PLAIN_BLOB: StaticSchema = (
    1,
    n0,
    _s442,
    {_s227: _s418},
)

DOCUMENT_TYPE_INPUT: StaticSchema = (
    18,
    n1,
    _s448,
    {_s30: _s449, _s32: None},
    (_s339, _s450),
    ((3, 0), (DOCUMENT, 0)),
)

DOCUMENT_TYPE_OUTPUT: StaticSchema = (
    18,
    n1,
    _s451,
    {_s30: _s449, _s92: None},
    (_s339, _s450),
    ((3, 0), (DOCUMENT, 0)),
)

DOCUMENT_TYPE: StaticOperationSchema = (
    23,
    n1,
    _s734,
    {_s729: MappingProxyType({"uri": "/DocumentType", "method": "PUT"})},
    DOCUMENT_TYPE_INPUT,
    DOCUMENT_TYPE_OUTPUT,
    (),
)

DOCUMENT_TYPE_AS_MAP_VALUE_INPUT: StaticSchema = (
    18,
    n1,
    _s452,
    {_s30: _s453, _s32: None},
    (_s454,),
    ((lambda: schemas.DOCUMENT_VALUED_MAP, 0),),
)

DOCUMENT_TYPE_AS_MAP_VALUE_OUTPUT: StaticSchema = (
    18,
    n1,
    _s455,
    {_s30: _s453, _s92: None},
    (_s454,),
    ((lambda: schemas.DOCUMENT_VALUED_MAP, 0),),
)

DOCUMENT_TYPE_AS_MAP_VALUE: StaticOperationSchema = (
    23,
    n1,
    _s735,
    {_s729: MappingProxyType({"uri": "/DocumentTypeAsMapValue", "method": "PUT"})},
    DOCUMENT_TYPE_AS_MAP_VALUE_INPUT,
    DOCUMENT_TYPE_AS_MAP_VALUE_OUTPUT,
    (),
)

DOCUMENT_TYPE_AS_PAYLOAD_INPUT: StaticSchema = (
    18,
    n1,
    _s456,
    {_s30: _s457, _s32: None},
    (_s450,),
    ((DOCUMENT, 16),),
)

DOCUMENT_TYPE_AS_PAYLOAD_OUTPUT: StaticSchema = (
    18,
    n1,
    _s458,
    {_s30: _s457, _s92: None},
    (_s450,),
    ((DOCUMENT, 16),),
)

DOCUMENT_TYPE_AS_PAYLOAD: StaticOperationSchema = (
    23,
    n1,
    _s736,
    {_s729: MappingProxyType({"uri": "/DocumentTypeAsPayload", "method": "PUT"})},
    DOCUMENT_TYPE_AS_PAYLOAD_INPUT,
    DOCUMENT_TYPE_AS_PAYLOAD_OUTPUT,
    (),
)

ENDPOINT_OPERATION_INPUT: StaticSchema = (
    18,
    n1,
    _s459,
    {_s30: _s444, _s32: None},
)

ENDPOINT_OPERATION_OUTPUT: StaticSchema = (
    18,
    n1,
    _s460,
    {_s30: _s444, _s92: None},
)

ENDPOINT_OPERATION: StaticOperationSchema = (
    23,
    n1,
    _s738,
    {
        _s739: MappingProxyType({"hostPrefix": "foo."}),
        _s729: MappingProxyType({"uri": "/EndpointOperation", "method": "POST"}),
    },
    ENDPOINT_OPERATION_INPUT,
    ENDPOINT_OPERATION_OUTPUT,
    (),
)

ENDPOINT_WITH_HOST_LABEL_OPERATION_INPUT: StaticSchema = (
    18,
    n1,
    _s461,
    {_s30: _s462, _s32: None},
    (_s463,),
    ((3, 257),),
)

ENDPOINT_WITH_HOST_LABEL_OPERATION_OUTPUT: StaticSchema = (
    18,
    n1,
    _s464,
    {_s30: _s444, _s92: None},
)

ENDPOINT_WITH_HOST_LABEL_OPERATION: StaticOperationSchema = (
    23,
    n1,
    _s740,
    {
        _s739: MappingProxyType({"hostPrefix": "foo.{label}."}),
        _s729: MappingProxyType(
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
    _s467,
    {_s30: _s444, _s32: None},
)

HOST_WITH_PATH_OPERATION_OUTPUT: StaticSchema = (
    18,
    n1,
    _s468,
    {_s30: _s444, _s92: None},
)

HOST_WITH_PATH_OPERATION: StaticOperationSchema = (
    23,
    n1,
    _s743,
    {_s729: MappingProxyType({"uri": "/HostWithPathOperation", "method": "GET"})},
    HOST_WITH_PATH_OPERATION_INPUT,
    HOST_WITH_PATH_OPERATION_OUTPUT,
    (),
)

HTTP_CHECKSUM_REQUIRED_INPUT: StaticSchema = (
    18,
    n1,
    _s469,
    {_s30: _s470, _s32: None},
    (_s181,),
    ((3, 0),),
)

HTTP_CHECKSUM_REQUIRED_OUTPUT: StaticSchema = (
    18,
    n1,
    _s471,
    {_s30: _s470, _s92: None},
    (_s181,),
    ((3, 0),),
)

HTTP_CHECKSUM_REQUIRED: StaticOperationSchema = (
    23,
    n1,
    _s744,
    {
        _s729: MappingProxyType({"uri": "/HttpChecksumRequired", "method": "POST"}),
        _s745: None,
    },
    HTTP_CHECKSUM_REQUIRED_INPUT,
    HTTP_CHECKSUM_REQUIRED_OUTPUT,
    (),
)

HTTP_ENUM_PAYLOAD_INPUT: StaticSchema = (
    18,
    n1,
    _s472,
    {_s30: _s473, _s32: None},
    (_s232,),
    ((STRING_ENUM, 16),),
)

HTTP_ENUM_PAYLOAD_OUTPUT: StaticSchema = (
    18,
    n1,
    _s474,
    {_s30: _s473, _s92: None},
    (_s232,),
    ((STRING_ENUM, 16),),
)

HTTP_ENUM_PAYLOAD: StaticOperationSchema = (
    23,
    n1,
    _s747,
    {_s729: MappingProxyType({"uri": "/EnumPayload", "method": "POST"})},
    HTTP_ENUM_PAYLOAD_INPUT,
    HTTP_ENUM_PAYLOAD_OUTPUT,
    (),
)

HTTP_PAYLOAD_TRAITS_INPUT: StaticSchema = (
    18,
    n1,
    _s475,
    {_s30: _s476, _s32: None},
    (_s181, _s239),
    ((3, {_s77: _s421}), (1, 16)),
)

HTTP_PAYLOAD_TRAITS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s477,
    {_s30: _s476, _s92: None},
    (_s181, _s239),
    ((3, {_s77: _s421}), (1, 16)),
)

HTTP_PAYLOAD_TRAITS: StaticOperationSchema = (
    23,
    n1,
    _s748,
    {_s729: MappingProxyType({"uri": "/HttpPayloadTraits", "method": "POST"})},
    HTTP_PAYLOAD_TRAITS_INPUT,
    HTTP_PAYLOAD_TRAITS_OUTPUT,
    (),
)

HTTP_PAYLOAD_TRAITS_WITH_MEDIA_TYPE_INPUT: StaticSchema = (
    18,
    n1,
    _s478,
    {_s30: _s479, _s32: None},
    (_s181, _s239),
    ((3, {_s77: _s421}), (TEXT_PLAIN_BLOB, 16)),
)

HTTP_PAYLOAD_TRAITS_WITH_MEDIA_TYPE_OUTPUT: StaticSchema = (
    18,
    n1,
    _s480,
    {_s30: _s479, _s92: None},
    (_s181, _s239),
    ((3, {_s77: _s421}), (TEXT_PLAIN_BLOB, 16)),
)

HTTP_PAYLOAD_TRAITS_WITH_MEDIA_TYPE: StaticOperationSchema = (
    23,
    n1,
    _s749,
    {
        _s729: MappingProxyType(
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
    _s481,
    {_s30: _s482, _s32: None},
    (_s483,),
    ((lambda: schemas.NESTED_PAYLOAD, 16),),
)

HTTP_PAYLOAD_WITH_STRUCTURE_OUTPUT: StaticSchema = (
    18,
    n1,
    _s484,
    {_s30: _s482, _s92: None},
    (_s483,),
    ((lambda: schemas.NESTED_PAYLOAD, 16),),
)

HTTP_PAYLOAD_WITH_STRUCTURE: StaticOperationSchema = (
    23,
    n1,
    _s750,
    {_s729: MappingProxyType({"uri": "/HttpPayloadWithStructure", "method": "PUT"})},
    HTTP_PAYLOAD_WITH_STRUCTURE_INPUT,
    HTTP_PAYLOAD_WITH_STRUCTURE_OUTPUT,
    (),
)

HTTP_PAYLOAD_WITH_UNION_INPUT: StaticSchema = (
    18,
    n1,
    _s485,
    {_s30: _s486, _s32: None},
    (_s483,),
    ((UNION_PAYLOAD, 16),),
)

HTTP_PAYLOAD_WITH_UNION_OUTPUT: StaticSchema = (
    18,
    n1,
    _s487,
    {_s30: _s486, _s92: None},
    (_s483,),
    ((UNION_PAYLOAD, 16),),
)

HTTP_PAYLOAD_WITH_UNION: StaticOperationSchema = (
    23,
    n1,
    _s751,
    {_s729: MappingProxyType({"uri": "/HttpPayloadWithUnion", "method": "PUT"})},
    HTTP_PAYLOAD_WITH_UNION_INPUT,
    HTTP_PAYLOAD_WITH_UNION_OUTPUT,
    (),
)

HTTP_QUERY_PARAMS_ONLY_OPERATION_INPUT: StaticSchema = (
    18,
    n1,
    _s488,
    {_s30: _s489, _s32: None},
    (_s490,),
    ((QUERY_MAP, 1024),),
)

HTTP_QUERY_PARAMS_ONLY_OPERATION_OUTPUT: StaticSchema = (
    18,
    n1,
    _s491,
    {_s30: _s444, _s92: None},
)

HTTP_QUERY_PARAMS_ONLY_OPERATION: StaticOperationSchema = (
    23,
    n1,
    _s754,
    {_s729: MappingProxyType({"uri": "/http-query-params-only", "method": "GET"})},
    HTTP_QUERY_PARAMS_ONLY_OPERATION_INPUT,
    HTTP_QUERY_PARAMS_ONLY_OPERATION_OUTPUT,
    (),
)

HTTP_STRING_PAYLOAD_INPUT: StaticSchema = (
    18,
    n1,
    _s498,
    {_s30: _s499, _s32: None},
    (_s232,),
    ((3, 16),),
)

HTTP_STRING_PAYLOAD_OUTPUT: StaticSchema = (
    18,
    n1,
    _s500,
    {_s30: _s499, _s92: None},
    (_s232,),
    ((3, 16),),
)

HTTP_STRING_PAYLOAD: StaticOperationSchema = (
    23,
    n1,
    _s761,
    {_s729: MappingProxyType({"uri": "/StringPayload", "method": "POST"})},
    HTTP_STRING_PAYLOAD_INPUT,
    HTTP_STRING_PAYLOAD_OUTPUT,
    (),
)

INPUT_AND_OUTPUT_WITH_HEADERS_INPUT: StaticSchema = (
    18,
    n1,
    _s502,
    {_s30: _s503, _s32: None},
    (
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
        _s532,
        _s534,
        _s536,
        _s538,
    ),
    (
        (3, {_s77: _s505}),
        (5, {_s77: _s507}),
        (6, {_s77: _s509}),
        (7, {_s77: _s511}),
        (8, {_s77: _s513}),
        (9, {_s77: _s515}),
        (10, {_s77: _s517}),
        (2, {_s77: _s519}),
        (2, {_s77: _s521}),
        (lambda: schemas.STRING_LIST, {_s77: _s523}),
        (lambda: schemas.STRING_SET, {_s77: _s525}),
        (lambda: schemas.INTEGER_LIST, {_s77: _s527}),
        (lambda: schemas.BOOLEAN_LIST, {_s77: _s529}),
        (lambda: schemas.TIMESTAMP_LIST, {_s77: _s531}),
        (lambda: schemas.FOO_ENUM, {_s77: _s533}),
        (lambda: schemas.FOO_ENUM_LIST, {_s77: _s535}),
        (lambda: schemas.INTEGER_ENUM, {_s77: _s537}),
        (lambda: schemas.INTEGER_ENUM_LIST, {_s77: _s539}),
    ),
)

INPUT_AND_OUTPUT_WITH_HEADERS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s540,
    {_s30: _s503, _s92: None},
    (
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
        _s532,
        _s534,
        _s536,
        _s538,
    ),
    (
        (3, {_s77: _s505}),
        (5, {_s77: _s507}),
        (6, {_s77: _s509}),
        (7, {_s77: _s511}),
        (8, {_s77: _s513}),
        (9, {_s77: _s515}),
        (10, {_s77: _s517}),
        (2, {_s77: _s519}),
        (2, {_s77: _s521}),
        (lambda: schemas.STRING_LIST, {_s77: _s523}),
        (lambda: schemas.STRING_SET, {_s77: _s525}),
        (lambda: schemas.INTEGER_LIST, {_s77: _s527}),
        (lambda: schemas.BOOLEAN_LIST, {_s77: _s529}),
        (lambda: schemas.TIMESTAMP_LIST, {_s77: _s531}),
        (lambda: schemas.FOO_ENUM, {_s77: _s533}),
        (lambda: schemas.FOO_ENUM_LIST, {_s77: _s535}),
        (lambda: schemas.INTEGER_ENUM, {_s77: _s537}),
        (lambda: schemas.INTEGER_ENUM_LIST, {_s77: _s539}),
    ),
)

INPUT_AND_OUTPUT_WITH_HEADERS: StaticOperationSchema = (
    23,
    n1,
    _s763,
    {_s729: MappingProxyType({"uri": "/InputAndOutputWithHeaders", "method": "POST"})},
    INPUT_AND_OUTPUT_WITH_HEADERS_INPUT,
    INPUT_AND_OUTPUT_WITH_HEADERS_OUTPUT,
    (),
)
