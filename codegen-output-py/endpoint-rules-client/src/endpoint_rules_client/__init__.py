from importlib import import_module
from typing import TYPE_CHECKING, Any

__version__: str = "0.0.1"

if TYPE_CHECKING:
    from .aio.client import AsyncEndpointService
    from .aio.config import AsyncConfig
    from .client import EndpointService
    from .config import Config

__all__ = ["AsyncConfig", "AsyncEndpointService", "Config", "EndpointService"]

_EXPORTS = {
    "EndpointService": ".client",
    "Config": ".config",
    "AsyncEndpointService": ".aio.client",
    "AsyncConfig": ".aio.config",
}


def __getattr__(name: str) -> Any:
    if name in _EXPORTS:
        return getattr(import_module(_EXPORTS[name], __name__), name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
