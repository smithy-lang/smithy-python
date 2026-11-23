from types import MappingProxyType

from smithy_core._schema_compact import StaticOperationSchema, StaticSchema

from . import schemas

n1 = "aws.protocoltests.restjson"
_s30 = "smithy.synthetic#originalShapeId"
_s32 = "smithy.api#input"
_s70 = "smithy.api#jsonName"
_s77 = "smithy.api#httpHeader"
_s92 = "smithy.api#output"
_s94 = "smithy.api#timestampFormat"
_s95 = "date-time"
_s107 = "hi"
_s178 = "foo"
_s191 = "epoch-seconds"
_s193 = "http-date"
_s196 = "memberEpochSeconds"
_s199 = "memberHttpDate"
_s200 = "memberDateTime"
_s201 = "defaultFormat"
_s202 = "targetEpochSeconds"
_s203 = "targetHttpDate"
_s204 = "targetDateTime"
_s336 = "stringValue"
_s376 = "data"
_s385 = "bar"
_s417 = "a"
_s418 = "b"
_s435 = "smithy.api#Unit"
_s468 = "X-Foo"
_s475 = "nested"
_s533 = "JsonBlobsInput"
_s534 = "aws.protocoltests.restjson#JsonBlobsInputOutput"
_s535 = "JsonBlobsOutput"
_s536 = "JsonEnumsInput"
_s537 = "aws.protocoltests.restjson#JsonEnumsInputOutput"
_s538 = "fooEnum1"
_s539 = "fooEnum2"
_s540 = "fooEnum3"
_s541 = "fooEnumList"
_s542 = "fooEnumSet"
_s543 = "fooEnumMap"
_s544 = "JsonEnumsOutput"
_s545 = "JsonIntEnumsInput"
_s546 = "aws.protocoltests.restjson#JsonIntEnumsInputOutput"
_s547 = "integerEnum1"
_s548 = "integerEnum2"
_s549 = "integerEnum3"
_s550 = "integerEnumList"
_s551 = "integerEnumSet"
_s552 = "integerEnumMap"
_s553 = "JsonIntEnumsOutput"
_s554 = "JsonListsInput"
_s555 = "aws.protocoltests.restjson#JsonListsInputOutput"
_s556 = "stringList"
_s557 = "stringSet"
_s558 = "integerList"
_s559 = "booleanList"
_s560 = "timestampList"
_s561 = "enumList"
_s562 = "intEnumList"
_s563 = "nestedStringList"
_s564 = "structureList"
_s565 = "myStructureList"
_s566 = "JsonListsOutput"
_s567 = "JsonMapsInput"
_s568 = "aws.protocoltests.restjson#JsonMapsInputOutput"
_s569 = "denseStructMap"
_s570 = "denseNumberMap"
_s571 = "denseBooleanMap"
_s572 = "denseStringMap"
_s573 = "denseSetMap"
_s574 = "JsonMapsOutput"
_s575 = "JsonTimestampsInput"
_s576 = "aws.protocoltests.restjson#JsonTimestampsInputOutput"
_s577 = "normal"
_s578 = "dateTime"
_s579 = "dateTimeOnTarget"
_s580 = "epochSeconds"
_s581 = "epochSecondsOnTarget"
_s582 = "httpDate"
_s583 = "httpDateOnTarget"
_s584 = "JsonTimestampsOutput"
_s585 = "JsonUnionsInput"
_s586 = "aws.protocoltests.restjson#UnionInputOutput"
_s587 = "contents"
_s588 = "JsonUnionsOutput"
_s589 = "MalformedAcceptWithBodyInput"
_s590 = "MalformedAcceptWithBodyOutput"
_s591 = "aws.protocoltests.shared#GreetingStruct"
_s597 = "MalformedContentTypeWithBodyInput"
_s598 = "MalformedContentTypeWithBodyOutput"
_s601 = "MalformedContentTypeWithoutBodyInput"
_s602 = "MalformedContentTypeWithoutBodyOutput"
_s626 = "NoInputAndNoOutputInput"
_s627 = "NoInputAndNoOutputOutput"
_s629 = "NullAndEmptyHeadersClientInput"
_s630 = "aws.protocoltests.restjson#NullAndEmptyHeadersIO"
_s631 = "X-A"
_s632 = "X-B"
_s633 = "c"
_s634 = "X-C"
_s635 = "NullAndEmptyHeadersClientOutput"
_s636 = "NullAndEmptyHeadersServerInput"
_s637 = "NullAndEmptyHeadersServerOutput"
_s644 = "RecursiveShapesInput"
_s645 = "aws.protocoltests.restjson#RecursiveShapesInputOutput"
_s646 = "RecursiveShapesOutput"
_s647 = "ResponseCodeHttpFallbackInput"
_s648 = "aws.protocoltests.restjson#ResponseCodeHttpFallbackInputOutput"
_s649 = "ResponseCodeHttpFallbackOutput"
_s651 = "SimpleScalarPropertiesInput"
_s652 = "aws.protocoltests.restjson#SimpleScalarPropertiesInputOutput"
_s653 = "trueBooleanValue"
_s654 = "falseBooleanValue"
_s655 = "byteValue"
_s656 = "shortValue"
_s657 = "integerValue"
_s658 = "longValue"
_s659 = "floatValue"
_s660 = "doubleValue"
_s661 = "DoubleDribble"
_s662 = "SimpleScalarPropertiesOutput"
_s663 = "SparseJsonListsInput"
_s664 = "aws.protocoltests.restjson#SparseJsonListsInputOutput"
_s665 = "sparseStringList"
_s666 = "sparseShortList"
_s667 = "SparseJsonListsOutput"
_s668 = "SparseJsonMapsInput"
_s669 = "aws.protocoltests.restjson#SparseJsonMapsInputOutput"
_s670 = "sparseStructMap"
_s671 = "sparseNumberMap"
_s672 = "sparseBooleanMap"
_s673 = "sparseStringMap"
_s674 = "sparseSetMap"
_s675 = "SparseJsonMapsOutput"
_s676 = "TestBodyStructureInput"
_s677 = "aws.protocoltests.restjson#TestBodyStructureInputOutput"
_s678 = "testId"
_s679 = "x-amz-test-id"
_s680 = "testConfig"
_s681 = "TestBodyStructureOutput"
_s682 = "TestGetNoInputNoPayloadInput"
_s683 = "TestGetNoInputNoPayloadOutput"
_s684 = "aws.protocoltests.restjson#TestNoPayloadInputOutput"
_s685 = "X-Amz-Test-Id"
_s686 = "TestGetNoPayloadInput"
_s687 = "TestGetNoPayloadOutput"
_s688 = "TestPayloadBlobInput"
_s689 = "aws.protocoltests.restjson#TestPayloadBlobInputOutput"
_s690 = "contentType"
_s691 = "Content-Type"
_s692 = "TestPayloadBlobOutput"
_s693 = "TestPayloadStructureInput"
_s694 = "aws.protocoltests.restjson#TestPayloadStructureInputOutput"
_s695 = "payloadConfig"
_s696 = "TestPayloadStructureOutput"
_s697 = "TestPostNoInputNoPayloadInput"
_s698 = "TestPostNoInputNoPayloadOutput"
_s699 = "TestPostNoPayloadInput"
_s700 = "TestPostNoPayloadOutput"
_s701 = "TimestampFormatHeadersInput"
_s702 = "aws.protocoltests.restjson#TimestampFormatHeadersIO"
_s703 = "X-memberEpochSeconds"
_s704 = "X-memberHttpDate"
_s705 = "X-memberDateTime"
_s706 = "X-defaultFormat"
_s707 = "X-targetEpochSeconds"
_s708 = "X-targetHttpDate"
_s709 = "X-targetDateTime"
_s710 = "TimestampFormatHeadersOutput"
_s711 = "UnitInputAndOutputInput"
_s712 = "UnitInputAndOutputOutput"
_s714 = "smithy.api#http"
_s749 = "JsonBlobs"
_s750 = "JsonEnums"
_s751 = "JsonIntEnums"
_s752 = "JsonLists"
_s753 = "JsonMaps"
_s754 = "JsonTimestamps"
_s755 = "JsonUnions"
_s756 = "MalformedAcceptWithBody"
_s762 = "MalformedContentTypeWithBody"
_s765 = "MalformedContentTypeWithoutBody"
_s790 = "NoInputAndNoOutput"
_s792 = "NullAndEmptyHeadersClient"
_s793 = "NullAndEmptyHeadersServer"
_s805 = "RecursiveShapes"
_s806 = "ResponseCodeHttpFallback"
_s808 = "SimpleScalarProperties"
_s809 = "SparseJsonLists"
_s810 = "SparseJsonMaps"
_s811 = "TestBodyStructure"
_s812 = "TestGetNoInputNoPayload"
_s813 = "TestGetNoPayload"
_s814 = "TestPayloadBlob"
_s815 = "TestPayloadStructure"
_s816 = "TestPostNoInputNoPayload"
_s817 = "TestPostNoPayload"
_s818 = "TimestampFormatHeaders"
_s819 = "UnitInputAndOutput"
_s820 = "RestJson"
_s821 = "aws.api#service"
_s822 = "aws.auth#sigv4"
_s823 = "aws.protocols#restJson1"
_s824 = "RecursiveShapesInputOutputNested1"
_s825 = "RecursiveShapesInputOutputNested2"
_s826 = "recursiveMember"

JSON_BLOBS_INPUT: StaticSchema = (
    18,
    n1,
    _s533,
    {_s30: _s534, _s32: None},
    (_s376,),
    ((1, 0),),
)

JSON_BLOBS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s535,
    {_s30: _s534, _s92: None},
    (_s376,),
    ((1, 0),),
)

JSON_BLOBS: StaticOperationSchema = (
    23,
    n1,
    _s749,
    {_s714: MappingProxyType({"uri": "/JsonBlobs", "method": "POST"})},
    JSON_BLOBS_INPUT,
    JSON_BLOBS_OUTPUT,
    (),
)

JSON_ENUMS_INPUT: StaticSchema = (
    18,
    n1,
    _s536,
    {_s30: _s537, _s32: None},
    (_s538, _s539, _s540, _s541, _s542, _s543),
    (
        (lambda: schemas.FOO_ENUM, 0),
        (lambda: schemas.FOO_ENUM, 0),
        (lambda: schemas.FOO_ENUM, 0),
        (lambda: schemas.FOO_ENUM_LIST, 0),
        (lambda: schemas.FOO_ENUM_SET, 0),
        (lambda: schemas.FOO_ENUM_MAP, 0),
    ),
)

JSON_ENUMS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s544,
    {_s30: _s537, _s92: None},
    (_s538, _s539, _s540, _s541, _s542, _s543),
    (
        (lambda: schemas.FOO_ENUM, 0),
        (lambda: schemas.FOO_ENUM, 0),
        (lambda: schemas.FOO_ENUM, 0),
        (lambda: schemas.FOO_ENUM_LIST, 0),
        (lambda: schemas.FOO_ENUM_SET, 0),
        (lambda: schemas.FOO_ENUM_MAP, 0),
    ),
)

JSON_ENUMS: StaticOperationSchema = (
    23,
    n1,
    _s750,
    {_s714: MappingProxyType({"uri": "/JsonEnums", "method": "PUT"})},
    JSON_ENUMS_INPUT,
    JSON_ENUMS_OUTPUT,
    (),
)

JSON_INT_ENUMS_INPUT: StaticSchema = (
    18,
    n1,
    _s545,
    {_s30: _s546, _s32: None},
    (_s547, _s548, _s549, _s550, _s551, _s552),
    (
        (lambda: schemas.INTEGER_ENUM, 0),
        (lambda: schemas.INTEGER_ENUM, 0),
        (lambda: schemas.INTEGER_ENUM, 0),
        (lambda: schemas.INTEGER_ENUM_LIST, 0),
        (lambda: schemas.INTEGER_ENUM_SET, 0),
        (lambda: schemas.INTEGER_ENUM_MAP, 0),
    ),
)

JSON_INT_ENUMS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s553,
    {_s30: _s546, _s92: None},
    (_s547, _s548, _s549, _s550, _s551, _s552),
    (
        (lambda: schemas.INTEGER_ENUM, 0),
        (lambda: schemas.INTEGER_ENUM, 0),
        (lambda: schemas.INTEGER_ENUM, 0),
        (lambda: schemas.INTEGER_ENUM_LIST, 0),
        (lambda: schemas.INTEGER_ENUM_SET, 0),
        (lambda: schemas.INTEGER_ENUM_MAP, 0),
    ),
)

JSON_INT_ENUMS: StaticOperationSchema = (
    23,
    n1,
    _s751,
    {_s714: MappingProxyType({"uri": "/JsonIntEnums", "method": "PUT"})},
    JSON_INT_ENUMS_INPUT,
    JSON_INT_ENUMS_OUTPUT,
    (),
)

JSON_LISTS_INPUT: StaticSchema = (
    18,
    n1,
    _s554,
    {_s30: _s555, _s32: None},
    (_s556, _s557, _s558, _s559, _s560, _s561, _s562, _s563, _s564),
    (
        (lambda: schemas.STRING_LIST, 0),
        (lambda: schemas.STRING_SET, 0),
        (lambda: schemas.INTEGER_LIST, 0),
        (lambda: schemas.BOOLEAN_LIST, 0),
        (lambda: schemas.TIMESTAMP_LIST, 0),
        (lambda: schemas.FOO_ENUM_LIST, 0),
        (lambda: schemas.INTEGER_ENUM_LIST, 0),
        (lambda: schemas.NESTED_STRING_LIST, 0),
        (lambda: schemas.STRUCTURE_LIST, {_s70: _s565}),
    ),
)

JSON_LISTS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s566,
    {_s30: _s555, _s92: None},
    (_s556, _s557, _s558, _s559, _s560, _s561, _s562, _s563, _s564),
    (
        (lambda: schemas.STRING_LIST, 0),
        (lambda: schemas.STRING_SET, 0),
        (lambda: schemas.INTEGER_LIST, 0),
        (lambda: schemas.BOOLEAN_LIST, 0),
        (lambda: schemas.TIMESTAMP_LIST, 0),
        (lambda: schemas.FOO_ENUM_LIST, 0),
        (lambda: schemas.INTEGER_ENUM_LIST, 0),
        (lambda: schemas.NESTED_STRING_LIST, 0),
        (lambda: schemas.STRUCTURE_LIST, {_s70: _s565}),
    ),
)

JSON_LISTS: StaticOperationSchema = (
    23,
    n1,
    _s752,
    {_s714: MappingProxyType({"uri": "/JsonLists", "method": "PUT"})},
    JSON_LISTS_INPUT,
    JSON_LISTS_OUTPUT,
    (),
)

JSON_MAPS_INPUT: StaticSchema = (
    18,
    n1,
    _s567,
    {_s30: _s568, _s32: None},
    (_s569, _s570, _s571, _s572, _s573),
    (
        (lambda: schemas.DENSE_STRUCT_MAP, 0),
        (lambda: schemas.DENSE_NUMBER_MAP, 0),
        (lambda: schemas.DENSE_BOOLEAN_MAP, 0),
        (lambda: schemas.DENSE_STRING_MAP, 0),
        (lambda: schemas.DENSE_SET_MAP, 0),
    ),
)

JSON_MAPS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s574,
    {_s30: _s568, _s92: None},
    (_s569, _s570, _s571, _s572, _s573),
    (
        (lambda: schemas.DENSE_STRUCT_MAP, 0),
        (lambda: schemas.DENSE_NUMBER_MAP, 0),
        (lambda: schemas.DENSE_BOOLEAN_MAP, 0),
        (lambda: schemas.DENSE_STRING_MAP, 0),
        (lambda: schemas.DENSE_SET_MAP, 0),
    ),
)

JSON_MAPS: StaticOperationSchema = (
    23,
    n1,
    _s753,
    {_s714: MappingProxyType({"uri": "/JsonMaps", "method": "POST"})},
    JSON_MAPS_INPUT,
    JSON_MAPS_OUTPUT,
    (),
)

JSON_TIMESTAMPS_INPUT: StaticSchema = (
    18,
    n1,
    _s575,
    {_s30: _s576, _s32: None},
    (_s577, _s578, _s579, _s580, _s581, _s582, _s583),
    (
        (4, 0),
        (4, {_s94: _s95}),
        (lambda: schemas.DATE_TIME, 0),
        (4, {_s94: _s191}),
        (lambda: schemas.EPOCH_SECONDS, 0),
        (4, {_s94: _s193}),
        (lambda: schemas.HTTP_DATE, 0),
    ),
)

JSON_TIMESTAMPS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s584,
    {_s30: _s576, _s92: None},
    (_s577, _s578, _s579, _s580, _s581, _s582, _s583),
    (
        (4, 0),
        (4, {_s94: _s95}),
        (lambda: schemas.DATE_TIME, 0),
        (4, {_s94: _s191}),
        (lambda: schemas.EPOCH_SECONDS, 0),
        (4, {_s94: _s193}),
        (lambda: schemas.HTTP_DATE, 0),
    ),
)

JSON_TIMESTAMPS: StaticOperationSchema = (
    23,
    n1,
    _s754,
    {_s714: MappingProxyType({"uri": "/JsonTimestamps", "method": "POST"})},
    JSON_TIMESTAMPS_INPUT,
    JSON_TIMESTAMPS_OUTPUT,
    (),
)

JSON_UNIONS_INPUT: StaticSchema = (
    18,
    n1,
    _s585,
    {_s30: _s586, _s32: None},
    (_s587,),
    ((lambda: schemas.MY_UNION, 0),),
)

JSON_UNIONS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s588,
    {_s30: _s586, _s92: None},
    (_s587,),
    ((lambda: schemas.MY_UNION, 0),),
)

JSON_UNIONS: StaticOperationSchema = (
    23,
    n1,
    _s755,
    {_s714: MappingProxyType({"uri": "/JsonUnions", "method": "PUT"})},
    JSON_UNIONS_INPUT,
    JSON_UNIONS_OUTPUT,
    (),
)

MALFORMED_ACCEPT_WITH_BODY_INPUT: StaticSchema = (
    18,
    n1,
    _s589,
    {_s30: _s435, _s32: None},
)

MALFORMED_ACCEPT_WITH_BODY_OUTPUT: StaticSchema = (
    18,
    n1,
    _s590,
    {_s30: _s591, _s92: None},
    (_s107,),
    ((3, 0),),
)

MALFORMED_ACCEPT_WITH_BODY: StaticOperationSchema = (
    23,
    n1,
    _s756,
    {_s714: MappingProxyType({"method": "POST", "uri": "/MalformedAcceptWithBody"})},
    MALFORMED_ACCEPT_WITH_BODY_INPUT,
    MALFORMED_ACCEPT_WITH_BODY_OUTPUT,
    (),
)

MALFORMED_CONTENT_TYPE_WITH_BODY_INPUT: StaticSchema = (
    18,
    n1,
    _s597,
    {_s30: _s591, _s32: None},
    (_s107,),
    ((3, 0),),
)

MALFORMED_CONTENT_TYPE_WITH_BODY_OUTPUT: StaticSchema = (
    18,
    n1,
    _s598,
    {_s30: _s435, _s92: None},
)

MALFORMED_CONTENT_TYPE_WITH_BODY: StaticOperationSchema = (
    23,
    n1,
    _s762,
    {
        _s714: MappingProxyType(
            {"method": "POST", "uri": "/MalformedContentTypeWithBody"}
        )
    },
    MALFORMED_CONTENT_TYPE_WITH_BODY_INPUT,
    MALFORMED_CONTENT_TYPE_WITH_BODY_OUTPUT,
    (),
)

MALFORMED_CONTENT_TYPE_WITHOUT_BODY_INPUT: StaticSchema = (
    18,
    n1,
    _s601,
    {_s30: _s435, _s32: None},
)

MALFORMED_CONTENT_TYPE_WITHOUT_BODY_OUTPUT: StaticSchema = (
    18,
    n1,
    _s602,
    {_s30: _s435, _s92: None},
)

MALFORMED_CONTENT_TYPE_WITHOUT_BODY: StaticOperationSchema = (
    23,
    n1,
    _s765,
    {
        _s714: MappingProxyType(
            {"method": "POST", "uri": "/MalformedContentTypeWithoutBody"}
        )
    },
    MALFORMED_CONTENT_TYPE_WITHOUT_BODY_INPUT,
    MALFORMED_CONTENT_TYPE_WITHOUT_BODY_OUTPUT,
    (),
)

NO_INPUT_AND_NO_OUTPUT_INPUT: StaticSchema = (
    18,
    n1,
    _s626,
    {_s30: _s435, _s32: None},
)

NO_INPUT_AND_NO_OUTPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s627,
    {_s30: _s435, _s92: None},
)

NO_INPUT_AND_NO_OUTPUT: StaticOperationSchema = (
    23,
    n1,
    _s790,
    {_s714: MappingProxyType({"uri": "/NoInputAndNoOutput", "method": "POST"})},
    NO_INPUT_AND_NO_OUTPUT_INPUT,
    NO_INPUT_AND_NO_OUTPUT_OUTPUT,
    (),
)

NULL_AND_EMPTY_HEADERS_CLIENT_INPUT: StaticSchema = (
    18,
    n1,
    _s629,
    {_s30: _s630, _s32: None},
    (_s417, _s418, _s633),
    (
        (3, {_s77: _s631}),
        (3, {_s77: _s632}),
        (lambda: schemas.STRING_LIST, {_s77: _s634}),
    ),
)

NULL_AND_EMPTY_HEADERS_CLIENT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s635,
    {_s30: _s630, _s92: None},
    (_s417, _s418, _s633),
    (
        (3, {_s77: _s631}),
        (3, {_s77: _s632}),
        (lambda: schemas.STRING_LIST, {_s77: _s634}),
    ),
)

NULL_AND_EMPTY_HEADERS_CLIENT: StaticOperationSchema = (
    23,
    n1,
    _s792,
    {_s714: MappingProxyType({"uri": "/NullAndEmptyHeadersClient", "method": "GET"})},
    NULL_AND_EMPTY_HEADERS_CLIENT_INPUT,
    NULL_AND_EMPTY_HEADERS_CLIENT_OUTPUT,
    (),
)

NULL_AND_EMPTY_HEADERS_SERVER_INPUT: StaticSchema = (
    18,
    n1,
    _s636,
    {_s30: _s630, _s32: None},
    (_s417, _s418, _s633),
    (
        (3, {_s77: _s631}),
        (3, {_s77: _s632}),
        (lambda: schemas.STRING_LIST, {_s77: _s634}),
    ),
)

NULL_AND_EMPTY_HEADERS_SERVER_OUTPUT: StaticSchema = (
    18,
    n1,
    _s637,
    {_s30: _s630, _s92: None},
    (_s417, _s418, _s633),
    (
        (3, {_s77: _s631}),
        (3, {_s77: _s632}),
        (lambda: schemas.STRING_LIST, {_s77: _s634}),
    ),
)

NULL_AND_EMPTY_HEADERS_SERVER: StaticOperationSchema = (
    23,
    n1,
    _s793,
    {_s714: MappingProxyType({"uri": "/NullAndEmptyHeadersServer", "method": "GET"})},
    NULL_AND_EMPTY_HEADERS_SERVER_INPUT,
    NULL_AND_EMPTY_HEADERS_SERVER_OUTPUT,
    (),
)

RECURSIVE_SHAPES_INPUT: StaticSchema = (
    18,
    n1,
    _s644,
    {_s30: _s645, _s32: None},
    (_s475,),
    ((lambda: RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED1, 0),),
)

RECURSIVE_SHAPES_OUTPUT: StaticSchema = (
    18,
    n1,
    _s646,
    {_s30: _s645, _s92: None},
    (_s475,),
    ((lambda: RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED1, 0),),
)

RECURSIVE_SHAPES: StaticOperationSchema = (
    23,
    n1,
    _s805,
    {_s714: MappingProxyType({"uri": "/RecursiveShapes", "method": "PUT"})},
    RECURSIVE_SHAPES_INPUT,
    RECURSIVE_SHAPES_OUTPUT,
    (),
)

RESPONSE_CODE_HTTP_FALLBACK_INPUT: StaticSchema = (
    18,
    n1,
    _s647,
    {_s30: _s648, _s32: None},
)

RESPONSE_CODE_HTTP_FALLBACK_OUTPUT: StaticSchema = (
    18,
    n1,
    _s649,
    {_s30: _s648, _s92: None},
)

RESPONSE_CODE_HTTP_FALLBACK: StaticOperationSchema = (
    23,
    n1,
    _s806,
    {
        _s714: MappingProxyType(
            {"method": "GET", "uri": "/responseCodeHttpFallback", "code": 201}
        )
    },
    RESPONSE_CODE_HTTP_FALLBACK_INPUT,
    RESPONSE_CODE_HTTP_FALLBACK_OUTPUT,
    (),
)

SIMPLE_SCALAR_PROPERTIES_INPUT: StaticSchema = (
    18,
    n1,
    _s651,
    {_s30: _s652, _s32: None},
    (_s178, _s336, _s653, _s654, _s655, _s656, _s657, _s658, _s659, _s660),
    (
        (3, {_s77: _s468}),
        (3, 0),
        (2, 0),
        (2, 0),
        (5, 0),
        (6, 0),
        (7, 0),
        (8, 0),
        (9, 0),
        (10, {_s70: _s661}),
    ),
)

SIMPLE_SCALAR_PROPERTIES_OUTPUT: StaticSchema = (
    18,
    n1,
    _s662,
    {_s30: _s652, _s92: None},
    (_s178, _s336, _s653, _s654, _s655, _s656, _s657, _s658, _s659, _s660),
    (
        (3, {_s77: _s468}),
        (3, 0),
        (2, 0),
        (2, 0),
        (5, 0),
        (6, 0),
        (7, 0),
        (8, 0),
        (9, 0),
        (10, {_s70: _s661}),
    ),
)

SIMPLE_SCALAR_PROPERTIES: StaticOperationSchema = (
    23,
    n1,
    _s808,
    {_s714: MappingProxyType({"uri": "/SimpleScalarProperties", "method": "PUT"})},
    SIMPLE_SCALAR_PROPERTIES_INPUT,
    SIMPLE_SCALAR_PROPERTIES_OUTPUT,
    (),
)

SPARSE_JSON_LISTS_INPUT: StaticSchema = (
    18,
    n1,
    _s663,
    {_s30: _s664, _s32: None},
    (_s665, _s666),
    ((lambda: schemas.SPARSE_STRING_LIST, 0), (lambda: schemas.SPARSE_SHORT_LIST, 0)),
)

SPARSE_JSON_LISTS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s667,
    {_s30: _s664, _s92: None},
    (_s665, _s666),
    ((lambda: schemas.SPARSE_STRING_LIST, 0), (lambda: schemas.SPARSE_SHORT_LIST, 0)),
)

SPARSE_JSON_LISTS: StaticOperationSchema = (
    23,
    n1,
    _s809,
    {_s714: MappingProxyType({"uri": "/SparseJsonLists", "method": "PUT"})},
    SPARSE_JSON_LISTS_INPUT,
    SPARSE_JSON_LISTS_OUTPUT,
    (),
)

SPARSE_JSON_MAPS_INPUT: StaticSchema = (
    18,
    n1,
    _s668,
    {_s30: _s669, _s32: None},
    (_s670, _s671, _s672, _s673, _s674),
    (
        (lambda: schemas.SPARSE_STRUCT_MAP, 0),
        (lambda: schemas.SPARSE_NUMBER_MAP, 0),
        (lambda: schemas.SPARSE_BOOLEAN_MAP, 0),
        (lambda: schemas.SPARSE_STRING_MAP, 0),
        (lambda: schemas.SPARSE_SET_MAP, 0),
    ),
)

SPARSE_JSON_MAPS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s675,
    {_s30: _s669, _s92: None},
    (_s670, _s671, _s672, _s673, _s674),
    (
        (lambda: schemas.SPARSE_STRUCT_MAP, 0),
        (lambda: schemas.SPARSE_NUMBER_MAP, 0),
        (lambda: schemas.SPARSE_BOOLEAN_MAP, 0),
        (lambda: schemas.SPARSE_STRING_MAP, 0),
        (lambda: schemas.SPARSE_SET_MAP, 0),
    ),
)

SPARSE_JSON_MAPS: StaticOperationSchema = (
    23,
    n1,
    _s810,
    {_s714: MappingProxyType({"uri": "/SparseJsonMaps", "method": "POST"})},
    SPARSE_JSON_MAPS_INPUT,
    SPARSE_JSON_MAPS_OUTPUT,
    (),
)

TEST_BODY_STRUCTURE_INPUT: StaticSchema = (
    18,
    n1,
    _s676,
    {_s30: _s677, _s32: None},
    (_s678, _s680),
    ((3, {_s77: _s679}), (lambda: schemas.TEST_CONFIG, 0)),
)

TEST_BODY_STRUCTURE_OUTPUT: StaticSchema = (
    18,
    n1,
    _s681,
    {_s30: _s677, _s92: None},
    (_s678, _s680),
    ((3, {_s77: _s679}), (lambda: schemas.TEST_CONFIG, 0)),
)

TEST_BODY_STRUCTURE: StaticOperationSchema = (
    23,
    n1,
    _s811,
    {_s714: MappingProxyType({"uri": "/body", "method": "POST"})},
    TEST_BODY_STRUCTURE_INPUT,
    TEST_BODY_STRUCTURE_OUTPUT,
    (),
)

TEST_GET_NO_INPUT_NO_PAYLOAD_INPUT: StaticSchema = (
    18,
    n1,
    _s682,
    {_s30: _s435, _s32: None},
)

TEST_GET_NO_INPUT_NO_PAYLOAD_OUTPUT: StaticSchema = (
    18,
    n1,
    _s683,
    {_s30: _s684, _s92: None},
    (_s678,),
    ((3, {_s77: _s685}),),
)

TEST_GET_NO_INPUT_NO_PAYLOAD: StaticOperationSchema = (
    23,
    n1,
    _s812,
    {_s714: MappingProxyType({"uri": "/no_input_no_payload", "method": "GET"})},
    TEST_GET_NO_INPUT_NO_PAYLOAD_INPUT,
    TEST_GET_NO_INPUT_NO_PAYLOAD_OUTPUT,
    (),
)

TEST_GET_NO_PAYLOAD_INPUT: StaticSchema = (
    18,
    n1,
    _s686,
    {_s30: _s684, _s32: None},
    (_s678,),
    ((3, {_s77: _s685}),),
)

TEST_GET_NO_PAYLOAD_OUTPUT: StaticSchema = (
    18,
    n1,
    _s687,
    {_s30: _s684, _s92: None},
    (_s678,),
    ((3, {_s77: _s685}),),
)

TEST_GET_NO_PAYLOAD: StaticOperationSchema = (
    23,
    n1,
    _s813,
    {_s714: MappingProxyType({"uri": "/no_payload", "method": "GET"})},
    TEST_GET_NO_PAYLOAD_INPUT,
    TEST_GET_NO_PAYLOAD_OUTPUT,
    (),
)

TEST_PAYLOAD_BLOB_INPUT: StaticSchema = (
    18,
    n1,
    _s688,
    {_s30: _s689, _s32: None},
    (_s690, _s376),
    ((3, {_s77: _s691}), (1, 16)),
)

TEST_PAYLOAD_BLOB_OUTPUT: StaticSchema = (
    18,
    n1,
    _s692,
    {_s30: _s689, _s92: None},
    (_s690, _s376),
    ((3, {_s77: _s691}), (1, 16)),
)

TEST_PAYLOAD_BLOB: StaticOperationSchema = (
    23,
    n1,
    _s814,
    {_s714: MappingProxyType({"uri": "/blob_payload", "method": "POST"})},
    TEST_PAYLOAD_BLOB_INPUT,
    TEST_PAYLOAD_BLOB_OUTPUT,
    (),
)

TEST_PAYLOAD_STRUCTURE_INPUT: StaticSchema = (
    18,
    n1,
    _s693,
    {_s30: _s694, _s32: None},
    (_s678, _s695),
    ((3, {_s77: _s679}), (lambda: schemas.PAYLOAD_CONFIG, 16)),
)

TEST_PAYLOAD_STRUCTURE_OUTPUT: StaticSchema = (
    18,
    n1,
    _s696,
    {_s30: _s694, _s92: None},
    (_s678, _s695),
    ((3, {_s77: _s679}), (lambda: schemas.PAYLOAD_CONFIG, 16)),
)

TEST_PAYLOAD_STRUCTURE: StaticOperationSchema = (
    23,
    n1,
    _s815,
    {_s714: MappingProxyType({"uri": "/payload", "method": "POST"})},
    TEST_PAYLOAD_STRUCTURE_INPUT,
    TEST_PAYLOAD_STRUCTURE_OUTPUT,
    (),
)

TEST_POST_NO_INPUT_NO_PAYLOAD_INPUT: StaticSchema = (
    18,
    n1,
    _s697,
    {_s30: _s435, _s32: None},
)

TEST_POST_NO_INPUT_NO_PAYLOAD_OUTPUT: StaticSchema = (
    18,
    n1,
    _s698,
    {_s30: _s684, _s92: None},
    (_s678,),
    ((3, {_s77: _s685}),),
)

TEST_POST_NO_INPUT_NO_PAYLOAD: StaticOperationSchema = (
    23,
    n1,
    _s816,
    {_s714: MappingProxyType({"uri": "/no_input_no_payload", "method": "POST"})},
    TEST_POST_NO_INPUT_NO_PAYLOAD_INPUT,
    TEST_POST_NO_INPUT_NO_PAYLOAD_OUTPUT,
    (),
)

TEST_POST_NO_PAYLOAD_INPUT: StaticSchema = (
    18,
    n1,
    _s699,
    {_s30: _s684, _s32: None},
    (_s678,),
    ((3, {_s77: _s685}),),
)

TEST_POST_NO_PAYLOAD_OUTPUT: StaticSchema = (
    18,
    n1,
    _s700,
    {_s30: _s684, _s92: None},
    (_s678,),
    ((3, {_s77: _s685}),),
)

TEST_POST_NO_PAYLOAD: StaticOperationSchema = (
    23,
    n1,
    _s817,
    {_s714: MappingProxyType({"uri": "/no_payload", "method": "POST"})},
    TEST_POST_NO_PAYLOAD_INPUT,
    TEST_POST_NO_PAYLOAD_OUTPUT,
    (),
)

TIMESTAMP_FORMAT_HEADERS_INPUT: StaticSchema = (
    18,
    n1,
    _s701,
    {_s30: _s702, _s32: None},
    (_s196, _s199, _s200, _s201, _s202, _s203, _s204),
    (
        (4, {_s77: _s703, _s94: _s191}),
        (4, {_s77: _s704, _s94: _s193}),
        (4, {_s77: _s705, _s94: _s95}),
        (4, {_s77: _s706}),
        (lambda: schemas.EPOCH_SECONDS, {_s77: _s707}),
        (lambda: schemas.HTTP_DATE, {_s77: _s708}),
        (lambda: schemas.DATE_TIME, {_s77: _s709}),
    ),
)

TIMESTAMP_FORMAT_HEADERS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s710,
    {_s30: _s702, _s92: None},
    (_s196, _s199, _s200, _s201, _s202, _s203, _s204),
    (
        (4, {_s77: _s703, _s94: _s191}),
        (4, {_s77: _s704, _s94: _s193}),
        (4, {_s77: _s705, _s94: _s95}),
        (4, {_s77: _s706}),
        (lambda: schemas.EPOCH_SECONDS, {_s77: _s707}),
        (lambda: schemas.HTTP_DATE, {_s77: _s708}),
        (lambda: schemas.DATE_TIME, {_s77: _s709}),
    ),
)

TIMESTAMP_FORMAT_HEADERS: StaticOperationSchema = (
    23,
    n1,
    _s818,
    {_s714: MappingProxyType({"uri": "/TimestampFormatHeaders", "method": "POST"})},
    TIMESTAMP_FORMAT_HEADERS_INPUT,
    TIMESTAMP_FORMAT_HEADERS_OUTPUT,
    (),
)

UNIT_INPUT_AND_OUTPUT_INPUT: StaticSchema = (
    18,
    n1,
    _s711,
    {_s30: _s435, _s32: None},
)

UNIT_INPUT_AND_OUTPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s712,
    {_s30: _s435, _s92: None},
)

UNIT_INPUT_AND_OUTPUT: StaticOperationSchema = (
    23,
    n1,
    _s819,
    {_s714: MappingProxyType({"uri": "/UnitInputAndOutput", "method": "POST"})},
    UNIT_INPUT_AND_OUTPUT_INPUT,
    UNIT_INPUT_AND_OUTPUT_OUTPUT,
    (),
)

REST_JSON: StaticSchema = (
    21,
    n1,
    _s820,
    {
        _s821: MappingProxyType({"sdkId": "Rest Json Protocol"}),
        _s822: MappingProxyType({"name": "restjson"}),
        _s823: None,
    },
)

RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED1: StaticSchema = (
    18,
    n1,
    _s824,
    0,
    (_s178, _s475),
    ((3, 0), (lambda: RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED2, 0)),
)

RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED2: StaticSchema = (
    18,
    n1,
    _s825,
    0,
    (_s385, _s826),
    ((3, 0), (RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED1, 0)),
)
