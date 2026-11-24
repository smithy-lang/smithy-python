#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""Async iterators over the pages of paginated operations.

Generated async clients return these from their ``paginate_*`` methods. The sync
twins are in ``smithy_core.pagination``.
"""

from collections.abc import AsyncIterator, Awaitable, Callable, Sequence
from typing import Any

from .._pagination import PaginationState, read_items
from ..exceptions import PaginationError

__all__ = ["AsyncItemPaginator", "AsyncPaginator"]


class AsyncPaginator[Page](AsyncIterator[Page]):
    """A single-use async iterator over the complete outputs of a paginated operation.

    Each advance sends one request. Nothing is sent before the first advance, and
    nothing is fetched ahead or in the background. Pagination ends after a page
    with no token, or, by default, with the same token as its request.
    """

    def __init__(
        self,
        request: object,
        operation: Callable[..., Awaitable[Page]],
        plugins: Sequence[Any] | None = None,
        *,
        input_token: str,
        output_token: Sequence[str],
        stop_on_same_token: bool = True,
    ) -> None:
        """
        :param request: The first request. It is copied, not modified.
        :param operation: Sends one request. It is called with a request and the
            keyword argument ``plugins``.
        :param plugins: Passed to every call of ``operation``, each time as a new
            list.
        :param input_token: The request member that takes the next token.
        :param output_token: The member names from a page to its next token.
        :param stop_on_same_token: Whether to end pagination after a page whose
            token equals the one its request sent, including a starting token.
            Set to False to keep requesting pages when tokens repeat.
        """
        self._operation = operation
        self._state = PaginationState(
            request,
            plugins,
            input_token=input_token,
            output_token=output_token,
            stop_on_same_token=stop_on_same_token,
        )
        self._advancing = False

    async def __anext__(self) -> Page:
        """Request and return the next page.

        :raises PaginationError: If another advance of this paginator hasn't
            finished, which that advance is not affected by.
        """
        if self._advancing:
            raise PaginationError(
                "This paginator is already requesting a page; await that first."
            )
        call = self._state.next_call()
        if call is None:
            raise StopAsyncIteration
        request, plugins = call
        self._advancing = True
        try:
            page = await self._operation(request, plugins=plugins)
            self._state.accept(page)
        except BaseException:
            self._state.stop()
            raise
        finally:
            self._advancing = False
        return page


class AsyncItemPaginator[Page, Item](AsyncPaginator[Page]):
    """An async paginator whose pages hold items, which it can also iterate."""

    def __init__(
        self,
        request: object,
        operation: Callable[..., Awaitable[Page]],
        plugins: Sequence[Any] | None = None,
        *,
        input_token: str,
        output_token: Sequence[str],
        items: Sequence[str],
        stop_on_same_token: bool = True,
    ) -> None:
        """
        :param request: The first request. It is copied, not modified.
        :param operation: Sends one request. It is called with a request and the
            keyword argument ``plugins``.
        :param plugins: Passed to every call of ``operation``, each time as a new
            list.
        :param input_token: The request member that takes the next token.
        :param output_token: The member names from a page to its next token.
        :param items: The member names from a page to its items.
        :param stop_on_same_token: Whether to end pagination after a page whose
            token equals the one its request sent, including a starting token.
            Set to False to keep requesting pages when tokens repeat.
        """
        super().__init__(
            request,
            operation,
            plugins,
            input_token=input_token,
            output_token=output_token,
            stop_on_same_token=stop_on_same_token,
        )
        self._items = tuple(items)

    async def items(self) -> AsyncIterator[Item]:
        """Iterate the items of the remaining pages.

        A list's items are its elements, and a map's are ``(key, value)`` tuples.
        The pages come from this paginator, so it advances too.
        """
        async for page in self:
            for item in read_items(page, self._items):
                yield item
