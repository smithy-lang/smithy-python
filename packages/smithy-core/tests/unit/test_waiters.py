#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import asyncio
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import pytest
from smithy_core import _waiters
from smithy_core import waiters as sync_waiters
from smithy_core.aio import waiters as async_waiters
from smithy_core.exceptions import (
    CallError,
    ModeledError,
    WaiterError,
    WaiterFailureError,
    WaiterTimeoutError,
)
from smithy_core.response import ErrorResponseMetadata
from smithy_core.schemas import APIOperation
from smithy_core.shapes import ShapeID, ShapeType

_NS = "com.example"


@dataclass
class _Input:
    name: str | None = None
    tags: list[str] = field(default_factory=list[str])


@dataclass
class _Thing:
    status: str | None = None


@dataclass
class _Output:
    status: str | None = None
    ready: bool | None = None
    things: list[_Thing] | None = None
    reason: str | None = None


@dataclass(kw_only=True)
class _NotFound(ModeledError):
    pass


class _Registry:
    def build(self, name: str) -> type:
        return {"NotFound": _NotFound}[name]


def _path(path: str, expected: str, comparator: str = "stringEquals") -> Any:
    return {"output": {"path": path, "expected": expected, "comparator": comparator}}


_WAITERS: dict[str, Any] = {
    "ThingReady": {
        "minDelay": 2,
        "maxDelay": 10,
        "acceptors": [
            {"state": "success", "matcher": _path("Status", "READY")},
            {
                "state": "failure",
                "matcher": _path("Status", "BROKEN"),
                "message": "Reason",
            },
            {"state": "failure", "matcher": _path("Status", "GONE")},
            {"state": "retry", "matcher": {"errorType": "Throttled"}},
        ],
    },
    "ThingGone": {
        "acceptors": [
            {"state": "success", "matcher": {"errorType": "NotFound"}},
        ],
    },
    "ExactlyGone": {
        "acceptors": [
            {"state": "success", "matcher": {"errorType": "com.example#NotFound"}},
        ],
    },
    "OtherGone": {
        "acceptors": [
            {"state": "success", "matcher": {"errorType": "com.other#NotFound"}},
        ],
    },
    "AllReady": {
        "acceptors": [
            {
                "state": "success",
                "matcher": _path("Things[].Status", "READY", "allStringEquals"),
            },
            {
                "state": "failure",
                "matcher": _path("Things[].Status", "BROKEN", "anyStringEquals"),
                "message": "Things[].Status",
            },
        ],
    },
    "Flagged": {
        "acceptors": [
            {"state": "success", "matcher": _path("Ready", "true", "booleanEquals")},
            {"state": "failure", "matcher": {"success": False}},
        ],
    },
    "Echoed": {
        "acceptors": [
            {
                "state": "success",
                "matcher": {
                    "inputOutput": {
                        "path": "input.Name == output.Status",
                        "expected": "true",
                        "comparator": "booleanEquals",
                    }
                },
            },
            {"state": "success", "matcher": {"success": True}},
        ],
    },
}


def _operation(waiters: Any = _WAITERS) -> APIOperation[Any, Any]:
    structure = ShapeType.STRUCTURE.value
    traits = {} if waiters is None else {"smithy.waiters#waitable": waiters}
    return APIOperation(
        static_schema=(
            ShapeType.OPERATION.value,
            _NS,
            "GetThing",
            traits,
            (structure, _NS, "GetThingInput", 0, (), ()),
            (structure, _NS, "GetThingOutput", 0, (), ()),
            (),
        ),
        model_registry=_Registry(),
        error_ids=(ShapeID(f"{_NS}#NotFound"),),
    )


_OPERATION = _operation()


class _Clock:
    """Stands in for the monotonic clock, advancing only when the waiter sleeps
    or a call takes time."""

    def __init__(self) -> None:
        self.now = 1000.0
        self.sleeps: list[float] = []

    def monotonic(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds

    async def sleep_async(self, seconds: float) -> None:
        self.sleep(seconds)


@pytest.fixture
def clock(monkeypatch: pytest.MonkeyPatch) -> _Clock:
    clock = _Clock()
    monkeypatch.setattr(_waiters, "monotonic", clock.monotonic)
    monkeypatch.setattr(sync_waiters, "sleep", clock.sleep)
    monkeypatch.setattr(async_waiters, "sleep", clock.sleep_async)
    # Delays take the top of each jitter range.
    monkeypatch.setattr(_waiters.random, "random", lambda: 1.0)
    return clock


class _Service:
    """Returns or raises the given results in order, recording each call."""

    def __init__(self, clock: _Clock, *results: object, call_time: float = 0.0) -> None:
        self.clock = clock
        self.results = list(results)
        self.call_time = call_time
        self.calls: list[tuple[_Input, list[Any] | None]] = []

    def __call__(self, request: _Input, *, plugins: list[Any] | None) -> Any:
        self.calls.append((request, plugins))
        self.clock.now += self.call_time
        result = self.results.pop(0) if len(self.results) > 1 else self.results[0]
        if isinstance(result, Exception):
            raise result
        return result

    async def call_async(self, request: _Input, *, plugins: list[Any] | None) -> Any:
        return self(request, plugins=plugins)


def _wait(
    aio: bool,
    service: _Service,
    waiter: str,
    request: _Input | None = None,
    plugins: list[Any] | None = None,
    operation: APIOperation[Any, Any] = _OPERATION,
    **options: Any,
) -> Any:
    options.setdefault("max_wait_time", 60)
    # The fakes aren't serializable shapes.
    payload: Any = request or _Input(name="n")
    if aio:
        return asyncio.run(
            async_waiters.wait_async(
                payload, operation, service.call_async, waiter, plugins, **options
            )
        )
    return sync_waiters.wait(payload, operation, service, waiter, plugins, **options)


_AIO = pytest.mark.parametrize("aio", [False, True], ids=["sync", "async"])


@_AIO
def test_returns_the_output_that_matched(aio: bool, clock: _Clock) -> None:
    ready = _Output(status="READY")
    service = _Service(clock, _Output(status="CREATING"), ready)
    plugin = object()
    request = _Input(name="n")

    assert _wait(aio, service, "ThingReady", request, [plugin]) is ready

    assert len(service.calls) == 2
    (first, first_plugins), (second, second_plugins) = service.calls
    assert first == request and first is not request and first is not second
    assert first_plugins == [plugin] and first_plugins is not second_plugins
    assert clock.sleeps == [2]


@_AIO
def test_delays_back_off_to_max_delay(aio: bool, clock: _Clock) -> None:
    service = _Service(clock, *([_Output()] * 6), _Output(status="READY"))

    _wait(aio, service, "ThingReady", max_wait_time=1000)

    assert clock.sleeps == [2, 4, 8, 10, 10, 10]


@_AIO
def test_callers_override_the_delays(aio: bool, clock: _Clock) -> None:
    service = _Service(clock, *([_Output()] * 3), _Output(status="READY"))

    _wait(aio, service, "ThingReady", min_delay=0.5, max_delay=1.5, max_wait_time=100)

    assert clock.sleeps == [0.5, 1, 1.5]


def test_delays_are_jittered_from_min_delay(
    monkeypatch: pytest.MonkeyPatch, clock: _Clock
) -> None:
    monkeypatch.setattr(_waiters.random, "random", lambda: 0.0)
    service = _Service(clock, *([_Output()] * 3), _Output(status="READY"))

    _wait(False, service, "ThingReady", max_wait_time=100)

    assert clock.sleeps == [2, 2, 2]


@_AIO
def test_makes_one_last_attempt_at_the_limit(aio: bool, clock: _Clock) -> None:
    service = _Service(clock, _Output(), call_time=1)

    with pytest.raises(WaiterTimeoutError) as raised:
        _wait(aio, service, "ThingReady", max_wait_time=10)

    # The second delay would leave less than min_delay, so it runs to the limit.
    assert clock.sleeps == [2, 6]
    assert raised.value.attempts == 3
    assert raised.value.last_output == _Output()
    assert raised.value.last_error is None
    assert "ThingReady timed out after 10 seconds and 3 attempts" in str(raised.value)


@_AIO
def test_the_last_attempt_can_still_succeed(aio: bool, clock: _Clock) -> None:
    ready = _Output(status="READY")
    service = _Service(clock, _Output(), _Output(), ready, call_time=1)

    assert _wait(aio, service, "ThingReady", max_wait_time=10) is ready
    assert clock.sleeps == [2, 6]


@_AIO
def test_times_out_without_sleeping_past_the_limit(aio: bool, clock: _Clock) -> None:
    service = _Service(clock, _Output(), call_time=5)

    with pytest.raises(WaiterTimeoutError) as raised:
        _wait(aio, service, "ThingReady", max_wait_time=4)

    assert clock.sleeps == []
    assert raised.value.attempts == 1


@_AIO
def test_a_failure_acceptor_fails_with_its_message(aio: bool, clock: _Clock) -> None:
    broken = _Output(status="BROKEN", reason="The disk is full.")
    service = _Service(clock, broken)

    with pytest.raises(WaiterFailureError) as raised:
        _wait(aio, service, "ThingReady")

    assert str(raised.value) == (
        "Waiter ThingReady failed after 1 attempt: The disk is full."
    )
    assert raised.value.attempts == 1
    assert raised.value.last_output is broken
    assert raised.value.last_error is None


@_AIO
def test_a_failure_acceptor_without_a_message(aio: bool, clock: _Clock) -> None:
    service = _Service(clock, _Output(), _Output(status="GONE"))

    with pytest.raises(WaiterFailureError) as raised:
        _wait(aio, service, "ThingReady")

    assert str(raised.value) == "Waiter ThingReady failed after 2 attempts."


@_AIO
def test_an_unmatched_error_fails(aio: bool, clock: _Clock) -> None:
    error = CallError("Access denied")
    service = _Service(clock, error)

    with pytest.raises(WaiterFailureError) as raised:
        _wait(aio, service, "ThingReady")

    assert raised.value.last_error is error
    assert raised.value.__cause__ is error
    assert raised.value.last_output is None
    assert str(raised.value) == (
        "Waiter ThingReady failed after 1 attempt on an error no acceptor matched: "
        "CallError"
    )


@_AIO
def test_a_retry_acceptor_keeps_polling_through_an_error(
    aio: bool, clock: _Clock
) -> None:
    throttled = CallError(
        response_metadata=ErrorResponseMetadata(error_code="Throttled")
    )
    service = _Service(clock, throttled, _Output(status="READY"))

    assert _wait(aio, service, "ThingReady") == _Output(status="READY")
    assert len(service.calls) == 2


@_AIO
def test_a_timeout_after_an_error_keeps_it(aio: bool, clock: _Clock) -> None:
    throttled = CallError(
        response_metadata=ErrorResponseMetadata(error_code="Throttled")
    )
    service = _Service(clock, throttled, call_time=5)

    with pytest.raises(WaiterTimeoutError) as raised:
        _wait(aio, service, "ThingReady", max_wait_time=4)

    assert raised.value.last_error is throttled
    assert raised.value.__cause__ is throttled


@pytest.mark.parametrize(
    "error",
    [
        pytest.param(_NotFound("gone"), id="modeled"),
        pytest.param(
            CallError(response_metadata=ErrorResponseMetadata(error_code="NotFound")),
            id="error-code",
        ),
    ],
)
@_AIO
def test_success_on_an_error_returns_none(
    aio: bool, clock: _Clock, error: Exception
) -> None:
    service = _Service(clock, error)

    assert _wait(aio, service, "ThingGone") is None


@_AIO
def test_an_absolute_shape_id_matches_only_that_modeled_error(
    aio: bool, clock: _Clock
) -> None:
    assert _wait(aio, _Service(clock, _NotFound("gone")), "ExactlyGone") is None

    code = CallError(response_metadata=ErrorResponseMetadata(error_code="NotFound"))
    for waiter, error in (("ExactlyGone", code), ("OtherGone", _NotFound("gone"))):
        with pytest.raises(WaiterFailureError):
            _wait(aio, _Service(clock, error), waiter)


def test_error_type_doesnt_match_other_errors(clock: _Clock) -> None:
    service = _Service(
        clock, CallError(response_metadata=ErrorResponseMetadata(error_code="Other"))
    )

    with pytest.raises(WaiterFailureError):
        _wait(False, service, "ThingGone")


@pytest.mark.parametrize(
    "things, outcome",
    [
        ([_Thing("READY"), _Thing("READY")], "success"),
        ([_Thing("READY"), _Thing("BROKEN")], "failure"),
        ([], "retry"),
        (None, "retry"),
        ([_Thing("READY"), _Thing("CREATING")], "retry"),
    ],
)
def test_list_comparators(clock: _Clock, things: Any, outcome: str) -> None:
    output = _Output(things=things)
    service = _Service(clock, output, _Output(things=[_Thing("READY")]))

    if outcome == "failure":
        with pytest.raises(WaiterFailureError):
            _wait(False, service, "AllReady")
        return
    _wait(False, service, "AllReady")
    assert len(service.calls) == (1 if outcome == "success" else 2)


@pytest.mark.parametrize("ready, attempts", [(True, 1), (False, 2), (None, 2)], ids=str)
def test_boolean_equals(clock: _Clock, ready: bool | None, attempts: int) -> None:
    service = _Service(clock, _Output(ready=ready), _Output(ready=True))

    _wait(False, service, "Flagged")

    assert len(service.calls) == attempts


def test_a_failure_message_list_is_joined(clock: _Clock) -> None:
    output = _Output(things=[_Thing("READY"), _Thing("BROKEN")])

    with pytest.raises(WaiterFailureError) as raised:
        _wait(False, _Service(clock, output), "AllReady")

    assert str(raised.value) == "Waiter AllReady failed after 1 attempt: READY; BROKEN"


def test_success_false_matches_any_error(clock: _Clock) -> None:
    service = _Service(clock, _NotFound("gone"))

    with pytest.raises(WaiterFailureError) as raised:
        _wait(False, service, "Flagged")

    assert str(raised.value) == "Waiter Flagged failed after 1 attempt."


def test_input_output_reads_the_callers_request(clock: _Clock) -> None:
    matched = _Output(status="n")
    service = _Service(clock, matched)

    assert _wait(False, service, "Echoed", _Input(name="n")) is matched


@pytest.mark.parametrize(
    "options, message",
    [
        ({"max_wait_time": 0}, "max_wait_time must be a positive"),
        ({"max_wait_time": float("inf")}, "max_wait_time must be a positive"),
        ({"min_delay": -1}, "min_delay must be a positive"),
        ({"max_delay": float("nan")}, "max_delay must be a positive"),
        ({"min_delay": 20}, r"min_delay \(20\) must not be above max_delay \(10\)"),
        ({"min_delay": 5, "max_delay": 4}, "must not be above max_delay"),
    ],
)
@_AIO
def test_invalid_times_fail_before_any_request(
    aio: bool, clock: _Clock, options: dict[str, Any], message: str
) -> None:
    service = _Service(clock, _Output(status="READY"))

    with pytest.raises(ValueError, match=message):
        _wait(aio, service, "ThingReady", **options)

    assert service.calls == []


def test_an_unknown_waiter_fails_before_any_request(clock: _Clock) -> None:
    service = _Service(clock, _Output(status="READY"))

    with pytest.raises(ValueError, match="no waiter named 'Missing'"):
        _wait(False, service, "Missing")
    with pytest.raises(ValueError, match="no waiter named"):
        _wait(False, service, "ThingReady", operation=_operation(None))

    assert service.calls == []


def test_definitions_are_cached_on_the_schema() -> None:
    first = _waiters.waiter_definition(_OPERATION, "ThingReady")

    assert _waiters.waiter_definition(_OPERATION, "ThingReady") is first
    assert first.min_delay == 2 and first.max_delay == 10
    defaults = _waiters.waiter_definition(_OPERATION, "ThingGone")
    assert (defaults.min_delay, defaults.max_delay) == (2, 120)


@pytest.mark.parametrize(
    "matcher, message",
    [
        (_path("a[?", "b"), "Unsupported JMESPath expression"),
        (
            {"input": {}},
            "Waiter Bad of com.example#GetThing has an unsupported 'input'",
        ),
        (_path("a", "b", "eq"), "unsupported 'eq' comparator"),
    ],
)
def test_unsupported_waiters_fail_on_first_use(matcher: Any, message: str) -> None:
    bad = {"acceptors": [{"state": "success", "matcher": matcher}]}

    with pytest.raises(ValueError, match=message):
        _waiters.waiter_definition(_operation({"Bad": bad}), "Bad")


def test_exceptions_share_a_base() -> None:
    assert issubclass(WaiterFailureError, WaiterError)
    assert issubclass(WaiterTimeoutError, WaiterError)
    error = WaiterTimeoutError("late", attempts=3)
    assert (error.attempts, error.last_output, error.last_error) == (3, None, None)


def test_operations_raise_only_exceptions_to_waiters(clock: _Clock) -> None:
    class _Stop(BaseException):
        pass

    def stop(request: Any, *, plugins: Any) -> Any:
        raise _Stop

    call: Callable[..., Any] = stop
    request: Any = _Input()
    with pytest.raises(_Stop):
        sync_waiters.wait(request, _OPERATION, call, "Flagged", max_wait_time=10)
