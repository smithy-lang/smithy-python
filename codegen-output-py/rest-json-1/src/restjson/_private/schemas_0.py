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
_s26 = "StringListMap"
_s27 = "key"
_s28 = "value"
n1 = "aws.protocoltests.restjson"
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
_s63 = "queryParamsMapOfStringList"
_s64 = "BlobPayloadEvent"
_s65 = "payload"
_s66 = "smithy.api#eventPayload"
_s67 = "ClientOptionalDefaults"
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
_s82 = "baz"
_s83 = "maybeSet"
_s84 = "ConstantQueryStringInput"
_s85 = "hello"
_s86 = "ContentTypeParametersInput"
_s87 = "ContentTypeParametersOutput"
_s88 = "smithy.api#output"
_s89 = "DateTime"
_s90 = "smithy.api#timestampFormat"
_s91 = "date-time"
_s92 = "DatetimeOffsetsOutput"
_s93 = "datetime"
_s94 = "TestStringList"
_s95 = "Document"
_s96 = "TestStringMap"
_s97 = "TestEnum"
_s98 = "TestIntEnum"
_s99 = "TWO"
_s100 = "Defaults"
_s101 = "defaultString"
_s102 = "hi"
_s103 = "defaultBoolean"
_s104 = "defaultList"
_s105 = "defaultDocumentMap"
_s106 = "defaultDocumentString"
_s107 = "defaultDocumentBoolean"
_s108 = "defaultDocumentList"
_s109 = "defaultNullDocument"
_s110 = "defaultTimestamp"
_s111 = "defaultBlob"
_s112 = "YWJj"
_s113 = "defaultByte"
_s114 = "defaultShort"
_s115 = "defaultInteger"
_s116 = "defaultLong"
_s117 = "defaultFloat"
_s118 = "defaultDouble"
_s119 = "defaultMap"
_s120 = "defaultEnum"
_s121 = "defaultIntEnum"
_s122 = "emptyString"
_s123 = ""
_s124 = "falseBoolean"
_s125 = "emptyBlob"
_s126 = "zeroByte"
_s127 = "zeroShort"
_s128 = "zeroInteger"
_s129 = "zeroLong"
_s130 = "zeroFloat"
_s131 = "zeroDouble"
_s132 = "DenseBooleanMap"
_s133 = "DenseNumberMap"
_s134 = "DenseSetMap"
_s135 = "DenseStringMap"
_s136 = "GreetingStruct"
_s137 = "DenseStructMap"
_s138 = "Farewell"
_s139 = "phrase"
_s140 = "bye"
_s141 = "Dialog"
_s142 = "language"
_s143 = "greeting"
_s144 = "farewell"
_s145 = "DialogList"
_s146 = "DialogMap"
_s147 = "DocumentValuedMap"
_s148 = "DocumentTypeAsMapValueInputOutput"
_s149 = "docValuedMap"
_s150 = "DocumentTypeAsPayloadInputOutput"
_s151 = "documentValue"
_s152 = "DocumentTypeInputOutput"
_s153 = "stringValue"
_s154 = "HeadersEvent"
_s155 = "booleanHeader"
_s156 = "smithy.api#eventHeader"
_s157 = "byteHeader"
_s158 = "shortHeader"
_s159 = "intHeader"
_s160 = "longHeader"
_s161 = "blobHeader"
_s162 = "stringHeader"
_s163 = "timestampHeader"
_s164 = "StringPayloadEvent"
_s165 = "PayloadStructure"
_s166 = "structureMember"
_s167 = "StructurePayloadEvent"
_s168 = "PayloadUnion"
_s169 = "unionMember"
_s170 = "UnionPayloadEvent"
_s171 = "HeadersAndExplicitPayloadEvent"
_s172 = "header"
_s173 = "HeadersAndImplicitPayloadEvent"
_s174 = "ErrorEvent"
_s175 = "message"
_s176 = "EventStream"
_s177 = "smithy.api#streaming"
_s178 = "headers"
_s179 = "blobPayload"
_s180 = "stringPayload"
_s181 = "structurePayload"
_s182 = "unionPayload"
_s183 = "headersAndExplicitPayload"
_s184 = "headersAndImplicitPayload"
_s185 = "error"
_s186 = "DuplexStreamInput"
_s187 = "stream"
_s188 = "DuplexStreamOutput"
_s189 = "DuplexStreamWithDistinctStreamsInput"
_s190 = "SingletonEvent"
_s191 = "SingletonEventStream"
_s192 = "singleton"
_s193 = "DuplexStreamWithDistinctStreamsOutput"
_s194 = "DuplexStreamWithInitialMessagesInput"
_s195 = "initialRequestMember"
_s196 = "initial-request-member"
_s197 = "smithy.api#required"
_s198 = "DuplexStreamWithInitialMessagesOutput"
_s199 = "initialResponseMember"
_s200 = "initial-response-member"
_s201 = "EmptyInputAndEmptyOutputInput"
_s202 = "EmptyInputAndEmptyOutputOutput"
_s203 = "StringEnum"
_s204 = "V"
_s205 = "enumvalue"
_s206 = "EnumPayloadInput"
_s207 = "FiniteStreamingBlob"
_s208 = "smithy.api#requiresLength"
_s209 = "FooError"
_s210 = "server"
_s211 = "FractionalSecondsOutput"
_s212 = "GreetingWithErrorsOutput"
_s213 = "X-Greeting"
_s214 = "HostLabelInput"
_s215 = "label"
_s216 = "HttpChecksumRequiredInputOutput"
_s217 = "foo"
_s218 = "StringMap"
_s219 = "HttpEmptyPrefixHeadersInput"
_s220 = "prefixHeaders"
_s221 = "smithy.api#httpPrefixHeaders"
_s222 = "specificHeader"
_s223 = "HttpEmptyPrefixHeadersOutput"
_s224 = "HttpPayloadTraitsInputOutput"
_s225 = "X-Foo"
_s226 = "blob"
_s227 = "TextPlainBlob"
_s228 = "smithy.api#mediaType"
_s229 = "text/plain"
_s341 = "a"
_s342 = "b"
_s457 = "NullAndEmptyHeadersIO"
_s458 = "X-A"
_s459 = "X-B"
_s460 = "c"
_s461 = "X-C"
_s506 = "ServiceUnavailableError"

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

STRING_LIST_MAP: StaticSchema = (
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
        (STRING_LIST, 0),
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
        (STRING_LIST_MAP, 1024),
    ),
)

BLOB_PAYLOAD_EVENT: StaticSchema = (
    18,
    n1,
    _s64,
    0,
    (_s65,),
    ((1, {_s66: None}),),
)

CLIENT_OPTIONAL_DEFAULTS: StaticSchema = (
    18,
    n1,
    _s67,
    0,
    (_s1,),
    ((7, {_s68: 0}),),
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
    (
        _s76,
        _s79,
        _s80,
    ),
    (
        (3, {_s77: _s78}),
        (3, 0),
        (COMPLEX_NESTED_ERROR_DATA, 0),
    ),
)

CONSTANT_AND_VARIABLE_QUERY_STRING_INPUT: StaticSchema = (
    18,
    n1,
    _s81,
    {_s30: None},
    (
        _s82,
        _s83,
    ),
    (
        (3, {_s32: _s82}),
        (3, {_s32: _s83}),
    ),
)

CONSTANT_QUERY_STRING_INPUT: StaticSchema = (
    18,
    n1,
    _s84,
    {_s30: None},
    (_s85,),
    ((3, 9),),
)

CONTENT_TYPE_PARAMETERS_INPUT: StaticSchema = (
    18,
    n1,
    _s86,
    {_s30: None},
    (_s28,),
    ((7, 0),),
)

CONTENT_TYPE_PARAMETERS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s87,
    {_s88: None},
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
    {_s88: None},
    (_s93,),
    ((DATE_TIME, 0),),
)

TEST_STRING_LIST: StaticSchema = (
    16,
    n1,
    _s94,
    0,
    (_s1,),
    ((3, 0),),
)

DOCUMENT: StaticSchema = (
    13,
    n1,
    _s95,
    0,
)

TEST_STRING_MAP: StaticSchema = (
    17,
    n1,
    _s96,
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

TEST_ENUM: StaticSchema = (
    14,
    n1,
    _s97,
    0,
    (
        _s9,
        _s14,
        _s12,
    ),
    (
        (-1, {_s10: _s9}),
        (-1, {_s10: _s14}),
        (-1, {_s10: _s12}),
    ),
)

TEST_INT_ENUM: StaticSchema = (
    15,
    n1,
    _s98,
    0,
    (
        _s16,
        _s99,
    ),
    (
        (-1, {_s10: 1}),
        (-1, {_s10: 2}),
    ),
)

DEFAULTS: StaticSchema = (
    18,
    n1,
    _s100,
    0,
    (
        _s101,
        _s103,
        _s104,
        _s105,
        _s106,
        _s107,
        _s108,
        _s109,
        _s110,
        _s111,
        _s113,
        _s114,
        _s115,
        _s116,
        _s117,
        _s118,
        _s119,
        _s120,
        _s121,
        _s122,
        _s124,
        _s125,
        _s126,
        _s127,
        _s128,
        _s129,
        _s130,
        _s131,
    ),
    (
        (3, {_s68: _s102}),
        (2, {_s68: True}),
        (TEST_STRING_LIST, {_s68: ()}),
        (DOCUMENT, {_s68: MappingProxyType[str, object]({})}),
        (DOCUMENT, {_s68: _s102}),
        (DOCUMENT, {_s68: True}),
        (DOCUMENT, {_s68: ()}),
        (DOCUMENT, {_s68: None}),
        (4, {_s68: 0}),
        (1, {_s68: _s112}),
        (5, {_s68: 1}),
        (6, {_s68: 1}),
        (7, {_s68: 10}),
        (8, {_s68: 100}),
        (9, {_s68: 1.0}),
        (10, {_s68: 1.0}),
        (TEST_STRING_MAP, {_s68: MappingProxyType[str, object]({})}),
        (TEST_ENUM, {_s68: _s9}),
        (TEST_INT_ENUM, {_s68: 1}),
        (3, {_s68: _s123}),
        (2, {_s68: False}),
        (1, {_s68: _s123}),
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
    _s132,
    0,
    (
        _s27,
        _s28,
    ),
    (
        (3, 0),
        (2, 0),
    ),
)

DENSE_NUMBER_MAP: StaticSchema = (
    17,
    n1,
    _s133,
    0,
    (
        _s27,
        _s28,
    ),
    (
        (3, 0),
        (7, 0),
    ),
)

DENSE_SET_MAP: StaticSchema = (
    17,
    n1,
    _s134,
    0,
    (
        _s27,
        _s28,
    ),
    (
        (3, 0),
        (STRING_SET, 0),
    ),
)

DENSE_STRING_MAP: StaticSchema = (
    17,
    n1,
    _s135,
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

GREETING_STRUCT: StaticSchema = (
    18,
    n0,
    _s136,
    {_s30: None, _s88: None},
    (_s102,),
    ((3, 0),),
)

DENSE_STRUCT_MAP: StaticSchema = (
    17,
    n1,
    _s137,
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

FAREWELL: StaticSchema = (
    18,
    n1,
    _s138,
    0,
    (_s139,),
    ((3, {_s68: _s140}),),
)

DIALOG: StaticSchema = (
    18,
    n1,
    _s141,
    0,
    (
        _s142,
        _s143,
        _s144,
    ),
    (
        (3, 0),
        (3, {_s68: _s102}),
        (FAREWELL, 0),
    ),
)

DIALOG_LIST: StaticSchema = (
    16,
    n1,
    _s145,
    0,
    (_s1,),
    ((DIALOG, 0),),
)

DIALOG_MAP: StaticSchema = (
    17,
    n1,
    _s146,
    0,
    (
        _s27,
        _s28,
    ),
    (
        (3, 0),
        (DIALOG, 0),
    ),
)

DOCUMENT_VALUED_MAP: StaticSchema = (
    17,
    n1,
    _s147,
    0,
    (
        _s27,
        _s28,
    ),
    (
        (3, 0),
        (DOCUMENT, 0),
    ),
)

DOCUMENT_TYPE_AS_MAP_VALUE_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s148,
    {_s30: None, _s88: None},
    (_s149,),
    ((DOCUMENT_VALUED_MAP, 0),),
)

DOCUMENT_TYPE_AS_PAYLOAD_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s150,
    {_s30: None, _s88: None},
    (_s151,),
    ((DOCUMENT, 16),),
)

DOCUMENT_TYPE_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s152,
    {_s30: None, _s88: None},
    (
        _s153,
        _s151,
    ),
    (
        (3, 0),
        (DOCUMENT, 0),
    ),
)

HEADERS_EVENT: StaticSchema = (
    18,
    n1,
    _s154,
    0,
    (
        _s155,
        _s157,
        _s158,
        _s159,
        _s160,
        _s161,
        _s162,
        _s163,
    ),
    (
        (2, {_s156: None}),
        (5, {_s156: None}),
        (6, {_s156: None}),
        (7, {_s156: None}),
        (8, {_s156: None}),
        (1, {_s156: None}),
        (3, {_s156: None}),
        (DATE_TIME, {_s156: None}),
    ),
)

STRING_PAYLOAD_EVENT: StaticSchema = (
    18,
    n1,
    _s164,
    0,
    (_s65,),
    ((3, {_s66: None}),),
)

PAYLOAD_STRUCTURE: StaticSchema = (
    18,
    n1,
    _s165,
    0,
    (_s166,),
    ((3, 0),),
)

STRUCTURE_PAYLOAD_EVENT: StaticSchema = (
    18,
    n1,
    _s167,
    0,
    (_s65,),
    ((PAYLOAD_STRUCTURE, {_s66: None}),),
)

PAYLOAD_UNION: StaticSchema = (
    19,
    n1,
    _s168,
    0,
    (_s169,),
    ((3, 0),),
)

UNION_PAYLOAD_EVENT: StaticSchema = (
    18,
    n1,
    _s170,
    0,
    (_s65,),
    ((PAYLOAD_UNION, {_s66: None}),),
)

HEADERS_AND_EXPLICIT_PAYLOAD_EVENT: StaticSchema = (
    18,
    n1,
    _s171,
    0,
    (
        _s172,
        _s65,
    ),
    (
        (3, {_s156: None}),
        (PAYLOAD_STRUCTURE, {_s66: None}),
    ),
)

HEADERS_AND_IMPLICIT_PAYLOAD_EVENT: StaticSchema = (
    18,
    n1,
    _s173,
    0,
    (
        _s172,
        _s65,
    ),
    (
        (3, {_s156: None}),
        (3, 0),
    ),
)

ERROR_EVENT: StaticSchema = (
    18,
    n1,
    _s174,
    {_s73: _s74},
    (_s175,),
    ((3, 0),),
)

EVENT_STREAM: StaticSchema = (
    19,
    n1,
    _s176,
    {_s177: None},
    (
        _s178,
        _s179,
        _s180,
        _s181,
        _s182,
        _s183,
        _s184,
        _s185,
    ),
    (
        (HEADERS_EVENT, 0),
        (BLOB_PAYLOAD_EVENT, 0),
        (STRING_PAYLOAD_EVENT, 0),
        (STRUCTURE_PAYLOAD_EVENT, 0),
        (UNION_PAYLOAD_EVENT, 0),
        (HEADERS_AND_EXPLICIT_PAYLOAD_EVENT, 0),
        (HEADERS_AND_IMPLICIT_PAYLOAD_EVENT, 0),
        (ERROR_EVENT, 0),
    ),
)

DUPLEX_STREAM_INPUT: StaticSchema = (
    18,
    n1,
    _s186,
    {_s30: None},
    (_s187,),
    ((EVENT_STREAM, 16),),
)

DUPLEX_STREAM_OUTPUT: StaticSchema = (
    18,
    n1,
    _s188,
    {_s88: None},
    (_s187,),
    ((EVENT_STREAM, 16),),
)

DUPLEX_STREAM_WITH_DISTINCT_STREAMS_INPUT: StaticSchema = (
    18,
    n1,
    _s189,
    {_s30: None},
    (_s187,),
    ((EVENT_STREAM, 16),),
)

DUPLEX_STREAM_WITH_DISTINCT_STREAMS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s193,
    {_s88: None},
    (_s187,),
    ((lambda: SINGLETON_EVENT_STREAM, 16),),
)

SINGLETON_EVENT: StaticSchema = (
    18,
    n1,
    _s190,
    0,
    (_s28,),
    ((3, 0),),
)

SINGLETON_EVENT_STREAM: StaticSchema = (
    19,
    n1,
    _s191,
    0,
    (_s192,),
    ((SINGLETON_EVENT, 0),),
)

DUPLEX_STREAM_WITH_INITIAL_MESSAGES_INPUT: StaticSchema = (
    18,
    n1,
    _s194,
    {_s30: None},
    (
        _s195,
        _s187,
    ),
    (
        (3, {_s77: _s196, _s197: None}),
        (EVENT_STREAM, 16),
    ),
)

DUPLEX_STREAM_WITH_INITIAL_MESSAGES_OUTPUT: StaticSchema = (
    18,
    n1,
    _s198,
    {_s88: None},
    (
        _s199,
        _s187,
    ),
    (
        (3, {_s77: _s200, _s197: None}),
        (EVENT_STREAM, 16),
    ),
)

EMPTY_INPUT_AND_EMPTY_OUTPUT_INPUT: StaticSchema = (
    18,
    n1,
    _s201,
    {_s30: None},
)

EMPTY_INPUT_AND_EMPTY_OUTPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s202,
    {_s88: None},
)

STRING_ENUM: StaticSchema = (
    14,
    n1,
    _s203,
    0,
    (_s204,),
    ((-1, {_s10: _s205}),),
)

ENUM_PAYLOAD_INPUT: StaticSchema = (
    18,
    n1,
    _s206,
    {_s30: None, _s88: None},
    (_s65,),
    ((STRING_ENUM, 16),),
)

FINITE_STREAMING_BLOB: StaticSchema = (
    1,
    n1,
    _s207,
    {_s177: None, _s208: None},
)

FOO_ERROR: StaticSchema = (
    18,
    n1,
    _s209,
    {_s73: _s210, _s75: 500},
)

FRACTIONAL_SECONDS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s211,
    {_s88: None},
    (_s93,),
    ((DATE_TIME, 0),),
)

GREETING_WITH_ERRORS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s212,
    {_s88: None},
    (_s143,),
    ((3, {_s77: _s213}),),
)

HOST_LABEL_INPUT: StaticSchema = (
    18,
    n1,
    _s214,
    {_s30: None},
    (_s215,),
    ((3, 257),),
)

HTTP_CHECKSUM_REQUIRED_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s216,
    {_s30: None, _s88: None},
    (_s217,),
    ((3, 0),),
)

STRING_MAP: StaticSchema = (
    17,
    n0,
    _s218,
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

HTTP_EMPTY_PREFIX_HEADERS_INPUT: StaticSchema = (
    18,
    n1,
    _s219,
    {_s30: None},
    (
        _s220,
        _s222,
    ),
    (
        (STRING_MAP, {_s221: _s123}),
        (3, {_s77: _s85}),
    ),
)

HTTP_EMPTY_PREFIX_HEADERS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s223,
    {_s88: None},
    (
        _s220,
        _s222,
    ),
    (
        (STRING_MAP, {_s221: _s123}),
        (3, {_s77: _s85}),
    ),
)

HTTP_PAYLOAD_TRAITS_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s224,
    {_s30: None, _s88: None},
    (
        _s217,
        _s226,
    ),
    (
        (3, {_s77: _s225}),
        (1, 16),
    ),
)

TEXT_PLAIN_BLOB: StaticSchema = (
    1,
    n0,
    _s227,
    {_s228: _s229},
)

NULL_AND_EMPTY_HEADERS_IO: StaticSchema = (
    18,
    n1,
    _s457,
    {_s30: None, _s88: None},
    (
        _s341,
        _s342,
        _s460,
    ),
    (
        (3, {_s77: _s458}),
        (3, {_s77: _s459}),
        (STRING_LIST, {_s77: _s461}),
    ),
)

SERVICE_UNAVAILABLE_ERROR: StaticSchema = (
    18,
    n1,
    _s506,
    {_s73: _s210, _s75: 500},
    (_s175,),
    ((3, 0),),
)
