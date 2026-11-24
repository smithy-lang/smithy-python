#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""Pagination rules shared by the sync and async paginators.

The adapters in ``smithy_core.pagination`` and ``smithy_core.aio.pagination`` only
send the request this state builds and report the outcome back to it.
"""

from collections.abc import Iterator, Mapping, Sequence
from copy import copy, deepcopy
from typing import Any, cast

__all__ = ["PaginationState", "read_items"]


class PaginationState:
    """The requests and stopping decision of one traversal.

    Holds a shallow snapshot of the first request, and one token: the one sent
    with the latest request, which is the first request's until a page is
    accepted. So it stays the same size however many pages are requested.
    """

    __slots__ = (
        "_done",
        "_input_token",
        "_output_token",
        "_plugins",
        "_request",
        "_stop_on_same_token",
        "_token",
    )

    def __init__(
        self,
        request: object,
        plugins: Sequence[Any] | None,
        *,
        input_token: str,
        output_token: Sequence[str],
        stop_on_same_token: bool = True,
    ) -> None:
        # A shallow copy: the caller's request is never modified, and nested values,
        # including streams, keep their identity.
        self._request = copy(request)
        self._plugins = None if plugins is None else list(plugins)
        self._input_token = input_token
        self._output_token = tuple(output_token)
        self._stop_on_same_token = stop_on_same_token
        # The caller's token is copied now, as later tokens are, so that changes
        # to it, or to a request it is sent in, don't reach the other.
        self._token: Any = _snapshot(getattr(self._request, input_token, None))
        self._done = False

    def next_call(self) -> tuple[Any, list[Any] | None] | None:
        """Return the next request and its plugins, or None if pagination ended."""
        if self._done:
            return None
        request = copy(self._request)
        # A copy, so that changes to this request, by an interceptor for example,
        # can't change the caller's token or the one the next page is compared with.
        setattr(request, self._input_token, _snapshot(self._token))
        plugins = None if self._plugins is None else list(self._plugins)
        return request, plugins

    def accept(self, page: object) -> None:
        """Record a page's token before the page is given to the caller.

        Ends pagination if the page has no token. Unless ``stop_on_same_token`` is
        False, also ends it if the page has the same token, by value, as the request
        it answers, including a starting token.
        """
        token = _walk(page, self._output_token)
        if _is_empty(token) or (self._stop_on_same_token and token == self._token):
            self._done = True
            return
        self._token = _snapshot(token)

    def stop(self) -> None:
        """End pagination, as when a request failed or was cancelled."""
        self._done = True


def read_items(page: object, path: Sequence[str]) -> Iterator[Any]:
    """Iterate a page's items: list elements, or map ``(key, value)`` tuples.

    A missing structure along the path, or missing items, yields nothing.
    """
    items = _walk(page, path)
    if items is None:
        return iter(())
    if isinstance(items, Mapping):
        return iter(cast("Mapping[Any, Any]", items).items())
    return iter(items)


def _walk(value: object, path: tuple[str, ...] | Sequence[str]) -> Any:
    for name in path:
        if value is None:
            return None
        value = getattr(value, name)
    return value


def _is_empty(token: object) -> bool:
    if token is None:
        return True
    if isinstance(token, str | Mapping):
        return len(token) == 0  # pyright: ignore[reportUnknownArgumentType]
    return False


def _snapshot(token: Any) -> Any:
    # Strings are immutable. A map token, such as a DynamoDB key, may hold
    # mutable values.
    return token if isinstance(token, str) else deepcopy(token)
