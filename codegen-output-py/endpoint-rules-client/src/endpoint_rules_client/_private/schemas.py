from types import MappingProxyType

from smithy_core._schema_compact import StaticOperationSchema, StaticSchema

n0 = "example.endpoints"
_s0 = "PluginNames"
_s1 = "member"
_s2 = "ThingTag"
_s3 = "key"
_s4 = "value"
_s5 = "PutThingInput"
_s6 = "smithy.synthetic#originalShapeId"
_s7 = "example.endpoints#PutThingInput"
_s8 = "smithy.api#input"
_s9 = "name"
_s10 = "smithy.rules#contextParam"
_s11 = "smithy.api#required"
_s12 = "tag"
_s13 = "plugins"
_s14 = "PingInput"
_s15 = "smithy.api#Unit"
_s16 = "PingOutput"
_s17 = "smithy.api#output"
_s18 = "PutThingOutput"
_s19 = "Ping"
_s20 = "smithy.rules#staticContextParams"
_s21 = "PutThing"
_s22 = "EndpointService"
_s23 = "smithy.protocols#rpcv2Cbor"

PLUGIN_NAMES: StaticSchema = (
    16,
    n0,
    _s0,
    0,
    (_s1,),
    ((3, 0),),
)

THING_TAG: StaticSchema = (
    18,
    n0,
    _s2,
    0,
    (_s3, _s4),
    ((3, 0), (3, 0)),
)

PUT_THING_INPUT: StaticSchema = (
    18,
    n0,
    _s5,
    {_s6: _s7, _s8: None},
    (_s9, _s12, _s13),
    (
        (3, {_s10: MappingProxyType({"name": "Name"}), _s11: None}),
        (THING_TAG, 0),
        (PLUGIN_NAMES, 0),
    ),
)

PING_INPUT: StaticSchema = (
    18,
    n0,
    _s14,
    {_s6: _s15, _s8: None},
)

PING_OUTPUT: StaticSchema = (
    18,
    n0,
    _s16,
    {_s6: _s15, _s17: None},
)

PUT_THING_OUTPUT: StaticSchema = (
    18,
    n0,
    _s18,
    {_s6: _s15, _s17: None},
)

PING: StaticOperationSchema = (
    23,
    n0,
    _s19,
    {_s20: MappingProxyType({"Kind": MappingProxyType({"value": "ping"})})},
    PING_INPUT,
    PING_OUTPUT,
    (),
)

PUT_THING: StaticOperationSchema = (
    23,
    n0,
    _s21,
    {_s20: MappingProxyType({"Kind": MappingProxyType({"value": "put"})})},
    PUT_THING_INPUT,
    PUT_THING_OUTPUT,
    (),
)

ENDPOINT_SERVICE: StaticSchema = (
    21,
    n0,
    _s22,
    {_s23: None},
)
