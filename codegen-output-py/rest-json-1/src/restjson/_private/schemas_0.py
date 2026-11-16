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
_s68 = "smithy.api#clientOptional"
_s69 = "smithy.api#default"
_s70 = "ComplexNestedErrorData"
_s71 = "smithy.api#jsonName"
_s72 = "Fooooo"
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
_s89 = "smithy.api#output"
_s90 = "DateTime"
_s91 = "smithy.api#timestampFormat"
_s92 = "date-time"
_s93 = "DatetimeOffsetsOutput"
_s94 = "datetime"
_s95 = "TestStringList"
_s96 = "Document"
_s97 = "TestStringMap"
_s98 = "TestEnum"
_s99 = "TestIntEnum"
_s100 = "TWO"
_s101 = "Defaults"
_s102 = "defaultString"
_s103 = "hi"
_s104 = "defaultBoolean"
_s105 = "defaultList"
_s106 = "defaultDocumentMap"
_s107 = "defaultDocumentString"
_s108 = "defaultDocumentBoolean"
_s109 = "defaultDocumentList"
_s110 = "defaultNullDocument"
_s111 = "defaultTimestamp"
_s112 = "defaultBlob"
_s113 = "YWJj"
_s114 = "defaultByte"
_s115 = "defaultShort"
_s116 = "defaultInteger"
_s117 = "defaultLong"
_s118 = "defaultFloat"
_s119 = "defaultDouble"
_s120 = "defaultMap"
_s121 = "defaultEnum"
_s122 = "defaultIntEnum"
_s123 = "emptyString"
_s124 = ""
_s125 = "falseBoolean"
_s126 = "emptyBlob"
_s127 = "zeroByte"
_s128 = "zeroShort"
_s129 = "zeroInteger"
_s130 = "zeroLong"
_s131 = "zeroFloat"
_s132 = "zeroDouble"
_s133 = "DenseBooleanMap"
_s134 = "DenseNumberMap"
_s135 = "DenseSetMap"
_s136 = "DenseStringMap"
_s137 = "GreetingStruct"
_s138 = "DenseStructMap"
_s139 = "Farewell"
_s140 = "phrase"
_s141 = "bye"
_s142 = "Dialog"
_s143 = "language"
_s144 = "greeting"
_s145 = "farewell"
_s146 = "DialogList"
_s147 = "DialogMap"
_s148 = "DocumentValuedMap"
_s149 = "DocumentTypeAsMapValueInputOutput"
_s150 = "docValuedMap"
_s151 = "DocumentTypeAsPayloadInputOutput"
_s152 = "documentValue"
_s153 = "DocumentTypeInputOutput"
_s154 = "stringValue"
_s155 = "HeadersEvent"
_s156 = "booleanHeader"
_s157 = "smithy.api#eventHeader"
_s158 = "byteHeader"
_s159 = "shortHeader"
_s160 = "intHeader"
_s161 = "longHeader"
_s162 = "blobHeader"
_s163 = "stringHeader"
_s164 = "timestampHeader"
_s165 = "StringPayloadEvent"
_s166 = "PayloadStructure"
_s167 = "structureMember"
_s168 = "StructurePayloadEvent"
_s169 = "PayloadUnion"
_s170 = "unionMember"
_s171 = "UnionPayloadEvent"
_s172 = "HeadersAndExplicitPayloadEvent"
_s173 = "header"
_s174 = "HeadersAndImplicitPayloadEvent"
_s175 = "ErrorEvent"
_s176 = "message"
_s177 = "EventStream"
_s178 = "smithy.api#streaming"
_s179 = "headers"
_s180 = "blobPayload"
_s181 = "stringPayload"
_s182 = "structurePayload"
_s183 = "unionPayload"
_s184 = "headersAndExplicitPayload"
_s185 = "headersAndImplicitPayload"
_s186 = "error"
_s187 = "DuplexStreamInput"
_s188 = "stream"
_s189 = "DuplexStreamOutput"
_s190 = "DuplexStreamWithDistinctStreamsInput"
_s191 = "SingletonEvent"
_s192 = "SingletonEventStream"
_s193 = "singleton"
_s194 = "DuplexStreamWithDistinctStreamsOutput"
_s195 = "DuplexStreamWithInitialMessagesInput"
_s196 = "initialRequestMember"
_s197 = "initial-request-member"
_s198 = "smithy.api#required"
_s199 = "DuplexStreamWithInitialMessagesOutput"
_s200 = "initialResponseMember"
_s201 = "initial-response-member"
_s202 = "EmptyInputAndEmptyOutputInput"
_s203 = "EmptyInputAndEmptyOutputOutput"
_s204 = "StringEnum"
_s205 = "V"
_s206 = "enumvalue"
_s207 = "EnumPayloadInput"
_s208 = "FiniteStreamingBlob"
_s209 = "smithy.api#requiresLength"
_s210 = "FooError"
_s211 = "server"
_s212 = "FractionalSecondsOutput"
_s213 = "GreetingWithErrorsOutput"
_s214 = "X-Greeting"
_s215 = "HostLabelInput"
_s216 = "label"
_s217 = "HttpChecksumRequiredInputOutput"
_s218 = "foo"
_s219 = "StringMap"
_s220 = "HttpEmptyPrefixHeadersInput"
_s221 = "prefixHeaders"
_s222 = "smithy.api#httpPrefixHeaders"
_s223 = "specificHeader"
_s224 = "HttpEmptyPrefixHeadersOutput"
_s225 = "HttpPayloadTraitsInputOutput"
_s226 = "X-Foo"
_s227 = "blob"
_s228 = "TextPlainBlob"
_s229 = "smithy.api#mediaType"
_s230 = "text/plain"
_s342 = "a"
_s343 = "b"
_s458 = "NullAndEmptyHeadersIO"
_s459 = "X-A"
_s460 = "X-B"
_s461 = "c"
_s462 = "X-C"
_s507 = "ServiceUnavailableError"

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
    ((7, {_s68: None, _s69: 0}),),
)

COMPLEX_NESTED_ERROR_DATA: StaticSchema = (
    18,
    n1,
    _s70,
    0,
    (_s11,),
    ((3, {_s71: _s72}),),
)

COMPLEX_ERROR: StaticSchema = (
    18,
    n1,
    _s73,
    {_s74: _s75, _s76: 403},
    (_s77, _s80, _s81),
    ((3, {_s78: _s79}), (3, 0), (COMPLEX_NESTED_ERROR_DATA, 0)),
)

CONSTANT_AND_VARIABLE_QUERY_STRING_INPUT: StaticSchema = (
    18,
    n1,
    _s82,
    {_s30: None},
    (_s83, _s84),
    ((3, {_s32: _s83}), (3, {_s32: _s84})),
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
    {_s89: None},
)

DATE_TIME: StaticSchema = (
    4,
    n0,
    _s90,
    {_s91: _s92},
)

DATETIME_OFFSETS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s93,
    {_s89: None},
    (_s94,),
    ((DATE_TIME, 0),),
)

TEST_STRING_LIST: StaticSchema = (
    16,
    n1,
    _s95,
    0,
    (_s1,),
    ((3, 0),),
)

DOCUMENT: StaticSchema = (
    13,
    n1,
    _s96,
    0,
)

TEST_STRING_MAP: StaticSchema = (
    17,
    n1,
    _s97,
    0,
    (_s27, _s28),
    ((3, 0), (3, 0)),
)

TEST_ENUM: StaticSchema = (
    14,
    n1,
    _s98,
    0,
    (_s9, _s14, _s12),
    ((-1, {_s10: _s9}), (-1, {_s10: _s14}), (-1, {_s10: _s12})),
)

TEST_INT_ENUM: StaticSchema = (
    15,
    n1,
    _s99,
    0,
    (_s16, _s100),
    ((-1, {_s10: 1}), (-1, {_s10: 2})),
)

DEFAULTS: StaticSchema = (
    18,
    n1,
    _s101,
    0,
    (
        _s102,
        _s104,
        _s105,
        _s106,
        _s107,
        _s108,
        _s109,
        _s110,
        _s111,
        _s112,
        _s114,
        _s115,
        _s116,
        _s117,
        _s118,
        _s119,
        _s120,
        _s121,
        _s122,
        _s123,
        _s125,
        _s126,
        _s127,
        _s128,
        _s129,
        _s130,
        _s131,
        _s132,
    ),
    (
        (3, {_s69: _s103}),
        (2, {_s69: True}),
        (TEST_STRING_LIST, {_s69: ()}),
        (DOCUMENT, {_s69: MappingProxyType[str, object]({})}),
        (DOCUMENT, {_s69: _s103}),
        (DOCUMENT, {_s69: True}),
        (DOCUMENT, {_s69: ()}),
        (DOCUMENT, {_s69: None}),
        (4, {_s69: 0}),
        (1, {_s69: _s113}),
        (5, {_s69: 1}),
        (6, {_s69: 1}),
        (7, {_s69: 10}),
        (8, {_s69: 100}),
        (9, {_s69: 1.0}),
        (10, {_s69: 1.0}),
        (TEST_STRING_MAP, {_s69: MappingProxyType[str, object]({})}),
        (TEST_ENUM, {_s69: _s9}),
        (TEST_INT_ENUM, {_s69: 1}),
        (3, {_s69: _s124}),
        (2, {_s69: False}),
        (1, {_s69: _s124}),
        (5, {_s69: 0}),
        (6, {_s69: 0}),
        (7, {_s69: 0}),
        (8, {_s69: 0}),
        (9, {_s69: 0.0}),
        (10, {_s69: 0.0}),
    ),
)

DENSE_BOOLEAN_MAP: StaticSchema = (
    17,
    n1,
    _s133,
    0,
    (_s27, _s28),
    ((3, 0), (2, 0)),
)

DENSE_NUMBER_MAP: StaticSchema = (
    17,
    n1,
    _s134,
    0,
    (_s27, _s28),
    ((3, 0), (7, 0)),
)

DENSE_SET_MAP: StaticSchema = (
    17,
    n1,
    _s135,
    0,
    (_s27, _s28),
    ((3, 0), (STRING_SET, 0)),
)

DENSE_STRING_MAP: StaticSchema = (
    17,
    n1,
    _s136,
    0,
    (_s27, _s28),
    ((3, 0), (3, 0)),
)

GREETING_STRUCT: StaticSchema = (
    18,
    n0,
    _s137,
    {_s30: None, _s89: None},
    (_s103,),
    ((3, 0),),
)

DENSE_STRUCT_MAP: StaticSchema = (
    17,
    n1,
    _s138,
    0,
    (_s27, _s28),
    ((3, 0), (GREETING_STRUCT, 0)),
)

FAREWELL: StaticSchema = (
    18,
    n1,
    _s139,
    0,
    (_s140,),
    ((3, {_s69: _s141}),),
)

DIALOG: StaticSchema = (
    18,
    n1,
    _s142,
    0,
    (_s143, _s144, _s145),
    ((3, 0), (3, {_s69: _s103}), (FAREWELL, 0)),
)

DIALOG_LIST: StaticSchema = (
    16,
    n1,
    _s146,
    0,
    (_s1,),
    ((DIALOG, 0),),
)

DIALOG_MAP: StaticSchema = (
    17,
    n1,
    _s147,
    0,
    (_s27, _s28),
    ((3, 0), (DIALOG, 0)),
)

DOCUMENT_VALUED_MAP: StaticSchema = (
    17,
    n1,
    _s148,
    0,
    (_s27, _s28),
    ((3, 0), (DOCUMENT, 0)),
)

DOCUMENT_TYPE_AS_MAP_VALUE_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s149,
    {_s30: None, _s89: None},
    (_s150,),
    ((DOCUMENT_VALUED_MAP, 0),),
)

DOCUMENT_TYPE_AS_PAYLOAD_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s151,
    {_s30: None, _s89: None},
    (_s152,),
    ((DOCUMENT, 16),),
)

DOCUMENT_TYPE_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s153,
    {_s30: None, _s89: None},
    (_s154, _s152),
    ((3, 0), (DOCUMENT, 0)),
)

HEADERS_EVENT: StaticSchema = (
    18,
    n1,
    _s155,
    0,
    (_s156, _s158, _s159, _s160, _s161, _s162, _s163, _s164),
    (
        (2, {_s157: None}),
        (5, {_s157: None}),
        (6, {_s157: None}),
        (7, {_s157: None}),
        (8, {_s157: None}),
        (1, {_s157: None}),
        (3, {_s157: None}),
        (DATE_TIME, {_s157: None}),
    ),
)

STRING_PAYLOAD_EVENT: StaticSchema = (
    18,
    n1,
    _s165,
    0,
    (_s65,),
    ((3, {_s66: None}),),
)

PAYLOAD_STRUCTURE: StaticSchema = (
    18,
    n1,
    _s166,
    0,
    (_s167,),
    ((3, 0),),
)

STRUCTURE_PAYLOAD_EVENT: StaticSchema = (
    18,
    n1,
    _s168,
    0,
    (_s65,),
    ((PAYLOAD_STRUCTURE, {_s66: None}),),
)

PAYLOAD_UNION: StaticSchema = (
    19,
    n1,
    _s169,
    0,
    (_s170,),
    ((3, 0),),
)

UNION_PAYLOAD_EVENT: StaticSchema = (
    18,
    n1,
    _s171,
    0,
    (_s65,),
    ((PAYLOAD_UNION, {_s66: None}),),
)

HEADERS_AND_EXPLICIT_PAYLOAD_EVENT: StaticSchema = (
    18,
    n1,
    _s172,
    0,
    (_s173, _s65),
    ((3, {_s157: None}), (PAYLOAD_STRUCTURE, {_s66: None})),
)

HEADERS_AND_IMPLICIT_PAYLOAD_EVENT: StaticSchema = (
    18,
    n1,
    _s174,
    0,
    (_s173, _s65),
    ((3, {_s157: None}), (3, 0)),
)

ERROR_EVENT: StaticSchema = (
    18,
    n1,
    _s175,
    {_s74: _s75},
    (_s176,),
    ((3, 0),),
)

EVENT_STREAM: StaticSchema = (
    19,
    n1,
    _s177,
    {_s178: None},
    (_s179, _s180, _s181, _s182, _s183, _s184, _s185, _s186),
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
    _s187,
    {_s30: None},
    (_s188,),
    ((EVENT_STREAM, 16),),
)

DUPLEX_STREAM_OUTPUT: StaticSchema = (
    18,
    n1,
    _s189,
    {_s89: None},
    (_s188,),
    ((EVENT_STREAM, 16),),
)

DUPLEX_STREAM_WITH_DISTINCT_STREAMS_INPUT: StaticSchema = (
    18,
    n1,
    _s190,
    {_s30: None},
    (_s188,),
    ((EVENT_STREAM, 16),),
)

DUPLEX_STREAM_WITH_DISTINCT_STREAMS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s194,
    {_s89: None},
    (_s188,),
    ((lambda: SINGLETON_EVENT_STREAM, 16),),
)

SINGLETON_EVENT: StaticSchema = (
    18,
    n1,
    _s191,
    0,
    (_s28,),
    ((3, 0),),
)

SINGLETON_EVENT_STREAM: StaticSchema = (
    19,
    n1,
    _s192,
    0,
    (_s193,),
    ((SINGLETON_EVENT, 0),),
)

DUPLEX_STREAM_WITH_INITIAL_MESSAGES_INPUT: StaticSchema = (
    18,
    n1,
    _s195,
    {_s30: None},
    (_s196, _s188),
    ((3, {_s78: _s197, _s198: None}), (EVENT_STREAM, 16)),
)

DUPLEX_STREAM_WITH_INITIAL_MESSAGES_OUTPUT: StaticSchema = (
    18,
    n1,
    _s199,
    {_s89: None},
    (_s200, _s188),
    ((3, {_s78: _s201, _s198: None}), (EVENT_STREAM, 16)),
)

EMPTY_INPUT_AND_EMPTY_OUTPUT_INPUT: StaticSchema = (
    18,
    n1,
    _s202,
    {_s30: None},
)

EMPTY_INPUT_AND_EMPTY_OUTPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s203,
    {_s89: None},
)

STRING_ENUM: StaticSchema = (
    14,
    n1,
    _s204,
    0,
    (_s205,),
    ((-1, {_s10: _s206}),),
)

ENUM_PAYLOAD_INPUT: StaticSchema = (
    18,
    n1,
    _s207,
    {_s30: None, _s89: None},
    (_s65,),
    ((STRING_ENUM, 16),),
)

FINITE_STREAMING_BLOB: StaticSchema = (
    1,
    n1,
    _s208,
    {_s178: None, _s209: None},
)

FOO_ERROR: StaticSchema = (
    18,
    n1,
    _s210,
    {_s74: _s211, _s76: 500},
)

FRACTIONAL_SECONDS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s212,
    {_s89: None},
    (_s94,),
    ((DATE_TIME, 0),),
)

GREETING_WITH_ERRORS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s213,
    {_s89: None},
    (_s144,),
    ((3, {_s78: _s214}),),
)

HOST_LABEL_INPUT: StaticSchema = (
    18,
    n1,
    _s215,
    {_s30: None},
    (_s216,),
    ((3, 257),),
)

HTTP_CHECKSUM_REQUIRED_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s217,
    {_s30: None, _s89: None},
    (_s218,),
    ((3, 0),),
)

STRING_MAP: StaticSchema = (
    17,
    n0,
    _s219,
    0,
    (_s27, _s28),
    ((3, 0), (3, 0)),
)

HTTP_EMPTY_PREFIX_HEADERS_INPUT: StaticSchema = (
    18,
    n1,
    _s220,
    {_s30: None},
    (_s221, _s223),
    ((STRING_MAP, {_s222: _s124}), (3, {_s78: _s86})),
)

HTTP_EMPTY_PREFIX_HEADERS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s224,
    {_s89: None},
    (_s221, _s223),
    ((STRING_MAP, {_s222: _s124}), (3, {_s78: _s86})),
)

HTTP_PAYLOAD_TRAITS_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s225,
    {_s30: None, _s89: None},
    (_s218, _s227),
    ((3, {_s78: _s226}), (1, 16)),
)

TEXT_PLAIN_BLOB: StaticSchema = (
    1,
    n0,
    _s228,
    {_s229: _s230},
)

NULL_AND_EMPTY_HEADERS_IO: StaticSchema = (
    18,
    n1,
    _s458,
    {_s30: None, _s89: None},
    (_s342, _s343, _s461),
    ((3, {_s78: _s459}), (3, {_s78: _s460}), (STRING_LIST, {_s78: _s462})),
)

SERVICE_UNAVAILABLE_ERROR: StaticSchema = (
    18,
    n1,
    _s507,
    {_s74: _s211, _s76: 500},
    (_s176,),
    ((3, 0),),
)
