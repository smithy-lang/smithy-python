from types import MappingProxyType

from smithy_core._schema_compact import StaticSchema

n0 = "aws.protocoltests.shared"
_s0 = "StringList"
_s1 = "member"
_s2 = "StringSet"
_s3 = "IntegerList"
_s4 = "IntegerSet"
_s5 = "DoubleList"
_s6 = "BooleanList"
_s7 = "TimestampList"
_s8 = "FooEnum"
_s9 = "FOO"
_s10 = "smithy.api#enumValue"
_s11 = "Foo"
_s12 = "BAZ"
_s13 = "Baz"
_s14 = "BAR"
_s15 = "Bar"
_s16 = "ONE"
_s17 = "1"
_s18 = "ZERO"
_s19 = "0"
_s20 = "FooEnumList"
_s21 = "IntegerEnum"
_s22 = "A"
_s23 = "B"
_s24 = "C"
_s25 = "IntegerEnumList"
_s26 = "StringMap"
_s27 = "key"
_s28 = "value"
n1 = "aws.protocoltests.restxml"
_s29 = "AllQueryStringTypesInput"
_s30 = "smithy.api#input"
_s31 = "queryString"
_s32 = "smithy.api#httpQuery"
_s33 = "String"
_s34 = "queryStringList"
_s35 = "queryStringSet"
_s36 = "queryByte"
_s37 = "Byte"
_s38 = "queryShort"
_s39 = "Short"
_s40 = "queryInteger"
_s41 = "Integer"
_s42 = "queryIntegerList"
_s43 = "queryIntegerSet"
_s44 = "queryLong"
_s45 = "Long"
_s46 = "queryFloat"
_s47 = "Float"
_s48 = "queryDouble"
_s49 = "Double"
_s50 = "queryDoubleList"
_s51 = "queryBoolean"
_s52 = "Boolean"
_s53 = "queryBooleanList"
_s54 = "queryTimestamp"
_s55 = "Timestamp"
_s56 = "queryTimestampList"
_s57 = "queryEnum"
_s58 = "Enum"
_s59 = "queryEnumList"
_s60 = "EnumList"
_s61 = "queryIntegerEnum"
_s62 = "queryIntegerEnumList"
_s63 = "queryParamsMapOfStrings"
_s64 = "PayloadWithXmlName"
_s65 = "smithy.api#xmlName"
_s66 = "Hello"
_s67 = "name"
_s68 = "BodyWithXmlNameInputOutput"
_s69 = "Ahoy"
_s70 = "smithy.api#output"
_s71 = "nested"
_s72 = "ComplexNestedErrorData"
_s73 = "ComplexError"
_s74 = "smithy.api#error"
_s75 = "client"
_s76 = "smithy.api#httpError"
_s77 = "Header"
_s78 = "smithy.api#httpHeader"
_s79 = "X-Header"
_s80 = "TopLevel"
_s81 = "Nested"
_s82 = "ConstantAndVariableQueryStringInput"
_s83 = "baz"
_s84 = "maybeSet"
_s85 = "ConstantQueryStringInput"
_s86 = "hello"
_s87 = "ContentTypeParametersInput"
_s88 = "ContentTypeParametersOutput"
_s89 = "DateTime"
_s90 = "smithy.api#timestampFormat"
_s91 = "date-time"
_s92 = "DatetimeOffsetsOutput"
_s93 = "datetime"
_s94 = "EmptyInputAndEmptyOutputInput"
_s95 = "EmptyInputAndEmptyOutputOutput"
_s96 = "EndpointWithHostLabelOperationRequest"
_s97 = "label"
_s98 = "StringEnum"
_s99 = "V"
_s100 = "enumvalue"
_s101 = "EnumPayloadInput"
_s102 = "payload"
_s103 = "FooEnumMap"
_s104 = "FlattenedXmlMapRequest"
_s105 = "myMap"
_s106 = "smithy.api#xmlFlattened"
_s107 = "FlattenedXmlMapResponse"
_s108 = "FlattenedXmlMapWithXmlNameInputOutputMap"
_s109 = "K"
_s110 = "FlattenedXmlMapWithXmlNameRequest"
_s111 = "KVP"
_s112 = "FlattenedXmlMapWithXmlNameResponse"
_s113 = "FlattenedXmlMapWithXmlNamespaceOutputMap"
_s114 = "smithy.api#xmlNamespace"
_s115 = "FlattenedXmlMapWithXmlNamespaceOutput"
_s116 = "FooPrefixHeaders"
_s117 = "FractionalSecondsOutput"
_s118 = "GreetingWithErrorsOutput"
_s119 = "greeting"
_s120 = "X-Greeting"
_s121 = "HostLabelHeaderInput"
_s122 = "accountId"
_s123 = "X-Amz-Account-Id"
_s124 = "smithy.api#hostLabel"
_s125 = "smithy.api#required"
_s126 = "HttpEmptyPrefixHeadersInput"
_s127 = "prefixHeaders"
_s128 = "smithy.api#httpPrefixHeaders"
_s129 = ""
_s130 = "specificHeader"
_s131 = "HttpEmptyPrefixHeadersOutput"
_s132 = "HttpPayloadTraitsInputOutput"
_s133 = "foo"
_s134 = "X-Foo"
_s135 = "blob"
_s136 = "TextPlainBlob"
_s137 = "smithy.api#mediaType"
_s138 = "text/plain"
_s139 = "HttpPayloadTraitsWithMediaTypeInputOutput"
_s140 = "HttpPayloadWithMemberXmlNameInputOutput"
_s141 = "Hola"
_s142 = "smithy.api#httpPayload"
_s143 = "NestedPayload"
_s144 = "HttpPayloadWithStructureInputOutput"
_s145 = "UnionPayload"
_s146 = "HttpPayloadWithUnionInputOutput"
_s147 = "HttpPayloadWithXmlNameInputOutput"
_s148 = "PayloadWithXmlNamespaceAndPrefix"
_s149 = "HttpPayloadWithXmlNamespaceAndPrefixInputOutput"
_s150 = "PayloadWithXmlNamespace"
_s151 = "HttpPayloadWithXmlNamespaceInputOutput"
_s152 = "HttpPrefixHeadersInputOutput"
_s153 = "x-foo"
_s154 = "fooMap"
_s155 = "x-foo-"
_s156 = "HttpRequestWithFloatLabelsInput"
_s157 = "float"
_s158 = "double"
_s159 = "HttpRequestWithGreedyLabelInPathInput"
_s160 = "EpochSeconds"
_s161 = "epoch-seconds"
_s162 = "HttpDate"
_s163 = "http-date"
_s164 = "HttpRequestWithLabelsAndTimestampFormatInput"
_s165 = "memberEpochSeconds"
_s166 = "smithy.api#httpLabel"
_s167 = "memberHttpDate"
_s168 = "memberDateTime"
_s169 = "defaultFormat"
_s170 = "targetEpochSeconds"
_s171 = "targetHttpDate"
_s172 = "targetDateTime"
_s173 = "HttpRequestWithLabelsInput"
_s174 = "string"
_s175 = "short"
_s176 = "integer"
_s177 = "long"
_s178 = "boolean"
_s179 = "timestamp"
_s180 = "HttpResponseCodeOutput"
_s181 = "Status"
_s182 = "IgnoreQueryParamsInResponseOutput"
_s183 = "InputAndOutputWithHeadersIO"
_s184 = "headerString"
_s185 = "X-String"
_s186 = "headerByte"
_s187 = "X-Byte"
_s188 = "headerShort"
_s189 = "X-Short"
_s190 = "headerInteger"
_s191 = "X-Integer"
_s192 = "headerLong"
_s193 = "X-Long"
_s194 = "headerFloat"
_s195 = "X-Float"
_s196 = "headerDouble"
_s197 = "X-Double"
_s198 = "headerTrueBool"
_s199 = "X-Boolean1"
_s200 = "headerFalseBool"
_s201 = "X-Boolean2"
_s202 = "headerStringList"
_s203 = "X-StringList"
_s204 = "headerStringSet"
_s205 = "X-StringSet"
_s206 = "headerIntegerList"
_s207 = "X-IntegerList"
_s208 = "headerBooleanList"
_s209 = "X-BooleanList"
_s210 = "headerTimestampList"
_s211 = "X-TimestampList"
_s212 = "headerEnum"
_s213 = "X-Enum"
_s214 = "headerEnumList"
_s215 = "X-EnumList"
_s216 = "InvalidGreeting"
_s217 = "Message"
_s218 = "ListWithMemberNamespace"
_s219 = "ListWithNamespace"
_s220 = "NestedMap"
_s221 = "NestedXmlMapWithXmlNameInnerMap"
_s222 = "InnerKey"
_s223 = "InnerValue"
_s224 = "NestedXmlMapWithXmlNameMap"
_s225 = "OuterKey"
_s226 = "NestedXmlMapWithXmlNameRequest"
_s227 = "nestedXmlMapWithXmlNameMap"
_s228 = "NestedXmlMapWithXmlNameResponse"
_s229 = "NestedXmlMapsRequest"
_s230 = "nestedMap"
_s231 = "flatNestedMap"
_s232 = "NestedXmlMapsResponse"
_s233 = "NoInputAndOutputOutput"
_s234 = "NullAndEmptyHeadersIO"
_s235 = "a"
_s236 = "X-A"
_s237 = "b"
_s238 = "X-B"
_s239 = "c"
_s240 = "X-C"
_s241 = "OmitsNullSerializesEmptyStringInput"
_s242 = "nullValue"
_s243 = "Null"
_s244 = "emptyString"
_s245 = "Empty"
_s246 = "PutWithContentEncodingInput"
_s247 = "encoding"
_s248 = "Content-Encoding"
_s249 = "data"

STRING_LIST: StaticSchema = (
    16,
    n0,
    _s0,
    0,
    (_s1,),
    ((3, 0),),
)

STRING_SET: StaticSchema = (
    16,
    n0,
    _s2,
    0,
    (_s1,),
    ((3, 0),),
)

INTEGER_LIST: StaticSchema = (
    16,
    n0,
    _s3,
    0,
    (_s1,),
    ((7, 0),),
)

INTEGER_SET: StaticSchema = (
    16,
    n0,
    _s4,
    0,
    (_s1,),
    ((7, 0),),
)

DOUBLE_LIST: StaticSchema = (
    16,
    n0,
    _s5,
    0,
    (_s1,),
    ((10, 0),),
)

BOOLEAN_LIST: StaticSchema = (
    16,
    n0,
    _s6,
    0,
    (_s1,),
    ((2, 0),),
)

TIMESTAMP_LIST: StaticSchema = (
    16,
    n0,
    _s7,
    0,
    (_s1,),
    ((4, 0),),
)

FOO_ENUM: StaticSchema = (
    14,
    n0,
    _s8,
    0,
    (
        _s9,
        _s12,
        _s14,
        _s16,
        _s18,
    ),
    (
        (-1, {_s10: _s11}),
        (-1, {_s10: _s13}),
        (-1, {_s10: _s15}),
        (-1, {_s10: _s17}),
        (-1, {_s10: _s19}),
    ),
)

FOO_ENUM_LIST: StaticSchema = (
    16,
    n0,
    _s20,
    0,
    (_s1,),
    ((FOO_ENUM, 0),),
)

INTEGER_ENUM: StaticSchema = (
    15,
    n0,
    _s21,
    0,
    (
        _s22,
        _s23,
        _s24,
    ),
    (
        (-1, {_s10: 1}),
        (-1, {_s10: 2}),
        (-1, {_s10: 3}),
    ),
)

INTEGER_ENUM_LIST: StaticSchema = (
    16,
    n0,
    _s25,
    0,
    (_s1,),
    ((INTEGER_ENUM, 0),),
)

STRING_MAP: StaticSchema = (
    17,
    n0,
    _s26,
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

ALL_QUERY_STRING_TYPES_INPUT: StaticSchema = (
    18,
    n1,
    _s29,
    {_s30: None},
    (
        _s31,
        _s34,
        _s35,
        _s36,
        _s38,
        _s40,
        _s42,
        _s43,
        _s44,
        _s46,
        _s48,
        _s50,
        _s51,
        _s53,
        _s54,
        _s56,
        _s57,
        _s59,
        _s61,
        _s62,
        _s63,
    ),
    (
        (3, {_s32: _s33}),
        (STRING_LIST, {_s32: _s0}),
        (STRING_SET, {_s32: _s2}),
        (5, {_s32: _s37}),
        (6, {_s32: _s39}),
        (7, {_s32: _s41}),
        (INTEGER_LIST, {_s32: _s3}),
        (INTEGER_SET, {_s32: _s4}),
        (8, {_s32: _s45}),
        (9, {_s32: _s47}),
        (10, {_s32: _s49}),
        (DOUBLE_LIST, {_s32: _s5}),
        (2, {_s32: _s52}),
        (BOOLEAN_LIST, {_s32: _s6}),
        (4, {_s32: _s55}),
        (TIMESTAMP_LIST, {_s32: _s7}),
        (FOO_ENUM, {_s32: _s58}),
        (FOO_ENUM_LIST, {_s32: _s60}),
        (INTEGER_ENUM, {_s32: _s21}),
        (INTEGER_ENUM_LIST, {_s32: _s25}),
        (STRING_MAP, 1024),
    ),
)

PAYLOAD_WITH_XML_NAME: StaticSchema = (
    18,
    n1,
    _s64,
    {_s65: _s66},
    (_s67,),
    ((3, 0),),
)

BODY_WITH_XML_NAME_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s68,
    {_s65: _s69, _s30: None, _s70: None},
    (_s71,),
    ((PAYLOAD_WITH_XML_NAME, 0),),
)

COMPLEX_NESTED_ERROR_DATA: StaticSchema = (
    18,
    n1,
    _s72,
    0,
    (_s11,),
    ((3, 0),),
)

COMPLEX_ERROR: StaticSchema = (
    18,
    n1,
    _s73,
    {_s74: _s75, _s76: 403},
    (
        _s77,
        _s80,
        _s81,
    ),
    (
        (3, {_s78: _s79}),
        (3, 0),
        (COMPLEX_NESTED_ERROR_DATA, 0),
    ),
)

CONSTANT_AND_VARIABLE_QUERY_STRING_INPUT: StaticSchema = (
    18,
    n1,
    _s82,
    {_s30: None},
    (
        _s83,
        _s84,
    ),
    (
        (3, {_s32: _s83}),
        (3, {_s32: _s84}),
    ),
)

CONSTANT_QUERY_STRING_INPUT: StaticSchema = (
    18,
    n1,
    _s85,
    {_s30: None},
    (_s86,),
    ((3, 9),),
)

CONTENT_TYPE_PARAMETERS_INPUT: StaticSchema = (
    18,
    n1,
    _s87,
    {_s30: None},
    (_s28,),
    ((7, 0),),
)

CONTENT_TYPE_PARAMETERS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s88,
    {_s70: None},
)

DATE_TIME: StaticSchema = (
    4,
    n0,
    _s89,
    {_s90: _s91},
)

DATETIME_OFFSETS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s92,
    {_s70: None},
    (_s93,),
    ((DATE_TIME, 0),),
)

EMPTY_INPUT_AND_EMPTY_OUTPUT_INPUT: StaticSchema = (
    18,
    n1,
    _s94,
    {_s30: None},
)

EMPTY_INPUT_AND_EMPTY_OUTPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s95,
    {_s70: None},
)

ENDPOINT_WITH_HOST_LABEL_OPERATION_REQUEST: StaticSchema = (
    18,
    n1,
    _s96,
    {_s30: None},
    (_s97,),
    ((3, 257),),
)

STRING_ENUM: StaticSchema = (
    14,
    n1,
    _s98,
    0,
    (_s99,),
    ((-1, {_s10: _s100}),),
)

ENUM_PAYLOAD_INPUT: StaticSchema = (
    18,
    n1,
    _s101,
    {_s30: None, _s70: None},
    (_s102,),
    ((STRING_ENUM, 16),),
)

FOO_ENUM_MAP: StaticSchema = (
    17,
    n0,
    _s103,
    0,
    (
        _s27,
        _s28,
    ),
    (
        (3, 0),
        (FOO_ENUM, 0),
    ),
)

FLATTENED_XML_MAP_REQUEST: StaticSchema = (
    18,
    n1,
    _s104,
    {_s30: None},
    (_s105,),
    ((FOO_ENUM_MAP, {_s106: None}),),
)

FLATTENED_XML_MAP_RESPONSE: StaticSchema = (
    18,
    n1,
    _s107,
    {_s70: None},
    (_s105,),
    ((FOO_ENUM_MAP, {_s106: None}),),
)

FLATTENED_XML_MAP_WITH_XML_NAME_INPUT_OUTPUT_MAP: StaticSchema = (
    17,
    n1,
    _s108,
    0,
    (
        _s27,
        _s28,
    ),
    (
        (3, {_s65: _s109}),
        (3, {_s65: _s99}),
    ),
)

FLATTENED_XML_MAP_WITH_XML_NAME_REQUEST: StaticSchema = (
    18,
    n1,
    _s110,
    {_s30: None},
    (_s105,),
    ((FLATTENED_XML_MAP_WITH_XML_NAME_INPUT_OUTPUT_MAP, {_s106: None, _s65: _s111}),),
)

FLATTENED_XML_MAP_WITH_XML_NAME_RESPONSE: StaticSchema = (
    18,
    n1,
    _s112,
    {_s70: None},
    (_s105,),
    ((FLATTENED_XML_MAP_WITH_XML_NAME_INPUT_OUTPUT_MAP, {_s106: None, _s65: _s111}),),
)

FLATTENED_XML_MAP_WITH_XML_NAMESPACE_OUTPUT_MAP: StaticSchema = (
    17,
    n1,
    _s113,
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

FLATTENED_XML_MAP_WITH_XML_NAMESPACE_OUTPUT: StaticSchema = (
    18,
    n1,
    _s115,
    {_s70: None},
    (_s105,),
    (
        (
            FLATTENED_XML_MAP_WITH_XML_NAMESPACE_OUTPUT_MAP,
            {
                _s106: None,
                _s65: _s111,
                _s114: MappingProxyType({"uri": "https://the-member.example.com"}),
            },
        ),
    ),
)

FOO_PREFIX_HEADERS: StaticSchema = (
    17,
    n1,
    _s116,
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

FRACTIONAL_SECONDS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s117,
    {_s70: None},
    (_s93,),
    ((DATE_TIME, 0),),
)

GREETING_WITH_ERRORS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s118,
    {_s70: None},
    (_s119,),
    ((3, {_s78: _s120}),),
)

HOST_LABEL_HEADER_INPUT: StaticSchema = (
    18,
    n1,
    _s121,
    {_s30: None},
    (_s122,),
    ((3, {_s78: _s123, _s124: None, _s125: None}),),
)

HTTP_EMPTY_PREFIX_HEADERS_INPUT: StaticSchema = (
    18,
    n1,
    _s126,
    {_s30: None},
    (
        _s127,
        _s130,
    ),
    (
        (STRING_MAP, {_s128: _s129}),
        (3, {_s78: _s86}),
    ),
)

HTTP_EMPTY_PREFIX_HEADERS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s131,
    {_s70: None},
    (
        _s127,
        _s130,
    ),
    (
        (STRING_MAP, {_s128: _s129}),
        (3, {_s78: _s86}),
    ),
)

HTTP_PAYLOAD_TRAITS_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s132,
    {_s30: None, _s70: None},
    (
        _s133,
        _s135,
    ),
    (
        (3, {_s78: _s134}),
        (1, 16),
    ),
)

TEXT_PLAIN_BLOB: StaticSchema = (
    1,
    n0,
    _s136,
    {_s137: _s138},
)

HTTP_PAYLOAD_TRAITS_WITH_MEDIA_TYPE_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s139,
    {_s30: None, _s70: None},
    (
        _s133,
        _s135,
    ),
    (
        (3, {_s78: _s134}),
        (TEXT_PLAIN_BLOB, 16),
    ),
)

HTTP_PAYLOAD_WITH_MEMBER_XML_NAME_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s140,
    {_s30: None, _s70: None},
    (_s71,),
    ((PAYLOAD_WITH_XML_NAME, {_s65: _s141, _s142: None}),),
)

NESTED_PAYLOAD: StaticSchema = (
    18,
    n1,
    _s143,
    0,
    (
        _s119,
        _s67,
    ),
    (
        (3, 0),
        (3, 0),
    ),
)

HTTP_PAYLOAD_WITH_STRUCTURE_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s144,
    {_s30: None, _s70: None},
    (_s71,),
    ((NESTED_PAYLOAD, 16),),
)

UNION_PAYLOAD: StaticSchema = (
    19,
    n1,
    _s145,
    0,
    (_s119,),
    ((3, 0),),
)

HTTP_PAYLOAD_WITH_UNION_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s146,
    {_s30: None, _s70: None},
    (_s71,),
    ((UNION_PAYLOAD, 16),),
)

HTTP_PAYLOAD_WITH_XML_NAME_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s147,
    {_s30: None, _s70: None},
    (_s71,),
    ((PAYLOAD_WITH_XML_NAME, 16),),
)

PAYLOAD_WITH_XML_NAMESPACE_AND_PREFIX: StaticSchema = (
    18,
    n1,
    _s148,
    {_s114: MappingProxyType({"uri": "http://foo.com", "prefix": "baz"})},
    (_s67,),
    ((3, 0),),
)

HTTP_PAYLOAD_WITH_XML_NAMESPACE_AND_PREFIX_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s149,
    {_s30: None, _s70: None},
    (_s71,),
    ((PAYLOAD_WITH_XML_NAMESPACE_AND_PREFIX, 16),),
)

PAYLOAD_WITH_XML_NAMESPACE: StaticSchema = (
    18,
    n1,
    _s150,
    {_s114: MappingProxyType({"uri": "http://foo.com"})},
    (_s67,),
    ((3, 0),),
)

HTTP_PAYLOAD_WITH_XML_NAMESPACE_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s151,
    {_s30: None, _s70: None},
    (_s71,),
    ((PAYLOAD_WITH_XML_NAMESPACE, 16),),
)

HTTP_PREFIX_HEADERS_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s152,
    {_s30: None, _s70: None},
    (
        _s133,
        _s154,
    ),
    (
        (3, {_s78: _s153}),
        (FOO_PREFIX_HEADERS, {_s128: _s155}),
    ),
)

HTTP_REQUEST_WITH_FLOAT_LABELS_INPUT: StaticSchema = (
    18,
    n1,
    _s156,
    {_s30: None},
    (
        _s157,
        _s158,
    ),
    (
        (9, 9),
        (10, 9),
    ),
)

HTTP_REQUEST_WITH_GREEDY_LABEL_IN_PATH_INPUT: StaticSchema = (
    18,
    n1,
    _s159,
    {_s30: None},
    (
        _s133,
        _s83,
    ),
    (
        (3, 9),
        (3, 9),
    ),
)

EPOCH_SECONDS: StaticSchema = (
    4,
    n0,
    _s160,
    {_s90: _s161},
)

HTTP_DATE: StaticSchema = (
    4,
    n0,
    _s162,
    {_s90: _s163},
)

HTTP_REQUEST_WITH_LABELS_AND_TIMESTAMP_FORMAT_INPUT: StaticSchema = (
    18,
    n1,
    _s164,
    {_s30: None},
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
        (4, {_s90: _s161, _s166: None, _s125: None}),
        (4, {_s90: _s163, _s166: None, _s125: None}),
        (4, {_s90: _s91, _s166: None, _s125: None}),
        (4, 9),
        (EPOCH_SECONDS, 9),
        (HTTP_DATE, 9),
        (DATE_TIME, 9),
    ),
)

HTTP_REQUEST_WITH_LABELS_INPUT: StaticSchema = (
    18,
    n1,
    _s173,
    {_s30: None},
    (
        _s174,
        _s175,
        _s176,
        _s177,
        _s157,
        _s158,
        _s178,
        _s179,
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

HTTP_RESPONSE_CODE_OUTPUT: StaticSchema = (
    18,
    n1,
    _s180,
    {_s70: None},
    (_s181,),
    ((7, 128),),
)

IGNORE_QUERY_PARAMS_IN_RESPONSE_OUTPUT: StaticSchema = (
    18,
    n1,
    _s182,
    {_s70: None},
    (_s83,),
    ((3, {_s32: _s83}),),
)

INPUT_AND_OUTPUT_WITH_HEADERS_IO: StaticSchema = (
    18,
    n1,
    _s183,
    {_s30: None, _s70: None},
    (
        _s184,
        _s186,
        _s188,
        _s190,
        _s192,
        _s194,
        _s196,
        _s198,
        _s200,
        _s202,
        _s204,
        _s206,
        _s208,
        _s210,
        _s212,
        _s214,
    ),
    (
        (3, {_s78: _s185}),
        (5, {_s78: _s187}),
        (6, {_s78: _s189}),
        (7, {_s78: _s191}),
        (8, {_s78: _s193}),
        (9, {_s78: _s195}),
        (10, {_s78: _s197}),
        (2, {_s78: _s199}),
        (2, {_s78: _s201}),
        (STRING_LIST, {_s78: _s203}),
        (STRING_SET, {_s78: _s205}),
        (INTEGER_LIST, {_s78: _s207}),
        (BOOLEAN_LIST, {_s78: _s209}),
        (TIMESTAMP_LIST, {_s78: _s211}),
        (FOO_ENUM, {_s78: _s213}),
        (FOO_ENUM_LIST, {_s78: _s215}),
    ),
)

INVALID_GREETING: StaticSchema = (
    18,
    n1,
    _s216,
    {_s74: _s75, _s76: 400},
    (_s217,),
    ((3, 0),),
)

LIST_WITH_MEMBER_NAMESPACE: StaticSchema = (
    16,
    n1,
    _s218,
    {_s114: MappingProxyType({"uri": "https://xml-list.example.com"})},
    (_s1,),
    ((3, {_s114: MappingProxyType({"uri": "https://xml-member.example.com"})}),),
)

LIST_WITH_NAMESPACE: StaticSchema = (
    16,
    n1,
    _s219,
    {_s114: MappingProxyType({"uri": "https://xml-list.example.com"})},
    (_s1,),
    ((3, 0),),
)

NESTED_MAP: StaticSchema = (
    17,
    n1,
    _s220,
    0,
    (
        _s27,
        _s28,
    ),
    (
        (3, 0),
        (FOO_ENUM_MAP, 0),
    ),
)

NESTED_XML_MAP_WITH_XML_NAME_INNER_MAP: StaticSchema = (
    17,
    n1,
    _s221,
    0,
    (
        _s27,
        _s28,
    ),
    (
        (3, {_s65: _s222}),
        (3, {_s65: _s223}),
    ),
)

NESTED_XML_MAP_WITH_XML_NAME_MAP: StaticSchema = (
    17,
    n1,
    _s224,
    0,
    (
        _s27,
        _s28,
    ),
    (
        (3, {_s65: _s225}),
        (NESTED_XML_MAP_WITH_XML_NAME_INNER_MAP, 0),
    ),
)

NESTED_XML_MAP_WITH_XML_NAME_REQUEST: StaticSchema = (
    18,
    n1,
    _s226,
    {_s30: None},
    (_s227,),
    ((NESTED_XML_MAP_WITH_XML_NAME_MAP, 0),),
)

NESTED_XML_MAP_WITH_XML_NAME_RESPONSE: StaticSchema = (
    18,
    n1,
    _s228,
    {_s70: None},
    (_s227,),
    ((NESTED_XML_MAP_WITH_XML_NAME_MAP, 0),),
)

NESTED_XML_MAPS_REQUEST: StaticSchema = (
    18,
    n1,
    _s229,
    {_s30: None},
    (
        _s230,
        _s231,
    ),
    (
        (NESTED_MAP, 0),
        (NESTED_MAP, {_s106: None}),
    ),
)

NESTED_XML_MAPS_RESPONSE: StaticSchema = (
    18,
    n1,
    _s232,
    {_s70: None},
    (
        _s230,
        _s231,
    ),
    (
        (NESTED_MAP, 0),
        (NESTED_MAP, {_s106: None}),
    ),
)

NO_INPUT_AND_OUTPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s233,
    {_s70: None},
)

NULL_AND_EMPTY_HEADERS_IO: StaticSchema = (
    18,
    n1,
    _s234,
    {_s30: None, _s70: None},
    (
        _s235,
        _s237,
        _s239,
    ),
    (
        (3, {_s78: _s236}),
        (3, {_s78: _s238}),
        (STRING_LIST, {_s78: _s240}),
    ),
)

OMITS_NULL_SERIALIZES_EMPTY_STRING_INPUT: StaticSchema = (
    18,
    n1,
    _s241,
    {_s30: None},
    (
        _s242,
        _s244,
    ),
    (
        (3, {_s32: _s243}),
        (3, {_s32: _s245}),
    ),
)

PUT_WITH_CONTENT_ENCODING_INPUT: StaticSchema = (
    18,
    n1,
    _s246,
    {_s30: None},
    (
        _s247,
        _s249,
    ),
    (
        (3, {_s78: _s248}),
        (3, 0),
    ),
)
