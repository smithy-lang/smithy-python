from types import MappingProxyType

from smithy_core._schema_compact import StaticSchema

n0 = "aws.protocoltests.json10"
_s0 = "ClientOptionalDefaults"
_s1 = "member"
_s2 = "smithy.api#clientOptional"
_s3 = "smithy.api#default"
_s4 = "ComplexNestedErrorData"
_s5 = "Foo"
_s6 = "smithy.api#jsonName"
_s7 = "Fooooo"
_s8 = "ComplexError"
_s9 = "smithy.api#error"
_s10 = "client"
_s11 = "TopLevel"
_s12 = "Nested"
_s13 = "ContentTypeParametersInput"
_s14 = "smithy.api#input"
_s15 = "value"
_s16 = "ContentTypeParametersOutput"
_s17 = "smithy.api#output"
_s18 = "TestStringList"
_s19 = "TestStringMap"
_s20 = "key"
_s21 = "TestEnum"
_s22 = "FOO"
_s23 = "smithy.api#enumValue"
_s24 = "BAR"
_s25 = "BAZ"
_s26 = "TestIntEnum"
_s27 = "ONE"
_s28 = "TWO"
_s29 = "Defaults"
_s30 = "defaultString"
_s31 = "hi"
_s32 = "defaultBoolean"
_s33 = "defaultList"
_s34 = "defaultDocumentMap"
_s35 = "defaultDocumentString"
_s36 = "defaultDocumentBoolean"
_s37 = "defaultDocumentList"
_s38 = "defaultNullDocument"
_s39 = "defaultTimestamp"
_s40 = "defaultBlob"
_s41 = "YWJj"
_s42 = "defaultByte"
_s43 = "defaultShort"
_s44 = "defaultInteger"
_s45 = "defaultLong"
_s46 = "defaultFloat"
_s47 = "defaultDouble"
_s48 = "defaultMap"
_s49 = "defaultEnum"
_s50 = "defaultIntEnum"
_s51 = "emptyString"
_s52 = ""
_s53 = "falseBoolean"
_s54 = "emptyBlob"
_s55 = "zeroByte"
_s56 = "zeroShort"
_s57 = "zeroInteger"
_s58 = "zeroLong"
_s59 = "zeroFloat"
_s60 = "zeroDouble"
_s61 = "Farewell"
_s62 = "phrase"
_s63 = "bye"
_s64 = "Dialog"
_s65 = "language"
_s66 = "greeting"
_s67 = "farewell"
_s68 = "DialogList"
_s69 = "DialogMap"
_s70 = "EmptyInputAndEmptyOutputInput"
_s71 = "EmptyInputAndEmptyOutputOutput"
_s72 = "EndpointWithHostLabelOperationInput"
_s73 = "label"
_s74 = "FooError"
_s75 = "server"
_s76 = "GreetingWithErrorsInput"
_s77 = "GreetingWithErrorsOutput"
_s78 = "InvalidGreeting"
_s79 = "Message"
n1 = "aws.protocoltests.shared"
_s80 = "FooEnum"
_s81 = "Baz"
_s82 = "Bar"
_s83 = "1"
_s84 = "ZERO"
_s85 = "0"
_s86 = "IntegerEnum"
_s87 = "A"
_s88 = "B"
_s89 = "C"
_s90 = "StringList"
_s91 = "StringMap"
_s92 = "GreetingStruct"
_s93 = "MyUnion"
_s94 = "stringValue"
_s95 = "booleanValue"
_s96 = "numberValue"
_s97 = "blobValue"
_s98 = "timestampValue"
_s99 = "enumValue"
_s100 = "intEnumValue"
_s101 = "listValue"
_s102 = "mapValue"
_s103 = "structureValue"
_s104 = "JsonUnionsInput"
_s105 = "contents"
_s106 = "JsonUnionsOutput"
_s107 = "NoInputAndOutputOutput"
_s108 = "OperationWithDefaultsInput"
_s109 = "defaults"
_s110 = "clientOptionalDefaults"
_s111 = "topLevelDefault"
_s112 = "otherTopLevelDefault"
_s113 = "OperationWithDefaultsOutput"
_s114 = "dialog"
_s115 = "dialogList"
_s116 = "dialogMap"
_s117 = "OperationWithNestedStructureInput"
_s118 = "topLevel"
_s119 = "OperationWithNestedStructureOutput"
_s120 = "RequiredStringList"
_s121 = "RequiredStringMap"
_s122 = "OperationWithRequiredMembersOutput"
_s123 = "requiredString"
_s124 = "requiredBoolean"
_s125 = "requiredList"
_s126 = "requiredTimestamp"
_s127 = "requiredBlob"
_s128 = "requiredByte"
_s129 = "requiredShort"
_s130 = "requiredInteger"
_s131 = "requiredLong"
_s132 = "requiredFloat"
_s133 = "requiredDouble"
_s134 = "requiredMap"
_s135 = "RequiredEnum"
_s136 = "RequiredIntEnum"
_s137 = "OperationWithRequiredMembersWithDefaultsOutput"
_s138 = "smithy.api#required"
_s139 = "YmxvYg=="
_s140 = "requiredEnum"
_s141 = "requiredIntEnum"
_s142 = "PutWithContentEncodingInput"
_s143 = "encoding"
_s144 = "smithy.api#httpHeader"
_s145 = "Content-Encoding"
_s146 = "data"
_s147 = "SimpleScalarPropertiesInput"
_s148 = "floatValue"
_s149 = "doubleValue"
_s150 = "SimpleScalarPropertiesOutput"

CLIENT_OPTIONAL_DEFAULTS: StaticSchema = (
    18,
    n0,
    _s0,
    0,
    (_s1,),
    ((7, {_s2: None, _s3: 0}),),
)

COMPLEX_NESTED_ERROR_DATA: StaticSchema = (
    18,
    n0,
    _s4,
    0,
    (_s5,),
    ((3, {_s6: _s7}),),
)

COMPLEX_ERROR: StaticSchema = (
    18,
    n0,
    _s8,
    {_s9: _s10},
    (_s11, _s12),
    ((3, 0), (COMPLEX_NESTED_ERROR_DATA, 0)),
)

CONTENT_TYPE_PARAMETERS_INPUT: StaticSchema = (
    18,
    n0,
    _s13,
    {_s14: None},
    (_s15,),
    ((7, 0),),
)

CONTENT_TYPE_PARAMETERS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s16,
    {_s17: None},
)

TEST_STRING_LIST: StaticSchema = (
    16,
    n0,
    _s18,
    0,
    (_s1,),
    ((3, 0),),
)

TEST_STRING_MAP: StaticSchema = (
    17,
    n0,
    _s19,
    0,
    (_s20, _s15),
    ((3, 0), (3, 0)),
)

TEST_ENUM: StaticSchema = (
    14,
    n0,
    _s21,
    0,
    (_s22, _s24, _s25),
    ((-1, {_s23: _s22}), (-1, {_s23: _s24}), (-1, {_s23: _s25})),
)

TEST_INT_ENUM: StaticSchema = (
    15,
    n0,
    _s26,
    0,
    (_s27, _s28),
    ((-1, {_s23: 1}), (-1, {_s23: 2})),
)

DEFAULTS: StaticSchema = (
    18,
    n0,
    _s29,
    0,
    (
        _s30,
        _s32,
        _s33,
        _s34,
        _s35,
        _s36,
        _s37,
        _s38,
        _s39,
        _s40,
        _s42,
        _s43,
        _s44,
        _s45,
        _s46,
        _s47,
        _s48,
        _s49,
        _s50,
        _s51,
        _s53,
        _s54,
        _s55,
        _s56,
        _s57,
        _s58,
        _s59,
        _s60,
    ),
    (
        (3, {_s3: _s31}),
        (2, {_s3: True}),
        (TEST_STRING_LIST, {_s3: ()}),
        (13, {_s3: MappingProxyType[str, object]({})}),
        (13, {_s3: _s31}),
        (13, {_s3: True}),
        (13, {_s3: ()}),
        (13, {_s3: None}),
        (4, {_s3: 0}),
        (1, {_s3: _s41}),
        (5, {_s3: 1}),
        (6, {_s3: 1}),
        (7, {_s3: 10}),
        (8, {_s3: 100}),
        (9, {_s3: 1.0}),
        (10, {_s3: 1.0}),
        (TEST_STRING_MAP, {_s3: MappingProxyType[str, object]({})}),
        (TEST_ENUM, {_s3: _s22}),
        (TEST_INT_ENUM, {_s3: 1}),
        (3, {_s3: _s52}),
        (2, {_s3: False}),
        (1, {_s3: _s52}),
        (5, {_s3: 0}),
        (6, {_s3: 0}),
        (7, {_s3: 0}),
        (8, {_s3: 0}),
        (9, {_s3: 0.0}),
        (10, {_s3: 0.0}),
    ),
)

FAREWELL: StaticSchema = (
    18,
    n0,
    _s61,
    0,
    (_s62,),
    ((3, {_s3: _s63}),),
)

DIALOG: StaticSchema = (
    18,
    n0,
    _s64,
    0,
    (_s65, _s66, _s67),
    ((3, 0), (3, {_s3: _s31}), (FAREWELL, 0)),
)

DIALOG_LIST: StaticSchema = (
    16,
    n0,
    _s68,
    0,
    (_s1,),
    ((DIALOG, 0),),
)

DIALOG_MAP: StaticSchema = (
    17,
    n0,
    _s69,
    0,
    (_s20, _s15),
    ((3, 0), (DIALOG, 0)),
)

EMPTY_INPUT_AND_EMPTY_OUTPUT_INPUT: StaticSchema = (
    18,
    n0,
    _s70,
    {_s14: None},
)

EMPTY_INPUT_AND_EMPTY_OUTPUT_OUTPUT: StaticSchema = (
    18,
    n0,
    _s71,
    {_s17: None},
)

ENDPOINT_WITH_HOST_LABEL_OPERATION_INPUT: StaticSchema = (
    18,
    n0,
    _s72,
    {_s14: None},
    (_s73,),
    ((3, 257),),
)

FOO_ERROR: StaticSchema = (
    18,
    n0,
    _s74,
    {_s9: _s75},
)

GREETING_WITH_ERRORS_INPUT: StaticSchema = (
    18,
    n0,
    _s76,
    {_s14: None},
    (_s66,),
    ((3, 0),),
)

GREETING_WITH_ERRORS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s77,
    {_s17: None},
    (_s66,),
    ((3, 0),),
)

INVALID_GREETING: StaticSchema = (
    18,
    n0,
    _s78,
    {_s9: _s10},
    (_s79,),
    ((3, 0),),
)

FOO_ENUM: StaticSchema = (
    14,
    n1,
    _s80,
    0,
    (_s22, _s25, _s24, _s27, _s84),
    (
        (-1, {_s23: _s5}),
        (-1, {_s23: _s81}),
        (-1, {_s23: _s82}),
        (-1, {_s23: _s83}),
        (-1, {_s23: _s85}),
    ),
)

INTEGER_ENUM: StaticSchema = (
    15,
    n1,
    _s86,
    0,
    (_s87, _s88, _s89),
    ((-1, {_s23: 1}), (-1, {_s23: 2}), (-1, {_s23: 3})),
)

STRING_LIST: StaticSchema = (
    16,
    n1,
    _s90,
    0,
    (_s1,),
    ((3, 0),),
)

STRING_MAP: StaticSchema = (
    17,
    n1,
    _s91,
    0,
    (_s20, _s15),
    ((3, 0), (3, 0)),
)

GREETING_STRUCT: StaticSchema = (
    18,
    n1,
    _s92,
    0,
    (_s31,),
    ((3, 0),),
)

MY_UNION: StaticSchema = (
    19,
    n0,
    _s93,
    0,
    (_s94, _s95, _s96, _s97, _s98, _s99, _s100, _s101, _s102, _s103),
    (
        (3, 0),
        (2, 0),
        (7, 0),
        (1, 0),
        (4, 0),
        (FOO_ENUM, 0),
        (INTEGER_ENUM, 0),
        (STRING_LIST, 0),
        (STRING_MAP, 0),
        (GREETING_STRUCT, 0),
    ),
)

JSON_UNIONS_INPUT: StaticSchema = (
    18,
    n0,
    _s104,
    {_s14: None},
    (_s105,),
    ((MY_UNION, 0),),
)

JSON_UNIONS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s106,
    {_s17: None},
    (_s105,),
    ((MY_UNION, 0),),
)

NO_INPUT_AND_OUTPUT_OUTPUT: StaticSchema = (
    18,
    n0,
    _s107,
    {_s17: None},
)

OPERATION_WITH_DEFAULTS_INPUT: StaticSchema = (
    18,
    n0,
    _s108,
    {_s14: None},
    (_s109, _s110, _s111, _s112),
    ((DEFAULTS, 0), (CLIENT_OPTIONAL_DEFAULTS, 0), (3, {_s3: _s31}), (7, {_s3: 0})),
)

OPERATION_WITH_DEFAULTS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s113,
    {_s17: None},
    (
        _s30,
        _s32,
        _s33,
        _s34,
        _s35,
        _s36,
        _s37,
        _s38,
        _s39,
        _s40,
        _s42,
        _s43,
        _s44,
        _s45,
        _s46,
        _s47,
        _s48,
        _s49,
        _s50,
        _s51,
        _s53,
        _s54,
        _s55,
        _s56,
        _s57,
        _s58,
        _s59,
        _s60,
    ),
    (
        (3, {_s3: _s31}),
        (2, {_s3: True}),
        (TEST_STRING_LIST, {_s3: ()}),
        (13, {_s3: MappingProxyType[str, object]({})}),
        (13, {_s3: _s31}),
        (13, {_s3: True}),
        (13, {_s3: ()}),
        (13, {_s3: None}),
        (4, {_s3: 0}),
        (1, {_s3: _s41}),
        (5, {_s3: 1}),
        (6, {_s3: 1}),
        (7, {_s3: 10}),
        (8, {_s3: 100}),
        (9, {_s3: 1.0}),
        (10, {_s3: 1.0}),
        (TEST_STRING_MAP, {_s3: MappingProxyType[str, object]({})}),
        (TEST_ENUM, {_s3: _s22}),
        (TEST_INT_ENUM, {_s3: 1}),
        (3, {_s3: _s52}),
        (2, {_s3: False}),
        (1, {_s3: _s52}),
        (5, {_s3: 0}),
        (6, {_s3: 0}),
        (7, {_s3: 0}),
        (8, {_s3: 0}),
        (9, {_s3: 0.0}),
        (10, {_s3: 0.0}),
    ),
)

TOP_LEVEL: StaticSchema = (
    18,
    n0,
    _s11,
    0,
    (_s114, _s115, _s116),
    (
        (DIALOG, 1),
        (DIALOG_LIST, {_s3: ()}),
        (DIALOG_MAP, {_s3: MappingProxyType[str, object]({})}),
    ),
)

OPERATION_WITH_NESTED_STRUCTURE_INPUT: StaticSchema = (
    18,
    n0,
    _s117,
    {_s14: None},
    (_s118,),
    ((TOP_LEVEL, 1),),
)

OPERATION_WITH_NESTED_STRUCTURE_OUTPUT: StaticSchema = (
    18,
    n0,
    _s119,
    {_s17: None},
    (_s114, _s115, _s116),
    (
        (DIALOG, 1),
        (DIALOG_LIST, {_s3: ()}),
        (DIALOG_MAP, {_s3: MappingProxyType[str, object]({})}),
    ),
)

REQUIRED_STRING_LIST: StaticSchema = (
    16,
    n0,
    _s120,
    0,
    (_s1,),
    ((3, 0),),
)

REQUIRED_STRING_MAP: StaticSchema = (
    17,
    n0,
    _s121,
    0,
    (_s20, _s15),
    ((3, 0), (3, 0)),
)

OPERATION_WITH_REQUIRED_MEMBERS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s122,
    {_s17: None},
    (
        _s123,
        _s124,
        _s125,
        _s126,
        _s127,
        _s128,
        _s129,
        _s130,
        _s131,
        _s132,
        _s133,
        _s134,
    ),
    (
        (3, 1),
        (2, 1),
        (REQUIRED_STRING_LIST, 1),
        (4, 1),
        (1, 1),
        (5, 1),
        (6, 1),
        (7, 1),
        (8, 1),
        (9, 1),
        (10, 1),
        (REQUIRED_STRING_MAP, 1),
    ),
)

REQUIRED_ENUM: StaticSchema = (
    14,
    n0,
    _s135,
    0,
    (_s22, _s24, _s25),
    ((-1, {_s23: _s22}), (-1, {_s23: _s24}), (-1, {_s23: _s25})),
)

REQUIRED_INT_ENUM: StaticSchema = (
    15,
    n0,
    _s136,
    0,
    (_s27, _s28),
    ((-1, {_s23: 1}), (-1, {_s23: 2})),
)

OPERATION_WITH_REQUIRED_MEMBERS_WITH_DEFAULTS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s137,
    {_s17: None},
    (
        _s123,
        _s124,
        _s125,
        _s126,
        _s127,
        _s128,
        _s129,
        _s130,
        _s131,
        _s132,
        _s133,
        _s134,
        _s140,
        _s141,
    ),
    (
        (3, {_s3: _s31, _s138: None}),
        (2, {_s3: True, _s138: None}),
        (REQUIRED_STRING_LIST, {_s3: (), _s138: None}),
        (4, {_s3: 1, _s138: None}),
        (1, {_s3: _s139, _s138: None}),
        (5, {_s3: 1, _s138: None}),
        (6, {_s3: 1, _s138: None}),
        (7, {_s3: 10, _s138: None}),
        (8, {_s3: 100, _s138: None}),
        (9, {_s3: 1.0, _s138: None}),
        (10, {_s3: 1.0, _s138: None}),
        (REQUIRED_STRING_MAP, {_s3: MappingProxyType[str, object]({}), _s138: None}),
        (REQUIRED_ENUM, {_s3: _s22, _s138: None}),
        (REQUIRED_INT_ENUM, {_s3: 1, _s138: None}),
    ),
)

PUT_WITH_CONTENT_ENCODING_INPUT: StaticSchema = (
    18,
    n0,
    _s142,
    {_s14: None},
    (_s143, _s146),
    ((3, {_s144: _s145}), (3, 0)),
)

SIMPLE_SCALAR_PROPERTIES_INPUT: StaticSchema = (
    18,
    n0,
    _s147,
    {_s14: None},
    (_s148, _s149),
    ((9, 0), (10, 0)),
)

SIMPLE_SCALAR_PROPERTIES_OUTPUT: StaticSchema = (
    18,
    n0,
    _s150,
    {_s17: None},
    (_s148, _s149),
    ((9, 0), (10, 0)),
)
