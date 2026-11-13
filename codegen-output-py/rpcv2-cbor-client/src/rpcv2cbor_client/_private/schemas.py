from types import MappingProxyType

from smithy_core._schema_compact import StaticOperationSchema, StaticSchema

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
_s62 = "Float16Output"
_s63 = "smithy.synthetic#originalShapeId"
_s64 = "smithy.protocoltests.rpcv2Cbor#Float16Output"
_s65 = "smithy.api#output"
_s66 = "DateTime"
_s67 = "smithy.api#timestampFormat"
_s68 = "date-time"
_s69 = "FractionalSecondsOutput"
_s70 = "smithy.protocoltests.rpcv2Cbor#FractionalSecondsOutput"
_s71 = "datetime"
_s72 = "GreetingWithErrorsOutput"
_s73 = "smithy.protocoltests.rpcv2Cbor#GreetingWithErrorsOutput"
_s74 = "greeting"
_s75 = "InvalidGreeting"
_s76 = "Message"
_s77 = "OperationWithDefaultsInput"
_s78 = "smithy.protocoltests.rpcv2Cbor#OperationWithDefaultsInput"
_s79 = "smithy.api#input"
_s80 = "defaults"
_s81 = "clientOptionalDefaults"
_s82 = "topLevelDefault"
_s83 = "otherTopLevelDefault"
_s84 = "OperationWithDefaultsOutput"
_s85 = "smithy.protocoltests.rpcv2Cbor#OperationWithDefaultsOutput"
_s86 = "RpcV2CborNestedUnion"
_s87 = "stringValue"
_s88 = "RpcV2CborUnion"
_s89 = "unionValue"
_s90 = "SparseBooleanMap"
_s91 = "SparseNumberMap"
_s92 = "SparseSetMap"
_s93 = "SparseStructMap"
_s94 = "StructureListMember"
_s95 = "a"
_s96 = "b"
_s97 = "StructureList"
_s98 = "BlobList"
_s99 = "BooleanList"
_s100 = "FooEnum"
_s101 = "Baz"
_s102 = "Bar"
_s103 = "1"
_s104 = "ZERO"
_s105 = "0"
_s106 = "FooEnumList"
_s107 = "IntegerEnum"
_s108 = "A"
_s109 = "B"
_s110 = "C"
_s111 = "IntegerEnumList"
_s112 = "IntegerList"
_s113 = "StringList"
_s114 = "NestedStringList"
_s115 = "SparseStringList"
_s116 = "SparseStringMap"
_s117 = "TimestampList"
_s118 = "EmptyInputOutputInput"
_s119 = "smithy.protocoltests.rpcv2Cbor#EmptyStructure"
_s120 = "EmptyInputOutputOutput"
_s121 = "Float16Input"
_s122 = "smithy.api#Unit"
_s123 = "FractionalSecondsInput"
_s124 = "GreetingWithErrorsInput"
_s125 = "NoInputOutputInput"
_s126 = "NoInputOutputOutput"
_s127 = "OptionalInputOutputInput"
_s128 = "smithy.protocoltests.rpcv2Cbor#SimpleStructure"
_s129 = "OptionalInputOutputOutput"
_s130 = "RecursiveShapesInput"
_s131 = "smithy.protocoltests.rpcv2Cbor#RecursiveShapesInputOutput"
_s132 = "nested"
_s133 = "RecursiveShapesOutput"
_s134 = "RpcV2CborDenseMapsInput"
_s135 = "smithy.protocoltests.rpcv2Cbor#RpcV2CborDenseMapsInputOutput"
_s136 = "denseStructMap"
_s137 = "denseNumberMap"
_s138 = "denseBooleanMap"
_s139 = "denseStringMap"
_s140 = "denseSetMap"
_s141 = "RpcV2CborDenseMapsOutput"
_s142 = "RpcV2CborListsInput"
_s143 = "smithy.protocoltests.rpcv2Cbor#RpcV2CborListInputOutput"
_s144 = "stringList"
_s145 = "stringSet"
_s146 = "integerList"
_s147 = "booleanList"
_s148 = "timestampList"
_s149 = "enumList"
_s150 = "intEnumList"
_s151 = "nestedStringList"
_s152 = "structureList"
_s153 = "blobList"
_s154 = "RpcV2CborListsOutput"
_s155 = "RpcV2CborSparseMapsInput"
_s156 = "smithy.protocoltests.rpcv2Cbor#RpcV2CborSparseMapsInputOutput"
_s157 = "sparseStructMap"
_s158 = "sparseNumberMap"
_s159 = "sparseBooleanMap"
_s160 = "sparseStringMap"
_s161 = "sparseSetMap"
_s162 = "RpcV2CborSparseMapsOutput"
_s163 = "RpcV2CborUnionsInput"
_s164 = "smithy.protocoltests.rpcv2Cbor#RpcV2CborUnionInputOutput"
_s165 = "contents"
_s166 = "otherValue"
_s167 = "RpcV2CborUnionsOutput"
_s168 = "SimpleScalarPropertiesInput"
_s169 = "smithy.protocoltests.rpcv2Cbor#SimpleScalarStructure"
_s170 = "trueBooleanValue"
_s171 = "falseBooleanValue"
_s172 = "byteValue"
_s173 = "doubleValue"
_s174 = "floatValue"
_s175 = "integerValue"
_s176 = "longValue"
_s177 = "shortValue"
_s178 = "blobValue"
_s179 = "SimpleScalarPropertiesOutput"
_s180 = "SparseNullsOperationInput"
_s181 = "smithy.protocoltests.rpcv2Cbor#SparseNullsOperationInputOutput"
_s182 = "sparseStringList"
_s183 = "SparseNullsOperationOutput"
_s184 = "EmptyInputOutput"
_s185 = "Float16"
_s186 = "FractionalSeconds"
_s187 = "GreetingWithErrors"
_s188 = "NoInputOutput"
_s189 = "OperationWithDefaults"
_s190 = "OptionalInputOutput"
_s191 = "RecursiveShapes"
_s192 = "RpcV2CborDenseMaps"
_s193 = "RpcV2CborLists"
_s194 = "RpcV2CborSparseMaps"
_s195 = "RpcV2CborUnions"
_s196 = "SimpleScalarProperties"
_s197 = "SparseNullsOperation"
_s198 = "RpcV2Protocol"
_s199 = "smithy.protocols#rpcv2Cbor"
_s200 = "RecursiveShapesInputOutputNested1"
_s201 = "foo"
_s202 = "RecursiveShapesInputOutputNested2"
_s203 = "bar"
_s204 = "recursiveMember"

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

FLOAT16_OUTPUT: StaticSchema = (
    18,
    n1,
    _s62,
    {_s63: _s64, _s65: None},
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
    {_s63: _s70, _s65: None},
    (_s71,),
    ((DATE_TIME, 0),),
)

GREETING_WITH_ERRORS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s72,
    {_s63: _s73, _s65: None},
    (_s74,),
    ((3, 0),),
)

INVALID_GREETING: StaticSchema = (
    18,
    n1,
    _s75,
    {_s6: _s7},
    (_s76,),
    ((3, 0),),
)

OPERATION_WITH_DEFAULTS_INPUT: StaticSchema = (
    18,
    n1,
    _s77,
    {_s63: _s78, _s79: None},
    (
        _s80,
        _s81,
        _s82,
        _s83,
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
    _s84,
    {_s63: _s85, _s65: None},
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

RPC_V2_CBOR_NESTED_UNION: StaticSchema = (
    19,
    n1,
    _s86,
    0,
    (_s87,),
    ((3, 0),),
)

RPC_V2_CBOR_UNION: StaticSchema = (
    19,
    n1,
    _s88,
    0,
    (
        _s87,
        _s89,
    ),
    (
        (3, 0),
        (RPC_V2_CBOR_NESTED_UNION, 0),
    ),
)

SPARSE_BOOLEAN_MAP: StaticSchema = (
    17,
    n1,
    _s90,
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

SPARSE_NUMBER_MAP: StaticSchema = (
    17,
    n1,
    _s91,
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

SPARSE_SET_MAP: StaticSchema = (
    17,
    n1,
    _s92,
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

SPARSE_STRUCT_MAP: StaticSchema = (
    17,
    n1,
    _s93,
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

STRUCTURE_LIST_MEMBER: StaticSchema = (
    18,
    n1,
    _s94,
    0,
    (
        _s95,
        _s96,
    ),
    (
        (3, 0),
        (3, 0),
    ),
)

STRUCTURE_LIST: StaticSchema = (
    16,
    n1,
    _s97,
    0,
    (_s4,),
    ((STRUCTURE_LIST_MEMBER, 0),),
)

BLOB_LIST: StaticSchema = (
    16,
    n2,
    _s98,
    0,
    (_s4,),
    ((1, 0),),
)

BOOLEAN_LIST: StaticSchema = (
    16,
    n2,
    _s99,
    0,
    (_s4,),
    ((2, 0),),
)

FOO_ENUM: StaticSchema = (
    14,
    n2,
    _s100,
    0,
    (
        _s21,
        _s24,
        _s23,
        _s26,
        _s104,
    ),
    (
        (-1, {_s22: _s12}),
        (-1, {_s22: _s101}),
        (-1, {_s22: _s102}),
        (-1, {_s22: _s103}),
        (-1, {_s22: _s105}),
    ),
)

FOO_ENUM_LIST: StaticSchema = (
    16,
    n2,
    _s106,
    0,
    (_s4,),
    ((FOO_ENUM, 0),),
)

INTEGER_ENUM: StaticSchema = (
    15,
    n2,
    _s107,
    0,
    (
        _s108,
        _s109,
        _s110,
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
    _s111,
    0,
    (_s4,),
    ((INTEGER_ENUM, 0),),
)

INTEGER_LIST: StaticSchema = (
    16,
    n2,
    _s112,
    0,
    (_s4,),
    ((7, 0),),
)

STRING_LIST: StaticSchema = (
    16,
    n2,
    _s113,
    0,
    (_s4,),
    ((3, 0),),
)

NESTED_STRING_LIST: StaticSchema = (
    16,
    n2,
    _s114,
    0,
    (_s4,),
    ((STRING_LIST, 0),),
)

SPARSE_STRING_LIST: StaticSchema = (
    16,
    n2,
    _s115,
    64,
    (_s4,),
    ((3, 0),),
)

SPARSE_STRING_MAP: StaticSchema = (
    17,
    n2,
    _s116,
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

TIMESTAMP_LIST: StaticSchema = (
    16,
    n2,
    _s117,
    0,
    (_s4,),
    ((4, 0),),
)

EMPTY_INPUT_OUTPUT_INPUT: StaticSchema = (
    18,
    n1,
    _s118,
    {_s63: _s119, _s79: None},
)

EMPTY_INPUT_OUTPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s120,
    {_s63: _s119, _s65: None},
)

FLOAT16_INPUT: StaticSchema = (
    18,
    n1,
    _s121,
    {_s63: _s122, _s79: None},
)

FRACTIONAL_SECONDS_INPUT: StaticSchema = (
    18,
    n1,
    _s123,
    {_s63: _s122, _s79: None},
)

GREETING_WITH_ERRORS_INPUT: StaticSchema = (
    18,
    n1,
    _s124,
    {_s63: _s122, _s79: None},
)

NO_INPUT_OUTPUT_INPUT: StaticSchema = (
    18,
    n1,
    _s125,
    {_s63: _s122, _s79: None},
)

NO_INPUT_OUTPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s126,
    {_s63: _s122, _s65: None},
)

OPTIONAL_INPUT_OUTPUT_INPUT: StaticSchema = (
    18,
    n1,
    _s127,
    {_s63: _s128, _s79: None},
    (_s19,),
    ((3, 0),),
)

OPTIONAL_INPUT_OUTPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s129,
    {_s63: _s128, _s65: None},
    (_s19,),
    ((3, 0),),
)

RECURSIVE_SHAPES_INPUT: StaticSchema = (
    18,
    n1,
    _s130,
    {_s63: _s131, _s79: None},
    (_s132,),
    ((lambda: RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED1, 0),),
)

RECURSIVE_SHAPES_OUTPUT: StaticSchema = (
    18,
    n1,
    _s133,
    {_s63: _s131, _s65: None},
    (_s132,),
    ((lambda: RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED1, 0),),
)

RPC_V2_CBOR_DENSE_MAPS_INPUT: StaticSchema = (
    18,
    n1,
    _s134,
    {_s63: _s135, _s79: None},
    (
        _s136,
        _s137,
        _s138,
        _s139,
        _s140,
    ),
    (
        (DENSE_STRUCT_MAP, 0),
        (DENSE_NUMBER_MAP, 0),
        (DENSE_BOOLEAN_MAP, 0),
        (DENSE_STRING_MAP, 0),
        (DENSE_SET_MAP, 0),
    ),
)

RPC_V2_CBOR_DENSE_MAPS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s141,
    {_s63: _s135, _s65: None},
    (
        _s136,
        _s137,
        _s138,
        _s139,
        _s140,
    ),
    (
        (DENSE_STRUCT_MAP, 0),
        (DENSE_NUMBER_MAP, 0),
        (DENSE_BOOLEAN_MAP, 0),
        (DENSE_STRING_MAP, 0),
        (DENSE_SET_MAP, 0),
    ),
)

RPC_V2_CBOR_LISTS_INPUT: StaticSchema = (
    18,
    n1,
    _s142,
    {_s63: _s143, _s79: None},
    (
        _s144,
        _s145,
        _s146,
        _s147,
        _s148,
        _s149,
        _s150,
        _s151,
        _s152,
        _s153,
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

RPC_V2_CBOR_LISTS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s154,
    {_s63: _s143, _s65: None},
    (
        _s144,
        _s145,
        _s146,
        _s147,
        _s148,
        _s149,
        _s150,
        _s151,
        _s152,
        _s153,
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

RPC_V2_CBOR_SPARSE_MAPS_INPUT: StaticSchema = (
    18,
    n1,
    _s155,
    {_s63: _s156, _s79: None},
    (
        _s157,
        _s158,
        _s159,
        _s160,
        _s161,
    ),
    (
        (SPARSE_STRUCT_MAP, 0),
        (SPARSE_NUMBER_MAP, 0),
        (SPARSE_BOOLEAN_MAP, 0),
        (SPARSE_STRING_MAP, 0),
        (SPARSE_SET_MAP, 0),
    ),
)

RPC_V2_CBOR_SPARSE_MAPS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s162,
    {_s63: _s156, _s65: None},
    (
        _s157,
        _s158,
        _s159,
        _s160,
        _s161,
    ),
    (
        (SPARSE_STRUCT_MAP, 0),
        (SPARSE_NUMBER_MAP, 0),
        (SPARSE_BOOLEAN_MAP, 0),
        (SPARSE_STRING_MAP, 0),
        (SPARSE_SET_MAP, 0),
    ),
)

RPC_V2_CBOR_UNIONS_INPUT: StaticSchema = (
    18,
    n1,
    _s163,
    {_s63: _s164, _s79: None},
    (
        _s165,
        _s166,
    ),
    (
        (RPC_V2_CBOR_UNION, 0),
        (3, 0),
    ),
)

RPC_V2_CBOR_UNIONS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s167,
    {_s63: _s164, _s65: None},
    (
        _s165,
        _s166,
    ),
    (
        (RPC_V2_CBOR_UNION, 0),
        (3, 0),
    ),
)

SIMPLE_SCALAR_PROPERTIES_INPUT: StaticSchema = (
    18,
    n1,
    _s168,
    {_s63: _s169, _s79: None},
    (
        _s170,
        _s171,
        _s172,
        _s173,
        _s174,
        _s175,
        _s176,
        _s177,
        _s87,
        _s178,
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

SIMPLE_SCALAR_PROPERTIES_OUTPUT: StaticSchema = (
    18,
    n1,
    _s179,
    {_s63: _s169, _s65: None},
    (
        _s170,
        _s171,
        _s172,
        _s173,
        _s174,
        _s175,
        _s176,
        _s177,
        _s87,
        _s178,
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

SPARSE_NULLS_OPERATION_INPUT: StaticSchema = (
    18,
    n1,
    _s180,
    {_s63: _s181, _s79: None},
    (
        _s182,
        _s160,
    ),
    (
        (SPARSE_STRING_LIST, 0),
        (SPARSE_STRING_MAP, 0),
    ),
)

SPARSE_NULLS_OPERATION_OUTPUT: StaticSchema = (
    18,
    n1,
    _s183,
    {_s63: _s181, _s65: None},
    (
        _s182,
        _s160,
    ),
    (
        (SPARSE_STRING_LIST, 0),
        (SPARSE_STRING_MAP, 0),
    ),
)

EMPTY_INPUT_OUTPUT: StaticOperationSchema = (
    23,
    n1,
    _s184,
    0,
    EMPTY_INPUT_OUTPUT_INPUT,
    EMPTY_INPUT_OUTPUT_OUTPUT,
    (),
)

FLOAT16: StaticOperationSchema = (
    23,
    n1,
    _s185,
    0,
    FLOAT16_INPUT,
    FLOAT16_OUTPUT,
    (),
)

FRACTIONAL_SECONDS: StaticOperationSchema = (
    23,
    n1,
    _s186,
    0,
    FRACTIONAL_SECONDS_INPUT,
    FRACTIONAL_SECONDS_OUTPUT,
    (),
)

GREETING_WITH_ERRORS: StaticOperationSchema = (
    23,
    n1,
    _s187,
    0,
    GREETING_WITH_ERRORS_INPUT,
    GREETING_WITH_ERRORS_OUTPUT,
    (COMPLEX_ERROR, INVALID_GREETING),
)

NO_INPUT_OUTPUT: StaticOperationSchema = (
    23,
    n1,
    _s188,
    0,
    NO_INPUT_OUTPUT_INPUT,
    NO_INPUT_OUTPUT_OUTPUT,
    (),
)

OPERATION_WITH_DEFAULTS: StaticOperationSchema = (
    23,
    n1,
    _s189,
    0,
    OPERATION_WITH_DEFAULTS_INPUT,
    OPERATION_WITH_DEFAULTS_OUTPUT,
    (VALIDATION_EXCEPTION,),
)

OPTIONAL_INPUT_OUTPUT: StaticOperationSchema = (
    23,
    n1,
    _s190,
    0,
    OPTIONAL_INPUT_OUTPUT_INPUT,
    OPTIONAL_INPUT_OUTPUT_OUTPUT,
    (),
)

RECURSIVE_SHAPES: StaticOperationSchema = (
    23,
    n1,
    _s191,
    0,
    RECURSIVE_SHAPES_INPUT,
    RECURSIVE_SHAPES_OUTPUT,
    (),
)

RPC_V2_CBOR_DENSE_MAPS: StaticOperationSchema = (
    23,
    n1,
    _s192,
    0,
    RPC_V2_CBOR_DENSE_MAPS_INPUT,
    RPC_V2_CBOR_DENSE_MAPS_OUTPUT,
    (VALIDATION_EXCEPTION,),
)

RPC_V2_CBOR_LISTS: StaticOperationSchema = (
    23,
    n1,
    _s193,
    0,
    RPC_V2_CBOR_LISTS_INPUT,
    RPC_V2_CBOR_LISTS_OUTPUT,
    (VALIDATION_EXCEPTION,),
)

RPC_V2_CBOR_SPARSE_MAPS: StaticOperationSchema = (
    23,
    n1,
    _s194,
    0,
    RPC_V2_CBOR_SPARSE_MAPS_INPUT,
    RPC_V2_CBOR_SPARSE_MAPS_OUTPUT,
    (VALIDATION_EXCEPTION,),
)

RPC_V2_CBOR_UNIONS: StaticOperationSchema = (
    23,
    n1,
    _s195,
    0,
    RPC_V2_CBOR_UNIONS_INPUT,
    RPC_V2_CBOR_UNIONS_OUTPUT,
    (),
)

SIMPLE_SCALAR_PROPERTIES: StaticOperationSchema = (
    23,
    n1,
    _s196,
    0,
    SIMPLE_SCALAR_PROPERTIES_INPUT,
    SIMPLE_SCALAR_PROPERTIES_OUTPUT,
    (),
)

SPARSE_NULLS_OPERATION: StaticOperationSchema = (
    23,
    n1,
    _s197,
    0,
    SPARSE_NULLS_OPERATION_INPUT,
    SPARSE_NULLS_OPERATION_OUTPUT,
    (),
)

RPC_V2_PROTOCOL: StaticSchema = (
    21,
    n1,
    _s198,
    {_s199: None},
)

RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED1: StaticSchema = (
    18,
    n1,
    _s200,
    0,
    (
        _s201,
        _s132,
    ),
    (
        (3, 0),
        (lambda: RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED2, 0),
    ),
)

RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED2: StaticSchema = (
    18,
    n1,
    _s202,
    0,
    (
        _s203,
        _s204,
    ),
    (
        (3, 0),
        (RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED1, 0),
    ),
)
