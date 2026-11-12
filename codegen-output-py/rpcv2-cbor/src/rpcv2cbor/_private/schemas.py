from types import MappingProxyType

from smithy_core._schema_compact import StaticSchema

n0 = "smithy.framework"
_s0 = "ValidationExceptionField"
_s1 = "path"
_s2 = "message"
_s3 = "ValidationExceptionFieldList"
_s4 = "member"
_s5 = "ValidationException"
_s6 = "smithy.api#error"
_s7 = "client"
_s8 = "fieldList"
n1 = "smithy.protocoltests.rpcv2Cbor"
_s9 = "ClientOptionalDefaults"
_s10 = "smithy.api#default"
_s11 = "ComplexNestedErrorData"
_s12 = "Foo"
_s13 = "ComplexError"
_s14 = "TopLevel"
_s15 = "Nested"
_s16 = "TestStringList"
_s17 = "TestStringMap"
_s18 = "key"
_s19 = "value"
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
_s33 = "defaultTimestamp"
_s34 = "defaultBlob"
_s35 = "YWJj"
_s36 = "defaultByte"
_s37 = "defaultShort"
_s38 = "defaultInteger"
_s39 = "defaultLong"
_s40 = "defaultFloat"
_s41 = "defaultDouble"
_s42 = "defaultMap"
_s43 = "defaultEnum"
_s44 = "defaultIntEnum"
_s45 = "emptyString"
_s46 = ""
_s47 = "falseBoolean"
_s48 = "emptyBlob"
_s49 = "zeroByte"
_s50 = "zeroShort"
_s51 = "zeroInteger"
_s52 = "zeroLong"
_s53 = "zeroFloat"
_s54 = "zeroDouble"
_s55 = "DenseBooleanMap"
_s56 = "DenseNumberMap"
n2 = "smithy.protocoltests.shared"
_s57 = "StringSet"
_s58 = "DenseSetMap"
_s59 = "DenseStringMap"
_s60 = "GreetingStruct"
_s61 = "DenseStructMap"
_s62 = "EmptyStructure"
_s63 = "smithy.api#input"
_s64 = "smithy.api#output"
_s65 = "Float16Output"
_s66 = "DateTime"
_s67 = "smithy.api#timestampFormat"
_s68 = "date-time"
_s69 = "FractionalSecondsOutput"
_s70 = "datetime"
_s71 = "GreetingWithErrorsOutput"
_s72 = "greeting"
_s73 = "InvalidGreeting"
_s74 = "Message"
_s75 = "OperationWithDefaultsInput"
_s76 = "defaults"
_s77 = "clientOptionalDefaults"
_s78 = "topLevelDefault"
_s79 = "otherTopLevelDefault"
_s80 = "OperationWithDefaultsOutput"
_s81 = "RecursiveShapesInputOutput"
_s82 = "nested"
_s83 = "RpcV2CborDenseMapsInputOutput"
_s84 = "denseStructMap"
_s85 = "denseNumberMap"
_s86 = "denseBooleanMap"
_s87 = "denseStringMap"
_s88 = "denseSetMap"
_s89 = "StringList"
_s90 = "IntegerList"
_s91 = "BooleanList"
_s92 = "TimestampList"
_s93 = "FooEnum"
_s94 = "Baz"
_s95 = "Bar"
_s96 = "1"
_s97 = "ZERO"
_s98 = "0"
_s99 = "FooEnumList"
_s100 = "IntegerEnum"
_s101 = "A"
_s102 = "B"
_s103 = "C"
_s104 = "IntegerEnumList"
_s105 = "NestedStringList"
_s106 = "StructureListMember"
_s107 = "a"
_s108 = "b"
_s109 = "StructureList"
_s110 = "BlobList"
_s111 = "RpcV2CborListInputOutput"
_s112 = "stringList"
_s113 = "stringSet"
_s114 = "integerList"
_s115 = "booleanList"
_s116 = "timestampList"
_s117 = "enumList"
_s118 = "intEnumList"
_s119 = "nestedStringList"
_s120 = "structureList"
_s121 = "blobList"
_s122 = "RpcV2CborNestedUnion"
_s123 = "stringValue"
_s124 = "SparseStructMap"
_s125 = "SparseNumberMap"
_s126 = "SparseBooleanMap"
_s127 = "SparseStringMap"
_s128 = "SparseSetMap"
_s129 = "RpcV2CborSparseMapsInputOutput"
_s130 = "sparseStructMap"
_s131 = "sparseNumberMap"
_s132 = "sparseBooleanMap"
_s133 = "sparseStringMap"
_s134 = "sparseSetMap"
_s135 = "RpcV2CborUnion"
_s136 = "unionValue"
_s137 = "RpcV2CborUnionInputOutput"
_s138 = "contents"
_s139 = "otherValue"
_s140 = "SimpleScalarStructure"
_s141 = "trueBooleanValue"
_s142 = "falseBooleanValue"
_s143 = "byteValue"
_s144 = "doubleValue"
_s145 = "floatValue"
_s146 = "integerValue"
_s147 = "longValue"
_s148 = "shortValue"
_s149 = "blobValue"
_s150 = "SimpleStructure"
_s151 = "SparseStringList"
_s152 = "SparseNullsOperationInputOutput"
_s153 = "sparseStringList"
_s154 = "RecursiveShapesInputOutputNested1"
_s155 = "foo"
_s156 = "RecursiveShapesInputOutputNested2"
_s157 = "bar"
_s158 = "recursiveMember"

VALIDATION_EXCEPTION_FIELD: StaticSchema = (
    18,
    n0,
    _s0,
    0,
    (
        _s1,
        _s2,
    ),
    (
        (3, 1),
        (3, 1),
    ),
)

VALIDATION_EXCEPTION_FIELD_LIST: StaticSchema = (
    16,
    n0,
    _s3,
    0,
    (_s4,),
    ((VALIDATION_EXCEPTION_FIELD, 0),),
)

VALIDATION_EXCEPTION: StaticSchema = (
    18,
    n0,
    _s5,
    {_s6: _s7},
    (
        _s2,
        _s8,
    ),
    (
        (3, 1),
        (VALIDATION_EXCEPTION_FIELD_LIST, 0),
    ),
)

CLIENT_OPTIONAL_DEFAULTS: StaticSchema = (
    18,
    n1,
    _s9,
    0,
    (_s4,),
    ((7, {_s10: 0}),),
)

COMPLEX_NESTED_ERROR_DATA: StaticSchema = (
    18,
    n1,
    _s11,
    0,
    (_s12,),
    ((3, 0),),
)

COMPLEX_ERROR: StaticSchema = (
    18,
    n1,
    _s13,
    {_s6: _s7},
    (
        _s14,
        _s15,
    ),
    (
        (3, 0),
        (COMPLEX_NESTED_ERROR_DATA, 0),
    ),
)

TEST_STRING_LIST: StaticSchema = (
    16,
    n1,
    _s16,
    0,
    (_s4,),
    ((3, 0),),
)

TEST_STRING_MAP: StaticSchema = (
    17,
    n1,
    _s17,
    0,
    (
        _s18,
        _s19,
    ),
    (
        (3, 0),
        (3, 0),
    ),
)

TEST_ENUM: StaticSchema = (
    14,
    n1,
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
    n1,
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
    n1,
    _s28,
    0,
    (
        _s29,
        _s31,
        _s32,
        _s33,
        _s34,
        _s36,
        _s37,
        _s38,
        _s39,
        _s40,
        _s41,
        _s42,
        _s43,
        _s44,
        _s45,
        _s47,
        _s48,
        _s49,
        _s50,
        _s51,
        _s52,
        _s53,
        _s54,
    ),
    (
        (3, {_s10: _s30}),
        (2, {_s10: True}),
        (TEST_STRING_LIST, {_s10: ()}),
        (4, {_s10: 0}),
        (1, {_s10: _s35}),
        (5, {_s10: 1}),
        (6, {_s10: 1}),
        (7, {_s10: 10}),
        (8, {_s10: 100}),
        (9, {_s10: 1.0}),
        (10, {_s10: 1.0}),
        (TEST_STRING_MAP, {_s10: MappingProxyType[str, object]({})}),
        (TEST_ENUM, {_s10: _s21}),
        (TEST_INT_ENUM, {_s10: 1}),
        (3, {_s10: _s46}),
        (2, {_s10: False}),
        (1, {_s10: _s46}),
        (5, {_s10: 0}),
        (6, {_s10: 0}),
        (7, {_s10: 0}),
        (8, {_s10: 0}),
        (9, {_s10: 0.0}),
        (10, {_s10: 0.0}),
    ),
)

DENSE_BOOLEAN_MAP: StaticSchema = (
    17,
    n1,
    _s55,
    0,
    (
        _s18,
        _s19,
    ),
    (
        (3, 0),
        (2, 0),
    ),
)

DENSE_NUMBER_MAP: StaticSchema = (
    17,
    n1,
    _s56,
    0,
    (
        _s18,
        _s19,
    ),
    (
        (3, 0),
        (7, 0),
    ),
)

STRING_SET: StaticSchema = (
    16,
    n2,
    _s57,
    0,
    (_s4,),
    ((3, 0),),
)

DENSE_SET_MAP: StaticSchema = (
    17,
    n1,
    _s58,
    0,
    (
        _s18,
        _s19,
    ),
    (
        (3, 0),
        (STRING_SET, 0),
    ),
)

DENSE_STRING_MAP: StaticSchema = (
    17,
    n1,
    _s59,
    0,
    (
        _s18,
        _s19,
    ),
    (
        (3, 0),
        (3, 0),
    ),
)

GREETING_STRUCT: StaticSchema = (
    18,
    n2,
    _s60,
    0,
    (_s30,),
    ((3, 0),),
)

DENSE_STRUCT_MAP: StaticSchema = (
    17,
    n1,
    _s61,
    0,
    (
        _s18,
        _s19,
    ),
    (
        (3, 0),
        (GREETING_STRUCT, 0),
    ),
)

EMPTY_STRUCTURE: StaticSchema = (
    18,
    n1,
    _s62,
    {_s63: None, _s64: None},
)

FLOAT16_OUTPUT: StaticSchema = (
    18,
    n1,
    _s65,
    {_s64: None},
    (_s19,),
    ((10, 0),),
)

DATE_TIME: StaticSchema = (
    4,
    n2,
    _s66,
    {_s67: _s68},
)

FRACTIONAL_SECONDS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s69,
    {_s64: None},
    (_s70,),
    ((DATE_TIME, 0),),
)

GREETING_WITH_ERRORS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s71,
    {_s64: None},
    (_s72,),
    ((3, 0),),
)

INVALID_GREETING: StaticSchema = (
    18,
    n1,
    _s73,
    {_s6: _s7},
    (_s74,),
    ((3, 0),),
)

OPERATION_WITH_DEFAULTS_INPUT: StaticSchema = (
    18,
    n1,
    _s75,
    {_s63: None},
    (
        _s76,
        _s77,
        _s78,
        _s79,
    ),
    (
        (DEFAULTS, 0),
        (CLIENT_OPTIONAL_DEFAULTS, 0),
        (3, {_s10: _s30}),
        (7, {_s10: 0}),
    ),
)

OPERATION_WITH_DEFAULTS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s80,
    {_s64: None},
    (
        _s29,
        _s31,
        _s32,
        _s33,
        _s34,
        _s36,
        _s37,
        _s38,
        _s39,
        _s40,
        _s41,
        _s42,
        _s43,
        _s44,
        _s45,
        _s47,
        _s48,
        _s49,
        _s50,
        _s51,
        _s52,
        _s53,
        _s54,
    ),
    (
        (3, {_s10: _s30}),
        (2, {_s10: True}),
        (TEST_STRING_LIST, {_s10: ()}),
        (4, {_s10: 0}),
        (1, {_s10: _s35}),
        (5, {_s10: 1}),
        (6, {_s10: 1}),
        (7, {_s10: 10}),
        (8, {_s10: 100}),
        (9, {_s10: 1.0}),
        (10, {_s10: 1.0}),
        (TEST_STRING_MAP, {_s10: MappingProxyType[str, object]({})}),
        (TEST_ENUM, {_s10: _s21}),
        (TEST_INT_ENUM, {_s10: 1}),
        (3, {_s10: _s46}),
        (2, {_s10: False}),
        (1, {_s10: _s46}),
        (5, {_s10: 0}),
        (6, {_s10: 0}),
        (7, {_s10: 0}),
        (8, {_s10: 0}),
        (9, {_s10: 0.0}),
        (10, {_s10: 0.0}),
    ),
)

RECURSIVE_SHAPES_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s81,
    {_s63: None, _s64: None},
    (_s82,),
    ((lambda: RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED1, 0),),
)

RPC_V2_CBOR_DENSE_MAPS_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s83,
    {_s63: None, _s64: None},
    (
        _s84,
        _s85,
        _s86,
        _s87,
        _s88,
    ),
    (
        (DENSE_STRUCT_MAP, 0),
        (DENSE_NUMBER_MAP, 0),
        (DENSE_BOOLEAN_MAP, 0),
        (DENSE_STRING_MAP, 0),
        (DENSE_SET_MAP, 0),
    ),
)

STRING_LIST: StaticSchema = (
    16,
    n2,
    _s89,
    0,
    (_s4,),
    ((3, 0),),
)

INTEGER_LIST: StaticSchema = (
    16,
    n2,
    _s90,
    0,
    (_s4,),
    ((7, 0),),
)

BOOLEAN_LIST: StaticSchema = (
    16,
    n2,
    _s91,
    0,
    (_s4,),
    ((2, 0),),
)

TIMESTAMP_LIST: StaticSchema = (
    16,
    n2,
    _s92,
    0,
    (_s4,),
    ((4, 0),),
)

FOO_ENUM: StaticSchema = (
    14,
    n2,
    _s93,
    0,
    (
        _s21,
        _s24,
        _s23,
        _s26,
        _s97,
    ),
    (
        (-1, {_s22: _s12}),
        (-1, {_s22: _s94}),
        (-1, {_s22: _s95}),
        (-1, {_s22: _s96}),
        (-1, {_s22: _s98}),
    ),
)

FOO_ENUM_LIST: StaticSchema = (
    16,
    n2,
    _s99,
    0,
    (_s4,),
    ((FOO_ENUM, 0),),
)

INTEGER_ENUM: StaticSchema = (
    15,
    n2,
    _s100,
    0,
    (
        _s101,
        _s102,
        _s103,
    ),
    (
        (-1, {_s22: 1}),
        (-1, {_s22: 2}),
        (-1, {_s22: 3}),
    ),
)

INTEGER_ENUM_LIST: StaticSchema = (
    16,
    n2,
    _s104,
    0,
    (_s4,),
    ((INTEGER_ENUM, 0),),
)

NESTED_STRING_LIST: StaticSchema = (
    16,
    n2,
    _s105,
    0,
    (_s4,),
    ((STRING_LIST, 0),),
)

STRUCTURE_LIST_MEMBER: StaticSchema = (
    18,
    n1,
    _s106,
    0,
    (
        _s107,
        _s108,
    ),
    (
        (3, 0),
        (3, 0),
    ),
)

STRUCTURE_LIST: StaticSchema = (
    16,
    n1,
    _s109,
    0,
    (_s4,),
    ((STRUCTURE_LIST_MEMBER, 0),),
)

BLOB_LIST: StaticSchema = (
    16,
    n2,
    _s110,
    0,
    (_s4,),
    ((1, 0),),
)

RPC_V2_CBOR_LIST_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s111,
    {_s63: None, _s64: None},
    (
        _s112,
        _s113,
        _s114,
        _s115,
        _s116,
        _s117,
        _s118,
        _s119,
        _s120,
        _s121,
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
        (STRUCTURE_LIST, 0),
        (BLOB_LIST, 0),
    ),
)

RPC_V2_CBOR_NESTED_UNION: StaticSchema = (
    19,
    n1,
    _s122,
    0,
    (_s123,),
    ((3, 0),),
)

SPARSE_STRUCT_MAP: StaticSchema = (
    17,
    n1,
    _s124,
    64,
    (
        _s18,
        _s19,
    ),
    (
        (3, 0),
        (GREETING_STRUCT, 0),
    ),
)

SPARSE_NUMBER_MAP: StaticSchema = (
    17,
    n1,
    _s125,
    64,
    (
        _s18,
        _s19,
    ),
    (
        (3, 0),
        (7, 0),
    ),
)

SPARSE_BOOLEAN_MAP: StaticSchema = (
    17,
    n1,
    _s126,
    64,
    (
        _s18,
        _s19,
    ),
    (
        (3, 0),
        (2, 0),
    ),
)

SPARSE_STRING_MAP: StaticSchema = (
    17,
    n2,
    _s127,
    64,
    (
        _s18,
        _s19,
    ),
    (
        (3, 0),
        (3, 0),
    ),
)

SPARSE_SET_MAP: StaticSchema = (
    17,
    n1,
    _s128,
    64,
    (
        _s18,
        _s19,
    ),
    (
        (3, 0),
        (STRING_SET, 0),
    ),
)

RPC_V2_CBOR_SPARSE_MAPS_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s129,
    {_s63: None, _s64: None},
    (
        _s130,
        _s131,
        _s132,
        _s133,
        _s134,
    ),
    (
        (SPARSE_STRUCT_MAP, 0),
        (SPARSE_NUMBER_MAP, 0),
        (SPARSE_BOOLEAN_MAP, 0),
        (SPARSE_STRING_MAP, 0),
        (SPARSE_SET_MAP, 0),
    ),
)

RPC_V2_CBOR_UNION: StaticSchema = (
    19,
    n1,
    _s135,
    0,
    (
        _s123,
        _s136,
    ),
    (
        (3, 0),
        (RPC_V2_CBOR_NESTED_UNION, 0),
    ),
)

RPC_V2_CBOR_UNION_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s137,
    {_s63: None, _s64: None},
    (
        _s138,
        _s139,
    ),
    (
        (RPC_V2_CBOR_UNION, 0),
        (3, 0),
    ),
)

SIMPLE_SCALAR_STRUCTURE: StaticSchema = (
    18,
    n1,
    _s140,
    {_s63: None, _s64: None},
    (
        _s141,
        _s142,
        _s143,
        _s144,
        _s145,
        _s146,
        _s147,
        _s148,
        _s123,
        _s149,
    ),
    (
        (2, 0),
        (2, 0),
        (5, 0),
        (10, 0),
        (9, 0),
        (7, 0),
        (8, 0),
        (6, 0),
        (3, 0),
        (1, 0),
    ),
)

SIMPLE_STRUCTURE: StaticSchema = (
    18,
    n1,
    _s150,
    {_s63: None, _s64: None},
    (_s19,),
    ((3, 0),),
)

SPARSE_STRING_LIST: StaticSchema = (
    16,
    n2,
    _s151,
    64,
    (_s4,),
    ((3, 0),),
)

SPARSE_NULLS_OPERATION_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s152,
    {_s63: None, _s64: None},
    (
        _s153,
        _s133,
    ),
    (
        (SPARSE_STRING_LIST, 0),
        (SPARSE_STRING_MAP, 0),
    ),
)

RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED1: StaticSchema = (
    18,
    n1,
    _s154,
    0,
    (
        _s155,
        _s82,
    ),
    (
        (3, 0),
        (lambda: RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED2, 0),
    ),
)

RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED2: StaticSchema = (
    18,
    n1,
    _s156,
    0,
    (
        _s157,
        _s158,
    ),
    (
        (3, 0),
        (RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED1, 0),
    ),
)
