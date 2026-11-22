from types import MappingProxyType

from smithy_core._schema_compact import StaticOperationSchema, StaticSchema

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
_s30 = "smithy.synthetic#originalShapeId"
_s31 = "aws.protocoltests.restxml#AllQueryStringTypesInput"
_s32 = "smithy.api#input"
_s33 = "queryString"
_s34 = "smithy.api#httpQuery"
_s35 = "String"
_s36 = "queryStringList"
_s37 = "queryStringSet"
_s38 = "queryByte"
_s39 = "Byte"
_s40 = "queryShort"
_s41 = "Short"
_s42 = "queryInteger"
_s43 = "Integer"
_s44 = "queryIntegerList"
_s45 = "queryIntegerSet"
_s46 = "queryLong"
_s47 = "Long"
_s48 = "queryFloat"
_s49 = "Float"
_s50 = "queryDouble"
_s51 = "Double"
_s52 = "queryDoubleList"
_s53 = "queryBoolean"
_s54 = "Boolean"
_s55 = "queryBooleanList"
_s56 = "queryTimestamp"
_s57 = "Timestamp"
_s58 = "queryTimestampList"
_s59 = "queryEnum"
_s60 = "Enum"
_s61 = "queryEnumList"
_s62 = "EnumList"
_s63 = "queryIntegerEnum"
_s64 = "queryIntegerEnumList"
_s65 = "queryParamsMapOfStrings"
_s66 = "ComplexNestedErrorData"
_s67 = "ComplexError"
_s68 = "smithy.api#error"
_s69 = "client"
_s70 = "smithy.api#httpError"
_s71 = "Header"
_s72 = "smithy.api#httpHeader"
_s73 = "X-Header"
_s74 = "TopLevel"
_s75 = "Nested"
_s76 = "ConstantAndVariableQueryStringInput"
_s77 = "aws.protocoltests.restxml#ConstantAndVariableQueryStringInput"
_s78 = "baz"
_s79 = "maybeSet"
_s80 = "ConstantQueryStringInput"
_s81 = "aws.protocoltests.restxml#ConstantQueryStringInput"
_s82 = "hello"
_s83 = "ContentTypeParametersInput"
_s84 = "aws.protocoltests.restxml#ContentTypeParametersInput"
_s85 = "ContentTypeParametersOutput"
_s86 = "aws.protocoltests.restxml#ContentTypeParametersOutput"
_s87 = "smithy.api#output"
_s88 = "DateTime"
_s89 = "smithy.api#timestampFormat"
_s90 = "date-time"
_s91 = "DatetimeOffsetsOutput"
_s92 = "aws.protocoltests.restxml#DatetimeOffsetsOutput"
_s93 = "datetime"
_s94 = "EmptyInputAndEmptyOutputInput"
_s95 = "aws.protocoltests.restxml#EmptyInputAndEmptyOutputInput"
_s96 = "EmptyInputAndEmptyOutputOutput"
_s97 = "aws.protocoltests.restxml#EmptyInputAndEmptyOutputOutput"
_s98 = "FlattenedXmlMapWithXmlNameInputOutputMap"
_s99 = "smithy.api#xmlName"
_s100 = "K"
_s101 = "V"
_s102 = "FlattenedXmlMapWithXmlNamespaceOutputMap"
_s103 = "smithy.api#xmlNamespace"
_s104 = "FlattenedXmlMapWithXmlNamespaceOutput"
_s105 = "aws.protocoltests.restxml#FlattenedXmlMapWithXmlNamespaceOutput"
_s106 = "myMap"
_s107 = "smithy.api#xmlFlattened"
_s108 = "KVP"
_s109 = "FooPrefixHeaders"
_s110 = "FractionalSecondsOutput"
_s111 = "aws.protocoltests.restxml#FractionalSecondsOutput"
_s112 = "GreetingWithErrorsOutput"
_s113 = "aws.protocoltests.restxml#GreetingWithErrorsOutput"
_s114 = "greeting"
_s115 = "X-Greeting"
_s116 = "HttpEmptyPrefixHeadersInput"
_s117 = "aws.protocoltests.restxml#HttpEmptyPrefixHeadersInput"
_s118 = "prefixHeaders"
_s119 = "smithy.api#httpPrefixHeaders"
_s120 = ""
_s121 = "specificHeader"
_s122 = "HttpEmptyPrefixHeadersOutput"
_s123 = "aws.protocoltests.restxml#HttpEmptyPrefixHeadersOutput"
_s124 = "HttpRequestWithFloatLabelsInput"
_s125 = "aws.protocoltests.restxml#HttpRequestWithFloatLabelsInput"
_s126 = "float"
_s127 = "double"
_s128 = "HttpRequestWithGreedyLabelInPathInput"
_s129 = "aws.protocoltests.restxml#HttpRequestWithGreedyLabelInPathInput"
_s130 = "foo"
_s131 = "EpochSeconds"
_s132 = "epoch-seconds"
_s133 = "HttpDate"
_s134 = "http-date"
_s135 = "HttpRequestWithLabelsAndTimestampFormatInput"
_s136 = "aws.protocoltests.restxml#HttpRequestWithLabelsAndTimestampFormatInput"
_s137 = "memberEpochSeconds"
_s138 = "smithy.api#httpLabel"
_s139 = "smithy.api#required"
_s140 = "memberHttpDate"
_s141 = "memberDateTime"
_s142 = "defaultFormat"
_s143 = "targetEpochSeconds"
_s144 = "targetHttpDate"
_s145 = "targetDateTime"
_s146 = "HttpRequestWithLabelsInput"
_s147 = "aws.protocoltests.restxml#HttpRequestWithLabelsInput"
_s148 = "string"
_s149 = "short"
_s150 = "integer"
_s151 = "long"
_s152 = "boolean"
_s153 = "timestamp"
_s154 = "HttpResponseCodeOutput"
_s155 = "aws.protocoltests.restxml#HttpResponseCodeOutput"
_s156 = "Status"
_s157 = "IgnoreQueryParamsInResponseOutput"
_s158 = "aws.protocoltests.restxml#IgnoreQueryParamsInResponseOutput"
_s159 = "InvalidGreeting"
_s160 = "Message"
_s161 = "ListWithMemberNamespace"
_s162 = "ListWithNamespace"
_s163 = "FooEnumMap"
_s164 = "NestedMap"
_s165 = "NestedPayload"
_s166 = "name"
_s167 = "NestedXmlMapWithXmlNameInnerMap"
_s168 = "InnerKey"
_s169 = "InnerValue"
_s170 = "NestedXmlMapWithXmlNameMap"
_s171 = "OuterKey"
_s172 = "NoInputAndOutputOutput"
_s173 = "aws.protocoltests.restxml#NoInputAndOutputOutput"
_s174 = "OmitsNullSerializesEmptyStringInput"
_s175 = "aws.protocoltests.restxml#OmitsNullSerializesEmptyStringInput"
_s176 = "nullValue"
_s177 = "Null"
_s178 = "emptyString"
_s179 = "Empty"
_s182 = "PayloadWithXmlNamespace"
_s183 = "PayloadWithXmlNamespaceAndPrefix"
_s184 = "PutWithContentEncodingInput"
_s185 = "aws.protocoltests.restxml#PutWithContentEncodingInput"
_s186 = "encoding"
_s187 = "Content-Encoding"
_s188 = "data"
_s189 = "QueryIdempotencyTokenAutoFillInput"
_s190 = "aws.protocoltests.restxml#QueryIdempotencyTokenAutoFillInput"
_s191 = "token"
_s192 = "smithy.api#idempotencyToken"
_s193 = "StringListMap"
_s194 = "QueryParamsAsStringListMapInput"
_s195 = "aws.protocoltests.restxml#QueryParamsAsStringListMapInput"
_s196 = "qux"
_s197 = "corge"
_s244 = "AllQueryStringTypesOutput"
_s245 = "smithy.api#Unit"
_s251 = "ConstantAndVariableQueryStringOutput"
_s252 = "ConstantQueryStringOutput"
_s253 = "DatetimeOffsetsInput"
_s274 = "FlattenedXmlMapWithXmlNamespaceInput"
_s275 = "FractionalSecondsInput"
_s276 = "GreetingWithErrorsInput"
_s315 = "HttpRequestWithFloatLabelsOutput"
_s316 = "HttpRequestWithGreedyLabelInPathOutput"
_s317 = "HttpRequestWithLabelsOutput"
_s318 = "HttpRequestWithLabelsAndTimestampFormatOutput"
_s319 = "HttpResponseCodeInput"
_s323 = "IgnoreQueryParamsInResponseInput"
_s372 = "NoInputAndOutputInput"
_s382 = "OmitsNullSerializesEmptyStringOutput"
_s383 = "PutWithContentEncodingOutput"
_s384 = "QueryIdempotencyTokenAutoFillOutput"
_s385 = "QueryParamsAsStringListMapOutput"
_s513 = "AllQueryStringTypes"
_s514 = "smithy.api#http"
_s516 = "ConstantAndVariableQueryString"
_s517 = "ConstantQueryString"
_s518 = "ContentTypeParameters"
_s519 = "DatetimeOffsets"
_s520 = "EmptyInputAndEmptyOutput"
_s527 = "FlattenedXmlMapWithXmlNamespace"
_s528 = "FractionalSeconds"
_s529 = "GreetingWithErrors"
_s530 = "HttpEmptyPrefixHeaders"
_s541 = "HttpRequestWithFloatLabels"
_s542 = "HttpRequestWithGreedyLabelInPath"
_s543 = "HttpRequestWithLabels"
_s544 = "HttpRequestWithLabelsAndTimestampFormat"
_s545 = "HttpResponseCode"
_s547 = "IgnoreQueryParamsInResponse"
_s552 = "NoInputAndOutput"
_s555 = "OmitsNullSerializesEmptyString"
_s556 = "PutWithContentEncoding"
_s557 = "smithy.api#requestCompression"
_s558 = "QueryIdempotencyTokenAutoFill"
_s559 = "QueryParamsAsStringListMap"

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
    (_s9, _s12, _s14, _s16, _s18),
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
    (_s22, _s23, _s24),
    ((-1, {_s10: 1}), (-1, {_s10: 2}), (-1, {_s10: 3})),
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
    (_s27, _s28),
    ((3, 0), (3, 0)),
)

ALL_QUERY_STRING_TYPES_INPUT: StaticSchema = (
    18,
    n1,
    _s29,
    {_s30: _s31, _s32: None},
    (
        _s33,
        _s36,
        _s37,
        _s38,
        _s40,
        _s42,
        _s44,
        _s45,
        _s46,
        _s48,
        _s50,
        _s52,
        _s53,
        _s55,
        _s56,
        _s58,
        _s59,
        _s61,
        _s63,
        _s64,
        _s65,
    ),
    (
        (3, {_s34: _s35}),
        (STRING_LIST, {_s34: _s0}),
        (STRING_SET, {_s34: _s2}),
        (5, {_s34: _s39}),
        (6, {_s34: _s41}),
        (7, {_s34: _s43}),
        (INTEGER_LIST, {_s34: _s3}),
        (INTEGER_SET, {_s34: _s4}),
        (8, {_s34: _s47}),
        (9, {_s34: _s49}),
        (10, {_s34: _s51}),
        (DOUBLE_LIST, {_s34: _s5}),
        (2, {_s34: _s54}),
        (BOOLEAN_LIST, {_s34: _s6}),
        (4, {_s34: _s57}),
        (TIMESTAMP_LIST, {_s34: _s7}),
        (FOO_ENUM, {_s34: _s60}),
        (FOO_ENUM_LIST, {_s34: _s62}),
        (INTEGER_ENUM, {_s34: _s21}),
        (INTEGER_ENUM_LIST, {_s34: _s25}),
        (STRING_MAP, 1024),
    ),
)

ALL_QUERY_STRING_TYPES_OUTPUT: StaticSchema = (
    18,
    n1,
    _s244,
    {_s30: _s245, _s87: None},
)

ALL_QUERY_STRING_TYPES: StaticOperationSchema = (
    23,
    n1,
    _s513,
    {_s514: MappingProxyType({"uri": "/AllQueryStringTypesInput", "method": "GET"})},
    ALL_QUERY_STRING_TYPES_INPUT,
    ALL_QUERY_STRING_TYPES_OUTPUT,
    (),
)

COMPLEX_NESTED_ERROR_DATA: StaticSchema = (
    18,
    n1,
    _s66,
    0,
    (_s11,),
    ((3, 0),),
)

COMPLEX_ERROR: StaticSchema = (
    18,
    n1,
    _s67,
    {_s68: _s69, _s70: 403},
    (_s71, _s74, _s75),
    ((3, {_s72: _s73}), (3, 0), (COMPLEX_NESTED_ERROR_DATA, 0)),
)

CONSTANT_AND_VARIABLE_QUERY_STRING_INPUT: StaticSchema = (
    18,
    n1,
    _s76,
    {_s30: _s77, _s32: None},
    (_s78, _s79),
    ((3, {_s34: _s78}), (3, {_s34: _s79})),
)

CONSTANT_AND_VARIABLE_QUERY_STRING_OUTPUT: StaticSchema = (
    18,
    n1,
    _s251,
    {_s30: _s245, _s87: None},
)

CONSTANT_AND_VARIABLE_QUERY_STRING: StaticOperationSchema = (
    23,
    n1,
    _s516,
    {
        _s514: MappingProxyType(
            {"uri": "/ConstantAndVariableQueryString?foo=bar", "method": "GET"}
        )
    },
    CONSTANT_AND_VARIABLE_QUERY_STRING_INPUT,
    CONSTANT_AND_VARIABLE_QUERY_STRING_OUTPUT,
    (),
)

CONSTANT_QUERY_STRING_INPUT: StaticSchema = (
    18,
    n1,
    _s80,
    {_s30: _s81, _s32: None},
    (_s82,),
    ((3, 9),),
)

CONSTANT_QUERY_STRING_OUTPUT: StaticSchema = (
    18,
    n1,
    _s252,
    {_s30: _s245, _s87: None},
)

CONSTANT_QUERY_STRING: StaticOperationSchema = (
    23,
    n1,
    _s517,
    {
        _s514: MappingProxyType(
            {"uri": "/ConstantQueryString/{hello}?foo=bar&hello", "method": "GET"}
        )
    },
    CONSTANT_QUERY_STRING_INPUT,
    CONSTANT_QUERY_STRING_OUTPUT,
    (),
)

CONTENT_TYPE_PARAMETERS_INPUT: StaticSchema = (
    18,
    n1,
    _s83,
    {_s30: _s84, _s32: None},
    (_s28,),
    ((7, 0),),
)

CONTENT_TYPE_PARAMETERS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s85,
    {_s30: _s86, _s87: None},
)

CONTENT_TYPE_PARAMETERS: StaticOperationSchema = (
    23,
    n1,
    _s518,
    {_s514: MappingProxyType({"uri": "/ContentTypeParameters", "method": "PUT"})},
    CONTENT_TYPE_PARAMETERS_INPUT,
    CONTENT_TYPE_PARAMETERS_OUTPUT,
    (),
)

DATE_TIME: StaticSchema = (
    4,
    n0,
    _s88,
    {_s89: _s90},
)

DATETIME_OFFSETS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s91,
    {_s30: _s92, _s87: None},
    (_s93,),
    ((DATE_TIME, 0),),
)

DATETIME_OFFSETS_INPUT: StaticSchema = (
    18,
    n1,
    _s253,
    {_s30: _s245, _s32: None},
)

DATETIME_OFFSETS: StaticOperationSchema = (
    23,
    n1,
    _s519,
    {_s514: MappingProxyType({"uri": "/DatetimeOffsets", "method": "POST"})},
    DATETIME_OFFSETS_INPUT,
    DATETIME_OFFSETS_OUTPUT,
    (),
)

EMPTY_INPUT_AND_EMPTY_OUTPUT_INPUT: StaticSchema = (
    18,
    n1,
    _s94,
    {_s30: _s95, _s32: None},
)

EMPTY_INPUT_AND_EMPTY_OUTPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s96,
    {_s30: _s97, _s87: None},
)

EMPTY_INPUT_AND_EMPTY_OUTPUT: StaticOperationSchema = (
    23,
    n1,
    _s520,
    {_s514: MappingProxyType({"uri": "/EmptyInputAndEmptyOutput", "method": "POST"})},
    EMPTY_INPUT_AND_EMPTY_OUTPUT_INPUT,
    EMPTY_INPUT_AND_EMPTY_OUTPUT_OUTPUT,
    (),
)

FLATTENED_XML_MAP_WITH_XML_NAME_INPUT_OUTPUT_MAP: StaticSchema = (
    17,
    n1,
    _s98,
    0,
    (_s27, _s28),
    ((3, {_s99: _s100}), (3, {_s99: _s101})),
)

FLATTENED_XML_MAP_WITH_XML_NAMESPACE_OUTPUT_MAP: StaticSchema = (
    17,
    n1,
    _s102,
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

FLATTENED_XML_MAP_WITH_XML_NAMESPACE_OUTPUT: StaticSchema = (
    18,
    n1,
    _s104,
    {_s30: _s105, _s87: None},
    (_s106,),
    (
        (
            FLATTENED_XML_MAP_WITH_XML_NAMESPACE_OUTPUT_MAP,
            {
                _s107: None,
                _s99: _s108,
                _s103: MappingProxyType({"uri": "https://the-member.example.com"}),
            },
        ),
    ),
)

FLATTENED_XML_MAP_WITH_XML_NAMESPACE_INPUT: StaticSchema = (
    18,
    n1,
    _s274,
    {_s30: _s245, _s32: None},
)

FLATTENED_XML_MAP_WITH_XML_NAMESPACE: StaticOperationSchema = (
    23,
    n1,
    _s527,
    {
        _s514: MappingProxyType(
            {"uri": "/FlattenedXmlMapWithXmlNamespace", "method": "POST"}
        )
    },
    FLATTENED_XML_MAP_WITH_XML_NAMESPACE_INPUT,
    FLATTENED_XML_MAP_WITH_XML_NAMESPACE_OUTPUT,
    (),
)

FOO_PREFIX_HEADERS: StaticSchema = (
    17,
    n1,
    _s109,
    0,
    (_s27, _s28),
    ((3, 0), (3, 0)),
)

FRACTIONAL_SECONDS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s110,
    {_s30: _s111, _s87: None},
    (_s93,),
    ((DATE_TIME, 0),),
)

FRACTIONAL_SECONDS_INPUT: StaticSchema = (
    18,
    n1,
    _s275,
    {_s30: _s245, _s32: None},
)

FRACTIONAL_SECONDS: StaticOperationSchema = (
    23,
    n1,
    _s528,
    {_s514: MappingProxyType({"uri": "/FractionalSeconds", "method": "POST"})},
    FRACTIONAL_SECONDS_INPUT,
    FRACTIONAL_SECONDS_OUTPUT,
    (),
)

GREETING_WITH_ERRORS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s112,
    {_s30: _s113, _s87: None},
    (_s114,),
    ((3, {_s72: _s115}),),
)

GREETING_WITH_ERRORS_INPUT: StaticSchema = (
    18,
    n1,
    _s276,
    {_s30: _s245, _s32: None},
)

GREETING_WITH_ERRORS: StaticOperationSchema = (
    23,
    n1,
    _s529,
    {_s514: MappingProxyType({"uri": "/GreetingWithErrors", "method": "PUT"})},
    GREETING_WITH_ERRORS_INPUT,
    GREETING_WITH_ERRORS_OUTPUT,
    (COMPLEX_ERROR, lambda: INVALID_GREETING),
)

HTTP_EMPTY_PREFIX_HEADERS_INPUT: StaticSchema = (
    18,
    n1,
    _s116,
    {_s30: _s117, _s32: None},
    (_s118, _s121),
    ((STRING_MAP, {_s119: _s120}), (3, {_s72: _s82})),
)

HTTP_EMPTY_PREFIX_HEADERS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s122,
    {_s30: _s123, _s87: None},
    (_s118, _s121),
    ((STRING_MAP, {_s119: _s120}), (3, {_s72: _s82})),
)

HTTP_EMPTY_PREFIX_HEADERS: StaticOperationSchema = (
    23,
    n1,
    _s530,
    {_s514: MappingProxyType({"uri": "/HttpEmptyPrefixHeaders", "method": "GET"})},
    HTTP_EMPTY_PREFIX_HEADERS_INPUT,
    HTTP_EMPTY_PREFIX_HEADERS_OUTPUT,
    (),
)

HTTP_REQUEST_WITH_FLOAT_LABELS_INPUT: StaticSchema = (
    18,
    n1,
    _s124,
    {_s30: _s125, _s32: None},
    (_s126, _s127),
    ((9, 9), (10, 9)),
)

HTTP_REQUEST_WITH_FLOAT_LABELS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s315,
    {_s30: _s245, _s87: None},
)

HTTP_REQUEST_WITH_FLOAT_LABELS: StaticOperationSchema = (
    23,
    n1,
    _s541,
    {
        _s514: MappingProxyType(
            {"method": "GET", "uri": "/FloatHttpLabels/{float}/{double}"}
        )
    },
    HTTP_REQUEST_WITH_FLOAT_LABELS_INPUT,
    HTTP_REQUEST_WITH_FLOAT_LABELS_OUTPUT,
    (),
)

HTTP_REQUEST_WITH_GREEDY_LABEL_IN_PATH_INPUT: StaticSchema = (
    18,
    n1,
    _s128,
    {_s30: _s129, _s32: None},
    (_s130, _s78),
    ((3, 9), (3, 9)),
)

HTTP_REQUEST_WITH_GREEDY_LABEL_IN_PATH_OUTPUT: StaticSchema = (
    18,
    n1,
    _s316,
    {_s30: _s245, _s87: None},
)

HTTP_REQUEST_WITH_GREEDY_LABEL_IN_PATH: StaticOperationSchema = (
    23,
    n1,
    _s542,
    {
        _s514: MappingProxyType(
            {
                "method": "GET",
                "uri": "/HttpRequestWithGreedyLabelInPath/foo/{foo}/baz/{baz+}",
            }
        )
    },
    HTTP_REQUEST_WITH_GREEDY_LABEL_IN_PATH_INPUT,
    HTTP_REQUEST_WITH_GREEDY_LABEL_IN_PATH_OUTPUT,
    (),
)

EPOCH_SECONDS: StaticSchema = (
    4,
    n0,
    _s131,
    {_s89: _s132},
)

HTTP_DATE: StaticSchema = (
    4,
    n0,
    _s133,
    {_s89: _s134},
)

HTTP_REQUEST_WITH_LABELS_AND_TIMESTAMP_FORMAT_INPUT: StaticSchema = (
    18,
    n1,
    _s135,
    {_s30: _s136, _s32: None},
    (_s137, _s140, _s141, _s142, _s143, _s144, _s145),
    (
        (4, {_s89: _s132, _s138: None, _s139: None}),
        (4, {_s89: _s134, _s138: None, _s139: None}),
        (4, {_s89: _s90, _s138: None, _s139: None}),
        (4, 9),
        (EPOCH_SECONDS, 9),
        (HTTP_DATE, 9),
        (DATE_TIME, 9),
    ),
)

HTTP_REQUEST_WITH_LABELS_AND_TIMESTAMP_FORMAT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s318,
    {_s30: _s245, _s87: None},
)

HTTP_REQUEST_WITH_LABELS_AND_TIMESTAMP_FORMAT: StaticOperationSchema = (
    23,
    n1,
    _s544,
    {
        _s514: MappingProxyType(
            {
                "method": "GET",
                "uri": "/HttpRequestWithLabelsAndTimestampFormat/{memberEpochSeconds}/{memberHttpDate}/{memberDateTime}/{defaultFormat}/{targetEpochSeconds}/{targetHttpDate}/{targetDateTime}",
            }
        )
    },
    HTTP_REQUEST_WITH_LABELS_AND_TIMESTAMP_FORMAT_INPUT,
    HTTP_REQUEST_WITH_LABELS_AND_TIMESTAMP_FORMAT_OUTPUT,
    (),
)

HTTP_REQUEST_WITH_LABELS_INPUT: StaticSchema = (
    18,
    n1,
    _s146,
    {_s30: _s147, _s32: None},
    (_s148, _s149, _s150, _s151, _s126, _s127, _s152, _s153),
    ((3, 9), (6, 9), (7, 9), (8, 9), (9, 9), (10, 9), (2, 9), (4, 9)),
)

HTTP_REQUEST_WITH_LABELS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s317,
    {_s30: _s245, _s87: None},
)

HTTP_REQUEST_WITH_LABELS: StaticOperationSchema = (
    23,
    n1,
    _s543,
    {
        _s514: MappingProxyType(
            {
                "method": "GET",
                "uri": "/HttpRequestWithLabels/{string}/{short}/{integer}/{long}/{float}/{double}/{boolean}/{timestamp}",
            }
        )
    },
    HTTP_REQUEST_WITH_LABELS_INPUT,
    HTTP_REQUEST_WITH_LABELS_OUTPUT,
    (),
)

HTTP_RESPONSE_CODE_OUTPUT: StaticSchema = (
    18,
    n1,
    _s154,
    {_s30: _s155, _s87: None},
    (_s156,),
    ((7, 128),),
)

HTTP_RESPONSE_CODE_INPUT: StaticSchema = (
    18,
    n1,
    _s319,
    {_s30: _s245, _s32: None},
)

HTTP_RESPONSE_CODE: StaticOperationSchema = (
    23,
    n1,
    _s545,
    {_s514: MappingProxyType({"uri": "/HttpResponseCode", "method": "PUT"})},
    HTTP_RESPONSE_CODE_INPUT,
    HTTP_RESPONSE_CODE_OUTPUT,
    (),
)

IGNORE_QUERY_PARAMS_IN_RESPONSE_OUTPUT: StaticSchema = (
    18,
    n1,
    _s157,
    {_s30: _s158, _s87: None},
    (_s78,),
    ((3, {_s34: _s78}),),
)

IGNORE_QUERY_PARAMS_IN_RESPONSE_INPUT: StaticSchema = (
    18,
    n1,
    _s323,
    {_s30: _s245, _s32: None},
)

IGNORE_QUERY_PARAMS_IN_RESPONSE: StaticOperationSchema = (
    23,
    n1,
    _s547,
    {_s514: MappingProxyType({"uri": "/IgnoreQueryParamsInResponse", "method": "GET"})},
    IGNORE_QUERY_PARAMS_IN_RESPONSE_INPUT,
    IGNORE_QUERY_PARAMS_IN_RESPONSE_OUTPUT,
    (),
)

INVALID_GREETING: StaticSchema = (
    18,
    n1,
    _s159,
    {_s68: _s69, _s70: 400},
    (_s160,),
    ((3, 0),),
)

LIST_WITH_MEMBER_NAMESPACE: StaticSchema = (
    16,
    n1,
    _s161,
    {_s103: MappingProxyType({"uri": "https://xml-list.example.com"})},
    (_s1,),
    ((3, {_s103: MappingProxyType({"uri": "https://xml-member.example.com"})}),),
)

LIST_WITH_NAMESPACE: StaticSchema = (
    16,
    n1,
    _s162,
    {_s103: MappingProxyType({"uri": "https://xml-list.example.com"})},
    (_s1,),
    ((3, 0),),
)

FOO_ENUM_MAP: StaticSchema = (
    17,
    n0,
    _s163,
    0,
    (_s27, _s28),
    ((3, 0), (FOO_ENUM, 0)),
)

NESTED_MAP: StaticSchema = (
    17,
    n1,
    _s164,
    0,
    (_s27, _s28),
    ((3, 0), (FOO_ENUM_MAP, 0)),
)

NESTED_PAYLOAD: StaticSchema = (
    18,
    n1,
    _s165,
    0,
    (_s114, _s166),
    ((3, 0), (3, 0)),
)

NESTED_XML_MAP_WITH_XML_NAME_INNER_MAP: StaticSchema = (
    17,
    n1,
    _s167,
    0,
    (_s27, _s28),
    ((3, {_s99: _s168}), (3, {_s99: _s169})),
)

NESTED_XML_MAP_WITH_XML_NAME_MAP: StaticSchema = (
    17,
    n1,
    _s170,
    0,
    (_s27, _s28),
    ((3, {_s99: _s171}), (NESTED_XML_MAP_WITH_XML_NAME_INNER_MAP, 0)),
)

NO_INPUT_AND_OUTPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s172,
    {_s30: _s173, _s87: None},
)

NO_INPUT_AND_OUTPUT_INPUT: StaticSchema = (
    18,
    n1,
    _s372,
    {_s30: _s245, _s32: None},
)

NO_INPUT_AND_OUTPUT: StaticOperationSchema = (
    23,
    n1,
    _s552,
    {_s514: MappingProxyType({"uri": "/NoInputAndOutputOutput", "method": "POST"})},
    NO_INPUT_AND_OUTPUT_INPUT,
    NO_INPUT_AND_OUTPUT_OUTPUT,
    (),
)

OMITS_NULL_SERIALIZES_EMPTY_STRING_INPUT: StaticSchema = (
    18,
    n1,
    _s174,
    {_s30: _s175, _s32: None},
    (_s176, _s178),
    ((3, {_s34: _s177}), (3, {_s34: _s179})),
)

OMITS_NULL_SERIALIZES_EMPTY_STRING_OUTPUT: StaticSchema = (
    18,
    n1,
    _s382,
    {_s30: _s245, _s87: None},
)

OMITS_NULL_SERIALIZES_EMPTY_STRING: StaticOperationSchema = (
    23,
    n1,
    _s555,
    {
        _s514: MappingProxyType(
            {"uri": "/OmitsNullSerializesEmptyString", "method": "GET"}
        )
    },
    OMITS_NULL_SERIALIZES_EMPTY_STRING_INPUT,
    OMITS_NULL_SERIALIZES_EMPTY_STRING_OUTPUT,
    (),
)

PAYLOAD_WITH_XML_NAMESPACE: StaticSchema = (
    18,
    n1,
    _s182,
    {_s103: MappingProxyType({"uri": "http://foo.com"})},
    (_s166,),
    ((3, 0),),
)

PAYLOAD_WITH_XML_NAMESPACE_AND_PREFIX: StaticSchema = (
    18,
    n1,
    _s183,
    {_s103: MappingProxyType({"uri": "http://foo.com", "prefix": "baz"})},
    (_s166,),
    ((3, 0),),
)

PUT_WITH_CONTENT_ENCODING_INPUT: StaticSchema = (
    18,
    n1,
    _s184,
    {_s30: _s185, _s32: None},
    (_s186, _s188),
    ((3, {_s72: _s187}), (3, 0)),
)

PUT_WITH_CONTENT_ENCODING_OUTPUT: StaticSchema = (
    18,
    n1,
    _s383,
    {_s30: _s245, _s87: None},
)

PUT_WITH_CONTENT_ENCODING: StaticOperationSchema = (
    23,
    n1,
    _s556,
    {
        _s514: MappingProxyType(
            {"method": "POST", "uri": "/requestcompression/putcontentwithencoding"}
        ),
        _s557: MappingProxyType({"encodings": ("gzip",)}),
    },
    PUT_WITH_CONTENT_ENCODING_INPUT,
    PUT_WITH_CONTENT_ENCODING_OUTPUT,
    (),
)

QUERY_IDEMPOTENCY_TOKEN_AUTO_FILL_INPUT: StaticSchema = (
    18,
    n1,
    _s189,
    {_s30: _s190, _s32: None},
    (_s191,),
    ((3, {_s34: _s191, _s192: None}),),
)

QUERY_IDEMPOTENCY_TOKEN_AUTO_FILL_OUTPUT: StaticSchema = (
    18,
    n1,
    _s384,
    {_s30: _s245, _s87: None},
)

QUERY_IDEMPOTENCY_TOKEN_AUTO_FILL: StaticOperationSchema = (
    23,
    n1,
    _s558,
    {
        _s514: MappingProxyType(
            {"uri": "/QueryIdempotencyTokenAutoFill", "method": "POST"}
        )
    },
    QUERY_IDEMPOTENCY_TOKEN_AUTO_FILL_INPUT,
    QUERY_IDEMPOTENCY_TOKEN_AUTO_FILL_OUTPUT,
    (),
)

STRING_LIST_MAP: StaticSchema = (
    17,
    n0,
    _s193,
    0,
    (_s27, _s28),
    ((3, 0), (STRING_LIST, 0)),
)

QUERY_PARAMS_AS_STRING_LIST_MAP_INPUT: StaticSchema = (
    18,
    n1,
    _s194,
    {_s30: _s195, _s32: None},
    (_s196, _s130),
    ((3, {_s34: _s197}), (STRING_LIST_MAP, 1024)),
)

QUERY_PARAMS_AS_STRING_LIST_MAP_OUTPUT: StaticSchema = (
    18,
    n1,
    _s385,
    {_s30: _s245, _s87: None},
)

QUERY_PARAMS_AS_STRING_LIST_MAP: StaticOperationSchema = (
    23,
    n1,
    _s559,
    {_s514: MappingProxyType({"uri": "/StringListMap", "method": "POST"})},
    QUERY_PARAMS_AS_STRING_LIST_MAP_INPUT,
    QUERY_PARAMS_AS_STRING_LIST_MAP_OUTPUT,
    (),
)
