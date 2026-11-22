from importlib import import_module
from typing import TYPE_CHECKING, Any

__version__: str = "0.0.1"

if TYPE_CHECKING:
    from .aio.client import AsyncRestXmlProtocolNamespaceClient
    from .aio.config import AsyncRestXmlProtocolNamespaceConfig
    from .client import RestXmlProtocolNamespaceClient
    from .config import RestXmlProtocolNamespaceConfig

__all__ = [
    "AsyncRestXmlProtocolNamespaceClient",
    "AsyncRestXmlProtocolNamespaceConfig",
    "RestXmlProtocolNamespaceClient",
    "RestXmlProtocolNamespaceConfig",
]

_EXPORTS = {
    "RestXmlProtocolNamespaceClient": ".client",
    "RestXmlProtocolNamespaceConfig": ".config",
    "AsyncRestXmlProtocolNamespaceClient": ".aio.client",
    "AsyncRestXmlProtocolNamespaceConfig": ".aio.config",
}


def __getattr__(name: str) -> Any:
    if name in _EXPORTS:
        return getattr(import_module(_EXPORTS[name], __name__), name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
