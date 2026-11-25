from importlib import import_module
from typing import TYPE_CHECKING, Any

__version__: str = "0.0.1"

if TYPE_CHECKING:
    from .aio.client import AsyncRestXmlProtocolClient
    from .aio.config import AsyncRestXmlProtocolConfig
    from .client import RestXmlProtocolClient
    from .config import RestXmlProtocolConfig

__all__ = [
    "AsyncRestXmlProtocolClient",
    "AsyncRestXmlProtocolConfig",
    "RestXmlProtocolClient",
    "RestXmlProtocolConfig",
]

_EXPORTS = {
    "RestXmlProtocolClient": ".client",
    "RestXmlProtocolConfig": ".config",
    "AsyncRestXmlProtocolClient": ".aio.client",
    "AsyncRestXmlProtocolConfig": ".aio.config",
}


def __getattr__(name: str) -> Any:
    if name in _EXPORTS:
        return getattr(import_module(_EXPORTS[name], __name__), name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
