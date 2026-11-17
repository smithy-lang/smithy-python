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
n1 = "smithy.protocoltests.rpcv2Json"
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
_s63 = "FractionalSecondsOutput"
_s64 = "smithy.synthetic#originalShapeId"
_s65 = "smithy.protocoltests.rpcv2Json#FractionalSecondsOutput"
_s66 = "smithy.api#output"
_s67 = "datetime"
_s68 = "GreetingWithErrorsOutput"
_s69 = "smithy.protocoltests.rpcv2Json#GreetingWithErrorsOutput"
_s70 = "greeting"
_s71 = "InvalidGreeting"
_s72 = "Message"
_s73 = "OperationWithDefaultsInput"
_s74 = "smithy.protocoltests.rpcv2Json#OperationWithDefaultsInput"
_s75 = "smithy.api#input"
_s76 = "defaults"
_s77 = "clientOptionalDefaults"
_s78 = "topLevelDefault"
_s79 = "otherTopLevelDefault"
_s80 = "OperationWithDefaultsOutput"
_s81 = "smithy.protocoltests.rpcv2Json#OperationWithDefaultsOutput"
_s82 = "SparseBooleanMap"
_s83 = "SparseNumberMap"
_s84 = "SparseSetMap"
_s85 = "SparseStructMap"
_s86 = "StructureListMember"
_s87 = "a"
_s88 = "b"
_s89 = "StructureList"
_s90 = "BlobList"
_s91 = "BooleanList"
_s92 = "DateTime"
_s93 = "smithy.api#timestampFormat"
_s94 = "date-time"
_s95 = "EpochSeconds"
_s96 = "epoch-seconds"
_s97 = "FooEnum"
_s98 = "Baz"
_s99 = "Bar"
_s100 = "1"
_s101 = "ZERO"
_s102 = "0"
_s103 = "FooEnumList"
_s104 = "HttpDate"
_s105 = "http-date"
_s106 = "IntegerEnum"
_s107 = "A"
_s108 = "B"
_s109 = "C"
_s110 = "IntegerEnumList"
_s111 = "IntegerList"
_s112 = "StringList"
_s113 = "NestedStringList"
_s114 = "SparseStringList"
_s115 = "SparseStringMap"
_s116 = "TimestampList"
_s117 = "BigDecimalOperationInput"
_s118 = "smithy.protocoltests.rpcv2Json#BigDecimalStructure"
_s119 = "BigDecimalOperationOutput"
_s120 = "BigIntegerOperationInput"
_s121 = "smithy.protocoltests.rpcv2Json#BigIntegerStructure"
_s122 = "BigIntegerOperationOutput"
_s123 = "EmptyInputOutputInput"
_s124 = "smithy.protocoltests.rpcv2Json#EmptyStructure"
_s125 = "EmptyInputOutputOutput"
_s126 = "FractionalSecondsInput"
_s127 = "smithy.api#Unit"
_s128 = "GreetingWithErrorsInput"
_s129 = "NoInputOutputInput"
_s130 = "NoInputOutputOutput"
_s131 = "OptionalInputOutputInput"
_s132 = "smithy.protocoltests.rpcv2Json#SimpleStructure"
_s133 = "OptionalInputOutputOutput"
_s134 = "RecursiveShapesInput"
_s135 = "smithy.protocoltests.rpcv2Json#RecursiveShapesInputOutput"
_s136 = "nested"
_s137 = "RecursiveShapesOutput"
_s138 = "RpcV2JsonDenseMapsInput"
_s139 = "smithy.protocoltests.rpcv2Json#RpcV2JsonDenseMapsInputOutput"
_s140 = "denseStructMap"
_s141 = "denseNumberMap"
_s142 = "denseBooleanMap"
_s143 = "denseStringMap"
_s144 = "denseSetMap"
_s145 = "RpcV2JsonDenseMapsOutput"
_s146 = "RpcV2JsonListsInput"
_s147 = "smithy.protocoltests.rpcv2Json#RpcV2JsonListInputOutput"
_s148 = "stringList"
_s149 = "stringSet"
_s150 = "integerList"
_s151 = "booleanList"
_s152 = "timestampList"
_s153 = "enumList"
_s154 = "intEnumList"
_s155 = "nestedStringList"
_s156 = "structureList"
_s157 = "blobList"
_s158 = "RpcV2JsonListsOutput"
_s159 = "RpcV2JsonSparseMapsInput"
_s160 = "smithy.protocoltests.rpcv2Json#RpcV2JsonSparseMapsInputOutput"
_s161 = "sparseStructMap"
_s162 = "sparseNumberMap"
_s163 = "sparseBooleanMap"
_s164 = "sparseStringMap"
_s165 = "sparseSetMap"
_s166 = "RpcV2JsonSparseMapsOutput"
_s167 = "SimpleScalarPropertiesInput"
_s168 = "smithy.protocoltests.rpcv2Json#SimpleScalarStructure"
_s169 = "trueBooleanValue"
_s170 = "falseBooleanValue"
_s171 = "byteValue"
_s172 = "doubleValue"
_s173 = "floatValue"
_s174 = "integerValue"
_s175 = "longValue"
_s176 = "shortValue"
_s177 = "stringValue"
_s178 = "blobValue"
_s179 = "SimpleScalarPropertiesOutput"
_s180 = "SparseNullsOperationInput"
_s181 = "smithy.protocoltests.rpcv2Json#SparseNullsOperationInputOutput"
_s182 = "sparseStringList"
_s183 = "SparseNullsOperationOutput"
_s184 = "TimestampFormatIgnoredInput"
_s185 = "smithy.protocoltests.rpcv2Json#TimestampFormatIgnoredIO"
_s186 = "dateTime"
_s187 = "httpDate"
_s188 = "epochSeconds"
_s189 = "normal"
_s190 = "TimestampFormatIgnoredOutput"
_s191 = "BigDecimalOperation"
_s192 = "BigIntegerOperation"
_s193 = "EmptyInputOutput"
_s194 = "FractionalSeconds"
_s195 = "GreetingWithErrors"
_s196 = "NoInputOutput"
_s197 = "OperationWithDefaults"
_s198 = "OptionalInputOutput"
_s199 = "RecursiveShapes"
_s200 = "RpcV2JsonDenseMaps"
_s201 = "RpcV2JsonLists"
_s202 = "RpcV2JsonSparseMaps"
_s203 = "SimpleScalarProperties"
_s204 = "SparseNullsOperation"
_s205 = "TimestampFormatIgnored"
_s206 = "RpcV2JsonProtocol"
_s207 = "smithy.protocols#rpcv2Json"
_s208 = "RecursiveShapesInputOutputNested1"
_s209 = "foo"
_s210 = "RecursiveShapesInputOutputNested2"
_s211 = "bar"
_s212 = "recursiveMember"

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

FRACTIONAL_SECONDS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s63,
    {_s64: _s65, _s66: None},
    (_s67,),
    ((4, 0),),
)

GREETING_WITH_ERRORS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s68,
    {_s64: _s69, _s66: None},
    (_s70,),
    ((3, 0),),
)

INVALID_GREETING: StaticSchema = (
    18,
    n1,
    _s71,
    {_s6: _s7},
    (_s72,),
    ((3, 0),),
)

OPERATION_WITH_DEFAULTS_INPUT: StaticSchema = (
    18,
    n1,
    _s73,
    {_s64: _s74, _s75: None},
    (_s76, _s77, _s78, _s79),
    ((DEFAULTS, 0), (CLIENT_OPTIONAL_DEFAULTS, 0), (3, {_s11: _s31}), (7, {_s11: 0})),
)

OPERATION_WITH_DEFAULTS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s80,
    {_s64: _s81, _s66: None},
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

SPARSE_BOOLEAN_MAP: StaticSchema = (
    17,
    n1,
    _s82,
    64,
    (_s19, _s20),
    ((3, 0), (2, 0)),
)

SPARSE_NUMBER_MAP: StaticSchema = (
    17,
    n1,
    _s83,
    64,
    (_s19, _s20),
    ((3, 0), (7, 0)),
)

SPARSE_SET_MAP: StaticSchema = (
    17,
    n1,
    _s84,
    64,
    (_s19, _s20),
    ((3, 0), (STRING_SET, 0)),
)

SPARSE_STRUCT_MAP: StaticSchema = (
    17,
    n1,
    _s85,
    64,
    (_s19, _s20),
    ((3, 0), (GREETING_STRUCT, 0)),
)

STRUCTURE_LIST_MEMBER: StaticSchema = (
    18,
    n1,
    _s86,
    0,
    (_s87, _s88),
    ((3, 0), (3, 0)),
)

STRUCTURE_LIST: StaticSchema = (
    16,
    n1,
    _s89,
    0,
    (_s4,),
    ((STRUCTURE_LIST_MEMBER, 0),),
)

BLOB_LIST: StaticSchema = (
    16,
    n2,
    _s90,
    0,
    (_s4,),
    ((1, 0),),
)

BOOLEAN_LIST: StaticSchema = (
    16,
    n2,
    _s91,
    0,
    (_s4,),
    ((2, 0),),
)

DATE_TIME: StaticSchema = (
    4,
    n2,
    _s92,
    {_s93: _s94},
)

EPOCH_SECONDS: StaticSchema = (
    4,
    n2,
    _s95,
    {_s93: _s96},
)

FOO_ENUM: StaticSchema = (
    14,
    n2,
    _s97,
    0,
    (_s22, _s25, _s24, _s27, _s101),
    (
        (-1, {_s23: _s13}),
        (-1, {_s23: _s98}),
        (-1, {_s23: _s99}),
        (-1, {_s23: _s100}),
        (-1, {_s23: _s102}),
    ),
)

FOO_ENUM_LIST: StaticSchema = (
    16,
    n2,
    _s103,
    0,
    (_s4,),
    ((FOO_ENUM, 0),),
)

HTTP_DATE: StaticSchema = (
    4,
    n2,
    _s104,
    {_s93: _s105},
)

INTEGER_ENUM: StaticSchema = (
    15,
    n2,
    _s106,
    0,
    (_s107, _s108, _s109),
    ((-1, {_s23: 1}), (-1, {_s23: 2}), (-1, {_s23: 3})),
)

INTEGER_ENUM_LIST: StaticSchema = (
    16,
    n2,
    _s110,
    0,
    (_s4,),
    ((INTEGER_ENUM, 0),),
)

INTEGER_LIST: StaticSchema = (
    16,
    n2,
    _s111,
    0,
    (_s4,),
    ((7, 0),),
)

STRING_LIST: StaticSchema = (
    16,
    n2,
    _s112,
    0,
    (_s4,),
    ((3, 0),),
)

NESTED_STRING_LIST: StaticSchema = (
    16,
    n2,
    _s113,
    0,
    (_s4,),
    ((STRING_LIST, 0),),
)

SPARSE_STRING_LIST: StaticSchema = (
    16,
    n2,
    _s114,
    64,
    (_s4,),
    ((3, 0),),
)

SPARSE_STRING_MAP: StaticSchema = (
    17,
    n2,
    _s115,
    64,
    (_s19, _s20),
    ((3, 0), (3, 0)),
)

TIMESTAMP_LIST: StaticSchema = (
    16,
    n2,
    _s116,
    0,
    (_s4,),
    ((4, 0),),
)

BIG_DECIMAL_OPERATION_INPUT: StaticSchema = (
    18,
    n1,
    _s117,
    {_s64: _s118, _s75: None},
    (_s20,),
    ((12, 0),),
)

BIG_DECIMAL_OPERATION_OUTPUT: StaticSchema = (
    18,
    n1,
    _s119,
    {_s64: _s118, _s66: None},
    (_s20,),
    ((12, 0),),
)

BIG_INTEGER_OPERATION_INPUT: StaticSchema = (
    18,
    n1,
    _s120,
    {_s64: _s121, _s75: None},
    (_s20,),
    ((11, 0),),
)

BIG_INTEGER_OPERATION_OUTPUT: StaticSchema = (
    18,
    n1,
    _s122,
    {_s64: _s121, _s66: None},
    (_s20,),
    ((11, 0),),
)

EMPTY_INPUT_OUTPUT_INPUT: StaticSchema = (
    18,
    n1,
    _s123,
    {_s64: _s124, _s75: None},
)

EMPTY_INPUT_OUTPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s125,
    {_s64: _s124, _s66: None},
)

FRACTIONAL_SECONDS_INPUT: StaticSchema = (
    18,
    n1,
    _s126,
    {_s64: _s127, _s75: None},
)

GREETING_WITH_ERRORS_INPUT: StaticSchema = (
    18,
    n1,
    _s128,
    {_s64: _s127, _s75: None},
)

NO_INPUT_OUTPUT_INPUT: StaticSchema = (
    18,
    n1,
    _s129,
    {_s64: _s127, _s75: None},
)

NO_INPUT_OUTPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s130,
    {_s64: _s127, _s66: None},
)

OPTIONAL_INPUT_OUTPUT_INPUT: StaticSchema = (
    18,
    n1,
    _s131,
    {_s64: _s132, _s75: None},
    (_s20,),
    ((3, 0),),
)

OPTIONAL_INPUT_OUTPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s133,
    {_s64: _s132, _s66: None},
    (_s20,),
    ((3, 0),),
)

RECURSIVE_SHAPES_INPUT: StaticSchema = (
    18,
    n1,
    _s134,
    {_s64: _s135, _s75: None},
    (_s136,),
    ((lambda: RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED1, 0),),
)

RECURSIVE_SHAPES_OUTPUT: StaticSchema = (
    18,
    n1,
    _s137,
    {_s64: _s135, _s66: None},
    (_s136,),
    ((lambda: RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED1, 0),),
)

RPC_V2_JSON_DENSE_MAPS_INPUT: StaticSchema = (
    18,
    n1,
    _s138,
    {_s64: _s139, _s75: None},
    (_s140, _s141, _s142, _s143, _s144),
    (
        (DENSE_STRUCT_MAP, 0),
        (DENSE_NUMBER_MAP, 0),
        (DENSE_BOOLEAN_MAP, 0),
        (DENSE_STRING_MAP, 0),
        (DENSE_SET_MAP, 0),
    ),
)

RPC_V2_JSON_DENSE_MAPS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s145,
    {_s64: _s139, _s66: None},
    (_s140, _s141, _s142, _s143, _s144),
    (
        (DENSE_STRUCT_MAP, 0),
        (DENSE_NUMBER_MAP, 0),
        (DENSE_BOOLEAN_MAP, 0),
        (DENSE_STRING_MAP, 0),
        (DENSE_SET_MAP, 0),
    ),
)

RPC_V2_JSON_LISTS_INPUT: StaticSchema = (
    18,
    n1,
    _s146,
    {_s64: _s147, _s75: None},
    (_s148, _s149, _s150, _s151, _s152, _s153, _s154, _s155, _s156, _s157),
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

RPC_V2_JSON_LISTS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s158,
    {_s64: _s147, _s66: None},
    (_s148, _s149, _s150, _s151, _s152, _s153, _s154, _s155, _s156, _s157),
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

RPC_V2_JSON_SPARSE_MAPS_INPUT: StaticSchema = (
    18,
    n1,
    _s159,
    {_s64: _s160, _s75: None},
    (_s161, _s162, _s163, _s164, _s165),
    (
        (SPARSE_STRUCT_MAP, 0),
        (SPARSE_NUMBER_MAP, 0),
        (SPARSE_BOOLEAN_MAP, 0),
        (SPARSE_STRING_MAP, 0),
        (SPARSE_SET_MAP, 0),
    ),
)

RPC_V2_JSON_SPARSE_MAPS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s166,
    {_s64: _s160, _s66: None},
    (_s161, _s162, _s163, _s164, _s165),
    (
        (SPARSE_STRUCT_MAP, 0),
        (SPARSE_NUMBER_MAP, 0),
        (SPARSE_BOOLEAN_MAP, 0),
        (SPARSE_STRING_MAP, 0),
        (SPARSE_SET_MAP, 0),
    ),
)

SIMPLE_SCALAR_PROPERTIES_INPUT: StaticSchema = (
    18,
    n1,
    _s167,
    {_s64: _s168, _s75: None},
    (_s169, _s170, _s171, _s172, _s173, _s174, _s175, _s176, _s177, _s178),
    ((2, 0), (2, 0), (5, 0), (10, 0), (9, 0), (7, 0), (8, 0), (6, 0), (3, 0), (1, 0)),
)

SIMPLE_SCALAR_PROPERTIES_OUTPUT: StaticSchema = (
    18,
    n1,
    _s179,
    {_s64: _s168, _s66: None},
    (_s169, _s170, _s171, _s172, _s173, _s174, _s175, _s176, _s177, _s178),
    ((2, 0), (2, 0), (5, 0), (10, 0), (9, 0), (7, 0), (8, 0), (6, 0), (3, 0), (1, 0)),
)

SPARSE_NULLS_OPERATION_INPUT: StaticSchema = (
    18,
    n1,
    _s180,
    {_s64: _s181, _s75: None},
    (_s182, _s164),
    ((SPARSE_STRING_LIST, 0), (SPARSE_STRING_MAP, 0)),
)

SPARSE_NULLS_OPERATION_OUTPUT: StaticSchema = (
    18,
    n1,
    _s183,
    {_s64: _s181, _s66: None},
    (_s182, _s164),
    ((SPARSE_STRING_LIST, 0), (SPARSE_STRING_MAP, 0)),
)

TIMESTAMP_FORMAT_IGNORED_INPUT: StaticSchema = (
    18,
    n1,
    _s184,
    {_s64: _s185, _s75: None},
    (_s186, _s187, _s188, _s189),
    ((DATE_TIME, 0), (HTTP_DATE, 0), (EPOCH_SECONDS, 0), (4, 0)),
)

TIMESTAMP_FORMAT_IGNORED_OUTPUT: StaticSchema = (
    18,
    n1,
    _s190,
    {_s64: _s185, _s66: None},
    (_s186, _s187, _s188, _s189),
    ((DATE_TIME, 0), (HTTP_DATE, 0), (EPOCH_SECONDS, 0), (4, 0)),
)

BIG_DECIMAL_OPERATION: StaticOperationSchema = (
    23,
    n1,
    _s191,
    0,
    BIG_DECIMAL_OPERATION_INPUT,
    BIG_DECIMAL_OPERATION_OUTPUT,
    (),
)

BIG_INTEGER_OPERATION: StaticOperationSchema = (
    23,
    n1,
    _s192,
    0,
    BIG_INTEGER_OPERATION_INPUT,
    BIG_INTEGER_OPERATION_OUTPUT,
    (),
)

EMPTY_INPUT_OUTPUT: StaticOperationSchema = (
    23,
    n1,
    _s193,
    0,
    EMPTY_INPUT_OUTPUT_INPUT,
    EMPTY_INPUT_OUTPUT_OUTPUT,
    (),
)

FRACTIONAL_SECONDS: StaticOperationSchema = (
    23,
    n1,
    _s194,
    0,
    FRACTIONAL_SECONDS_INPUT,
    FRACTIONAL_SECONDS_OUTPUT,
    (),
)

GREETING_WITH_ERRORS: StaticOperationSchema = (
    23,
    n1,
    _s195,
    0,
    GREETING_WITH_ERRORS_INPUT,
    GREETING_WITH_ERRORS_OUTPUT,
    (COMPLEX_ERROR, INVALID_GREETING),
)

NO_INPUT_OUTPUT: StaticOperationSchema = (
    23,
    n1,
    _s196,
    0,
    NO_INPUT_OUTPUT_INPUT,
    NO_INPUT_OUTPUT_OUTPUT,
    (),
)

OPERATION_WITH_DEFAULTS: StaticOperationSchema = (
    23,
    n1,
    _s197,
    0,
    OPERATION_WITH_DEFAULTS_INPUT,
    OPERATION_WITH_DEFAULTS_OUTPUT,
    (VALIDATION_EXCEPTION,),
)

OPTIONAL_INPUT_OUTPUT: StaticOperationSchema = (
    23,
    n1,
    _s198,
    0,
    OPTIONAL_INPUT_OUTPUT_INPUT,
    OPTIONAL_INPUT_OUTPUT_OUTPUT,
    (),
)

RECURSIVE_SHAPES: StaticOperationSchema = (
    23,
    n1,
    _s199,
    0,
    RECURSIVE_SHAPES_INPUT,
    RECURSIVE_SHAPES_OUTPUT,
    (),
)

RPC_V2_JSON_DENSE_MAPS: StaticOperationSchema = (
    23,
    n1,
    _s200,
    0,
    RPC_V2_JSON_DENSE_MAPS_INPUT,
    RPC_V2_JSON_DENSE_MAPS_OUTPUT,
    (VALIDATION_EXCEPTION,),
)

RPC_V2_JSON_LISTS: StaticOperationSchema = (
    23,
    n1,
    _s201,
    0,
    RPC_V2_JSON_LISTS_INPUT,
    RPC_V2_JSON_LISTS_OUTPUT,
    (VALIDATION_EXCEPTION,),
)

RPC_V2_JSON_SPARSE_MAPS: StaticOperationSchema = (
    23,
    n1,
    _s202,
    0,
    RPC_V2_JSON_SPARSE_MAPS_INPUT,
    RPC_V2_JSON_SPARSE_MAPS_OUTPUT,
    (VALIDATION_EXCEPTION,),
)

SIMPLE_SCALAR_PROPERTIES: StaticOperationSchema = (
    23,
    n1,
    _s203,
    0,
    SIMPLE_SCALAR_PROPERTIES_INPUT,
    SIMPLE_SCALAR_PROPERTIES_OUTPUT,
    (),
)

SPARSE_NULLS_OPERATION: StaticOperationSchema = (
    23,
    n1,
    _s204,
    0,
    SPARSE_NULLS_OPERATION_INPUT,
    SPARSE_NULLS_OPERATION_OUTPUT,
    (),
)

TIMESTAMP_FORMAT_IGNORED: StaticOperationSchema = (
    23,
    n1,
    _s205,
    0,
    TIMESTAMP_FORMAT_IGNORED_INPUT,
    TIMESTAMP_FORMAT_IGNORED_OUTPUT,
    (),
)

RPC_V2_JSON_PROTOCOL: StaticSchema = (
    21,
    n1,
    _s206,
    {_s207: None},
)

RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED1: StaticSchema = (
    18,
    n1,
    _s208,
    0,
    (_s209, _s136),
    ((3, 0), (lambda: RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED2, 0)),
)

RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED2: StaticSchema = (
    18,
    n1,
    _s210,
    0,
    (_s211, _s212),
    ((3, 0), (RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED1, 0)),
)
