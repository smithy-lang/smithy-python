from types import MappingProxyType

from smithy_core._schema_compact import StaticOperationSchema, StaticSchema

n0 = "aws.protocoltests.restxml.xmlns"
_s0 = "NestedWithNamespace"
_s1 = "attrField"
_s2 = "smithy.api#xmlAttribute"
_s3 = "smithy.api#xmlName"
_s4 = "xsi:someName"
_s5 = "SimpleScalarPropertiesInput"
_s6 = "smithy.synthetic#originalShapeId"
_s7 = "aws.protocoltests.restxml.xmlns#SimpleScalarPropertiesRequest"
_s8 = "smithy.api#input"
_s9 = "foo"
_s10 = "smithy.api#httpHeader"
_s11 = "X-Foo"
_s12 = "stringValue"
_s13 = "trueBooleanValue"
_s14 = "falseBooleanValue"
_s15 = "byteValue"
_s16 = "shortValue"
_s17 = "integerValue"
_s18 = "longValue"
_s19 = "floatValue"
_s20 = "Nested"
_s21 = "smithy.api#xmlNamespace"
_s22 = "doubleValue"
_s23 = "DoubleDribble"
_s24 = "SimpleScalarPropertiesOutput"
_s25 = "aws.protocoltests.restxml.xmlns#SimpleScalarPropertiesResponse"
_s26 = "smithy.api#output"
_s27 = "SimpleScalarProperties"
_s28 = "smithy.api#http"
_s29 = "RestXmlWithNamespace"
_s30 = "aws.api#service"
_s31 = "aws.auth#sigv4"
_s32 = "aws.protocols#restXml"

NESTED_WITH_NAMESPACE: StaticSchema = (
    18,
    n0,
    _s0,
    0,
    (_s1,),
    ((3, {_s2: None, _s3: _s4}),),
)

SIMPLE_SCALAR_PROPERTIES_INPUT: StaticSchema = (
    18,
    n0,
    _s5,
    {_s6: _s7, _s8: None},
    (_s9, _s12, _s13, _s14, _s15, _s16, _s17, _s18, _s19, _s20, _s22),
    (
        (3, {_s10: _s11}),
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
            {_s21: MappingProxyType({"prefix": "xsi", "uri": "https://example.com"})},
        ),
        (10, {_s3: _s23}),
    ),
)

SIMPLE_SCALAR_PROPERTIES_OUTPUT: StaticSchema = (
    18,
    n0,
    _s24,
    {_s6: _s25, _s26: None},
    (_s9, _s12, _s13, _s14, _s15, _s16, _s17, _s18, _s19, _s20, _s22),
    (
        (3, {_s10: _s11}),
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
            {_s21: MappingProxyType({"prefix": "xsi", "uri": "https://example.com"})},
        ),
        (10, {_s3: _s23}),
    ),
)

SIMPLE_SCALAR_PROPERTIES: StaticOperationSchema = (
    23,
    n0,
    _s27,
    {_s28: MappingProxyType({"uri": "/SimpleScalarProperties", "method": "PUT"})},
    SIMPLE_SCALAR_PROPERTIES_INPUT,
    SIMPLE_SCALAR_PROPERTIES_OUTPUT,
    (),
)

REST_XML_WITH_NAMESPACE: StaticSchema = (
    21,
    n0,
    _s29,
    {
        _s30: MappingProxyType({"sdkId": "Rest Xml Protocol Namespace"}),
        _s31: MappingProxyType({"name": "restxmlwithnamespace"}),
        _s32: None,
        _s21: MappingProxyType({"uri": "https://example.com"}),
    },
)
