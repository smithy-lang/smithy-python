from importlib import import_module
from typing import TYPE_CHECKING, Any

__version__: str = "0.0.1"

if TYPE_CHECKING:
    from .aio.client import AsyncQueryProtocolClient
    from .aio.config import AsyncQueryProtocolConfig
    from .client import QueryProtocolClient
    from .config import QueryProtocolConfig

__all__ = [
    "AsyncQueryProtocolClient",
    "AsyncQueryProtocolConfig",
    "QueryProtocolClient",
    "QueryProtocolConfig",
]

_EXPORTS = {
    "QueryProtocolClient": ".client",
    "QueryProtocolConfig": ".config",
    "AsyncQueryProtocolClient": ".aio.client",
    "AsyncQueryProtocolConfig": ".aio.config",
}


def __getattr__(name: str) -> Any:
    if name in _EXPORTS:
        return getattr(import_module(_EXPORTS[name], __name__), name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
