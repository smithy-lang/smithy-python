from types import MappingProxyType

from smithy_core._schema_compact import StaticOperationSchema, StaticSchema

from . import schemas

n1 = "aws.protocoltests.restxml"
_s30 = "smithy.synthetic#originalShapeId"
_s32 = "smithy.api#input"
_s72 = "smithy.api#httpHeader"
_s87 = "smithy.api#output"
_s89 = "smithy.api#timestampFormat"
_s90 = "date-time"
_s99 = "smithy.api#xmlName"
_s103 = "smithy.api#xmlNamespace"
_s106 = "myMap"
_s107 = "smithy.api#xmlFlattened"
_s108 = "KVP"
_s130 = "foo"
_s132 = "epoch-seconds"
_s134 = "http-date"
_s137 = "memberEpochSeconds"
_s140 = "memberHttpDate"
_s141 = "memberDateTime"
_s142 = "defaultFormat"
_s143 = "targetEpochSeconds"
_s144 = "targetHttpDate"
_s145 = "targetDateTime"
_s178 = "emptyString"
_s188 = "data"
_s200 = "bar"
_s206 = "a"
_s207 = "b"
_s212 = "attr"
_s213 = "smithy.api#xmlAttribute"
_s214 = "test"
_s229 = "stringValue"
_s230 = "booleanValue"
_s231 = "byteValue"
_s232 = "shortValue"
_s233 = "integerValue"
_s234 = "longValue"
_s235 = "floatValue"
_s236 = "doubleValue"
_s249 = "nested"
_s279 = "payload"
_s283 = "X-Foo"
_s374 = "aws.protocoltests.restxml#NullAndEmptyHeadersIO"
_s375 = "X-A"
_s376 = "X-B"
_s377 = "c"
_s378 = "X-C"
_s380 = "NullAndEmptyHeadersServerInput"
_s381 = "NullAndEmptyHeadersServerOutput"
_s387 = "RecursiveShapesInput"
_s388 = "aws.protocoltests.restxml#RecursiveShapesRequest"
_s389 = "RecursiveShapesOutput"
_s390 = "aws.protocoltests.restxml#RecursiveShapesResponse"
_s391 = "SimpleScalarPropertiesInput"
_s392 = "aws.protocoltests.restxml#SimpleScalarPropertiesRequest"
_s393 = "trueBooleanValue"
_s394 = "falseBooleanValue"
_s395 = "DoubleDribble"
_s396 = "SimpleScalarPropertiesOutput"
_s397 = "aws.protocoltests.restxml#SimpleScalarPropertiesResponse"
_s398 = "TimestampFormatHeadersInput"
_s399 = "aws.protocoltests.restxml#TimestampFormatHeadersIO"
_s400 = "X-memberEpochSeconds"
_s401 = "X-memberHttpDate"
_s402 = "X-memberDateTime"
_s403 = "X-defaultFormat"
_s404 = "X-targetEpochSeconds"
_s405 = "X-targetHttpDate"
_s406 = "X-targetDateTime"
_s407 = "TimestampFormatHeadersOutput"
_s408 = "XmlAttributesInput"
_s409 = "aws.protocoltests.restxml#XmlAttributesRequest"
_s410 = "XmlAttributesOutput"
_s411 = "aws.protocoltests.restxml#XmlAttributesResponse"
_s412 = "XmlAttributesInMiddleInput"
_s413 = "aws.protocoltests.restxml#XmlAttributesInMiddleRequest"
_s414 = "XmlAttributesInMiddleOutput"
_s415 = "aws.protocoltests.restxml#XmlAttributesInMiddleResponse"
_s416 = "XmlAttributesOnPayloadInput"
_s417 = "aws.protocoltests.restxml#XmlAttributesOnPayloadRequest"
_s418 = "XmlAttributesOnPayloadOutput"
_s419 = "aws.protocoltests.restxml#XmlAttributesOnPayloadResponse"
_s420 = "XmlBlobsInput"
_s421 = "aws.protocoltests.restxml#XmlBlobsRequest"
_s422 = "XmlBlobsOutput"
_s423 = "aws.protocoltests.restxml#XmlBlobsResponse"
_s424 = "XmlEmptyBlobsInput"
_s425 = "aws.protocoltests.restxml#XmlEmptyBlobsRequest"
_s426 = "XmlEmptyBlobsOutput"
_s427 = "aws.protocoltests.restxml#XmlEmptyBlobsResponse"
_s428 = "XmlEmptyListsInput"
_s429 = "aws.protocoltests.restxml#XmlEmptyListsRequest"
_s430 = "stringList"
_s431 = "stringSet"
_s432 = "integerList"
_s433 = "booleanList"
_s434 = "timestampList"
_s435 = "enumList"
_s436 = "intEnumList"
_s437 = "nestedStringList"
_s438 = "renamedListMembers"
_s439 = "renamed"
_s440 = "flattenedList"
_s441 = "flattenedList2"
_s442 = "customName"
_s443 = "flattenedListWithMemberNamespace"
_s444 = "flattenedListWithNamespace"
_s445 = "structureList"
_s446 = "myStructureList"
_s447 = "flattenedStructureList"
_s448 = "XmlEmptyListsOutput"
_s449 = "aws.protocoltests.restxml#XmlEmptyListsResponse"
_s450 = "XmlEmptyMapsInput"
_s451 = "aws.protocoltests.restxml#XmlEmptyMapsRequest"
_s452 = "XmlEmptyMapsOutput"
_s453 = "aws.protocoltests.restxml#XmlEmptyMapsResponse"
_s454 = "XmlEmptyStringsInput"
_s455 = "aws.protocoltests.restxml#XmlEmptyStringsRequest"
_s456 = "XmlEmptyStringsOutput"
_s457 = "aws.protocoltests.restxml#XmlEmptyStringsResponse"
_s458 = "XmlEnumsInput"
_s459 = "aws.protocoltests.restxml#XmlEnumsRequest"
_s460 = "fooEnum1"
_s461 = "fooEnum2"
_s462 = "fooEnum3"
_s463 = "fooEnumList"
_s464 = "fooEnumSet"
_s465 = "fooEnumMap"
_s466 = "XmlEnumsOutput"
_s467 = "aws.protocoltests.restxml#XmlEnumsResponse"
_s468 = "XmlIntEnumsInput"
_s469 = "aws.protocoltests.restxml#XmlIntEnumsRequest"
_s470 = "intEnum1"
_s471 = "intEnum2"
_s472 = "intEnum3"
_s473 = "intEnumSet"
_s474 = "intEnumMap"
_s475 = "XmlIntEnumsOutput"
_s476 = "aws.protocoltests.restxml#XmlIntEnumsResponse"
_s477 = "XmlListsInput"
_s478 = "aws.protocoltests.restxml#XmlListsRequest"
_s479 = "XmlListsOutput"
_s480 = "aws.protocoltests.restxml#XmlListsResponse"
_s481 = "XmlMapWithXmlNamespaceInput"
_s482 = "aws.protocoltests.restxml#XmlMapWithXmlNamespaceRequest"
_s483 = "XmlMapWithXmlNamespaceOutput"
_s484 = "aws.protocoltests.restxml#XmlMapWithXmlNamespaceResponse"
_s485 = "XmlMapsInput"
_s486 = "aws.protocoltests.restxml#XmlMapsRequest"
_s487 = "XmlMapsOutput"
_s488 = "aws.protocoltests.restxml#XmlMapsResponse"
_s489 = "XmlMapsXmlNameInput"
_s490 = "aws.protocoltests.restxml#XmlMapsXmlNameRequest"
_s491 = "XmlMapsXmlNameOutput"
_s492 = "aws.protocoltests.restxml#XmlMapsXmlNameResponse"
_s493 = "XmlNamespacesInput"
_s494 = "aws.protocoltests.restxml#XmlNamespacesRequest"
_s495 = "XmlNamespacesOutput"
_s496 = "aws.protocoltests.restxml#XmlNamespacesResponse"
_s497 = "XmlTimestampsInput"
_s498 = "aws.protocoltests.restxml#XmlTimestampsRequest"
_s499 = "normal"
_s500 = "dateTime"
_s501 = "dateTimeOnTarget"
_s502 = "epochSeconds"
_s503 = "epochSecondsOnTarget"
_s504 = "httpDate"
_s505 = "httpDateOnTarget"
_s506 = "XmlTimestampsOutput"
_s507 = "aws.protocoltests.restxml#XmlTimestampsResponse"
_s508 = "XmlUnionsInput"
_s509 = "aws.protocoltests.restxml#XmlUnionsRequest"
_s510 = "unionValue"
_s511 = "XmlUnionsOutput"
_s512 = "aws.protocoltests.restxml#XmlUnionsResponse"
_s514 = "smithy.api#http"
_s554 = "NullAndEmptyHeadersServer"
_s561 = "RecursiveShapes"
_s562 = "SimpleScalarProperties"
_s563 = "TimestampFormatHeaders"
_s564 = "XmlAttributes"
_s565 = "XmlAttributesInMiddle"
_s566 = "XmlAttributesOnPayload"
_s567 = "XmlBlobs"
_s568 = "XmlEmptyBlobs"
_s569 = "XmlEmptyLists"
_s570 = "XmlEmptyMaps"
_s571 = "XmlEmptyStrings"
_s572 = "XmlEnums"
_s573 = "XmlIntEnums"
_s574 = "XmlLists"
_s575 = "XmlMapWithXmlNamespace"
_s576 = "XmlMaps"
_s577 = "XmlMapsXmlName"
_s578 = "XmlNamespaces"
_s579 = "XmlTimestamps"
_s580 = "XmlUnions"
_s581 = "RestXml"
_s582 = "aws.api#service"
_s583 = "aws.auth#sigv4"
_s584 = "aws.protocols#restXml"
_s585 = "RecursiveShapesInputOutputNested1"
_s586 = "RecursiveShapesInputOutputNested2"
_s587 = "recursiveMember"
_s588 = "XmlUnionShape"
_s589 = "structValue"

NULL_AND_EMPTY_HEADERS_SERVER_INPUT: StaticSchema = (
    18,
    n1,
    _s380,
    {_s30: _s374, _s32: None},
    (_s206, _s207, _s377),
    (
        (3, {_s72: _s375}),
        (3, {_s72: _s376}),
        (lambda: schemas.STRING_LIST, {_s72: _s378}),
    ),
)

NULL_AND_EMPTY_HEADERS_SERVER_OUTPUT: StaticSchema = (
    18,
    n1,
    _s381,
    {_s30: _s374, _s87: None},
    (_s206, _s207, _s377),
    (
        (3, {_s72: _s375}),
        (3, {_s72: _s376}),
        (lambda: schemas.STRING_LIST, {_s72: _s378}),
    ),
)

NULL_AND_EMPTY_HEADERS_SERVER: StaticOperationSchema = (
    23,
    n1,
    _s554,
    {_s514: MappingProxyType({"uri": "/NullAndEmptyHeadersServer", "method": "GET"})},
    NULL_AND_EMPTY_HEADERS_SERVER_INPUT,
    NULL_AND_EMPTY_HEADERS_SERVER_OUTPUT,
    (),
)

RECURSIVE_SHAPES_INPUT: StaticSchema = (
    18,
    n1,
    _s387,
    {_s30: _s388, _s32: None},
    (_s249,),
    ((lambda: RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED1, 0),),
)

RECURSIVE_SHAPES_OUTPUT: StaticSchema = (
    18,
    n1,
    _s389,
    {_s30: _s390, _s87: None},
    (_s249,),
    ((lambda: RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED1, 0),),
)

RECURSIVE_SHAPES: StaticOperationSchema = (
    23,
    n1,
    _s561,
    {_s514: MappingProxyType({"uri": "/RecursiveShapes", "method": "PUT"})},
    RECURSIVE_SHAPES_INPUT,
    RECURSIVE_SHAPES_OUTPUT,
    (),
)

SIMPLE_SCALAR_PROPERTIES_INPUT: StaticSchema = (
    18,
    n1,
    _s391,
    {_s30: _s392, _s32: None},
    (_s130, _s229, _s393, _s394, _s231, _s232, _s233, _s234, _s235, _s236),
    (
        (3, {_s72: _s283}),
        (3, 0),
        (2, 0),
        (2, 0),
        (5, 0),
        (6, 0),
        (7, 0),
        (8, 0),
        (9, 0),
        (10, {_s99: _s395}),
    ),
)

SIMPLE_SCALAR_PROPERTIES_OUTPUT: StaticSchema = (
    18,
    n1,
    _s396,
    {_s30: _s397, _s87: None},
    (_s130, _s229, _s393, _s394, _s231, _s232, _s233, _s234, _s235, _s236),
    (
        (3, {_s72: _s283}),
        (3, 0),
        (2, 0),
        (2, 0),
        (5, 0),
        (6, 0),
        (7, 0),
        (8, 0),
        (9, 0),
        (10, {_s99: _s395}),
    ),
)

SIMPLE_SCALAR_PROPERTIES: StaticOperationSchema = (
    23,
    n1,
    _s562,
    {_s514: MappingProxyType({"uri": "/SimpleScalarProperties", "method": "PUT"})},
    SIMPLE_SCALAR_PROPERTIES_INPUT,
    SIMPLE_SCALAR_PROPERTIES_OUTPUT,
    (),
)

TIMESTAMP_FORMAT_HEADERS_INPUT: StaticSchema = (
    18,
    n1,
    _s398,
    {_s30: _s399, _s32: None},
    (_s137, _s140, _s141, _s142, _s143, _s144, _s145),
    (
        (4, {_s72: _s400, _s89: _s132}),
        (4, {_s72: _s401, _s89: _s134}),
        (4, {_s72: _s402, _s89: _s90}),
        (4, {_s72: _s403}),
        (lambda: schemas.EPOCH_SECONDS, {_s72: _s404}),
        (lambda: schemas.HTTP_DATE, {_s72: _s405}),
        (lambda: schemas.DATE_TIME, {_s72: _s406}),
    ),
)

TIMESTAMP_FORMAT_HEADERS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s407,
    {_s30: _s399, _s87: None},
    (_s137, _s140, _s141, _s142, _s143, _s144, _s145),
    (
        (4, {_s72: _s400, _s89: _s132}),
        (4, {_s72: _s401, _s89: _s134}),
        (4, {_s72: _s402, _s89: _s90}),
        (4, {_s72: _s403}),
        (lambda: schemas.EPOCH_SECONDS, {_s72: _s404}),
        (lambda: schemas.HTTP_DATE, {_s72: _s405}),
        (lambda: schemas.DATE_TIME, {_s72: _s406}),
    ),
)

TIMESTAMP_FORMAT_HEADERS: StaticOperationSchema = (
    23,
    n1,
    _s563,
    {_s514: MappingProxyType({"uri": "/TimestampFormatHeaders", "method": "POST"})},
    TIMESTAMP_FORMAT_HEADERS_INPUT,
    TIMESTAMP_FORMAT_HEADERS_OUTPUT,
    (),
)

XML_ATTRIBUTES_INPUT: StaticSchema = (
    18,
    n1,
    _s408,
    {_s30: _s409, _s32: None},
    (_s130, _s212),
    ((3, 0), (3, {_s213: None, _s99: _s214})),
)

XML_ATTRIBUTES_OUTPUT: StaticSchema = (
    18,
    n1,
    _s410,
    {_s30: _s411, _s87: None},
    (_s130, _s212),
    ((3, 0), (3, {_s213: None, _s99: _s214})),
)

XML_ATTRIBUTES: StaticOperationSchema = (
    23,
    n1,
    _s564,
    {_s514: MappingProxyType({"uri": "/XmlAttributes", "method": "PUT"})},
    XML_ATTRIBUTES_INPUT,
    XML_ATTRIBUTES_OUTPUT,
    (),
)

XML_ATTRIBUTES_IN_MIDDLE_INPUT: StaticSchema = (
    18,
    n1,
    _s412,
    {_s30: _s413, _s32: None},
    (_s279,),
    ((lambda: schemas.XML_ATTRIBUTES_IN_MIDDLE_PAYLOAD_REQUEST, 16),),
)

XML_ATTRIBUTES_IN_MIDDLE_OUTPUT: StaticSchema = (
    18,
    n1,
    _s414,
    {_s30: _s415, _s87: None},
    (_s279,),
    ((lambda: schemas.XML_ATTRIBUTES_IN_MIDDLE_PAYLOAD_RESPONSE, 16),),
)

XML_ATTRIBUTES_IN_MIDDLE: StaticOperationSchema = (
    23,
    n1,
    _s565,
    {_s514: MappingProxyType({"uri": "/XmlAttributesInMiddle", "method": "PUT"})},
    XML_ATTRIBUTES_IN_MIDDLE_INPUT,
    XML_ATTRIBUTES_IN_MIDDLE_OUTPUT,
    (),
)

XML_ATTRIBUTES_ON_PAYLOAD_INPUT: StaticSchema = (
    18,
    n1,
    _s416,
    {_s30: _s417, _s32: None},
    (_s279,),
    ((lambda: schemas.XML_ATTRIBUTES_PAYLOAD_REQUEST, 16),),
)

XML_ATTRIBUTES_ON_PAYLOAD_OUTPUT: StaticSchema = (
    18,
    n1,
    _s418,
    {_s30: _s419, _s87: None},
    (_s279,),
    ((lambda: schemas.XML_ATTRIBUTES_PAYLOAD_RESPONSE, 16),),
)

XML_ATTRIBUTES_ON_PAYLOAD: StaticOperationSchema = (
    23,
    n1,
    _s566,
    {_s514: MappingProxyType({"uri": "/XmlAttributesOnPayload", "method": "PUT"})},
    XML_ATTRIBUTES_ON_PAYLOAD_INPUT,
    XML_ATTRIBUTES_ON_PAYLOAD_OUTPUT,
    (),
)

XML_BLOBS_INPUT: StaticSchema = (
    18,
    n1,
    _s420,
    {_s30: _s421, _s32: None},
    (_s188,),
    ((1, 0),),
)

XML_BLOBS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s422,
    {_s30: _s423, _s87: None},
    (_s188,),
    ((1, 0),),
)

XML_BLOBS: StaticOperationSchema = (
    23,
    n1,
    _s567,
    {_s514: MappingProxyType({"uri": "/XmlBlobs", "method": "POST"})},
    XML_BLOBS_INPUT,
    XML_BLOBS_OUTPUT,
    (),
)

XML_EMPTY_BLOBS_INPUT: StaticSchema = (
    18,
    n1,
    _s424,
    {_s30: _s425, _s32: None},
    (_s188,),
    ((1, 0),),
)

XML_EMPTY_BLOBS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s426,
    {_s30: _s427, _s87: None},
    (_s188,),
    ((1, 0),),
)

XML_EMPTY_BLOBS: StaticOperationSchema = (
    23,
    n1,
    _s568,
    {_s514: MappingProxyType({"uri": "/XmlEmptyBlobs", "method": "POST"})},
    XML_EMPTY_BLOBS_INPUT,
    XML_EMPTY_BLOBS_OUTPUT,
    (),
)

XML_EMPTY_LISTS_INPUT: StaticSchema = (
    18,
    n1,
    _s428,
    {_s30: _s429, _s32: None},
    (
        _s430,
        _s431,
        _s432,
        _s433,
        _s434,
        _s435,
        _s436,
        _s437,
        _s438,
        _s440,
        _s441,
        _s443,
        _s444,
        _s445,
        _s447,
    ),
    (
        (lambda: schemas.STRING_LIST, 0),
        (lambda: schemas.STRING_SET, 0),
        (lambda: schemas.INTEGER_LIST, 0),
        (lambda: schemas.BOOLEAN_LIST, 0),
        (lambda: schemas.TIMESTAMP_LIST, 0),
        (lambda: schemas.FOO_ENUM_LIST, 0),
        (lambda: schemas.INTEGER_ENUM_LIST, 0),
        (lambda: schemas.NESTED_STRING_LIST, 0),
        (lambda: schemas.RENAMED_LIST_MEMBERS, {_s99: _s439}),
        (lambda: schemas.RENAMED_LIST_MEMBERS, {_s107: None}),
        (lambda: schemas.RENAMED_LIST_MEMBERS, {_s107: None, _s99: _s442}),
        (lambda: schemas.LIST_WITH_MEMBER_NAMESPACE, {_s107: None}),
        (lambda: schemas.LIST_WITH_NAMESPACE, {_s107: None}),
        (lambda: schemas.STRUCTURE_LIST, {_s99: _s446}),
        (lambda: schemas.STRUCTURE_LIST, {_s107: None}),
    ),
)

XML_EMPTY_LISTS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s448,
    {_s30: _s449, _s87: None},
    (
        _s430,
        _s431,
        _s432,
        _s433,
        _s434,
        _s435,
        _s436,
        _s437,
        _s438,
        _s440,
        _s441,
        _s443,
        _s444,
        _s445,
        _s447,
    ),
    (
        (lambda: schemas.STRING_LIST, 0),
        (lambda: schemas.STRING_SET, 0),
        (lambda: schemas.INTEGER_LIST, 0),
        (lambda: schemas.BOOLEAN_LIST, 0),
        (lambda: schemas.TIMESTAMP_LIST, 0),
        (lambda: schemas.FOO_ENUM_LIST, 0),
        (lambda: schemas.INTEGER_ENUM_LIST, 0),
        (lambda: schemas.NESTED_STRING_LIST, 0),
        (lambda: schemas.RENAMED_LIST_MEMBERS, {_s99: _s439}),
        (lambda: schemas.RENAMED_LIST_MEMBERS, {_s107: None}),
        (lambda: schemas.RENAMED_LIST_MEMBERS, {_s107: None, _s99: _s442}),
        (lambda: schemas.LIST_WITH_MEMBER_NAMESPACE, {_s107: None}),
        (lambda: schemas.LIST_WITH_NAMESPACE, {_s107: None}),
        (lambda: schemas.STRUCTURE_LIST, {_s99: _s446}),
        (lambda: schemas.STRUCTURE_LIST, {_s107: None}),
    ),
)

XML_EMPTY_LISTS: StaticOperationSchema = (
    23,
    n1,
    _s569,
    {_s514: MappingProxyType({"uri": "/XmlEmptyLists", "method": "PUT"})},
    XML_EMPTY_LISTS_INPUT,
    XML_EMPTY_LISTS_OUTPUT,
    (),
)

XML_EMPTY_MAPS_INPUT: StaticSchema = (
    18,
    n1,
    _s450,
    {_s30: _s451, _s32: None},
    (_s106,),
    ((lambda: schemas.XML_MAPS_INPUT_OUTPUT_MAP, 0),),
)

XML_EMPTY_MAPS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s452,
    {_s30: _s453, _s87: None},
    (_s106,),
    ((lambda: schemas.XML_MAPS_INPUT_OUTPUT_MAP, 0),),
)

XML_EMPTY_MAPS: StaticOperationSchema = (
    23,
    n1,
    _s570,
    {_s514: MappingProxyType({"uri": "/XmlEmptyMaps", "method": "POST"})},
    XML_EMPTY_MAPS_INPUT,
    XML_EMPTY_MAPS_OUTPUT,
    (),
)

XML_EMPTY_STRINGS_INPUT: StaticSchema = (
    18,
    n1,
    _s454,
    {_s30: _s455, _s32: None},
    (_s178,),
    ((3, 0),),
)

XML_EMPTY_STRINGS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s456,
    {_s30: _s457, _s87: None},
    (_s178,),
    ((3, 0),),
)

XML_EMPTY_STRINGS: StaticOperationSchema = (
    23,
    n1,
    _s571,
    {_s514: MappingProxyType({"uri": "/XmlEmptyStrings", "method": "PUT"})},
    XML_EMPTY_STRINGS_INPUT,
    XML_EMPTY_STRINGS_OUTPUT,
    (),
)

XML_ENUMS_INPUT: StaticSchema = (
    18,
    n1,
    _s458,
    {_s30: _s459, _s32: None},
    (_s460, _s461, _s462, _s463, _s464, _s465),
    (
        (lambda: schemas.FOO_ENUM, 0),
        (lambda: schemas.FOO_ENUM, 0),
        (lambda: schemas.FOO_ENUM, 0),
        (lambda: schemas.FOO_ENUM_LIST, 0),
        (lambda: schemas.FOO_ENUM_SET, 0),
        (lambda: schemas.FOO_ENUM_MAP, 0),
    ),
)

XML_ENUMS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s466,
    {_s30: _s467, _s87: None},
    (_s460, _s461, _s462, _s463, _s464, _s465),
    (
        (lambda: schemas.FOO_ENUM, 0),
        (lambda: schemas.FOO_ENUM, 0),
        (lambda: schemas.FOO_ENUM, 0),
        (lambda: schemas.FOO_ENUM_LIST, 0),
        (lambda: schemas.FOO_ENUM_SET, 0),
        (lambda: schemas.FOO_ENUM_MAP, 0),
    ),
)

XML_ENUMS: StaticOperationSchema = (
    23,
    n1,
    _s572,
    {_s514: MappingProxyType({"uri": "/XmlEnums", "method": "PUT"})},
    XML_ENUMS_INPUT,
    XML_ENUMS_OUTPUT,
    (),
)

XML_INT_ENUMS_INPUT: StaticSchema = (
    18,
    n1,
    _s468,
    {_s30: _s469, _s32: None},
    (_s470, _s471, _s472, _s436, _s473, _s474),
    (
        (lambda: schemas.INTEGER_ENUM, 0),
        (lambda: schemas.INTEGER_ENUM, 0),
        (lambda: schemas.INTEGER_ENUM, 0),
        (lambda: schemas.INTEGER_ENUM_LIST, 0),
        (lambda: schemas.INTEGER_ENUM_SET, 0),
        (lambda: schemas.INTEGER_ENUM_MAP, 0),
    ),
)

XML_INT_ENUMS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s475,
    {_s30: _s476, _s87: None},
    (_s470, _s471, _s472, _s436, _s473, _s474),
    (
        (lambda: schemas.INTEGER_ENUM, 0),
        (lambda: schemas.INTEGER_ENUM, 0),
        (lambda: schemas.INTEGER_ENUM, 0),
        (lambda: schemas.INTEGER_ENUM_LIST, 0),
        (lambda: schemas.INTEGER_ENUM_SET, 0),
        (lambda: schemas.INTEGER_ENUM_MAP, 0),
    ),
)

XML_INT_ENUMS: StaticOperationSchema = (
    23,
    n1,
    _s573,
    {_s514: MappingProxyType({"uri": "/XmlIntEnums", "method": "PUT"})},
    XML_INT_ENUMS_INPUT,
    XML_INT_ENUMS_OUTPUT,
    (),
)

XML_LISTS_INPUT: StaticSchema = (
    18,
    n1,
    _s477,
    {_s30: _s478, _s32: None},
    (
        _s430,
        _s431,
        _s432,
        _s433,
        _s434,
        _s435,
        _s436,
        _s437,
        _s438,
        _s440,
        _s441,
        _s443,
        _s444,
        _s445,
        _s447,
    ),
    (
        (lambda: schemas.STRING_LIST, 0),
        (lambda: schemas.STRING_SET, 0),
        (lambda: schemas.INTEGER_LIST, 0),
        (lambda: schemas.BOOLEAN_LIST, 0),
        (lambda: schemas.TIMESTAMP_LIST, 0),
        (lambda: schemas.FOO_ENUM_LIST, 0),
        (lambda: schemas.INTEGER_ENUM_LIST, 0),
        (lambda: schemas.NESTED_STRING_LIST, 0),
        (lambda: schemas.RENAMED_LIST_MEMBERS, {_s99: _s439}),
        (lambda: schemas.RENAMED_LIST_MEMBERS, {_s107: None}),
        (lambda: schemas.RENAMED_LIST_MEMBERS, {_s107: None, _s99: _s442}),
        (lambda: schemas.LIST_WITH_MEMBER_NAMESPACE, {_s107: None}),
        (lambda: schemas.LIST_WITH_NAMESPACE, {_s107: None}),
        (lambda: schemas.STRUCTURE_LIST, {_s99: _s446}),
        (lambda: schemas.STRUCTURE_LIST, {_s107: None}),
    ),
)

XML_LISTS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s479,
    {_s30: _s480, _s87: None},
    (
        _s430,
        _s431,
        _s432,
        _s433,
        _s434,
        _s435,
        _s436,
        _s437,
        _s438,
        _s440,
        _s441,
        _s443,
        _s444,
        _s445,
        _s447,
    ),
    (
        (lambda: schemas.STRING_LIST, 0),
        (lambda: schemas.STRING_SET, 0),
        (lambda: schemas.INTEGER_LIST, 0),
        (lambda: schemas.BOOLEAN_LIST, 0),
        (lambda: schemas.TIMESTAMP_LIST, 0),
        (lambda: schemas.FOO_ENUM_LIST, 0),
        (lambda: schemas.INTEGER_ENUM_LIST, 0),
        (lambda: schemas.NESTED_STRING_LIST, 0),
        (lambda: schemas.RENAMED_LIST_MEMBERS, {_s99: _s439}),
        (lambda: schemas.RENAMED_LIST_MEMBERS, {_s107: None}),
        (lambda: schemas.RENAMED_LIST_MEMBERS, {_s107: None, _s99: _s442}),
        (lambda: schemas.LIST_WITH_MEMBER_NAMESPACE, {_s107: None}),
        (lambda: schemas.LIST_WITH_NAMESPACE, {_s107: None}),
        (lambda: schemas.STRUCTURE_LIST, {_s99: _s446}),
        (lambda: schemas.STRUCTURE_LIST, {_s107: None}),
    ),
)

XML_LISTS: StaticOperationSchema = (
    23,
    n1,
    _s574,
    {_s514: MappingProxyType({"uri": "/XmlLists", "method": "PUT"})},
    XML_LISTS_INPUT,
    XML_LISTS_OUTPUT,
    (),
)

XML_MAP_WITH_XML_NAMESPACE_INPUT: StaticSchema = (
    18,
    n1,
    _s481,
    {_s30: _s482, _s32: None},
    (_s106,),
    (
        (
            lambda: schemas.XML_MAP_WITH_XML_NAMESPACE_INPUT_OUTPUT_MAP,
            {
                _s99: _s108,
                _s103: MappingProxyType({"uri": "https://the-member.example.com"}),
            },
        ),
    ),
)

XML_MAP_WITH_XML_NAMESPACE_OUTPUT: StaticSchema = (
    18,
    n1,
    _s483,
    {_s30: _s484, _s87: None},
    (_s106,),
    (
        (
            lambda: schemas.XML_MAP_WITH_XML_NAMESPACE_INPUT_OUTPUT_MAP,
            {
                _s99: _s108,
                _s103: MappingProxyType({"uri": "https://the-member.example.com"}),
            },
        ),
    ),
)

XML_MAP_WITH_XML_NAMESPACE: StaticOperationSchema = (
    23,
    n1,
    _s575,
    {_s514: MappingProxyType({"uri": "/XmlMapWithXmlNamespace", "method": "POST"})},
    XML_MAP_WITH_XML_NAMESPACE_INPUT,
    XML_MAP_WITH_XML_NAMESPACE_OUTPUT,
    (),
)

XML_MAPS_INPUT: StaticSchema = (
    18,
    n1,
    _s485,
    {_s30: _s486, _s32: None},
    (_s106,),
    ((lambda: schemas.XML_MAPS_INPUT_OUTPUT_MAP, 0),),
)

XML_MAPS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s487,
    {_s30: _s488, _s87: None},
    (_s106,),
    ((lambda: schemas.XML_MAPS_INPUT_OUTPUT_MAP, 0),),
)

XML_MAPS: StaticOperationSchema = (
    23,
    n1,
    _s576,
    {_s514: MappingProxyType({"uri": "/XmlMaps", "method": "POST"})},
    XML_MAPS_INPUT,
    XML_MAPS_OUTPUT,
    (),
)

XML_MAPS_XML_NAME_INPUT: StaticSchema = (
    18,
    n1,
    _s489,
    {_s30: _s490, _s32: None},
    (_s106,),
    ((lambda: schemas.XML_MAPS_XML_NAME_INPUT_OUTPUT_MAP, 0),),
)

XML_MAPS_XML_NAME_OUTPUT: StaticSchema = (
    18,
    n1,
    _s491,
    {_s30: _s492, _s87: None},
    (_s106,),
    ((lambda: schemas.XML_MAPS_XML_NAME_INPUT_OUTPUT_MAP, 0),),
)

XML_MAPS_XML_NAME: StaticOperationSchema = (
    23,
    n1,
    _s577,
    {_s514: MappingProxyType({"uri": "/XmlMapsXmlName", "method": "POST"})},
    XML_MAPS_XML_NAME_INPUT,
    XML_MAPS_XML_NAME_OUTPUT,
    (),
)

XML_NAMESPACES_INPUT: StaticSchema = (
    18,
    n1,
    _s493,
    {_s103: MappingProxyType({"uri": "http://foo.com"}), _s30: _s494, _s32: None},
    (_s249,),
    ((lambda: schemas.XML_NAMESPACE_NESTED, 0),),
)

XML_NAMESPACES_OUTPUT: StaticSchema = (
    18,
    n1,
    _s495,
    {_s103: MappingProxyType({"uri": "http://foo.com"}), _s30: _s496, _s87: None},
    (_s249,),
    ((lambda: schemas.XML_NAMESPACE_NESTED, 0),),
)

XML_NAMESPACES: StaticOperationSchema = (
    23,
    n1,
    _s578,
    {_s514: MappingProxyType({"uri": "/XmlNamespaces", "method": "POST"})},
    XML_NAMESPACES_INPUT,
    XML_NAMESPACES_OUTPUT,
    (),
)

XML_TIMESTAMPS_INPUT: StaticSchema = (
    18,
    n1,
    _s497,
    {_s30: _s498, _s32: None},
    (_s499, _s500, _s501, _s502, _s503, _s504, _s505),
    (
        (4, 0),
        (4, {_s89: _s90}),
        (lambda: schemas.DATE_TIME, 0),
        (4, {_s89: _s132}),
        (lambda: schemas.EPOCH_SECONDS, 0),
        (4, {_s89: _s134}),
        (lambda: schemas.HTTP_DATE, 0),
    ),
)

XML_TIMESTAMPS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s506,
    {_s30: _s507, _s87: None},
    (_s499, _s500, _s501, _s502, _s503, _s504, _s505),
    (
        (4, 0),
        (4, {_s89: _s90}),
        (lambda: schemas.DATE_TIME, 0),
        (4, {_s89: _s132}),
        (lambda: schemas.EPOCH_SECONDS, 0),
        (4, {_s89: _s134}),
        (lambda: schemas.HTTP_DATE, 0),
    ),
)

XML_TIMESTAMPS: StaticOperationSchema = (
    23,
    n1,
    _s579,
    {_s514: MappingProxyType({"uri": "/XmlTimestamps", "method": "POST"})},
    XML_TIMESTAMPS_INPUT,
    XML_TIMESTAMPS_OUTPUT,
    (),
)

XML_UNIONS_INPUT: StaticSchema = (
    18,
    n1,
    _s508,
    {_s30: _s509, _s32: None},
    (_s510,),
    ((lambda: XML_UNION_SHAPE, 0),),
)

XML_UNIONS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s511,
    {_s30: _s512, _s87: None},
    (_s510,),
    ((lambda: XML_UNION_SHAPE, 0),),
)

XML_UNIONS: StaticOperationSchema = (
    23,
    n1,
    _s580,
    {_s514: MappingProxyType({"uri": "/XmlUnions", "method": "PUT"})},
    XML_UNIONS_INPUT,
    XML_UNIONS_OUTPUT,
    (),
)

REST_XML: StaticSchema = (
    21,
    n1,
    _s581,
    {
        _s582: MappingProxyType({"sdkId": "Rest Xml Protocol"}),
        _s583: MappingProxyType({"name": "restxml"}),
        _s584: None,
    },
)

RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED1: StaticSchema = (
    18,
    n1,
    _s585,
    0,
    (_s130, _s249),
    ((3, 0), (lambda: RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED2, 0)),
)

RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED2: StaticSchema = (
    18,
    n1,
    _s586,
    0,
    (_s200, _s587),
    ((3, 0), (RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED1, 0)),
)

XML_UNION_SHAPE: StaticSchema = (
    19,
    n1,
    _s588,
    0,
    (_s229, _s230, _s231, _s232, _s233, _s234, _s235, _s236, _s510, _s589),
    (
        (3, 0),
        (2, 0),
        (5, 0),
        (6, 0),
        (7, 0),
        (8, 0),
        (9, 0),
        (10, 0),
        (lambda: XML_UNION_SHAPE, 0),
        (lambda: schemas.XML_NESTED_UNION_STRUCT, 0),
    ),
)
