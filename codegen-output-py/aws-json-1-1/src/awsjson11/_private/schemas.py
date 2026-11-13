from smithy_core._schema_compact import StaticSchema

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
_s10 = "smithy.api#input"
_s11 = "value"
_s12 = "ContentTypeParametersOutput"
_s13 = "smithy.api#output"
n1 = "aws.protocoltests.shared"
_s14 = "DateTime"
_s15 = "smithy.api#timestampFormat"
_s16 = "date-time"
_s17 = "DatetimeOffsetsOutput"
_s18 = "datetime"
_s19 = "Document"
_s20 = "EmptyStruct"
_s21 = "JsonValue"
_s22 = "smithy.api#mediaType"
_s23 = "application/json"
_s24 = "ListOfStrings"
_s25 = "member"
_s26 = "ListOfListOfStrings"
_s27 = "MapOfStrings"
_s28 = "key"
_s29 = "ListOfMapsOfStrings"
_s30 = "SimpleStruct"
_s31 = "Value"
_s32 = "ListOfStructs"
_s33 = "MapOfListsOfStrings"
_s34 = "MapOfMapOfStrings"
_s35 = "MapOfStructs"
_s36 = "StructWithJsonName"
_s37 = "RenamedMember"
_s38 = "ErrorWithMembers"
_s39 = "Code"
_s40 = "ComplexData"
_s41 = "IntegerField"
_s42 = "ListField"
_s43 = "MapField"
_s44 = "Message"
_s45 = "StringField"
_s46 = "ErrorWithoutMembers"
_s47 = "server"
_s48 = "FooError"
_s49 = "FractionalSecondsOutput"
_s50 = "GreetingWithErrorsOutput"
_s51 = "greeting"
_s52 = "HostLabelInput"
_s53 = "label"
_s54 = "InvalidGreeting"
_s55 = "FooEnum"
_s56 = "FOO"
_s57 = "smithy.api#enumValue"
_s58 = "BAZ"
_s59 = "Baz"
_s60 = "BAR"
_s61 = "Bar"
_s62 = "ONE"
_s63 = "1"
_s64 = "ZERO"
_s65 = "0"
_s66 = "FooEnumList"
_s67 = "FooEnumSet"
_s68 = "FooEnumMap"
_s69 = "JsonEnumsInputOutput"
_s70 = "fooEnum1"
_s71 = "fooEnum2"
_s72 = "fooEnum3"
_s73 = "fooEnumList"
_s74 = "fooEnumSet"
_s75 = "fooEnumMap"
_s76 = "IntegerEnum"
_s77 = "A"
_s78 = "B"
_s79 = "C"
_s80 = "IntegerEnumList"
_s81 = "IntegerEnumSet"
_s82 = "IntegerEnumMap"
_s83 = "JsonIntEnumsInputOutput"
_s84 = "intEnum1"
_s85 = "intEnum2"
_s86 = "intEnum3"
_s87 = "intEnumList"
_s88 = "intEnumSet"
_s89 = "intEnumMap"
_s90 = "StringList"
_s91 = "StringMap"
_s92 = "GreetingStruct"
_s93 = "hi"
_s94 = "MyUnion"
_s95 = "stringValue"
_s96 = "booleanValue"
_s97 = "numberValue"
_s98 = "blobValue"
_s99 = "timestampValue"
_s100 = "enumValue"
_s101 = "listValue"
_s102 = "mapValue"
_s103 = "structureValue"
_s104 = "NullOperationInputOutput"
_s105 = "string"
_s106 = "OperationWithOptionalInputOutputInput"
_s107 = "OperationWithOptionalInputOutputOutput"
_s108 = "PutAndGetInlineDocumentsInputOutput"
_s109 = "inlineDocument"
_s110 = "PutWithContentEncodingInput"
_s111 = "encoding"
_s112 = "smithy.api#httpHeader"
_s113 = "Content-Encoding"
_s114 = "data"
_s115 = "SimpleScalarPropertiesInputOutput"
_s116 = "floatValue"
_s117 = "doubleValue"
_s118 = "SparseStringList"
_s119 = "SparseStringMap"
_s120 = "SparseNullsOperationInputOutput"
_s121 = "sparseStringList"
_s122 = "sparseStringMap"
_s123 = "UnionInputOutput"
_s124 = "contents"
_s125 = "KitchenSink"
_s126 = "Blob"
_s127 = "Boolean"
_s128 = "Double"
_s129 = "Float"
_s130 = "HttpdateTimestamp"
_s131 = "http-date"
_s132 = "Integer"
_s133 = "Iso8601Timestamp"
_s134 = "ListOfLists"
_s135 = "Long"
_s136 = "MapOfMaps"
_s137 = "RecursiveList"
_s138 = "RecursiveMap"
_s139 = "RecursiveStruct"
_s140 = "String"
_s141 = "Timestamp"
_s142 = "UnixTimestamp"
_s143 = "epoch-seconds"
_s144 = "ListOfKitchenSinks"
_s145 = "MapOfKitchenSinks"

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
    (
        _s7,
        _s8,
    ),
    (
        (3, 0),
        (COMPLEX_NESTED_ERROR_DATA, 0),
    ),
)

CONTENT_TYPE_PARAMETERS_INPUT: StaticSchema = (
    18,
    n0,
    _s9,
    {_s10: None},
    (_s11,),
    ((7, 0),),
)

CONTENT_TYPE_PARAMETERS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s12,
    {_s13: None},
)

DATE_TIME: StaticSchema = (
    4,
    n1,
    _s14,
    {_s15: _s16},
)

DATETIME_OFFSETS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s17,
    {_s13: None},
    (_s18,),
    ((DATE_TIME, 0),),
)

DOCUMENT: StaticSchema = (
    13,
    n0,
    _s19,
    0,
)

EMPTY_STRUCT: StaticSchema = (
    18,
    n0,
    _s20,
    0,
)

JSON_VALUE: StaticSchema = (
    3,
    n0,
    _s21,
    {_s22: _s23},
)

LIST_OF_STRINGS: StaticSchema = (
    16,
    n0,
    _s24,
    0,
    (_s25,),
    ((3, 0),),
)

LIST_OF_LIST_OF_STRINGS: StaticSchema = (
    16,
    n0,
    _s26,
    0,
    (_s25,),
    ((LIST_OF_STRINGS, 0),),
)

MAP_OF_STRINGS: StaticSchema = (
    17,
    n0,
    _s27,
    0,
    (
        _s28,
        _s11,
    ),
    (
        (3, 0),
        (3, 0),
    ),
)

LIST_OF_MAPS_OF_STRINGS: StaticSchema = (
    16,
    n0,
    _s29,
    0,
    (_s25,),
    ((MAP_OF_STRINGS, 0),),
)

SIMPLE_STRUCT: StaticSchema = (
    18,
    n0,
    _s30,
    0,
    (_s31,),
    ((3, 0),),
)

LIST_OF_STRUCTS: StaticSchema = (
    16,
    n0,
    _s32,
    0,
    (_s25,),
    ((SIMPLE_STRUCT, 0),),
)

MAP_OF_LISTS_OF_STRINGS: StaticSchema = (
    17,
    n0,
    _s33,
    0,
    (
        _s28,
        _s11,
    ),
    (
        (3, 0),
        (LIST_OF_STRINGS, 0),
    ),
)

MAP_OF_MAP_OF_STRINGS: StaticSchema = (
    17,
    n0,
    _s34,
    0,
    (
        _s28,
        _s11,
    ),
    (
        (3, 0),
        (MAP_OF_STRINGS, 0),
    ),
)

MAP_OF_STRUCTS: StaticSchema = (
    17,
    n0,
    _s35,
    0,
    (
        _s28,
        _s11,
    ),
    (
        (3, 0),
        (SIMPLE_STRUCT, 0),
    ),
)

STRUCT_WITH_JSON_NAME: StaticSchema = (
    18,
    n0,
    _s36,
    0,
    (_s31,),
    ((3, {_s2: _s37}),),
)

ERROR_WITH_MEMBERS: StaticSchema = (
    18,
    n0,
    _s38,
    {_s5: _s6},
    (
        _s39,
        _s40,
        _s41,
        _s42,
        _s43,
        _s44,
        _s45,
    ),
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
    _s46,
    {_s5: _s47},
)

FOO_ERROR: StaticSchema = (
    18,
    n0,
    _s48,
    {_s5: _s47},
)

FRACTIONAL_SECONDS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s49,
    {_s13: None},
    (_s18,),
    ((DATE_TIME, 0),),
)

GREETING_WITH_ERRORS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s50,
    {_s13: None},
    (_s51,),
    ((3, 0),),
)

HOST_LABEL_INPUT: StaticSchema = (
    18,
    n0,
    _s52,
    {_s10: None},
    (_s53,),
    ((3, 257),),
)

INVALID_GREETING: StaticSchema = (
    18,
    n0,
    _s54,
    {_s5: _s6},
    (_s44,),
    ((3, 0),),
)

FOO_ENUM: StaticSchema = (
    14,
    n1,
    _s55,
    0,
    (
        _s56,
        _s58,
        _s60,
        _s62,
        _s64,
    ),
    (
        (-1, {_s57: _s1}),
        (-1, {_s57: _s59}),
        (-1, {_s57: _s61}),
        (-1, {_s57: _s63}),
        (-1, {_s57: _s65}),
    ),
)

FOO_ENUM_LIST: StaticSchema = (
    16,
    n1,
    _s66,
    0,
    (_s25,),
    ((FOO_ENUM, 0),),
)

FOO_ENUM_SET: StaticSchema = (
    16,
    n1,
    _s67,
    0,
    (_s25,),
    ((FOO_ENUM, 0),),
)

FOO_ENUM_MAP: StaticSchema = (
    17,
    n1,
    _s68,
    0,
    (
        _s28,
        _s11,
    ),
    (
        (3, 0),
        (FOO_ENUM, 0),
    ),
)

JSON_ENUMS_INPUT_OUTPUT: StaticSchema = (
    18,
    n0,
    _s69,
    {_s10: None, _s13: None},
    (
        _s70,
        _s71,
        _s72,
        _s73,
        _s74,
        _s75,
    ),
    (
        (FOO_ENUM, 0),
        (FOO_ENUM, 0),
        (FOO_ENUM, 0),
        (FOO_ENUM_LIST, 0),
        (FOO_ENUM_SET, 0),
        (FOO_ENUM_MAP, 0),
    ),
)

INTEGER_ENUM: StaticSchema = (
    15,
    n1,
    _s76,
    0,
    (
        _s77,
        _s78,
        _s79,
    ),
    (
        (-1, {_s57: 1}),
        (-1, {_s57: 2}),
        (-1, {_s57: 3}),
    ),
)

INTEGER_ENUM_LIST: StaticSchema = (
    16,
    n1,
    _s80,
    0,
    (_s25,),
    ((INTEGER_ENUM, 0),),
)

INTEGER_ENUM_SET: StaticSchema = (
    16,
    n1,
    _s81,
    0,
    (_s25,),
    ((INTEGER_ENUM, 0),),
)

INTEGER_ENUM_MAP: StaticSchema = (
    17,
    n1,
    _s82,
    0,
    (
        _s28,
        _s11,
    ),
    (
        (3, 0),
        (INTEGER_ENUM, 0),
    ),
)

JSON_INT_ENUMS_INPUT_OUTPUT: StaticSchema = (
    18,
    n0,
    _s83,
    {_s10: None, _s13: None},
    (
        _s84,
        _s85,
        _s86,
        _s87,
        _s88,
        _s89,
    ),
    (
        (INTEGER_ENUM, 0),
        (INTEGER_ENUM, 0),
        (INTEGER_ENUM, 0),
        (INTEGER_ENUM_LIST, 0),
        (INTEGER_ENUM_SET, 0),
        (INTEGER_ENUM_MAP, 0),
    ),
)

STRING_LIST: StaticSchema = (
    16,
    n1,
    _s90,
    0,
    (_s25,),
    ((3, 0),),
)

STRING_MAP: StaticSchema = (
    17,
    n1,
    _s91,
    0,
    (
        _s28,
        _s11,
    ),
    (
        (3, 0),
        (3, 0),
    ),
)

GREETING_STRUCT: StaticSchema = (
    18,
    n1,
    _s92,
    0,
    (_s93,),
    ((3, 0),),
)

MY_UNION: StaticSchema = (
    19,
    n0,
    _s94,
    0,
    (
        _s95,
        _s96,
        _s97,
        _s98,
        _s99,
        _s100,
        _s101,
        _s102,
        _s103,
    ),
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

NULL_OPERATION_INPUT_OUTPUT: StaticSchema = (
    18,
    n0,
    _s104,
    {_s10: None, _s13: None},
    (_s105,),
    ((3, 0),),
)

OPERATION_WITH_OPTIONAL_INPUT_OUTPUT_INPUT: StaticSchema = (
    18,
    n0,
    _s106,
    {_s10: None},
    (_s31,),
    ((3, 0),),
)

OPERATION_WITH_OPTIONAL_INPUT_OUTPUT_OUTPUT: StaticSchema = (
    18,
    n0,
    _s107,
    {_s13: None},
    (_s31,),
    ((3, 0),),
)

PUT_AND_GET_INLINE_DOCUMENTS_INPUT_OUTPUT: StaticSchema = (
    18,
    n0,
    _s108,
    {_s10: None, _s13: None},
    (_s109,),
    ((DOCUMENT, 0),),
)

PUT_WITH_CONTENT_ENCODING_INPUT: StaticSchema = (
    18,
    n0,
    _s110,
    {_s10: None},
    (
        _s111,
        _s114,
    ),
    (
        (3, {_s112: _s113}),
        (3, 0),
    ),
)

SIMPLE_SCALAR_PROPERTIES_INPUT_OUTPUT: StaticSchema = (
    18,
    n0,
    _s115,
    {_s10: None, _s13: None},
    (
        _s116,
        _s117,
    ),
    (
        (9, 0),
        (10, 0),
    ),
)

SPARSE_STRING_LIST: StaticSchema = (
    16,
    n1,
    _s118,
    64,
    (_s25,),
    ((3, 0),),
)

SPARSE_STRING_MAP: StaticSchema = (
    17,
    n1,
    _s119,
    64,
    (
        _s28,
        _s11,
    ),
    (
        (3, 0),
        (3, 0),
    ),
)

SPARSE_NULLS_OPERATION_INPUT_OUTPUT: StaticSchema = (
    18,
    n0,
    _s120,
    {_s10: None, _s13: None},
    (
        _s121,
        _s122,
    ),
    (
        (SPARSE_STRING_LIST, 0),
        (SPARSE_STRING_MAP, 0),
    ),
)

UNION_INPUT_OUTPUT: StaticSchema = (
    18,
    n0,
    _s123,
    {_s10: None, _s13: None},
    (_s124,),
    ((MY_UNION, 0),),
)

KITCHEN_SINK: StaticSchema = (
    18,
    n0,
    _s125,
    {_s10: None, _s13: None},
    (
        _s126,
        _s127,
        _s128,
        _s20,
        _s129,
        _s130,
        _s132,
        _s133,
        _s21,
        _s134,
        _s29,
        _s24,
        _s32,
        _s135,
        _s33,
        _s136,
        _s27,
        _s35,
        _s137,
        _s138,
        _s139,
        _s30,
        _s140,
        _s36,
        _s141,
        _s142,
    ),
    (
        (1, 0),
        (2, 0),
        (10, 0),
        (EMPTY_STRUCT, 0),
        (9, 0),
        (4, {_s15: _s131}),
        (7, 0),
        (4, {_s15: _s16}),
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
        (4, {_s15: _s143}),
    ),
)

LIST_OF_KITCHEN_SINKS: StaticSchema = (
    16,
    n0,
    _s144,
    0,
    (_s25,),
    ((KITCHEN_SINK, 0),),
)

MAP_OF_KITCHEN_SINKS: StaticSchema = (
    17,
    n0,
    _s145,
    0,
    (
        _s28,
        _s11,
    ),
    (
        (3, 0),
        (KITCHEN_SINK, 0),
    ),
)
