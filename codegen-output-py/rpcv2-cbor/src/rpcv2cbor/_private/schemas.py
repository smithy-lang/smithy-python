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
_s10 = "smithy.api#clientOptional"
_s11 = "smithy.api#default"
_s12 = "ComplexNestedErrorData"
_s13 = "Foo"
_s14 = "ComplexError"
_s15 = "TopLevel"
_s16 = "Nested"
_s17 = "TestStringList"
_s18 = "TestStringMap"
_s19 = "key"
_s20 = "value"
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
_s34 = "defaultTimestamp"
_s35 = "defaultBlob"
_s36 = "YWJj"
_s37 = "defaultByte"
_s38 = "defaultShort"
_s39 = "defaultInteger"
_s40 = "defaultLong"
_s41 = "defaultFloat"
_s42 = "defaultDouble"
_s43 = "defaultMap"
_s44 = "defaultEnum"
_s45 = "defaultIntEnum"
_s46 = "emptyString"
_s47 = ""
_s48 = "falseBoolean"
_s49 = "emptyBlob"
_s50 = "zeroByte"
_s51 = "zeroShort"
_s52 = "zeroInteger"
_s53 = "zeroLong"
_s54 = "zeroFloat"
_s55 = "zeroDouble"
_s56 = "DenseBooleanMap"
_s57 = "DenseNumberMap"
n2 = "smithy.protocoltests.shared"
_s58 = "StringSet"
_s59 = "DenseSetMap"
_s60 = "DenseStringMap"
_s61 = "GreetingStruct"
_s62 = "DenseStructMap"
_s63 = "EmptyStructure"
_s64 = "smithy.api#input"
_s65 = "smithy.api#output"
_s66 = "Float16Output"
_s67 = "DateTime"
_s68 = "smithy.api#timestampFormat"
_s69 = "date-time"
_s70 = "FractionalSecondsOutput"
_s71 = "datetime"
_s72 = "GreetingWithErrorsOutput"
_s73 = "greeting"
_s74 = "InvalidGreeting"
_s75 = "Message"
_s76 = "OperationWithDefaultsInput"
_s77 = "defaults"
_s78 = "clientOptionalDefaults"
_s79 = "topLevelDefault"
_s80 = "otherTopLevelDefault"
_s81 = "OperationWithDefaultsOutput"
_s82 = "RecursiveShapesInputOutput"
_s83 = "nested"
_s84 = "RpcV2CborDenseMapsInputOutput"
_s85 = "denseStructMap"
_s86 = "denseNumberMap"
_s87 = "denseBooleanMap"
_s88 = "denseStringMap"
_s89 = "denseSetMap"
_s90 = "StringList"
_s91 = "IntegerList"
_s92 = "BooleanList"
_s93 = "TimestampList"
_s94 = "FooEnum"
_s95 = "Baz"
_s96 = "Bar"
_s97 = "1"
_s98 = "ZERO"
_s99 = "0"
_s100 = "FooEnumList"
_s101 = "IntegerEnum"
_s102 = "A"
_s103 = "B"
_s104 = "C"
_s105 = "IntegerEnumList"
_s106 = "NestedStringList"
_s107 = "StructureListMember"
_s108 = "a"
_s109 = "b"
_s110 = "StructureList"
_s111 = "BlobList"
_s112 = "RpcV2CborListInputOutput"
_s113 = "stringList"
_s114 = "stringSet"
_s115 = "integerList"
_s116 = "booleanList"
_s117 = "timestampList"
_s118 = "enumList"
_s119 = "intEnumList"
_s120 = "nestedStringList"
_s121 = "structureList"
_s122 = "blobList"
_s123 = "RpcV2CborNestedUnion"
_s124 = "stringValue"
_s125 = "SparseStructMap"
_s126 = "SparseNumberMap"
_s127 = "SparseBooleanMap"
_s128 = "SparseStringMap"
_s129 = "SparseSetMap"
_s130 = "RpcV2CborSparseMapsInputOutput"
_s131 = "sparseStructMap"
_s132 = "sparseNumberMap"
_s133 = "sparseBooleanMap"
_s134 = "sparseStringMap"
_s135 = "sparseSetMap"
_s136 = "RpcV2CborUnion"
_s137 = "unionValue"
_s138 = "RpcV2CborUnionInputOutput"
_s139 = "contents"
_s140 = "otherValue"
_s141 = "SimpleScalarStructure"
_s142 = "trueBooleanValue"
_s143 = "falseBooleanValue"
_s144 = "byteValue"
_s145 = "doubleValue"
_s146 = "floatValue"
_s147 = "integerValue"
_s148 = "longValue"
_s149 = "shortValue"
_s150 = "blobValue"
_s151 = "SimpleStructure"
_s152 = "SparseStringList"
_s153 = "SparseNullsOperationInputOutput"
_s154 = "sparseStringList"
_s155 = "RecursiveShapesInputOutputNested1"
_s156 = "foo"
_s157 = "RecursiveShapesInputOutputNested2"
_s158 = "bar"
_s159 = "recursiveMember"

VALIDATION_EXCEPTION_FIELD: StaticSchema = (
    18,
    n0,
    _s0,
    0,
    (_s1, _s2),
    ((3, 1), (3, 1)),
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
    (_s2, _s8),
    ((3, 1), (VALIDATION_EXCEPTION_FIELD_LIST, 0)),
)

CLIENT_OPTIONAL_DEFAULTS: StaticSchema = (
    18,
    n1,
    _s9,
    0,
    (_s4,),
    ((7, {_s10: None, _s11: 0}),),
)

COMPLEX_NESTED_ERROR_DATA: StaticSchema = (
    18,
    n1,
    _s12,
    0,
    (_s13,),
    ((3, 0),),
)

COMPLEX_ERROR: StaticSchema = (
    18,
    n1,
    _s14,
    {_s6: _s7},
    (_s15, _s16),
    ((3, 0), (COMPLEX_NESTED_ERROR_DATA, 0)),
)

TEST_STRING_LIST: StaticSchema = (
    16,
    n1,
    _s17,
    0,
    (_s4,),
    ((3, 0),),
)

TEST_STRING_MAP: StaticSchema = (
    17,
    n1,
    _s18,
    0,
    (_s19, _s20),
    ((3, 0), (3, 0)),
)

TEST_ENUM: StaticSchema = (
    14,
    n1,
    _s21,
    0,
    (_s22, _s24, _s25),
    ((-1, {_s23: _s22}), (-1, {_s23: _s24}), (-1, {_s23: _s25})),
)

TEST_INT_ENUM: StaticSchema = (
    15,
    n1,
    _s26,
    0,
    (_s27, _s28),
    ((-1, {_s23: 1}), (-1, {_s23: 2})),
)

DEFAULTS: StaticSchema = (
    18,
    n1,
    _s29,
    0,
    (
        _s30,
        _s32,
        _s33,
        _s34,
        _s35,
        _s37,
        _s38,
        _s39,
        _s40,
        _s41,
        _s42,
        _s43,
        _s44,
        _s45,
        _s46,
        _s48,
        _s49,
        _s50,
        _s51,
        _s52,
        _s53,
        _s54,
        _s55,
    ),
    (
        (3, {_s11: _s31}),
        (2, {_s11: True}),
        (TEST_STRING_LIST, {_s11: ()}),
        (4, {_s11: 0}),
        (1, {_s11: _s36}),
        (5, {_s11: 1}),
        (6, {_s11: 1}),
        (7, {_s11: 10}),
        (8, {_s11: 100}),
        (9, {_s11: 1.0}),
        (10, {_s11: 1.0}),
        (TEST_STRING_MAP, {_s11: MappingProxyType[str, object]({})}),
        (TEST_ENUM, {_s11: _s22}),
        (TEST_INT_ENUM, {_s11: 1}),
        (3, {_s11: _s47}),
        (2, {_s11: False}),
        (1, {_s11: _s47}),
        (5, {_s11: 0}),
        (6, {_s11: 0}),
        (7, {_s11: 0}),
        (8, {_s11: 0}),
        (9, {_s11: 0.0}),
        (10, {_s11: 0.0}),
    ),
)

DENSE_BOOLEAN_MAP: StaticSchema = (
    17,
    n1,
    _s56,
    0,
    (_s19, _s20),
    ((3, 0), (2, 0)),
)

DENSE_NUMBER_MAP: StaticSchema = (
    17,
    n1,
    _s57,
    0,
    (_s19, _s20),
    ((3, 0), (7, 0)),
)

STRING_SET: StaticSchema = (
    16,
    n2,
    _s58,
    0,
    (_s4,),
    ((3, 0),),
)

DENSE_SET_MAP: StaticSchema = (
    17,
    n1,
    _s59,
    0,
    (_s19, _s20),
    ((3, 0), (STRING_SET, 0)),
)

DENSE_STRING_MAP: StaticSchema = (
    17,
    n1,
    _s60,
    0,
    (_s19, _s20),
    ((3, 0), (3, 0)),
)

GREETING_STRUCT: StaticSchema = (
    18,
    n2,
    _s61,
    0,
    (_s31,),
    ((3, 0),),
)

DENSE_STRUCT_MAP: StaticSchema = (
    17,
    n1,
    _s62,
    0,
    (_s19, _s20),
    ((3, 0), (GREETING_STRUCT, 0)),
)

EMPTY_STRUCTURE: StaticSchema = (
    18,
    n1,
    _s63,
    {_s64: None, _s65: None},
)

FLOAT16_OUTPUT: StaticSchema = (
    18,
    n1,
    _s66,
    {_s65: None},
    (_s20,),
    ((10, 0),),
)

DATE_TIME: StaticSchema = (
    4,
    n2,
    _s67,
    {_s68: _s69},
)

FRACTIONAL_SECONDS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s70,
    {_s65: None},
    (_s71,),
    ((DATE_TIME, 0),),
)

GREETING_WITH_ERRORS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s72,
    {_s65: None},
    (_s73,),
    ((3, 0),),
)

INVALID_GREETING: StaticSchema = (
    18,
    n1,
    _s74,
    {_s6: _s7},
    (_s75,),
    ((3, 0),),
)

OPERATION_WITH_DEFAULTS_INPUT: StaticSchema = (
    18,
    n1,
    _s76,
    {_s64: None},
    (_s77, _s78, _s79, _s80),
    ((DEFAULTS, 0), (CLIENT_OPTIONAL_DEFAULTS, 0), (3, {_s11: _s31}), (7, {_s11: 0})),
)

OPERATION_WITH_DEFAULTS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s81,
    {_s65: None},
    (
        _s30,
        _s32,
        _s33,
        _s34,
        _s35,
        _s37,
        _s38,
        _s39,
        _s40,
        _s41,
        _s42,
        _s43,
        _s44,
        _s45,
        _s46,
        _s48,
        _s49,
        _s50,
        _s51,
        _s52,
        _s53,
        _s54,
        _s55,
    ),
    (
        (3, {_s11: _s31}),
        (2, {_s11: True}),
        (TEST_STRING_LIST, {_s11: ()}),
        (4, {_s11: 0}),
        (1, {_s11: _s36}),
        (5, {_s11: 1}),
        (6, {_s11: 1}),
        (7, {_s11: 10}),
        (8, {_s11: 100}),
        (9, {_s11: 1.0}),
        (10, {_s11: 1.0}),
        (TEST_STRING_MAP, {_s11: MappingProxyType[str, object]({})}),
        (TEST_ENUM, {_s11: _s22}),
        (TEST_INT_ENUM, {_s11: 1}),
        (3, {_s11: _s47}),
        (2, {_s11: False}),
        (1, {_s11: _s47}),
        (5, {_s11: 0}),
        (6, {_s11: 0}),
        (7, {_s11: 0}),
        (8, {_s11: 0}),
        (9, {_s11: 0.0}),
        (10, {_s11: 0.0}),
    ),
)

RECURSIVE_SHAPES_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s82,
    {_s64: None, _s65: None},
    (_s83,),
    ((lambda: RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED1, 0),),
)

RPC_V2_CBOR_DENSE_MAPS_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s84,
    {_s64: None, _s65: None},
    (_s85, _s86, _s87, _s88, _s89),
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
    _s90,
    0,
    (_s4,),
    ((3, 0),),
)

INTEGER_LIST: StaticSchema = (
    16,
    n2,
    _s91,
    0,
    (_s4,),
    ((7, 0),),
)

BOOLEAN_LIST: StaticSchema = (
    16,
    n2,
    _s92,
    0,
    (_s4,),
    ((2, 0),),
)

TIMESTAMP_LIST: StaticSchema = (
    16,
    n2,
    _s93,
    0,
    (_s4,),
    ((4, 0),),
)

FOO_ENUM: StaticSchema = (
    14,
    n2,
    _s94,
    0,
    (_s22, _s25, _s24, _s27, _s98),
    (
        (-1, {_s23: _s13}),
        (-1, {_s23: _s95}),
        (-1, {_s23: _s96}),
        (-1, {_s23: _s97}),
        (-1, {_s23: _s99}),
    ),
)

FOO_ENUM_LIST: StaticSchema = (
    16,
    n2,
    _s100,
    0,
    (_s4,),
    ((FOO_ENUM, 0),),
)

INTEGER_ENUM: StaticSchema = (
    15,
    n2,
    _s101,
    0,
    (_s102, _s103, _s104),
    ((-1, {_s23: 1}), (-1, {_s23: 2}), (-1, {_s23: 3})),
)

INTEGER_ENUM_LIST: StaticSchema = (
    16,
    n2,
    _s105,
    0,
    (_s4,),
    ((INTEGER_ENUM, 0),),
)

NESTED_STRING_LIST: StaticSchema = (
    16,
    n2,
    _s106,
    0,
    (_s4,),
    ((STRING_LIST, 0),),
)

STRUCTURE_LIST_MEMBER: StaticSchema = (
    18,
    n1,
    _s107,
    0,
    (_s108, _s109),
    ((3, 0), (3, 0)),
)

STRUCTURE_LIST: StaticSchema = (
    16,
    n1,
    _s110,
    0,
    (_s4,),
    ((STRUCTURE_LIST_MEMBER, 0),),
)

BLOB_LIST: StaticSchema = (
    16,
    n2,
    _s111,
    0,
    (_s4,),
    ((1, 0),),
)

RPC_V2_CBOR_LIST_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s112,
    {_s64: None, _s65: None},
    (_s113, _s114, _s115, _s116, _s117, _s118, _s119, _s120, _s121, _s122),
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
    _s123,
    0,
    (_s124,),
    ((3, 0),),
)

SPARSE_STRUCT_MAP: StaticSchema = (
    17,
    n1,
    _s125,
    64,
    (_s19, _s20),
    ((3, 0), (GREETING_STRUCT, 0)),
)

SPARSE_NUMBER_MAP: StaticSchema = (
    17,
    n1,
    _s126,
    64,
    (_s19, _s20),
    ((3, 0), (7, 0)),
)

SPARSE_BOOLEAN_MAP: StaticSchema = (
    17,
    n1,
    _s127,
    64,
    (_s19, _s20),
    ((3, 0), (2, 0)),
)

SPARSE_STRING_MAP: StaticSchema = (
    17,
    n2,
    _s128,
    64,
    (_s19, _s20),
    ((3, 0), (3, 0)),
)

SPARSE_SET_MAP: StaticSchema = (
    17,
    n1,
    _s129,
    64,
    (_s19, _s20),
    ((3, 0), (STRING_SET, 0)),
)

RPC_V2_CBOR_SPARSE_MAPS_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s130,
    {_s64: None, _s65: None},
    (_s131, _s132, _s133, _s134, _s135),
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
    _s136,
    0,
    (_s124, _s137),
    ((3, 0), (RPC_V2_CBOR_NESTED_UNION, 0)),
)

RPC_V2_CBOR_UNION_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s138,
    {_s64: None, _s65: None},
    (_s139, _s140),
    ((RPC_V2_CBOR_UNION, 0), (3, 0)),
)

SIMPLE_SCALAR_STRUCTURE: StaticSchema = (
    18,
    n1,
    _s141,
    {_s64: None, _s65: None},
    (_s142, _s143, _s144, _s145, _s146, _s147, _s148, _s149, _s124, _s150),
    ((2, 0), (2, 0), (5, 0), (10, 0), (9, 0), (7, 0), (8, 0), (6, 0), (3, 0), (1, 0)),
)

SIMPLE_STRUCTURE: StaticSchema = (
    18,
    n1,
    _s151,
    {_s64: None, _s65: None},
    (_s20,),
    ((3, 0),),
)

SPARSE_STRING_LIST: StaticSchema = (
    16,
    n2,
    _s152,
    64,
    (_s4,),
    ((3, 0),),
)

SPARSE_NULLS_OPERATION_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s153,
    {_s64: None, _s65: None},
    (_s154, _s134),
    ((SPARSE_STRING_LIST, 0), (SPARSE_STRING_MAP, 0)),
)

RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED1: StaticSchema = (
    18,
    n1,
    _s155,
    0,
    (_s156, _s83),
    ((3, 0), (lambda: RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED2, 0)),
)

RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED2: StaticSchema = (
    18,
    n1,
    _s157,
    0,
    (_s158, _s159),
    ((3, 0), (RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED1, 0)),
)
