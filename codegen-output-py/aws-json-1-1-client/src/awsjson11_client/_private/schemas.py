from types import MappingProxyType

from smithy_core._schema_compact import StaticOperationSchema, StaticSchema

n0 = "aws.protocoltests.json"
_s0 = "ComplexNestedErrorData"
_s1 = "Foo"
_s2 = "smithy.api#jsonName"
_s3 = "Fooooo"
_s4 = "ComplexError"
_s5 = "smithy.api#error"
_s6 = "client"
_s7 = "TopLevel"
_s8 = "Nested"
_s9 = "ContentTypeParametersInput"
_s10 = "smithy.synthetic#originalShapeId"
_s11 = "aws.protocoltests.json#ContentTypeParametersInput"
_s12 = "smithy.api#input"
_s13 = "value"
_s14 = "ContentTypeParametersOutput"
_s15 = "aws.protocoltests.json#ContentTypeParametersOutput"
_s16 = "smithy.api#output"
n1 = "aws.protocoltests.shared"
_s17 = "DateTime"
_s18 = "smithy.api#timestampFormat"
_s19 = "date-time"
_s20 = "DatetimeOffsetsOutput"
_s21 = "aws.protocoltests.json#DatetimeOffsetsOutput"
_s22 = "datetime"
_s23 = "Document"
_s24 = "EmptyStruct"
_s25 = "JsonValue"
_s26 = "smithy.api#mediaType"
_s27 = "application/json"
_s28 = "ListOfStrings"
_s29 = "member"
_s30 = "ListOfListOfStrings"
_s31 = "MapOfStrings"
_s32 = "key"
_s33 = "ListOfMapsOfStrings"
_s34 = "SimpleStruct"
_s35 = "Value"
_s36 = "ListOfStructs"
_s37 = "MapOfListsOfStrings"
_s38 = "MapOfMapOfStrings"
_s39 = "MapOfStructs"
_s40 = "StructWithJsonName"
_s41 = "RenamedMember"
_s42 = "ErrorWithMembers"
_s43 = "Code"
_s44 = "ComplexData"
_s45 = "IntegerField"
_s46 = "ListField"
_s47 = "MapField"
_s48 = "Message"
_s49 = "StringField"
_s50 = "ErrorWithoutMembers"
_s51 = "server"
_s52 = "FooError"
_s53 = "FractionalSecondsOutput"
_s54 = "aws.protocoltests.json#FractionalSecondsOutput"
_s55 = "GreetingWithErrorsOutput"
_s56 = "aws.protocoltests.json#GreetingWithErrorsOutput"
_s57 = "greeting"
_s58 = "InvalidGreeting"
_s59 = "FooEnum"
_s60 = "FOO"
_s61 = "smithy.api#enumValue"
_s62 = "BAZ"
_s63 = "Baz"
_s64 = "BAR"
_s65 = "Bar"
_s66 = "ONE"
_s67 = "1"
_s68 = "ZERO"
_s69 = "0"
_s70 = "StringList"
_s71 = "StringMap"
_s72 = "GreetingStruct"
_s73 = "hi"
_s74 = "MyUnion"
_s75 = "stringValue"
_s76 = "booleanValue"
_s77 = "numberValue"
_s78 = "blobValue"
_s79 = "timestampValue"
_s80 = "enumValue"
_s81 = "listValue"
_s82 = "mapValue"
_s83 = "structureValue"
_s84 = "OperationWithOptionalInputOutputInput"
_s85 = "aws.protocoltests.json#OperationWithOptionalInputOutputInput"
_s86 = "OperationWithOptionalInputOutputOutput"
_s87 = "aws.protocoltests.json#OperationWithOptionalInputOutputOutput"
_s88 = "PutWithContentEncodingInput"
_s89 = "aws.protocoltests.json#PutWithContentEncodingInput"
_s90 = "encoding"
_s91 = "smithy.api#httpHeader"
_s92 = "Content-Encoding"
_s93 = "data"
_s94 = "FooEnumList"
_s95 = "FooEnumMap"
_s96 = "FooEnumSet"
_s97 = "IntegerEnum"
_s98 = "A"
_s99 = "B"
_s100 = "C"
_s101 = "IntegerEnumList"
_s102 = "IntegerEnumMap"
_s103 = "IntegerEnumSet"
_s104 = "SparseStringList"
_s105 = "SparseStringMap"
_s106 = "DatetimeOffsetsInput"
_s107 = "smithy.api#Unit"
_s108 = "EmptyOperationInput"
_s109 = "EmptyOperationOutput"
_s110 = "EndpointOperationInput"
_s111 = "EndpointOperationOutput"
_s112 = "EndpointWithHostLabelOperationInput"
_s113 = "aws.protocoltests.json#HostLabelInput"
_s114 = "label"
_s115 = "EndpointWithHostLabelOperationOutput"
_s116 = "FractionalSecondsInput"
_s117 = "GreetingWithErrorsInput"
_s118 = "HostWithPathOperationInput"
_s119 = "HostWithPathOperationOutput"
_s120 = "JsonEnumsInput"
_s121 = "aws.protocoltests.json#JsonEnumsInputOutput"
_s122 = "fooEnum1"
_s123 = "fooEnum2"
_s124 = "fooEnum3"
_s125 = "fooEnumList"
_s126 = "fooEnumSet"
_s127 = "fooEnumMap"
_s128 = "JsonEnumsOutput"
_s129 = "JsonIntEnumsInput"
_s130 = "aws.protocoltests.json#JsonIntEnumsInputOutput"
_s131 = "intEnum1"
_s132 = "intEnum2"
_s133 = "intEnum3"
_s134 = "intEnumList"
_s135 = "intEnumSet"
_s136 = "intEnumMap"
_s137 = "JsonIntEnumsOutput"
_s138 = "JsonUnionsInput"
_s139 = "aws.protocoltests.json#UnionInputOutput"
_s140 = "contents"
_s141 = "JsonUnionsOutput"
_s142 = "KitchenSinkOperationInput"
_s143 = "aws.protocoltests.json#KitchenSink"
_s144 = "Blob"
_s145 = "Boolean"
_s146 = "Double"
_s147 = "Float"
_s148 = "HttpdateTimestamp"
_s149 = "http-date"
_s150 = "Integer"
_s151 = "Iso8601Timestamp"
_s152 = "ListOfLists"
_s153 = "Long"
_s154 = "MapOfMaps"
_s155 = "RecursiveList"
_s156 = "RecursiveMap"
_s157 = "RecursiveStruct"
_s158 = "String"
_s159 = "Timestamp"
_s160 = "UnixTimestamp"
_s161 = "epoch-seconds"
_s162 = "KitchenSinkOperationOutput"
_s163 = "NullOperationInput"
_s164 = "aws.protocoltests.json#NullOperationInputOutput"
_s165 = "string"
_s166 = "NullOperationOutput"
_s167 = "PutAndGetInlineDocumentsInput"
_s168 = "aws.protocoltests.json#PutAndGetInlineDocumentsInputOutput"
_s169 = "inlineDocument"
_s170 = "PutAndGetInlineDocumentsOutput"
_s171 = "PutWithContentEncodingOutput"
_s172 = "SimpleScalarPropertiesInput"
_s173 = "aws.protocoltests.json#SimpleScalarPropertiesInputOutput"
_s174 = "floatValue"
_s175 = "doubleValue"
_s176 = "SimpleScalarPropertiesOutput"
_s177 = "SparseNullsOperationInput"
_s178 = "aws.protocoltests.json#SparseNullsOperationInputOutput"
_s179 = "sparseStringList"
_s180 = "sparseStringMap"
_s181 = "SparseNullsOperationOutput"
_s182 = "ContentTypeParameters"
_s183 = "DatetimeOffsets"
_s184 = "EmptyOperation"
_s185 = "EndpointOperation"
_s186 = "smithy.api#endpoint"
_s187 = "EndpointWithHostLabelOperation"
_s188 = "FractionalSeconds"
_s189 = "GreetingWithErrors"
_s190 = "HostWithPathOperation"
_s191 = "JsonEnums"
_s192 = "JsonIntEnums"
_s193 = "JsonUnions"
_s194 = "KitchenSinkOperation"
_s195 = "NullOperation"
_s196 = "OperationWithOptionalInputOutput"
_s197 = "PutAndGetInlineDocuments"
_s198 = "PutWithContentEncoding"
_s199 = "smithy.api#requestCompression"
_s200 = "SimpleScalarProperties"
_s201 = "SparseNullsOperation"
_s202 = "JsonProtocol"
_s203 = "aws.api#service"
_s204 = "aws.auth#sigv4"
_s205 = "aws.protocols#awsJson1_1"
_s206 = "KitchenSink"
_s207 = "ListOfKitchenSinks"
_s208 = "MapOfKitchenSinks"

COMPLEX_NESTED_ERROR_DATA: StaticSchema = (
    18,
    n0,
    _s0,
    0,
    (_s1,),
    ((3, {_s2: _s3}),),
)

COMPLEX_ERROR: StaticSchema = (
    18,
    n0,
    _s4,
    {_s5: _s6},
    (_s7, _s8),
    ((3, 0), (COMPLEX_NESTED_ERROR_DATA, 0)),
)

CONTENT_TYPE_PARAMETERS_INPUT: StaticSchema = (
    18,
    n0,
    _s9,
    {_s10: _s11, _s12: None},
    (_s13,),
    ((7, 0),),
)

CONTENT_TYPE_PARAMETERS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s14,
    {_s10: _s15, _s16: None},
)

DATE_TIME: StaticSchema = (
    4,
    n1,
    _s17,
    {_s18: _s19},
)

DATETIME_OFFSETS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s20,
    {_s10: _s21, _s16: None},
    (_s22,),
    ((DATE_TIME, 0),),
)

DOCUMENT: StaticSchema = (
    13,
    n0,
    _s23,
    0,
)

EMPTY_STRUCT: StaticSchema = (
    18,
    n0,
    _s24,
    0,
)

JSON_VALUE: StaticSchema = (
    3,
    n0,
    _s25,
    {_s26: _s27},
)

LIST_OF_STRINGS: StaticSchema = (
    16,
    n0,
    _s28,
    0,
    (_s29,),
    ((3, 0),),
)

LIST_OF_LIST_OF_STRINGS: StaticSchema = (
    16,
    n0,
    _s30,
    0,
    (_s29,),
    ((LIST_OF_STRINGS, 0),),
)

MAP_OF_STRINGS: StaticSchema = (
    17,
    n0,
    _s31,
    0,
    (_s32, _s13),
    ((3, 0), (3, 0)),
)

LIST_OF_MAPS_OF_STRINGS: StaticSchema = (
    16,
    n0,
    _s33,
    0,
    (_s29,),
    ((MAP_OF_STRINGS, 0),),
)

SIMPLE_STRUCT: StaticSchema = (
    18,
    n0,
    _s34,
    0,
    (_s35,),
    ((3, 0),),
)

LIST_OF_STRUCTS: StaticSchema = (
    16,
    n0,
    _s36,
    0,
    (_s29,),
    ((SIMPLE_STRUCT, 0),),
)

MAP_OF_LISTS_OF_STRINGS: StaticSchema = (
    17,
    n0,
    _s37,
    0,
    (_s32, _s13),
    ((3, 0), (LIST_OF_STRINGS, 0)),
)

MAP_OF_MAP_OF_STRINGS: StaticSchema = (
    17,
    n0,
    _s38,
    0,
    (_s32, _s13),
    ((3, 0), (MAP_OF_STRINGS, 0)),
)

MAP_OF_STRUCTS: StaticSchema = (
    17,
    n0,
    _s39,
    0,
    (_s32, _s13),
    ((3, 0), (SIMPLE_STRUCT, 0)),
)

STRUCT_WITH_JSON_NAME: StaticSchema = (
    18,
    n0,
    _s40,
    0,
    (_s35,),
    ((3, {_s2: _s41}),),
)

ERROR_WITH_MEMBERS: StaticSchema = (
    18,
    n0,
    _s42,
    {_s5: _s6},
    (_s43, _s44, _s45, _s46, _s47, _s48, _s49),
    (
        (3, 0),
        (lambda: KITCHEN_SINK, 0),
        (7, 0),
        (LIST_OF_STRINGS, 0),
        (MAP_OF_STRINGS, 0),
        (3, 0),
        (3, 0),
    ),
)

ERROR_WITHOUT_MEMBERS: StaticSchema = (
    18,
    n0,
    _s50,
    {_s5: _s51},
)

FOO_ERROR: StaticSchema = (
    18,
    n0,
    _s52,
    {_s5: _s51},
)

FRACTIONAL_SECONDS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s53,
    {_s10: _s54, _s16: None},
    (_s22,),
    ((DATE_TIME, 0),),
)

GREETING_WITH_ERRORS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s55,
    {_s10: _s56, _s16: None},
    (_s57,),
    ((3, 0),),
)

INVALID_GREETING: StaticSchema = (
    18,
    n0,
    _s58,
    {_s5: _s6},
    (_s48,),
    ((3, 0),),
)

FOO_ENUM: StaticSchema = (
    14,
    n1,
    _s59,
    0,
    (_s60, _s62, _s64, _s66, _s68),
    (
        (-1, {_s61: _s1}),
        (-1, {_s61: _s63}),
        (-1, {_s61: _s65}),
        (-1, {_s61: _s67}),
        (-1, {_s61: _s69}),
    ),
)

STRING_LIST: StaticSchema = (
    16,
    n1,
    _s70,
    0,
    (_s29,),
    ((3, 0),),
)

STRING_MAP: StaticSchema = (
    17,
    n1,
    _s71,
    0,
    (_s32, _s13),
    ((3, 0), (3, 0)),
)

GREETING_STRUCT: StaticSchema = (
    18,
    n1,
    _s72,
    0,
    (_s73,),
    ((3, 0),),
)

MY_UNION: StaticSchema = (
    19,
    n0,
    _s74,
    0,
    (_s75, _s76, _s77, _s78, _s79, _s80, _s81, _s82, _s83),
    (
        (3, 0),
        (2, 0),
        (7, 0),
        (1, 0),
        (4, 0),
        (FOO_ENUM, 0),
        (STRING_LIST, 0),
        (STRING_MAP, 0),
        (GREETING_STRUCT, 0),
    ),
)

OPERATION_WITH_OPTIONAL_INPUT_OUTPUT_INPUT: StaticSchema = (
    18,
    n0,
    _s84,
    {_s10: _s85, _s12: None},
    (_s35,),
    ((3, 0),),
)

OPERATION_WITH_OPTIONAL_INPUT_OUTPUT_OUTPUT: StaticSchema = (
    18,
    n0,
    _s86,
    {_s10: _s87, _s16: None},
    (_s35,),
    ((3, 0),),
)

PUT_WITH_CONTENT_ENCODING_INPUT: StaticSchema = (
    18,
    n0,
    _s88,
    {_s10: _s89, _s12: None},
    (_s90, _s93),
    ((3, {_s91: _s92}), (3, 0)),
)

FOO_ENUM_LIST: StaticSchema = (
    16,
    n1,
    _s94,
    0,
    (_s29,),
    ((FOO_ENUM, 0),),
)

FOO_ENUM_MAP: StaticSchema = (
    17,
    n1,
    _s95,
    0,
    (_s32, _s13),
    ((3, 0), (FOO_ENUM, 0)),
)

FOO_ENUM_SET: StaticSchema = (
    16,
    n1,
    _s96,
    0,
    (_s29,),
    ((FOO_ENUM, 0),),
)

INTEGER_ENUM: StaticSchema = (
    15,
    n1,
    _s97,
    0,
    (_s98, _s99, _s100),
    ((-1, {_s61: 1}), (-1, {_s61: 2}), (-1, {_s61: 3})),
)

INTEGER_ENUM_LIST: StaticSchema = (
    16,
    n1,
    _s101,
    0,
    (_s29,),
    ((INTEGER_ENUM, 0),),
)

INTEGER_ENUM_MAP: StaticSchema = (
    17,
    n1,
    _s102,
    0,
    (_s32, _s13),
    ((3, 0), (INTEGER_ENUM, 0)),
)

INTEGER_ENUM_SET: StaticSchema = (
    16,
    n1,
    _s103,
    0,
    (_s29,),
    ((INTEGER_ENUM, 0),),
)

SPARSE_STRING_LIST: StaticSchema = (
    16,
    n1,
    _s104,
    64,
    (_s29,),
    ((3, 0),),
)

SPARSE_STRING_MAP: StaticSchema = (
    17,
    n1,
    _s105,
    64,
    (_s32, _s13),
    ((3, 0), (3, 0)),
)

DATETIME_OFFSETS_INPUT: StaticSchema = (
    18,
    n0,
    _s106,
    {_s10: _s107, _s12: None},
)

EMPTY_OPERATION_INPUT: StaticSchema = (
    18,
    n0,
    _s108,
    {_s10: _s107, _s12: None},
)

EMPTY_OPERATION_OUTPUT: StaticSchema = (
    18,
    n0,
    _s109,
    {_s10: _s107, _s16: None},
)

ENDPOINT_OPERATION_INPUT: StaticSchema = (
    18,
    n0,
    _s110,
    {_s10: _s107, _s12: None},
)

ENDPOINT_OPERATION_OUTPUT: StaticSchema = (
    18,
    n0,
    _s111,
    {_s10: _s107, _s16: None},
)

ENDPOINT_WITH_HOST_LABEL_OPERATION_INPUT: StaticSchema = (
    18,
    n0,
    _s112,
    {_s10: _s113, _s12: None},
    (_s114,),
    ((3, 257),),
)

ENDPOINT_WITH_HOST_LABEL_OPERATION_OUTPUT: StaticSchema = (
    18,
    n0,
    _s115,
    {_s10: _s107, _s16: None},
)

FRACTIONAL_SECONDS_INPUT: StaticSchema = (
    18,
    n0,
    _s116,
    {_s10: _s107, _s12: None},
)

GREETING_WITH_ERRORS_INPUT: StaticSchema = (
    18,
    n0,
    _s117,
    {_s10: _s107, _s12: None},
)

HOST_WITH_PATH_OPERATION_INPUT: StaticSchema = (
    18,
    n0,
    _s118,
    {_s10: _s107, _s12: None},
)

HOST_WITH_PATH_OPERATION_OUTPUT: StaticSchema = (
    18,
    n0,
    _s119,
    {_s10: _s107, _s16: None},
)

JSON_ENUMS_INPUT: StaticSchema = (
    18,
    n0,
    _s120,
    {_s10: _s121, _s12: None},
    (_s122, _s123, _s124, _s125, _s126, _s127),
    (
        (FOO_ENUM, 0),
        (FOO_ENUM, 0),
        (FOO_ENUM, 0),
        (FOO_ENUM_LIST, 0),
        (FOO_ENUM_SET, 0),
        (FOO_ENUM_MAP, 0),
    ),
)

JSON_ENUMS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s128,
    {_s10: _s121, _s16: None},
    (_s122, _s123, _s124, _s125, _s126, _s127),
    (
        (FOO_ENUM, 0),
        (FOO_ENUM, 0),
        (FOO_ENUM, 0),
        (FOO_ENUM_LIST, 0),
        (FOO_ENUM_SET, 0),
        (FOO_ENUM_MAP, 0),
    ),
)

JSON_INT_ENUMS_INPUT: StaticSchema = (
    18,
    n0,
    _s129,
    {_s10: _s130, _s12: None},
    (_s131, _s132, _s133, _s134, _s135, _s136),
    (
        (INTEGER_ENUM, 0),
        (INTEGER_ENUM, 0),
        (INTEGER_ENUM, 0),
        (INTEGER_ENUM_LIST, 0),
        (INTEGER_ENUM_SET, 0),
        (INTEGER_ENUM_MAP, 0),
    ),
)

JSON_INT_ENUMS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s137,
    {_s10: _s130, _s16: None},
    (_s131, _s132, _s133, _s134, _s135, _s136),
    (
        (INTEGER_ENUM, 0),
        (INTEGER_ENUM, 0),
        (INTEGER_ENUM, 0),
        (INTEGER_ENUM_LIST, 0),
        (INTEGER_ENUM_SET, 0),
        (INTEGER_ENUM_MAP, 0),
    ),
)

JSON_UNIONS_INPUT: StaticSchema = (
    18,
    n0,
    _s138,
    {_s10: _s139, _s12: None},
    (_s140,),
    ((MY_UNION, 0),),
)

JSON_UNIONS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s141,
    {_s10: _s139, _s16: None},
    (_s140,),
    ((MY_UNION, 0),),
)

KITCHEN_SINK_OPERATION_INPUT: StaticSchema = (
    18,
    n0,
    _s142,
    {_s10: _s143, _s12: None},
    (
        _s144,
        _s145,
        _s146,
        _s24,
        _s147,
        _s148,
        _s150,
        _s151,
        _s25,
        _s152,
        _s33,
        _s28,
        _s36,
        _s153,
        _s37,
        _s154,
        _s31,
        _s39,
        _s155,
        _s156,
        _s157,
        _s34,
        _s158,
        _s40,
        _s159,
        _s160,
    ),
    (
        (1, 0),
        (2, 0),
        (10, 0),
        (EMPTY_STRUCT, 0),
        (9, 0),
        (4, {_s18: _s149}),
        (7, 0),
        (4, {_s18: _s19}),
        (JSON_VALUE, 0),
        (LIST_OF_LIST_OF_STRINGS, 0),
        (LIST_OF_MAPS_OF_STRINGS, 0),
        (LIST_OF_STRINGS, 0),
        (LIST_OF_STRUCTS, 0),
        (8, 0),
        (MAP_OF_LISTS_OF_STRINGS, 0),
        (MAP_OF_MAP_OF_STRINGS, 0),
        (MAP_OF_STRINGS, 0),
        (MAP_OF_STRUCTS, 0),
        (lambda: LIST_OF_KITCHEN_SINKS, 0),
        (lambda: MAP_OF_KITCHEN_SINKS, 0),
        (lambda: KITCHEN_SINK, 0),
        (SIMPLE_STRUCT, 0),
        (3, 0),
        (STRUCT_WITH_JSON_NAME, 0),
        (4, 0),
        (4, {_s18: _s161}),
    ),
)

KITCHEN_SINK_OPERATION_OUTPUT: StaticSchema = (
    18,
    n0,
    _s162,
    {_s10: _s143, _s16: None},
    (
        _s144,
        _s145,
        _s146,
        _s24,
        _s147,
        _s148,
        _s150,
        _s151,
        _s25,
        _s152,
        _s33,
        _s28,
        _s36,
        _s153,
        _s37,
        _s154,
        _s31,
        _s39,
        _s155,
        _s156,
        _s157,
        _s34,
        _s158,
        _s40,
        _s159,
        _s160,
    ),
    (
        (1, 0),
        (2, 0),
        (10, 0),
        (EMPTY_STRUCT, 0),
        (9, 0),
        (4, {_s18: _s149}),
        (7, 0),
        (4, {_s18: _s19}),
        (JSON_VALUE, 0),
        (LIST_OF_LIST_OF_STRINGS, 0),
        (LIST_OF_MAPS_OF_STRINGS, 0),
        (LIST_OF_STRINGS, 0),
        (LIST_OF_STRUCTS, 0),
        (8, 0),
        (MAP_OF_LISTS_OF_STRINGS, 0),
        (MAP_OF_MAP_OF_STRINGS, 0),
        (MAP_OF_STRINGS, 0),
        (MAP_OF_STRUCTS, 0),
        (lambda: LIST_OF_KITCHEN_SINKS, 0),
        (lambda: MAP_OF_KITCHEN_SINKS, 0),
        (lambda: KITCHEN_SINK, 0),
        (SIMPLE_STRUCT, 0),
        (3, 0),
        (STRUCT_WITH_JSON_NAME, 0),
        (4, 0),
        (4, {_s18: _s161}),
    ),
)

NULL_OPERATION_INPUT: StaticSchema = (
    18,
    n0,
    _s163,
    {_s10: _s164, _s12: None},
    (_s165,),
    ((3, 0),),
)

NULL_OPERATION_OUTPUT: StaticSchema = (
    18,
    n0,
    _s166,
    {_s10: _s164, _s16: None},
    (_s165,),
    ((3, 0),),
)

PUT_AND_GET_INLINE_DOCUMENTS_INPUT: StaticSchema = (
    18,
    n0,
    _s167,
    {_s10: _s168, _s12: None},
    (_s169,),
    ((DOCUMENT, 0),),
)

PUT_AND_GET_INLINE_DOCUMENTS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s170,
    {_s10: _s168, _s16: None},
    (_s169,),
    ((DOCUMENT, 0),),
)

PUT_WITH_CONTENT_ENCODING_OUTPUT: StaticSchema = (
    18,
    n0,
    _s171,
    {_s10: _s107, _s16: None},
)

SIMPLE_SCALAR_PROPERTIES_INPUT: StaticSchema = (
    18,
    n0,
    _s172,
    {_s10: _s173, _s12: None},
    (_s174, _s175),
    ((9, 0), (10, 0)),
)

SIMPLE_SCALAR_PROPERTIES_OUTPUT: StaticSchema = (
    18,
    n0,
    _s176,
    {_s10: _s173, _s16: None},
    (_s174, _s175),
    ((9, 0), (10, 0)),
)

SPARSE_NULLS_OPERATION_INPUT: StaticSchema = (
    18,
    n0,
    _s177,
    {_s10: _s178, _s12: None},
    (_s179, _s180),
    ((SPARSE_STRING_LIST, 0), (SPARSE_STRING_MAP, 0)),
)

SPARSE_NULLS_OPERATION_OUTPUT: StaticSchema = (
    18,
    n0,
    _s181,
    {_s10: _s178, _s16: None},
    (_s179, _s180),
    ((SPARSE_STRING_LIST, 0), (SPARSE_STRING_MAP, 0)),
)

CONTENT_TYPE_PARAMETERS: StaticOperationSchema = (
    23,
    n0,
    _s182,
    0,
    CONTENT_TYPE_PARAMETERS_INPUT,
    CONTENT_TYPE_PARAMETERS_OUTPUT,
    (),
)

DATETIME_OFFSETS: StaticOperationSchema = (
    23,
    n0,
    _s183,
    0,
    DATETIME_OFFSETS_INPUT,
    DATETIME_OFFSETS_OUTPUT,
    (),
)

EMPTY_OPERATION: StaticOperationSchema = (
    23,
    n0,
    _s184,
    0,
    EMPTY_OPERATION_INPUT,
    EMPTY_OPERATION_OUTPUT,
    (),
)

ENDPOINT_OPERATION: StaticOperationSchema = (
    23,
    n0,
    _s185,
    {_s186: MappingProxyType({"hostPrefix": "foo."})},
    ENDPOINT_OPERATION_INPUT,
    ENDPOINT_OPERATION_OUTPUT,
    (),
)

ENDPOINT_WITH_HOST_LABEL_OPERATION: StaticOperationSchema = (
    23,
    n0,
    _s187,
    {_s186: MappingProxyType({"hostPrefix": "foo.{label}."})},
    ENDPOINT_WITH_HOST_LABEL_OPERATION_INPUT,
    ENDPOINT_WITH_HOST_LABEL_OPERATION_OUTPUT,
    (),
)

FRACTIONAL_SECONDS: StaticOperationSchema = (
    23,
    n0,
    _s188,
    0,
    FRACTIONAL_SECONDS_INPUT,
    FRACTIONAL_SECONDS_OUTPUT,
    (),
)

GREETING_WITH_ERRORS: StaticOperationSchema = (
    23,
    n0,
    _s189,
    0,
    GREETING_WITH_ERRORS_INPUT,
    GREETING_WITH_ERRORS_OUTPUT,
    (COMPLEX_ERROR, FOO_ERROR, INVALID_GREETING),
)

HOST_WITH_PATH_OPERATION: StaticOperationSchema = (
    23,
    n0,
    _s190,
    0,
    HOST_WITH_PATH_OPERATION_INPUT,
    HOST_WITH_PATH_OPERATION_OUTPUT,
    (),
)

JSON_ENUMS: StaticOperationSchema = (
    23,
    n0,
    _s191,
    0,
    JSON_ENUMS_INPUT,
    JSON_ENUMS_OUTPUT,
    (),
)

JSON_INT_ENUMS: StaticOperationSchema = (
    23,
    n0,
    _s192,
    0,
    JSON_INT_ENUMS_INPUT,
    JSON_INT_ENUMS_OUTPUT,
    (),
)

JSON_UNIONS: StaticOperationSchema = (
    23,
    n0,
    _s193,
    0,
    JSON_UNIONS_INPUT,
    JSON_UNIONS_OUTPUT,
    (),
)

KITCHEN_SINK_OPERATION: StaticOperationSchema = (
    23,
    n0,
    _s194,
    0,
    KITCHEN_SINK_OPERATION_INPUT,
    KITCHEN_SINK_OPERATION_OUTPUT,
    (ERROR_WITH_MEMBERS, ERROR_WITHOUT_MEMBERS),
)

NULL_OPERATION: StaticOperationSchema = (
    23,
    n0,
    _s195,
    0,
    NULL_OPERATION_INPUT,
    NULL_OPERATION_OUTPUT,
    (),
)

OPERATION_WITH_OPTIONAL_INPUT_OUTPUT: StaticOperationSchema = (
    23,
    n0,
    _s196,
    0,
    OPERATION_WITH_OPTIONAL_INPUT_OUTPUT_INPUT,
    OPERATION_WITH_OPTIONAL_INPUT_OUTPUT_OUTPUT,
    (),
)

PUT_AND_GET_INLINE_DOCUMENTS: StaticOperationSchema = (
    23,
    n0,
    _s197,
    0,
    PUT_AND_GET_INLINE_DOCUMENTS_INPUT,
    PUT_AND_GET_INLINE_DOCUMENTS_OUTPUT,
    (),
)

PUT_WITH_CONTENT_ENCODING: StaticOperationSchema = (
    23,
    n0,
    _s198,
    {_s199: MappingProxyType({"encodings": ("gzip",)})},
    PUT_WITH_CONTENT_ENCODING_INPUT,
    PUT_WITH_CONTENT_ENCODING_OUTPUT,
    (),
)

SIMPLE_SCALAR_PROPERTIES: StaticOperationSchema = (
    23,
    n0,
    _s200,
    0,
    SIMPLE_SCALAR_PROPERTIES_INPUT,
    SIMPLE_SCALAR_PROPERTIES_OUTPUT,
    (),
)

SPARSE_NULLS_OPERATION: StaticOperationSchema = (
    23,
    n0,
    _s201,
    0,
    SPARSE_NULLS_OPERATION_INPUT,
    SPARSE_NULLS_OPERATION_OUTPUT,
    (),
)

JSON_PROTOCOL: StaticSchema = (
    21,
    n0,
    _s202,
    {
        _s203: MappingProxyType(
            {
                "sdkId": "Json Protocol",
                "arnNamespace": "jsonprotocol",
                "cloudFormationName": "JsonProtocol",
                "cloudTrailEventSource": "jsonprotocol.amazonaws.com",
            }
        ),
        _s204: MappingProxyType({"name": "jsonprotocol"}),
        _s205: None,
    },
)

KITCHEN_SINK: StaticSchema = (
    18,
    n0,
    _s206,
    0,
    (
        _s144,
        _s145,
        _s146,
        _s24,
        _s147,
        _s148,
        _s150,
        _s151,
        _s25,
        _s152,
        _s33,
        _s28,
        _s36,
        _s153,
        _s37,
        _s154,
        _s31,
        _s39,
        _s155,
        _s156,
        _s157,
        _s34,
        _s158,
        _s40,
        _s159,
        _s160,
    ),
    (
        (1, 0),
        (2, 0),
        (10, 0),
        (EMPTY_STRUCT, 0),
        (9, 0),
        (4, {_s18: _s149}),
        (7, 0),
        (4, {_s18: _s19}),
        (JSON_VALUE, 0),
        (LIST_OF_LIST_OF_STRINGS, 0),
        (LIST_OF_MAPS_OF_STRINGS, 0),
        (LIST_OF_STRINGS, 0),
        (LIST_OF_STRUCTS, 0),
        (8, 0),
        (MAP_OF_LISTS_OF_STRINGS, 0),
        (MAP_OF_MAP_OF_STRINGS, 0),
        (MAP_OF_STRINGS, 0),
        (MAP_OF_STRUCTS, 0),
        (lambda: LIST_OF_KITCHEN_SINKS, 0),
        (lambda: MAP_OF_KITCHEN_SINKS, 0),
        (lambda: KITCHEN_SINK, 0),
        (SIMPLE_STRUCT, 0),
        (3, 0),
        (STRUCT_WITH_JSON_NAME, 0),
        (4, 0),
        (4, {_s18: _s161}),
    ),
)

LIST_OF_KITCHEN_SINKS: StaticSchema = (
    16,
    n0,
    _s207,
    0,
    (_s29,),
    ((KITCHEN_SINK, 0),),
)

MAP_OF_KITCHEN_SINKS: StaticSchema = (
    17,
    n0,
    _s208,
    0,
    (_s32, _s13),
    ((3, 0), (KITCHEN_SINK, 0)),
)
