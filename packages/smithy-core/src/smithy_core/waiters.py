#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""The wait loop of modeled waiters.

Generated clients call this from their ``wait_until_*`` methods. The async twin is
in ``smithy_core.aio.waiters``.
"""

from collections.abc import Callable, Sequence
from time import sleep
from typing import Any, Concatenate

from ._waiters import WaiterState
from .deserializers import DeserializeableShape
from .schemas import APIOperation
from .serializers import SerializeableShape

__all__ = ["wait"]


def wait[I: SerializeableShape, O: DeserializeableShape](
    request: I,
    operation: APIOperation[I, O],
    poll: Callable[Concatenate[I, ...], O],
    waiter: str,
    plugins: Sequence[Any] | None = None,
    *,
    max_wait_time: float,
    min_delay: float | None = None,
    max_delay: float | None = None,
) -> O | None:
    """Poll an operation until its waiter succeeds, fails, or times out.

    Attempts are spaced by jittered exponential backoff.

    :param request: The request. Each attempt sends a copy.
    :param operation: The operation whose waitable trait defines the waiter.
    :param poll: Sends one request through the client.
    :param waiter: The waiter's name in the model.
    :param plugins: Plugins for each attempt.
    :param max_wait_time: Maximum seconds to wait, including requests.
    :param min_delay: Minimum seconds between attempts. Defaults to the waiter's.
    :param max_delay: Maximum seconds between attempts. Defaults to the waiter's.
    :returns: The matching output, or None if the waiter succeeded on an error.
    :raises ValueError: If a time or the waiter name is invalid.
    :raises WaiterFailureError: If the waiter reached its failure state.
    :raises WaiterTimeoutError: If ``max_wait_time`` passed first.
    """
    state = WaiterState(
        request,
        operation,
        waiter,
        plugins,
        max_wait_time=max_wait_time,
        min_delay=min_delay,
        max_delay=max_delay,
    )
    while True:
        attempt, attempt_plugins = state.next_call()
        try:
            output = poll(attempt, plugins=attempt_plugins)
        except Exception as error:
            delay = state.accept(None, error)
            output = None
        else:
            delay = state.accept(output, None)
        if delay is None:
            return output
        sleep(delay)
