#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""Mode-neutral programs shared by the sync and async clients.

A program is a generator that yields zero-argument effects and receives each
effect's result. Effects invoke the injected components (transports, resolvers,
signers), so the same program runs synchronously over sync components and
asynchronously over async ones.
"""

from collections.abc import Callable, Generator
from inspect import isawaitable
from typing import Any

from .exceptions import AsyncBodyError

__all__ = ["Effect", "Program", "run_program"]

type Effect = Callable[[], Any]
type Program[T] = Generator[Effect, Any, T]


def run_program[T](program: Program[T]) -> T:
    """Drive a program to completion, calling each effect synchronously.

    :raises AsyncBodyError: If an effect returns an awaitable.
    """
    value: Any = None
    error: BaseException | None = None
    while True:
        try:
            effect = program.send(value) if error is None else program.throw(error)
        except StopIteration as stop:
            return stop.value
        try:
            value, error = effect(), None
            if isawaitable(value):
                close = getattr(value, "close", None)
                if close is not None:
                    close()
                raise AsyncBodyError(
                    f"A synchronous client received an asynchronous result from {effect}."
                )
        except BaseException as e:
            value, error = None, e
