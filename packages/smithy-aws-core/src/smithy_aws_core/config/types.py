# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0


from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Literal

__all__ = [
    "UNSET",
    "ConfigSource",
    "FieldSpec",
    "RequestChecksumCalculation",
    "Resolved",
    "ResponseChecksumValidation",
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

    resolver: Callable[..., Any] | None = None
    """Function that resolves the field from env/profile/etc.

    It returns a :py:data:`smithy_core.program.Program` of a ``Resolved`` value,
    which both sync and async configs drive. Sync configs also take a function that
    returns ``Resolved``; async configs also take one that returns an awaitable.
    """

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


type RequestChecksumCalculation = Literal["when_supported", "when_required"]
"""When to calculate checksums of request payloads.

* ``when_supported``: calculate a checksum for the request payload of every
  operation that supports request checksums.
* ``when_required``: only calculate a checksum when the operation requires one, or
  when the caller chose a checksum algorithm on the request.

Values from the environment and shared config files are case-insensitive.
"""


type ResponseChecksumValidation = Literal["when_supported", "when_required"]
"""When to validate the checksums of response payloads.

* ``when_supported``: validate the response payload of every operation that models
  response checksums, as long as one of the modeled algorithms is supported.
* ``when_required``: only validate a response payload when the caller enabled
  validation on the request, such as by setting ``checksum_mode`` to ``ENABLED``.

Values from the environment and shared config files are case-insensitive.
"""
