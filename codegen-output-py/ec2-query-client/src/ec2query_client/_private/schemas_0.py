from types import MappingProxyType

from smithy_core._schema_compact import StaticOperationSchema, StaticSchema

from . import schemas

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
_s11 = "smithy.synthetic#originalShapeId"
_s12 = "aws.protocoltests.ec2#DatetimeOffsetsOutput"
_s13 = "smithy.api#output"
_s14 = "datetime"
_s15 = "EmptyInputAndEmptyOutputInput"
_s16 = "aws.protocoltests.ec2#EmptyInputAndEmptyOutputInput"
_s17 = "smithy.api#input"
_s18 = "EmptyInputAndEmptyOutputOutput"
_s19 = "aws.protocoltests.ec2#EmptyInputAndEmptyOutputOutput"
_s20 = "FractionalSecondsOutput"
_s21 = "aws.protocoltests.ec2#FractionalSecondsOutput"
_s22 = "GreetingWithErrorsOutput"
_s23 = "aws.protocoltests.ec2#GreetingWithErrorsOutput"
_s24 = "greeting"
_s25 = "IgnoresWrappingXmlNameOutput"
_s26 = "smithy.api#xmlName"
_s27 = "IgnoreMe"
_s28 = "aws.protocoltests.ec2#IgnoresWrappingXmlNameOutput"
_s29 = "foo"
_s30 = "InvalidGreeting"
_s31 = "Message"
_s32 = "ListWithMemberNamespace"
_s33 = "smithy.api#xmlNamespace"
_s34 = "member"
_s35 = "ListWithNamespace"
_s36 = "ListWithXmlName"
_s37 = "item"
_s38 = "StringList"
_s39 = "NestedStructWithList"
_s40 = "ListArg"
_s41 = "NestedStructuresInput"
_s42 = "aws.protocoltests.ec2#NestedStructuresInput"
_s43 = "NoInputAndOutputOutput"
_s44 = "aws.protocoltests.ec2#NoInputAndOutputOutput"
_s45 = "PutWithContentEncodingInput"
_s46 = "aws.protocoltests.ec2#PutWithContentEncodingInput"
_s47 = "encoding"
_s48 = "smithy.api#httpHeader"
_s49 = "Content-Encoding"
_s50 = "data"
_s51 = "QueryIdempotencyTokenAutoFillInput"
_s52 = "aws.protocoltests.ec2#QueryIdempotencyTokenAutoFillInput"
_s53 = "token"
_s54 = "GreetingStruct"
_s55 = "hi"
_s56 = "GreetingList"
_s57 = "QueryListsInput"
_s58 = "aws.protocoltests.ec2#QueryListsInput"
_s59 = "ComplexListArg"
_s60 = "ListArgWithXmlNameMember"
_s61 = "ListArgWithXmlName"
_s62 = "Hi"
_s63 = "NestedWithList"
_s64 = "EpochSeconds"
_s65 = "epoch-seconds"
_s66 = "QueryTimestampsInput"
_s67 = "aws.protocoltests.ec2#QueryTimestampsInput"
_s68 = "normalFormat"
_s69 = "epochMember"
_s70 = "epochTarget"
_s71 = "RecursiveXmlShapesOutput"
_s72 = "aws.protocoltests.ec2#RecursiveXmlShapesOutput"
_s73 = "nested"
_s74 = "RenamedListMembers"
_s75 = "FooEnum"
_s76 = "FOO"
_s77 = "smithy.api#enumValue"
_s78 = "BAZ"
_s79 = "Baz"
_s80 = "BAR"
_s81 = "Bar"
_s82 = "ONE"
_s83 = "1"
_s84 = "ZERO"
_s85 = "0"
_s86 = "SimpleInputParamsInput"
_s87 = "aws.protocoltests.ec2#SimpleInputParamsInput"
_s88 = "Bam"
_s89 = "FloatValue"
_s90 = "Boo"
_s91 = "Qux"
_s92 = "HasQueryName"
_s93 = "aws.protocols#ec2QueryName"
_s94 = "HasQueryAndXmlName"
_s95 = "hasQueryAndXmlName"
_s96 = "UsesXmlName"
_s97 = "usesXmlName"
_s98 = "DistinctQueryName"
_s99 = "QueryName"
_s100 = "DistinctQueryAndXmlName"
_s101 = "queryAndXmlName"
_s102 = "xmlAndQueryName"
_s103 = "DistinctXmlName"
_s104 = "xmlNameOnly"
_s105 = "SimpleScalarXmlPropertiesOutput"
_s106 = "aws.protocoltests.ec2#SimpleScalarXmlPropertiesOutput"
_s107 = "stringValue"
_s108 = "emptyStringValue"
_s109 = "trueBooleanValue"
_s110 = "falseBooleanValue"
_s111 = "byteValue"
_s112 = "shortValue"
_s113 = "integerValue"
_s114 = "longValue"
_s115 = "floatValue"
_s116 = "doubleValue"
_s117 = "DoubleDribble"
_s118 = "StructureListMember"
_s119 = "a"
_s120 = "value"
_s121 = "b"
_s122 = "other"
_s172 = "DatetimeOffsetsInput"
_s173 = "smithy.api#Unit"
_s180 = "FractionalSecondsInput"
_s181 = "GreetingWithErrorsInput"
_s184 = "IgnoresWrappingXmlNameInput"
_s185 = "NestedStructuresOutput"
_s186 = "NoInputAndOutputInput"
_s187 = "PutWithContentEncodingOutput"
_s188 = "QueryIdempotencyTokenAutoFillOutput"
_s189 = "QueryListsOutput"
_s190 = "QueryTimestampsOutput"
_s191 = "RecursiveXmlShapesInput"
_s192 = "SimpleInputParamsOutput"
_s193 = "SimpleScalarXmlPropertiesInput"
_s225 = "DatetimeOffsets"
_s226 = "EmptyInputAndEmptyOutput"
_s230 = "FractionalSeconds"
_s231 = "GreetingWithErrors"
_s233 = "IgnoresWrappingXmlName"
_s234 = "NestedStructures"
_s235 = "NoInputAndOutput"
_s236 = "PutWithContentEncoding"
_s237 = "smithy.api#requestCompression"
_s238 = "QueryIdempotencyTokenAutoFill"
_s239 = "QueryLists"
_s240 = "QueryTimestamps"
_s241 = "RecursiveXmlShapes"
_s242 = "SimpleInputParams"
_s243 = "SimpleScalarXmlProperties"

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
    (_s5, _s6),
    ((3, 0), (COMPLEX_NESTED_ERROR_DATA, 0)),
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
    {_s11: _s12, _s13: None},
    (_s14,),
    ((DATE_TIME, 0),),
)

DATETIME_OFFSETS_INPUT: StaticSchema = (
    18,
    n0,
    _s172,
    {_s11: _s173, _s17: None},
)

DATETIME_OFFSETS: StaticOperationSchema = (
    23,
    n0,
    _s225,
    0,
    DATETIME_OFFSETS_INPUT,
    DATETIME_OFFSETS_OUTPUT,
    (),
)

EMPTY_INPUT_AND_EMPTY_OUTPUT_INPUT: StaticSchema = (
    18,
    n0,
    _s15,
    {_s11: _s16, _s17: None},
)

EMPTY_INPUT_AND_EMPTY_OUTPUT_OUTPUT: StaticSchema = (
    18,
    n0,
    _s18,
    {_s11: _s19, _s13: None},
)

EMPTY_INPUT_AND_EMPTY_OUTPUT: StaticOperationSchema = (
    23,
    n0,
    _s226,
    0,
    EMPTY_INPUT_AND_EMPTY_OUTPUT_INPUT,
    EMPTY_INPUT_AND_EMPTY_OUTPUT_OUTPUT,
    (),
)

FRACTIONAL_SECONDS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s20,
    {_s11: _s21, _s13: None},
    (_s14,),
    ((DATE_TIME, 0),),
)

FRACTIONAL_SECONDS_INPUT: StaticSchema = (
    18,
    n0,
    _s180,
    {_s11: _s173, _s17: None},
)

FRACTIONAL_SECONDS: StaticOperationSchema = (
    23,
    n0,
    _s230,
    0,
    FRACTIONAL_SECONDS_INPUT,
    FRACTIONAL_SECONDS_OUTPUT,
    (),
)

GREETING_WITH_ERRORS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s22,
    {_s11: _s23, _s13: None},
    (_s24,),
    ((3, 0),),
)

GREETING_WITH_ERRORS_INPUT: StaticSchema = (
    18,
    n0,
    _s181,
    {_s11: _s173, _s17: None},
)

GREETING_WITH_ERRORS: StaticOperationSchema = (
    23,
    n0,
    _s231,
    0,
    GREETING_WITH_ERRORS_INPUT,
    GREETING_WITH_ERRORS_OUTPUT,
    (COMPLEX_ERROR, lambda: INVALID_GREETING),
)

IGNORES_WRAPPING_XML_NAME_OUTPUT: StaticSchema = (
    18,
    n0,
    _s25,
    {_s26: _s27, _s11: _s28, _s13: None},
    (_s29,),
    ((3, 0),),
)

IGNORES_WRAPPING_XML_NAME_INPUT: StaticSchema = (
    18,
    n0,
    _s184,
    {_s11: _s173, _s17: None},
)

IGNORES_WRAPPING_XML_NAME: StaticOperationSchema = (
    23,
    n0,
    _s233,
    0,
    IGNORES_WRAPPING_XML_NAME_INPUT,
    IGNORES_WRAPPING_XML_NAME_OUTPUT,
    (),
)

INVALID_GREETING: StaticSchema = (
    18,
    n0,
    _s30,
    {_s3: _s4},
    (_s31,),
    ((3, 0),),
)

LIST_WITH_MEMBER_NAMESPACE: StaticSchema = (
    16,
    n0,
    _s32,
    {_s33: MappingProxyType({"uri": "https://xml-list.example.com"})},
    (_s34,),
    ((3, {_s33: MappingProxyType({"uri": "https://xml-member.example.com"})}),),
)

LIST_WITH_NAMESPACE: StaticSchema = (
    16,
    n0,
    _s35,
    {_s33: MappingProxyType({"uri": "https://xml-list.example.com"})},
    (_s34,),
    ((3, 0),),
)

LIST_WITH_XML_NAME: StaticSchema = (
    16,
    n0,
    _s36,
    0,
    (_s34,),
    ((3, {_s26: _s37}),),
)

STRING_LIST: StaticSchema = (
    16,
    n1,
    _s38,
    0,
    (_s34,),
    ((3, 0),),
)

NESTED_STRUCT_WITH_LIST: StaticSchema = (
    18,
    n0,
    _s39,
    0,
    (_s40,),
    ((STRING_LIST, 0),),
)

NESTED_STRUCTURES_INPUT: StaticSchema = (
    18,
    n0,
    _s41,
    {_s11: _s42, _s17: None},
    (_s6,),
    ((lambda: schemas.STRUCT_ARG, 0),),
)

NESTED_STRUCTURES_OUTPUT: StaticSchema = (
    18,
    n0,
    _s185,
    {_s11: _s173, _s13: None},
)

NESTED_STRUCTURES: StaticOperationSchema = (
    23,
    n0,
    _s234,
    0,
    NESTED_STRUCTURES_INPUT,
    NESTED_STRUCTURES_OUTPUT,
    (),
)

NO_INPUT_AND_OUTPUT_OUTPUT: StaticSchema = (
    18,
    n0,
    _s43,
    {_s11: _s44, _s13: None},
)

NO_INPUT_AND_OUTPUT_INPUT: StaticSchema = (
    18,
    n0,
    _s186,
    {_s11: _s173, _s17: None},
)

NO_INPUT_AND_OUTPUT: StaticOperationSchema = (
    23,
    n0,
    _s235,
    0,
    NO_INPUT_AND_OUTPUT_INPUT,
    NO_INPUT_AND_OUTPUT_OUTPUT,
    (),
)

PUT_WITH_CONTENT_ENCODING_INPUT: StaticSchema = (
    18,
    n0,
    _s45,
    {_s11: _s46, _s17: None},
    (_s47, _s50),
    ((3, {_s48: _s49}), (3, 0)),
)

PUT_WITH_CONTENT_ENCODING_OUTPUT: StaticSchema = (
    18,
    n0,
    _s187,
    {_s11: _s173, _s13: None},
)

PUT_WITH_CONTENT_ENCODING: StaticOperationSchema = (
    23,
    n0,
    _s236,
    {_s237: MappingProxyType({"encodings": ("gzip",)})},
    PUT_WITH_CONTENT_ENCODING_INPUT,
    PUT_WITH_CONTENT_ENCODING_OUTPUT,
    (),
)

QUERY_IDEMPOTENCY_TOKEN_AUTO_FILL_INPUT: StaticSchema = (
    18,
    n0,
    _s51,
    {_s11: _s52, _s17: None},
    (_s53,),
    ((3, 2),),
)

QUERY_IDEMPOTENCY_TOKEN_AUTO_FILL_OUTPUT: StaticSchema = (
    18,
    n0,
    _s188,
    {_s11: _s173, _s13: None},
)

QUERY_IDEMPOTENCY_TOKEN_AUTO_FILL: StaticOperationSchema = (
    23,
    n0,
    _s238,
    0,
    QUERY_IDEMPOTENCY_TOKEN_AUTO_FILL_INPUT,
    QUERY_IDEMPOTENCY_TOKEN_AUTO_FILL_OUTPUT,
    (),
)

GREETING_STRUCT: StaticSchema = (
    18,
    n1,
    _s54,
    0,
    (_s55,),
    ((3, 0),),
)

GREETING_LIST: StaticSchema = (
    16,
    n1,
    _s56,
    0,
    (_s34,),
    ((GREETING_STRUCT, 0),),
)

QUERY_LISTS_INPUT: StaticSchema = (
    18,
    n0,
    _s57,
    {_s11: _s58, _s17: None},
    (_s40, _s59, _s60, _s61, _s63),
    (
        (STRING_LIST, 0),
        (GREETING_LIST, 0),
        (LIST_WITH_XML_NAME, 0),
        (LIST_WITH_XML_NAME, {_s26: _s62}),
        (NESTED_STRUCT_WITH_LIST, 0),
    ),
)

QUERY_LISTS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s189,
    {_s11: _s173, _s13: None},
)

QUERY_LISTS: StaticOperationSchema = (
    23,
    n0,
    _s239,
    0,
    QUERY_LISTS_INPUT,
    QUERY_LISTS_OUTPUT,
    (),
)

EPOCH_SECONDS: StaticSchema = (
    4,
    n1,
    _s64,
    {_s8: _s65},
)

QUERY_TIMESTAMPS_INPUT: StaticSchema = (
    18,
    n0,
    _s66,
    {_s11: _s67, _s17: None},
    (_s68, _s69, _s70),
    ((4, 0), (4, {_s8: _s65}), (EPOCH_SECONDS, 0)),
)

QUERY_TIMESTAMPS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s190,
    {_s11: _s173, _s13: None},
)

QUERY_TIMESTAMPS: StaticOperationSchema = (
    23,
    n0,
    _s240,
    0,
    QUERY_TIMESTAMPS_INPUT,
    QUERY_TIMESTAMPS_OUTPUT,
    (),
)

RECURSIVE_XML_SHAPES_OUTPUT: StaticSchema = (
    18,
    n0,
    _s71,
    {_s11: _s72, _s13: None},
    (_s73,),
    ((lambda: schemas.RECURSIVE_XML_SHAPES_OUTPUT_NESTED1, 0),),
)

RECURSIVE_XML_SHAPES_INPUT: StaticSchema = (
    18,
    n0,
    _s191,
    {_s11: _s173, _s17: None},
)

RECURSIVE_XML_SHAPES: StaticOperationSchema = (
    23,
    n0,
    _s241,
    0,
    RECURSIVE_XML_SHAPES_INPUT,
    RECURSIVE_XML_SHAPES_OUTPUT,
    (),
)

RENAMED_LIST_MEMBERS: StaticSchema = (
    16,
    n0,
    _s74,
    0,
    (_s34,),
    ((3, {_s26: _s37}),),
)

FOO_ENUM: StaticSchema = (
    14,
    n1,
    _s75,
    0,
    (_s76, _s78, _s80, _s82, _s84),
    (
        (-1, {_s77: _s1}),
        (-1, {_s77: _s79}),
        (-1, {_s77: _s81}),
        (-1, {_s77: _s83}),
        (-1, {_s77: _s85}),
    ),
)

SIMPLE_INPUT_PARAMS_INPUT: StaticSchema = (
    18,
    n0,
    _s86,
    {_s11: _s87, _s17: None},
    (
        _s1,
        _s81,
        _s79,
        _s88,
        _s89,
        _s90,
        _s91,
        _s75,
        _s92,
        _s94,
        _s96,
        _s98,
        _s100,
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
        (3, {_s93: _s92}),
        (3, {_s93: _s94, _s26: _s95}),
        (3, {_s26: _s97}),
        (3, {_s93: _s99}),
        (3, {_s93: _s101, _s26: _s102}),
        (3, {_s26: _s104}),
    ),
)

SIMPLE_INPUT_PARAMS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s192,
    {_s11: _s173, _s13: None},
)

SIMPLE_INPUT_PARAMS: StaticOperationSchema = (
    23,
    n0,
    _s242,
    0,
    SIMPLE_INPUT_PARAMS_INPUT,
    SIMPLE_INPUT_PARAMS_OUTPUT,
    (),
)

SIMPLE_SCALAR_XML_PROPERTIES_OUTPUT: StaticSchema = (
    18,
    n0,
    _s105,
    {_s11: _s106, _s13: None},
    (_s107, _s108, _s109, _s110, _s111, _s112, _s113, _s114, _s115, _s116),
    (
        (3, {_s93: _s27}),
        (3, 0),
        (2, 0),
        (2, 0),
        (5, 0),
        (6, 0),
        (7, 0),
        (8, 0),
        (9, 0),
        (10, {_s26: _s117}),
    ),
)

SIMPLE_SCALAR_XML_PROPERTIES_INPUT: StaticSchema = (
    18,
    n0,
    _s193,
    {_s11: _s173, _s17: None},
)

SIMPLE_SCALAR_XML_PROPERTIES: StaticOperationSchema = (
    23,
    n0,
    _s243,
    0,
    SIMPLE_SCALAR_XML_PROPERTIES_INPUT,
    SIMPLE_SCALAR_XML_PROPERTIES_OUTPUT,
    (),
)

STRUCTURE_LIST_MEMBER: StaticSchema = (
    18,
    n0,
    _s118,
    0,
    (_s119, _s121),
    ((3, {_s26: _s120}), (3, {_s26: _s122})),
)
