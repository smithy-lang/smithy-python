from types import MappingProxyType

from smithy_core._schema_compact import StaticSchema

n0 = "aws.protocoltests.ec2"
_s0 = "ComplexNestedErrorData"
_s1 = "Foo"
_s2 = "ComplexError"
_s3 = "smithy.api#error"
_s4 = "client"
_s5 = "TopLevel"
_s6 = "Nested"
n1 = "aws.protocoltests.shared"
_s7 = "DateTime"
_s8 = "smithy.api#timestampFormat"
_s9 = "date-time"
_s10 = "DatetimeOffsetsOutput"
_s11 = "smithy.api#output"
_s12 = "datetime"
_s13 = "EmptyInputAndEmptyOutputInput"
_s14 = "smithy.api#input"
_s15 = "EmptyInputAndEmptyOutputOutput"
_s16 = "FractionalSecondsOutput"
_s17 = "GreetingWithErrorsOutput"
_s18 = "greeting"
_s19 = "HostLabelInput"
_s20 = "label"
_s21 = "IgnoresWrappingXmlNameOutput"
_s22 = "smithy.api#xmlName"
_s23 = "IgnoreMe"
_s24 = "foo"
_s25 = "InvalidGreeting"
_s26 = "Message"
_s27 = "ListWithMemberNamespace"
_s28 = "smithy.api#xmlNamespace"
_s29 = "member"
_s30 = "ListWithNamespace"
_s31 = "ListWithXmlName"
_s32 = "item"
_s33 = "StringList"
_s34 = "NestedStructWithList"
_s35 = "ListArg"
_s36 = "NestedStructuresInput"
_s37 = "NoInputAndOutputOutput"
_s38 = "PutWithContentEncodingInput"
_s39 = "encoding"
_s40 = "smithy.api#httpHeader"
_s41 = "Content-Encoding"
_s42 = "data"
_s43 = "QueryIdempotencyTokenAutoFillInput"
_s44 = "token"
_s45 = "GreetingStruct"
_s46 = "hi"
_s47 = "GreetingList"
_s48 = "QueryListsInput"
_s49 = "ComplexListArg"
_s50 = "ListArgWithXmlNameMember"
_s51 = "ListArgWithXmlName"
_s52 = "Hi"
_s53 = "NestedWithList"
_s54 = "EpochSeconds"
_s55 = "epoch-seconds"
_s56 = "QueryTimestampsInput"
_s57 = "normalFormat"
_s58 = "epochMember"
_s59 = "epochTarget"
_s60 = "RecursiveXmlShapesOutput"
_s61 = "nested"
_s62 = "RenamedListMembers"
_s63 = "FooEnum"
_s64 = "FOO"
_s65 = "smithy.api#enumValue"
_s66 = "BAZ"
_s67 = "Baz"
_s68 = "BAR"
_s69 = "Bar"
_s70 = "ONE"
_s71 = "1"
_s72 = "ZERO"
_s73 = "0"
_s74 = "SimpleInputParamsInput"
_s75 = "Bam"
_s76 = "FloatValue"
_s77 = "Boo"
_s78 = "Qux"
_s79 = "HasQueryName"
_s80 = "aws.protocols#ec2QueryName"
_s81 = "HasQueryAndXmlName"
_s82 = "hasQueryAndXmlName"
_s83 = "UsesXmlName"
_s84 = "usesXmlName"
_s85 = "DistinctQueryName"
_s86 = "QueryName"
_s87 = "DistinctQueryAndXmlName"
_s88 = "queryAndXmlName"
_s89 = "xmlAndQueryName"
_s90 = "DistinctXmlName"
_s91 = "xmlNameOnly"
_s92 = "SimpleScalarXmlPropertiesOutput"
_s93 = "stringValue"
_s94 = "emptyStringValue"
_s95 = "trueBooleanValue"
_s96 = "falseBooleanValue"
_s97 = "byteValue"
_s98 = "shortValue"
_s99 = "integerValue"
_s100 = "longValue"
_s101 = "floatValue"
_s102 = "doubleValue"
_s103 = "DoubleDribble"
_s104 = "StructureListMember"
_s105 = "a"
_s106 = "value"
_s107 = "b"
_s108 = "other"
_s109 = "StructureList"
_s110 = "XmlBlobsOutput"
_s111 = "FooEnumList"
_s112 = "FooEnumSet"
_s113 = "FooEnumMap"
_s114 = "key"
_s115 = "XmlEnumsOutput"
_s116 = "fooEnum1"
_s117 = "fooEnum2"
_s118 = "fooEnum3"
_s119 = "fooEnumList"
_s120 = "fooEnumSet"
_s121 = "fooEnumMap"
_s122 = "IntegerEnum"
_s123 = "A"
_s124 = "B"
_s125 = "C"
_s126 = "IntegerEnumList"
_s127 = "IntegerEnumSet"
_s128 = "IntegerEnumMap"
_s129 = "XmlIntEnumsOutput"
_s130 = "intEnum1"
_s131 = "intEnum2"
_s132 = "intEnum3"
_s133 = "intEnumList"
_s134 = "intEnumSet"
_s135 = "intEnumMap"
_s136 = "StringSet"
_s137 = "IntegerList"
_s138 = "BooleanList"
_s139 = "TimestampList"
_s140 = "NestedStringList"
_s141 = "XmlListsOutput"
_s142 = "stringList"
_s143 = "stringSet"
_s144 = "integerList"
_s145 = "booleanList"
_s146 = "timestampList"
_s147 = "enumList"
_s148 = "nestedStringList"
_s149 = "renamedListMembers"
_s150 = "renamed"
_s151 = "flattenedList"
_s152 = "smithy.api#xmlFlattened"
_s153 = "flattenedList2"
_s154 = "customName"
_s155 = "flattenedListWithMemberNamespace"
_s156 = "flattenedListWithNamespace"
_s157 = "structureList"
_s158 = "myStructureList"
_s159 = "XmlNamespacedList"
_s160 = "XmlNamespaceNested"
_s161 = "values"
_s162 = "XmlNamespacesOutput"
_s163 = "HttpDate"
_s164 = "http-date"
_s165 = "XmlTimestampsOutput"
_s166 = "normal"
_s167 = "dateTime"
_s168 = "dateTimeOnTarget"
_s169 = "epochSeconds"
_s170 = "epochSecondsOnTarget"
_s171 = "httpDate"
_s172 = "httpDateOnTarget"
_s173 = "RecursiveXmlShapesOutputNested1"
_s174 = "RecursiveXmlShapesOutputNested2"
_s175 = "bar"
_s176 = "recursiveMember"
_s177 = "StructArg"
_s178 = "StringArg"
_s179 = "OtherArg"
_s180 = "RecursiveArg"

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

DATE_TIME: StaticSchema = (
    4,
    n1,
    _s7,
    {_s8: _s9},
)

DATETIME_OFFSETS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s10,
    {_s11: None},
    (_s12,),
    ((DATE_TIME, 0),),
)

EMPTY_INPUT_AND_EMPTY_OUTPUT_INPUT: StaticSchema = (
    18,
    n0,
    _s13,
    {_s14: None},
)

EMPTY_INPUT_AND_EMPTY_OUTPUT_OUTPUT: StaticSchema = (
    18,
    n0,
    _s15,
    {_s11: None},
)

FRACTIONAL_SECONDS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s16,
    {_s11: None},
    (_s12,),
    ((DATE_TIME, 0),),
)

GREETING_WITH_ERRORS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s17,
    {_s11: None},
    (_s18,),
    ((3, 0),),
)

HOST_LABEL_INPUT: StaticSchema = (
    18,
    n0,
    _s19,
    {_s14: None},
    (_s20,),
    ((3, 257),),
)

IGNORES_WRAPPING_XML_NAME_OUTPUT: StaticSchema = (
    18,
    n0,
    _s21,
    {_s22: _s23, _s11: None},
    (_s24,),
    ((3, 0),),
)

INVALID_GREETING: StaticSchema = (
    18,
    n0,
    _s25,
    {_s3: _s4},
    (_s26,),
    ((3, 0),),
)

LIST_WITH_MEMBER_NAMESPACE: StaticSchema = (
    16,
    n0,
    _s27,
    {_s28: MappingProxyType({"uri": "https://xml-list.example.com"})},
    (_s29,),
    ((3, {_s28: MappingProxyType({"uri": "https://xml-member.example.com"})}),),
)

LIST_WITH_NAMESPACE: StaticSchema = (
    16,
    n0,
    _s30,
    {_s28: MappingProxyType({"uri": "https://xml-list.example.com"})},
    (_s29,),
    ((3, 0),),
)

LIST_WITH_XML_NAME: StaticSchema = (
    16,
    n0,
    _s31,
    0,
    (_s29,),
    ((3, {_s22: _s32}),),
)

STRING_LIST: StaticSchema = (
    16,
    n1,
    _s33,
    0,
    (_s29,),
    ((3, 0),),
)

NESTED_STRUCT_WITH_LIST: StaticSchema = (
    18,
    n0,
    _s34,
    0,
    (_s35,),
    ((STRING_LIST, 0),),
)

NESTED_STRUCTURES_INPUT: StaticSchema = (
    18,
    n0,
    _s36,
    {_s14: None},
    (_s6,),
    ((lambda: STRUCT_ARG, 0),),
)

NO_INPUT_AND_OUTPUT_OUTPUT: StaticSchema = (
    18,
    n0,
    _s37,
    {_s11: None},
)

PUT_WITH_CONTENT_ENCODING_INPUT: StaticSchema = (
    18,
    n0,
    _s38,
    {_s14: None},
    (
        _s39,
        _s42,
    ),
    (
        (3, {_s40: _s41}),
        (3, 0),
    ),
)

QUERY_IDEMPOTENCY_TOKEN_AUTO_FILL_INPUT: StaticSchema = (
    18,
    n0,
    _s43,
    {_s14: None},
    (_s44,),
    ((3, 2),),
)

GREETING_STRUCT: StaticSchema = (
    18,
    n1,
    _s45,
    0,
    (_s46,),
    ((3, 0),),
)

GREETING_LIST: StaticSchema = (
    16,
    n1,
    _s47,
    0,
    (_s29,),
    ((GREETING_STRUCT, 0),),
)

QUERY_LISTS_INPUT: StaticSchema = (
    18,
    n0,
    _s48,
    {_s14: None},
    (
        _s35,
        _s49,
        _s50,
        _s51,
        _s53,
    ),
    (
        (STRING_LIST, 0),
        (GREETING_LIST, 0),
        (LIST_WITH_XML_NAME, 0),
        (LIST_WITH_XML_NAME, {_s22: _s52}),
        (NESTED_STRUCT_WITH_LIST, 0),
    ),
)

EPOCH_SECONDS: StaticSchema = (
    4,
    n1,
    _s54,
    {_s8: _s55},
)

QUERY_TIMESTAMPS_INPUT: StaticSchema = (
    18,
    n0,
    _s56,
    {_s14: None},
    (
        _s57,
        _s58,
        _s59,
    ),
    (
        (4, 0),
        (4, {_s8: _s55}),
        (EPOCH_SECONDS, 0),
    ),
)

RECURSIVE_XML_SHAPES_OUTPUT: StaticSchema = (
    18,
    n0,
    _s60,
    {_s11: None},
    (_s61,),
    ((lambda: RECURSIVE_XML_SHAPES_OUTPUT_NESTED1, 0),),
)

RENAMED_LIST_MEMBERS: StaticSchema = (
    16,
    n0,
    _s62,
    0,
    (_s29,),
    ((3, {_s22: _s32}),),
)

FOO_ENUM: StaticSchema = (
    14,
    n1,
    _s63,
    0,
    (
        _s64,
        _s66,
        _s68,
        _s70,
        _s72,
    ),
    (
        (-1, {_s65: _s1}),
        (-1, {_s65: _s67}),
        (-1, {_s65: _s69}),
        (-1, {_s65: _s71}),
        (-1, {_s65: _s73}),
    ),
)

SIMPLE_INPUT_PARAMS_INPUT: StaticSchema = (
    18,
    n0,
    _s74,
    {_s14: None},
    (
        _s1,
        _s69,
        _s67,
        _s75,
        _s76,
        _s77,
        _s78,
        _s63,
        _s79,
        _s81,
        _s83,
        _s85,
        _s87,
        _s90,
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
        (3, {_s80: _s79}),
        (3, {_s80: _s81, _s22: _s82}),
        (3, {_s22: _s84}),
        (3, {_s80: _s86}),
        (3, {_s80: _s88, _s22: _s89}),
        (3, {_s22: _s91}),
    ),
)

SIMPLE_SCALAR_XML_PROPERTIES_OUTPUT: StaticSchema = (
    18,
    n0,
    _s92,
    {_s11: None},
    (
        _s93,
        _s94,
        _s95,
        _s96,
        _s97,
        _s98,
        _s99,
        _s100,
        _s101,
        _s102,
    ),
    (
        (3, {_s80: _s23}),
        (3, 0),
        (2, 0),
        (2, 0),
        (5, 0),
        (6, 0),
        (7, 0),
        (8, 0),
        (9, 0),
        (10, {_s22: _s103}),
    ),
)

STRUCTURE_LIST_MEMBER: StaticSchema = (
    18,
    n0,
    _s104,
    0,
    (
        _s105,
        _s107,
    ),
    (
        (3, {_s22: _s106}),
        (3, {_s22: _s108}),
    ),
)

STRUCTURE_LIST: StaticSchema = (
    16,
    n0,
    _s109,
    0,
    (_s29,),
    ((STRUCTURE_LIST_MEMBER, {_s22: _s32}),),
)

XML_BLOBS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s110,
    {_s11: None},
    (_s42,),
    ((1, 0),),
)

FOO_ENUM_LIST: StaticSchema = (
    16,
    n1,
    _s111,
    0,
    (_s29,),
    ((FOO_ENUM, 0),),
)

FOO_ENUM_SET: StaticSchema = (
    16,
    n1,
    _s112,
    0,
    (_s29,),
    ((FOO_ENUM, 0),),
)

FOO_ENUM_MAP: StaticSchema = (
    17,
    n1,
    _s113,
    0,
    (
        _s114,
        _s106,
    ),
    (
        (3, 0),
        (FOO_ENUM, 0),
    ),
)

XML_ENUMS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s115,
    {_s11: None},
    (
        _s116,
        _s117,
        _s118,
        _s119,
        _s120,
        _s121,
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
    _s122,
    0,
    (
        _s123,
        _s124,
        _s125,
    ),
    (
        (-1, {_s65: 1}),
        (-1, {_s65: 2}),
        (-1, {_s65: 3}),
    ),
)

INTEGER_ENUM_LIST: StaticSchema = (
    16,
    n1,
    _s126,
    0,
    (_s29,),
    ((INTEGER_ENUM, 0),),
)

INTEGER_ENUM_SET: StaticSchema = (
    16,
    n1,
    _s127,
    0,
    (_s29,),
    ((INTEGER_ENUM, 0),),
)

INTEGER_ENUM_MAP: StaticSchema = (
    17,
    n1,
    _s128,
    0,
    (
        _s114,
        _s106,
    ),
    (
        (3, 0),
        (INTEGER_ENUM, 0),
    ),
)

XML_INT_ENUMS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s129,
    {_s11: None},
    (
        _s130,
        _s131,
        _s132,
        _s133,
        _s134,
        _s135,
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
    _s136,
    0,
    (_s29,),
    ((3, 0),),
)

INTEGER_LIST: StaticSchema = (
    16,
    n1,
    _s137,
    0,
    (_s29,),
    ((7, 0),),
)

BOOLEAN_LIST: StaticSchema = (
    16,
    n1,
    _s138,
    0,
    (_s29,),
    ((2, 0),),
)

TIMESTAMP_LIST: StaticSchema = (
    16,
    n1,
    _s139,
    0,
    (_s29,),
    ((4, 0),),
)

NESTED_STRING_LIST: StaticSchema = (
    16,
    n1,
    _s140,
    0,
    (_s29,),
    ((STRING_LIST, 0),),
)

XML_LISTS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s141,
    {_s11: None},
    (
        _s142,
        _s143,
        _s144,
        _s145,
        _s146,
        _s147,
        _s133,
        _s148,
        _s149,
        _s151,
        _s153,
        _s155,
        _s156,
        _s157,
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
        (RENAMED_LIST_MEMBERS, {_s22: _s150}),
        (RENAMED_LIST_MEMBERS, {_s152: None}),
        (RENAMED_LIST_MEMBERS, {_s152: None, _s22: _s154}),
        (LIST_WITH_MEMBER_NAMESPACE, {_s152: None}),
        (LIST_WITH_NAMESPACE, {_s152: None}),
        (STRUCTURE_LIST, {_s22: _s158}),
    ),
)

XML_NAMESPACED_LIST: StaticSchema = (
    16,
    n0,
    _s159,
    0,
    (_s29,),
    ((3, {_s28: MappingProxyType({"uri": "http://bux.com"})}),),
)

XML_NAMESPACE_NESTED: StaticSchema = (
    18,
    n0,
    _s160,
    {_s28: MappingProxyType({"uri": "http://foo.com"})},
    (
        _s24,
        _s161,
    ),
    (
        (3, {_s28: MappingProxyType({"uri": "http://baz.com", "prefix": "baz"})}),
        (XML_NAMESPACED_LIST, {_s28: MappingProxyType({"uri": "http://qux.com"})}),
    ),
)

XML_NAMESPACES_OUTPUT: StaticSchema = (
    18,
    n0,
    _s162,
    {_s28: MappingProxyType({"uri": "http://foo.com"}), _s11: None},
    (_s61,),
    ((XML_NAMESPACE_NESTED, 0),),
)

HTTP_DATE: StaticSchema = (
    4,
    n1,
    _s163,
    {_s8: _s164},
)

XML_TIMESTAMPS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s165,
    {_s11: None},
    (
        _s166,
        _s167,
        _s168,
        _s169,
        _s170,
        _s171,
        _s172,
    ),
    (
        (4, 0),
        (4, {_s8: _s9}),
        (DATE_TIME, 0),
        (4, {_s8: _s55}),
        (EPOCH_SECONDS, 0),
        (4, {_s8: _s164}),
        (HTTP_DATE, 0),
    ),
)

RECURSIVE_XML_SHAPES_OUTPUT_NESTED1: StaticSchema = (
    18,
    n0,
    _s173,
    0,
    (
        _s24,
        _s61,
    ),
    (
        (3, 0),
        (lambda: RECURSIVE_XML_SHAPES_OUTPUT_NESTED2, 0),
    ),
)

RECURSIVE_XML_SHAPES_OUTPUT_NESTED2: StaticSchema = (
    18,
    n0,
    _s174,
    0,
    (
        _s175,
        _s176,
    ),
    (
        (3, 0),
        (RECURSIVE_XML_SHAPES_OUTPUT_NESTED1, 0),
    ),
)

STRUCT_ARG: StaticSchema = (
    18,
    n0,
    _s177,
    0,
    (
        _s178,
        _s179,
        _s180,
    ),
    (
        (3, 0),
        (2, 0),
        (lambda: STRUCT_ARG, 0),
    ),
)
