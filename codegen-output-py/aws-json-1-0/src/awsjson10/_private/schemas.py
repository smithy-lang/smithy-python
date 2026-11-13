from types import MappingProxyType

from smithy_core._schema_compact import StaticSchema

n0 = "aws.protocoltests.json10"
_s0 = "ClientOptionalDefaults"
_s1 = "member"
_s2 = "smithy.api#default"
_s3 = "ComplexNestedErrorData"
_s4 = "Foo"
_s5 = "smithy.api#jsonName"
_s6 = "Fooooo"
_s7 = "ComplexError"
_s8 = "smithy.api#error"
_s9 = "client"
_s10 = "TopLevel"
_s11 = "Nested"
_s12 = "ContentTypeParametersInput"
_s13 = "smithy.api#input"
_s14 = "value"
_s15 = "ContentTypeParametersOutput"
_s16 = "smithy.api#output"
_s17 = "TestStringList"
_s18 = "TestStringMap"
_s19 = "key"
_s20 = "TestEnum"
_s21 = "FOO"
_s22 = "smithy.api#enumValue"
_s23 = "BAR"
_s24 = "BAZ"
_s25 = "TestIntEnum"
_s26 = "ONE"
_s27 = "TWO"
_s28 = "Defaults"
_s29 = "defaultString"
_s30 = "hi"
_s31 = "defaultBoolean"
_s32 = "defaultList"
_s33 = "defaultDocumentMap"
_s34 = "defaultDocumentString"
_s35 = "defaultDocumentBoolean"
_s36 = "defaultDocumentList"
_s37 = "defaultNullDocument"
_s38 = "defaultTimestamp"
_s39 = "defaultBlob"
_s40 = "YWJj"
_s41 = "defaultByte"
_s42 = "defaultShort"
_s43 = "defaultInteger"
_s44 = "defaultLong"
_s45 = "defaultFloat"
_s46 = "defaultDouble"
_s47 = "defaultMap"
_s48 = "defaultEnum"
_s49 = "defaultIntEnum"
_s50 = "emptyString"
_s51 = ""
_s52 = "falseBoolean"
_s53 = "emptyBlob"
_s54 = "zeroByte"
_s55 = "zeroShort"
_s56 = "zeroInteger"
_s57 = "zeroLong"
_s58 = "zeroFloat"
_s59 = "zeroDouble"
_s60 = "Farewell"
_s61 = "phrase"
_s62 = "bye"
_s63 = "Dialog"
_s64 = "language"
_s65 = "greeting"
_s66 = "farewell"
_s67 = "DialogList"
_s68 = "DialogMap"
_s69 = "EmptyInputAndEmptyOutputInput"
_s70 = "EmptyInputAndEmptyOutputOutput"
_s71 = "EndpointWithHostLabelOperationInput"
_s72 = "label"
_s73 = "FooError"
_s74 = "server"
_s75 = "GreetingWithErrorsInput"
_s76 = "GreetingWithErrorsOutput"
_s77 = "InvalidGreeting"
_s78 = "Message"
n1 = "aws.protocoltests.shared"
_s79 = "FooEnum"
_s80 = "Baz"
_s81 = "Bar"
_s82 = "1"
_s83 = "ZERO"
_s84 = "0"
_s85 = "IntegerEnum"
_s86 = "A"
_s87 = "B"
_s88 = "C"
_s89 = "StringList"
_s90 = "StringMap"
_s91 = "GreetingStruct"
_s92 = "MyUnion"
_s93 = "stringValue"
_s94 = "booleanValue"
_s95 = "numberValue"
_s96 = "blobValue"
_s97 = "timestampValue"
_s98 = "enumValue"
_s99 = "intEnumValue"
_s100 = "listValue"
_s101 = "mapValue"
_s102 = "structureValue"
_s103 = "JsonUnionsInput"
_s104 = "contents"
_s105 = "JsonUnionsOutput"
_s106 = "NoInputAndOutputOutput"
_s107 = "OperationWithDefaultsInput"
_s108 = "defaults"
_s109 = "clientOptionalDefaults"
_s110 = "topLevelDefault"
_s111 = "otherTopLevelDefault"
_s112 = "OperationWithDefaultsOutput"
_s113 = "dialog"
_s114 = "dialogList"
_s115 = "dialogMap"
_s116 = "OperationWithNestedStructureInput"
_s117 = "topLevel"
_s118 = "OperationWithNestedStructureOutput"
_s119 = "RequiredStringList"
_s120 = "RequiredStringMap"
_s121 = "OperationWithRequiredMembersOutput"
_s122 = "requiredString"
_s123 = "requiredBoolean"
_s124 = "requiredList"
_s125 = "requiredTimestamp"
_s126 = "requiredBlob"
_s127 = "requiredByte"
_s128 = "requiredShort"
_s129 = "requiredInteger"
_s130 = "requiredLong"
_s131 = "requiredFloat"
_s132 = "requiredDouble"
_s133 = "requiredMap"
_s134 = "RequiredEnum"
_s135 = "RequiredIntEnum"
_s136 = "OperationWithRequiredMembersWithDefaultsOutput"
_s137 = "smithy.api#required"
_s138 = "YmxvYg=="
_s139 = "requiredEnum"
_s140 = "requiredIntEnum"
_s141 = "PutWithContentEncodingInput"
_s142 = "encoding"
_s143 = "smithy.api#httpHeader"
_s144 = "Content-Encoding"
_s145 = "data"
_s146 = "SimpleScalarPropertiesInput"
_s147 = "floatValue"
_s148 = "doubleValue"
_s149 = "SimpleScalarPropertiesOutput"

CLIENT_OPTIONAL_DEFAULTS: StaticSchema = (
    18,
    n0,
    _s0,
    0,
    (_s1,),
    ((7, {_s2: 0}),),
)

COMPLEX_NESTED_ERROR_DATA: StaticSchema = (
    18,
    n0,
    _s3,
    0,
    (_s4,),
    ((3, {_s5: _s6}),),
)

COMPLEX_ERROR: StaticSchema = (
    18,
    n0,
    _s7,
    {_s8: _s9},
    (
        _s10,
        _s11,
    ),
    (
        (3, 0),
        (COMPLEX_NESTED_ERROR_DATA, 0),
    ),
)

CONTENT_TYPE_PARAMETERS_INPUT: StaticSchema = (
    18,
    n0,
    _s12,
    {_s13: None},
    (_s14,),
    ((7, 0),),
)

CONTENT_TYPE_PARAMETERS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s15,
    {_s16: None},
)

TEST_STRING_LIST: StaticSchema = (
    16,
    n0,
    _s17,
    0,
    (_s1,),
    ((3, 0),),
)

TEST_STRING_MAP: StaticSchema = (
    17,
    n0,
    _s18,
    0,
    (
        _s19,
        _s14,
    ),
    (
        (3, 0),
        (3, 0),
    ),
)

TEST_ENUM: StaticSchema = (
    14,
    n0,
    _s20,
    0,
    (
        _s21,
        _s23,
        _s24,
    ),
    (
        (-1, {_s22: _s21}),
        (-1, {_s22: _s23}),
        (-1, {_s22: _s24}),
    ),
)

TEST_INT_ENUM: StaticSchema = (
    15,
    n0,
    _s25,
    0,
    (
        _s26,
        _s27,
    ),
    (
        (-1, {_s22: 1}),
        (-1, {_s22: 2}),
    ),
)

DEFAULTS: StaticSchema = (
    18,
    n0,
    _s28,
    0,
    (
        _s29,
        _s31,
        _s32,
        _s33,
        _s34,
        _s35,
        _s36,
        _s37,
        _s38,
        _s39,
        _s41,
        _s42,
        _s43,
        _s44,
        _s45,
        _s46,
        _s47,
        _s48,
        _s49,
        _s50,
        _s52,
        _s53,
        _s54,
        _s55,
        _s56,
        _s57,
        _s58,
        _s59,
    ),
    (
        (3, {_s2: _s30}),
        (2, {_s2: True}),
        (TEST_STRING_LIST, {_s2: ()}),
        (13, {_s2: MappingProxyType[str, object]({})}),
        (13, {_s2: _s30}),
        (13, {_s2: True}),
        (13, {_s2: ()}),
        (13, {_s2: None}),
        (4, {_s2: 0}),
        (1, {_s2: _s40}),
        (5, {_s2: 1}),
        (6, {_s2: 1}),
        (7, {_s2: 10}),
        (8, {_s2: 100}),
        (9, {_s2: 1.0}),
        (10, {_s2: 1.0}),
        (TEST_STRING_MAP, {_s2: MappingProxyType[str, object]({})}),
        (TEST_ENUM, {_s2: _s21}),
        (TEST_INT_ENUM, {_s2: 1}),
        (3, {_s2: _s51}),
        (2, {_s2: False}),
        (1, {_s2: _s51}),
        (5, {_s2: 0}),
        (6, {_s2: 0}),
        (7, {_s2: 0}),
        (8, {_s2: 0}),
        (9, {_s2: 0.0}),
        (10, {_s2: 0.0}),
    ),
)

FAREWELL: StaticSchema = (
    18,
    n0,
    _s60,
    0,
    (_s61,),
    ((3, {_s2: _s62}),),
)

DIALOG: StaticSchema = (
    18,
    n0,
    _s63,
    0,
    (
        _s64,
        _s65,
        _s66,
    ),
    (
        (3, 0),
        (3, {_s2: _s30}),
        (FAREWELL, 0),
    ),
)

DIALOG_LIST: StaticSchema = (
    16,
    n0,
    _s67,
    0,
    (_s1,),
    ((DIALOG, 0),),
)

DIALOG_MAP: StaticSchema = (
    17,
    n0,
    _s68,
    0,
    (
        _s19,
        _s14,
    ),
    (
        (3, 0),
        (DIALOG, 0),
    ),
)

EMPTY_INPUT_AND_EMPTY_OUTPUT_INPUT: StaticSchema = (
    18,
    n0,
    _s69,
    {_s13: None},
)

EMPTY_INPUT_AND_EMPTY_OUTPUT_OUTPUT: StaticSchema = (
    18,
    n0,
    _s70,
    {_s16: None},
)

ENDPOINT_WITH_HOST_LABEL_OPERATION_INPUT: StaticSchema = (
    18,
    n0,
    _s71,
    {_s13: None},
    (_s72,),
    ((3, 257),),
)

FOO_ERROR: StaticSchema = (
    18,
    n0,
    _s73,
    {_s8: _s74},
)

GREETING_WITH_ERRORS_INPUT: StaticSchema = (
    18,
    n0,
    _s75,
    {_s13: None},
    (_s65,),
    ((3, 0),),
)

GREETING_WITH_ERRORS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s76,
    {_s16: None},
    (_s65,),
    ((3, 0),),
)

INVALID_GREETING: StaticSchema = (
    18,
    n0,
    _s77,
    {_s8: _s9},
    (_s78,),
    ((3, 0),),
)

FOO_ENUM: StaticSchema = (
    14,
    n1,
    _s79,
    0,
    (
        _s21,
        _s24,
        _s23,
        _s26,
        _s83,
    ),
    (
        (-1, {_s22: _s4}),
        (-1, {_s22: _s80}),
        (-1, {_s22: _s81}),
        (-1, {_s22: _s82}),
        (-1, {_s22: _s84}),
    ),
)

INTEGER_ENUM: StaticSchema = (
    15,
    n1,
    _s85,
    0,
    (
        _s86,
        _s87,
        _s88,
    ),
    (
        (-1, {_s22: 1}),
        (-1, {_s22: 2}),
        (-1, {_s22: 3}),
    ),
)

STRING_LIST: StaticSchema = (
    16,
    n1,
    _s89,
    0,
    (_s1,),
    ((3, 0),),
)

STRING_MAP: StaticSchema = (
    17,
    n1,
    _s90,
    0,
    (
        _s19,
        _s14,
    ),
    (
        (3, 0),
        (3, 0),
    ),
)

GREETING_STRUCT: StaticSchema = (
    18,
    n1,
    _s91,
    0,
    (_s30,),
    ((3, 0),),
)

MY_UNION: StaticSchema = (
    19,
    n0,
    _s92,
    0,
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
    _s103,
    {_s13: None},
    (_s104,),
    ((MY_UNION, 0),),
)

JSON_UNIONS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s105,
    {_s16: None},
    (_s104,),
    ((MY_UNION, 0),),
)

NO_INPUT_AND_OUTPUT_OUTPUT: StaticSchema = (
    18,
    n0,
    _s106,
    {_s16: None},
)

OPERATION_WITH_DEFAULTS_INPUT: StaticSchema = (
    18,
    n0,
    _s107,
    {_s13: None},
    (
        _s108,
        _s109,
        _s110,
        _s111,
    ),
    (
        (DEFAULTS, 0),
        (CLIENT_OPTIONAL_DEFAULTS, 0),
        (3, {_s2: _s30}),
        (7, {_s2: 0}),
    ),
)

OPERATION_WITH_DEFAULTS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s112,
    {_s16: None},
    (
        _s29,
        _s31,
        _s32,
        _s33,
        _s34,
        _s35,
        _s36,
        _s37,
        _s38,
        _s39,
        _s41,
        _s42,
        _s43,
        _s44,
        _s45,
        _s46,
        _s47,
        _s48,
        _s49,
        _s50,
        _s52,
        _s53,
        _s54,
        _s55,
        _s56,
        _s57,
        _s58,
        _s59,
    ),
    (
        (3, {_s2: _s30}),
        (2, {_s2: True}),
        (TEST_STRING_LIST, {_s2: ()}),
        (13, {_s2: MappingProxyType[str, object]({})}),
        (13, {_s2: _s30}),
        (13, {_s2: True}),
        (13, {_s2: ()}),
        (13, {_s2: None}),
        (4, {_s2: 0}),
        (1, {_s2: _s40}),
        (5, {_s2: 1}),
        (6, {_s2: 1}),
        (7, {_s2: 10}),
        (8, {_s2: 100}),
        (9, {_s2: 1.0}),
        (10, {_s2: 1.0}),
        (TEST_STRING_MAP, {_s2: MappingProxyType[str, object]({})}),
        (TEST_ENUM, {_s2: _s21}),
        (TEST_INT_ENUM, {_s2: 1}),
        (3, {_s2: _s51}),
        (2, {_s2: False}),
        (1, {_s2: _s51}),
        (5, {_s2: 0}),
        (6, {_s2: 0}),
        (7, {_s2: 0}),
        (8, {_s2: 0}),
        (9, {_s2: 0.0}),
        (10, {_s2: 0.0}),
    ),
)

TOP_LEVEL: StaticSchema = (
    18,
    n0,
    _s10,
    0,
    (
        _s113,
        _s114,
        _s115,
    ),
    (
        (DIALOG, 1),
        (DIALOG_LIST, {_s2: ()}),
        (DIALOG_MAP, {_s2: MappingProxyType[str, object]({})}),
    ),
)

OPERATION_WITH_NESTED_STRUCTURE_INPUT: StaticSchema = (
    18,
    n0,
    _s116,
    {_s13: None},
    (_s117,),
    ((TOP_LEVEL, 1),),
)

OPERATION_WITH_NESTED_STRUCTURE_OUTPUT: StaticSchema = (
    18,
    n0,
    _s118,
    {_s16: None},
    (
        _s113,
        _s114,
        _s115,
    ),
    (
        (DIALOG, 1),
        (DIALOG_LIST, {_s2: ()}),
        (DIALOG_MAP, {_s2: MappingProxyType[str, object]({})}),
    ),
)

REQUIRED_STRING_LIST: StaticSchema = (
    16,
    n0,
    _s119,
    0,
    (_s1,),
    ((3, 0),),
)

REQUIRED_STRING_MAP: StaticSchema = (
    17,
    n0,
    _s120,
    0,
    (
        _s19,
        _s14,
    ),
    (
        (3, 0),
        (3, 0),
    ),
)

OPERATION_WITH_REQUIRED_MEMBERS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s121,
    {_s16: None},
    (
        _s122,
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
    _s134,
    0,
    (
        _s21,
        _s23,
        _s24,
    ),
    (
        (-1, {_s22: _s21}),
        (-1, {_s22: _s23}),
        (-1, {_s22: _s24}),
    ),
)

REQUIRED_INT_ENUM: StaticSchema = (
    15,
    n0,
    _s135,
    0,
    (
        _s26,
        _s27,
    ),
    (
        (-1, {_s22: 1}),
        (-1, {_s22: 2}),
    ),
)

OPERATION_WITH_REQUIRED_MEMBERS_WITH_DEFAULTS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s136,
    {_s16: None},
    (
        _s122,
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
        _s139,
        _s140,
    ),
    (
        (3, {_s2: _s30, _s137: None}),
        (2, {_s2: True, _s137: None}),
        (REQUIRED_STRING_LIST, {_s2: (), _s137: None}),
        (4, {_s2: 1, _s137: None}),
        (1, {_s2: _s138, _s137: None}),
        (5, {_s2: 1, _s137: None}),
        (6, {_s2: 1, _s137: None}),
        (7, {_s2: 10, _s137: None}),
        (8, {_s2: 100, _s137: None}),
        (9, {_s2: 1.0, _s137: None}),
        (10, {_s2: 1.0, _s137: None}),
        (REQUIRED_STRING_MAP, {_s2: MappingProxyType[str, object]({}), _s137: None}),
        (REQUIRED_ENUM, {_s2: _s21, _s137: None}),
        (REQUIRED_INT_ENUM, {_s2: 1, _s137: None}),
    ),
)

PUT_WITH_CONTENT_ENCODING_INPUT: StaticSchema = (
    18,
    n0,
    _s141,
    {_s13: None},
    (
        _s142,
        _s145,
    ),
    (
        (3, {_s143: _s144}),
        (3, 0),
    ),
)

SIMPLE_SCALAR_PROPERTIES_INPUT: StaticSchema = (
    18,
    n0,
    _s146,
    {_s13: None},
    (
        _s147,
        _s148,
    ),
    (
        (9, 0),
        (10, 0),
    ),
)

SIMPLE_SCALAR_PROPERTIES_OUTPUT: StaticSchema = (
    18,
    n0,
    _s149,
    {_s16: None},
    (
        _s147,
        _s148,
    ),
    (
        (9, 0),
        (10, 0),
    ),
)
