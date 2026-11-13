from types import MappingProxyType

from smithy_core._schema_compact import StaticSchema

n0 = "aws.protocoltests.query"
_s0 = "ComplexNestedErrorData"
_s1 = "Foo"
_s2 = "ComplexError"
_s3 = "smithy.api#error"
_s4 = "client"
_s5 = "TopLevel"
_s6 = "Nested"
n1 = "aws.protocoltests.shared"
_s7 = "GreetingStruct"
_s8 = "hi"
_s9 = "ComplexMap"
_s10 = "key"
_s11 = "value"
_s12 = "CustomCodeError"
_s13 = "aws.protocols#awsQueryError"
_s14 = "Message"
_s15 = "DateTime"
_s16 = "smithy.api#timestampFormat"
_s17 = "date-time"
_s18 = "DatetimeOffsetsOutput"
_s19 = "smithy.api#output"
_s20 = "datetime"
_s21 = "EmptyInputAndEmptyOutputInput"
_s22 = "smithy.api#input"
_s23 = "EmptyInputAndEmptyOutputOutput"
_s24 = "FooEnum"
_s25 = "FOO"
_s26 = "smithy.api#enumValue"
_s27 = "BAZ"
_s28 = "Baz"
_s29 = "BAR"
_s30 = "Bar"
_s31 = "ONE"
_s32 = "1"
_s33 = "ZERO"
_s34 = "0"
_s35 = "FooEnumMap"
_s36 = "FlattenedXmlMapOutput"
_s37 = "myMap"
_s38 = "smithy.api#xmlFlattened"
_s39 = "FlattenedXmlMapWithXmlNameOutputMap"
_s40 = "smithy.api#xmlName"
_s41 = "K"
_s42 = "V"
_s43 = "FlattenedXmlMapWithXmlNameOutput"
_s44 = "KVP"
_s45 = "FlattenedXmlMapWithXmlNamespaceOutputMap"
_s46 = "smithy.api#xmlNamespace"
_s47 = "FlattenedXmlMapWithXmlNamespaceOutput"
_s48 = "FractionalSecondsOutput"
_s49 = "GreetingWithErrorsOutput"
_s50 = "greeting"
_s51 = "HostLabelInput"
_s52 = "label"
_s53 = "IgnoresWrappingXmlNameOutput"
_s54 = "IgnoreMe"
_s55 = "foo"
_s56 = "InvalidGreeting"
_s57 = "ListWithMemberNamespace"
_s58 = "member"
_s59 = "ListWithNamespace"
_s60 = "ListWithXmlName"
_s61 = "item"
_s62 = "StringList"
_s63 = "MapOfLists"
_s64 = "MapWithXmlName"
_s65 = "NestedStructWithList"
_s66 = "ListArg"
_s67 = "StringMap"
_s68 = "NestedStructWithMap"
_s69 = "MapArg"
_s70 = "NestedStructuresInput"
_s71 = "NoInputAndOutputInput"
_s72 = "NoInputAndOutputOutput"
_s73 = "PutWithContentEncodingInput"
_s74 = "encoding"
_s75 = "smithy.api#httpHeader"
_s76 = "Content-Encoding"
_s77 = "data"
_s78 = "QueryIdempotencyTokenAutoFillInput"
_s79 = "token"
_s80 = "GreetingList"
_s81 = "QueryListsInput"
_s82 = "ComplexListArg"
_s83 = "FlattenedListArg"
_s84 = "ListArgWithXmlNameMember"
_s85 = "FlattenedListArgWithXmlName"
_s86 = "Hi"
_s87 = "NestedWithList"
_s88 = "QueryMapsInput"
_s89 = "RenamedMapArg"
_s90 = "ComplexMapArg"
_s91 = "MapWithXmlMemberName"
_s92 = "FlattenedMap"
_s93 = "FlattenedMapWithXmlName"
_s94 = "EpochSeconds"
_s95 = "epoch-seconds"
_s96 = "QueryTimestampsInput"
_s97 = "normalFormat"
_s98 = "epochMember"
_s99 = "epochTarget"
_s100 = "RecursiveXmlShapesOutput"
_s101 = "nested"
_s102 = "RenamedListMembers"
_s103 = "IntegerEnum"
_s104 = "A"
_s105 = "B"
_s106 = "C"
_s107 = "SimpleInputParamsInput"
_s108 = "Bam"
_s109 = "FloatValue"
_s110 = "Boo"
_s111 = "Qux"
_s112 = "SimpleScalarXmlPropertiesOutput"
_s113 = "stringValue"
_s114 = "emptyStringValue"
_s115 = "trueBooleanValue"
_s116 = "falseBooleanValue"
_s117 = "byteValue"
_s118 = "shortValue"
_s119 = "integerValue"
_s120 = "longValue"
_s121 = "floatValue"
_s122 = "doubleValue"
_s123 = "DoubleDribble"
_s124 = "StructureListMember"
_s125 = "a"
_s126 = "b"
_s127 = "other"
_s128 = "StructureList"
_s129 = "XmlBlobsOutput"
_s130 = "FooEnumList"
_s131 = "FooEnumSet"
_s132 = "XmlEnumsOutput"
_s133 = "fooEnum1"
_s134 = "fooEnum2"
_s135 = "fooEnum3"
_s136 = "fooEnumList"
_s137 = "fooEnumSet"
_s138 = "fooEnumMap"
_s139 = "IntegerEnumList"
_s140 = "IntegerEnumSet"
_s141 = "IntegerEnumMap"
_s142 = "XmlIntEnumsOutput"
_s143 = "intEnum1"
_s144 = "intEnum2"
_s145 = "intEnum3"
_s146 = "intEnumList"
_s147 = "intEnumSet"
_s148 = "intEnumMap"
_s149 = "StringSet"
_s150 = "IntegerList"
_s151 = "BooleanList"
_s152 = "TimestampList"
_s153 = "NestedStringList"
_s154 = "XmlListsOutput"
_s155 = "stringList"
_s156 = "stringSet"
_s157 = "integerList"
_s158 = "booleanList"
_s159 = "timestampList"
_s160 = "enumList"
_s161 = "nestedStringList"
_s162 = "renamedListMembers"
_s163 = "renamed"
_s164 = "flattenedList"
_s165 = "flattenedList2"
_s166 = "customName"
_s167 = "flattenedListWithMemberNamespace"
_s168 = "flattenedListWithNamespace"
_s169 = "structureList"
_s170 = "myStructureList"
_s171 = "XmlMapsOutputMap"
_s172 = "XmlMapsOutput"
_s173 = "XmlMapsXmlNameOutputMap"
_s174 = "Attribute"
_s175 = "Setting"
_s176 = "XmlMapsXmlNameOutput"
_s177 = "XmlNamespacedList"
_s178 = "XmlNamespaceNested"
_s179 = "values"
_s180 = "XmlNamespacesOutput"
_s181 = "HttpDate"
_s182 = "http-date"
_s183 = "XmlTimestampsOutput"
_s184 = "normal"
_s185 = "dateTime"
_s186 = "dateTimeOnTarget"
_s187 = "epochSeconds"
_s188 = "epochSecondsOnTarget"
_s189 = "httpDate"
_s190 = "httpDateOnTarget"
_s191 = "RecursiveXmlShapesOutputNested1"
_s192 = "RecursiveXmlShapesOutputNested2"
_s193 = "bar"
_s194 = "recursiveMember"
_s195 = "StructArg"
_s196 = "StringArg"
_s197 = "OtherArg"
_s198 = "RecursiveArg"

COMPLEX_NESTED_ERROR_DATA: StaticSchema = (
    18,
    n0,
    _s0,
    0,
    (_s1,),
    ((3, 0),),
)

COMPLEX_ERROR: StaticSchema = (
    18,
    n0,
    _s2,
    {_s3: _s4},
    (
        _s5,
        _s6,
    ),
    (
        (3, 0),
        (COMPLEX_NESTED_ERROR_DATA, 0),
    ),
)

GREETING_STRUCT: StaticSchema = (
    18,
    n1,
    _s7,
    0,
    (_s8,),
    ((3, 0),),
)

COMPLEX_MAP: StaticSchema = (
    17,
    n0,
    _s9,
    0,
    (
        _s10,
        _s11,
    ),
    (
        (3, 0),
        (GREETING_STRUCT, 0),
    ),
)

CUSTOM_CODE_ERROR: StaticSchema = (
    18,
    n0,
    _s12,
    {_s13: MappingProxyType({"code": "Customized", "httpResponseCode": 402}), _s3: _s4},
    (_s14,),
    ((3, 0),),
)

DATE_TIME: StaticSchema = (
    4,
    n1,
    _s15,
    {_s16: _s17},
)

DATETIME_OFFSETS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s18,
    {_s19: None},
    (_s20,),
    ((DATE_TIME, 0),),
)

EMPTY_INPUT_AND_EMPTY_OUTPUT_INPUT: StaticSchema = (
    18,
    n0,
    _s21,
    {_s22: None},
)

EMPTY_INPUT_AND_EMPTY_OUTPUT_OUTPUT: StaticSchema = (
    18,
    n0,
    _s23,
    {_s19: None},
)

FOO_ENUM: StaticSchema = (
    14,
    n1,
    _s24,
    0,
    (
        _s25,
        _s27,
        _s29,
        _s31,
        _s33,
    ),
    (
        (-1, {_s26: _s1}),
        (-1, {_s26: _s28}),
        (-1, {_s26: _s30}),
        (-1, {_s26: _s32}),
        (-1, {_s26: _s34}),
    ),
)

FOO_ENUM_MAP: StaticSchema = (
    17,
    n1,
    _s35,
    0,
    (
        _s10,
        _s11,
    ),
    (
        (3, 0),
        (FOO_ENUM, 0),
    ),
)

FLATTENED_XML_MAP_OUTPUT: StaticSchema = (
    18,
    n0,
    _s36,
    {_s19: None},
    (_s37,),
    ((FOO_ENUM_MAP, {_s38: None}),),
)

FLATTENED_XML_MAP_WITH_XML_NAME_OUTPUT_MAP: StaticSchema = (
    17,
    n0,
    _s39,
    0,
    (
        _s10,
        _s11,
    ),
    (
        (3, {_s40: _s41}),
        (3, {_s40: _s42}),
    ),
)

FLATTENED_XML_MAP_WITH_XML_NAME_OUTPUT: StaticSchema = (
    18,
    n0,
    _s43,
    {_s19: None},
    (_s37,),
    ((FLATTENED_XML_MAP_WITH_XML_NAME_OUTPUT_MAP, {_s38: None, _s40: _s44}),),
)

FLATTENED_XML_MAP_WITH_XML_NAMESPACE_OUTPUT_MAP: StaticSchema = (
    17,
    n0,
    _s45,
    0,
    (
        _s10,
        _s11,
    ),
    (
        (
            3,
            {
                _s40: _s41,
                _s46: MappingProxyType({"uri": "https://the-key.example.com"}),
            },
        ),
        (
            3,
            {
                _s40: _s42,
                _s46: MappingProxyType({"uri": "https://the-value.example.com"}),
            },
        ),
    ),
)

FLATTENED_XML_MAP_WITH_XML_NAMESPACE_OUTPUT: StaticSchema = (
    18,
    n0,
    _s47,
    {_s19: None},
    (_s37,),
    (
        (
            FLATTENED_XML_MAP_WITH_XML_NAMESPACE_OUTPUT_MAP,
            {
                _s38: None,
                _s40: _s44,
                _s46: MappingProxyType({"uri": "https://the-member.example.com"}),
            },
        ),
    ),
)

FRACTIONAL_SECONDS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s48,
    {_s19: None},
    (_s20,),
    ((DATE_TIME, 0),),
)

GREETING_WITH_ERRORS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s49,
    {_s19: None},
    (_s50,),
    ((3, 0),),
)

HOST_LABEL_INPUT: StaticSchema = (
    18,
    n0,
    _s51,
    {_s22: None},
    (_s52,),
    ((3, 257),),
)

IGNORES_WRAPPING_XML_NAME_OUTPUT: StaticSchema = (
    18,
    n0,
    _s53,
    {_s40: _s54, _s19: None},
    (_s55,),
    ((3, 0),),
)

INVALID_GREETING: StaticSchema = (
    18,
    n0,
    _s56,
    {_s3: _s4},
    (_s14,),
    ((3, 0),),
)

LIST_WITH_MEMBER_NAMESPACE: StaticSchema = (
    16,
    n0,
    _s57,
    {_s46: MappingProxyType({"uri": "https://xml-list.example.com"})},
    (_s58,),
    ((3, {_s46: MappingProxyType({"uri": "https://xml-member.example.com"})}),),
)

LIST_WITH_NAMESPACE: StaticSchema = (
    16,
    n0,
    _s59,
    {_s46: MappingProxyType({"uri": "https://xml-list.example.com"})},
    (_s58,),
    ((3, 0),),
)

LIST_WITH_XML_NAME: StaticSchema = (
    16,
    n0,
    _s60,
    0,
    (_s58,),
    ((3, {_s40: _s61}),),
)

STRING_LIST: StaticSchema = (
    16,
    n1,
    _s62,
    0,
    (_s58,),
    ((3, 0),),
)

MAP_OF_LISTS: StaticSchema = (
    17,
    n0,
    _s63,
    0,
    (
        _s10,
        _s11,
    ),
    (
        (3, 0),
        (STRING_LIST, 0),
    ),
)

MAP_WITH_XML_NAME: StaticSchema = (
    17,
    n0,
    _s64,
    0,
    (
        _s10,
        _s11,
    ),
    (
        (3, {_s40: _s41}),
        (3, {_s40: _s42}),
    ),
)

NESTED_STRUCT_WITH_LIST: StaticSchema = (
    18,
    n0,
    _s65,
    0,
    (_s66,),
    ((STRING_LIST, 0),),
)

STRING_MAP: StaticSchema = (
    17,
    n1,
    _s67,
    0,
    (
        _s10,
        _s11,
    ),
    (
        (3, 0),
        (3, 0),
    ),
)

NESTED_STRUCT_WITH_MAP: StaticSchema = (
    18,
    n0,
    _s68,
    0,
    (_s69,),
    ((STRING_MAP, 0),),
)

NESTED_STRUCTURES_INPUT: StaticSchema = (
    18,
    n0,
    _s70,
    {_s22: None},
    (_s6,),
    ((lambda: STRUCT_ARG, 0),),
)

NO_INPUT_AND_OUTPUT_INPUT: StaticSchema = (
    18,
    n0,
    _s71,
    {_s22: None},
)

NO_INPUT_AND_OUTPUT_OUTPUT: StaticSchema = (
    18,
    n0,
    _s72,
    {_s19: None},
)

PUT_WITH_CONTENT_ENCODING_INPUT: StaticSchema = (
    18,
    n0,
    _s73,
    {_s22: None},
    (
        _s74,
        _s77,
    ),
    (
        (3, {_s75: _s76}),
        (3, 0),
    ),
)

QUERY_IDEMPOTENCY_TOKEN_AUTO_FILL_INPUT: StaticSchema = (
    18,
    n0,
    _s78,
    {_s22: None},
    (_s79,),
    ((3, 2),),
)

GREETING_LIST: StaticSchema = (
    16,
    n1,
    _s80,
    0,
    (_s58,),
    ((GREETING_STRUCT, 0),),
)

QUERY_LISTS_INPUT: StaticSchema = (
    18,
    n0,
    _s81,
    {_s22: None},
    (
        _s66,
        _s82,
        _s83,
        _s84,
        _s85,
        _s87,
    ),
    (
        (STRING_LIST, 0),
        (GREETING_LIST, 0),
        (STRING_LIST, {_s38: None}),
        (LIST_WITH_XML_NAME, 0),
        (LIST_WITH_XML_NAME, {_s38: None, _s40: _s86}),
        (NESTED_STRUCT_WITH_LIST, 0),
    ),
)

QUERY_MAPS_INPUT: StaticSchema = (
    18,
    n0,
    _s88,
    {_s22: None},
    (
        _s69,
        _s89,
        _s90,
        _s91,
        _s92,
        _s93,
        _s63,
        _s68,
    ),
    (
        (STRING_MAP, 0),
        (STRING_MAP, {_s40: _s1}),
        (COMPLEX_MAP, 0),
        (MAP_WITH_XML_NAME, 0),
        (STRING_MAP, {_s38: None}),
        (MAP_WITH_XML_NAME, {_s38: None, _s40: _s86}),
        (MAP_OF_LISTS, 0),
        (NESTED_STRUCT_WITH_MAP, 0),
    ),
)

EPOCH_SECONDS: StaticSchema = (
    4,
    n1,
    _s94,
    {_s16: _s95},
)

QUERY_TIMESTAMPS_INPUT: StaticSchema = (
    18,
    n0,
    _s96,
    {_s22: None},
    (
        _s97,
        _s98,
        _s99,
    ),
    (
        (4, 0),
        (4, {_s16: _s95}),
        (EPOCH_SECONDS, 0),
    ),
)

RECURSIVE_XML_SHAPES_OUTPUT: StaticSchema = (
    18,
    n0,
    _s100,
    {_s19: None},
    (_s101,),
    ((lambda: RECURSIVE_XML_SHAPES_OUTPUT_NESTED1, 0),),
)

RENAMED_LIST_MEMBERS: StaticSchema = (
    16,
    n0,
    _s102,
    0,
    (_s58,),
    ((3, {_s40: _s61}),),
)

INTEGER_ENUM: StaticSchema = (
    15,
    n1,
    _s103,
    0,
    (
        _s104,
        _s105,
        _s106,
    ),
    (
        (-1, {_s26: 1}),
        (-1, {_s26: 2}),
        (-1, {_s26: 3}),
    ),
)

SIMPLE_INPUT_PARAMS_INPUT: StaticSchema = (
    18,
    n0,
    _s107,
    {_s22: None},
    (
        _s1,
        _s30,
        _s28,
        _s108,
        _s109,
        _s110,
        _s111,
        _s24,
        _s103,
    ),
    (
        (3, 0),
        (3, 0),
        (2, 0),
        (7, 0),
        (9, 0),
        (10, 0),
        (1, 0),
        (FOO_ENUM, 0),
        (INTEGER_ENUM, 0),
    ),
)

SIMPLE_SCALAR_XML_PROPERTIES_OUTPUT: StaticSchema = (
    18,
    n0,
    _s112,
    {_s19: None},
    (
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
    ),
    (
        (3, 0),
        (3, 0),
        (2, 0),
        (2, 0),
        (5, 0),
        (6, 0),
        (7, 0),
        (8, 0),
        (9, 0),
        (10, {_s40: _s123}),
    ),
)

STRUCTURE_LIST_MEMBER: StaticSchema = (
    18,
    n0,
    _s124,
    0,
    (
        _s125,
        _s126,
    ),
    (
        (3, {_s40: _s11}),
        (3, {_s40: _s127}),
    ),
)

STRUCTURE_LIST: StaticSchema = (
    16,
    n0,
    _s128,
    0,
    (_s58,),
    ((STRUCTURE_LIST_MEMBER, {_s40: _s61}),),
)

XML_BLOBS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s129,
    {_s19: None},
    (_s77,),
    ((1, 0),),
)

FOO_ENUM_LIST: StaticSchema = (
    16,
    n1,
    _s130,
    0,
    (_s58,),
    ((FOO_ENUM, 0),),
)

FOO_ENUM_SET: StaticSchema = (
    16,
    n1,
    _s131,
    0,
    (_s58,),
    ((FOO_ENUM, 0),),
)

XML_ENUMS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s132,
    {_s19: None},
    (
        _s133,
        _s134,
        _s135,
        _s136,
        _s137,
        _s138,
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

INTEGER_ENUM_LIST: StaticSchema = (
    16,
    n1,
    _s139,
    0,
    (_s58,),
    ((INTEGER_ENUM, 0),),
)

INTEGER_ENUM_SET: StaticSchema = (
    16,
    n1,
    _s140,
    0,
    (_s58,),
    ((INTEGER_ENUM, 0),),
)

INTEGER_ENUM_MAP: StaticSchema = (
    17,
    n1,
    _s141,
    0,
    (
        _s10,
        _s11,
    ),
    (
        (3, 0),
        (INTEGER_ENUM, 0),
    ),
)

XML_INT_ENUMS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s142,
    {_s19: None},
    (
        _s143,
        _s144,
        _s145,
        _s146,
        _s147,
        _s148,
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

STRING_SET: StaticSchema = (
    16,
    n1,
    _s149,
    0,
    (_s58,),
    ((3, 0),),
)

INTEGER_LIST: StaticSchema = (
    16,
    n1,
    _s150,
    0,
    (_s58,),
    ((7, 0),),
)

BOOLEAN_LIST: StaticSchema = (
    16,
    n1,
    _s151,
    0,
    (_s58,),
    ((2, 0),),
)

TIMESTAMP_LIST: StaticSchema = (
    16,
    n1,
    _s152,
    0,
    (_s58,),
    ((4, 0),),
)

NESTED_STRING_LIST: StaticSchema = (
    16,
    n1,
    _s153,
    0,
    (_s58,),
    ((STRING_LIST, 0),),
)

XML_LISTS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s154,
    {_s19: None},
    (
        _s155,
        _s156,
        _s157,
        _s158,
        _s159,
        _s160,
        _s146,
        _s161,
        _s162,
        _s164,
        _s165,
        _s167,
        _s168,
        _s169,
    ),
    (
        (STRING_LIST, 0),
        (STRING_SET, 0),
        (INTEGER_LIST, 0),
        (BOOLEAN_LIST, 0),
        (TIMESTAMP_LIST, 0),
        (FOO_ENUM_LIST, 0),
        (INTEGER_ENUM_LIST, 0),
        (NESTED_STRING_LIST, 0),
        (RENAMED_LIST_MEMBERS, {_s40: _s163}),
        (RENAMED_LIST_MEMBERS, {_s38: None}),
        (RENAMED_LIST_MEMBERS, {_s38: None, _s40: _s166}),
        (LIST_WITH_MEMBER_NAMESPACE, {_s38: None}),
        (LIST_WITH_NAMESPACE, {_s38: None}),
        (STRUCTURE_LIST, {_s40: _s170}),
    ),
)

XML_MAPS_OUTPUT_MAP: StaticSchema = (
    17,
    n0,
    _s171,
    0,
    (
        _s10,
        _s11,
    ),
    (
        (3, 0),
        (GREETING_STRUCT, 0),
    ),
)

XML_MAPS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s172,
    {_s19: None},
    (_s37,),
    ((XML_MAPS_OUTPUT_MAP, 0),),
)

XML_MAPS_XML_NAME_OUTPUT_MAP: StaticSchema = (
    17,
    n0,
    _s173,
    0,
    (
        _s10,
        _s11,
    ),
    (
        (3, {_s40: _s174}),
        (GREETING_STRUCT, {_s40: _s175}),
    ),
)

XML_MAPS_XML_NAME_OUTPUT: StaticSchema = (
    18,
    n0,
    _s176,
    {_s19: None},
    (_s37,),
    ((XML_MAPS_XML_NAME_OUTPUT_MAP, 0),),
)

XML_NAMESPACED_LIST: StaticSchema = (
    16,
    n0,
    _s177,
    0,
    (_s58,),
    ((3, {_s46: MappingProxyType({"uri": "http://bux.com"})}),),
)

XML_NAMESPACE_NESTED: StaticSchema = (
    18,
    n0,
    _s178,
    {_s46: MappingProxyType({"uri": "http://boo.com"})},
    (
        _s55,
        _s179,
    ),
    (
        (3, {_s46: MappingProxyType({"uri": "http://baz.com", "prefix": "baz"})}),
        (XML_NAMESPACED_LIST, {_s46: MappingProxyType({"uri": "http://qux.com"})}),
    ),
)

XML_NAMESPACES_OUTPUT: StaticSchema = (
    18,
    n0,
    _s180,
    {_s46: MappingProxyType({"uri": "http://foo.com"}), _s19: None},
    (_s101,),
    ((XML_NAMESPACE_NESTED, 0),),
)

HTTP_DATE: StaticSchema = (
    4,
    n1,
    _s181,
    {_s16: _s182},
)

XML_TIMESTAMPS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s183,
    {_s19: None},
    (
        _s184,
        _s185,
        _s186,
        _s187,
        _s188,
        _s189,
        _s190,
    ),
    (
        (4, 0),
        (4, {_s16: _s17}),
        (DATE_TIME, 0),
        (4, {_s16: _s95}),
        (EPOCH_SECONDS, 0),
        (4, {_s16: _s182}),
        (HTTP_DATE, 0),
    ),
)

RECURSIVE_XML_SHAPES_OUTPUT_NESTED1: StaticSchema = (
    18,
    n0,
    _s191,
    0,
    (
        _s55,
        _s101,
    ),
    (
        (3, 0),
        (lambda: RECURSIVE_XML_SHAPES_OUTPUT_NESTED2, 0),
    ),
)

RECURSIVE_XML_SHAPES_OUTPUT_NESTED2: StaticSchema = (
    18,
    n0,
    _s192,
    0,
    (
        _s193,
        _s194,
    ),
    (
        (3, 0),
        (RECURSIVE_XML_SHAPES_OUTPUT_NESTED1, 0),
    ),
)

STRUCT_ARG: StaticSchema = (
    18,
    n0,
    _s195,
    0,
    (
        _s196,
        _s197,
        _s198,
    ),
    (
        (3, 0),
        (2, 0),
        (lambda: STRUCT_ARG, 0),
    ),
)
