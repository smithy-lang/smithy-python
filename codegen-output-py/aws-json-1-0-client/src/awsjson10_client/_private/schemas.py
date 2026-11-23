from types import MappingProxyType

from smithy_core._schema_compact import StaticOperationSchema, StaticSchema

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
_s14 = "smithy.synthetic#originalShapeId"
_s15 = "aws.protocoltests.json10#ContentTypeParametersInput"
_s16 = "smithy.api#input"
_s17 = "value"
_s18 = "ContentTypeParametersOutput"
_s19 = "aws.protocoltests.json10#ContentTypeParametersOutput"
_s20 = "smithy.api#output"
_s21 = "TestStringList"
_s22 = "TestStringMap"
_s23 = "key"
_s24 = "TestEnum"
_s25 = "FOO"
_s26 = "smithy.api#enumValue"
_s27 = "BAR"
_s28 = "BAZ"
_s29 = "TestIntEnum"
_s30 = "ONE"
_s31 = "TWO"
_s32 = "Defaults"
_s33 = "defaultString"
_s34 = "hi"
_s35 = "defaultBoolean"
_s36 = "defaultList"
_s37 = "defaultDocumentMap"
_s38 = "defaultDocumentString"
_s39 = "defaultDocumentBoolean"
_s40 = "defaultDocumentList"
_s41 = "defaultNullDocument"
_s42 = "defaultTimestamp"
_s43 = "defaultBlob"
_s44 = "YWJj"
_s45 = "defaultByte"
_s46 = "defaultShort"
_s47 = "defaultInteger"
_s48 = "defaultLong"
_s49 = "defaultFloat"
_s50 = "defaultDouble"
_s51 = "defaultMap"
_s52 = "defaultEnum"
_s53 = "defaultIntEnum"
_s54 = "emptyString"
_s55 = ""
_s56 = "falseBoolean"
_s57 = "emptyBlob"
_s58 = "zeroByte"
_s59 = "zeroShort"
_s60 = "zeroInteger"
_s61 = "zeroLong"
_s62 = "zeroFloat"
_s63 = "zeroDouble"
_s64 = "Farewell"
_s65 = "phrase"
_s66 = "bye"
_s67 = "Dialog"
_s68 = "language"
_s69 = "greeting"
_s70 = "farewell"
_s71 = "DialogList"
_s72 = "DialogMap"
_s73 = "EmptyInputAndEmptyOutputInput"
_s74 = "aws.protocoltests.json10#EmptyInputAndEmptyOutputInput"
_s75 = "EmptyInputAndEmptyOutputOutput"
_s76 = "aws.protocoltests.json10#EmptyInputAndEmptyOutputOutput"
_s77 = "EndpointWithHostLabelOperationInput"
_s78 = "aws.protocoltests.json10#EndpointWithHostLabelOperationInput"
_s79 = "label"
_s80 = "FooError"
_s81 = "server"
_s82 = "GreetingWithErrorsInput"
_s83 = "aws.protocoltests.json10#GreetingWithErrorsInput"
_s84 = "GreetingWithErrorsOutput"
_s85 = "aws.protocoltests.json10#GreetingWithErrorsOutput"
_s86 = "InvalidGreeting"
_s87 = "Message"
n1 = "aws.protocoltests.shared"
_s88 = "FooEnum"
_s89 = "Baz"
_s90 = "Bar"
_s91 = "1"
_s92 = "ZERO"
_s93 = "0"
_s94 = "IntegerEnum"
_s95 = "A"
_s96 = "B"
_s97 = "C"
_s98 = "StringList"
_s99 = "StringMap"
_s100 = "GreetingStruct"
_s101 = "MyUnion"
_s102 = "stringValue"
_s103 = "booleanValue"
_s104 = "numberValue"
_s105 = "blobValue"
_s106 = "timestampValue"
_s107 = "enumValue"
_s108 = "intEnumValue"
_s109 = "listValue"
_s110 = "mapValue"
_s111 = "structureValue"
_s112 = "JsonUnionsInput"
_s113 = "aws.protocoltests.json10#JsonUnionsInput"
_s114 = "contents"
_s115 = "JsonUnionsOutput"
_s116 = "aws.protocoltests.json10#JsonUnionsOutput"
_s117 = "NoInputAndOutputOutput"
_s118 = "aws.protocoltests.json10#NoInputAndOutputOutput"
_s119 = "OperationWithDefaultsInput"
_s120 = "aws.protocoltests.json10#OperationWithDefaultsInput"
_s121 = "defaults"
_s122 = "clientOptionalDefaults"
_s123 = "topLevelDefault"
_s124 = "otherTopLevelDefault"
_s125 = "OperationWithDefaultsOutput"
_s126 = "aws.protocoltests.json10#OperationWithDefaultsOutput"
_s127 = "dialog"
_s128 = "dialogList"
_s129 = "dialogMap"
_s130 = "OperationWithNestedStructureInput"
_s131 = "aws.protocoltests.json10#OperationWithNestedStructureInput"
_s132 = "topLevel"
_s133 = "OperationWithNestedStructureOutput"
_s134 = "aws.protocoltests.json10#OperationWithNestedStructureOutput"
_s135 = "RequiredStringList"
_s136 = "RequiredStringMap"
_s137 = "OperationWithRequiredMembersOutput"
_s138 = "aws.protocoltests.json10#OperationWithRequiredMembersOutput"
_s139 = "requiredString"
_s140 = "requiredBoolean"
_s141 = "requiredList"
_s142 = "requiredTimestamp"
_s143 = "requiredBlob"
_s144 = "requiredByte"
_s145 = "requiredShort"
_s146 = "requiredInteger"
_s147 = "requiredLong"
_s148 = "requiredFloat"
_s149 = "requiredDouble"
_s150 = "requiredMap"
_s151 = "RequiredEnum"
_s152 = "RequiredIntEnum"
_s153 = "OperationWithRequiredMembersWithDefaultsOutput"
_s154 = "aws.protocoltests.json10#OperationWithRequiredMembersWithDefaultsOutput"
_s155 = "smithy.api#required"
_s156 = "YmxvYg=="
_s157 = "requiredEnum"
_s158 = "requiredIntEnum"
_s159 = "PutWithContentEncodingInput"
_s160 = "aws.protocoltests.json10#PutWithContentEncodingInput"
_s161 = "encoding"
_s162 = "smithy.api#httpHeader"
_s163 = "Content-Encoding"
_s164 = "data"
_s165 = "SimpleScalarPropertiesInput"
_s166 = "aws.protocoltests.json10#SimpleScalarPropertiesInput"
_s167 = "floatValue"
_s168 = "doubleValue"
_s169 = "SimpleScalarPropertiesOutput"
_s170 = "aws.protocoltests.json10#SimpleScalarPropertiesOutput"
_s171 = "EndpointOperationInput"
_s172 = "smithy.api#Unit"
_s173 = "EndpointOperationOutput"
_s174 = "EndpointWithHostLabelOperationOutput"
_s175 = "HostWithPathOperationInput"
_s176 = "HostWithPathOperationOutput"
_s177 = "NoInputAndNoOutputInput"
_s178 = "NoInputAndNoOutputOutput"
_s179 = "NoInputAndOutputInput"
_s180 = "OperationWithRequiredMembersInput"
_s181 = "OperationWithRequiredMembersWithDefaultsInput"
_s182 = "PutWithContentEncodingOutput"
_s183 = "QueryIncompatibleOperationInput"
_s184 = "QueryIncompatibleOperationOutput"
_s185 = "ContentTypeParameters"
_s186 = "EmptyInputAndEmptyOutput"
_s187 = "EndpointOperation"
_s188 = "smithy.api#endpoint"
_s189 = "EndpointWithHostLabelOperation"
_s190 = "GreetingWithErrors"
_s191 = "HostWithPathOperation"
_s192 = "JsonUnions"
_s193 = "NoInputAndNoOutput"
_s194 = "NoInputAndOutput"
_s195 = "OperationWithDefaults"
_s196 = "OperationWithNestedStructure"
_s197 = "OperationWithRequiredMembers"
_s198 = "OperationWithRequiredMembersWithDefaults"
_s199 = "PutWithContentEncoding"
_s200 = "smithy.api#requestCompression"
_s201 = "QueryIncompatibleOperation"
_s202 = "SimpleScalarProperties"
_s203 = "JsonRpc10"
_s204 = "aws.api#service"
_s205 = "aws.auth#sigv4"
_s206 = "aws.protocols#awsJson1_0"

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
    {_s14: _s15, _s16: None},
    (_s17,),
    ((7, 0),),
)

CONTENT_TYPE_PARAMETERS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s18,
    {_s14: _s19, _s20: None},
)

TEST_STRING_LIST: StaticSchema = (
    16,
    n0,
    _s21,
    0,
    (_s1,),
    ((3, 0),),
)

TEST_STRING_MAP: StaticSchema = (
    17,
    n0,
    _s22,
    0,
    (_s23, _s17),
    ((3, 0), (3, 0)),
)

TEST_ENUM: StaticSchema = (
    14,
    n0,
    _s24,
    0,
    (_s25, _s27, _s28),
    ((-1, {_s26: _s25}), (-1, {_s26: _s27}), (-1, {_s26: _s28})),
)

TEST_INT_ENUM: StaticSchema = (
    15,
    n0,
    _s29,
    0,
    (_s30, _s31),
    ((-1, {_s26: 1}), (-1, {_s26: 2})),
)

DEFAULTS: StaticSchema = (
    18,
    n0,
    _s32,
    0,
    (
        _s33,
        _s35,
        _s36,
        _s37,
        _s38,
        _s39,
        _s40,
        _s41,
        _s42,
        _s43,
        _s45,
        _s46,
        _s47,
        _s48,
        _s49,
        _s50,
        _s51,
        _s52,
        _s53,
        _s54,
        _s56,
        _s57,
        _s58,
        _s59,
        _s60,
        _s61,
        _s62,
        _s63,
    ),
    (
        (3, {_s3: _s34}),
        (2, {_s3: True}),
        (TEST_STRING_LIST, {_s3: ()}),
        (13, {_s3: MappingProxyType[str, object]({})}),
        (13, {_s3: _s34}),
        (13, {_s3: True}),
        (13, {_s3: ()}),
        (13, {_s3: None}),
        (4, {_s3: 0}),
        (1, {_s3: _s44}),
        (5, {_s3: 1}),
        (6, {_s3: 1}),
        (7, {_s3: 10}),
        (8, {_s3: 100}),
        (9, {_s3: 1.0}),
        (10, {_s3: 1.0}),
        (TEST_STRING_MAP, {_s3: MappingProxyType[str, object]({})}),
        (TEST_ENUM, {_s3: _s25}),
        (TEST_INT_ENUM, {_s3: 1}),
        (3, {_s3: _s55}),
        (2, {_s3: False}),
        (1, {_s3: _s55}),
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
    _s64,
    0,
    (_s65,),
    ((3, {_s3: _s66}),),
)

DIALOG: StaticSchema = (
    18,
    n0,
    _s67,
    0,
    (_s68, _s69, _s70),
    ((3, 0), (3, {_s3: _s34}), (FAREWELL, 0)),
)

DIALOG_LIST: StaticSchema = (
    16,
    n0,
    _s71,
    0,
    (_s1,),
    ((DIALOG, 0),),
)

DIALOG_MAP: StaticSchema = (
    17,
    n0,
    _s72,
    0,
    (_s23, _s17),
    ((3, 0), (DIALOG, 0)),
)

EMPTY_INPUT_AND_EMPTY_OUTPUT_INPUT: StaticSchema = (
    18,
    n0,
    _s73,
    {_s14: _s74, _s16: None},
)

EMPTY_INPUT_AND_EMPTY_OUTPUT_OUTPUT: StaticSchema = (
    18,
    n0,
    _s75,
    {_s14: _s76, _s20: None},
)

ENDPOINT_WITH_HOST_LABEL_OPERATION_INPUT: StaticSchema = (
    18,
    n0,
    _s77,
    {_s14: _s78, _s16: None},
    (_s79,),
    ((3, 257),),
)

FOO_ERROR: StaticSchema = (
    18,
    n0,
    _s80,
    {_s9: _s81},
)

GREETING_WITH_ERRORS_INPUT: StaticSchema = (
    18,
    n0,
    _s82,
    {_s14: _s83, _s16: None},
    (_s69,),
    ((3, 0),),
)

GREETING_WITH_ERRORS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s84,
    {_s14: _s85, _s20: None},
    (_s69,),
    ((3, 0),),
)

INVALID_GREETING: StaticSchema = (
    18,
    n0,
    _s86,
    {_s9: _s10},
    (_s87,),
    ((3, 0),),
)

FOO_ENUM: StaticSchema = (
    14,
    n1,
    _s88,
    0,
    (_s25, _s28, _s27, _s30, _s92),
    (
        (-1, {_s26: _s5}),
        (-1, {_s26: _s89}),
        (-1, {_s26: _s90}),
        (-1, {_s26: _s91}),
        (-1, {_s26: _s93}),
    ),
)

INTEGER_ENUM: StaticSchema = (
    15,
    n1,
    _s94,
    0,
    (_s95, _s96, _s97),
    ((-1, {_s26: 1}), (-1, {_s26: 2}), (-1, {_s26: 3})),
)

STRING_LIST: StaticSchema = (
    16,
    n1,
    _s98,
    0,
    (_s1,),
    ((3, 0),),
)

STRING_MAP: StaticSchema = (
    17,
    n1,
    _s99,
    0,
    (_s23, _s17),
    ((3, 0), (3, 0)),
)

GREETING_STRUCT: StaticSchema = (
    18,
    n1,
    _s100,
    0,
    (_s34,),
    ((3, 0),),
)

MY_UNION: StaticSchema = (
    19,
    n0,
    _s101,
    0,
    (_s102, _s103, _s104, _s105, _s106, _s107, _s108, _s109, _s110, _s111),
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
    _s112,
    {_s14: _s113, _s16: None},
    (_s114,),
    ((MY_UNION, 0),),
)

JSON_UNIONS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s115,
    {_s14: _s116, _s20: None},
    (_s114,),
    ((MY_UNION, 0),),
)

NO_INPUT_AND_OUTPUT_OUTPUT: StaticSchema = (
    18,
    n0,
    _s117,
    {_s14: _s118, _s20: None},
)

OPERATION_WITH_DEFAULTS_INPUT: StaticSchema = (
    18,
    n0,
    _s119,
    {_s14: _s120, _s16: None},
    (_s121, _s122, _s123, _s124),
    ((DEFAULTS, 0), (CLIENT_OPTIONAL_DEFAULTS, 0), (3, {_s3: _s34}), (7, {_s3: 0})),
)

OPERATION_WITH_DEFAULTS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s125,
    {_s14: _s126, _s20: None},
    (
        _s33,
        _s35,
        _s36,
        _s37,
        _s38,
        _s39,
        _s40,
        _s41,
        _s42,
        _s43,
        _s45,
        _s46,
        _s47,
        _s48,
        _s49,
        _s50,
        _s51,
        _s52,
        _s53,
        _s54,
        _s56,
        _s57,
        _s58,
        _s59,
        _s60,
        _s61,
        _s62,
        _s63,
    ),
    (
        (3, {_s3: _s34}),
        (2, {_s3: True}),
        (TEST_STRING_LIST, {_s3: ()}),
        (13, {_s3: MappingProxyType[str, object]({})}),
        (13, {_s3: _s34}),
        (13, {_s3: True}),
        (13, {_s3: ()}),
        (13, {_s3: None}),
        (4, {_s3: 0}),
        (1, {_s3: _s44}),
        (5, {_s3: 1}),
        (6, {_s3: 1}),
        (7, {_s3: 10}),
        (8, {_s3: 100}),
        (9, {_s3: 1.0}),
        (10, {_s3: 1.0}),
        (TEST_STRING_MAP, {_s3: MappingProxyType[str, object]({})}),
        (TEST_ENUM, {_s3: _s25}),
        (TEST_INT_ENUM, {_s3: 1}),
        (3, {_s3: _s55}),
        (2, {_s3: False}),
        (1, {_s3: _s55}),
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
    (_s127, _s128, _s129),
    (
        (DIALOG, 1),
        (DIALOG_LIST, {_s3: ()}),
        (DIALOG_MAP, {_s3: MappingProxyType[str, object]({})}),
    ),
)

OPERATION_WITH_NESTED_STRUCTURE_INPUT: StaticSchema = (
    18,
    n0,
    _s130,
    {_s14: _s131, _s16: None},
    (_s132,),
    ((TOP_LEVEL, 1),),
)

OPERATION_WITH_NESTED_STRUCTURE_OUTPUT: StaticSchema = (
    18,
    n0,
    _s133,
    {_s14: _s134, _s20: None},
    (_s127, _s128, _s129),
    (
        (DIALOG, 1),
        (DIALOG_LIST, {_s3: ()}),
        (DIALOG_MAP, {_s3: MappingProxyType[str, object]({})}),
    ),
)

REQUIRED_STRING_LIST: StaticSchema = (
    16,
    n0,
    _s135,
    0,
    (_s1,),
    ((3, 0),),
)

REQUIRED_STRING_MAP: StaticSchema = (
    17,
    n0,
    _s136,
    0,
    (_s23, _s17),
    ((3, 0), (3, 0)),
)

OPERATION_WITH_REQUIRED_MEMBERS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s137,
    {_s14: _s138, _s20: None},
    (
        _s139,
        _s140,
        _s141,
        _s142,
        _s143,
        _s144,
        _s145,
        _s146,
        _s147,
        _s148,
        _s149,
        _s150,
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
    _s151,
    0,
    (_s25, _s27, _s28),
    ((-1, {_s26: _s25}), (-1, {_s26: _s27}), (-1, {_s26: _s28})),
)

REQUIRED_INT_ENUM: StaticSchema = (
    15,
    n0,
    _s152,
    0,
    (_s30, _s31),
    ((-1, {_s26: 1}), (-1, {_s26: 2})),
)

OPERATION_WITH_REQUIRED_MEMBERS_WITH_DEFAULTS_OUTPUT: StaticSchema = (
    18,
    n0,
    _s153,
    {_s14: _s154, _s20: None},
    (
        _s139,
        _s140,
        _s141,
        _s142,
        _s143,
        _s144,
        _s145,
        _s146,
        _s147,
        _s148,
        _s149,
        _s150,
        _s157,
        _s158,
    ),
    (
        (3, {_s3: _s34, _s155: None}),
        (2, {_s3: True, _s155: None}),
        (REQUIRED_STRING_LIST, {_s3: (), _s155: None}),
        (4, {_s3: 1, _s155: None}),
        (1, {_s3: _s156, _s155: None}),
        (5, {_s3: 1, _s155: None}),
        (6, {_s3: 1, _s155: None}),
        (7, {_s3: 10, _s155: None}),
        (8, {_s3: 100, _s155: None}),
        (9, {_s3: 1.0, _s155: None}),
        (10, {_s3: 1.0, _s155: None}),
        (REQUIRED_STRING_MAP, {_s3: MappingProxyType[str, object]({}), _s155: None}),
        (REQUIRED_ENUM, {_s3: _s25, _s155: None}),
        (REQUIRED_INT_ENUM, {_s3: 1, _s155: None}),
    ),
)

PUT_WITH_CONTENT_ENCODING_INPUT: StaticSchema = (
    18,
    n0,
    _s159,
    {_s14: _s160, _s16: None},
    (_s161, _s164),
    ((3, {_s162: _s163}), (3, 0)),
)

SIMPLE_SCALAR_PROPERTIES_INPUT: StaticSchema = (
    18,
    n0,
    _s165,
    {_s14: _s166, _s16: None},
    (_s167, _s168),
    ((9, 0), (10, 0)),
)

SIMPLE_SCALAR_PROPERTIES_OUTPUT: StaticSchema = (
    18,
    n0,
    _s169,
    {_s14: _s170, _s20: None},
    (_s167, _s168),
    ((9, 0), (10, 0)),
)

ENDPOINT_OPERATION_INPUT: StaticSchema = (
    18,
    n0,
    _s171,
    {_s14: _s172, _s16: None},
)

ENDPOINT_OPERATION_OUTPUT: StaticSchema = (
    18,
    n0,
    _s173,
    {_s14: _s172, _s20: None},
)

ENDPOINT_WITH_HOST_LABEL_OPERATION_OUTPUT: StaticSchema = (
    18,
    n0,
    _s174,
    {_s14: _s172, _s20: None},
)

HOST_WITH_PATH_OPERATION_INPUT: StaticSchema = (
    18,
    n0,
    _s175,
    {_s14: _s172, _s16: None},
)

HOST_WITH_PATH_OPERATION_OUTPUT: StaticSchema = (
    18,
    n0,
    _s176,
    {_s14: _s172, _s20: None},
)

NO_INPUT_AND_NO_OUTPUT_INPUT: StaticSchema = (
    18,
    n0,
    _s177,
    {_s14: _s172, _s16: None},
)

NO_INPUT_AND_NO_OUTPUT_OUTPUT: StaticSchema = (
    18,
    n0,
    _s178,
    {_s14: _s172, _s20: None},
)

NO_INPUT_AND_OUTPUT_INPUT: StaticSchema = (
    18,
    n0,
    _s179,
    {_s14: _s172, _s16: None},
)

OPERATION_WITH_REQUIRED_MEMBERS_INPUT: StaticSchema = (
    18,
    n0,
    _s180,
    {_s14: _s172, _s16: None},
)

OPERATION_WITH_REQUIRED_MEMBERS_WITH_DEFAULTS_INPUT: StaticSchema = (
    18,
    n0,
    _s181,
    {_s14: _s172, _s16: None},
)

PUT_WITH_CONTENT_ENCODING_OUTPUT: StaticSchema = (
    18,
    n0,
    _s182,
    {_s14: _s172, _s20: None},
)

QUERY_INCOMPATIBLE_OPERATION_INPUT: StaticSchema = (
    18,
    n0,
    _s183,
    {_s14: _s172, _s16: None},
)

QUERY_INCOMPATIBLE_OPERATION_OUTPUT: StaticSchema = (
    18,
    n0,
    _s184,
    {_s14: _s172, _s20: None},
)

CONTENT_TYPE_PARAMETERS: StaticOperationSchema = (
    23,
    n0,
    _s185,
    0,
    CONTENT_TYPE_PARAMETERS_INPUT,
    CONTENT_TYPE_PARAMETERS_OUTPUT,
    (),
)

EMPTY_INPUT_AND_EMPTY_OUTPUT: StaticOperationSchema = (
    23,
    n0,
    _s186,
    0,
    EMPTY_INPUT_AND_EMPTY_OUTPUT_INPUT,
    EMPTY_INPUT_AND_EMPTY_OUTPUT_OUTPUT,
    (),
)

ENDPOINT_OPERATION: StaticOperationSchema = (
    23,
    n0,
    _s187,
    {_s188: MappingProxyType({"hostPrefix": "foo."})},
    ENDPOINT_OPERATION_INPUT,
    ENDPOINT_OPERATION_OUTPUT,
    (),
)

ENDPOINT_WITH_HOST_LABEL_OPERATION: StaticOperationSchema = (
    23,
    n0,
    _s189,
    {_s188: MappingProxyType({"hostPrefix": "foo.{label}."})},
    ENDPOINT_WITH_HOST_LABEL_OPERATION_INPUT,
    ENDPOINT_WITH_HOST_LABEL_OPERATION_OUTPUT,
    (),
)

GREETING_WITH_ERRORS: StaticOperationSchema = (
    23,
    n0,
    _s190,
    0,
    GREETING_WITH_ERRORS_INPUT,
    GREETING_WITH_ERRORS_OUTPUT,
    (COMPLEX_ERROR, FOO_ERROR, INVALID_GREETING),
)

HOST_WITH_PATH_OPERATION: StaticOperationSchema = (
    23,
    n0,
    _s191,
    0,
    HOST_WITH_PATH_OPERATION_INPUT,
    HOST_WITH_PATH_OPERATION_OUTPUT,
    (),
)

JSON_UNIONS: StaticOperationSchema = (
    23,
    n0,
    _s192,
    0,
    JSON_UNIONS_INPUT,
    JSON_UNIONS_OUTPUT,
    (),
)

NO_INPUT_AND_NO_OUTPUT: StaticOperationSchema = (
    23,
    n0,
    _s193,
    0,
    NO_INPUT_AND_NO_OUTPUT_INPUT,
    NO_INPUT_AND_NO_OUTPUT_OUTPUT,
    (),
)

NO_INPUT_AND_OUTPUT: StaticOperationSchema = (
    23,
    n0,
    _s194,
    0,
    NO_INPUT_AND_OUTPUT_INPUT,
    NO_INPUT_AND_OUTPUT_OUTPUT,
    (),
)

OPERATION_WITH_DEFAULTS: StaticOperationSchema = (
    23,
    n0,
    _s195,
    0,
    OPERATION_WITH_DEFAULTS_INPUT,
    OPERATION_WITH_DEFAULTS_OUTPUT,
    (),
)

OPERATION_WITH_NESTED_STRUCTURE: StaticOperationSchema = (
    23,
    n0,
    _s196,
    0,
    OPERATION_WITH_NESTED_STRUCTURE_INPUT,
    OPERATION_WITH_NESTED_STRUCTURE_OUTPUT,
    (),
)

OPERATION_WITH_REQUIRED_MEMBERS: StaticOperationSchema = (
    23,
    n0,
    _s197,
    0,
    OPERATION_WITH_REQUIRED_MEMBERS_INPUT,
    OPERATION_WITH_REQUIRED_MEMBERS_OUTPUT,
    (),
)

OPERATION_WITH_REQUIRED_MEMBERS_WITH_DEFAULTS: StaticOperationSchema = (
    23,
    n0,
    _s198,
    0,
    OPERATION_WITH_REQUIRED_MEMBERS_WITH_DEFAULTS_INPUT,
    OPERATION_WITH_REQUIRED_MEMBERS_WITH_DEFAULTS_OUTPUT,
    (),
)

PUT_WITH_CONTENT_ENCODING: StaticOperationSchema = (
    23,
    n0,
    _s199,
    {_s200: MappingProxyType({"encodings": ("gzip",)})},
    PUT_WITH_CONTENT_ENCODING_INPUT,
    PUT_WITH_CONTENT_ENCODING_OUTPUT,
    (),
)

QUERY_INCOMPATIBLE_OPERATION: StaticOperationSchema = (
    23,
    n0,
    _s201,
    0,
    QUERY_INCOMPATIBLE_OPERATION_INPUT,
    QUERY_INCOMPATIBLE_OPERATION_OUTPUT,
    (),
)

SIMPLE_SCALAR_PROPERTIES: StaticOperationSchema = (
    23,
    n0,
    _s202,
    0,
    SIMPLE_SCALAR_PROPERTIES_INPUT,
    SIMPLE_SCALAR_PROPERTIES_OUTPUT,
    (),
)

JSON_RPC10: StaticSchema = (
    21,
    n0,
    _s203,
    {
        _s204: MappingProxyType({"sdkId": "JSON RPC 10"}),
        _s205: MappingProxyType({"name": "jsonrpc10"}),
        _s206: None,
    },
)
