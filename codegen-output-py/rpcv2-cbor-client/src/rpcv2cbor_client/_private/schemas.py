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
_s63 = "Float16Output"
_s64 = "smithy.synthetic#originalShapeId"
_s65 = "smithy.protocoltests.rpcv2Cbor#Float16Output"
_s66 = "smithy.api#output"
_s67 = "DateTime"
_s68 = "smithy.api#timestampFormat"
_s69 = "date-time"
_s70 = "FractionalSecondsOutput"
_s71 = "smithy.protocoltests.rpcv2Cbor#FractionalSecondsOutput"
_s72 = "datetime"
_s73 = "GreetingWithErrorsOutput"
_s74 = "smithy.protocoltests.rpcv2Cbor#GreetingWithErrorsOutput"
_s75 = "greeting"
_s76 = "InvalidGreeting"
_s77 = "Message"
_s78 = "OperationWithDefaultsInput"
_s79 = "smithy.protocoltests.rpcv2Cbor#OperationWithDefaultsInput"
_s80 = "smithy.api#input"
_s81 = "defaults"
_s82 = "clientOptionalDefaults"
_s83 = "topLevelDefault"
_s84 = "otherTopLevelDefault"
_s85 = "OperationWithDefaultsOutput"
_s86 = "smithy.protocoltests.rpcv2Cbor#OperationWithDefaultsOutput"
_s87 = "RpcV2CborNestedUnion"
_s88 = "stringValue"
_s89 = "RpcV2CborUnion"
_s90 = "unionValue"
_s91 = "SparseBooleanMap"
_s92 = "SparseNumberMap"
_s93 = "SparseSetMap"
_s94 = "SparseStructMap"
_s95 = "StructureListMember"
_s96 = "a"
_s97 = "b"
_s98 = "StructureList"
_s99 = "BlobList"
_s100 = "BooleanList"
_s101 = "FooEnum"
_s102 = "Baz"
_s103 = "Bar"
_s104 = "1"
_s105 = "ZERO"
_s106 = "0"
_s107 = "FooEnumList"
_s108 = "IntegerEnum"
_s109 = "A"
_s110 = "B"
_s111 = "C"
_s112 = "IntegerEnumList"
_s113 = "IntegerList"
_s114 = "StringList"
_s115 = "NestedStringList"
_s116 = "SparseStringList"
_s117 = "SparseStringMap"
_s118 = "TimestampList"
_s119 = "EmptyInputOutputInput"
_s120 = "smithy.protocoltests.rpcv2Cbor#EmptyStructure"
_s121 = "EmptyInputOutputOutput"
_s122 = "Float16Input"
_s123 = "smithy.api#Unit"
_s124 = "FractionalSecondsInput"
_s125 = "GreetingWithErrorsInput"
_s126 = "NoInputOutputInput"
_s127 = "NoInputOutputOutput"
_s128 = "OptionalInputOutputInput"
_s129 = "smithy.protocoltests.rpcv2Cbor#SimpleStructure"
_s130 = "OptionalInputOutputOutput"
_s131 = "RecursiveShapesInput"
_s132 = "smithy.protocoltests.rpcv2Cbor#RecursiveShapesInputOutput"
_s133 = "nested"
_s134 = "RecursiveShapesOutput"
_s135 = "RpcV2CborDenseMapsInput"
_s136 = "smithy.protocoltests.rpcv2Cbor#RpcV2CborDenseMapsInputOutput"
_s137 = "denseStructMap"
_s138 = "denseNumberMap"
_s139 = "denseBooleanMap"
_s140 = "denseStringMap"
_s141 = "denseSetMap"
_s142 = "RpcV2CborDenseMapsOutput"
_s143 = "RpcV2CborListsInput"
_s144 = "smithy.protocoltests.rpcv2Cbor#RpcV2CborListInputOutput"
_s145 = "stringList"
_s146 = "stringSet"
_s147 = "integerList"
_s148 = "booleanList"
_s149 = "timestampList"
_s150 = "enumList"
_s151 = "intEnumList"
_s152 = "nestedStringList"
_s153 = "structureList"
_s154 = "blobList"
_s155 = "RpcV2CborListsOutput"
_s156 = "RpcV2CborSparseMapsInput"
_s157 = "smithy.protocoltests.rpcv2Cbor#RpcV2CborSparseMapsInputOutput"
_s158 = "sparseStructMap"
_s159 = "sparseNumberMap"
_s160 = "sparseBooleanMap"
_s161 = "sparseStringMap"
_s162 = "sparseSetMap"
_s163 = "RpcV2CborSparseMapsOutput"
_s164 = "RpcV2CborUnionsInput"
_s165 = "smithy.protocoltests.rpcv2Cbor#RpcV2CborUnionInputOutput"
_s166 = "contents"
_s167 = "otherValue"
_s168 = "RpcV2CborUnionsOutput"
_s169 = "SimpleScalarPropertiesInput"
_s170 = "smithy.protocoltests.rpcv2Cbor#SimpleScalarStructure"
_s171 = "trueBooleanValue"
_s172 = "falseBooleanValue"
_s173 = "byteValue"
_s174 = "doubleValue"
_s175 = "floatValue"
_s176 = "integerValue"
_s177 = "longValue"
_s178 = "shortValue"
_s179 = "blobValue"
_s180 = "SimpleScalarPropertiesOutput"
_s181 = "SparseNullsOperationInput"
_s182 = "smithy.protocoltests.rpcv2Cbor#SparseNullsOperationInputOutput"
_s183 = "sparseStringList"
_s184 = "SparseNullsOperationOutput"
_s185 = "EmptyInputOutput"
_s186 = "Float16"
_s187 = "FractionalSeconds"
_s188 = "GreetingWithErrors"
_s189 = "NoInputOutput"
_s190 = "OperationWithDefaults"
_s191 = "OptionalInputOutput"
_s192 = "RecursiveShapes"
_s193 = "RpcV2CborDenseMaps"
_s194 = "RpcV2CborLists"
_s195 = "RpcV2CborSparseMaps"
_s196 = "RpcV2CborUnions"
_s197 = "SimpleScalarProperties"
_s198 = "SparseNullsOperation"
_s199 = "RpcV2Protocol"
_s200 = "smithy.protocols#rpcv2Cbor"
_s201 = "RecursiveShapesInputOutputNested1"
_s202 = "foo"
_s203 = "RecursiveShapesInputOutputNested2"
_s204 = "bar"
_s205 = "recursiveMember"

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

FLOAT16_OUTPUT: StaticSchema = (
    18,
    n1,
    _s63,
    {_s64: _s65, _s66: None},
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
    {_s64: _s71, _s66: None},
    (_s72,),
    ((DATE_TIME, 0),),
)

GREETING_WITH_ERRORS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s73,
    {_s64: _s74, _s66: None},
    (_s75,),
    ((3, 0),),
)

INVALID_GREETING: StaticSchema = (
    18,
    n1,
    _s76,
    {_s6: _s7},
    (_s77,),
    ((3, 0),),
)

OPERATION_WITH_DEFAULTS_INPUT: StaticSchema = (
    18,
    n1,
    _s78,
    {_s64: _s79, _s80: None},
    (_s81, _s82, _s83, _s84),
    ((DEFAULTS, 0), (CLIENT_OPTIONAL_DEFAULTS, 0), (3, {_s11: _s31}), (7, {_s11: 0})),
)

OPERATION_WITH_DEFAULTS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s85,
    {_s64: _s86, _s66: None},
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

RPC_V2_CBOR_NESTED_UNION: StaticSchema = (
    19,
    n1,
    _s87,
    0,
    (_s88,),
    ((3, 0),),
)

RPC_V2_CBOR_UNION: StaticSchema = (
    19,
    n1,
    _s89,
    0,
    (_s88, _s90),
    ((3, 0), (RPC_V2_CBOR_NESTED_UNION, 0)),
)

SPARSE_BOOLEAN_MAP: StaticSchema = (
    17,
    n1,
    _s91,
    64,
    (_s19, _s20),
    ((3, 0), (2, 0)),
)

SPARSE_NUMBER_MAP: StaticSchema = (
    17,
    n1,
    _s92,
    64,
    (_s19, _s20),
    ((3, 0), (7, 0)),
)

SPARSE_SET_MAP: StaticSchema = (
    17,
    n1,
    _s93,
    64,
    (_s19, _s20),
    ((3, 0), (STRING_SET, 0)),
)

SPARSE_STRUCT_MAP: StaticSchema = (
    17,
    n1,
    _s94,
    64,
    (_s19, _s20),
    ((3, 0), (GREETING_STRUCT, 0)),
)

STRUCTURE_LIST_MEMBER: StaticSchema = (
    18,
    n1,
    _s95,
    0,
    (_s96, _s97),
    ((3, 0), (3, 0)),
)

STRUCTURE_LIST: StaticSchema = (
    16,
    n1,
    _s98,
    0,
    (_s4,),
    ((STRUCTURE_LIST_MEMBER, 0),),
)

BLOB_LIST: StaticSchema = (
    16,
    n2,
    _s99,
    0,
    (_s4,),
    ((1, 0),),
)

BOOLEAN_LIST: StaticSchema = (
    16,
    n2,
    _s100,
    0,
    (_s4,),
    ((2, 0),),
)

FOO_ENUM: StaticSchema = (
    14,
    n2,
    _s101,
    0,
    (_s22, _s25, _s24, _s27, _s105),
    (
        (-1, {_s23: _s13}),
        (-1, {_s23: _s102}),
        (-1, {_s23: _s103}),
        (-1, {_s23: _s104}),
        (-1, {_s23: _s106}),
    ),
)

FOO_ENUM_LIST: StaticSchema = (
    16,
    n2,
    _s107,
    0,
    (_s4,),
    ((FOO_ENUM, 0),),
)

INTEGER_ENUM: StaticSchema = (
    15,
    n2,
    _s108,
    0,
    (_s109, _s110, _s111),
    ((-1, {_s23: 1}), (-1, {_s23: 2}), (-1, {_s23: 3})),
)

INTEGER_ENUM_LIST: StaticSchema = (
    16,
    n2,
    _s112,
    0,
    (_s4,),
    ((INTEGER_ENUM, 0),),
)

INTEGER_LIST: StaticSchema = (
    16,
    n2,
    _s113,
    0,
    (_s4,),
    ((7, 0),),
)

STRING_LIST: StaticSchema = (
    16,
    n2,
    _s114,
    0,
    (_s4,),
    ((3, 0),),
)

NESTED_STRING_LIST: StaticSchema = (
    16,
    n2,
    _s115,
    0,
    (_s4,),
    ((STRING_LIST, 0),),
)

SPARSE_STRING_LIST: StaticSchema = (
    16,
    n2,
    _s116,
    64,
    (_s4,),
    ((3, 0),),
)

SPARSE_STRING_MAP: StaticSchema = (
    17,
    n2,
    _s117,
    64,
    (_s19, _s20),
    ((3, 0), (3, 0)),
)

TIMESTAMP_LIST: StaticSchema = (
    16,
    n2,
    _s118,
    0,
    (_s4,),
    ((4, 0),),
)

EMPTY_INPUT_OUTPUT_INPUT: StaticSchema = (
    18,
    n1,
    _s119,
    {_s64: _s120, _s80: None},
)

EMPTY_INPUT_OUTPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s121,
    {_s64: _s120, _s66: None},
)

FLOAT16_INPUT: StaticSchema = (
    18,
    n1,
    _s122,
    {_s64: _s123, _s80: None},
)

FRACTIONAL_SECONDS_INPUT: StaticSchema = (
    18,
    n1,
    _s124,
    {_s64: _s123, _s80: None},
)

GREETING_WITH_ERRORS_INPUT: StaticSchema = (
    18,
    n1,
    _s125,
    {_s64: _s123, _s80: None},
)

NO_INPUT_OUTPUT_INPUT: StaticSchema = (
    18,
    n1,
    _s126,
    {_s64: _s123, _s80: None},
)

NO_INPUT_OUTPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s127,
    {_s64: _s123, _s66: None},
)

OPTIONAL_INPUT_OUTPUT_INPUT: StaticSchema = (
    18,
    n1,
    _s128,
    {_s64: _s129, _s80: None},
    (_s20,),
    ((3, 0),),
)

OPTIONAL_INPUT_OUTPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s130,
    {_s64: _s129, _s66: None},
    (_s20,),
    ((3, 0),),
)

RECURSIVE_SHAPES_INPUT: StaticSchema = (
    18,
    n1,
    _s131,
    {_s64: _s132, _s80: None},
    (_s133,),
    ((lambda: RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED1, 0),),
)

RECURSIVE_SHAPES_OUTPUT: StaticSchema = (
    18,
    n1,
    _s134,
    {_s64: _s132, _s66: None},
    (_s133,),
    ((lambda: RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED1, 0),),
)

RPC_V2_CBOR_DENSE_MAPS_INPUT: StaticSchema = (
    18,
    n1,
    _s135,
    {_s64: _s136, _s80: None},
    (_s137, _s138, _s139, _s140, _s141),
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
    _s142,
    {_s64: _s136, _s66: None},
    (_s137, _s138, _s139, _s140, _s141),
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
    _s143,
    {_s64: _s144, _s80: None},
    (_s145, _s146, _s147, _s148, _s149, _s150, _s151, _s152, _s153, _s154),
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
    _s155,
    {_s64: _s144, _s66: None},
    (_s145, _s146, _s147, _s148, _s149, _s150, _s151, _s152, _s153, _s154),
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
    _s156,
    {_s64: _s157, _s80: None},
    (_s158, _s159, _s160, _s161, _s162),
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
    _s163,
    {_s64: _s157, _s66: None},
    (_s158, _s159, _s160, _s161, _s162),
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
    _s164,
    {_s64: _s165, _s80: None},
    (_s166, _s167),
    ((RPC_V2_CBOR_UNION, 0), (3, 0)),
)

RPC_V2_CBOR_UNIONS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s168,
    {_s64: _s165, _s66: None},
    (_s166, _s167),
    ((RPC_V2_CBOR_UNION, 0), (3, 0)),
)

SIMPLE_SCALAR_PROPERTIES_INPUT: StaticSchema = (
    18,
    n1,
    _s169,
    {_s64: _s170, _s80: None},
    (_s171, _s172, _s173, _s174, _s175, _s176, _s177, _s178, _s88, _s179),
    ((2, 0), (2, 0), (5, 0), (10, 0), (9, 0), (7, 0), (8, 0), (6, 0), (3, 0), (1, 0)),
)

SIMPLE_SCALAR_PROPERTIES_OUTPUT: StaticSchema = (
    18,
    n1,
    _s180,
    {_s64: _s170, _s66: None},
    (_s171, _s172, _s173, _s174, _s175, _s176, _s177, _s178, _s88, _s179),
    ((2, 0), (2, 0), (5, 0), (10, 0), (9, 0), (7, 0), (8, 0), (6, 0), (3, 0), (1, 0)),
)

SPARSE_NULLS_OPERATION_INPUT: StaticSchema = (
    18,
    n1,
    _s181,
    {_s64: _s182, _s80: None},
    (_s183, _s161),
    ((SPARSE_STRING_LIST, 0), (SPARSE_STRING_MAP, 0)),
)

SPARSE_NULLS_OPERATION_OUTPUT: StaticSchema = (
    18,
    n1,
    _s184,
    {_s64: _s182, _s66: None},
    (_s183, _s161),
    ((SPARSE_STRING_LIST, 0), (SPARSE_STRING_MAP, 0)),
)

EMPTY_INPUT_OUTPUT: StaticOperationSchema = (
    23,
    n1,
    _s185,
    0,
    EMPTY_INPUT_OUTPUT_INPUT,
    EMPTY_INPUT_OUTPUT_OUTPUT,
    (),
)

FLOAT16: StaticOperationSchema = (
    23,
    n1,
    _s186,
    0,
    FLOAT16_INPUT,
    FLOAT16_OUTPUT,
    (),
)

FRACTIONAL_SECONDS: StaticOperationSchema = (
    23,
    n1,
    _s187,
    0,
    FRACTIONAL_SECONDS_INPUT,
    FRACTIONAL_SECONDS_OUTPUT,
    (),
)

GREETING_WITH_ERRORS: StaticOperationSchema = (
    23,
    n1,
    _s188,
    0,
    GREETING_WITH_ERRORS_INPUT,
    GREETING_WITH_ERRORS_OUTPUT,
    (COMPLEX_ERROR, INVALID_GREETING),
)

NO_INPUT_OUTPUT: StaticOperationSchema = (
    23,
    n1,
    _s189,
    0,
    NO_INPUT_OUTPUT_INPUT,
    NO_INPUT_OUTPUT_OUTPUT,
    (),
)

OPERATION_WITH_DEFAULTS: StaticOperationSchema = (
    23,
    n1,
    _s190,
    0,
    OPERATION_WITH_DEFAULTS_INPUT,
    OPERATION_WITH_DEFAULTS_OUTPUT,
    (VALIDATION_EXCEPTION,),
)

OPTIONAL_INPUT_OUTPUT: StaticOperationSchema = (
    23,
    n1,
    _s191,
    0,
    OPTIONAL_INPUT_OUTPUT_INPUT,
    OPTIONAL_INPUT_OUTPUT_OUTPUT,
    (),
)

RECURSIVE_SHAPES: StaticOperationSchema = (
    23,
    n1,
    _s192,
    0,
    RECURSIVE_SHAPES_INPUT,
    RECURSIVE_SHAPES_OUTPUT,
    (),
)

RPC_V2_CBOR_DENSE_MAPS: StaticOperationSchema = (
    23,
    n1,
    _s193,
    0,
    RPC_V2_CBOR_DENSE_MAPS_INPUT,
    RPC_V2_CBOR_DENSE_MAPS_OUTPUT,
    (VALIDATION_EXCEPTION,),
)

RPC_V2_CBOR_LISTS: StaticOperationSchema = (
    23,
    n1,
    _s194,
    0,
    RPC_V2_CBOR_LISTS_INPUT,
    RPC_V2_CBOR_LISTS_OUTPUT,
    (VALIDATION_EXCEPTION,),
)

RPC_V2_CBOR_SPARSE_MAPS: StaticOperationSchema = (
    23,
    n1,
    _s195,
    0,
    RPC_V2_CBOR_SPARSE_MAPS_INPUT,
    RPC_V2_CBOR_SPARSE_MAPS_OUTPUT,
    (VALIDATION_EXCEPTION,),
)

RPC_V2_CBOR_UNIONS: StaticOperationSchema = (
    23,
    n1,
    _s196,
    0,
    RPC_V2_CBOR_UNIONS_INPUT,
    RPC_V2_CBOR_UNIONS_OUTPUT,
    (),
)

SIMPLE_SCALAR_PROPERTIES: StaticOperationSchema = (
    23,
    n1,
    _s197,
    0,
    SIMPLE_SCALAR_PROPERTIES_INPUT,
    SIMPLE_SCALAR_PROPERTIES_OUTPUT,
    (),
)

SPARSE_NULLS_OPERATION: StaticOperationSchema = (
    23,
    n1,
    _s198,
    0,
    SPARSE_NULLS_OPERATION_INPUT,
    SPARSE_NULLS_OPERATION_OUTPUT,
    (),
)

RPC_V2_PROTOCOL: StaticSchema = (
    21,
    n1,
    _s199,
    {_s200: None},
)

RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED1: StaticSchema = (
    18,
    n1,
    _s201,
    0,
    (_s202, _s133),
    ((3, 0), (lambda: RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED2, 0)),
)

RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED2: StaticSchema = (
    18,
    n1,
    _s203,
    0,
    (_s204, _s205),
    ((3, 0), (RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED1, 0)),
)
