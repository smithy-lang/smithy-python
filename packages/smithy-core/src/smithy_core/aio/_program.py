#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from inspect import isawaitable
from typing import Any

from .._program import Program

__all__ = ["run_program_async"]


async def run_program_async[T](program: Program[T]) -> T:
    """Drive a program to completion, awaiting each effect that returns an awaitable."""
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
                value = await value
        except BaseException as e:
            value, error = None, e
