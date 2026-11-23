from smithy_core._dynamic_models import ModelRegistry
from smithy_core.exceptions import ModeledError

from ._private import schemas


class ServiceError(ModeledError):
    """
    Base error for all errors in the service.

    Some exceptions do not extend from this class, including synthetic,
    implicit, and shared exception types.
    """


_MODEL_INDEX = {
    "CustomCodeError": "CUSTOM_CODE_ERROR",
    "NoCustomCodeError": "NO_CUSTOM_CODE_ERROR",
    "QueryCompatibleOperationInput": "QUERY_COMPATIBLE_OPERATION_INPUT",
    "QueryCompatibleOperationOutput": "QUERY_COMPATIBLE_OPERATION_OUTPUT",
}

_RENAMES: dict[str, str] = {}

_TARGET_NAMES: dict[str, str] = {}

_OPERATIONS: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "QUERY_COMPATIBLE_OPERATION": (
        (
            "aws.protocoltests.json10#CustomCodeError",
            "aws.protocoltests.json10#NoCustomCodeError",
        ),
        ("aws.auth#sigv4",),
    ),
}

_MODEL_NAMES = tuple(_MODEL_INDEX)
__all__ = ("ServiceError", *_MODEL_NAMES, *_OPERATIONS)  # pyright: ignore[reportUnsupportedDunderAll]


_registry = ModelRegistry(
    schemas,
    renames=_RENAMES,
    index=_MODEL_INDEX,
    target_names=_TARGET_NAMES,
    shape_names=frozenset(
        {
            "CustomCodeError",
            "NoCustomCodeError",
            "QueryCompatibleOperationInput",
            "QueryCompatibleOperationOutput",
        }
    ),
    service_error="ServiceError",
)
del schemas, ModelRegistry, ModeledError


def __getattr__(name: str):
    if (data := _OPERATIONS.get(name)) is not None:
        return globals().setdefault(name, _registry.build_operation(name, *data))
    value = _registry.build(name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted({*globals(), *__all__})
