#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# This ruff check warns against using the assert statement, which can be stripped out
# when running Python with certain (common) optimization settings. Assert is used here
# for trait values. Since these are always generated, we can be fairly confident that
# they're correct regardless, so it's okay if the checks are stripped out.
# ruff: noqa: S101

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, ClassVar

from .shapes import ShapeID
from .types import PathPattern, TimestampFormat

if TYPE_CHECKING:
    from .documents import DocumentValue


@dataclass(kw_only=True, frozen=True, slots=True)
class DynamicTrait:
    """A component that can be attached to a schema to describe additional information
    about it.

    Typed traits can be used by creating a :py:class:`Trait` subclass.
    """

    id: ShapeID
    """The ID of the trait."""

    document_value: "DocumentValue" = None
    """The value of the trait."""


@dataclass(init=False, frozen=True)
class Trait:
    """A component that can be attached to a schema to describe additional information
    about it.

    This is a base class that registers subclasses. Any known subclasses will
    automatically be used when constructing schemas. Any unknown traits may instead be
    created as a :py:class:`DynamicTrait`.

    The `id` property of subclasses is set during subclass creation by
    `__init_subclass__`, so it is not necessary for subclasses to set it manually.
    """

    _REGISTRY: ClassVar[dict[ShapeID, type["Trait"]]] = {}

    id: ClassVar[ShapeID]
    """The ID of the trait."""

    document_value: "DocumentValue" = None
    """The value of the trait as a DocumentValue."""

    def __init_subclass__(cls, id: ShapeID) -> None:
        cls.id = id
        Trait._REGISTRY[id] = cls

    def __init__(self, value: "DocumentValue | DynamicTrait" = None):
        if type(self) is Trait:
            raise TypeError(
                "Only subclasses of Trait may be directly instantiated. "
                "Use DynamicTrait for traits without a concrete class."
            )

        if isinstance(value, DynamicTrait):
            if value.id != self.id:
                raise ValueError(
                    f"Attempted to instantiate an instance of {type(self)} from an "
                    f"invalid ID. Expected {self.id} but found {value.id}."
                )
            # Note that setattr is needed because it's a frozen (read-only) dataclass
            object.__setattr__(self, "document_value", value.document_value)
        else:
            object.__setattr__(self, "document_value", value)

    # Dynamically creates a subclass instance based on the trait id
    @staticmethod
    def new(id: ShapeID, value: "DocumentValue" = None) -> "Trait | DynamicTrait":
        """Dynamically create a new trait of the given ID.

        If the ID corresponds to a known Trait class, that class will be instantiated
        and returned. Otherwise, a :py:class:`DynamicTrait` will be returned.

        :returns: A trait of the given ID with the given value.
        """
        if (cls := Trait._REGISTRY.get(id, None)) is not None:
            return cls(value)
        return DynamicTrait(id=id, document_value=value)


@dataclass(init=False, frozen=True)
class DefaultTrait(Trait, id=ShapeID("smithy.appi#default")):
    @property
    def value(self) -> "DocumentValue":
        return self.document_value


@dataclass(init=False, frozen=True)
class SparseTrait(Trait, id=ShapeID("smithy.api#sparse")):
    def __post_init__(self):
        assert self.document_value is None


@dataclass(init=False, frozen=True)
class TimestampFormatTrait(Trait, id=ShapeID("smithy.api#timestampFormat")):
    format: TimestampFormat

    def __init__(self, value: "DocumentValue | DynamicTrait" = None):
        super().__init__(value)
        assert isinstance(self.document_value, str)
        object.__setattr__(self, "format", TimestampFormat(self.document_value))


class ErrorFault(Enum):
    CLIENT = "client"
    SERVER = "server"


@dataclass(init=False, frozen=True)
class ErrorTrait(Trait, id=ShapeID("smithy.api#error")):
    fault: ErrorFault

    def __init__(self, value: "DocumentValue | DynamicTrait" = None):
        super().__init__(value)
        assert isinstance(self.document_value, str)
        object.__setattr__(self, "fault", ErrorFault(self.document_value))


@dataclass(init=False, frozen=True)
class RequiredTrait(Trait, id=ShapeID("smithy.api#required")):
    def __post_init__(self):
        assert self.document_value is None


@dataclass(init=False, frozen=True)
class InternalTrait(Trait, id=ShapeID("smithy.api#internal")):
    def __post_init__(self):
        assert self.document_value is None


@dataclass(init=False, frozen=True)
class SensitiveTrait(Trait, id=ShapeID("smithy.api#sensitive")):
    def __post_init__(self):
        assert self.document_value is None


@dataclass(init=False, frozen=True)
class StreamingTrait(Trait, id=ShapeID("smithy.api#streaming")):
    def __post_init__(self):
        assert self.document_value is None


@dataclass(init=False, frozen=True)
class UnitTypeTrait(Trait, id=ShapeID("smithy.api#UnitTypeTrait")):
    def __post_init__(self):
        assert self.document_value is None


@dataclass(init=False, frozen=True)
class MediaTypeTrait(Trait, id=ShapeID("smithy.api#mediaType")):
    document_value: str | None = None

    def __post_init__(self):
        assert isinstance(self.document_value, str)

    @property
    def value(self) -> str:
        return self.document_value  # type: ignore


@dataclass(init=False, frozen=True)
class EventHeaderTrait(Trait, id=ShapeID("smithy.api#eventheader")):
    def __post_init__(self):
        assert self.document_value is None


@dataclass(init=False, frozen=True)
class EventPayloadTrait(Trait, id=ShapeID("smithy.api#eventPayload")):
    def __post_init__(self):
        assert self.document_value is None


@dataclass(init=False, frozen=True)
class JSONNameTrait(Trait, id=ShapeID("smithy.api#jsonName")):
    document_value: str | None = None

    def __post_init__(self):
        assert isinstance(self.document_value, str)

    @property
    def value(self) -> str:
        return self.document_value  # type: ignore


@dataclass(init=False, frozen=True)
class IdempotencyTokenTrait(Trait, id=ShapeID("smithy.api#IdempotencyToken")):
    def __post_init__(self):
        assert self.document_value is None


# TODO: Get all this moved over to the http package
@dataclass(init=False, frozen=True)
class HTTPTrait(Trait, id=ShapeID("smithy.api#http")):
    path: PathPattern = field(repr=False, hash=False, compare=False)
    code: int = field(repr=False, hash=False, compare=False)
    query: str | None = field(default=None, repr=False, hash=False, compare=False)

    def __init__(self, value: "DocumentValue | DynamicTrait" = None):
        super().__init__(value)
        assert isinstance(self.document_value, Mapping)
        assert isinstance(self.document_value["method"], str)

        code = self.document_value.get("code", 200)
        assert isinstance(code, int)
        object.__setattr__(self, "code", code)

        uri = self.document_value["uri"]
        assert isinstance(uri, str)
        parts = uri.split("?", 1)

        object.__setattr__(self, "path", PathPattern(parts[0]))
        object.__setattr__(self, "query", parts[1] if len(parts) == 2 else None)

    @property
    def method(self) -> str:
        return self.document_value["method"]  # type: ignore


@dataclass(init=False, frozen=True)
class HTTPErrorTrait(Trait, id=ShapeID("smithy.api#httpError")):
    def __post_init__(self):
        assert isinstance(self.document_value, int)

    @property
    def code(self) -> int:
        return self.document_value  # type: ignore


@dataclass(init=False, frozen=True)
class HTTPHeaderTrait(Trait, id=ShapeID("smithy.api#httpHeader")):
    def __post_init__(self):
        assert isinstance(self.document_value, str)

    @property
    def key(self) -> str:
        return self.document_value  # type: ignore


@dataclass(init=False, frozen=True)
class HTTPLabelTrait(Trait, id=ShapeID("smithy.api#httpLabel")):
    def __post_init__(self):
        assert self.document_value is None


@dataclass(init=False, frozen=True)
class HTTPPayloadTrait(Trait, id=ShapeID("smithy.api#httpPayload")):
    def __post_init__(self):
        assert self.document_value is None


@dataclass(init=False, frozen=True)
class HTTPPrefixHeadersTrait(Trait, id=ShapeID("smithy.api#httpPrefixHeaders")):
    def __post_init__(self):
        assert isinstance(self.document_value, str)

    @property
    def prefix(self) -> str:
        return self.document_value  # type: ignore


@dataclass(init=False, frozen=True)
class HTTPQueryTrait(Trait, id=ShapeID("smithy.api#httpQuery")):
    def __post_init__(self):
        assert isinstance(self.document_value, str)

    @property
    def key(self) -> str:
        return self.document_value  # type: ignore


@dataclass(init=False, frozen=True)
class HTTPQueryParamsTrait(Trait, id=ShapeID("smithy.api#httpQueryParams")):
    def __post_init__(self):
        assert self.document_value is None


@dataclass(init=False, frozen=True)
class HTTPResponseCodeTrait(Trait, id=ShapeID("smithy.api#httpResponseCode")):
    def __post_init__(self):
        assert self.document_value is None


@dataclass(init=False, frozen=True)
class HTTPChecksumRequiredTrait(Trait, id=ShapeID("smithy.api#httpChecksumRequired")):
    def __post_init__(self):
        assert self.document_value is None


@dataclass(init=False, frozen=True)
class EndpointTrait(Trait, id=ShapeID("smithy.api#endpoint")):
    def __post_init__(self):
        assert isinstance(self.document_value, str)

    @property
    def host_prefix(self) -> str:
        return self.document_value["hostPrefix"]  # type: ignore


@dataclass(init=False, frozen=True)
class HostLabelTrait(Trait, id=ShapeID("smithy.api#hostLabel")):
    def __post_init__(self):
        assert self.document_value is None
