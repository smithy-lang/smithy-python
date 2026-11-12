from types import MappingProxyType

from smithy_core._schema_compact import StaticSchema

from . import schemas

n0 = "aws.protocoltests.shared"
_s1 = "member"
_s27 = "key"
_s28 = "value"
n1 = "aws.protocoltests.restxml"
_s30 = "smithy.api#input"
_s32 = "smithy.api#httpQuery"
_s65 = "smithy.api#xmlName"
_s70 = "smithy.api#output"
_s71 = "nested"
_s78 = "smithy.api#httpHeader"
_s83 = "baz"
_s90 = "smithy.api#timestampFormat"
_s91 = "date-time"
_s99 = "V"
_s102 = "payload"
_s105 = "myMap"
_s106 = "smithy.api#xmlFlattened"
_s109 = "K"
_s111 = "KVP"
_s114 = "smithy.api#xmlNamespace"
_s133 = "foo"
_s134 = "X-Foo"
_s161 = "epoch-seconds"
_s163 = "http-date"
_s165 = "memberEpochSeconds"
_s167 = "memberHttpDate"
_s168 = "memberDateTime"
_s169 = "defaultFormat"
_s170 = "targetEpochSeconds"
_s171 = "targetHttpDate"
_s172 = "targetDateTime"
_s235 = "a"
_s237 = "b"
_s244 = "emptyString"
_s249 = "data"
_s250 = "QueryIdempotencyTokenAutoFillInput"
_s251 = "token"
_s252 = "smithy.api#idempotencyToken"
_s253 = "StringListMap"
_s254 = "QueryParamsAsStringListMapInput"
_s255 = "qux"
_s256 = "corge"
_s257 = "QueryPrecedenceInput"
_s258 = "bar"
_s259 = "RecursiveShapesRequest"
_s260 = "RecursiveShapesResponse"
_s261 = "RenamedListMembers"
_s262 = "item"
_s263 = "SimpleScalarPropertiesRequest"
_s264 = "stringValue"
_s265 = "trueBooleanValue"
_s266 = "falseBooleanValue"
_s267 = "byteValue"
_s268 = "shortValue"
_s269 = "integerValue"
_s270 = "longValue"
_s271 = "floatValue"
_s272 = "doubleValue"
_s273 = "DoubleDribble"
_s274 = "SimpleScalarPropertiesResponse"
_s275 = "StringPayloadInput"
_s276 = "StructureListMember"
_s277 = "other"
_s278 = "StructureList"
_s279 = "TimestampFormatHeadersIO"
_s280 = "X-memberEpochSeconds"
_s281 = "X-memberHttpDate"
_s282 = "X-memberDateTime"
_s283 = "X-defaultFormat"
_s284 = "X-targetEpochSeconds"
_s285 = "X-targetHttpDate"
_s286 = "X-targetDateTime"
_s287 = "XmlAttributesInMiddlePayloadRequest"
_s288 = "attr"
_s289 = "smithy.api#xmlAttribute"
_s290 = "test"
_s291 = "XmlAttributesInMiddlePayloadResponse"
_s292 = "XmlAttributesInMiddleRequest"
_s293 = "XmlAttributesInMiddleResponse"
_s294 = "XmlAttributesPayloadRequest"
_s295 = "XmlAttributesOnPayloadRequest"
_s296 = "XmlAttributesPayloadResponse"
_s297 = "XmlAttributesOnPayloadResponse"
_s298 = "XmlAttributesRequest"
_s299 = "XmlAttributesResponse"
_s300 = "XmlBlobsRequest"
_s301 = "XmlBlobsResponse"
_s302 = "XmlEmptyBlobsRequest"
_s303 = "XmlEmptyBlobsResponse"
_s304 = "NestedStringList"
_s305 = "XmlEmptyListsRequest"
_s306 = "stringList"
_s307 = "stringSet"
_s308 = "integerList"
_s309 = "booleanList"
_s310 = "timestampList"
_s311 = "enumList"
_s312 = "intEnumList"
_s313 = "nestedStringList"
_s314 = "renamedListMembers"
_s315 = "renamed"
_s316 = "flattenedList"
_s317 = "flattenedList2"
_s318 = "customName"
_s319 = "flattenedListWithMemberNamespace"
_s320 = "flattenedListWithNamespace"
_s321 = "structureList"
_s322 = "myStructureList"
_s323 = "flattenedStructureList"
_s324 = "XmlEmptyListsResponse"
_s325 = "GreetingStruct"
_s326 = "hi"
_s327 = "XmlMapsInputOutputMap"
_s328 = "XmlEmptyMapsRequest"
_s329 = "XmlEmptyMapsResponse"
_s330 = "XmlEmptyStringsRequest"
_s331 = "XmlEmptyStringsResponse"
_s332 = "FooEnumSet"
_s333 = "XmlEnumsRequest"
_s334 = "fooEnum1"
_s335 = "fooEnum2"
_s336 = "fooEnum3"
_s337 = "fooEnumList"
_s338 = "fooEnumSet"
_s339 = "fooEnumMap"
_s340 = "XmlEnumsResponse"
_s341 = "IntegerEnumSet"
_s342 = "IntegerEnumMap"
_s343 = "XmlIntEnumsRequest"
_s344 = "intEnum1"
_s345 = "intEnum2"
_s346 = "intEnum3"
_s347 = "intEnumSet"
_s348 = "intEnumMap"
_s349 = "XmlIntEnumsResponse"
_s350 = "XmlListsRequest"
_s351 = "XmlListsResponse"
_s352 = "XmlMapWithXmlNamespaceInputOutputMap"
_s353 = "XmlMapWithXmlNamespaceRequest"
_s354 = "XmlMapWithXmlNamespaceResponse"
_s355 = "XmlMapsRequest"
_s356 = "XmlMapsResponse"
_s357 = "XmlMapsXmlNameInputOutputMap"
_s358 = "Attribute"
_s359 = "Setting"
_s360 = "XmlMapsXmlNameRequest"
_s361 = "XmlMapsXmlNameResponse"
_s362 = "XmlNamespacedList"
_s363 = "XmlNamespaceNested"
_s364 = "values"
_s365 = "XmlNamespacesRequest"
_s366 = "XmlNamespacesResponse"
_s367 = "XmlNestedUnionStruct"
_s368 = "booleanValue"
_s369 = "XmlTimestampsRequest"
_s370 = "normal"
_s371 = "dateTime"
_s372 = "dateTimeOnTarget"
_s373 = "epochSeconds"
_s374 = "epochSecondsOnTarget"
_s375 = "httpDate"
_s376 = "httpDateOnTarget"
_s377 = "XmlTimestampsResponse"
_s378 = "XmlUnionsRequest"
_s379 = "unionValue"
_s380 = "XmlUnionsResponse"
_s381 = "RecursiveShapesInputOutputNested1"
_s382 = "RecursiveShapesInputOutputNested2"
_s383 = "recursiveMember"
_s384 = "XmlUnionShape"
_s385 = "structValue"

QUERY_IDEMPOTENCY_TOKEN_AUTO_FILL_INPUT: StaticSchema = (
    18,
    n1,
    _s250,
    {_s30: None},
    (_s251,),
    ((3, {_s32: _s251, _s252: None}),),
)

STRING_LIST_MAP: StaticSchema = (
    17,
    n0,
    _s253,
    0,
    (
        _s27,
        _s28,
    ),
    (
        (3, 0),
        (lambda: schemas.STRING_LIST, 0),
    ),
)

QUERY_PARAMS_AS_STRING_LIST_MAP_INPUT: StaticSchema = (
    18,
    n1,
    _s254,
    {_s30: None},
    (
        _s255,
        _s133,
    ),
    (
        (3, {_s32: _s256}),
        (STRING_LIST_MAP, 1024),
    ),
)

QUERY_PRECEDENCE_INPUT: StaticSchema = (
    18,
    n1,
    _s257,
    {_s30: None},
    (
        _s133,
        _s83,
    ),
    (
        (3, {_s32: _s258}),
        (lambda: schemas.STRING_MAP, 1024),
    ),
)

RECURSIVE_SHAPES_REQUEST: StaticSchema = (
    18,
    n1,
    _s259,
    {_s30: None},
    (_s71,),
    ((lambda: RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED1, 0),),
)

RECURSIVE_SHAPES_RESPONSE: StaticSchema = (
    18,
    n1,
    _s260,
    {_s70: None},
    (_s71,),
    ((lambda: RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED1, 0),),
)

RENAMED_LIST_MEMBERS: StaticSchema = (
    16,
    n1,
    _s261,
    0,
    (_s1,),
    ((3, {_s65: _s262}),),
)

SIMPLE_SCALAR_PROPERTIES_REQUEST: StaticSchema = (
    18,
    n1,
    _s263,
    {_s30: None},
    (
        _s133,
        _s264,
        _s265,
        _s266,
        _s267,
        _s268,
        _s269,
        _s270,
        _s271,
        _s272,
    ),
    (
        (3, {_s78: _s134}),
        (3, 0),
        (2, 0),
        (2, 0),
        (5, 0),
        (6, 0),
        (7, 0),
        (8, 0),
        (9, 0),
        (10, {_s65: _s273}),
    ),
)

SIMPLE_SCALAR_PROPERTIES_RESPONSE: StaticSchema = (
    18,
    n1,
    _s274,
    {_s70: None},
    (
        _s133,
        _s264,
        _s265,
        _s266,
        _s267,
        _s268,
        _s269,
        _s270,
        _s271,
        _s272,
    ),
    (
        (3, {_s78: _s134}),
        (3, 0),
        (2, 0),
        (2, 0),
        (5, 0),
        (6, 0),
        (7, 0),
        (8, 0),
        (9, 0),
        (10, {_s65: _s273}),
    ),
)

STRING_PAYLOAD_INPUT: StaticSchema = (
    18,
    n1,
    _s275,
    {_s30: None, _s70: None},
    (_s102,),
    ((3, 16),),
)

STRUCTURE_LIST_MEMBER: StaticSchema = (
    18,
    n1,
    _s276,
    0,
    (
        _s235,
        _s237,
    ),
    (
        (3, {_s65: _s28}),
        (3, {_s65: _s277}),
    ),
)

STRUCTURE_LIST: StaticSchema = (
    16,
    n1,
    _s278,
    0,
    (_s1,),
    ((STRUCTURE_LIST_MEMBER, {_s65: _s262}),),
)

TIMESTAMP_FORMAT_HEADERS_IO: StaticSchema = (
    18,
    n1,
    _s279,
    {_s30: None, _s70: None},
    (
        _s165,
        _s167,
        _s168,
        _s169,
        _s170,
        _s171,
        _s172,
    ),
    (
        (4, {_s78: _s280, _s90: _s161}),
        (4, {_s78: _s281, _s90: _s163}),
        (4, {_s78: _s282, _s90: _s91}),
        (4, {_s78: _s283}),
        (lambda: schemas.EPOCH_SECONDS, {_s78: _s284}),
        (lambda: schemas.HTTP_DATE, {_s78: _s285}),
        (lambda: schemas.DATE_TIME, {_s78: _s286}),
    ),
)

XML_ATTRIBUTES_IN_MIDDLE_PAYLOAD_REQUEST: StaticSchema = (
    18,
    n1,
    _s287,
    0,
    (
        _s133,
        _s288,
        _s83,
    ),
    (
        (3, 0),
        (3, {_s289: None, _s65: _s290}),
        (3, 0),
    ),
)

XML_ATTRIBUTES_IN_MIDDLE_PAYLOAD_RESPONSE: StaticSchema = (
    18,
    n1,
    _s291,
    0,
    (
        _s133,
        _s288,
        _s83,
    ),
    (
        (3, 0),
        (3, {_s289: None, _s65: _s290}),
        (3, 0),
    ),
)

XML_ATTRIBUTES_IN_MIDDLE_REQUEST: StaticSchema = (
    18,
    n1,
    _s292,
    {_s30: None},
    (_s102,),
    ((XML_ATTRIBUTES_IN_MIDDLE_PAYLOAD_REQUEST, 16),),
)

XML_ATTRIBUTES_IN_MIDDLE_RESPONSE: StaticSchema = (
    18,
    n1,
    _s293,
    {_s70: None},
    (_s102,),
    ((XML_ATTRIBUTES_IN_MIDDLE_PAYLOAD_RESPONSE, 16),),
)

XML_ATTRIBUTES_PAYLOAD_REQUEST: StaticSchema = (
    18,
    n1,
    _s294,
    0,
    (
        _s133,
        _s288,
    ),
    (
        (3, 0),
        (3, {_s289: None, _s65: _s290}),
    ),
)

XML_ATTRIBUTES_ON_PAYLOAD_REQUEST: StaticSchema = (
    18,
    n1,
    _s295,
    {_s30: None},
    (_s102,),
    ((XML_ATTRIBUTES_PAYLOAD_REQUEST, 16),),
)

XML_ATTRIBUTES_ON_PAYLOAD_RESPONSE: StaticSchema = (
    18,
    n1,
    _s297,
    {_s70: None},
    (_s102,),
    ((lambda: XML_ATTRIBUTES_PAYLOAD_RESPONSE, 16),),
)

XML_ATTRIBUTES_PAYLOAD_RESPONSE: StaticSchema = (
    18,
    n1,
    _s296,
    0,
    (
        _s133,
        _s288,
    ),
    (
        (3, 0),
        (3, {_s289: None, _s65: _s290}),
    ),
)

XML_ATTRIBUTES_REQUEST: StaticSchema = (
    18,
    n1,
    _s298,
    {_s30: None},
    (
        _s133,
        _s288,
    ),
    (
        (3, 0),
        (3, {_s289: None, _s65: _s290}),
    ),
)

XML_ATTRIBUTES_RESPONSE: StaticSchema = (
    18,
    n1,
    _s299,
    {_s70: None},
    (
        _s133,
        _s288,
    ),
    (
        (3, 0),
        (3, {_s289: None, _s65: _s290}),
    ),
)

XML_BLOBS_REQUEST: StaticSchema = (
    18,
    n1,
    _s300,
    {_s30: None},
    (_s249,),
    ((1, 0),),
)

XML_BLOBS_RESPONSE: StaticSchema = (
    18,
    n1,
    _s301,
    {_s70: None},
    (_s249,),
    ((1, 0),),
)

XML_EMPTY_BLOBS_REQUEST: StaticSchema = (
    18,
    n1,
    _s302,
    {_s30: None},
    (_s249,),
    ((1, 0),),
)

XML_EMPTY_BLOBS_RESPONSE: StaticSchema = (
    18,
    n1,
    _s303,
    {_s70: None},
    (_s249,),
    ((1, 0),),
)

NESTED_STRING_LIST: StaticSchema = (
    16,
    n0,
    _s304,
    0,
    (_s1,),
    ((lambda: schemas.STRING_LIST, 0),),
)

XML_EMPTY_LISTS_REQUEST: StaticSchema = (
    18,
    n1,
    _s305,
    {_s30: None},
    (
        _s306,
        _s307,
        _s308,
        _s309,
        _s310,
        _s311,
        _s312,
        _s313,
        _s314,
        _s316,
        _s317,
        _s319,
        _s320,
        _s321,
        _s323,
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
        (RENAMED_LIST_MEMBERS, {_s65: _s315}),
        (RENAMED_LIST_MEMBERS, {_s106: None}),
        (RENAMED_LIST_MEMBERS, {_s106: None, _s65: _s318}),
        (lambda: schemas.LIST_WITH_MEMBER_NAMESPACE, {_s106: None}),
        (lambda: schemas.LIST_WITH_NAMESPACE, {_s106: None}),
        (STRUCTURE_LIST, {_s65: _s322}),
        (STRUCTURE_LIST, {_s106: None}),
    ),
)

XML_EMPTY_LISTS_RESPONSE: StaticSchema = (
    18,
    n1,
    _s324,
    {_s70: None},
    (
        _s306,
        _s307,
        _s308,
        _s309,
        _s310,
        _s311,
        _s312,
        _s313,
        _s314,
        _s316,
        _s317,
        _s319,
        _s320,
        _s321,
        _s323,
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
        (RENAMED_LIST_MEMBERS, {_s65: _s315}),
        (RENAMED_LIST_MEMBERS, {_s106: None}),
        (RENAMED_LIST_MEMBERS, {_s106: None, _s65: _s318}),
        (lambda: schemas.LIST_WITH_MEMBER_NAMESPACE, {_s106: None}),
        (lambda: schemas.LIST_WITH_NAMESPACE, {_s106: None}),
        (STRUCTURE_LIST, {_s65: _s322}),
        (STRUCTURE_LIST, {_s106: None}),
    ),
)

GREETING_STRUCT: StaticSchema = (
    18,
    n0,
    _s325,
    0,
    (_s326,),
    ((3, 0),),
)

XML_MAPS_INPUT_OUTPUT_MAP: StaticSchema = (
    17,
    n1,
    _s327,
    0,
    (
        _s27,
        _s28,
    ),
    (
        (3, 0),
        (GREETING_STRUCT, 0),
    ),
)

XML_EMPTY_MAPS_REQUEST: StaticSchema = (
    18,
    n1,
    _s328,
    {_s30: None},
    (_s105,),
    ((XML_MAPS_INPUT_OUTPUT_MAP, 0),),
)

XML_EMPTY_MAPS_RESPONSE: StaticSchema = (
    18,
    n1,
    _s329,
    {_s70: None},
    (_s105,),
    ((XML_MAPS_INPUT_OUTPUT_MAP, 0),),
)

XML_EMPTY_STRINGS_REQUEST: StaticSchema = (
    18,
    n1,
    _s330,
    {_s30: None},
    (_s244,),
    ((3, 0),),
)

XML_EMPTY_STRINGS_RESPONSE: StaticSchema = (
    18,
    n1,
    _s331,
    {_s70: None},
    (_s244,),
    ((3, 0),),
)

FOO_ENUM_SET: StaticSchema = (
    16,
    n0,
    _s332,
    0,
    (_s1,),
    ((lambda: schemas.FOO_ENUM, 0),),
)

XML_ENUMS_REQUEST: StaticSchema = (
    18,
    n1,
    _s333,
    {_s30: None},
    (
        _s334,
        _s335,
        _s336,
        _s337,
        _s338,
        _s339,
    ),
    (
        (lambda: schemas.FOO_ENUM, 0),
        (lambda: schemas.FOO_ENUM, 0),
        (lambda: schemas.FOO_ENUM, 0),
        (lambda: schemas.FOO_ENUM_LIST, 0),
        (FOO_ENUM_SET, 0),
        (lambda: schemas.FOO_ENUM_MAP, 0),
    ),
)

XML_ENUMS_RESPONSE: StaticSchema = (
    18,
    n1,
    _s340,
    {_s70: None},
    (
        _s334,
        _s335,
        _s336,
        _s337,
        _s338,
        _s339,
    ),
    (
        (lambda: schemas.FOO_ENUM, 0),
        (lambda: schemas.FOO_ENUM, 0),
        (lambda: schemas.FOO_ENUM, 0),
        (lambda: schemas.FOO_ENUM_LIST, 0),
        (FOO_ENUM_SET, 0),
        (lambda: schemas.FOO_ENUM_MAP, 0),
    ),
)

INTEGER_ENUM_SET: StaticSchema = (
    16,
    n0,
    _s341,
    0,
    (_s1,),
    ((lambda: schemas.INTEGER_ENUM, 0),),
)

INTEGER_ENUM_MAP: StaticSchema = (
    17,
    n0,
    _s342,
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

XML_INT_ENUMS_REQUEST: StaticSchema = (
    18,
    n1,
    _s343,
    {_s30: None},
    (
        _s344,
        _s345,
        _s346,
        _s312,
        _s347,
        _s348,
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

XML_INT_ENUMS_RESPONSE: StaticSchema = (
    18,
    n1,
    _s349,
    {_s70: None},
    (
        _s344,
        _s345,
        _s346,
        _s312,
        _s347,
        _s348,
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

XML_LISTS_REQUEST: StaticSchema = (
    18,
    n1,
    _s350,
    {_s30: None},
    (
        _s306,
        _s307,
        _s308,
        _s309,
        _s310,
        _s311,
        _s312,
        _s313,
        _s314,
        _s316,
        _s317,
        _s319,
        _s320,
        _s321,
        _s323,
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
        (RENAMED_LIST_MEMBERS, {_s65: _s315}),
        (RENAMED_LIST_MEMBERS, {_s106: None}),
        (RENAMED_LIST_MEMBERS, {_s106: None, _s65: _s318}),
        (lambda: schemas.LIST_WITH_MEMBER_NAMESPACE, {_s106: None}),
        (lambda: schemas.LIST_WITH_NAMESPACE, {_s106: None}),
        (STRUCTURE_LIST, {_s65: _s322}),
        (STRUCTURE_LIST, {_s106: None}),
    ),
)

XML_LISTS_RESPONSE: StaticSchema = (
    18,
    n1,
    _s351,
    {_s70: None},
    (
        _s306,
        _s307,
        _s308,
        _s309,
        _s310,
        _s311,
        _s312,
        _s313,
        _s314,
        _s316,
        _s317,
        _s319,
        _s320,
        _s321,
        _s323,
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
        (RENAMED_LIST_MEMBERS, {_s65: _s315}),
        (RENAMED_LIST_MEMBERS, {_s106: None}),
        (RENAMED_LIST_MEMBERS, {_s106: None, _s65: _s318}),
        (lambda: schemas.LIST_WITH_MEMBER_NAMESPACE, {_s106: None}),
        (lambda: schemas.LIST_WITH_NAMESPACE, {_s106: None}),
        (STRUCTURE_LIST, {_s65: _s322}),
        (STRUCTURE_LIST, {_s106: None}),
    ),
)

XML_MAP_WITH_XML_NAMESPACE_INPUT_OUTPUT_MAP: StaticSchema = (
    17,
    n1,
    _s352,
    0,
    (
        _s27,
        _s28,
    ),
    (
        (
            3,
            {
                _s65: _s109,
                _s114: MappingProxyType({"uri": "https://the-key.example.com"}),
            },
        ),
        (
            3,
            {
                _s65: _s99,
                _s114: MappingProxyType({"uri": "https://the-value.example.com"}),
            },
        ),
    ),
)

XML_MAP_WITH_XML_NAMESPACE_REQUEST: StaticSchema = (
    18,
    n1,
    _s353,
    {_s30: None},
    (_s105,),
    (
        (
            XML_MAP_WITH_XML_NAMESPACE_INPUT_OUTPUT_MAP,
            {
                _s65: _s111,
                _s114: MappingProxyType({"uri": "https://the-member.example.com"}),
            },
        ),
    ),
)

XML_MAP_WITH_XML_NAMESPACE_RESPONSE: StaticSchema = (
    18,
    n1,
    _s354,
    {_s70: None},
    (_s105,),
    (
        (
            XML_MAP_WITH_XML_NAMESPACE_INPUT_OUTPUT_MAP,
            {
                _s65: _s111,
                _s114: MappingProxyType({"uri": "https://the-member.example.com"}),
            },
        ),
    ),
)

XML_MAPS_REQUEST: StaticSchema = (
    18,
    n1,
    _s355,
    {_s30: None},
    (_s105,),
    ((XML_MAPS_INPUT_OUTPUT_MAP, 0),),
)

XML_MAPS_RESPONSE: StaticSchema = (
    18,
    n1,
    _s356,
    {_s70: None},
    (_s105,),
    ((XML_MAPS_INPUT_OUTPUT_MAP, 0),),
)

XML_MAPS_XML_NAME_INPUT_OUTPUT_MAP: StaticSchema = (
    17,
    n1,
    _s357,
    0,
    (
        _s27,
        _s28,
    ),
    (
        (3, {_s65: _s358}),
        (GREETING_STRUCT, {_s65: _s359}),
    ),
)

XML_MAPS_XML_NAME_REQUEST: StaticSchema = (
    18,
    n1,
    _s360,
    {_s30: None},
    (_s105,),
    ((XML_MAPS_XML_NAME_INPUT_OUTPUT_MAP, 0),),
)

XML_MAPS_XML_NAME_RESPONSE: StaticSchema = (
    18,
    n1,
    _s361,
    {_s70: None},
    (_s105,),
    ((XML_MAPS_XML_NAME_INPUT_OUTPUT_MAP, 0),),
)

XML_NAMESPACED_LIST: StaticSchema = (
    16,
    n1,
    _s362,
    0,
    (_s1,),
    ((3, {_s114: MappingProxyType({"uri": "http://bux.com"})}),),
)

XML_NAMESPACE_NESTED: StaticSchema = (
    18,
    n1,
    _s363,
    {_s114: MappingProxyType({"uri": "http://foo.com"})},
    (
        _s133,
        _s364,
    ),
    (
        (3, {_s114: MappingProxyType({"uri": "http://baz.com", "prefix": "baz"})}),
        (XML_NAMESPACED_LIST, {_s114: MappingProxyType({"uri": "http://qux.com"})}),
    ),
)

XML_NAMESPACES_REQUEST: StaticSchema = (
    18,
    n1,
    _s365,
    {_s114: MappingProxyType({"uri": "http://foo.com"}), _s30: None},
    (_s71,),
    ((XML_NAMESPACE_NESTED, 0),),
)

XML_NAMESPACES_RESPONSE: StaticSchema = (
    18,
    n1,
    _s366,
    {_s114: MappingProxyType({"uri": "http://foo.com"}), _s70: None},
    (_s71,),
    ((XML_NAMESPACE_NESTED, 0),),
)

XML_NESTED_UNION_STRUCT: StaticSchema = (
    18,
    n1,
    _s367,
    0,
    (
        _s264,
        _s368,
        _s267,
        _s268,
        _s269,
        _s270,
        _s271,
        _s272,
    ),
    (
        (3, 0),
        (2, 0),
        (5, 0),
        (6, 0),
        (7, 0),
        (8, 0),
        (9, 0),
        (10, 0),
    ),
)

XML_TIMESTAMPS_REQUEST: StaticSchema = (
    18,
    n1,
    _s369,
    {_s30: None},
    (
        _s370,
        _s371,
        _s372,
        _s373,
        _s374,
        _s375,
        _s376,
    ),
    (
        (4, 0),
        (4, {_s90: _s91}),
        (lambda: schemas.DATE_TIME, 0),
        (4, {_s90: _s161}),
        (lambda: schemas.EPOCH_SECONDS, 0),
        (4, {_s90: _s163}),
        (lambda: schemas.HTTP_DATE, 0),
    ),
)

XML_TIMESTAMPS_RESPONSE: StaticSchema = (
    18,
    n1,
    _s377,
    {_s70: None},
    (
        _s370,
        _s371,
        _s372,
        _s373,
        _s374,
        _s375,
        _s376,
    ),
    (
        (4, 0),
        (4, {_s90: _s91}),
        (lambda: schemas.DATE_TIME, 0),
        (4, {_s90: _s161}),
        (lambda: schemas.EPOCH_SECONDS, 0),
        (4, {_s90: _s163}),
        (lambda: schemas.HTTP_DATE, 0),
    ),
)

XML_UNIONS_REQUEST: StaticSchema = (
    18,
    n1,
    _s378,
    {_s30: None},
    (_s379,),
    ((lambda: XML_UNION_SHAPE, 0),),
)

XML_UNIONS_RESPONSE: StaticSchema = (
    18,
    n1,
    _s380,
    {_s70: None},
    (_s379,),
    ((lambda: XML_UNION_SHAPE, 0),),
)

RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED1: StaticSchema = (
    18,
    n1,
    _s381,
    0,
    (
        _s133,
        _s71,
    ),
    (
        (3, 0),
        (lambda: RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED2, 0),
    ),
)

RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED2: StaticSchema = (
    18,
    n1,
    _s382,
    0,
    (
        _s258,
        _s383,
    ),
    (
        (3, 0),
        (RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED1, 0),
    ),
)

XML_UNION_SHAPE: StaticSchema = (
    19,
    n1,
    _s384,
    0,
    (
        _s264,
        _s368,
        _s267,
        _s268,
        _s269,
        _s270,
        _s271,
        _s272,
        _s379,
        _s385,
    ),
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
        (XML_NESTED_UNION_STRUCT, 0),
    ),
)
