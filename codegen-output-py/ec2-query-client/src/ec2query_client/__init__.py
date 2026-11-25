from importlib import import_module
from typing import TYPE_CHECKING, Any

__version__: str = "0.0.1"

if TYPE_CHECKING:
    from .aio.client import AsyncEC2ProtocolClient
    from .aio.config import AsyncEC2ProtocolConfig
    from .client import EC2ProtocolClient
    from .config import EC2ProtocolConfig

__all__ = [
    "AsyncEC2ProtocolClient",
    "AsyncEC2ProtocolConfig",
    "EC2ProtocolClient",
    "EC2ProtocolConfig",
]

_EXPORTS = {
    "EC2ProtocolClient": ".client",
    "EC2ProtocolConfig": ".config",
    "AsyncEC2ProtocolClient": ".aio.client",
    "AsyncEC2ProtocolConfig": ".aio.config",
}


def __getattr__(name: str) -> Any:
    if name in _EXPORTS:
        return getattr(import_module(_EXPORTS[name], __name__), name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
