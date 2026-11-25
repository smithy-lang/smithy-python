#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""The wait loop of modeled waiters.

Generated clients call this from their ``wait_until_*`` methods. The async twin is
in ``smithy_core.aio.waiters``.
"""

from collections.abc import Callable, Sequence
from time import sleep
from typing import Any

from ._waiters import WaiterState
from .schemas import APIOperation

__all__ = ["wait"]


def wait[O](
    request: object,
    operation: APIOperation[Any, Any],
    call: Callable[..., O],
    waiter: str,
    plugins: Sequence[Any] | None = None,
    *,
    max_wait_time: float,
    min_delay: float | None = None,
    max_delay: float | None = None,
) -> O | None:
    """Poll an operation until one of its modeled waiter's acceptors ends the wait.

    Each attempt calls the operation through the client, so its retries handle
    throttling and transient errors. Between attempts, this blocks for a jittered
    exponential backoff between ``min_delay`` and ``max_delay``.

    :param request: The request each attempt sends a copy of.
    :param operation: The operation, whose schema's waitable trait defines the
        waiter.
    :param call: Sends one request. It is called with a request and the keyword
        argument ``plugins``.
    :param waiter: The name of the waiter, as the model defines it.
    :param plugins: Passed to every call, each time as a new list.
    :param max_wait_time: The most seconds to wait, counting requests and delays.
    :param min_delay: The fewest seconds between attempts, if not the waiter's.
    :param max_delay: The most seconds between attempts, if not the waiter's.
    :returns: The output that matched a success acceptor, or None if an error
        did.
    :raises ValueError: Before any request, if a time is not a positive number of
        seconds, ``min_delay`` is above ``max_delay``, or the operation has no such
        waiter.
    :raises WaiterFailureError: If the wait reached its failure state.
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
            output = call(attempt, plugins=attempt_plugins)
        except Exception as error:
            delay = state.accept(None, error)
            output = None
        else:
            delay = state.accept(output, None)
        if delay is None:
            return output
        sleep(delay)
