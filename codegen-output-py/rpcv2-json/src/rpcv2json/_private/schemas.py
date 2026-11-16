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
_s15 = "smithy.api#clientOptional"
_s16 = "smithy.api#default"
_s17 = "ComplexNestedErrorData"
_s18 = "Foo"
_s19 = "ComplexError"
_s20 = "TopLevel"
_s21 = "Nested"
_s22 = "TestStringList"
_s23 = "TestStringMap"
_s24 = "key"
_s25 = "TestEnum"
_s26 = "FOO"
_s27 = "smithy.api#enumValue"
_s28 = "BAR"
_s29 = "BAZ"
_s30 = "TestIntEnum"
_s31 = "ONE"
_s32 = "TWO"
_s33 = "Defaults"
_s34 = "defaultString"
_s35 = "hi"
_s36 = "defaultBoolean"
_s37 = "defaultList"
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
_s60 = "DenseBooleanMap"
_s61 = "DenseNumberMap"
n2 = "smithy.protocoltests.shared"
_s62 = "StringSet"
_s63 = "DenseSetMap"
_s64 = "DenseStringMap"
_s65 = "GreetingStruct"
_s66 = "DenseStructMap"
_s67 = "EmptyStructure"
_s68 = "FractionalSecondsOutput"
_s69 = "datetime"
_s70 = "GreetingWithErrorsOutput"
_s71 = "greeting"
_s72 = "InvalidGreeting"
_s73 = "Message"
_s74 = "OperationWithDefaultsInput"
_s75 = "defaults"
_s76 = "clientOptionalDefaults"
_s77 = "topLevelDefault"
_s78 = "otherTopLevelDefault"
_s79 = "OperationWithDefaultsOutput"
_s80 = "RecursiveShapesInputOutput"
_s81 = "nested"
_s82 = "RpcV2JsonDenseMapsInputOutput"
_s83 = "denseStructMap"
_s84 = "denseNumberMap"
_s85 = "denseBooleanMap"
_s86 = "denseStringMap"
_s87 = "denseSetMap"
_s88 = "StringList"
_s89 = "IntegerList"
_s90 = "BooleanList"
_s91 = "TimestampList"
_s92 = "FooEnum"
_s93 = "Baz"
_s94 = "Bar"
_s95 = "1"
_s96 = "ZERO"
_s97 = "0"
_s98 = "FooEnumList"
_s99 = "IntegerEnum"
_s100 = "A"
_s101 = "B"
_s102 = "C"
_s103 = "IntegerEnumList"
_s104 = "NestedStringList"
_s105 = "StructureListMember"
_s106 = "a"
_s107 = "b"
_s108 = "StructureList"
_s109 = "BlobList"
_s110 = "RpcV2JsonListInputOutput"
_s111 = "stringList"
_s112 = "stringSet"
_s113 = "integerList"
_s114 = "booleanList"
_s115 = "timestampList"
_s116 = "enumList"
_s117 = "intEnumList"
_s118 = "nestedStringList"
_s119 = "structureList"
_s120 = "blobList"
_s121 = "SparseStructMap"
_s122 = "SparseNumberMap"
_s123 = "SparseBooleanMap"
_s124 = "SparseStringMap"
_s125 = "SparseSetMap"
_s126 = "RpcV2JsonSparseMapsInputOutput"
_s127 = "sparseStructMap"
_s128 = "sparseNumberMap"
_s129 = "sparseBooleanMap"
_s130 = "sparseStringMap"
_s131 = "sparseSetMap"
_s132 = "SimpleScalarStructure"
_s133 = "trueBooleanValue"
_s134 = "falseBooleanValue"
_s135 = "byteValue"
_s136 = "doubleValue"
_s137 = "floatValue"
_s138 = "integerValue"
_s139 = "longValue"
_s140 = "shortValue"
_s141 = "stringValue"
_s142 = "blobValue"
_s143 = "SimpleStructure"
_s144 = "SparseStringList"
_s145 = "SparseNullsOperationInputOutput"
_s146 = "sparseStringList"
_s147 = "DateTime"
_s148 = "smithy.api#timestampFormat"
_s149 = "date-time"
_s150 = "HttpDate"
_s151 = "http-date"
_s152 = "EpochSeconds"
_s153 = "epoch-seconds"
_s154 = "TimestampFormatIgnoredIO"
_s155 = "dateTime"
_s156 = "httpDate"
_s157 = "epochSeconds"
_s158 = "normal"
_s159 = "RecursiveShapesInputOutputNested1"
_s160 = "foo"
_s161 = "RecursiveShapesInputOutputNested2"
_s162 = "bar"
_s163 = "recursiveMember"

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
    ((7, {_s15: None, _s16: 0}),),
)

COMPLEX_NESTED_ERROR_DATA: StaticSchema = (
    18,
    n1,
    _s17,
    0,
    (_s18,),
    ((3, 0),),
)

COMPLEX_ERROR: StaticSchema = (
    18,
    n1,
    _s19,
    {_s6: _s7},
    (_s20, _s21),
    ((3, 0), (COMPLEX_NESTED_ERROR_DATA, 0)),
)

TEST_STRING_LIST: StaticSchema = (
    16,
    n1,
    _s22,
    0,
    (_s4,),
    ((3, 0),),
)

TEST_STRING_MAP: StaticSchema = (
    17,
    n1,
    _s23,
    0,
    (_s24, _s12),
    ((3, 0), (3, 0)),
)

TEST_ENUM: StaticSchema = (
    14,
    n1,
    _s25,
    0,
    (_s26, _s28, _s29),
    ((-1, {_s27: _s26}), (-1, {_s27: _s28}), (-1, {_s27: _s29})),
)

TEST_INT_ENUM: StaticSchema = (
    15,
    n1,
    _s30,
    0,
    (_s31, _s32),
    ((-1, {_s27: 1}), (-1, {_s27: 2})),
)

DEFAULTS: StaticSchema = (
    18,
    n1,
    _s33,
    0,
    (
        _s34,
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
        (3, {_s16: _s35}),
        (2, {_s16: True}),
        (TEST_STRING_LIST, {_s16: ()}),
        (4, {_s16: 0}),
        (1, {_s16: _s40}),
        (5, {_s16: 1}),
        (6, {_s16: 1}),
        (7, {_s16: 10}),
        (8, {_s16: 100}),
        (9, {_s16: 1.0}),
        (10, {_s16: 1.0}),
        (TEST_STRING_MAP, {_s16: MappingProxyType[str, object]({})}),
        (TEST_ENUM, {_s16: _s26}),
        (TEST_INT_ENUM, {_s16: 1}),
        (3, {_s16: _s51}),
        (2, {_s16: False}),
        (1, {_s16: _s51}),
        (5, {_s16: 0}),
        (6, {_s16: 0}),
        (7, {_s16: 0}),
        (8, {_s16: 0}),
        (9, {_s16: 0.0}),
        (10, {_s16: 0.0}),
    ),
)

DENSE_BOOLEAN_MAP: StaticSchema = (
    17,
    n1,
    _s60,
    0,
    (_s24, _s12),
    ((3, 0), (2, 0)),
)

DENSE_NUMBER_MAP: StaticSchema = (
    17,
    n1,
    _s61,
    0,
    (_s24, _s12),
    ((3, 0), (7, 0)),
)

STRING_SET: StaticSchema = (
    16,
    n2,
    _s62,
    0,
    (_s4,),
    ((3, 0),),
)

DENSE_SET_MAP: StaticSchema = (
    17,
    n1,
    _s63,
    0,
    (_s24, _s12),
    ((3, 0), (STRING_SET, 0)),
)

DENSE_STRING_MAP: StaticSchema = (
    17,
    n1,
    _s64,
    0,
    (_s24, _s12),
    ((3, 0), (3, 0)),
)

GREETING_STRUCT: StaticSchema = (
    18,
    n2,
    _s65,
    0,
    (_s35,),
    ((3, 0),),
)

DENSE_STRUCT_MAP: StaticSchema = (
    17,
    n1,
    _s66,
    0,
    (_s24, _s12),
    ((3, 0), (GREETING_STRUCT, 0)),
)

EMPTY_STRUCTURE: StaticSchema = (
    18,
    n1,
    _s67,
    {_s10: None, _s11: None},
)

FRACTIONAL_SECONDS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s68,
    {_s11: None},
    (_s69,),
    ((4, 0),),
)

GREETING_WITH_ERRORS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s70,
    {_s11: None},
    (_s71,),
    ((3, 0),),
)

INVALID_GREETING: StaticSchema = (
    18,
    n1,
    _s72,
    {_s6: _s7},
    (_s73,),
    ((3, 0),),
)

OPERATION_WITH_DEFAULTS_INPUT: StaticSchema = (
    18,
    n1,
    _s74,
    {_s10: None},
    (_s75, _s76, _s77, _s78),
    ((DEFAULTS, 0), (CLIENT_OPTIONAL_DEFAULTS, 0), (3, {_s16: _s35}), (7, {_s16: 0})),
)

OPERATION_WITH_DEFAULTS_OUTPUT: StaticSchema = (
    18,
    n1,
    _s79,
    {_s11: None},
    (
        _s34,
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
        (3, {_s16: _s35}),
        (2, {_s16: True}),
        (TEST_STRING_LIST, {_s16: ()}),
        (4, {_s16: 0}),
        (1, {_s16: _s40}),
        (5, {_s16: 1}),
        (6, {_s16: 1}),
        (7, {_s16: 10}),
        (8, {_s16: 100}),
        (9, {_s16: 1.0}),
        (10, {_s16: 1.0}),
        (TEST_STRING_MAP, {_s16: MappingProxyType[str, object]({})}),
        (TEST_ENUM, {_s16: _s26}),
        (TEST_INT_ENUM, {_s16: 1}),
        (3, {_s16: _s51}),
        (2, {_s16: False}),
        (1, {_s16: _s51}),
        (5, {_s16: 0}),
        (6, {_s16: 0}),
        (7, {_s16: 0}),
        (8, {_s16: 0}),
        (9, {_s16: 0.0}),
        (10, {_s16: 0.0}),
    ),
)

RECURSIVE_SHAPES_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s80,
    {_s10: None, _s11: None},
    (_s81,),
    ((lambda: RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED1, 0),),
)

RPC_V2_JSON_DENSE_MAPS_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s82,
    {_s10: None, _s11: None},
    (_s83, _s84, _s85, _s86, _s87),
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
    _s88,
    0,
    (_s4,),
    ((3, 0),),
)

INTEGER_LIST: StaticSchema = (
    16,
    n2,
    _s89,
    0,
    (_s4,),
    ((7, 0),),
)

BOOLEAN_LIST: StaticSchema = (
    16,
    n2,
    _s90,
    0,
    (_s4,),
    ((2, 0),),
)

TIMESTAMP_LIST: StaticSchema = (
    16,
    n2,
    _s91,
    0,
    (_s4,),
    ((4, 0),),
)

FOO_ENUM: StaticSchema = (
    14,
    n2,
    _s92,
    0,
    (_s26, _s29, _s28, _s31, _s96),
    (
        (-1, {_s27: _s18}),
        (-1, {_s27: _s93}),
        (-1, {_s27: _s94}),
        (-1, {_s27: _s95}),
        (-1, {_s27: _s97}),
    ),
)

FOO_ENUM_LIST: StaticSchema = (
    16,
    n2,
    _s98,
    0,
    (_s4,),
    ((FOO_ENUM, 0),),
)

INTEGER_ENUM: StaticSchema = (
    15,
    n2,
    _s99,
    0,
    (_s100, _s101, _s102),
    ((-1, {_s27: 1}), (-1, {_s27: 2}), (-1, {_s27: 3})),
)

INTEGER_ENUM_LIST: StaticSchema = (
    16,
    n2,
    _s103,
    0,
    (_s4,),
    ((INTEGER_ENUM, 0),),
)

NESTED_STRING_LIST: StaticSchema = (
    16,
    n2,
    _s104,
    0,
    (_s4,),
    ((STRING_LIST, 0),),
)

STRUCTURE_LIST_MEMBER: StaticSchema = (
    18,
    n1,
    _s105,
    0,
    (_s106, _s107),
    ((3, 0), (3, 0)),
)

STRUCTURE_LIST: StaticSchema = (
    16,
    n1,
    _s108,
    0,
    (_s4,),
    ((STRUCTURE_LIST_MEMBER, 0),),
)

BLOB_LIST: StaticSchema = (
    16,
    n2,
    _s109,
    0,
    (_s4,),
    ((1, 0),),
)

RPC_V2_JSON_LIST_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s110,
    {_s10: None, _s11: None},
    (_s111, _s112, _s113, _s114, _s115, _s116, _s117, _s118, _s119, _s120),
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
    _s121,
    64,
    (_s24, _s12),
    ((3, 0), (GREETING_STRUCT, 0)),
)

SPARSE_NUMBER_MAP: StaticSchema = (
    17,
    n1,
    _s122,
    64,
    (_s24, _s12),
    ((3, 0), (7, 0)),
)

SPARSE_BOOLEAN_MAP: StaticSchema = (
    17,
    n1,
    _s123,
    64,
    (_s24, _s12),
    ((3, 0), (2, 0)),
)

SPARSE_STRING_MAP: StaticSchema = (
    17,
    n2,
    _s124,
    64,
    (_s24, _s12),
    ((3, 0), (3, 0)),
)

SPARSE_SET_MAP: StaticSchema = (
    17,
    n1,
    _s125,
    64,
    (_s24, _s12),
    ((3, 0), (STRING_SET, 0)),
)

RPC_V2_JSON_SPARSE_MAPS_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s126,
    {_s10: None, _s11: None},
    (_s127, _s128, _s129, _s130, _s131),
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
    _s132,
    {_s10: None, _s11: None},
    (_s133, _s134, _s135, _s136, _s137, _s138, _s139, _s140, _s141, _s142),
    ((2, 0), (2, 0), (5, 0), (10, 0), (9, 0), (7, 0), (8, 0), (6, 0), (3, 0), (1, 0)),
)

SIMPLE_STRUCTURE: StaticSchema = (
    18,
    n1,
    _s143,
    {_s10: None, _s11: None},
    (_s12,),
    ((3, 0),),
)

SPARSE_STRING_LIST: StaticSchema = (
    16,
    n2,
    _s144,
    64,
    (_s4,),
    ((3, 0),),
)

SPARSE_NULLS_OPERATION_INPUT_OUTPUT: StaticSchema = (
    18,
    n1,
    _s145,
    {_s10: None, _s11: None},
    (_s146, _s130),
    ((SPARSE_STRING_LIST, 0), (SPARSE_STRING_MAP, 0)),
)

DATE_TIME: StaticSchema = (
    4,
    n2,
    _s147,
    {_s148: _s149},
)

HTTP_DATE: StaticSchema = (
    4,
    n2,
    _s150,
    {_s148: _s151},
)

EPOCH_SECONDS: StaticSchema = (
    4,
    n2,
    _s152,
    {_s148: _s153},
)

TIMESTAMP_FORMAT_IGNORED_IO: StaticSchema = (
    18,
    n1,
    _s154,
    {_s10: None, _s11: None},
    (_s155, _s156, _s157, _s158),
    ((DATE_TIME, 0), (HTTP_DATE, 0), (EPOCH_SECONDS, 0), (4, 0)),
)

RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED1: StaticSchema = (
    18,
    n1,
    _s159,
    0,
    (_s160, _s81),
    ((3, 0), (lambda: RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED2, 0)),
)

RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED2: StaticSchema = (
    18,
    n1,
    _s161,
    0,
    (_s162, _s163),
    ((3, 0), (RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED1, 0)),
)
