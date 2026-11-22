from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .client import AsyncRestXmlProtocolNamespaceClient
    from .config import AsyncRestXmlProtocolNamespaceConfig

__all__ = ["AsyncRestXmlProtocolNamespaceClient", "AsyncRestXmlProtocolNamespaceConfig"]

_EXPORTS = {
    "AsyncRestXmlProtocolNamespaceClient": ".client",
    "AsyncRestXmlProtocolNamespaceConfig": ".config",
}


def __getattr__(name: str) -> Any:
    if name in _EXPORTS:
        return getattr(import_module(_EXPORTS[name], __name__), name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
