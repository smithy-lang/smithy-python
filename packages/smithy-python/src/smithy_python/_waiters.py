# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Planning of the ``wait_until_*`` methods of generated clients."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from . import exceptions as _exceptions
from . import model as _model
from .symbols import (
    _CLIENT_METHOD_NAMES,  # pyright: ignore[reportPrivateUsage]
    _name,  # pyright: ignore[reportPrivateUsage]
)

if TYPE_CHECKING:
    from ._pagination import PaginatorPlan
    from .clients import ClientPlan

__all__ = ["WaiterPlan", "plan_waiters"]


@dataclass(frozen=True, slots=True)
class WaiterPlan:
    """The generated description of one waiter of an operation's waitable trait.

    The acceptors aren't planned: the runtime reads them from the operation's
    schema.
    """

    name: str
    method_name: str
    documentation: str | None
    min_delay: int
    max_delay: int
    deprecated: bool


def plan_waiters(
    plan: ClientPlan, paginators: Sequence[PaginatorPlan | None]
) -> tuple[tuple[WaiterPlan, ...], ...]:
    """Plan the waiters of each operation of the client, in waiter name order.

    The result is parallel to ``plan.operations``.

    :param paginators: The paginators of the operations, whose names waiters avoid.
    :raises CodegenError: Naming the operation and waiter, if a waitable trait isn't
        a map of valid waiter names to waiters with acceptors, or a waiter's delays
        aren't whole seconds from 1 with ``minDelay`` at most ``maxDelay``.
    """
    waiters = {
        operation.operation.id: _waiters(operation.operation)
        for operation in plan.operations
    }
    names = _allocate_names(plan, waiters, paginators)
    return tuple(
        tuple(
            _plan(operation.operation, name, waiter, names[name])
            for name, waiter in sorted(waiters[operation.operation.id].items())
        )
        for operation in plan.operations
    )


_WAITABLE: Final = _model.ShapeId("smithy.waiters", "waitable")
_PREFIX: Final = "wait_until_"
_WAITER_NAME: Final = re.compile(r"[A-Z]+[A-Za-z0-9]*")
_DEFAULT_MIN_DELAY: Final = 2
_DEFAULT_MAX_DELAY: Final = 120


def _waiters(operation: _model.OperationShape) -> Mapping[str, _model.Node]:
    if not operation.has_trait(_WAITABLE):
        return {}
    value = operation.get_trait(_WAITABLE)
    if not isinstance(value, Mapping):
        raise _exceptions.CodegenError(
            f"Operation {operation.id} has a waitable trait that is not a map"
        )
    for name in value:
        if not _WAITER_NAME.fullmatch(name):
            raise _exceptions.CodegenError(
                f"Operation {operation.id} has the waiter {name!r}, but waiter "
                "names must be UpperCamelCase letters and digits"
            )
    return value


def _allocate_names(
    plan: ClientPlan,
    waiters: Mapping[_model.ShapeId, Mapping[str, _model.Node]],
    paginators: Sequence[PaginatorPlan | None],
) -> dict[str, str]:
    """Name each waiter ``wait_until_`` plus its snake-cased name.

    Operation and paginator names never change. A waiter name that is taken by an
    operation, a paginator, or a client member gets underscores until it is free of
    those and of every other waiter's preferred name, so names don't depend on
    operation order.
    """
    preferred = {
        name: _PREFIX + _name(name)
        for operation_waiters in waiters.values()
        for name in operation_waiters
    }
    taken = {operation.method_name for operation in plan.operations}
    taken |= {paginator.method_name for paginator in paginators if paginator}
    taken |= _CLIENT_METHOD_NAMES
    reserved = taken | set(preferred.values())
    names: dict[str, str] = {}
    for waiter, name in sorted(preferred.items()):
        if name in taken:
            while name in reserved:
                name += "_"
            reserved.add(name)
        names[waiter] = name
    return names


def _plan(
    operation: _model.OperationShape, name: str, waiter: _model.Node, method: str
) -> WaiterPlan:
    label = f"Waiter {name} of operation {operation.id}"
    if not isinstance(waiter, Mapping):
        raise _exceptions.CodegenError(f"{label} is not a structure")
    acceptors = waiter.get("acceptors")
    if (
        not isinstance(acceptors, Sequence)
        or isinstance(acceptors, str)
        or not acceptors
    ):
        raise _exceptions.CodegenError(f"{label} has no acceptors")
    min_delay = waiter.get("minDelay", _DEFAULT_MIN_DELAY)
    max_delay = waiter.get("maxDelay", _DEFAULT_MAX_DELAY)
    for setting, value in (("minDelay", min_delay), ("maxDelay", max_delay)):
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            raise _exceptions.CodegenError(
                f"{label} has a {setting} that is not a whole number of seconds from 1"
            )
    assert isinstance(min_delay, int) and isinstance(max_delay, int)  # noqa: S101
    if min_delay > max_delay:
        raise _exceptions.CodegenError(
            f"{label} has a minDelay of {min_delay}, above its maxDelay of {max_delay}"
        )
    documentation = waiter.get("documentation")
    return WaiterPlan(
        name=name,
        method_name=method,
        documentation=documentation if isinstance(documentation, str) else None,
        min_delay=min_delay,
        max_delay=max_delay,
        deprecated=waiter.get("deprecated") is True,
    )
