from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .client import AsyncJSONRPC10Client
    from .config import AsyncJSONRPC10Config

__all__ = ["AsyncJSONRPC10Client", "AsyncJSONRPC10Config"]

_EXPORTS = {
    "AsyncJSONRPC10Client": ".client",
    "AsyncJSONRPC10Config": ".config",
}


def __getattr__(name: str) -> Any:
    if name in _EXPORTS:
        return getattr(import_module(_EXPORTS[name], __name__), name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
