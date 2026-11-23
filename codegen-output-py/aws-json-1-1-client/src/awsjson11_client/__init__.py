from importlib import import_module
from typing import TYPE_CHECKING, Any

__version__: str = "0.0.1"

if TYPE_CHECKING:
    from .aio.client import AsyncJsonProtocolClient
    from .aio.config import AsyncJsonProtocolConfig
    from .client import JsonProtocolClient
    from .config import JsonProtocolConfig

__all__ = [
    "AsyncJsonProtocolClient",
    "AsyncJsonProtocolConfig",
    "JsonProtocolClient",
    "JsonProtocolConfig",
]

_EXPORTS = {
    "JsonProtocolClient": ".client",
    "JsonProtocolConfig": ".config",
    "AsyncJsonProtocolClient": ".aio.client",
    "AsyncJsonProtocolConfig": ".aio.config",
}


def __getattr__(name: str) -> Any:
    if name in _EXPORTS:
        return getattr(import_module(_EXPORTS[name], __name__), name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
