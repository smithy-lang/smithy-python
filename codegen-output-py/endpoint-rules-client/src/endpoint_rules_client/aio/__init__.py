from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .client import AsyncEndpointService
    from .config import AsyncConfig

__all__ = ["AsyncConfig", "AsyncEndpointService"]

_EXPORTS = {
    "AsyncEndpointService": ".client",
    "AsyncConfig": ".config",
}


def __getattr__(name: str) -> Any:
    if name in _EXPORTS:
        return getattr(import_module(_EXPORTS[name], __name__), name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
