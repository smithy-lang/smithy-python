from importlib import import_module
from typing import TYPE_CHECKING, Any

__version__: str = "0.0.1"

if TYPE_CHECKING:
    from .aio.client import AsyncRpcV2Protocol
    from .aio.config import AsyncConfig
    from .client import RpcV2Protocol
    from .config import Config

__all__ = ["AsyncConfig", "AsyncRpcV2Protocol", "Config", "RpcV2Protocol"]

_EXPORTS = {
    "RpcV2Protocol": ".client",
    "Config": ".config",
    "AsyncRpcV2Protocol": ".aio.client",
    "AsyncConfig": ".aio.config",
}


def __getattr__(name: str) -> Any:
    if name in _EXPORTS:
        return getattr(import_module(_EXPORTS[name], __name__), name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
