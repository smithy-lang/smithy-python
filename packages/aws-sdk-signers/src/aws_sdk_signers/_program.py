# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Mode-neutral programs shared by the sync and async signers.

A program is a generator that yields zero-argument effects and receives each effect's
result. This is a copy of ``smithy_core.program``, since this package has no
dependencies.
"""

from collections.abc import Callable, Generator
from inspect import isawaitable
from typing import Any

type Effect = Callable[[], Any]
type Program[T] = Generator[Effect, Any, T]


def run_program[T](program: Program[T]) -> T:
    """Drive a program to completion, calling each effect synchronously.

    :raises TypeError: If an effect returns an awaitable.
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
                raise TypeError(
                    "A synchronous signer received an asynchronous result. Use the "
                    "signers in aws_sdk_signers.aio for async request bodies."
                )
        except BaseException as e:
            value, error = None, e
