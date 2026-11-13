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
n1 = "smithy.protocoltests.rpcv2Json"
_s9 = "BigDecimalStructure"
_s10 = "smithy.api#input"
_s11 = "smithy.api#output"
_s12 = "value"
_s13 = "BigIntegerStructure"
_s14 = "ClientOptionalDefaults"
_s15 = "smithy.api#default"
_s16 = "ComplexNestedErrorData"
_s17 = "Foo"
_s18 = "ComplexError"
_s19 = "TopLevel"
_s20 = "Nested"
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
_s37 = "defaultTimestamp"
_s38 = "defaultBlob"
_s39 = "YWJj"
_s40 = "defaultByte"
_s41 = "defaultShort"
_s42 = "defaultInteger"
_s43 = "defaultLong"
_s44 = "defaultFloat"
_s45 = "defaultDouble"
_s46 = "defaultMap"
_s47 = "defaultEnum"
_s48 = "defaultIntEnum"
_s49 = "emptyString"
_s50 = ""
_s51 = "falseBoolean"
_s52 = "emptyBlob"
_s53 = "zeroByte"
_s54 = "zeroShort"
_s55 = "zeroInteger"
_s56 = "zeroLong"
_s57 = "zeroFloat"
_s58 = "zeroDouble"
_s59 = "DenseBooleanMap"
_s60 = "DenseNumberMap"
n2 = "smithy.protocoltests.shared"
_s61 = "StringSet"
_s62 = "DenseSetMap"
_s63 = "DenseStringMap"
_s64 = "GreetingStruct"
_s65 = "DenseStructMap"
_s66 = "EmptyStructure"
_s67 = "FractionalSecondsOutput"
_s68 = "datetime"
_s69 = "GreetingWithErrorsOutput"
_s70 = "greeting"
_s71 = "InvalidGreeting"
_s72 = "Message"
_s73 = "OperationWithDefaultsInput"
_s74 = "defaults"
_s75 = "clientOptionalDefaults"
_s76 = "topLevelDefault"
_s77 = "otherTopLevelDefault"
_s78 = "OperationWithDefaultsOutput"
_s79 = "RecursiveShapesInputOutput"
_s80 = "nested"
_s81 = "RpcV2JsonDenseMapsInputOutput"
_s82 = "denseStructMap"
_s83 = "denseNumberMap"
_s84 = "denseBooleanMap"
_s85 = "denseStringMap"
_s86 = "denseSetMap"
_s87 = "StringList"
_s88 = "IntegerList"
_s89 = "BooleanList"
_s90 = "TimestampList"
_s91 = "FooEnum"
_s92 = "Baz"
_s93 = "Bar"
_s94 = "1"
_s95 = "ZERO"
_s96 = "0"
_s97 = "FooEnumList"
_s98 = "IntegerEnum"
_s99 = "A"
_s100 = "B"
_s101 = "C"
_s102 = "IntegerEnumList"
_s103 = "NestedStringList"
_s104 = "StructureListMember"
_s105 = "a"
_s106 = "b"
_s107 = "StructureList"
_s108 = "BlobList"
_s109 = "RpcV2JsonListInputOutput"
_s110 = "stringList"
_s111 = "stringSet"
_s112 = "integerList"
_s113 = "booleanList"
_s114 = "timestampList"
_s115 = "enumList"
_s116 = "intEnumList"
_s117 = "nestedStringList"
_s118 = "structureList"
_s119 = "blobList"
_s120 = "SparseStructMap"
_s121 = "SparseNumberMap"
_s122 = "SparseBooleanMap"
_s123 = "SparseStringMap"
_s124 = "SparseSetMap"
_s125 = "RpcV2JsonSparseMapsInputOutput"
_s126 = "sparseStructMap"
_s127 = "sparseNumberMap"
_s128 = "sparseBooleanMap"
_s129 = "sparseStringMap"
_s130 = "sparseSetMap"
_s131 = "SimpleScalarStructure"
_s132 = "trueBooleanValue"
_s133 = "falseBooleanValue"
_s134 = "byteValue"
_s135 = "doubleValue"
_s136 = "floatValue"
_s137 = "integerValue"
_s138 = "longValue"
_s139 = "shortValue"
_s140 = "stringValue"
_s141 = "blobValue"
_s142 = "SimpleStructure"
_s143 = "SparseStringList"
_s144 = "SparseNullsOperationInputOutput"
_s145 = "sparseStringList"
_s146 = "DateTime"
_s147 = "smithy.api#timestampFormat"
_s148 = "date-time"
_s149 = "HttpDate"
_s150 = "http-date"
_s151 = "EpochSeconds"
_s152 = "epoch-seconds"
_s153 = "TimestampFormatIgnoredIO"
_s154 = "dateTime"
_s155 = "httpDate"
_s156 = "epochSeconds"
_s157 = "normal"
_s158 = "RecursiveShapesInputOutputNested1"
_s159 = "foo"
_s160 = "RecursiveShapesInputOutputNested2"
_s161 = "bar"
_s162 = "recursiveMember"

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

BIG_DECIMAL_STRUCTURE: StaticSchema = (
    18,
    n1,
    _s9,
    {_s10: None, _s11: None},
    (_s12,),
    ((12, 0),),
)

BIG_INTEGER_STRUCTURE: StaticSchema = (
    18,
    n1,
    _s13,
    {_s10: None, _s11: None},
    (_s12,),
    ((11, 0),),
)

CLIENT_OPTIONAL_DEFAULTS: StaticSchema = (
    18,
    n1,
    _s14,
    0,
    (_s4,),
    ((7, {_s15: 0}),),
)

COMPLEX_NESTED_ERROR_DATA: StaticSchema = (
    18,
    n1,
    _s16,
    0,
    (_s17,),
    ((3, 0),),
)

COMPLEX_ERROR: StaticSchema = (
    18,
    n1,
    _s18,
    {_s6: _s7},
    (
        _s19,
        _s20,
    ),
    (
        (3, 0),
        (COMPLEX_NESTED_ERROR_DATA, 0),
    ),
)

TEST_STRING_LIST: StaticSchema = (
    16,
    n1,
    _s21,
    0,
    (_s4,),
    ((3, 0),),
)

TEST_STRING_MAP: StaticSchema = (
    17,
    n1,
    _s22,
    0,
    (
        _s23,
        _s12,
    ),
    (
        (3, 0),
        (3, 0),
    ),
)

TEST_ENUM: StaticSchema = (
    14,
    n1,
    _s24,
    0,
    (
        _s25,
        _s27,
        _s28,
    ),
    (
        (-1, {_s26: _s25}),
        (-1, {_s26: _s27}),
        (-1, {_s26: _s28}),
    ),
)

TEST_INT_ENUM: StaticSchema = (
    15,
    n1,
    _s29,
    0,
    (
        _s30,
        _s31,
    ),
    (
        (-1, {_s26: 1}),
        (-1, {_s26: 2}),
    ),
)

DEFAULTS: StaticSchema = (
    18,
    n1,
    _s32,
    0,
    (
        _s33,
        _s35,
        _s36,
        _s37,
        _s38,
        _s40,
        _s41,
        _s42,
        _s43,
        _s44,
        _s45,
        _s46,
        _s47,
        _s48,
        _s49,
        _s51,
        _s52,
        _s53,
        _s54,
        _s55,
        _s56,
        _s57,
        _s58,
    ),
    (
        (3, {_s15: _s34}),
        (2, {_s15: True}),
        (TEST_STRING_LIST, {_s15: ()}),
        (4, {_s15: 0}),
        (1, {_s15: _s39}),
        (5, {_s15: 1}),
        (6, {_s15: 1}),
        (7, {_s15: 10}),
        (8, {_s15: 100}),
        (9, {_s15: 1.0}),
        (10, {_s15: 1.0}),
        (TEST_STRING_MAP, {_s15: MappingProxyType[str, object]({})}),
        (TEST_ENUM, {_s15: _s25}),
        (TEST_INT_ENUM, {_s15: 1}),
        (3, {_s15: _s50}),
        (2, {_s15: False}),
        (1, {_s15: _s50}),
        (5, {_s15: 0}),
        (6, {_s15: 0}),
        (7, {_s15: 0}),
        (8, {_s15: 0}),
        (9, {_s15: 0.0}),
        (10, {_s15: 0.0}),
    ),
)

DENSE_BOOLEAN_MAP: StaticSchema = (
    17,
    n1,
    _s59,
    0,
    (
        _s23,
        _s12,
    ),
    (
        (3, 0),
        (2, 0),
    ),
)

DENSE_NUMBER_MAP: StaticSchema = (
    17,
    n1,
    _s60,
    0,
    (
        _s23,
        _s12,
    ),
    (
        (3, 0),
        (7, 0),
    ),
)

STRING_SET: StaticSchema = (
    16,
    n2,
    _s61,
    0,
    (_s4,),
    ((3, 0),),
)

DENSE_SET_MAP: StaticSchema = (
    17,
    n1,
    _s62,
    0,
    (
        _s23,
        _s12,
    ),
    (
        (3, 0),
        (STRING_SET, 0),
    ),
)

DENSE_STRING_MAP: StaticSchema = (
    17,
    n1,
    _s63,
    0,
    (
        _s23,
        _s12,
    ),
    (
        (3, 0),
        (3, 0),
    ),
)

GREETING_STRUCT: StaticSchema = (
    18,
    n2,
    _s64,
    0,
    (_s34,),
    ((3, 0),),
)

DENSE_STRUCT_MAP: StaticSchema = (
    17,
    n1,
    _s65,
    0,
    (
        _s23,
        _s12,
    ),
    (
        (3, 0),
        (GREETING_STRUCT, 0),
    ),
)

EMPTY_STRUCTURE: StaticSchema = (
    18,
    n1,
    _s66,
    {_s10: None, _s11: None},
)

FRACTIONAL_SECONDS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s67,
    {_s11: None},
    (_s68,),
    ((4, 0),),
)

GREETING_WITH_ERRORS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s69,
    {_s11: None},
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
    {_s10: None},
    (
        _s74,
        _s75,
        _s76,
        _s77,
    ),
    (
        (DEFAULTS, 0),
        (CLIENT_OPTIONAL_DEFAULTS, 0),
        (3, {_s15: _s34}),
        (7, {_s15: 0}),
    ),
)

OPERATION_WITH_DEFAULTS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s78,
    {_s11: None},
    (
        _s33,
        _s35,
        _s36,
        _s37,
        _s38,
        _s40,
        _s41,
        _s42,
        _s43,
        _s44,
        _s45,
        _s46,
        _s47,
        _s48,
        _s49,
        _s51,
        _s52,
        _s53,
        _s54,
        _s55,
        _s56,
        _s57,
        _s58,
    ),
    (
        (3, {_s15: _s34}),
        (2, {_s15: True}),
        (TEST_STRING_LIST, {_s15: ()}),
        (4, {_s15: 0}),
        (1, {_s15: _s39}),
        (5, {_s15: 1}),
        (6, {_s15: 1}),
        (7, {_s15: 10}),
        (8, {_s15: 100}),
        (9, {_s15: 1.0}),
        (10, {_s15: 1.0}),
        (TEST_STRING_MAP, {_s15: MappingProxyType[str, object]({})}),
        (TEST_ENUM, {_s15: _s25}),
        (TEST_INT_ENUM, {_s15: 1}),
        (3, {_s15: _s50}),
        (2, {_s15: False}),
        (1, {_s15: _s50}),
        (5, {_s15: 0}),
        (6, {_s15: 0}),
        (7, {_s15: 0}),
        (8, {_s15: 0}),
        (9, {_s15: 0.0}),
        (10, {_s15: 0.0}),
    ),
)

RECURSIVE_SHAPES_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s79,
    {_s10: None, _s11: None},
    (_s80,),
    ((lambda: RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED1, 0),),
)

RPC_V2_JSON_DENSE_MAPS_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s81,
    {_s10: None, _s11: None},
    (
        _s82,
        _s83,
        _s84,
        _s85,
        _s86,
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
    _s87,
    0,
    (_s4,),
    ((3, 0),),
)

INTEGER_LIST: StaticSchema = (
    16,
    n2,
    _s88,
    0,
    (_s4,),
    ((7, 0),),
)

BOOLEAN_LIST: StaticSchema = (
    16,
    n2,
    _s89,
    0,
    (_s4,),
    ((2, 0),),
)

TIMESTAMP_LIST: StaticSchema = (
    16,
    n2,
    _s90,
    0,
    (_s4,),
    ((4, 0),),
)

FOO_ENUM: StaticSchema = (
    14,
    n2,
    _s91,
    0,
    (
        _s25,
        _s28,
        _s27,
        _s30,
        _s95,
    ),
    (
        (-1, {_s26: _s17}),
        (-1, {_s26: _s92}),
        (-1, {_s26: _s93}),
        (-1, {_s26: _s94}),
        (-1, {_s26: _s96}),
    ),
)

FOO_ENUM_LIST: StaticSchema = (
    16,
    n2,
    _s97,
    0,
    (_s4,),
    ((FOO_ENUM, 0),),
)

INTEGER_ENUM: StaticSchema = (
    15,
    n2,
    _s98,
    0,
    (
        _s99,
        _s100,
        _s101,
    ),
    (
        (-1, {_s26: 1}),
        (-1, {_s26: 2}),
        (-1, {_s26: 3}),
    ),
)

INTEGER_ENUM_LIST: StaticSchema = (
    16,
    n2,
    _s102,
    0,
    (_s4,),
    ((INTEGER_ENUM, 0),),
)

NESTED_STRING_LIST: StaticSchema = (
    16,
    n2,
    _s103,
    0,
    (_s4,),
    ((STRING_LIST, 0),),
)

STRUCTURE_LIST_MEMBER: StaticSchema = (
    18,
    n1,
    _s104,
    0,
    (
        _s105,
        _s106,
    ),
    (
        (3, 0),
        (3, 0),
    ),
)

STRUCTURE_LIST: StaticSchema = (
    16,
    n1,
    _s107,
    0,
    (_s4,),
    ((STRUCTURE_LIST_MEMBER, 0),),
)

BLOB_LIST: StaticSchema = (
    16,
    n2,
    _s108,
    0,
    (_s4,),
    ((1, 0),),
)

RPC_V2_JSON_LIST_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s109,
    {_s10: None, _s11: None},
    (
        _s110,
        _s111,
        _s112,
        _s113,
        _s114,
        _s115,
        _s116,
        _s117,
        _s118,
        _s119,
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

SPARSE_STRUCT_MAP: StaticSchema = (
    17,
    n1,
    _s120,
    64,
    (
        _s23,
        _s12,
    ),
    (
        (3, 0),
        (GREETING_STRUCT, 0),
    ),
)

SPARSE_NUMBER_MAP: StaticSchema = (
    17,
    n1,
    _s121,
    64,
    (
        _s23,
        _s12,
    ),
    (
        (3, 0),
        (7, 0),
    ),
)

SPARSE_BOOLEAN_MAP: StaticSchema = (
    17,
    n1,
    _s122,
    64,
    (
        _s23,
        _s12,
    ),
    (
        (3, 0),
        (2, 0),
    ),
)

SPARSE_STRING_MAP: StaticSchema = (
    17,
    n2,
    _s123,
    64,
    (
        _s23,
        _s12,
    ),
    (
        (3, 0),
        (3, 0),
    ),
)

SPARSE_SET_MAP: StaticSchema = (
    17,
    n1,
    _s124,
    64,
    (
        _s23,
        _s12,
    ),
    (
        (3, 0),
        (STRING_SET, 0),
    ),
)

RPC_V2_JSON_SPARSE_MAPS_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s125,
    {_s10: None, _s11: None},
    (
        _s126,
        _s127,
        _s128,
        _s129,
        _s130,
    ),
    (
        (SPARSE_STRUCT_MAP, 0),
        (SPARSE_NUMBER_MAP, 0),
        (SPARSE_BOOLEAN_MAP, 0),
        (SPARSE_STRING_MAP, 0),
        (SPARSE_SET_MAP, 0),
    ),
)

SIMPLE_SCALAR_STRUCTURE: StaticSchema = (
    18,
    n1,
    _s131,
    {_s10: None, _s11: None},
    (
        _s132,
        _s133,
        _s134,
        _s135,
        _s136,
        _s137,
        _s138,
        _s139,
        _s140,
        _s141,
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
    _s142,
    {_s10: None, _s11: None},
    (_s12,),
    ((3, 0),),
)

SPARSE_STRING_LIST: StaticSchema = (
    16,
    n2,
    _s143,
    64,
    (_s4,),
    ((3, 0),),
)

SPARSE_NULLS_OPERATION_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s144,
    {_s10: None, _s11: None},
    (
        _s145,
        _s129,
    ),
    (
        (SPARSE_STRING_LIST, 0),
        (SPARSE_STRING_MAP, 0),
    ),
)

DATE_TIME: StaticSchema = (
    4,
    n2,
    _s146,
    {_s147: _s148},
)

HTTP_DATE: StaticSchema = (
    4,
    n2,
    _s149,
    {_s147: _s150},
)

EPOCH_SECONDS: StaticSchema = (
    4,
    n2,
    _s151,
    {_s147: _s152},
)

TIMESTAMP_FORMAT_IGNORED_IO: StaticSchema = (
    18,
    n1,
    _s153,
    {_s10: None, _s11: None},
    (
        _s154,
        _s155,
        _s156,
        _s157,
    ),
    (
        (DATE_TIME, 0),
        (HTTP_DATE, 0),
        (EPOCH_SECONDS, 0),
        (4, 0),
    ),
)

RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED1: StaticSchema = (
    18,
    n1,
    _s158,
    0,
    (
        _s159,
        _s80,
    ),
    (
        (3, 0),
        (lambda: RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED2, 0),
    ),
)

RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED2: StaticSchema = (
    18,
    n1,
    _s160,
    0,
    (
        _s161,
        _s162,
    ),
    (
        (3, 0),
        (RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED1, 0),
    ),
)
