# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0


from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Literal

__all__ = [
    "UNSET",
    "ConfigSource",
    "FieldSpec",
    "Resolved",
    "ResponseChecksumValidation",
    "normalize_response_checksum_validation",
]


class _UnsetType:
    def __repr__(self) -> str:
        return "UNSET"

    def __bool__(self) -> bool:
        return False


UNSET = _UnsetType()


class ConfigSource(StrEnum):
    """Where a resolved config value came from."""

    ENV = "env"
    PROFILE = "profile"
    DEFAULT = "default"
    OVERRIDE = "override"


@dataclass(frozen=True, kw_only=True)
class Resolved[T]:
    """A resolved config value paired with its provenance source."""

    value: T
    source: ConfigSource


@dataclass(frozen=True, kw_only=True)
class FieldSpec:
    """Specification for a single config field.

    Carries everything the resolution pipeline needs to resolve,
    validate, and default a field.

    """

    default: Any = UNSET
    """Value used if no resolver runs or all providers return unresolved."""

    default_factory: Callable[[], Any] | None = None
    """Factory for mutable defaults (lists, dicts) that need a fresh instance per config."""

    resolver: Callable[..., Awaitable[Resolved[Any]]] | None = None
    """Async function that resolves the field from env/profile/etc."""

    validator: Callable[[Any], None] | None = None
    """Function that validates the resolved value. Raises on invalid input."""

    converter: Callable[[Any], Any] | None = None
    """Normalizes an explicit override value before it is set.

    Applied only to ``overrides`` values, not to resolver or default values.
    """

    def __post_init__(self) -> None:
        has_default = self.default is not UNSET
        has_factory = self.default_factory is not None
        if has_default and has_factory:
            raise ValueError(
                "FieldSpec: cannot set both 'default' and 'default_factory'"
            )
        if not has_default and not has_factory:
            raise ValueError(
                "FieldSpec: exactly one of 'default' or 'default_factory' must be set"
            )


type ResponseChecksumValidation = Literal["when_supported", "when_required"]
"""When to validate the checksums of response payloads.

* ``when_supported``: validate the response payload of every operation that models
  response checksums, as long as one of the modeled algorithms is supported.
* ``when_required``: only validate a response payload when the caller enabled
  validation on the request, such as by setting ``checksum_mode`` to ``ENABLED``.

Values are case-insensitive.
"""


def normalize_response_checksum_validation(value: Any) -> Any:
    """Lowercase a ``ResponseChecksumValidation`` value, since it's case-insensitive.

    Values that aren't strings are returned unchanged for the validator to reject.
    """
    return value.lower() if isinstance(value, str) else value
