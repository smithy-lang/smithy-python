from smithy_core._schema_compact import StaticSchema

n0 = "example"
_s0 = "GetExampleInput"
_s1 = "smithy.api#input"
_s2 = "id"
_s3 = "TagList"
_s4 = "member"
_s5 = "Attributes"
_s6 = "key"
_s7 = "value"
_s8 = "Value"
_s9 = "text"
_s10 = "number"
_s11 = "empty"
_s12 = "Status"
_s13 = "ACTIVE"
_s14 = "smithy.api#enumValue"
_s15 = "active"
_s16 = "INACTIVE"
_s17 = "inactive"
_s18 = "Code"
_s19 = "OK"
_s20 = "NOT_FOUND"
_s21 = "Example"
_s22 = "name"
_s23 = "count"
_s24 = "tags"
_s25 = "attributes"
_s26 = "choice"
_s27 = "status"
_s28 = "code"
_s29 = "EventStream"
_s30 = "smithy.api#streaming"
_s31 = "GetExampleOutput"
_s32 = "smithy.api#output"
_s33 = "events"
_s34 = "ExampleError"
_s35 = "smithy.api#error"
_s36 = "client"
_s37 = "message"
_s38 = "retryAfterSeconds"

GET_EXAMPLE_INPUT: StaticSchema = (
    18,
    n0,
    _s0,
    {_s1: None},
    (_s2,),
    ((3, 1),),
)

TAG_LIST: StaticSchema = (
    16,
    n0,
    _s3,
    0,
    (_s4,),
    ((3, 0),),
)

ATTRIBUTES: StaticSchema = (
    17,
    n0,
    _s5,
    0,
    (
        _s6,
        _s7,
    ),
    (
        (3, 0),
        (13, 0),
    ),
)

EXAMPLE_VALUE: StaticSchema = (
    19,
    n0,
    _s8,
    0,
    (
        _s9,
        _s10,
        _s11,
    ),
    (
        (3, 0),
        (7, 0),
        (-1, 0),
    ),
)

STATUS: StaticSchema = (
    14,
    n0,
    _s12,
    0,
    (
        _s13,
        _s16,
    ),
    (
        (-1, {_s14: _s15}),
        (-1, {_s14: _s17}),
    ),
)

CODE: StaticSchema = (
    15,
    n0,
    _s18,
    0,
    (
        _s19,
        _s20,
    ),
    (
        (-1, {_s14: 200}),
        (-1, {_s14: 404}),
    ),
)

RENAMED_EXAMPLE: StaticSchema = (
    18,
    n0,
    _s21,
    0,
    (
        _s22,
        _s23,
        _s24,
        _s25,
        _s26,
        _s27,
        _s28,
    ),
    (
        (3, 1),
        (-5, 0),
        (TAG_LIST, 0),
        (ATTRIBUTES, 0),
        (EXAMPLE_VALUE, 0),
        (STATUS, 0),
        (CODE, 0),
    ),
)

EVENT_STREAM: StaticSchema = (
    19,
    n0,
    _s29,
    {_s30: None},
    (n0,),
    ((RENAMED_EXAMPLE, 0),),
)

GET_EXAMPLE_OUTPUT: StaticSchema = (
    18,
    n0,
    _s31,
    {_s32: None},
    (
        n0,
        _s7,
        _s33,
    ),
    (
        (RENAMED_EXAMPLE, 0),
        (EXAMPLE_VALUE, 0),
        (EVENT_STREAM, 0),
    ),
)

EXAMPLE_ERROR: StaticSchema = (
    18,
    n0,
    _s34,
    {_s35: _s36},
    (
        _s37,
        _s38,
    ),
    (
        (3, 0),
        (7, 0),
    ),
)
