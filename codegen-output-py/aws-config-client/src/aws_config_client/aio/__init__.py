from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .client import AsyncWeatherStationClient
    from .config import AsyncWeatherStationConfig

__all__ = ["AsyncWeatherStationClient", "AsyncWeatherStationConfig"]

_EXPORTS = {
    "AsyncWeatherStationClient": ".client",
    "AsyncWeatherStationConfig": ".config",
}


def __getattr__(name: str) -> Any:
    if name in _EXPORTS:
        return getattr(import_module(_EXPORTS[name], __name__), name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
