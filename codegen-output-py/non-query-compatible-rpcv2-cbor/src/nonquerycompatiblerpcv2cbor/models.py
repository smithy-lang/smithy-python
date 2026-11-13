from smithy_core._dynamic_models import ModelRegistry
from smithy_core.exceptions import ModeledError

from ._private import schemas


class ServiceError(ModeledError):
    """
    Base error for all errors in the service.

    Some exceptions do not extend from this class, including synthetic,
    implicit, and shared exception types.
    """


_MODEL_INDEX: dict[str, str] = {}

_RENAMES: dict[str, str] = {}

_TARGET_NAMES: dict[str, str] = {}

_MODEL_NAMES = tuple(_MODEL_INDEX)
__all__ = ("ServiceError", *_MODEL_NAMES)  # pyright: ignore[reportUnsupportedDunderAll]


_registry = ModelRegistry(
    schemas,
    renames=_RENAMES,
    index=_MODEL_INDEX,
    target_names=_TARGET_NAMES,
    shape_names=frozenset(),
    service_error="ServiceError",
)
del schemas, ModelRegistry, ModeledError


def __getattr__(name: str):
    value = _registry.build(name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted({*globals(), *__all__})
