from importlib import import_module
from typing import TYPE_CHECKING, Any

__version__: str = "0.0.1"

if TYPE_CHECKING:
    from .aio.client import AsyncJSONRPC10Client
    from .aio.config import AsyncJSONRPC10Config
    from .client import JSONRPC10Client
    from .config import JSONRPC10Config

__all__ = [
    "AsyncJSONRPC10Client",
    "AsyncJSONRPC10Config",
    "JSONRPC10Client",
    "JSONRPC10Config",
]

_EXPORTS = {
    "JSONRPC10Client": ".client",
    "JSONRPC10Config": ".config",
    "AsyncJSONRPC10Client": ".aio.client",
    "AsyncJSONRPC10Config": ".aio.config",
}


def __getattr__(name: str) -> Any:
    if name in _EXPORTS:
        return getattr(import_module(_EXPORTS[name], __name__), name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
