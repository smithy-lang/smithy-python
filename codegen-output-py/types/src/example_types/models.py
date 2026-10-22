from __future__ import annotations

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
    "GetExampleInput": "GET_EXAMPLE_INPUT",
    "GetExampleOutput": "GET_EXAMPLE_OUTPUT",
    "ExampleError": "EXAMPLE_ERROR",
    "RenamedExample": "RENAMED_EXAMPLE",
    "ExampleValue": "EXAMPLE_VALUE",
    "ExampleValueText": "EXAMPLE_VALUE",
    "ExampleValueNumber": "EXAMPLE_VALUE",
    "ExampleValueEmpty": "EXAMPLE_VALUE",
    "ExampleValueUnknown": "EXAMPLE_VALUE",
    "Status": "STATUS",
    "Code": "CODE",
}

_RENAMES = {
    "RenamedExample": "RENAMED_EXAMPLE",
    "ExampleValue": "EXAMPLE_VALUE",
}

_TARGET_NAMES = {
    "example#Example": "RenamedExample",
    "example#Value": "ExampleValue",
}

_MODEL_NAMES = (*tuple(_MODEL_INDEX), "Unit")
__all__ = ("ServiceError", *_MODEL_NAMES)


_registry = ModelRegistry(
    schemas,
    renames=_RENAMES,
    index=_MODEL_INDEX,
    target_names=_TARGET_NAMES,
    shape_names=frozenset(
        {
            "Code",
            "ExampleError",
            "ExampleValue",
            "GetExampleInput",
            "GetExampleOutput",
            "RenamedExample",
            "Status",
            "Unit",
        }
    ),
    service_error="ServiceError",
)
del schemas, ModelRegistry, ModeledError


def __getattr__(name: str):
    value = _registry.build(name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted({*globals(), *__all__})
