from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .client import AsyncJsonProtocolClient
    from .config import AsyncJsonProtocolConfig

__all__ = ["AsyncJsonProtocolClient", "AsyncJsonProtocolConfig"]

_EXPORTS = {
    "AsyncJsonProtocolClient": ".client",
    "AsyncJsonProtocolConfig": ".config",
}


def __getattr__(name: str) -> Any:
    if name in _EXPORTS:
        return getattr(import_module(_EXPORTS[name], __name__), name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
