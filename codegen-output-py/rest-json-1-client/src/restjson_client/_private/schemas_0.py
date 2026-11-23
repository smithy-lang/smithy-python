from types import MappingProxyType

from smithy_core._schema_compact import StaticOperationSchema, StaticSchema

from . import schemas

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
_s26 = "StringListMap"
_s27 = "key"
_s28 = "value"
n1 = "aws.protocoltests.restjson"
_s29 = "AllQueryStringTypesInput"
_s30 = "smithy.synthetic#originalShapeId"
_s31 = "aws.protocoltests.restjson#AllQueryStringTypesInput"
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
_s65 = "queryParamsMapOfStringList"
_s66 = "ClientOptionalDefaults"
_s67 = "smithy.api#clientOptional"
_s68 = "smithy.api#default"
_s69 = "ComplexNestedErrorData"
_s70 = "smithy.api#jsonName"
_s71 = "Fooooo"
_s72 = "ComplexError"
_s73 = "smithy.api#error"
_s74 = "client"
_s75 = "smithy.api#httpError"
_s76 = "Header"
_s77 = "smithy.api#httpHeader"
_s78 = "X-Header"
_s79 = "TopLevel"
_s80 = "Nested"
_s81 = "ConstantAndVariableQueryStringInput"
_s82 = "aws.protocoltests.restjson#ConstantAndVariableQueryStringInput"
_s83 = "baz"
_s84 = "maybeSet"
_s85 = "ConstantQueryStringInput"
_s86 = "aws.protocoltests.restjson#ConstantQueryStringInput"
_s87 = "hello"
_s88 = "ContentTypeParametersInput"
_s89 = "aws.protocoltests.restjson#ContentTypeParametersInput"
_s90 = "ContentTypeParametersOutput"
_s91 = "aws.protocoltests.restjson#ContentTypeParametersOutput"
_s92 = "smithy.api#output"
_s93 = "DateTime"
_s94 = "smithy.api#timestampFormat"
_s95 = "date-time"
_s96 = "DatetimeOffsetsOutput"
_s97 = "aws.protocoltests.restjson#DatetimeOffsetsOutput"
_s98 = "datetime"
_s99 = "TestStringList"
_s101 = "TestStringMap"
_s102 = "TestEnum"
_s103 = "TestIntEnum"
_s104 = "TWO"
_s105 = "Defaults"
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
_s137 = "DenseBooleanMap"
_s138 = "DenseNumberMap"
_s139 = "DenseSetMap"
_s140 = "DenseStringMap"
_s141 = "GreetingStruct"
_s142 = "DenseStructMap"
_s143 = "Farewell"
_s144 = "phrase"
_s145 = "bye"
_s146 = "Dialog"
_s147 = "language"
_s148 = "greeting"
_s149 = "farewell"
_s150 = "DialogList"
_s151 = "DialogMap"
_s152 = "DocumentValuedMap"
_s153 = "EmptyInputAndEmptyOutputInput"
_s154 = "aws.protocoltests.restjson#EmptyInputAndEmptyOutputInput"
_s155 = "EmptyInputAndEmptyOutputOutput"
_s156 = "aws.protocoltests.restjson#EmptyInputAndEmptyOutputOutput"
_s157 = "FooError"
_s158 = "server"
_s159 = "FractionalSecondsOutput"
_s160 = "aws.protocoltests.restjson#FractionalSecondsOutput"
_s161 = "GreetingWithErrorsOutput"
_s162 = "aws.protocoltests.restjson#GreetingWithErrorsOutput"
_s163 = "X-Greeting"
_s164 = "StringMap"
_s165 = "HttpEmptyPrefixHeadersInput"
_s166 = "aws.protocoltests.restjson#HttpEmptyPrefixHeadersInput"
_s167 = "prefixHeaders"
_s168 = "smithy.api#httpPrefixHeaders"
_s169 = "specificHeader"
_s170 = "HttpEmptyPrefixHeadersOutput"
_s171 = "aws.protocoltests.restjson#HttpEmptyPrefixHeadersOutput"
_s172 = "HttpPrefixHeadersInResponseInput"
_s173 = "aws.protocoltests.restjson#HttpPrefixHeadersInResponseInput"
_s174 = "HttpPrefixHeadersInResponseOutput"
_s175 = "aws.protocoltests.restjson#HttpPrefixHeadersInResponseOutput"
_s176 = "HttpPrefixHeadersInput"
_s177 = "aws.protocoltests.restjson#HttpPrefixHeadersInput"
_s178 = "foo"
_s179 = "x-foo"
_s180 = "fooMap"
_s181 = "x-foo-"
_s182 = "HttpPrefixHeadersOutput"
_s183 = "aws.protocoltests.restjson#HttpPrefixHeadersOutput"
_s184 = "HttpRequestWithFloatLabelsInput"
_s185 = "aws.protocoltests.restjson#HttpRequestWithFloatLabelsInput"
_s186 = "float"
_s187 = "double"
_s188 = "HttpRequestWithGreedyLabelInPathInput"
_s189 = "aws.protocoltests.restjson#HttpRequestWithGreedyLabelInPathInput"
_s190 = "EpochSeconds"
_s191 = "epoch-seconds"
_s192 = "HttpDate"
_s193 = "http-date"
_s194 = "HttpRequestWithLabelsAndTimestampFormatInput"
_s195 = "aws.protocoltests.restjson#HttpRequestWithLabelsAndTimestampFormatInput"
_s196 = "memberEpochSeconds"
_s197 = "smithy.api#httpLabel"
_s198 = "smithy.api#required"
_s199 = "memberHttpDate"
_s200 = "memberDateTime"
_s201 = "defaultFormat"
_s202 = "targetEpochSeconds"
_s203 = "targetHttpDate"
_s204 = "targetDateTime"
_s205 = "HttpRequestWithLabelsInput"
_s206 = "aws.protocoltests.restjson#HttpRequestWithLabelsInput"
_s207 = "string"
_s208 = "short"
_s209 = "integer"
_s210 = "long"
_s211 = "boolean"
_s212 = "timestamp"
_s213 = "HttpRequestWithRegexLiteralInput"
_s214 = "aws.protocoltests.restjson#HttpRequestWithRegexLiteralInput"
_s215 = "str"
_s216 = "HttpResponseCodeOutput"
_s217 = "aws.protocoltests.restjson#HttpResponseCodeOutput"
_s218 = "Status"
_s219 = "IgnoreQueryParamsInResponseOutput"
_s220 = "aws.protocoltests.restjson#IgnoreQueryParamsInResponseOutput"
_s221 = "InvalidGreeting"
_s222 = "Message"
_s223 = "JsonHeaderString"
_s224 = "smithy.api#mediaType"
_s225 = "application/json"
_s226 = "JsonValue"
_s227 = "MalformedAcceptWithGenericStringOutput"
_s228 = "aws.protocoltests.restjson#MalformedAcceptWithGenericStringOutput"
_s229 = "payload"
_s434 = "AllQueryStringTypesOutput"
_s435 = "smithy.api#Unit"
_s436 = "ConstantAndVariableQueryStringOutput"
_s437 = "ConstantQueryStringOutput"
_s438 = "DatetimeOffsetsInput"
_s456 = "FractionalSecondsInput"
_s457 = "GreetingWithErrorsInput"
_s484 = "HttpRequestWithFloatLabelsOutput"
_s485 = "HttpRequestWithGreedyLabelInPathOutput"
_s486 = "HttpRequestWithLabelsOutput"
_s487 = "HttpRequestWithLabelsAndTimestampFormatOutput"
_s488 = "HttpRequestWithRegexLiteralOutput"
_s489 = "HttpResponseCodeInput"
_s493 = "IgnoreQueryParamsInResponseInput"
_s592 = "MalformedAcceptWithGenericStringInput"
_s713 = "AllQueryStringTypes"
_s714 = "smithy.api#http"
_s715 = "ConstantAndVariableQueryString"
_s716 = "ConstantQueryString"
_s717 = "ContentTypeParameters"
_s718 = "DatetimeOffsets"
_s722 = "EmptyInputAndEmptyOutput"
_s726 = "FractionalSeconds"
_s727 = "GreetingWithErrors"
_s731 = "HttpEmptyPrefixHeaders"
_s737 = "HttpPrefixHeaders"
_s738 = "HttpPrefixHeadersInResponse"
_s740 = "HttpRequestWithFloatLabels"
_s741 = "HttpRequestWithGreedyLabelInPath"
_s742 = "HttpRequestWithLabels"
_s743 = "HttpRequestWithLabelsAndTimestampFormat"
_s744 = "HttpRequestWithRegexLiteral"
_s745 = "HttpResponseCode"
_s747 = "IgnoreQueryParamsInResponse"
_s757 = "MalformedAcceptWithGenericString"

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

STRING_LIST_MAP: StaticSchema = (
    17,
    n0,
    _s26,
    0,
    (_s27, _s28),
    ((3, 0), (STRING_LIST, 0)),
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
        (STRING_LIST_MAP, 1024),
    ),
)

ALL_QUERY_STRING_TYPES_OUTPUT: StaticSchema = (
    18,
    n1,
    _s434,
    {_s30: _s435, _s92: None},
)

ALL_QUERY_STRING_TYPES: StaticOperationSchema = (
    23,
    n1,
    _s713,
    {_s714: MappingProxyType({"uri": "/AllQueryStringTypesInput", "method": "GET"})},
    ALL_QUERY_STRING_TYPES_INPUT,
    ALL_QUERY_STRING_TYPES_OUTPUT,
    (),
)

CLIENT_OPTIONAL_DEFAULTS: StaticSchema = (
    18,
    n1,
    _s66,
    0,
    (_s1,),
    ((7, {_s67: None, _s68: 0}),),
)

COMPLEX_NESTED_ERROR_DATA: StaticSchema = (
    18,
    n1,
    _s69,
    0,
    (_s11,),
    ((3, {_s70: _s71}),),
)

COMPLEX_ERROR: StaticSchema = (
    18,
    n1,
    _s72,
    {_s73: _s74, _s75: 403},
    (_s76, _s79, _s80),
    ((3, {_s77: _s78}), (3, 0), (COMPLEX_NESTED_ERROR_DATA, 0)),
)

CONSTANT_AND_VARIABLE_QUERY_STRING_INPUT: StaticSchema = (
    18,
    n1,
    _s81,
    {_s30: _s82, _s32: None},
    (_s83, _s84),
    ((3, {_s34: _s83}), (3, {_s34: _s84})),
)

CONSTANT_AND_VARIABLE_QUERY_STRING_OUTPUT: StaticSchema = (
    18,
    n1,
    _s436,
    {_s30: _s435, _s92: None},
)

CONSTANT_AND_VARIABLE_QUERY_STRING: StaticOperationSchema = (
    23,
    n1,
    _s715,
    {
        _s714: MappingProxyType(
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
    _s85,
    {_s30: _s86, _s32: None},
    (_s87,),
    ((3, 9),),
)

CONSTANT_QUERY_STRING_OUTPUT: StaticSchema = (
    18,
    n1,
    _s437,
    {_s30: _s435, _s92: None},
)

CONSTANT_QUERY_STRING: StaticOperationSchema = (
    23,
    n1,
    _s716,
    {
        _s714: MappingProxyType(
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
    _s88,
    {_s30: _s89, _s32: None},
    (_s28,),
    ((7, 0),),
)

CONTENT_TYPE_PARAMETERS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s90,
    {_s30: _s91, _s92: None},
)

CONTENT_TYPE_PARAMETERS: StaticOperationSchema = (
    23,
    n1,
    _s717,
    {_s714: MappingProxyType({"uri": "/ContentTypeParameters", "method": "POST"})},
    CONTENT_TYPE_PARAMETERS_INPUT,
    CONTENT_TYPE_PARAMETERS_OUTPUT,
    (),
)

DATE_TIME: StaticSchema = (
    4,
    n0,
    _s93,
    {_s94: _s95},
)

DATETIME_OFFSETS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s96,
    {_s30: _s97, _s92: None},
    (_s98,),
    ((DATE_TIME, 0),),
)

DATETIME_OFFSETS_INPUT: StaticSchema = (
    18,
    n1,
    _s438,
    {_s30: _s435, _s32: None},
)

DATETIME_OFFSETS: StaticOperationSchema = (
    23,
    n1,
    _s718,
    {_s714: MappingProxyType({"uri": "/DatetimeOffsets", "method": "POST"})},
    DATETIME_OFFSETS_INPUT,
    DATETIME_OFFSETS_OUTPUT,
    (),
)

TEST_STRING_LIST: StaticSchema = (
    16,
    n1,
    _s99,
    0,
    (_s1,),
    ((3, 0),),
)

TEST_STRING_MAP: StaticSchema = (
    17,
    n1,
    _s101,
    0,
    (_s27, _s28),
    ((3, 0), (3, 0)),
)

TEST_ENUM: StaticSchema = (
    14,
    n1,
    _s102,
    0,
    (_s9, _s14, _s12),
    ((-1, {_s10: _s9}), (-1, {_s10: _s14}), (-1, {_s10: _s12})),
)

TEST_INT_ENUM: StaticSchema = (
    15,
    n1,
    _s103,
    0,
    (_s16, _s104),
    ((-1, {_s10: 1}), (-1, {_s10: 2})),
)

DEFAULTS: StaticSchema = (
    18,
    n1,
    _s105,
    0,
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
        (TEST_STRING_LIST, {_s68: ()}),
        (lambda: schemas.DOCUMENT, {_s68: MappingProxyType[str, object]({})}),
        (lambda: schemas.DOCUMENT, {_s68: _s107}),
        (lambda: schemas.DOCUMENT, {_s68: True}),
        (lambda: schemas.DOCUMENT, {_s68: ()}),
        (lambda: schemas.DOCUMENT, {_s68: None}),
        (4, {_s68: 0}),
        (1, {_s68: _s117}),
        (5, {_s68: 1}),
        (6, {_s68: 1}),
        (7, {_s68: 10}),
        (8, {_s68: 100}),
        (9, {_s68: 1.0}),
        (10, {_s68: 1.0}),
        (TEST_STRING_MAP, {_s68: MappingProxyType[str, object]({})}),
        (TEST_ENUM, {_s68: _s9}),
        (TEST_INT_ENUM, {_s68: 1}),
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

DENSE_BOOLEAN_MAP: StaticSchema = (
    17,
    n1,
    _s137,
    0,
    (_s27, _s28),
    ((3, 0), (2, 0)),
)

DENSE_NUMBER_MAP: StaticSchema = (
    17,
    n1,
    _s138,
    0,
    (_s27, _s28),
    ((3, 0), (7, 0)),
)

DENSE_SET_MAP: StaticSchema = (
    17,
    n1,
    _s139,
    0,
    (_s27, _s28),
    ((3, 0), (STRING_SET, 0)),
)

DENSE_STRING_MAP: StaticSchema = (
    17,
    n1,
    _s140,
    0,
    (_s27, _s28),
    ((3, 0), (3, 0)),
)

GREETING_STRUCT: StaticSchema = (
    18,
    n0,
    _s141,
    0,
    (_s107,),
    ((3, 0),),
)

DENSE_STRUCT_MAP: StaticSchema = (
    17,
    n1,
    _s142,
    0,
    (_s27, _s28),
    ((3, 0), (GREETING_STRUCT, 0)),
)

FAREWELL: StaticSchema = (
    18,
    n1,
    _s143,
    0,
    (_s144,),
    ((3, {_s68: _s145}),),
)

DIALOG: StaticSchema = (
    18,
    n1,
    _s146,
    0,
    (_s147, _s148, _s149),
    ((3, 0), (3, {_s68: _s107}), (FAREWELL, 0)),
)

DIALOG_LIST: StaticSchema = (
    16,
    n1,
    _s150,
    0,
    (_s1,),
    ((DIALOG, 0),),
)

DIALOG_MAP: StaticSchema = (
    17,
    n1,
    _s151,
    0,
    (_s27, _s28),
    ((3, 0), (DIALOG, 0)),
)

DOCUMENT_VALUED_MAP: StaticSchema = (
    17,
    n1,
    _s152,
    0,
    (_s27, _s28),
    ((3, 0), (lambda: schemas.DOCUMENT, 0)),
)

EMPTY_INPUT_AND_EMPTY_OUTPUT_INPUT: StaticSchema = (
    18,
    n1,
    _s153,
    {_s30: _s154, _s32: None},
)

EMPTY_INPUT_AND_EMPTY_OUTPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s155,
    {_s30: _s156, _s92: None},
)

EMPTY_INPUT_AND_EMPTY_OUTPUT: StaticOperationSchema = (
    23,
    n1,
    _s722,
    {_s714: MappingProxyType({"uri": "/EmptyInputAndEmptyOutput", "method": "POST"})},
    EMPTY_INPUT_AND_EMPTY_OUTPUT_INPUT,
    EMPTY_INPUT_AND_EMPTY_OUTPUT_OUTPUT,
    (),
)

FOO_ERROR: StaticSchema = (
    18,
    n1,
    _s157,
    {_s73: _s158, _s75: 500},
)

FRACTIONAL_SECONDS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s159,
    {_s30: _s160, _s92: None},
    (_s98,),
    ((DATE_TIME, 0),),
)

FRACTIONAL_SECONDS_INPUT: StaticSchema = (
    18,
    n1,
    _s456,
    {_s30: _s435, _s32: None},
)

FRACTIONAL_SECONDS: StaticOperationSchema = (
    23,
    n1,
    _s726,
    {_s714: MappingProxyType({"uri": "/FractionalSeconds", "method": "POST"})},
    FRACTIONAL_SECONDS_INPUT,
    FRACTIONAL_SECONDS_OUTPUT,
    (),
)

GREETING_WITH_ERRORS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s161,
    {_s30: _s162, _s92: None},
    (_s148,),
    ((3, {_s77: _s163}),),
)

GREETING_WITH_ERRORS_INPUT: StaticSchema = (
    18,
    n1,
    _s457,
    {_s30: _s435, _s32: None},
)

GREETING_WITH_ERRORS: StaticOperationSchema = (
    23,
    n1,
    _s727,
    {_s714: MappingProxyType({"uri": "/GreetingWithErrors", "method": "PUT"})},
    GREETING_WITH_ERRORS_INPUT,
    GREETING_WITH_ERRORS_OUTPUT,
    (COMPLEX_ERROR, FOO_ERROR, lambda: INVALID_GREETING),
)

STRING_MAP: StaticSchema = (
    17,
    n0,
    _s164,
    0,
    (_s27, _s28),
    ((3, 0), (3, 0)),
)

HTTP_EMPTY_PREFIX_HEADERS_INPUT: StaticSchema = (
    18,
    n1,
    _s165,
    {_s30: _s166, _s32: None},
    (_s167, _s169),
    ((STRING_MAP, {_s168: _s128}), (3, {_s77: _s87})),
)

HTTP_EMPTY_PREFIX_HEADERS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s170,
    {_s30: _s171, _s92: None},
    (_s167, _s169),
    ((STRING_MAP, {_s168: _s128}), (3, {_s77: _s87})),
)

HTTP_EMPTY_PREFIX_HEADERS: StaticOperationSchema = (
    23,
    n1,
    _s731,
    {_s714: MappingProxyType({"uri": "/HttpEmptyPrefixHeaders", "method": "GET"})},
    HTTP_EMPTY_PREFIX_HEADERS_INPUT,
    HTTP_EMPTY_PREFIX_HEADERS_OUTPUT,
    (),
)

HTTP_PREFIX_HEADERS_IN_RESPONSE_INPUT: StaticSchema = (
    18,
    n1,
    _s172,
    {_s30: _s173, _s32: None},
)

HTTP_PREFIX_HEADERS_IN_RESPONSE_OUTPUT: StaticSchema = (
    18,
    n1,
    _s174,
    {_s30: _s175, _s92: None},
    (_s167,),
    ((STRING_MAP, {_s168: _s128}),),
)

HTTP_PREFIX_HEADERS_IN_RESPONSE: StaticOperationSchema = (
    23,
    n1,
    _s738,
    {_s714: MappingProxyType({"uri": "/HttpPrefixHeadersResponse", "method": "GET"})},
    HTTP_PREFIX_HEADERS_IN_RESPONSE_INPUT,
    HTTP_PREFIX_HEADERS_IN_RESPONSE_OUTPUT,
    (),
)

HTTP_PREFIX_HEADERS_INPUT: StaticSchema = (
    18,
    n1,
    _s176,
    {_s30: _s177, _s32: None},
    (_s178, _s180),
    ((3, {_s77: _s179}), (STRING_MAP, {_s168: _s181})),
)

HTTP_PREFIX_HEADERS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s182,
    {_s30: _s183, _s92: None},
    (_s178, _s180),
    ((3, {_s77: _s179}), (STRING_MAP, {_s168: _s181})),
)

HTTP_PREFIX_HEADERS: StaticOperationSchema = (
    23,
    n1,
    _s737,
    {_s714: MappingProxyType({"uri": "/HttpPrefixHeaders", "method": "GET"})},
    HTTP_PREFIX_HEADERS_INPUT,
    HTTP_PREFIX_HEADERS_OUTPUT,
    (),
)

HTTP_REQUEST_WITH_FLOAT_LABELS_INPUT: StaticSchema = (
    18,
    n1,
    _s184,
    {_s30: _s185, _s32: None},
    (_s186, _s187),
    ((9, 9), (10, 9)),
)

HTTP_REQUEST_WITH_FLOAT_LABELS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s484,
    {_s30: _s435, _s92: None},
)

HTTP_REQUEST_WITH_FLOAT_LABELS: StaticOperationSchema = (
    23,
    n1,
    _s740,
    {
        _s714: MappingProxyType(
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
    _s188,
    {_s30: _s189, _s32: None},
    (_s178, _s83),
    ((3, 9), (3, 9)),
)

HTTP_REQUEST_WITH_GREEDY_LABEL_IN_PATH_OUTPUT: StaticSchema = (
    18,
    n1,
    _s485,
    {_s30: _s435, _s92: None},
)

HTTP_REQUEST_WITH_GREEDY_LABEL_IN_PATH: StaticOperationSchema = (
    23,
    n1,
    _s741,
    {
        _s714: MappingProxyType(
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
    _s190,
    {_s94: _s191},
)

HTTP_DATE: StaticSchema = (
    4,
    n0,
    _s192,
    {_s94: _s193},
)

HTTP_REQUEST_WITH_LABELS_AND_TIMESTAMP_FORMAT_INPUT: StaticSchema = (
    18,
    n1,
    _s194,
    {_s30: _s195, _s32: None},
    (_s196, _s199, _s200, _s201, _s202, _s203, _s204),
    (
        (4, {_s94: _s191, _s197: None, _s198: None}),
        (4, {_s94: _s193, _s197: None, _s198: None}),
        (4, {_s94: _s95, _s197: None, _s198: None}),
        (4, 9),
        (EPOCH_SECONDS, 9),
        (HTTP_DATE, 9),
        (DATE_TIME, 9),
    ),
)

HTTP_REQUEST_WITH_LABELS_AND_TIMESTAMP_FORMAT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s487,
    {_s30: _s435, _s92: None},
)

HTTP_REQUEST_WITH_LABELS_AND_TIMESTAMP_FORMAT: StaticOperationSchema = (
    23,
    n1,
    _s743,
    {
        _s714: MappingProxyType(
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
    _s205,
    {_s30: _s206, _s32: None},
    (_s207, _s208, _s209, _s210, _s186, _s187, _s211, _s212),
    ((3, 9), (6, 9), (7, 9), (8, 9), (9, 9), (10, 9), (2, 9), (4, 9)),
)

HTTP_REQUEST_WITH_LABELS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s486,
    {_s30: _s435, _s92: None},
)

HTTP_REQUEST_WITH_LABELS: StaticOperationSchema = (
    23,
    n1,
    _s742,
    {
        _s714: MappingProxyType(
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

HTTP_REQUEST_WITH_REGEX_LITERAL_INPUT: StaticSchema = (
    18,
    n1,
    _s213,
    {_s30: _s214, _s32: None},
    (_s215,),
    ((3, 9),),
)

HTTP_REQUEST_WITH_REGEX_LITERAL_OUTPUT: StaticSchema = (
    18,
    n1,
    _s488,
    {_s30: _s435, _s92: None},
)

HTTP_REQUEST_WITH_REGEX_LITERAL: StaticOperationSchema = (
    23,
    n1,
    _s744,
    {_s714: MappingProxyType({"method": "GET", "uri": "/ReDosLiteral/{str}/(a+)+"})},
    HTTP_REQUEST_WITH_REGEX_LITERAL_INPUT,
    HTTP_REQUEST_WITH_REGEX_LITERAL_OUTPUT,
    (),
)

HTTP_RESPONSE_CODE_OUTPUT: StaticSchema = (
    18,
    n1,
    _s216,
    {_s30: _s217, _s92: None},
    (_s218,),
    ((7, 128),),
)

HTTP_RESPONSE_CODE_INPUT: StaticSchema = (
    18,
    n1,
    _s489,
    {_s30: _s435, _s32: None},
)

HTTP_RESPONSE_CODE: StaticOperationSchema = (
    23,
    n1,
    _s745,
    {_s714: MappingProxyType({"uri": "/HttpResponseCode", "method": "PUT"})},
    HTTP_RESPONSE_CODE_INPUT,
    HTTP_RESPONSE_CODE_OUTPUT,
    (),
)

IGNORE_QUERY_PARAMS_IN_RESPONSE_OUTPUT: StaticSchema = (
    18,
    n1,
    _s219,
    {_s30: _s220, _s92: None},
    (_s83,),
    ((3, {_s34: _s83}),),
)

IGNORE_QUERY_PARAMS_IN_RESPONSE_INPUT: StaticSchema = (
    18,
    n1,
    _s493,
    {_s30: _s435, _s32: None},
)

IGNORE_QUERY_PARAMS_IN_RESPONSE: StaticOperationSchema = (
    23,
    n1,
    _s747,
    {_s714: MappingProxyType({"uri": "/IgnoreQueryParamsInResponse", "method": "GET"})},
    IGNORE_QUERY_PARAMS_IN_RESPONSE_INPUT,
    IGNORE_QUERY_PARAMS_IN_RESPONSE_OUTPUT,
    (),
)

INVALID_GREETING: StaticSchema = (
    18,
    n1,
    _s221,
    {_s73: _s74, _s75: 400},
    (_s222,),
    ((3, 0),),
)

JSON_HEADER_STRING: StaticSchema = (
    3,
    n1,
    _s223,
    {_s224: _s225},
)

JSON_VALUE: StaticSchema = (
    3,
    n1,
    _s226,
    {_s224: _s225},
)

MALFORMED_ACCEPT_WITH_GENERIC_STRING_OUTPUT: StaticSchema = (
    18,
    n1,
    _s227,
    {_s30: _s228, _s92: None},
    (_s229,),
    ((3, 16),),
)

MALFORMED_ACCEPT_WITH_GENERIC_STRING_INPUT: StaticSchema = (
    18,
    n1,
    _s592,
    {_s30: _s435, _s32: None},
)

MALFORMED_ACCEPT_WITH_GENERIC_STRING: StaticOperationSchema = (
    23,
    n1,
    _s757,
    {
        _s714: MappingProxyType(
            {"method": "POST", "uri": "/MalformedAcceptWithGenericString"}
        )
    },
    MALFORMED_ACCEPT_WITH_GENERIC_STRING_INPUT,
    MALFORMED_ACCEPT_WITH_GENERIC_STRING_OUTPUT,
    (),
)
