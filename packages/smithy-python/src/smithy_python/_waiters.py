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
    """One waiter's generated method. The runtime reads its acceptors from the schema."""

    name: str
    method_name: str
    documentation: str | None
    min_delay: int
    max_delay: int
    deprecated: bool


def plan_waiters(
    plan: ClientPlan, paginators: Sequence[PaginatorPlan | None]
) -> tuple[tuple[WaiterPlan, ...], ...]:
    """Plan each operation's waiters, parallel to ``plan.operations``."""
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
_WAITER_NAME: Final = re.compile(r"[A-Z][A-Za-z0-9]*")
_DEFAULT_MIN_DELAY: Final = 2
_DEFAULT_MAX_DELAY: Final = 120


def _waiters(operation: _model.OperationShape) -> Mapping[str, _model.Node]:
    value = operation.get_trait(_WAITABLE) if operation.has_trait(_WAITABLE) else None
    if not isinstance(value, Mapping):
        return {}
    for name in value:
        if not _WAITER_NAME.fullmatch(name):
            raise _exceptions.CodegenError(
                f"Waitable operation {operation.id} has waiter {name!r}, but waiter "
                "names must be UpperCamelCase letters and digits"
            )
    return value


def _allocate_names(
    plan: ClientPlan,
    waiters: Mapping[_model.ShapeId, Mapping[str, _model.Node]],
    paginators: Sequence[PaginatorPlan | None],
) -> dict[str, str]:
    """Name each waiter ``wait_until_`` plus its snake-cased name.

    A name taken by an operation, paginator, or client member gets underscores until
    it's also free of every other waiter's preferred name.
    """
    owners: dict[str, tuple[str, _model.ShapeId]] = {}
    for operation_id, operation_waiters in waiters.items():
        for name in operation_waiters:
            other, owner = owners.setdefault(name.lower(), (name, operation_id))
            if (other, owner) != (name, operation_id):
                raise _exceptions.CodegenError(
                    f"Waitable operations {owner} and {operation_id} have waiters "
                    f"named {other!r} and {name!r}, but waiter names must be unique"
                )
    preferred = {name: _PREFIX + _name(name) for name, _ in owners.values()}
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
    settings: Mapping[str, _model.Node] = waiter if isinstance(waiter, Mapping) else {}
    delays: list[int] = []
    for setting, default in (
        ("minDelay", _DEFAULT_MIN_DELAY),
        ("maxDelay", _DEFAULT_MAX_DELAY),
    ):
        # The delays are written into the method's documentation.
        delay = settings.get(setting, default)
        if not isinstance(delay, int) or isinstance(delay, bool):
            raise _exceptions.CodegenError(
                f"Waitable operation {operation.id} has waiter {name!r} with a "
                f"{setting} that is not an integer"
            )
        delays.append(delay)
    if delays[0] > delays[1]:
        raise _exceptions.CodegenError(
            f"Waitable operation {operation.id} has waiter {name!r} with a minDelay of "
            f"{delays[0]}, above its maxDelay of {delays[1]}"
        )
    documentation = settings.get("documentation")
    return WaiterPlan(
        name=name,
        method_name=method,
        documentation=documentation if isinstance(documentation, str) else None,
        min_delay=delays[0],
        max_delay=delays[1],
        deprecated=settings.get("deprecated") is True,
    )
