from importlib import import_module
from typing import TYPE_CHECKING, Any

__version__: str = "0.0.1"

if TYPE_CHECKING:
    from .aio.client import AsyncQueryCompatibleJSONRPC10Client
    from .aio.config import AsyncQueryCompatibleJSONRPC10Config
    from .client import QueryCompatibleJSONRPC10Client
    from .config import QueryCompatibleJSONRPC10Config

__all__ = [
    "AsyncQueryCompatibleJSONRPC10Client",
    "AsyncQueryCompatibleJSONRPC10Config",
    "QueryCompatibleJSONRPC10Client",
    "QueryCompatibleJSONRPC10Config",
]

_EXPORTS = {
    "QueryCompatibleJSONRPC10Client": ".client",
    "QueryCompatibleJSONRPC10Config": ".config",
    "AsyncQueryCompatibleJSONRPC10Client": ".aio.client",
    "AsyncQueryCompatibleJSONRPC10Config": ".aio.config",
}


def __getattr__(name: str) -> Any:
    if name in _EXPORTS:
        return getattr(import_module(_EXPORTS[name], __name__), name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
