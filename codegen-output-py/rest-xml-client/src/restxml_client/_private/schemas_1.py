from types import MappingProxyType

from smithy_core._schema_compact import StaticOperationSchema, StaticSchema

from . import schemas

n0 = "aws.protocoltests.shared"
_s1 = "member"
_s10 = "smithy.api#enumValue"
_s27 = "key"
_s28 = "value"
n1 = "aws.protocoltests.restxml"
_s30 = "smithy.synthetic#originalShapeId"
_s32 = "smithy.api#input"
_s34 = "smithy.api#httpQuery"
_s72 = "smithy.api#httpHeader"
_s78 = "baz"
_s87 = "smithy.api#output"
_s99 = "smithy.api#xmlName"
_s100 = "K"
_s101 = "V"
_s103 = "smithy.api#xmlNamespace"
_s106 = "myMap"
_s107 = "smithy.api#xmlFlattened"
_s108 = "KVP"
_s114 = "greeting"
_s119 = "smithy.api#httpPrefixHeaders"
_s130 = "foo"
_s139 = "smithy.api#required"
_s166 = "name"
_s180 = "PayloadWithXmlName"
_s181 = "Hello"
_s198 = "QueryPrecedenceInput"
_s199 = "aws.protocoltests.restxml#QueryPrecedenceInput"
_s200 = "bar"
_s201 = "RenamedListMembers"
_s202 = "item"
_s203 = "StringEnum"
_s204 = "enumvalue"
_s205 = "StructureListMember"
_s206 = "a"
_s207 = "b"
_s208 = "other"
_s209 = "StructureList"
_s210 = "UnionPayload"
_s211 = "XmlAttributesInMiddlePayloadRequest"
_s212 = "attr"
_s213 = "smithy.api#xmlAttribute"
_s214 = "test"
_s215 = "XmlAttributesInMiddlePayloadResponse"
_s216 = "XmlAttributesPayloadRequest"
_s217 = "XmlAttributesPayloadResponse"
_s218 = "XmlMapWithXmlNamespaceInputOutputMap"
_s219 = "GreetingStruct"
_s220 = "hi"
_s221 = "XmlMapsInputOutputMap"
_s222 = "XmlMapsXmlNameInputOutputMap"
_s223 = "Attribute"
_s224 = "Setting"
_s225 = "XmlNamespacedList"
_s226 = "XmlNamespaceNested"
_s227 = "values"
_s228 = "XmlNestedUnionStruct"
_s229 = "stringValue"
_s230 = "booleanValue"
_s231 = "byteValue"
_s232 = "shortValue"
_s233 = "integerValue"
_s234 = "longValue"
_s235 = "floatValue"
_s236 = "doubleValue"
_s237 = "FooEnumSet"
_s238 = "IntegerEnumMap"
_s239 = "IntegerEnumSet"
_s240 = "NestedStringList"
_s241 = "TextPlainBlob"
_s242 = "smithy.api#mediaType"
_s243 = "text/plain"
_s245 = "smithy.api#Unit"
_s246 = "BodyWithXmlNameInput"
_s247 = "Ahoy"
_s248 = "aws.protocoltests.restxml#BodyWithXmlNameInputOutput"
_s249 = "nested"
_s250 = "BodyWithXmlNameOutput"
_s254 = "EndpointOperationInput"
_s255 = "EndpointOperationOutput"
_s256 = "EndpointWithHostLabelHeaderOperationInput"
_s257 = "aws.protocoltests.restxml#HostLabelHeaderInput"
_s258 = "accountId"
_s259 = "X-Amz-Account-Id"
_s260 = "smithy.api#hostLabel"
_s261 = "EndpointWithHostLabelHeaderOperationOutput"
_s262 = "EndpointWithHostLabelOperationInput"
_s263 = "aws.protocoltests.restxml#EndpointWithHostLabelOperationRequest"
_s264 = "label"
_s265 = "EndpointWithHostLabelOperationOutput"
_s266 = "FlattenedXmlMapInput"
_s267 = "aws.protocoltests.restxml#FlattenedXmlMapRequest"
_s268 = "FlattenedXmlMapOutput"
_s269 = "aws.protocoltests.restxml#FlattenedXmlMapResponse"
_s270 = "FlattenedXmlMapWithXmlNameInput"
_s271 = "aws.protocoltests.restxml#FlattenedXmlMapWithXmlNameRequest"
_s272 = "FlattenedXmlMapWithXmlNameOutput"
_s273 = "aws.protocoltests.restxml#FlattenedXmlMapWithXmlNameResponse"
_s277 = "HttpEnumPayloadInput"
_s278 = "aws.protocoltests.restxml#EnumPayloadInput"
_s279 = "payload"
_s280 = "HttpEnumPayloadOutput"
_s281 = "HttpPayloadTraitsInput"
_s282 = "aws.protocoltests.restxml#HttpPayloadTraitsInputOutput"
_s283 = "X-Foo"
_s284 = "blob"
_s285 = "HttpPayloadTraitsOutput"
_s286 = "HttpPayloadTraitsWithMediaTypeInput"
_s287 = "aws.protocoltests.restxml#HttpPayloadTraitsWithMediaTypeInputOutput"
_s288 = "HttpPayloadTraitsWithMediaTypeOutput"
_s289 = "HttpPayloadWithMemberXmlNameInput"
_s290 = "aws.protocoltests.restxml#HttpPayloadWithMemberXmlNameInputOutput"
_s291 = "Hola"
_s292 = "smithy.api#httpPayload"
_s293 = "HttpPayloadWithMemberXmlNameOutput"
_s294 = "HttpPayloadWithStructureInput"
_s295 = "aws.protocoltests.restxml#HttpPayloadWithStructureInputOutput"
_s296 = "HttpPayloadWithStructureOutput"
_s297 = "HttpPayloadWithUnionInput"
_s298 = "aws.protocoltests.restxml#HttpPayloadWithUnionInputOutput"
_s299 = "HttpPayloadWithUnionOutput"
_s300 = "HttpPayloadWithXmlNameInput"
_s301 = "aws.protocoltests.restxml#HttpPayloadWithXmlNameInputOutput"
_s302 = "HttpPayloadWithXmlNameOutput"
_s303 = "HttpPayloadWithXmlNamespaceInput"
_s304 = "aws.protocoltests.restxml#HttpPayloadWithXmlNamespaceInputOutput"
_s305 = "HttpPayloadWithXmlNamespaceOutput"
_s306 = "HttpPayloadWithXmlNamespaceAndPrefixInput"
_s307 = "aws.protocoltests.restxml#HttpPayloadWithXmlNamespaceAndPrefixInputOutput"
_s308 = "HttpPayloadWithXmlNamespaceAndPrefixOutput"
_s309 = "HttpPrefixHeadersInput"
_s310 = "aws.protocoltests.restxml#HttpPrefixHeadersInputOutput"
_s311 = "x-foo"
_s312 = "fooMap"
_s313 = "x-foo-"
_s314 = "HttpPrefixHeadersOutput"
_s320 = "HttpStringPayloadInput"
_s321 = "aws.protocoltests.restxml#StringPayloadInput"
_s322 = "HttpStringPayloadOutput"
_s324 = "InputAndOutputWithHeadersInput"
_s325 = "aws.protocoltests.restxml#InputAndOutputWithHeadersIO"
_s326 = "headerString"
_s327 = "X-String"
_s328 = "headerByte"
_s329 = "X-Byte"
_s330 = "headerShort"
_s331 = "X-Short"
_s332 = "headerInteger"
_s333 = "X-Integer"
_s334 = "headerLong"
_s335 = "X-Long"
_s336 = "headerFloat"
_s337 = "X-Float"
_s338 = "headerDouble"
_s339 = "X-Double"
_s340 = "headerTrueBool"
_s341 = "X-Boolean1"
_s342 = "headerFalseBool"
_s343 = "X-Boolean2"
_s344 = "headerStringList"
_s345 = "X-StringList"
_s346 = "headerStringSet"
_s347 = "X-StringSet"
_s348 = "headerIntegerList"
_s349 = "X-IntegerList"
_s350 = "headerBooleanList"
_s351 = "X-BooleanList"
_s352 = "headerTimestampList"
_s353 = "X-TimestampList"
_s354 = "headerEnum"
_s355 = "X-Enum"
_s356 = "headerEnumList"
_s357 = "X-EnumList"
_s358 = "InputAndOutputWithHeadersOutput"
_s359 = "NestedXmlMapWithXmlNameInput"
_s360 = "aws.protocoltests.restxml#NestedXmlMapWithXmlNameRequest"
_s361 = "nestedXmlMapWithXmlNameMap"
_s362 = "NestedXmlMapWithXmlNameOutput"
_s363 = "aws.protocoltests.restxml#NestedXmlMapWithXmlNameResponse"
_s364 = "NestedXmlMapsInput"
_s365 = "aws.protocoltests.restxml#NestedXmlMapsRequest"
_s366 = "nestedMap"
_s367 = "flatNestedMap"
_s368 = "NestedXmlMapsOutput"
_s369 = "aws.protocoltests.restxml#NestedXmlMapsResponse"
_s370 = "NoInputAndNoOutputInput"
_s371 = "NoInputAndNoOutputOutput"
_s373 = "NullAndEmptyHeadersClientInput"
_s374 = "aws.protocoltests.restxml#NullAndEmptyHeadersIO"
_s375 = "X-A"
_s376 = "X-B"
_s377 = "c"
_s378 = "X-C"
_s379 = "NullAndEmptyHeadersClientOutput"
_s386 = "QueryPrecedenceOutput"
_s514 = "smithy.api#http"
_s515 = "BodyWithXmlName"
_s521 = "EndpointOperation"
_s522 = "smithy.api#endpoint"
_s523 = "EndpointWithHostLabelHeaderOperation"
_s524 = "EndpointWithHostLabelOperation"
_s525 = "FlattenedXmlMap"
_s526 = "FlattenedXmlMapWithXmlName"
_s531 = "HttpEnumPayload"
_s532 = "HttpPayloadTraits"
_s533 = "HttpPayloadTraitsWithMediaType"
_s534 = "HttpPayloadWithMemberXmlName"
_s535 = "HttpPayloadWithStructure"
_s536 = "HttpPayloadWithUnion"
_s537 = "HttpPayloadWithXmlName"
_s538 = "HttpPayloadWithXmlNamespace"
_s539 = "HttpPayloadWithXmlNamespaceAndPrefix"
_s540 = "HttpPrefixHeaders"
_s546 = "HttpStringPayload"
_s548 = "InputAndOutputWithHeaders"
_s549 = "NestedXmlMapWithXmlName"
_s550 = "NestedXmlMaps"
_s551 = "NoInputAndNoOutput"
_s553 = "NullAndEmptyHeadersClient"
_s560 = "QueryPrecedence"

PAYLOAD_WITH_XML_NAME: StaticSchema = (
    18,
    n1,
    _s180,
    {_s99: _s181},
    (_s166,),
    ((3, 0),),
)

QUERY_PRECEDENCE_INPUT: StaticSchema = (
    18,
    n1,
    _s198,
    {_s30: _s199, _s32: None},
    (_s130, _s78),
    ((3, {_s34: _s200}), (lambda: schemas.STRING_MAP, 1024)),
)

QUERY_PRECEDENCE_OUTPUT: StaticSchema = (
    18,
    n1,
    _s386,
    {_s30: _s245, _s87: None},
)

QUERY_PRECEDENCE: StaticOperationSchema = (
    23,
    n1,
    _s560,
    {_s514: MappingProxyType({"uri": "/Precedence", "method": "POST"})},
    QUERY_PRECEDENCE_INPUT,
    QUERY_PRECEDENCE_OUTPUT,
    (),
)

RENAMED_LIST_MEMBERS: StaticSchema = (
    16,
    n1,
    _s201,
    0,
    (_s1,),
    ((3, {_s99: _s202}),),
)

STRING_ENUM: StaticSchema = (
    14,
    n1,
    _s203,
    0,
    (_s101,),
    ((-1, {_s10: _s204}),),
)

STRUCTURE_LIST_MEMBER: StaticSchema = (
    18,
    n1,
    _s205,
    0,
    (_s206, _s207),
    ((3, {_s99: _s28}), (3, {_s99: _s208})),
)

STRUCTURE_LIST: StaticSchema = (
    16,
    n1,
    _s209,
    0,
    (_s1,),
    ((STRUCTURE_LIST_MEMBER, {_s99: _s202}),),
)

UNION_PAYLOAD: StaticSchema = (
    19,
    n1,
    _s210,
    0,
    (_s114,),
    ((3, 0),),
)

XML_ATTRIBUTES_IN_MIDDLE_PAYLOAD_REQUEST: StaticSchema = (
    18,
    n1,
    _s211,
    0,
    (_s130, _s212, _s78),
    ((3, 0), (3, {_s213: None, _s99: _s214}), (3, 0)),
)

XML_ATTRIBUTES_IN_MIDDLE_PAYLOAD_RESPONSE: StaticSchema = (
    18,
    n1,
    _s215,
    0,
    (_s130, _s212, _s78),
    ((3, 0), (3, {_s213: None, _s99: _s214}), (3, 0)),
)

XML_ATTRIBUTES_PAYLOAD_REQUEST: StaticSchema = (
    18,
    n1,
    _s216,
    0,
    (_s130, _s212),
    ((3, 0), (3, {_s213: None, _s99: _s214})),
)

XML_ATTRIBUTES_PAYLOAD_RESPONSE: StaticSchema = (
    18,
    n1,
    _s217,
    0,
    (_s130, _s212),
    ((3, 0), (3, {_s213: None, _s99: _s214})),
)

XML_MAP_WITH_XML_NAMESPACE_INPUT_OUTPUT_MAP: StaticSchema = (
    17,
    n1,
    _s218,
    0,
    (_s27, _s28),
    (
        (
            3,
            {
                _s99: _s100,
                _s103: MappingProxyType({"uri": "https://the-key.example.com"}),
            },
        ),
        (
            3,
            {
                _s99: _s101,
                _s103: MappingProxyType({"uri": "https://the-value.example.com"}),
            },
        ),
    ),
)

GREETING_STRUCT: StaticSchema = (
    18,
    n0,
    _s219,
    0,
    (_s220,),
    ((3, 0),),
)

XML_MAPS_INPUT_OUTPUT_MAP: StaticSchema = (
    17,
    n1,
    _s221,
    0,
    (_s27, _s28),
    ((3, 0), (GREETING_STRUCT, 0)),
)

XML_MAPS_XML_NAME_INPUT_OUTPUT_MAP: StaticSchema = (
    17,
    n1,
    _s222,
    0,
    (_s27, _s28),
    ((3, {_s99: _s223}), (GREETING_STRUCT, {_s99: _s224})),
)

XML_NAMESPACED_LIST: StaticSchema = (
    16,
    n1,
    _s225,
    0,
    (_s1,),
    ((3, {_s103: MappingProxyType({"uri": "http://bux.com"})}),),
)

XML_NAMESPACE_NESTED: StaticSchema = (
    18,
    n1,
    _s226,
    {_s103: MappingProxyType({"uri": "http://foo.com"})},
    (_s130, _s227),
    (
        (3, {_s103: MappingProxyType({"uri": "http://baz.com", "prefix": "baz"})}),
        (XML_NAMESPACED_LIST, {_s103: MappingProxyType({"uri": "http://qux.com"})}),
    ),
)

XML_NESTED_UNION_STRUCT: StaticSchema = (
    18,
    n1,
    _s228,
    0,
    (_s229, _s230, _s231, _s232, _s233, _s234, _s235, _s236),
    ((3, 0), (2, 0), (5, 0), (6, 0), (7, 0), (8, 0), (9, 0), (10, 0)),
)

FOO_ENUM_SET: StaticSchema = (
    16,
    n0,
    _s237,
    0,
    (_s1,),
    ((lambda: schemas.FOO_ENUM, 0),),
)

INTEGER_ENUM_MAP: StaticSchema = (
    17,
    n0,
    _s238,
    0,
    (_s27, _s28),
    ((3, 0), (lambda: schemas.INTEGER_ENUM, 0)),
)

INTEGER_ENUM_SET: StaticSchema = (
    16,
    n0,
    _s239,
    0,
    (_s1,),
    ((lambda: schemas.INTEGER_ENUM, 0),),
)

NESTED_STRING_LIST: StaticSchema = (
    16,
    n0,
    _s240,
    0,
    (_s1,),
    ((lambda: schemas.STRING_LIST, 0),),
)

TEXT_PLAIN_BLOB: StaticSchema = (
    1,
    n0,
    _s241,
    {_s242: _s243},
)

BODY_WITH_XML_NAME_INPUT: StaticSchema = (
    18,
    n1,
    _s246,
    {_s99: _s247, _s30: _s248, _s32: None},
    (_s249,),
    ((PAYLOAD_WITH_XML_NAME, 0),),
)

BODY_WITH_XML_NAME_OUTPUT: StaticSchema = (
    18,
    n1,
    _s250,
    {_s99: _s247, _s30: _s248, _s87: None},
    (_s249,),
    ((PAYLOAD_WITH_XML_NAME, 0),),
)

BODY_WITH_XML_NAME: StaticOperationSchema = (
    23,
    n1,
    _s515,
    {_s514: MappingProxyType({"uri": "/BodyWithXmlName", "method": "PUT"})},
    BODY_WITH_XML_NAME_INPUT,
    BODY_WITH_XML_NAME_OUTPUT,
    (),
)

ENDPOINT_OPERATION_INPUT: StaticSchema = (
    18,
    n1,
    _s254,
    {_s30: _s245, _s32: None},
)

ENDPOINT_OPERATION_OUTPUT: StaticSchema = (
    18,
    n1,
    _s255,
    {_s30: _s245, _s87: None},
)

ENDPOINT_OPERATION: StaticOperationSchema = (
    23,
    n1,
    _s521,
    {
        _s522: MappingProxyType({"hostPrefix": "foo."}),
        _s514: MappingProxyType({"uri": "/EndpointOperation", "method": "POST"}),
    },
    ENDPOINT_OPERATION_INPUT,
    ENDPOINT_OPERATION_OUTPUT,
    (),
)

ENDPOINT_WITH_HOST_LABEL_HEADER_OPERATION_INPUT: StaticSchema = (
    18,
    n1,
    _s256,
    {_s30: _s257, _s32: None},
    (_s258,),
    ((3, {_s72: _s259, _s260: None, _s139: None}),),
)

ENDPOINT_WITH_HOST_LABEL_HEADER_OPERATION_OUTPUT: StaticSchema = (
    18,
    n1,
    _s261,
    {_s30: _s245, _s87: None},
)

ENDPOINT_WITH_HOST_LABEL_HEADER_OPERATION: StaticOperationSchema = (
    23,
    n1,
    _s523,
    {
        _s522: MappingProxyType({"hostPrefix": "{accountId}."}),
        _s514: MappingProxyType(
            {"uri": "/EndpointWithHostLabelHeaderOperation", "method": "POST"}
        ),
    },
    ENDPOINT_WITH_HOST_LABEL_HEADER_OPERATION_INPUT,
    ENDPOINT_WITH_HOST_LABEL_HEADER_OPERATION_OUTPUT,
    (),
)

ENDPOINT_WITH_HOST_LABEL_OPERATION_INPUT: StaticSchema = (
    18,
    n1,
    _s262,
    {_s30: _s263, _s32: None},
    (_s264,),
    ((3, 257),),
)

ENDPOINT_WITH_HOST_LABEL_OPERATION_OUTPUT: StaticSchema = (
    18,
    n1,
    _s265,
    {_s30: _s245, _s87: None},
)

ENDPOINT_WITH_HOST_LABEL_OPERATION: StaticOperationSchema = (
    23,
    n1,
    _s524,
    {
        _s522: MappingProxyType({"hostPrefix": "foo.{label}."}),
        _s514: MappingProxyType(
            {"uri": "/EndpointWithHostLabelOperation", "method": "POST"}
        ),
    },
    ENDPOINT_WITH_HOST_LABEL_OPERATION_INPUT,
    ENDPOINT_WITH_HOST_LABEL_OPERATION_OUTPUT,
    (),
)

FLATTENED_XML_MAP_INPUT: StaticSchema = (
    18,
    n1,
    _s266,
    {_s30: _s267, _s32: None},
    (_s106,),
    ((lambda: schemas.FOO_ENUM_MAP, {_s107: None}),),
)

FLATTENED_XML_MAP_OUTPUT: StaticSchema = (
    18,
    n1,
    _s268,
    {_s30: _s269, _s87: None},
    (_s106,),
    ((lambda: schemas.FOO_ENUM_MAP, {_s107: None}),),
)

FLATTENED_XML_MAP: StaticOperationSchema = (
    23,
    n1,
    _s525,
    {_s514: MappingProxyType({"uri": "/FlattenedXmlMap", "method": "POST"})},
    FLATTENED_XML_MAP_INPUT,
    FLATTENED_XML_MAP_OUTPUT,
    (),
)

FLATTENED_XML_MAP_WITH_XML_NAME_INPUT: StaticSchema = (
    18,
    n1,
    _s270,
    {_s30: _s271, _s32: None},
    (_s106,),
    (
        (
            lambda: schemas.FLATTENED_XML_MAP_WITH_XML_NAME_INPUT_OUTPUT_MAP,
            {_s107: None, _s99: _s108},
        ),
    ),
)

FLATTENED_XML_MAP_WITH_XML_NAME_OUTPUT: StaticSchema = (
    18,
    n1,
    _s272,
    {_s30: _s273, _s87: None},
    (_s106,),
    (
        (
            lambda: schemas.FLATTENED_XML_MAP_WITH_XML_NAME_INPUT_OUTPUT_MAP,
            {_s107: None, _s99: _s108},
        ),
    ),
)

FLATTENED_XML_MAP_WITH_XML_NAME: StaticOperationSchema = (
    23,
    n1,
    _s526,
    {_s514: MappingProxyType({"uri": "/FlattenedXmlMapWithXmlName", "method": "POST"})},
    FLATTENED_XML_MAP_WITH_XML_NAME_INPUT,
    FLATTENED_XML_MAP_WITH_XML_NAME_OUTPUT,
    (),
)

HTTP_ENUM_PAYLOAD_INPUT: StaticSchema = (
    18,
    n1,
    _s277,
    {_s30: _s278, _s32: None},
    (_s279,),
    ((STRING_ENUM, 16),),
)

HTTP_ENUM_PAYLOAD_OUTPUT: StaticSchema = (
    18,
    n1,
    _s280,
    {_s30: _s278, _s87: None},
    (_s279,),
    ((STRING_ENUM, 16),),
)

HTTP_ENUM_PAYLOAD: StaticOperationSchema = (
    23,
    n1,
    _s531,
    {_s514: MappingProxyType({"uri": "/EnumPayload", "method": "POST"})},
    HTTP_ENUM_PAYLOAD_INPUT,
    HTTP_ENUM_PAYLOAD_OUTPUT,
    (),
)

HTTP_PAYLOAD_TRAITS_INPUT: StaticSchema = (
    18,
    n1,
    _s281,
    {_s30: _s282, _s32: None},
    (_s130, _s284),
    ((3, {_s72: _s283}), (1, 16)),
)

HTTP_PAYLOAD_TRAITS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s285,
    {_s30: _s282, _s87: None},
    (_s130, _s284),
    ((3, {_s72: _s283}), (1, 16)),
)

HTTP_PAYLOAD_TRAITS: StaticOperationSchema = (
    23,
    n1,
    _s532,
    {_s514: MappingProxyType({"uri": "/HttpPayloadTraits", "method": "POST"})},
    HTTP_PAYLOAD_TRAITS_INPUT,
    HTTP_PAYLOAD_TRAITS_OUTPUT,
    (),
)

HTTP_PAYLOAD_TRAITS_WITH_MEDIA_TYPE_INPUT: StaticSchema = (
    18,
    n1,
    _s286,
    {_s30: _s287, _s32: None},
    (_s130, _s284),
    ((3, {_s72: _s283}), (TEXT_PLAIN_BLOB, 16)),
)

HTTP_PAYLOAD_TRAITS_WITH_MEDIA_TYPE_OUTPUT: StaticSchema = (
    18,
    n1,
    _s288,
    {_s30: _s287, _s87: None},
    (_s130, _s284),
    ((3, {_s72: _s283}), (TEXT_PLAIN_BLOB, 16)),
)

HTTP_PAYLOAD_TRAITS_WITH_MEDIA_TYPE: StaticOperationSchema = (
    23,
    n1,
    _s533,
    {
        _s514: MappingProxyType(
            {"uri": "/HttpPayloadTraitsWithMediaType", "method": "POST"}
        )
    },
    HTTP_PAYLOAD_TRAITS_WITH_MEDIA_TYPE_INPUT,
    HTTP_PAYLOAD_TRAITS_WITH_MEDIA_TYPE_OUTPUT,
    (),
)

HTTP_PAYLOAD_WITH_MEMBER_XML_NAME_INPUT: StaticSchema = (
    18,
    n1,
    _s289,
    {_s30: _s290, _s32: None},
    (_s249,),
    ((PAYLOAD_WITH_XML_NAME, {_s99: _s291, _s292: None}),),
)

HTTP_PAYLOAD_WITH_MEMBER_XML_NAME_OUTPUT: StaticSchema = (
    18,
    n1,
    _s293,
    {_s30: _s290, _s87: None},
    (_s249,),
    ((PAYLOAD_WITH_XML_NAME, {_s99: _s291, _s292: None}),),
)

HTTP_PAYLOAD_WITH_MEMBER_XML_NAME: StaticOperationSchema = (
    23,
    n1,
    _s534,
    {
        _s514: MappingProxyType(
            {"uri": "/HttpPayloadWithMemberXmlName", "method": "PUT"}
        )
    },
    HTTP_PAYLOAD_WITH_MEMBER_XML_NAME_INPUT,
    HTTP_PAYLOAD_WITH_MEMBER_XML_NAME_OUTPUT,
    (),
)

HTTP_PAYLOAD_WITH_STRUCTURE_INPUT: StaticSchema = (
    18,
    n1,
    _s294,
    {_s30: _s295, _s32: None},
    (_s249,),
    ((lambda: schemas.NESTED_PAYLOAD, 16),),
)

HTTP_PAYLOAD_WITH_STRUCTURE_OUTPUT: StaticSchema = (
    18,
    n1,
    _s296,
    {_s30: _s295, _s87: None},
    (_s249,),
    ((lambda: schemas.NESTED_PAYLOAD, 16),),
)

HTTP_PAYLOAD_WITH_STRUCTURE: StaticOperationSchema = (
    23,
    n1,
    _s535,
    {_s514: MappingProxyType({"uri": "/HttpPayloadWithStructure", "method": "PUT"})},
    HTTP_PAYLOAD_WITH_STRUCTURE_INPUT,
    HTTP_PAYLOAD_WITH_STRUCTURE_OUTPUT,
    (),
)

HTTP_PAYLOAD_WITH_UNION_INPUT: StaticSchema = (
    18,
    n1,
    _s297,
    {_s30: _s298, _s32: None},
    (_s249,),
    ((UNION_PAYLOAD, 16),),
)

HTTP_PAYLOAD_WITH_UNION_OUTPUT: StaticSchema = (
    18,
    n1,
    _s299,
    {_s30: _s298, _s87: None},
    (_s249,),
    ((UNION_PAYLOAD, 16),),
)

HTTP_PAYLOAD_WITH_UNION: StaticOperationSchema = (
    23,
    n1,
    _s536,
    {_s514: MappingProxyType({"uri": "/HttpPayloadWithUnion", "method": "PUT"})},
    HTTP_PAYLOAD_WITH_UNION_INPUT,
    HTTP_PAYLOAD_WITH_UNION_OUTPUT,
    (),
)

HTTP_PAYLOAD_WITH_XML_NAME_INPUT: StaticSchema = (
    18,
    n1,
    _s300,
    {_s30: _s301, _s32: None},
    (_s249,),
    ((PAYLOAD_WITH_XML_NAME, 16),),
)

HTTP_PAYLOAD_WITH_XML_NAME_OUTPUT: StaticSchema = (
    18,
    n1,
    _s302,
    {_s30: _s301, _s87: None},
    (_s249,),
    ((PAYLOAD_WITH_XML_NAME, 16),),
)

HTTP_PAYLOAD_WITH_XML_NAME: StaticOperationSchema = (
    23,
    n1,
    _s537,
    {_s514: MappingProxyType({"uri": "/HttpPayloadWithXmlName", "method": "PUT"})},
    HTTP_PAYLOAD_WITH_XML_NAME_INPUT,
    HTTP_PAYLOAD_WITH_XML_NAME_OUTPUT,
    (),
)

HTTP_PAYLOAD_WITH_XML_NAMESPACE_INPUT: StaticSchema = (
    18,
    n1,
    _s303,
    {_s30: _s304, _s32: None},
    (_s249,),
    ((lambda: schemas.PAYLOAD_WITH_XML_NAMESPACE, 16),),
)

HTTP_PAYLOAD_WITH_XML_NAMESPACE_OUTPUT: StaticSchema = (
    18,
    n1,
    _s305,
    {_s30: _s304, _s87: None},
    (_s249,),
    ((lambda: schemas.PAYLOAD_WITH_XML_NAMESPACE, 16),),
)

HTTP_PAYLOAD_WITH_XML_NAMESPACE: StaticOperationSchema = (
    23,
    n1,
    _s538,
    {_s514: MappingProxyType({"uri": "/HttpPayloadWithXmlNamespace", "method": "PUT"})},
    HTTP_PAYLOAD_WITH_XML_NAMESPACE_INPUT,
    HTTP_PAYLOAD_WITH_XML_NAMESPACE_OUTPUT,
    (),
)

HTTP_PAYLOAD_WITH_XML_NAMESPACE_AND_PREFIX_INPUT: StaticSchema = (
    18,
    n1,
    _s306,
    {_s30: _s307, _s32: None},
    (_s249,),
    ((lambda: schemas.PAYLOAD_WITH_XML_NAMESPACE_AND_PREFIX, 16),),
)

HTTP_PAYLOAD_WITH_XML_NAMESPACE_AND_PREFIX_OUTPUT: StaticSchema = (
    18,
    n1,
    _s308,
    {_s30: _s307, _s87: None},
    (_s249,),
    ((lambda: schemas.PAYLOAD_WITH_XML_NAMESPACE_AND_PREFIX, 16),),
)

HTTP_PAYLOAD_WITH_XML_NAMESPACE_AND_PREFIX: StaticOperationSchema = (
    23,
    n1,
    _s539,
    {
        _s514: MappingProxyType(
            {"uri": "/HttpPayloadWithXmlNamespaceAndPrefix", "method": "PUT"}
        )
    },
    HTTP_PAYLOAD_WITH_XML_NAMESPACE_AND_PREFIX_INPUT,
    HTTP_PAYLOAD_WITH_XML_NAMESPACE_AND_PREFIX_OUTPUT,
    (),
)

HTTP_PREFIX_HEADERS_INPUT: StaticSchema = (
    18,
    n1,
    _s309,
    {_s30: _s310, _s32: None},
    (_s130, _s312),
    ((3, {_s72: _s311}), (lambda: schemas.FOO_PREFIX_HEADERS, {_s119: _s313})),
)

HTTP_PREFIX_HEADERS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s314,
    {_s30: _s310, _s87: None},
    (_s130, _s312),
    ((3, {_s72: _s311}), (lambda: schemas.FOO_PREFIX_HEADERS, {_s119: _s313})),
)

HTTP_PREFIX_HEADERS: StaticOperationSchema = (
    23,
    n1,
    _s540,
    {_s514: MappingProxyType({"uri": "/HttpPrefixHeaders", "method": "GET"})},
    HTTP_PREFIX_HEADERS_INPUT,
    HTTP_PREFIX_HEADERS_OUTPUT,
    (),
)

HTTP_STRING_PAYLOAD_INPUT: StaticSchema = (
    18,
    n1,
    _s320,
    {_s30: _s321, _s32: None},
    (_s279,),
    ((3, 16),),
)

HTTP_STRING_PAYLOAD_OUTPUT: StaticSchema = (
    18,
    n1,
    _s322,
    {_s30: _s321, _s87: None},
    (_s279,),
    ((3, 16),),
)

HTTP_STRING_PAYLOAD: StaticOperationSchema = (
    23,
    n1,
    _s546,
    {_s514: MappingProxyType({"uri": "/StringPayload", "method": "POST"})},
    HTTP_STRING_PAYLOAD_INPUT,
    HTTP_STRING_PAYLOAD_OUTPUT,
    (),
)

INPUT_AND_OUTPUT_WITH_HEADERS_INPUT: StaticSchema = (
    18,
    n1,
    _s324,
    {_s30: _s325, _s32: None},
    (
        _s326,
        _s328,
        _s330,
        _s332,
        _s334,
        _s336,
        _s338,
        _s340,
        _s342,
        _s344,
        _s346,
        _s348,
        _s350,
        _s352,
        _s354,
        _s356,
    ),
    (
        (3, {_s72: _s327}),
        (5, {_s72: _s329}),
        (6, {_s72: _s331}),
        (7, {_s72: _s333}),
        (8, {_s72: _s335}),
        (9, {_s72: _s337}),
        (10, {_s72: _s339}),
        (2, {_s72: _s341}),
        (2, {_s72: _s343}),
        (lambda: schemas.STRING_LIST, {_s72: _s345}),
        (lambda: schemas.STRING_SET, {_s72: _s347}),
        (lambda: schemas.INTEGER_LIST, {_s72: _s349}),
        (lambda: schemas.BOOLEAN_LIST, {_s72: _s351}),
        (lambda: schemas.TIMESTAMP_LIST, {_s72: _s353}),
        (lambda: schemas.FOO_ENUM, {_s72: _s355}),
        (lambda: schemas.FOO_ENUM_LIST, {_s72: _s357}),
    ),
)

INPUT_AND_OUTPUT_WITH_HEADERS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s358,
    {_s30: _s325, _s87: None},
    (
        _s326,
        _s328,
        _s330,
        _s332,
        _s334,
        _s336,
        _s338,
        _s340,
        _s342,
        _s344,
        _s346,
        _s348,
        _s350,
        _s352,
        _s354,
        _s356,
    ),
    (
        (3, {_s72: _s327}),
        (5, {_s72: _s329}),
        (6, {_s72: _s331}),
        (7, {_s72: _s333}),
        (8, {_s72: _s335}),
        (9, {_s72: _s337}),
        (10, {_s72: _s339}),
        (2, {_s72: _s341}),
        (2, {_s72: _s343}),
        (lambda: schemas.STRING_LIST, {_s72: _s345}),
        (lambda: schemas.STRING_SET, {_s72: _s347}),
        (lambda: schemas.INTEGER_LIST, {_s72: _s349}),
        (lambda: schemas.BOOLEAN_LIST, {_s72: _s351}),
        (lambda: schemas.TIMESTAMP_LIST, {_s72: _s353}),
        (lambda: schemas.FOO_ENUM, {_s72: _s355}),
        (lambda: schemas.FOO_ENUM_LIST, {_s72: _s357}),
    ),
)

INPUT_AND_OUTPUT_WITH_HEADERS: StaticOperationSchema = (
    23,
    n1,
    _s548,
    {_s514: MappingProxyType({"uri": "/InputAndOutputWithHeaders", "method": "POST"})},
    INPUT_AND_OUTPUT_WITH_HEADERS_INPUT,
    INPUT_AND_OUTPUT_WITH_HEADERS_OUTPUT,
    (),
)

NESTED_XML_MAP_WITH_XML_NAME_INPUT: StaticSchema = (
    18,
    n1,
    _s359,
    {_s30: _s360, _s32: None},
    (_s361,),
    ((lambda: schemas.NESTED_XML_MAP_WITH_XML_NAME_MAP, 0),),
)

NESTED_XML_MAP_WITH_XML_NAME_OUTPUT: StaticSchema = (
    18,
    n1,
    _s362,
    {_s30: _s363, _s87: None},
    (_s361,),
    ((lambda: schemas.NESTED_XML_MAP_WITH_XML_NAME_MAP, 0),),
)

NESTED_XML_MAP_WITH_XML_NAME: StaticOperationSchema = (
    23,
    n1,
    _s549,
    {_s514: MappingProxyType({"uri": "/NestedXmlMapWithXmlName", "method": "POST"})},
    NESTED_XML_MAP_WITH_XML_NAME_INPUT,
    NESTED_XML_MAP_WITH_XML_NAME_OUTPUT,
    (),
)

NESTED_XML_MAPS_INPUT: StaticSchema = (
    18,
    n1,
    _s364,
    {_s30: _s365, _s32: None},
    (_s366, _s367),
    ((lambda: schemas.NESTED_MAP, 0), (lambda: schemas.NESTED_MAP, {_s107: None})),
)

NESTED_XML_MAPS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s368,
    {_s30: _s369, _s87: None},
    (_s366, _s367),
    ((lambda: schemas.NESTED_MAP, 0), (lambda: schemas.NESTED_MAP, {_s107: None})),
)

NESTED_XML_MAPS: StaticOperationSchema = (
    23,
    n1,
    _s550,
    {_s514: MappingProxyType({"uri": "/NestedXmlMaps", "method": "POST"})},
    NESTED_XML_MAPS_INPUT,
    NESTED_XML_MAPS_OUTPUT,
    (),
)

NO_INPUT_AND_NO_OUTPUT_INPUT: StaticSchema = (
    18,
    n1,
    _s370,
    {_s30: _s245, _s32: None},
)

NO_INPUT_AND_NO_OUTPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s371,
    {_s30: _s245, _s87: None},
)

NO_INPUT_AND_NO_OUTPUT: StaticOperationSchema = (
    23,
    n1,
    _s551,
    {_s514: MappingProxyType({"uri": "/NoInputAndNoOutput", "method": "POST"})},
    NO_INPUT_AND_NO_OUTPUT_INPUT,
    NO_INPUT_AND_NO_OUTPUT_OUTPUT,
    (),
)

NULL_AND_EMPTY_HEADERS_CLIENT_INPUT: StaticSchema = (
    18,
    n1,
    _s373,
    {_s30: _s374, _s32: None},
    (_s206, _s207, _s377),
    (
        (3, {_s72: _s375}),
        (3, {_s72: _s376}),
        (lambda: schemas.STRING_LIST, {_s72: _s378}),
    ),
)

NULL_AND_EMPTY_HEADERS_CLIENT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s379,
    {_s30: _s374, _s87: None},
    (_s206, _s207, _s377),
    (
        (3, {_s72: _s375}),
        (3, {_s72: _s376}),
        (lambda: schemas.STRING_LIST, {_s72: _s378}),
    ),
)

NULL_AND_EMPTY_HEADERS_CLIENT: StaticOperationSchema = (
    23,
    n1,
    _s553,
    {_s514: MappingProxyType({"uri": "/NullAndEmptyHeadersClient", "method": "GET"})},
    NULL_AND_EMPTY_HEADERS_CLIENT_INPUT,
    NULL_AND_EMPTY_HEADERS_CLIENT_OUTPUT,
    (),
)
