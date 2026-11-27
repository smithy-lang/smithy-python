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
    "ChecksumAlgorithm": "CHECKSUM_ALGORITHM",
    "ChecksumMode": "CHECKSUM_MODE",
    "DescribeNoteInput": "DESCRIBE_NOTE_INPUT",
    "DescribeNoteOutput": "DESCRIBE_NOTE_OUTPUT",
    "GetNoteInput": "GET_NOTE_INPUT",
    "GetNoteOutput": "GET_NOTE_OUTPUT",
    "GetThingInput": "GET_THING_INPUT",
    "GetThingOutput": "GET_THING_OUTPUT",
    "ListNotesInput": "LIST_NOTES_INPUT",
    "ListNotesOutput": "LIST_NOTES_OUTPUT",
    "NoteNotFound": "NOTE_NOT_FOUND",
    "NoteState": "NOTE_STATE",
    "PutNoteInput": "PUT_NOTE_INPUT",
    "PutNoteOutput": "PUT_NOTE_OUTPUT",
    "PutThingInput": "PUT_THING_INPUT",
    "ThingTag": "THING_TAG",
    "EchoInput": "ECHO_INPUT",
    "EchoOutput": "ECHO_OUTPUT",
    "PingInput": "PING_INPUT",
    "PingOutput": "PING_OUTPUT",
    "PutThingOutput": "PUT_THING_OUTPUT",
}

_RENAMES: dict[str, str] = {}

_TARGET_NAMES: dict[str, str] = {}

_OPERATIONS: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "DESCRIBE_NOTE": (
        ("example.features#NoteNotFound",),
        ("smithy.api#noAuth",),
    ),
    "ECHO": (
        (),
        ("smithy.api#httpApiKeyAuth", "smithy.api#noAuth"),
    ),
    "GET_NOTE": (
        (),
        ("smithy.api#httpBearerAuth",),
    ),
    "GET_THING": (
        (),
        ("smithy.api#httpApiKeyAuth",),
    ),
    "LIST_NOTES": (
        (),
        ("smithy.api#noAuth",),
    ),
    "PING": (
        (),
        ("smithy.api#noAuth",),
    ),
    "PUT_NOTE": (
        (),
        ("aws.auth#sigv4", "smithy.api#httpApiKeyAuth", "smithy.api#httpBearerAuth"),
    ),
    "PUT_THING": (
        (),
        ("smithy.api#noAuth",),
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
            "ChecksumAlgorithm",
            "ChecksumMode",
            "DescribeNoteInput",
            "DescribeNoteOutput",
            "EchoInput",
            "EchoOutput",
            "GetNoteInput",
            "GetNoteOutput",
            "GetThingInput",
            "GetThingOutput",
            "ListNotesInput",
            "ListNotesOutput",
            "NoteNotFound",
            "NoteState",
            "PingInput",
            "PingOutput",
            "PutNoteInput",
            "PutNoteOutput",
            "PutThingInput",
            "PutThingOutput",
            "ThingTag",
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
