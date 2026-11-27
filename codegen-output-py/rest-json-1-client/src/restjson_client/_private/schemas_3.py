from types import MappingProxyType

from smithy_core._schema_compact import StaticOperationSchema, StaticSchema

from . import schemas

n1 = "aws.protocoltests.restjson"
_s30 = "smithy.synthetic#originalShapeId"
_s32 = "smithy.api#input"
_s68 = "smithy.api#default"
_s70 = "smithy.api#jsonName"
_s77 = "smithy.api#httpHeader"
_s92 = "smithy.api#output"
_s94 = "smithy.api#timestampFormat"
_s95 = "date-time"
_s107 = "hi"
_s128 = ""
_s181 = "foo"
_s194 = "epoch-seconds"
_s196 = "http-date"
_s199 = "memberEpochSeconds"
_s202 = "memberHttpDate"
_s203 = "memberDateTime"
_s204 = "defaultFormat"
_s205 = "targetEpochSeconds"
_s206 = "targetHttpDate"
_s207 = "targetDateTime"
_s239 = "blob"
_s339 = "stringValue"
_s379 = "data"
_s388 = "bar"
_s421 = "X-Foo"
_s422 = "smithy.api#httpPayload"
_s427 = "a"
_s428 = "b"
_s444 = "smithy.api#Unit"
_s483 = "nested"
_s541 = "JsonBlobsInput"
_s542 = "aws.protocoltests.restjson#JsonBlobsInputOutput"
_s543 = "JsonBlobsOutput"
_s544 = "JsonEnumsInput"
_s545 = "aws.protocoltests.restjson#JsonEnumsInputOutput"
_s546 = "fooEnum1"
_s547 = "fooEnum2"
_s548 = "fooEnum3"
_s549 = "fooEnumList"
_s550 = "fooEnumSet"
_s551 = "fooEnumMap"
_s552 = "JsonEnumsOutput"
_s553 = "JsonIntEnumsInput"
_s554 = "aws.protocoltests.restjson#JsonIntEnumsInputOutput"
_s555 = "integerEnum1"
_s556 = "integerEnum2"
_s557 = "integerEnum3"
_s558 = "integerEnumList"
_s559 = "integerEnumSet"
_s560 = "integerEnumMap"
_s561 = "JsonIntEnumsOutput"
_s562 = "JsonListsInput"
_s563 = "aws.protocoltests.restjson#JsonListsInputOutput"
_s564 = "stringList"
_s565 = "stringSet"
_s566 = "integerList"
_s567 = "booleanList"
_s568 = "timestampList"
_s569 = "enumList"
_s570 = "intEnumList"
_s571 = "nestedStringList"
_s572 = "structureList"
_s573 = "myStructureList"
_s574 = "JsonListsOutput"
_s575 = "JsonMapsInput"
_s576 = "aws.protocoltests.restjson#JsonMapsInputOutput"
_s577 = "denseStructMap"
_s578 = "denseNumberMap"
_s579 = "denseBooleanMap"
_s580 = "denseStringMap"
_s581 = "denseSetMap"
_s582 = "JsonMapsOutput"
_s583 = "JsonTimestampsInput"
_s584 = "aws.protocoltests.restjson#JsonTimestampsInputOutput"
_s585 = "normal"
_s586 = "dateTime"
_s587 = "dateTimeOnTarget"
_s588 = "epochSeconds"
_s589 = "epochSecondsOnTarget"
_s590 = "httpDate"
_s591 = "httpDateOnTarget"
_s592 = "JsonTimestampsOutput"
_s593 = "JsonUnionsInput"
_s594 = "aws.protocoltests.restjson#UnionInputOutput"
_s595 = "contents"
_s596 = "JsonUnionsOutput"
_s597 = "MalformedAcceptWithBodyInput"
_s598 = "MalformedAcceptWithBodyOutput"
_s599 = "aws.protocoltests.shared#GreetingStruct"
_s605 = "MalformedContentTypeWithBodyInput"
_s606 = "MalformedContentTypeWithBodyOutput"
_s609 = "MalformedContentTypeWithoutBodyInput"
_s610 = "MalformedContentTypeWithoutBodyOutput"
_s634 = "NoInputAndNoOutputInput"
_s635 = "NoInputAndNoOutputOutput"
_s637 = "NullAndEmptyHeadersClientInput"
_s638 = "aws.protocoltests.restjson#NullAndEmptyHeadersIO"
_s639 = "X-A"
_s640 = "X-B"
_s641 = "c"
_s642 = "X-C"
_s643 = "NullAndEmptyHeadersClientOutput"
_s644 = "NullAndEmptyHeadersServerInput"
_s645 = "NullAndEmptyHeadersServerOutput"
_s652 = "RecursiveShapesInput"
_s653 = "aws.protocoltests.restjson#RecursiveShapesInputOutput"
_s654 = "RecursiveShapesOutput"
_s655 = "ResponseCodeHttpFallbackInput"
_s656 = "aws.protocoltests.restjson#ResponseCodeHttpFallbackInputOutput"
_s657 = "ResponseCodeHttpFallbackOutput"
_s659 = "SimpleScalarPropertiesInput"
_s660 = "aws.protocoltests.restjson#SimpleScalarPropertiesInputOutput"
_s661 = "trueBooleanValue"
_s662 = "falseBooleanValue"
_s663 = "byteValue"
_s664 = "shortValue"
_s665 = "integerValue"
_s666 = "longValue"
_s667 = "floatValue"
_s668 = "doubleValue"
_s669 = "DoubleDribble"
_s670 = "SimpleScalarPropertiesOutput"
_s671 = "SparseJsonListsInput"
_s672 = "aws.protocoltests.restjson#SparseJsonListsInputOutput"
_s673 = "sparseStringList"
_s674 = "sparseShortList"
_s675 = "SparseJsonListsOutput"
_s676 = "SparseJsonMapsInput"
_s677 = "aws.protocoltests.restjson#SparseJsonMapsInputOutput"
_s678 = "sparseStructMap"
_s679 = "sparseNumberMap"
_s680 = "sparseBooleanMap"
_s681 = "sparseStringMap"
_s682 = "sparseSetMap"
_s683 = "SparseJsonMapsOutput"
_s684 = "StreamingTraitsInput"
_s685 = "aws.protocoltests.restjson#StreamingTraitsInputOutput"
_s686 = "StreamingTraitsOutput"
_s688 = "StreamingTraitsWithMediaTypeInput"
_s689 = "aws.protocoltests.restjson#StreamingTraitsWithMediaTypeInputOutput"
_s690 = "StreamingTraitsWithMediaTypeOutput"
_s691 = "TestBodyStructureInput"
_s692 = "aws.protocoltests.restjson#TestBodyStructureInputOutput"
_s693 = "testId"
_s694 = "x-amz-test-id"
_s695 = "testConfig"
_s696 = "TestBodyStructureOutput"
_s697 = "TestGetNoInputNoPayloadInput"
_s698 = "TestGetNoInputNoPayloadOutput"
_s699 = "aws.protocoltests.restjson#TestNoPayloadInputOutput"
_s700 = "X-Amz-Test-Id"
_s701 = "TestGetNoPayloadInput"
_s702 = "TestGetNoPayloadOutput"
_s703 = "TestPayloadBlobInput"
_s704 = "aws.protocoltests.restjson#TestPayloadBlobInputOutput"
_s705 = "contentType"
_s706 = "Content-Type"
_s707 = "TestPayloadBlobOutput"
_s708 = "TestPayloadStructureInput"
_s709 = "aws.protocoltests.restjson#TestPayloadStructureInputOutput"
_s710 = "payloadConfig"
_s711 = "TestPayloadStructureOutput"
_s712 = "TestPostNoInputNoPayloadInput"
_s713 = "TestPostNoInputNoPayloadOutput"
_s714 = "TestPostNoPayloadInput"
_s715 = "TestPostNoPayloadOutput"
_s716 = "TimestampFormatHeadersInput"
_s717 = "aws.protocoltests.restjson#TimestampFormatHeadersIO"
_s718 = "X-memberEpochSeconds"
_s719 = "X-memberHttpDate"
_s720 = "X-memberDateTime"
_s721 = "X-defaultFormat"
_s722 = "X-targetEpochSeconds"
_s723 = "X-targetHttpDate"
_s724 = "X-targetDateTime"
_s725 = "TimestampFormatHeadersOutput"
_s726 = "UnitInputAndOutputInput"
_s727 = "UnitInputAndOutputOutput"
_s729 = "smithy.api#http"
_s764 = "JsonBlobs"
_s765 = "JsonEnums"
_s766 = "JsonIntEnums"
_s767 = "JsonLists"
_s768 = "JsonMaps"
_s769 = "JsonTimestamps"
_s770 = "JsonUnions"
_s771 = "MalformedAcceptWithBody"
_s777 = "MalformedContentTypeWithBody"
_s780 = "MalformedContentTypeWithoutBody"
_s805 = "NoInputAndNoOutput"
_s807 = "NullAndEmptyHeadersClient"
_s808 = "NullAndEmptyHeadersServer"
_s820 = "RecursiveShapes"
_s821 = "ResponseCodeHttpFallback"
_s823 = "SimpleScalarProperties"
_s824 = "SparseJsonLists"
_s825 = "SparseJsonMaps"
_s826 = "StreamingTraits"
_s828 = "StreamingTraitsWithMediaType"
_s829 = "TestBodyStructure"
_s830 = "TestGetNoInputNoPayload"
_s831 = "TestGetNoPayload"
_s832 = "TestPayloadBlob"
_s833 = "TestPayloadStructure"
_s834 = "TestPostNoInputNoPayload"
_s835 = "TestPostNoPayload"
_s836 = "TimestampFormatHeaders"
_s837 = "UnitInputAndOutput"
_s838 = "RestJson"
_s839 = "aws.api#service"
_s840 = "aws.auth#sigv4"
_s841 = "aws.protocols#restJson1"
_s842 = "RecursiveShapesInputOutputNested1"
_s843 = "RecursiveShapesInputOutputNested2"
_s844 = "recursiveMember"

JSON_BLOBS_INPUT: StaticSchema = (
    18,
    n1,
    _s541,
    {_s30: _s542, _s32: None},
    (_s379,),
    ((1, 0),),
)

JSON_BLOBS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s543,
    {_s30: _s542, _s92: None},
    (_s379,),
    ((1, 0),),
)

JSON_BLOBS: StaticOperationSchema = (
    23,
    n1,
    _s764,
    {_s729: MappingProxyType({"uri": "/JsonBlobs", "method": "POST"})},
    JSON_BLOBS_INPUT,
    JSON_BLOBS_OUTPUT,
    (),
)

JSON_ENUMS_INPUT: StaticSchema = (
    18,
    n1,
    _s544,
    {_s30: _s545, _s32: None},
    (_s546, _s547, _s548, _s549, _s550, _s551),
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
    _s552,
    {_s30: _s545, _s92: None},
    (_s546, _s547, _s548, _s549, _s550, _s551),
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
    _s765,
    {_s729: MappingProxyType({"uri": "/JsonEnums", "method": "PUT"})},
    JSON_ENUMS_INPUT,
    JSON_ENUMS_OUTPUT,
    (),
)

JSON_INT_ENUMS_INPUT: StaticSchema = (
    18,
    n1,
    _s553,
    {_s30: _s554, _s32: None},
    (_s555, _s556, _s557, _s558, _s559, _s560),
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
    _s561,
    {_s30: _s554, _s92: None},
    (_s555, _s556, _s557, _s558, _s559, _s560),
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
    _s766,
    {_s729: MappingProxyType({"uri": "/JsonIntEnums", "method": "PUT"})},
    JSON_INT_ENUMS_INPUT,
    JSON_INT_ENUMS_OUTPUT,
    (),
)

JSON_LISTS_INPUT: StaticSchema = (
    18,
    n1,
    _s562,
    {_s30: _s563, _s32: None},
    (_s564, _s565, _s566, _s567, _s568, _s569, _s570, _s571, _s572),
    (
        (lambda: schemas.STRING_LIST, 0),
        (lambda: schemas.STRING_SET, 0),
        (lambda: schemas.INTEGER_LIST, 0),
        (lambda: schemas.BOOLEAN_LIST, 0),
        (lambda: schemas.TIMESTAMP_LIST, 0),
        (lambda: schemas.FOO_ENUM_LIST, 0),
        (lambda: schemas.INTEGER_ENUM_LIST, 0),
        (lambda: schemas.NESTED_STRING_LIST, 0),
        (lambda: schemas.STRUCTURE_LIST, {_s70: _s573}),
    ),
)

JSON_LISTS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s574,
    {_s30: _s563, _s92: None},
    (_s564, _s565, _s566, _s567, _s568, _s569, _s570, _s571, _s572),
    (
        (lambda: schemas.STRING_LIST, 0),
        (lambda: schemas.STRING_SET, 0),
        (lambda: schemas.INTEGER_LIST, 0),
        (lambda: schemas.BOOLEAN_LIST, 0),
        (lambda: schemas.TIMESTAMP_LIST, 0),
        (lambda: schemas.FOO_ENUM_LIST, 0),
        (lambda: schemas.INTEGER_ENUM_LIST, 0),
        (lambda: schemas.NESTED_STRING_LIST, 0),
        (lambda: schemas.STRUCTURE_LIST, {_s70: _s573}),
    ),
)

JSON_LISTS: StaticOperationSchema = (
    23,
    n1,
    _s767,
    {_s729: MappingProxyType({"uri": "/JsonLists", "method": "PUT"})},
    JSON_LISTS_INPUT,
    JSON_LISTS_OUTPUT,
    (),
)

JSON_MAPS_INPUT: StaticSchema = (
    18,
    n1,
    _s575,
    {_s30: _s576, _s32: None},
    (_s577, _s578, _s579, _s580, _s581),
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
    _s582,
    {_s30: _s576, _s92: None},
    (_s577, _s578, _s579, _s580, _s581),
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
    _s768,
    {_s729: MappingProxyType({"uri": "/JsonMaps", "method": "POST"})},
    JSON_MAPS_INPUT,
    JSON_MAPS_OUTPUT,
    (),
)

JSON_TIMESTAMPS_INPUT: StaticSchema = (
    18,
    n1,
    _s583,
    {_s30: _s584, _s32: None},
    (_s585, _s586, _s587, _s588, _s589, _s590, _s591),
    (
        (4, 0),
        (4, {_s94: _s95}),
        (lambda: schemas.DATE_TIME, 0),
        (4, {_s94: _s194}),
        (lambda: schemas.EPOCH_SECONDS, 0),
        (4, {_s94: _s196}),
        (lambda: schemas.HTTP_DATE, 0),
    ),
)

JSON_TIMESTAMPS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s592,
    {_s30: _s584, _s92: None},
    (_s585, _s586, _s587, _s588, _s589, _s590, _s591),
    (
        (4, 0),
        (4, {_s94: _s95}),
        (lambda: schemas.DATE_TIME, 0),
        (4, {_s94: _s194}),
        (lambda: schemas.EPOCH_SECONDS, 0),
        (4, {_s94: _s196}),
        (lambda: schemas.HTTP_DATE, 0),
    ),
)

JSON_TIMESTAMPS: StaticOperationSchema = (
    23,
    n1,
    _s769,
    {_s729: MappingProxyType({"uri": "/JsonTimestamps", "method": "POST"})},
    JSON_TIMESTAMPS_INPUT,
    JSON_TIMESTAMPS_OUTPUT,
    (),
)

JSON_UNIONS_INPUT: StaticSchema = (
    18,
    n1,
    _s593,
    {_s30: _s594, _s32: None},
    (_s595,),
    ((lambda: schemas.MY_UNION, 0),),
)

JSON_UNIONS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s596,
    {_s30: _s594, _s92: None},
    (_s595,),
    ((lambda: schemas.MY_UNION, 0),),
)

JSON_UNIONS: StaticOperationSchema = (
    23,
    n1,
    _s770,
    {_s729: MappingProxyType({"uri": "/JsonUnions", "method": "PUT"})},
    JSON_UNIONS_INPUT,
    JSON_UNIONS_OUTPUT,
    (),
)

MALFORMED_ACCEPT_WITH_BODY_INPUT: StaticSchema = (
    18,
    n1,
    _s597,
    {_s30: _s444, _s32: None},
)

MALFORMED_ACCEPT_WITH_BODY_OUTPUT: StaticSchema = (
    18,
    n1,
    _s598,
    {_s30: _s599, _s92: None},
    (_s107,),
    ((3, 0),),
)

MALFORMED_ACCEPT_WITH_BODY: StaticOperationSchema = (
    23,
    n1,
    _s771,
    {_s729: MappingProxyType({"method": "POST", "uri": "/MalformedAcceptWithBody"})},
    MALFORMED_ACCEPT_WITH_BODY_INPUT,
    MALFORMED_ACCEPT_WITH_BODY_OUTPUT,
    (),
)

MALFORMED_CONTENT_TYPE_WITH_BODY_INPUT: StaticSchema = (
    18,
    n1,
    _s605,
    {_s30: _s599, _s32: None},
    (_s107,),
    ((3, 0),),
)

MALFORMED_CONTENT_TYPE_WITH_BODY_OUTPUT: StaticSchema = (
    18,
    n1,
    _s606,
    {_s30: _s444, _s92: None},
)

MALFORMED_CONTENT_TYPE_WITH_BODY: StaticOperationSchema = (
    23,
    n1,
    _s777,
    {
        _s729: MappingProxyType(
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
    _s609,
    {_s30: _s444, _s32: None},
)

MALFORMED_CONTENT_TYPE_WITHOUT_BODY_OUTPUT: StaticSchema = (
    18,
    n1,
    _s610,
    {_s30: _s444, _s92: None},
)

MALFORMED_CONTENT_TYPE_WITHOUT_BODY: StaticOperationSchema = (
    23,
    n1,
    _s780,
    {
        _s729: MappingProxyType(
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
    _s634,
    {_s30: _s444, _s32: None},
)

NO_INPUT_AND_NO_OUTPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s635,
    {_s30: _s444, _s92: None},
)

NO_INPUT_AND_NO_OUTPUT: StaticOperationSchema = (
    23,
    n1,
    _s805,
    {_s729: MappingProxyType({"uri": "/NoInputAndNoOutput", "method": "POST"})},
    NO_INPUT_AND_NO_OUTPUT_INPUT,
    NO_INPUT_AND_NO_OUTPUT_OUTPUT,
    (),
)

NULL_AND_EMPTY_HEADERS_CLIENT_INPUT: StaticSchema = (
    18,
    n1,
    _s637,
    {_s30: _s638, _s32: None},
    (_s427, _s428, _s641),
    (
        (3, {_s77: _s639}),
        (3, {_s77: _s640}),
        (lambda: schemas.STRING_LIST, {_s77: _s642}),
    ),
)

NULL_AND_EMPTY_HEADERS_CLIENT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s643,
    {_s30: _s638, _s92: None},
    (_s427, _s428, _s641),
    (
        (3, {_s77: _s639}),
        (3, {_s77: _s640}),
        (lambda: schemas.STRING_LIST, {_s77: _s642}),
    ),
)

NULL_AND_EMPTY_HEADERS_CLIENT: StaticOperationSchema = (
    23,
    n1,
    _s807,
    {_s729: MappingProxyType({"uri": "/NullAndEmptyHeadersClient", "method": "GET"})},
    NULL_AND_EMPTY_HEADERS_CLIENT_INPUT,
    NULL_AND_EMPTY_HEADERS_CLIENT_OUTPUT,
    (),
)

NULL_AND_EMPTY_HEADERS_SERVER_INPUT: StaticSchema = (
    18,
    n1,
    _s644,
    {_s30: _s638, _s32: None},
    (_s427, _s428, _s641),
    (
        (3, {_s77: _s639}),
        (3, {_s77: _s640}),
        (lambda: schemas.STRING_LIST, {_s77: _s642}),
    ),
)

NULL_AND_EMPTY_HEADERS_SERVER_OUTPUT: StaticSchema = (
    18,
    n1,
    _s645,
    {_s30: _s638, _s92: None},
    (_s427, _s428, _s641),
    (
        (3, {_s77: _s639}),
        (3, {_s77: _s640}),
        (lambda: schemas.STRING_LIST, {_s77: _s642}),
    ),
)

NULL_AND_EMPTY_HEADERS_SERVER: StaticOperationSchema = (
    23,
    n1,
    _s808,
    {_s729: MappingProxyType({"uri": "/NullAndEmptyHeadersServer", "method": "GET"})},
    NULL_AND_EMPTY_HEADERS_SERVER_INPUT,
    NULL_AND_EMPTY_HEADERS_SERVER_OUTPUT,
    (),
)

RECURSIVE_SHAPES_INPUT: StaticSchema = (
    18,
    n1,
    _s652,
    {_s30: _s653, _s32: None},
    (_s483,),
    ((lambda: RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED1, 0),),
)

RECURSIVE_SHAPES_OUTPUT: StaticSchema = (
    18,
    n1,
    _s654,
    {_s30: _s653, _s92: None},
    (_s483,),
    ((lambda: RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED1, 0),),
)

RECURSIVE_SHAPES: StaticOperationSchema = (
    23,
    n1,
    _s820,
    {_s729: MappingProxyType({"uri": "/RecursiveShapes", "method": "PUT"})},
    RECURSIVE_SHAPES_INPUT,
    RECURSIVE_SHAPES_OUTPUT,
    (),
)

RESPONSE_CODE_HTTP_FALLBACK_INPUT: StaticSchema = (
    18,
    n1,
    _s655,
    {_s30: _s656, _s32: None},
)

RESPONSE_CODE_HTTP_FALLBACK_OUTPUT: StaticSchema = (
    18,
    n1,
    _s657,
    {_s30: _s656, _s92: None},
)

RESPONSE_CODE_HTTP_FALLBACK: StaticOperationSchema = (
    23,
    n1,
    _s821,
    {
        _s729: MappingProxyType(
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
    _s659,
    {_s30: _s660, _s32: None},
    (_s181, _s339, _s661, _s662, _s663, _s664, _s665, _s666, _s667, _s668),
    (
        (3, {_s77: _s421}),
        (3, 0),
        (2, 0),
        (2, 0),
        (5, 0),
        (6, 0),
        (7, 0),
        (8, 0),
        (9, 0),
        (10, {_s70: _s669}),
    ),
)

SIMPLE_SCALAR_PROPERTIES_OUTPUT: StaticSchema = (
    18,
    n1,
    _s670,
    {_s30: _s660, _s92: None},
    (_s181, _s339, _s661, _s662, _s663, _s664, _s665, _s666, _s667, _s668),
    (
        (3, {_s77: _s421}),
        (3, 0),
        (2, 0),
        (2, 0),
        (5, 0),
        (6, 0),
        (7, 0),
        (8, 0),
        (9, 0),
        (10, {_s70: _s669}),
    ),
)

SIMPLE_SCALAR_PROPERTIES: StaticOperationSchema = (
    23,
    n1,
    _s823,
    {_s729: MappingProxyType({"uri": "/SimpleScalarProperties", "method": "PUT"})},
    SIMPLE_SCALAR_PROPERTIES_INPUT,
    SIMPLE_SCALAR_PROPERTIES_OUTPUT,
    (),
)

SPARSE_JSON_LISTS_INPUT: StaticSchema = (
    18,
    n1,
    _s671,
    {_s30: _s672, _s32: None},
    (_s673, _s674),
    ((lambda: schemas.SPARSE_STRING_LIST, 0), (lambda: schemas.SPARSE_SHORT_LIST, 0)),
)

SPARSE_JSON_LISTS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s675,
    {_s30: _s672, _s92: None},
    (_s673, _s674),
    ((lambda: schemas.SPARSE_STRING_LIST, 0), (lambda: schemas.SPARSE_SHORT_LIST, 0)),
)

SPARSE_JSON_LISTS: StaticOperationSchema = (
    23,
    n1,
    _s824,
    {_s729: MappingProxyType({"uri": "/SparseJsonLists", "method": "PUT"})},
    SPARSE_JSON_LISTS_INPUT,
    SPARSE_JSON_LISTS_OUTPUT,
    (),
)

SPARSE_JSON_MAPS_INPUT: StaticSchema = (
    18,
    n1,
    _s676,
    {_s30: _s677, _s32: None},
    (_s678, _s679, _s680, _s681, _s682),
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
    _s683,
    {_s30: _s677, _s92: None},
    (_s678, _s679, _s680, _s681, _s682),
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
    _s825,
    {_s729: MappingProxyType({"uri": "/SparseJsonMaps", "method": "POST"})},
    SPARSE_JSON_MAPS_INPUT,
    SPARSE_JSON_MAPS_OUTPUT,
    (),
)

STREAMING_TRAITS_INPUT: StaticSchema = (
    18,
    n1,
    _s684,
    {_s30: _s685, _s32: None},
    (_s181, _s239),
    ((3, {_s77: _s421}), (lambda: schemas.STREAMING_BLOB, {_s68: _s128, _s422: None})),
)

STREAMING_TRAITS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s686,
    {_s30: _s685, _s92: None},
    (_s181, _s239),
    ((3, {_s77: _s421}), (lambda: schemas.STREAMING_BLOB, {_s68: _s128, _s422: None})),
)

STREAMING_TRAITS: StaticOperationSchema = (
    23,
    n1,
    _s826,
    {_s729: MappingProxyType({"uri": "/StreamingTraits", "method": "POST"})},
    STREAMING_TRAITS_INPUT,
    STREAMING_TRAITS_OUTPUT,
    (),
)

STREAMING_TRAITS_WITH_MEDIA_TYPE_INPUT: StaticSchema = (
    18,
    n1,
    _s688,
    {_s30: _s689, _s32: None},
    (_s181, _s239),
    (
        (3, {_s77: _s421}),
        (lambda: schemas.STREAMING_TEXT_PLAIN_BLOB, {_s68: _s128, _s422: None}),
    ),
)

STREAMING_TRAITS_WITH_MEDIA_TYPE_OUTPUT: StaticSchema = (
    18,
    n1,
    _s690,
    {_s30: _s689, _s92: None},
    (_s181, _s239),
    (
        (3, {_s77: _s421}),
        (lambda: schemas.STREAMING_TEXT_PLAIN_BLOB, {_s68: _s128, _s422: None}),
    ),
)

STREAMING_TRAITS_WITH_MEDIA_TYPE: StaticOperationSchema = (
    23,
    n1,
    _s828,
    {
        _s729: MappingProxyType(
            {"uri": "/StreamingTraitsWithMediaType", "method": "POST"}
        )
    },
    STREAMING_TRAITS_WITH_MEDIA_TYPE_INPUT,
    STREAMING_TRAITS_WITH_MEDIA_TYPE_OUTPUT,
    (),
)

TEST_BODY_STRUCTURE_INPUT: StaticSchema = (
    18,
    n1,
    _s691,
    {_s30: _s692, _s32: None},
    (_s693, _s695),
    ((3, {_s77: _s694}), (lambda: schemas.TEST_CONFIG, 0)),
)

TEST_BODY_STRUCTURE_OUTPUT: StaticSchema = (
    18,
    n1,
    _s696,
    {_s30: _s692, _s92: None},
    (_s693, _s695),
    ((3, {_s77: _s694}), (lambda: schemas.TEST_CONFIG, 0)),
)

TEST_BODY_STRUCTURE: StaticOperationSchema = (
    23,
    n1,
    _s829,
    {_s729: MappingProxyType({"uri": "/body", "method": "POST"})},
    TEST_BODY_STRUCTURE_INPUT,
    TEST_BODY_STRUCTURE_OUTPUT,
    (),
)

TEST_GET_NO_INPUT_NO_PAYLOAD_INPUT: StaticSchema = (
    18,
    n1,
    _s697,
    {_s30: _s444, _s32: None},
)

TEST_GET_NO_INPUT_NO_PAYLOAD_OUTPUT: StaticSchema = (
    18,
    n1,
    _s698,
    {_s30: _s699, _s92: None},
    (_s693,),
    ((3, {_s77: _s700}),),
)

TEST_GET_NO_INPUT_NO_PAYLOAD: StaticOperationSchema = (
    23,
    n1,
    _s830,
    {_s729: MappingProxyType({"uri": "/no_input_no_payload", "method": "GET"})},
    TEST_GET_NO_INPUT_NO_PAYLOAD_INPUT,
    TEST_GET_NO_INPUT_NO_PAYLOAD_OUTPUT,
    (),
)

TEST_GET_NO_PAYLOAD_INPUT: StaticSchema = (
    18,
    n1,
    _s701,
    {_s30: _s699, _s32: None},
    (_s693,),
    ((3, {_s77: _s700}),),
)

TEST_GET_NO_PAYLOAD_OUTPUT: StaticSchema = (
    18,
    n1,
    _s702,
    {_s30: _s699, _s92: None},
    (_s693,),
    ((3, {_s77: _s700}),),
)

TEST_GET_NO_PAYLOAD: StaticOperationSchema = (
    23,
    n1,
    _s831,
    {_s729: MappingProxyType({"uri": "/no_payload", "method": "GET"})},
    TEST_GET_NO_PAYLOAD_INPUT,
    TEST_GET_NO_PAYLOAD_OUTPUT,
    (),
)

TEST_PAYLOAD_BLOB_INPUT: StaticSchema = (
    18,
    n1,
    _s703,
    {_s30: _s704, _s32: None},
    (_s705, _s379),
    ((3, {_s77: _s706}), (1, 16)),
)

TEST_PAYLOAD_BLOB_OUTPUT: StaticSchema = (
    18,
    n1,
    _s707,
    {_s30: _s704, _s92: None},
    (_s705, _s379),
    ((3, {_s77: _s706}), (1, 16)),
)

TEST_PAYLOAD_BLOB: StaticOperationSchema = (
    23,
    n1,
    _s832,
    {_s729: MappingProxyType({"uri": "/blob_payload", "method": "POST"})},
    TEST_PAYLOAD_BLOB_INPUT,
    TEST_PAYLOAD_BLOB_OUTPUT,
    (),
)

TEST_PAYLOAD_STRUCTURE_INPUT: StaticSchema = (
    18,
    n1,
    _s708,
    {_s30: _s709, _s32: None},
    (_s693, _s710),
    ((3, {_s77: _s694}), (lambda: schemas.PAYLOAD_CONFIG, 16)),
)

TEST_PAYLOAD_STRUCTURE_OUTPUT: StaticSchema = (
    18,
    n1,
    _s711,
    {_s30: _s709, _s92: None},
    (_s693, _s710),
    ((3, {_s77: _s694}), (lambda: schemas.PAYLOAD_CONFIG, 16)),
)

TEST_PAYLOAD_STRUCTURE: StaticOperationSchema = (
    23,
    n1,
    _s833,
    {_s729: MappingProxyType({"uri": "/payload", "method": "POST"})},
    TEST_PAYLOAD_STRUCTURE_INPUT,
    TEST_PAYLOAD_STRUCTURE_OUTPUT,
    (),
)

TEST_POST_NO_INPUT_NO_PAYLOAD_INPUT: StaticSchema = (
    18,
    n1,
    _s712,
    {_s30: _s444, _s32: None},
)

TEST_POST_NO_INPUT_NO_PAYLOAD_OUTPUT: StaticSchema = (
    18,
    n1,
    _s713,
    {_s30: _s699, _s92: None},
    (_s693,),
    ((3, {_s77: _s700}),),
)

TEST_POST_NO_INPUT_NO_PAYLOAD: StaticOperationSchema = (
    23,
    n1,
    _s834,
    {_s729: MappingProxyType({"uri": "/no_input_no_payload", "method": "POST"})},
    TEST_POST_NO_INPUT_NO_PAYLOAD_INPUT,
    TEST_POST_NO_INPUT_NO_PAYLOAD_OUTPUT,
    (),
)

TEST_POST_NO_PAYLOAD_INPUT: StaticSchema = (
    18,
    n1,
    _s714,
    {_s30: _s699, _s32: None},
    (_s693,),
    ((3, {_s77: _s700}),),
)

TEST_POST_NO_PAYLOAD_OUTPUT: StaticSchema = (
    18,
    n1,
    _s715,
    {_s30: _s699, _s92: None},
    (_s693,),
    ((3, {_s77: _s700}),),
)

TEST_POST_NO_PAYLOAD: StaticOperationSchema = (
    23,
    n1,
    _s835,
    {_s729: MappingProxyType({"uri": "/no_payload", "method": "POST"})},
    TEST_POST_NO_PAYLOAD_INPUT,
    TEST_POST_NO_PAYLOAD_OUTPUT,
    (),
)

TIMESTAMP_FORMAT_HEADERS_INPUT: StaticSchema = (
    18,
    n1,
    _s716,
    {_s30: _s717, _s32: None},
    (_s199, _s202, _s203, _s204, _s205, _s206, _s207),
    (
        (4, {_s77: _s718, _s94: _s194}),
        (4, {_s77: _s719, _s94: _s196}),
        (4, {_s77: _s720, _s94: _s95}),
        (4, {_s77: _s721}),
        (lambda: schemas.EPOCH_SECONDS, {_s77: _s722}),
        (lambda: schemas.HTTP_DATE, {_s77: _s723}),
        (lambda: schemas.DATE_TIME, {_s77: _s724}),
    ),
)

TIMESTAMP_FORMAT_HEADERS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s725,
    {_s30: _s717, _s92: None},
    (_s199, _s202, _s203, _s204, _s205, _s206, _s207),
    (
        (4, {_s77: _s718, _s94: _s194}),
        (4, {_s77: _s719, _s94: _s196}),
        (4, {_s77: _s720, _s94: _s95}),
        (4, {_s77: _s721}),
        (lambda: schemas.EPOCH_SECONDS, {_s77: _s722}),
        (lambda: schemas.HTTP_DATE, {_s77: _s723}),
        (lambda: schemas.DATE_TIME, {_s77: _s724}),
    ),
)

TIMESTAMP_FORMAT_HEADERS: StaticOperationSchema = (
    23,
    n1,
    _s836,
    {_s729: MappingProxyType({"uri": "/TimestampFormatHeaders", "method": "POST"})},
    TIMESTAMP_FORMAT_HEADERS_INPUT,
    TIMESTAMP_FORMAT_HEADERS_OUTPUT,
    (),
)

UNIT_INPUT_AND_OUTPUT_INPUT: StaticSchema = (
    18,
    n1,
    _s726,
    {_s30: _s444, _s32: None},
)

UNIT_INPUT_AND_OUTPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s727,
    {_s30: _s444, _s92: None},
)

UNIT_INPUT_AND_OUTPUT: StaticOperationSchema = (
    23,
    n1,
    _s837,
    {_s729: MappingProxyType({"uri": "/UnitInputAndOutput", "method": "POST"})},
    UNIT_INPUT_AND_OUTPUT_INPUT,
    UNIT_INPUT_AND_OUTPUT_OUTPUT,
    (),
)

REST_JSON: StaticSchema = (
    21,
    n1,
    _s838,
    {
        _s839: MappingProxyType({"sdkId": "Rest Json Protocol"}),
        _s840: MappingProxyType({"name": "restjson"}),
        _s841: None,
    },
)

RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED1: StaticSchema = (
    18,
    n1,
    _s842,
    0,
    (_s181, _s483),
    ((3, 0), (lambda: RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED2, 0)),
)

RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED2: StaticSchema = (
    18,
    n1,
    _s843,
    0,
    (_s388, _s844),
    ((3, 0), (RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED1, 0)),
)
