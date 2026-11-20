from importlib import import_module
from typing import TYPE_CHECKING, Any

__version__: str = "0.0.1"

if TYPE_CHECKING:
    from .aio.client import AsyncFieldNotesClient
    from .aio.config import AsyncFieldNotesConfig
    from .client import FieldNotesClient
    from .config import FieldNotesConfig

__all__ = [
    "AsyncFieldNotesClient",
    "AsyncFieldNotesConfig",
    "FieldNotesClient",
    "FieldNotesConfig",
]

_EXPORTS = {
    "FieldNotesClient": ".client",
    "FieldNotesConfig": ".config",
    "AsyncFieldNotesClient": ".aio.client",
    "AsyncFieldNotesConfig": ".aio.config",
}


def __getattr__(name: str) -> Any:
    if name in _EXPORTS:
        return getattr(import_module(_EXPORTS[name], __name__), name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
