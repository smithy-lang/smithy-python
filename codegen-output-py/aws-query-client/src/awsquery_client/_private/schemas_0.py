from types import MappingProxyType

from smithy_core._schema_compact import StaticOperationSchema, StaticSchema

from . import schemas

n0 = "aws.protocoltests.query"
_s0 = "ComplexNestedErrorData"
_s1 = "Foo"
_s2 = "ComplexError"
_s3 = "smithy.api#error"
_s4 = "client"
_s5 = "TopLevel"
_s6 = "Nested"
n1 = "aws.protocoltests.shared"
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
_s19 = "smithy.synthetic#originalShapeId"
_s20 = "aws.protocoltests.query#DatetimeOffsetsOutput"
_s21 = "smithy.api#output"
_s22 = "datetime"
_s23 = "EmptyInputAndEmptyOutputInput"
_s24 = "aws.protocoltests.query#EmptyInputAndEmptyOutputInput"
_s25 = "smithy.api#input"
_s26 = "EmptyInputAndEmptyOutputOutput"
_s27 = "aws.protocoltests.query#EmptyInputAndEmptyOutputOutput"
_s28 = "FooEnum"
_s29 = "FOO"
_s30 = "smithy.api#enumValue"
_s31 = "BAZ"
_s32 = "Baz"
_s33 = "BAR"
_s34 = "Bar"
_s35 = "ONE"
_s36 = "1"
_s37 = "ZERO"
_s38 = "0"
_s39 = "FooEnumMap"
_s40 = "FlattenedXmlMapOutput"
_s41 = "aws.protocoltests.query#FlattenedXmlMapOutput"
_s42 = "myMap"
_s43 = "smithy.api#xmlFlattened"
_s44 = "FlattenedXmlMapWithXmlNameOutputMap"
_s45 = "smithy.api#xmlName"
_s46 = "K"
_s47 = "V"
_s48 = "FlattenedXmlMapWithXmlNameOutput"
_s49 = "aws.protocoltests.query#FlattenedXmlMapWithXmlNameOutput"
_s50 = "KVP"
_s51 = "FlattenedXmlMapWithXmlNamespaceOutputMap"
_s52 = "smithy.api#xmlNamespace"
_s53 = "FlattenedXmlMapWithXmlNamespaceOutput"
_s54 = "aws.protocoltests.query#FlattenedXmlMapWithXmlNamespaceOutput"
_s55 = "FractionalSecondsOutput"
_s56 = "aws.protocoltests.query#FractionalSecondsOutput"
_s57 = "GreetingWithErrorsOutput"
_s58 = "aws.protocoltests.query#GreetingWithErrorsOutput"
_s59 = "greeting"
_s60 = "IgnoresWrappingXmlNameOutput"
_s61 = "IgnoreMe"
_s62 = "aws.protocoltests.query#IgnoresWrappingXmlNameOutput"
_s63 = "foo"
_s64 = "InvalidGreeting"
_s65 = "ListWithMemberNamespace"
_s66 = "member"
_s67 = "ListWithNamespace"
_s68 = "ListWithXmlName"
_s69 = "item"
_s70 = "StringList"
_s71 = "MapOfLists"
_s72 = "MapWithXmlName"
_s73 = "NestedStructWithList"
_s74 = "ListArg"
_s75 = "StringMap"
_s76 = "NestedStructWithMap"
_s77 = "MapArg"
_s78 = "NestedStructuresInput"
_s79 = "aws.protocoltests.query#NestedStructuresInput"
_s80 = "NoInputAndOutputInput"
_s81 = "aws.protocoltests.query#NoInputAndOutputInput"
_s82 = "NoInputAndOutputOutput"
_s83 = "aws.protocoltests.query#NoInputAndOutputOutput"
_s84 = "PutWithContentEncodingInput"
_s85 = "aws.protocoltests.query#PutWithContentEncodingInput"
_s86 = "encoding"
_s87 = "smithy.api#httpHeader"
_s88 = "Content-Encoding"
_s89 = "data"
_s90 = "QueryIdempotencyTokenAutoFillInput"
_s91 = "aws.protocoltests.query#QueryIdempotencyTokenAutoFillInput"
_s92 = "token"
_s93 = "GreetingList"
_s94 = "QueryListsInput"
_s95 = "aws.protocoltests.query#QueryListsInput"
_s96 = "ComplexListArg"
_s97 = "FlattenedListArg"
_s98 = "ListArgWithXmlNameMember"
_s99 = "FlattenedListArgWithXmlName"
_s100 = "Hi"
_s101 = "NestedWithList"
_s102 = "QueryMapsInput"
_s103 = "aws.protocoltests.query#QueryMapsInput"
_s104 = "RenamedMapArg"
_s105 = "ComplexMapArg"
_s106 = "MapWithXmlMemberName"
_s107 = "FlattenedMap"
_s108 = "FlattenedMapWithXmlName"
_s109 = "EpochSeconds"
_s110 = "epoch-seconds"
_s111 = "QueryTimestampsInput"
_s112 = "aws.protocoltests.query#QueryTimestampsInput"
_s113 = "normalFormat"
_s114 = "epochMember"
_s115 = "epochTarget"
_s116 = "RecursiveXmlShapesOutput"
_s117 = "aws.protocoltests.query#RecursiveXmlShapesOutput"
_s118 = "nested"
_s119 = "RenamedListMembers"
_s120 = "IntegerEnum"
_s121 = "A"
_s122 = "B"
_s123 = "C"
_s124 = "SimpleInputParamsInput"
_s125 = "aws.protocoltests.query#SimpleInputParamsInput"
_s126 = "Bam"
_s127 = "FloatValue"
_s128 = "Boo"
_s129 = "Qux"
_s196 = "DatetimeOffsetsInput"
_s197 = "smithy.api#Unit"
_s204 = "FlattenedXmlMapInput"
_s205 = "FlattenedXmlMapWithXmlNameInput"
_s206 = "FlattenedXmlMapWithXmlNamespaceInput"
_s207 = "FractionalSecondsInput"
_s208 = "GreetingWithErrorsInput"
_s211 = "IgnoresWrappingXmlNameInput"
_s212 = "NestedStructuresOutput"
_s215 = "PutWithContentEncodingOutput"
_s216 = "QueryIdempotencyTokenAutoFillOutput"
_s217 = "QueryListsOutput"
_s218 = "QueryMapsOutput"
_s219 = "QueryTimestampsOutput"
_s220 = "RecursiveXmlShapesInput"
_s221 = "SimpleInputParamsOutput"
_s259 = "DatetimeOffsets"
_s260 = "EmptyInputAndEmptyOutput"
_s264 = "FlattenedXmlMap"
_s265 = "FlattenedXmlMapWithXmlName"
_s266 = "FlattenedXmlMapWithXmlNamespace"
_s267 = "FractionalSeconds"
_s268 = "GreetingWithErrors"
_s270 = "IgnoresWrappingXmlName"
_s271 = "NestedStructures"
_s273 = "NoInputAndOutput"
_s274 = "PutWithContentEncoding"
_s275 = "smithy.api#requestCompression"
_s276 = "QueryIdempotencyTokenAutoFill"
_s277 = "QueryLists"
_s278 = "QueryMaps"
_s279 = "QueryTimestamps"
_s280 = "RecursiveXmlShapes"
_s281 = "SimpleInputParams"

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

COMPLEX_MAP: StaticSchema = (
    17,
    n0,
    _s9,
    0,
    (_s10, _s11),
    ((3, 0), (lambda: schemas.GREETING_STRUCT, 0)),
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
    {_s19: _s20, _s21: None},
    (_s22,),
    ((DATE_TIME, 0),),
)

DATETIME_OFFSETS_INPUT: StaticSchema = (
    18,
    n0,
    _s196,
    {_s19: _s197, _s25: None},
)

DATETIME_OFFSETS: StaticOperationSchema = (
    23,
    n0,
    _s259,
    0,
    DATETIME_OFFSETS_INPUT,
    DATETIME_OFFSETS_OUTPUT,
    (),
)

EMPTY_INPUT_AND_EMPTY_OUTPUT_INPUT: StaticSchema = (
    18,
    n0,
    _s23,
    {_s19: _s24, _s25: None},
)

EMPTY_INPUT_AND_EMPTY_OUTPUT_OUTPUT: StaticSchema = (
    18,
    n0,
    _s26,
    {_s19: _s27, _s21: None},
)

EMPTY_INPUT_AND_EMPTY_OUTPUT: StaticOperationSchema = (
    23,
    n0,
    _s260,
    0,
    EMPTY_INPUT_AND_EMPTY_OUTPUT_INPUT,
    EMPTY_INPUT_AND_EMPTY_OUTPUT_OUTPUT,
    (),
)

FOO_ENUM: StaticSchema = (
    14,
    n1,
    _s28,
    0,
    (_s29, _s31, _s33, _s35, _s37),
    (
        (-1, {_s30: _s1}),
        (-1, {_s30: _s32}),
        (-1, {_s30: _s34}),
        (-1, {_s30: _s36}),
        (-1, {_s30: _s38}),
    ),
)

FOO_ENUM_MAP: StaticSchema = (
    17,
    n1,
    _s39,
    0,
    (_s10, _s11),
    ((3, 0), (FOO_ENUM, 0)),
)

FLATTENED_XML_MAP_OUTPUT: StaticSchema = (
    18,
    n0,
    _s40,
    {_s19: _s41, _s21: None},
    (_s42,),
    ((FOO_ENUM_MAP, {_s43: None}),),
)

FLATTENED_XML_MAP_INPUT: StaticSchema = (
    18,
    n0,
    _s204,
    {_s19: _s197, _s25: None},
)

FLATTENED_XML_MAP: StaticOperationSchema = (
    23,
    n0,
    _s264,
    0,
    FLATTENED_XML_MAP_INPUT,
    FLATTENED_XML_MAP_OUTPUT,
    (),
)

FLATTENED_XML_MAP_WITH_XML_NAME_OUTPUT_MAP: StaticSchema = (
    17,
    n0,
    _s44,
    0,
    (_s10, _s11),
    ((3, {_s45: _s46}), (3, {_s45: _s47})),
)

FLATTENED_XML_MAP_WITH_XML_NAME_OUTPUT: StaticSchema = (
    18,
    n0,
    _s48,
    {_s19: _s49, _s21: None},
    (_s42,),
    ((FLATTENED_XML_MAP_WITH_XML_NAME_OUTPUT_MAP, {_s43: None, _s45: _s50}),),
)

FLATTENED_XML_MAP_WITH_XML_NAME_INPUT: StaticSchema = (
    18,
    n0,
    _s205,
    {_s19: _s197, _s25: None},
)

FLATTENED_XML_MAP_WITH_XML_NAME: StaticOperationSchema = (
    23,
    n0,
    _s265,
    0,
    FLATTENED_XML_MAP_WITH_XML_NAME_INPUT,
    FLATTENED_XML_MAP_WITH_XML_NAME_OUTPUT,
    (),
)

FLATTENED_XML_MAP_WITH_XML_NAMESPACE_OUTPUT_MAP: StaticSchema = (
    17,
    n0,
    _s51,
    0,
    (_s10, _s11),
    (
        (
            3,
            {
                _s45: _s46,
                _s52: MappingProxyType({"uri": "https://the-key.example.com"}),
            },
        ),
        (
            3,
            {
                _s45: _s47,
                _s52: MappingProxyType({"uri": "https://the-value.example.com"}),
            },
        ),
    ),
)

FLATTENED_XML_MAP_WITH_XML_NAMESPACE_OUTPUT: StaticSchema = (
    18,
    n0,
    _s53,
    {_s19: _s54, _s21: None},
    (_s42,),
    (
        (
            FLATTENED_XML_MAP_WITH_XML_NAMESPACE_OUTPUT_MAP,
            {
                _s43: None,
                _s45: _s50,
                _s52: MappingProxyType({"uri": "https://the-member.example.com"}),
            },
        ),
    ),
)

FLATTENED_XML_MAP_WITH_XML_NAMESPACE_INPUT: StaticSchema = (
    18,
    n0,
    _s206,
    {_s19: _s197, _s25: None},
)

FLATTENED_XML_MAP_WITH_XML_NAMESPACE: StaticOperationSchema = (
    23,
    n0,
    _s266,
    0,
    FLATTENED_XML_MAP_WITH_XML_NAMESPACE_INPUT,
    FLATTENED_XML_MAP_WITH_XML_NAMESPACE_OUTPUT,
    (),
)

FRACTIONAL_SECONDS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s55,
    {_s19: _s56, _s21: None},
    (_s22,),
    ((DATE_TIME, 0),),
)

FRACTIONAL_SECONDS_INPUT: StaticSchema = (
    18,
    n0,
    _s207,
    {_s19: _s197, _s25: None},
)

FRACTIONAL_SECONDS: StaticOperationSchema = (
    23,
    n0,
    _s267,
    0,
    FRACTIONAL_SECONDS_INPUT,
    FRACTIONAL_SECONDS_OUTPUT,
    (),
)

GREETING_WITH_ERRORS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s57,
    {_s19: _s58, _s21: None},
    (_s59,),
    ((3, 0),),
)

GREETING_WITH_ERRORS_INPUT: StaticSchema = (
    18,
    n0,
    _s208,
    {_s19: _s197, _s25: None},
)

GREETING_WITH_ERRORS: StaticOperationSchema = (
    23,
    n0,
    _s268,
    0,
    GREETING_WITH_ERRORS_INPUT,
    GREETING_WITH_ERRORS_OUTPUT,
    (COMPLEX_ERROR, CUSTOM_CODE_ERROR, lambda: INVALID_GREETING),
)

IGNORES_WRAPPING_XML_NAME_OUTPUT: StaticSchema = (
    18,
    n0,
    _s60,
    {_s45: _s61, _s19: _s62, _s21: None},
    (_s63,),
    ((3, 0),),
)

IGNORES_WRAPPING_XML_NAME_INPUT: StaticSchema = (
    18,
    n0,
    _s211,
    {_s19: _s197, _s25: None},
)

IGNORES_WRAPPING_XML_NAME: StaticOperationSchema = (
    23,
    n0,
    _s270,
    0,
    IGNORES_WRAPPING_XML_NAME_INPUT,
    IGNORES_WRAPPING_XML_NAME_OUTPUT,
    (),
)

INVALID_GREETING: StaticSchema = (
    18,
    n0,
    _s64,
    {_s3: _s4},
    (_s14,),
    ((3, 0),),
)

LIST_WITH_MEMBER_NAMESPACE: StaticSchema = (
    16,
    n0,
    _s65,
    {_s52: MappingProxyType({"uri": "https://xml-list.example.com"})},
    (_s66,),
    ((3, {_s52: MappingProxyType({"uri": "https://xml-member.example.com"})}),),
)

LIST_WITH_NAMESPACE: StaticSchema = (
    16,
    n0,
    _s67,
    {_s52: MappingProxyType({"uri": "https://xml-list.example.com"})},
    (_s66,),
    ((3, 0),),
)

LIST_WITH_XML_NAME: StaticSchema = (
    16,
    n0,
    _s68,
    0,
    (_s66,),
    ((3, {_s45: _s69}),),
)

STRING_LIST: StaticSchema = (
    16,
    n1,
    _s70,
    0,
    (_s66,),
    ((3, 0),),
)

MAP_OF_LISTS: StaticSchema = (
    17,
    n0,
    _s71,
    0,
    (_s10, _s11),
    ((3, 0), (STRING_LIST, 0)),
)

MAP_WITH_XML_NAME: StaticSchema = (
    17,
    n0,
    _s72,
    0,
    (_s10, _s11),
    ((3, {_s45: _s46}), (3, {_s45: _s47})),
)

NESTED_STRUCT_WITH_LIST: StaticSchema = (
    18,
    n0,
    _s73,
    0,
    (_s74,),
    ((STRING_LIST, 0),),
)

STRING_MAP: StaticSchema = (
    17,
    n1,
    _s75,
    0,
    (_s10, _s11),
    ((3, 0), (3, 0)),
)

NESTED_STRUCT_WITH_MAP: StaticSchema = (
    18,
    n0,
    _s76,
    0,
    (_s77,),
    ((STRING_MAP, 0),),
)

NESTED_STRUCTURES_INPUT: StaticSchema = (
    18,
    n0,
    _s78,
    {_s19: _s79, _s25: None},
    (_s6,),
    ((lambda: schemas.STRUCT_ARG, 0),),
)

NESTED_STRUCTURES_OUTPUT: StaticSchema = (
    18,
    n0,
    _s212,
    {_s19: _s197, _s21: None},
)

NESTED_STRUCTURES: StaticOperationSchema = (
    23,
    n0,
    _s271,
    0,
    NESTED_STRUCTURES_INPUT,
    NESTED_STRUCTURES_OUTPUT,
    (),
)

NO_INPUT_AND_OUTPUT_INPUT: StaticSchema = (
    18,
    n0,
    _s80,
    {_s19: _s81, _s25: None},
)

NO_INPUT_AND_OUTPUT_OUTPUT: StaticSchema = (
    18,
    n0,
    _s82,
    {_s19: _s83, _s21: None},
)

NO_INPUT_AND_OUTPUT: StaticOperationSchema = (
    23,
    n0,
    _s273,
    0,
    NO_INPUT_AND_OUTPUT_INPUT,
    NO_INPUT_AND_OUTPUT_OUTPUT,
    (),
)

PUT_WITH_CONTENT_ENCODING_INPUT: StaticSchema = (
    18,
    n0,
    _s84,
    {_s19: _s85, _s25: None},
    (_s86, _s89),
    ((3, {_s87: _s88}), (3, 0)),
)

PUT_WITH_CONTENT_ENCODING_OUTPUT: StaticSchema = (
    18,
    n0,
    _s215,
    {_s19: _s197, _s21: None},
)

PUT_WITH_CONTENT_ENCODING: StaticOperationSchema = (
    23,
    n0,
    _s274,
    {_s275: MappingProxyType({"encodings": ("gzip",)})},
    PUT_WITH_CONTENT_ENCODING_INPUT,
    PUT_WITH_CONTENT_ENCODING_OUTPUT,
    (),
)

QUERY_IDEMPOTENCY_TOKEN_AUTO_FILL_INPUT: StaticSchema = (
    18,
    n0,
    _s90,
    {_s19: _s91, _s25: None},
    (_s92,),
    ((3, 2),),
)

QUERY_IDEMPOTENCY_TOKEN_AUTO_FILL_OUTPUT: StaticSchema = (
    18,
    n0,
    _s216,
    {_s19: _s197, _s21: None},
)

QUERY_IDEMPOTENCY_TOKEN_AUTO_FILL: StaticOperationSchema = (
    23,
    n0,
    _s276,
    0,
    QUERY_IDEMPOTENCY_TOKEN_AUTO_FILL_INPUT,
    QUERY_IDEMPOTENCY_TOKEN_AUTO_FILL_OUTPUT,
    (),
)

GREETING_LIST: StaticSchema = (
    16,
    n1,
    _s93,
    0,
    (_s66,),
    ((lambda: schemas.GREETING_STRUCT, 0),),
)

QUERY_LISTS_INPUT: StaticSchema = (
    18,
    n0,
    _s94,
    {_s19: _s95, _s25: None},
    (_s74, _s96, _s97, _s98, _s99, _s101),
    (
        (STRING_LIST, 0),
        (GREETING_LIST, 0),
        (STRING_LIST, {_s43: None}),
        (LIST_WITH_XML_NAME, 0),
        (LIST_WITH_XML_NAME, {_s43: None, _s45: _s100}),
        (NESTED_STRUCT_WITH_LIST, 0),
    ),
)

QUERY_LISTS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s217,
    {_s19: _s197, _s21: None},
)

QUERY_LISTS: StaticOperationSchema = (
    23,
    n0,
    _s277,
    0,
    QUERY_LISTS_INPUT,
    QUERY_LISTS_OUTPUT,
    (),
)

QUERY_MAPS_INPUT: StaticSchema = (
    18,
    n0,
    _s102,
    {_s19: _s103, _s25: None},
    (_s77, _s104, _s105, _s106, _s107, _s108, _s71, _s76),
    (
        (STRING_MAP, 0),
        (STRING_MAP, {_s45: _s1}),
        (COMPLEX_MAP, 0),
        (MAP_WITH_XML_NAME, 0),
        (STRING_MAP, {_s43: None}),
        (MAP_WITH_XML_NAME, {_s43: None, _s45: _s100}),
        (MAP_OF_LISTS, 0),
        (NESTED_STRUCT_WITH_MAP, 0),
    ),
)

QUERY_MAPS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s218,
    {_s19: _s197, _s21: None},
)

QUERY_MAPS: StaticOperationSchema = (
    23,
    n0,
    _s278,
    0,
    QUERY_MAPS_INPUT,
    QUERY_MAPS_OUTPUT,
    (),
)

EPOCH_SECONDS: StaticSchema = (
    4,
    n1,
    _s109,
    {_s16: _s110},
)

QUERY_TIMESTAMPS_INPUT: StaticSchema = (
    18,
    n0,
    _s111,
    {_s19: _s112, _s25: None},
    (_s113, _s114, _s115),
    ((4, 0), (4, {_s16: _s110}), (EPOCH_SECONDS, 0)),
)

QUERY_TIMESTAMPS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s219,
    {_s19: _s197, _s21: None},
)

QUERY_TIMESTAMPS: StaticOperationSchema = (
    23,
    n0,
    _s279,
    0,
    QUERY_TIMESTAMPS_INPUT,
    QUERY_TIMESTAMPS_OUTPUT,
    (),
)

RECURSIVE_XML_SHAPES_OUTPUT: StaticSchema = (
    18,
    n0,
    _s116,
    {_s19: _s117, _s21: None},
    (_s118,),
    ((lambda: schemas.RECURSIVE_XML_SHAPES_OUTPUT_NESTED1, 0),),
)

RECURSIVE_XML_SHAPES_INPUT: StaticSchema = (
    18,
    n0,
    _s220,
    {_s19: _s197, _s25: None},
)

RECURSIVE_XML_SHAPES: StaticOperationSchema = (
    23,
    n0,
    _s280,
    0,
    RECURSIVE_XML_SHAPES_INPUT,
    RECURSIVE_XML_SHAPES_OUTPUT,
    (),
)

RENAMED_LIST_MEMBERS: StaticSchema = (
    16,
    n0,
    _s119,
    0,
    (_s66,),
    ((3, {_s45: _s69}),),
)

INTEGER_ENUM: StaticSchema = (
    15,
    n1,
    _s120,
    0,
    (_s121, _s122, _s123),
    ((-1, {_s30: 1}), (-1, {_s30: 2}), (-1, {_s30: 3})),
)

SIMPLE_INPUT_PARAMS_INPUT: StaticSchema = (
    18,
    n0,
    _s124,
    {_s19: _s125, _s25: None},
    (_s1, _s34, _s32, _s126, _s127, _s128, _s129, _s28, _s120),
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

SIMPLE_INPUT_PARAMS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s221,
    {_s19: _s197, _s21: None},
)

SIMPLE_INPUT_PARAMS: StaticOperationSchema = (
    23,
    n0,
    _s281,
    0,
    SIMPLE_INPUT_PARAMS_INPUT,
    SIMPLE_INPUT_PARAMS_OUTPUT,
    (),
)
