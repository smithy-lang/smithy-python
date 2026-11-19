from importlib import import_module
from typing import TYPE_CHECKING, Any

__version__: str = "0.0.1"

if TYPE_CHECKING:
    from .aio.client import AsyncWeatherStationClient
    from .aio.config import AsyncWeatherStationConfig
    from .client import WeatherStationClient
    from .config import WeatherStationConfig

__all__ = [
    "AsyncWeatherStationClient",
    "AsyncWeatherStationConfig",
    "WeatherStationClient",
    "WeatherStationConfig",
]

_EXPORTS = {
    "WeatherStationClient": ".client",
    "WeatherStationConfig": ".config",
    "AsyncWeatherStationClient": ".aio.client",
    "AsyncWeatherStationConfig": ".aio.config",
}


def __getattr__(name: str) -> Any:
    if name in _EXPORTS:
        return getattr(import_module(_EXPORTS[name], __name__), name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
