#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""Waiter rules shared by the sync and async wait loops."""

import math
import random
from collections.abc import Callable, Mapping, Sequence
from copy import copy
from dataclasses import dataclass
from time import monotonic
from types import MappingProxyType
from typing import Any, Final, Literal, Protocol, TypeGuard

from . import _jmespath
from .exceptions import CallError, WaiterFailureError, WaiterTimeoutError
from .schemas import APIOperation, Schema, SchemaExtension
from .traits import WaitableTrait

__all__ = ["WaiterDefinition", "WaiterState", "waiter_definition"]

type _Path = Callable[[Any], Any]
type _AcceptorState = Literal["success", "failure", "retry"]

_DEFAULT_MIN_DELAY: Final = 2
_DEFAULT_MAX_DELAY: Final = 120


@dataclass(frozen=True, slots=True)
class WaiterDefinition:
    """A waiter's delays, in seconds, and its acceptors in the order they're checked."""

    min_delay: float
    max_delay: float
    acceptors: tuple["_Acceptor", ...]


def waiter_definition(operation: APIOperation[Any, Any], name: str) -> WaiterDefinition:
    """Return an operation's waiter, built once from its schema's waitable trait.

    Raises ``ValueError`` if there's no such waiter or the trait is malformed.
    """
    definitions = operation.schema.get_extension(_DEFINITIONS)
    try:
        return definitions[name]
    except KeyError:
        raise ValueError(
            f"Operation {operation.schema.id} has no waiter named {name!r}"
        ) from None


class WaiterState:
    """The deadline, attempts, and request of one wait."""

    __slots__ = (
        "_attempts",
        "_deadline",
        "_definition",
        "_final",
        "_max_delay",
        "_max_wait_time",
        "_min_delay",
        "_name",
        "_operation",
        "_plugins",
        "_request",
    )

    def __init__(
        self,
        request: object,
        operation: APIOperation[Any, Any],
        waiter: str,
        plugins: Sequence[Any] | None,
        *,
        max_wait_time: float,
        min_delay: float | None = None,
        max_delay: float | None = None,
    ) -> None:
        definition = waiter_definition(operation, waiter)
        min_delay = definition.min_delay if min_delay is None else min_delay
        max_delay = definition.max_delay if max_delay is None else max_delay
        for parameter, value in (
            ("max_wait_time", max_wait_time),
            ("min_delay", min_delay),
            ("max_delay", max_delay),
        ):
            if not _is_seconds(value):
                raise ValueError(
                    f"{parameter} must be a positive number of seconds, not {value!r}"
                )
        if min_delay > max_delay:
            raise ValueError(
                f"min_delay ({min_delay}) must not be above max_delay ({max_delay})"
            )
        self._definition = definition
        self._operation = operation
        self._name = waiter
        # Shallow, so the caller's request is never modified.
        self._request = copy(request)
        self._plugins = None if plugins is None else list(plugins)
        self._min_delay = min_delay
        self._max_delay = max_delay
        self._max_wait_time = max_wait_time
        self._deadline = monotonic() + max_wait_time
        self._attempts = 0
        self._final = False

    def next_call(self) -> tuple[Any, list[Any] | None]:
        """Return the next attempt's request and plugins."""
        # Copies, so interceptors can't change later attempts or what matchers read.
        plugins = None if self._plugins is None else list(self._plugins)
        return copy(self._request), plugins

    def accept(self, output: object, error: Exception | None) -> float | None:
        """Check an attempt's outcome against the acceptors.

        Returns None on success or the seconds to sleep before retrying. Raises
        ``WaiterFailureError`` or ``WaiterTimeoutError`` when the wait ends otherwise.
        """
        self._attempts += 1
        for acceptor in self._definition.acceptors:
            if acceptor.matcher.matches(self._request, output, error, self._operation):
                break
        else:
            acceptor = None
        state = (
            acceptor.state
            if acceptor is not None
            else "failure"
            if error is not None
            else "retry"
        )
        match state:
            case "success":
                return None
            case "failure":
                raise WaiterFailureError(
                    self._failure_message(acceptor, output, error),
                    attempts=self._attempts,
                    last_output=output,
                    last_error=error,
                ) from error
            case _:
                return self._retry_delay(output, error)

    def _failure_message(
        self, acceptor: "_Acceptor | None", output: object, error: Exception | None
    ) -> str:
        message = f"Waiter {self._name} failed after {self._attempt_count()}"
        if acceptor is None:
            return f"{message} on an unexpected {type(error).__name__}."
        if acceptor.message is not None and error is None:
            detail = acceptor.message(output)
            if isinstance(detail, list | tuple) and all(
                isinstance(item, str)
                for item in detail  # pyright: ignore[reportUnknownVariableType]
            ):
                detail = "; ".join(detail)  # pyright: ignore[reportUnknownArgumentType]
            if isinstance(detail, str) and detail:
                return f"{message}: {detail}"
        return f"{message}."

    def _retry_delay(self, output: object, error: Exception | None) -> float:
        remaining = self._deadline - monotonic()
        if self._final or remaining <= 0:
            raise WaiterTimeoutError(
                f"Waiter {self._name} timed out after {self._max_wait_time} seconds "
                f"and {self._attempt_count()}.",
                attempts=self._attempts,
                last_output=output,
                last_error=error,
            ) from error
        delay = _backoff(self._attempts, self._min_delay, self._max_delay)
        # Sleep until the limit and make one last attempt.
        if remaining - delay <= self._min_delay:
            self._final = True
            return remaining
        return delay

    def _attempt_count(self) -> str:
        return "1 attempt" if self._attempts == 1 else f"{self._attempts} attempts"


class _Matcher(Protocol):
    def matches(
        self,
        request: object,
        output: object,
        error: Exception | None,
        operation: APIOperation[Any, Any],
    ) -> bool: ...


@dataclass(frozen=True, slots=True)
class _PathMatcher:
    """An ``output`` or ``inputOutput`` matcher, which only matches outputs."""

    path: _Path
    comparator: Callable[[Any], bool]
    input_output: bool

    def matches(
        self,
        request: object,
        output: object,
        error: Exception | None,
        operation: APIOperation[Any, Any],
    ) -> bool:
        if error is not None:
            return False
        value = {"input": request, "output": output} if self.input_output else output
        return self.comparator(self.path(value))


@dataclass(frozen=True, slots=True)
class _SuccessMatcher:
    success: bool

    def matches(
        self,
        request: object,
        output: object,
        error: Exception | None,
        operation: APIOperation[Any, Any],
    ) -> bool:
        return (error is None) is self.success


@dataclass(frozen=True, slots=True)
class _ErrorTypeMatcher:
    """Matches a shape name or error code."""

    name: str

    def matches(
        self,
        request: object,
        output: object,
        error: Exception | None,
        operation: APIOperation[Any, Any],
    ) -> bool:
        if error is None:
            return False
        if (
            isinstance(error, CallError)
            and error.response_metadata.error_code == self.name
        ):
            return True
        return any(
            error_id.name == self.name
            and isinstance(error, operation.error_registry.get(error_id))
            for error_id in operation.error_ids
        )


@dataclass(frozen=True, slots=True)
class _Acceptor:
    state: _AcceptorState
    matcher: _Matcher
    message: _Path | None


def _build_definitions(schema: Schema) -> Mapping[str, WaiterDefinition]:
    trait = schema.get_trait(WaitableTrait)
    if trait is None:
        return MappingProxyType({})
    return MappingProxyType(
        {
            name: _definition(f"Waiter {name} of {schema.id}", waiter)
            for name, waiter in trait.waiters.items()
        }
    )


_DEFINITIONS: Final = SchemaExtension(_build_definitions)


def _definition(label: str, waiter: Any) -> WaiterDefinition:
    return WaiterDefinition(
        min_delay=waiter.get("minDelay", _DEFAULT_MIN_DELAY),
        max_delay=waiter.get("maxDelay", _DEFAULT_MAX_DELAY),
        acceptors=tuple(_acceptor(label, acceptor) for acceptor in waiter["acceptors"]),
    )


def _acceptor(label: str, acceptor: Any) -> _Acceptor:
    ((kind, value),) = acceptor["matcher"].items()
    message = acceptor.get("message")
    return _Acceptor(
        state=acceptor["state"],
        matcher=_matcher(label, kind, value),
        message=None if message is None else _jmespath.compile(message),
    )


def _matcher(label: str, kind: str, value: Any) -> _Matcher:
    match kind:
        case "output" | "inputOutput":
            return _PathMatcher(
                path=_jmespath.compile(value["path"]),
                comparator=_comparator(label, value["comparator"], value["expected"]),
                input_output=kind == "inputOutput",
            )
        case "success":
            return _SuccessMatcher(value)
        case "errorType":
            # An absolute shape ID matches on its name alone.
            return _ErrorTypeMatcher(value.rpartition("#")[2])
        case _:
            raise ValueError(f"{label} has an unsupported {kind!r} matcher")


def _comparator(label: str, comparator: str, expected: str) -> Callable[[Any], bool]:
    match comparator:
        case "stringEquals":
            return lambda result: isinstance(result, str) and result == expected
        case "booleanEquals":
            wanted = expected == "true"
            return lambda result: isinstance(result, bool) and result is wanted
        case "allStringEquals":
            return lambda result: (
                isinstance(result, list | tuple)
                and len(result) > 0  # pyright: ignore[reportUnknownArgumentType]
                and all(
                    isinstance(item, str) and item == expected
                    for item in result  # pyright: ignore[reportUnknownVariableType]
                )
            )
        case "anyStringEquals":
            return lambda result: (
                isinstance(result, list | tuple)
                and any(
                    isinstance(item, str) and item == expected
                    for item in result  # pyright: ignore[reportUnknownVariableType]
                )
            )
        case _:
            raise ValueError(f"{label} has an unsupported {comparator!r} comparator")


def _is_seconds(value: object) -> TypeGuard[float]:
    return (
        isinstance(value, int | float)
        and not isinstance(value, bool)
        and math.isfinite(value)
        and value > 0
    )


def _backoff(attempt: int, min_delay: float, max_delay: float) -> float:
    """The specification's exponential backoff with full jitter, in seconds."""
    ceiling = math.log(max_delay / min_delay) / math.log(2) + 1
    if attempt > ceiling:
        upper = max_delay
    else:
        upper = min(max_delay, min_delay * 2 ** (attempt - 1))
    return min_delay + random.random() * (upper - min_delay)  # noqa: S311 - jitter
