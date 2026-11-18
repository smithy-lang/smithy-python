from importlib import import_module
from typing import TYPE_CHECKING, Any

__version__: str = "0.0.1"

if TYPE_CHECKING:
    from .aio.client import AsyncApiKeyService
    from .aio.config import AsyncConfig
    from .client import ApiKeyService
    from .config import Config

__all__ = ["ApiKeyService", "AsyncApiKeyService", "AsyncConfig", "Config"]

_EXPORTS = {
    "ApiKeyService": ".client",
    "Config": ".config",
    "AsyncApiKeyService": ".aio.client",
    "AsyncConfig": ".aio.config",
}


def __getattr__(name: str) -> Any:
    if name in _EXPORTS:
        return getattr(import_module(_EXPORTS[name], __name__), name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
