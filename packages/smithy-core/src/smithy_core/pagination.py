#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""Iterators over the pages of paginated operations.

Generated clients return these from their ``paginate_*`` methods. The async
twins are in ``smithy_core.aio.pagination``.
"""

from collections.abc import Callable, Iterator, Sequence
from typing import Any

from ._pagination import PaginationState, read_items

__all__ = ["ItemPaginator", "Paginator"]


class Paginator[Page](Iterator[Page]):
    """A single-use iterator over the complete outputs of a paginated operation.

    Each advance sends one request. Nothing is sent before the first advance, and
    nothing is fetched ahead. Pagination ends when a page has no token.
    """

    def __init__(
        self,
        request: object,
        operation: Callable[..., Page],
        plugins: Sequence[Any] | None = None,
        *,
        input_token: str,
        output_token: Sequence[str],
    ) -> None:
        """
        :param request: The first request. It is copied, not modified.
        :param operation: Sends one request. It is called with a request and the
            keyword argument ``plugins``.
        :param plugins: Passed to every call of ``operation``, each time as a new
            list.
        :param input_token: The request member that takes the next token.
        :param output_token: The member names from a page to its next token.
        """
        self._operation = operation
        self._state = PaginationState(
            request, plugins, input_token=input_token, output_token=output_token
        )

    def __next__(self) -> Page:
        """Request and return the next page.

        :raises PaginationError: If the previous two pages returned the same
            token. Pagination then ends.
        """
        call = self._state.next_call()
        if call is None:
            raise StopIteration
        request, plugins = call
        try:
            page = self._operation(request, plugins=plugins)
            self._state.accept(page)
        except BaseException:
            self._state.stop()
            raise
        return page


class ItemPaginator[Page, Item](Paginator[Page]):
    """A paginator whose pages hold items, which it can also iterate."""

    def __init__(
        self,
        request: object,
        operation: Callable[..., Page],
        plugins: Sequence[Any] | None = None,
        *,
        input_token: str,
        output_token: Sequence[str],
        items: Sequence[str],
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
        """
        super().__init__(
            request,
            operation,
            plugins,
            input_token=input_token,
            output_token=output_token,
        )
        self._items = tuple(items)

    def items(self) -> Iterator[Item]:
        """Iterate the items of the remaining pages.

        A list's items are its elements, and a map's are ``(key, value)`` tuples.
        The pages come from this paginator, so it advances too.
        """
        for page in self:
            yield from read_items(page, self._items)
