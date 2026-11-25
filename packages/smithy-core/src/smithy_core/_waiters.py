#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""Waiter rules shared by the sync and async wait loops.

The loops in ``smithy_core.waiters`` and ``smithy_core.aio.waiters`` only send the
request this state gives them, report the outcome back to it, and sleep as long as
it says.
"""

import math
import random
from collections.abc import Callable, Mapping, Sequence
from copy import copy
from dataclasses import dataclass
from time import monotonic
from types import MappingProxyType
from typing import Any, Final, Literal, Protocol, TypeGuard, cast

from . import _jmespath
from .exceptions import CallError, WaiterFailureError, WaiterTimeoutError
from .schemas import APIOperation, Schema, SchemaExtension
from .shapes import ShapeID

__all__ = ["WaiterDefinition", "WaiterState", "waiter_definition"]

type _Path = Callable[[Any], Any]
type _AcceptorState = Literal["success", "failure", "retry"]

_WAITABLE: Final = ShapeID("smithy.waiters#waitable")
# The defaults of the waiter structure's minDelay and maxDelay members.
_DEFAULT_MIN_DELAY: Final = 2
_DEFAULT_MAX_DELAY: Final = 120
_STATES: Final = frozenset({"success", "failure", "retry"})


@dataclass(frozen=True, slots=True)
class WaiterDefinition:
    """A waiter's delays, in seconds, and its acceptors in the order they're checked."""

    min_delay: float
    max_delay: float
    acceptors: tuple["_Acceptor", ...]


def waiter_definition(operation: APIOperation[Any, Any], name: str) -> WaiterDefinition:
    """Return a waiter of an operation, as its schema's waitable trait defines it.

    The operation's waiters are built on first use and cached on its schema.

    :raises ValueError: If the operation has no waiter of the name, or its waitable
        trait is malformed or has a path outside the supported JMESPath subset.
    """
    definitions = operation.schema.get_extension(_DEFINITIONS)
    try:
        return definitions[name]
    except KeyError:
        raise ValueError(
            f"Operation {operation.schema.id} has no waiter named {name!r}"
        ) from None


class WaiterState:
    """The attempts and decisions of one wait.

    Holds a shallow snapshot of the request, which each attempt sends a copy of and
    ``inputOutput`` matchers read, and the deadline, so its size doesn't grow with
    the number of attempts.
    """

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
        """
        :raises ValueError: If a time is not a positive number of seconds,
            ``min_delay`` is above ``max_delay``, or the operation has no such
            waiter.
        """
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
        # A shallow copy: the caller's request is never modified, and nested values
        # keep their identity.
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
        # Copies, so that changes to them, by an interceptor for example, don't
        # reach later attempts or the input that matchers read.
        plugins = None if self._plugins is None else list(self._plugins)
        return copy(self._request), plugins

    def accept(self, output: object, error: Exception | None) -> float | None:
        """Record an attempt's outcome and decide what happens next.

        Acceptors are checked in order, and the first that matches sets the state.
        If none matches, an error fails the wait and an output retries it.

        :param output: The attempt's output, or None if it raised an error.
        :param error: The error the attempt raised, or None.
        :returns: None if the wait succeeded, or the seconds to sleep before the
            next attempt.
        :raises WaiterFailureError: If the wait reached its failure state.
        :raises WaiterTimeoutError: If the time limit passed without the wait
            reaching its success or failure state.
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
            return f"{message} on an error no acceptor matched: {type(error).__name__}"
        if acceptor.message is not None and error is None:
            detail = acceptor.message(output)
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
        # Rather than sleep past the limit, make one last attempt at it.
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
    """Matches an error whose shape name or error code is the name.

    The error code covers errors the model doesn't define, and services whose
    codes differ from their errors' shape names. An absolute shape ID matches only
    the modeled error with that ID.
    """

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
        if "#" in self.name:
            return any(
                str(error_id) == self.name
                and isinstance(error, operation.error_registry.get(error_id))
                for error_id in operation.error_ids
            )
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
    trait = schema.get_trait(_WAITABLE)
    if trait is None:
        return MappingProxyType({})
    waiters = _structure(trait.document_value, f"The waitable trait of {schema.id}")
    return MappingProxyType(
        {
            name: _definition(f"Waiter {name} of {schema.id}", waiter)
            for name, waiter in waiters.items()
        }
    )


_DEFINITIONS: Final = SchemaExtension(_build_definitions)


def _structure(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} is not a structure")
    return cast("Mapping[str, object]", value)


def _definition(label: str, waiter: object) -> WaiterDefinition:
    members = _structure(waiter, label)
    min_delay = members.get("minDelay", _DEFAULT_MIN_DELAY)
    max_delay = members.get("maxDelay", _DEFAULT_MAX_DELAY)
    if not _is_seconds(min_delay) or not _is_seconds(max_delay):
        raise ValueError(f"{label} has a minDelay or maxDelay that is not positive")
    if min_delay > max_delay:
        raise ValueError(f"{label} has a minDelay above its maxDelay")
    acceptors = members.get("acceptors")
    if not isinstance(acceptors, Sequence) or isinstance(acceptors, str):
        raise ValueError(f"{label} has no acceptors")
    return WaiterDefinition(
        min_delay=min_delay,
        max_delay=max_delay,
        acceptors=tuple(
            _acceptor(label, acceptor)
            for acceptor in cast("Sequence[object]", acceptors)
        ),
    )


def _acceptor(label: str, acceptor: object) -> _Acceptor:
    members = _structure(acceptor, f"An acceptor of {label}")
    state = members.get("state")
    if state not in _STATES:
        raise ValueError(f"{label} has an acceptor with the unknown state {state!r}")
    matcher = _structure(members.get("matcher"), f"A matcher of {label}")
    if len(matcher) != 1:
        raise ValueError(f"{label} has a matcher that doesn't set exactly one member")
    ((kind, value),) = matcher.items()
    message = members.get("message")
    if message is not None and not isinstance(message, str):
        raise ValueError(f"{label} has an acceptor message that is not a path")
    return _Acceptor(
        state=cast("_AcceptorState", state),
        matcher=_matcher(label, kind, value),
        message=None if message is None else _jmespath.compile(message),
    )


def _matcher(label: str, kind: str, value: object) -> _Matcher:
    match kind:
        case "output" | "inputOutput":
            members = _structure(value, f"A {kind} matcher of {label}")
            path, expected = members.get("path"), members.get("expected")
            if not isinstance(path, str) or not isinstance(expected, str):
                raise ValueError(f"{label} has a {kind} matcher without a path")
            return _PathMatcher(
                path=_jmespath.compile(path),
                comparator=_comparator(label, members.get("comparator"), expected),
                input_output=kind == "inputOutput",
            )
        case "success" if isinstance(value, bool):
            return _SuccessMatcher(value)
        case "errorType" if isinstance(value, str):
            return _ErrorTypeMatcher(value)
        case _:
            raise ValueError(f"{label} has an unsupported {kind!r} matcher")


def _comparator(label: str, comparator: object, expected: str) -> Callable[[Any], bool]:
    match comparator:
        case "stringEquals":
            return lambda result: isinstance(result, str) and result == expected
        case "booleanEquals" if expected in ("true", "false"):
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
            raise ValueError(
                f"{label} has the unsupported comparator {comparator!r} for "
                f"{expected!r}"
            )


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
