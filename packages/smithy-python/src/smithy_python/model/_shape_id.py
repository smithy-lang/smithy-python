# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Shape identifiers."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final, Self

from ..exceptions import InvalidShapeIdError

_IDENTIFIER: Final = r"(?:[A-Za-z]|_+[A-Za-z0-9])[A-Za-z0-9_]*"
_IDENTIFIER_RE: Final = re.compile(_IDENTIFIER)
_NAMESPACE_RE: Final = re.compile(rf"{_IDENTIFIER}(?:\.{_IDENTIFIER})*")

PRELUDE_NAMESPACE: Final = "smithy.api"


@dataclass(frozen=True, slots=True)
class ShapeId:
    """A Smithy shape ID: ``namespace#Name`` or ``namespace#Name$member``.

    Shape IDs are hashable and totally ordered by (namespace, name, member),
    with the root shape sorting before its members.
    """

    namespace: str
    name: str
    member: str | None = None

    def __post_init__(self) -> None:
        if not _NAMESPACE_RE.fullmatch(self.namespace):
            raise InvalidShapeIdError(
                f"Invalid shape ID namespace {self.namespace!r} in {self._raw()!r}"
            )
        if not _IDENTIFIER_RE.fullmatch(self.name):
            raise InvalidShapeIdError(
                f"Invalid shape ID name {self.name!r} in {self._raw()!r}"
            )
        if self.member is not None and not _IDENTIFIER_RE.fullmatch(self.member):
            raise InvalidShapeIdError(
                f"Invalid shape ID member {self.member!r} in {self._raw()!r}"
            )

    @classmethod
    def from_string(cls, value: str, *, default_namespace: str | None = None) -> Self:
        """Parse an absolute or relative shape ID.

        Relative IDs (no ``#``) are resolved against ``default_namespace``;
        without one they are rejected.
        """
        if "#" in value:
            namespace, _, rest = value.partition("#")
            if "#" in rest:
                raise InvalidShapeIdError(f"Invalid shape ID {value!r}")
        elif default_namespace is not None:
            namespace, rest = default_namespace, value
        else:
            raise InvalidShapeIdError(
                f"Invalid shape ID {value!r}: expected an absolute shape ID "
                "of the form namespace#Name"
            )
        name, sep, member = rest.partition("$")
        try:
            return cls(namespace, name, member if sep else None)
        except InvalidShapeIdError:
            raise InvalidShapeIdError(f"Invalid shape ID {value!r}") from None

    @property
    def is_member(self) -> bool:
        """Whether this ID refers to a member."""
        return self.member is not None

    @property
    def root(self) -> ShapeId:
        """This ID without its member component."""
        if self.member is None:
            return self
        return ShapeId(self.namespace, self.name)

    def with_member(self, member: str) -> ShapeId:
        """Return the ID of ``member`` within this shape."""
        return ShapeId(self.namespace, self.name, member)

    def __str__(self) -> str:
        return self._raw()

    def _raw(self) -> str:
        base = f"{self.namespace}#{self.name}"
        return base if self.member is None else f"{base}${self.member}"

    def _key(self) -> tuple[str, str, bool, str]:
        return (self.namespace, self.name, self.member is not None, self.member or "")

    def __lt__(self, other: ShapeId) -> bool:
        return self._key() < other._key()

    def __le__(self, other: ShapeId) -> bool:
        return self._key() <= other._key()

    def __gt__(self, other: ShapeId) -> bool:
        return self._key() > other._key()

    def __ge__(self, other: ShapeId) -> bool:
        return self._key() >= other._key()


def as_shape_id(
    value: ShapeId | str, *, default_namespace: str | None = None
) -> ShapeId:
    """Coerce a string or ShapeId to a ShapeId."""
    if isinstance(value, ShapeId):
        return value
    return ShapeId.from_string(value, default_namespace=default_namespace)
