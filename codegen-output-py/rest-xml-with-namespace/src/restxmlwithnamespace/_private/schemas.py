from types import MappingProxyType

from smithy_core._schema_compact import StaticSchema

n0 = "aws.protocoltests.restxml.xmlns"
_s0 = "NestedWithNamespace"
_s1 = "attrField"
_s2 = "smithy.api#xmlAttribute"
_s3 = "smithy.api#xmlName"
_s4 = "xsi:someName"
_s5 = "SimpleScalarPropertiesRequest"
_s6 = "smithy.api#input"
_s7 = "foo"
_s8 = "smithy.api#httpHeader"
_s9 = "X-Foo"
_s10 = "stringValue"
_s11 = "trueBooleanValue"
_s12 = "falseBooleanValue"
_s13 = "byteValue"
_s14 = "shortValue"
_s15 = "integerValue"
_s16 = "longValue"
_s17 = "floatValue"
_s18 = "Nested"
_s19 = "smithy.api#xmlNamespace"
_s20 = "doubleValue"
_s21 = "DoubleDribble"
_s22 = "SimpleScalarPropertiesResponse"
_s23 = "smithy.api#output"

NESTED_WITH_NAMESPACE: StaticSchema = (
    18,
    n0,
    _s0,
    0,
    (_s1,),
    ((3, {_s2: None, _s3: _s4}),),
)

SIMPLE_SCALAR_PROPERTIES_REQUEST: StaticSchema = (
    18,
    n0,
    _s5,
    {_s6: None},
    (
        _s7,
        _s10,
        _s11,
        _s12,
        _s13,
        _s14,
        _s15,
        _s16,
        _s17,
        _s18,
        _s20,
    ),
    (
        (3, {_s8: _s9}),
        (3, 0),
        (2, 0),
        (2, 0),
        (5, 0),
        (6, 0),
        (7, 0),
        (8, 0),
        (9, 0),
        (
            NESTED_WITH_NAMESPACE,
            {_s19: MappingProxyType({"prefix": "xsi", "uri": "https://example.com"})},
        ),
        (10, {_s3: _s21}),
    ),
)

SIMPLE_SCALAR_PROPERTIES_RESPONSE: StaticSchema = (
    18,
    n0,
    _s22,
    {_s23: None},
    (
        _s7,
        _s10,
        _s11,
        _s12,
        _s13,
        _s14,
        _s15,
        _s16,
        _s17,
        _s18,
        _s20,
    ),
    (
        (3, {_s8: _s9}),
        (3, 0),
        (2, 0),
        (2, 0),
        (5, 0),
        (6, 0),
        (7, 0),
        (8, 0),
        (9, 0),
        (
            NESTED_WITH_NAMESPACE,
            {_s19: MappingProxyType({"prefix": "xsi", "uri": "https://example.com"})},
        ),
        (10, {_s3: _s21}),
    ),
)
