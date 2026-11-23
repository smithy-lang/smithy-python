from importlib import import_module
from typing import TYPE_CHECKING, Any

__version__: str = "0.0.1"

if TYPE_CHECKING:
    from .aio.client import AsyncRestJsonProtocolClient
    from .aio.config import AsyncRestJsonProtocolConfig
    from .client import RestJsonProtocolClient
    from .config import RestJsonProtocolConfig

__all__ = [
    "AsyncRestJsonProtocolClient",
    "AsyncRestJsonProtocolConfig",
    "RestJsonProtocolClient",
    "RestJsonProtocolConfig",
]

_EXPORTS = {
    "RestJsonProtocolClient": ".client",
    "RestJsonProtocolConfig": ".config",
    "AsyncRestJsonProtocolClient": ".aio.client",
    "AsyncRestJsonProtocolConfig": ".aio.config",
}


def __getattr__(name: str) -> Any:
    if name in _EXPORTS:
        return getattr(import_module(_EXPORTS[name], __name__), name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
