from types import MappingProxyType

from smithy_core._schema_compact import StaticOperationSchema, StaticSchema

n0 = "example.awsconfig"
_s0 = "GetForecastInput"
_s1 = "smithy.synthetic#originalShapeId"
_s2 = "example.awsconfig#GetForecastInput"
_s3 = "smithy.api#input"
_s4 = "city"
_s5 = "GetForecastOutput"
_s6 = "example.awsconfig#GetForecastOutput"
_s7 = "smithy.api#output"
_s8 = "summary"
_s9 = "GetForecast"
_s10 = "WeatherStation"
_s11 = "aws.api#service"
_s12 = "smithy.protocols#rpcv2Cbor"

GET_FORECAST_INPUT: StaticSchema = (
    18,
    n0,
    _s0,
    {_s1: _s2, _s3: None},
    (_s4,),
    ((3, 0),),
)

GET_FORECAST_OUTPUT: StaticSchema = (
    18,
    n0,
    _s5,
    {_s1: _s6, _s7: None},
    (_s8,),
    ((3, 0),),
)

GET_FORECAST: StaticOperationSchema = (
    23,
    n0,
    _s9,
    0,
    GET_FORECAST_INPUT,
    GET_FORECAST_OUTPUT,
    (),
)

WEATHER_STATION: StaticSchema = (
    21,
    n0,
    _s10,
    {_s11: MappingProxyType({"sdkId": "Weather Station"}), _s12: None},
)
