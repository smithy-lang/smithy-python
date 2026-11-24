#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import asyncio
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any

import pytest
from smithy_core.aio.pagination import AsyncItemPaginator, AsyncPaginator
from smithy_core.exceptions import PaginationError
from smithy_core.pagination import ItemPaginator, Paginator


@dataclass
class _Request:
    token: Any = None
    nested: list[str] = field(default_factory=list[str])


@dataclass
class _Wrapper:
    token: Any = None
    items: Any = None


@dataclass
class _Page:
    wrapper: _Wrapper | None = None


def _page(token: Any = None, items: Any = None) -> _Page:
    return _Page(_Wrapper(token, items))


class _Service:
    """Returns the given pages in order, recording each call."""

    def __init__(self, *pages: _Page | BaseException) -> None:
        self.pages = list(pages)
        self.calls: list[tuple[_Request, list[Any] | None]] = []

    def __call__(self, request: _Request, *, plugins: list[Any] | None) -> _Page:
        self.calls.append((request, plugins))
        page = self.pages.pop(0)
        if isinstance(page, BaseException):
            raise page
        return page

    async def call_async(
        self, request: _Request, *, plugins: list[Any] | None
    ) -> _Page:
        return self(request, plugins=plugins)

    @property
    def tokens(self) -> list[Any]:
        return [request.token for request, _ in self.calls]


def _paginator(
    aio: bool,
    service: _Service,
    request: _Request | None = None,
    plugins: list[Any] | None = None,
    **options: Any,
) -> Any:
    paths: dict[str, Any] = {
        "input_token": "token",
        "output_token": ("wrapper", "token"),
        "items": ("wrapper", "items"),
        **options,
    }
    request = request or _Request()
    if aio:
        return AsyncItemPaginator[_Page, Any](
            request, service.call_async, plugins, **paths
        )
    return ItemPaginator[_Page, Any](request, service, plugins, **paths)


async def _next(aio: bool, paginator: Any) -> Any:
    return await anext(paginator) if aio else next(paginator)


async def _pages(aio: bool, paginator: Any) -> list[Any]:
    return [page async for page in paginator] if aio else list(paginator)


async def _items(aio: bool, paginator: Any) -> list[Any]:
    items = paginator.items()
    return [item async for item in items] if aio else list(items)


async def _assert_ended(aio: bool, paginator: Any) -> None:
    # StopIteration can't propagate out of a coroutine, so it is caught here.
    if aio:
        with pytest.raises(StopAsyncIteration):
            await anext(paginator)
    else:
        with pytest.raises(StopIteration):
            next(paginator)


AIO = pytest.mark.parametrize("aio", [False, True], ids=["sync", "async"])


@AIO
async def test_requests_pages_lazily_until_the_token_ends(aio: bool) -> None:
    pages = [_page("a", [1]), _page("b", []), _page(None, [2])]
    service = _Service(*pages)
    paginator = _paginator(aio, service, _Request(token="start"))
    assert not service.calls
    assert (aiter(paginator) if aio else iter(paginator)) is paginator

    assert await _next(aio, paginator) is pages[0]
    assert len(service.calls) == 1
    assert await _pages(aio, paginator) == pages[1:]
    assert service.tokens == ["start", "a", "b"]
    # Omitted plugins are passed as None, not as an empty list.
    assert all(plugins is None for _, plugins in service.calls)
    await _assert_ended(aio, paginator)
    assert len(service.calls) == 3


@AIO
@pytest.mark.parametrize(
    "last",
    [_page(None), _page(""), _page({}), _Page()],
    ids=["missing-token", "empty-string-token", "empty-map-token", "missing-wrapper"],
)
async def test_missing_or_empty_tokens_and_wrappers_end(aio: bool, last: _Page) -> None:
    service = _Service(_page({"k": "v"}), last)
    assert await _pages(aio, _paginator(aio, service)) == [_page({"k": "v"}), last]
    assert service.tokens == [None, {"k": "v"}]


@AIO
async def test_items_flatten_lists_and_map_entries(aio: bool) -> None:
    service = _Service(
        _page("a", ["x", None]),
        _page("b"),
        _page("c", []),
        _page(None, {"k": None, "j": 1}),
    )
    assert await _items(aio, _paginator(aio, service)) == [
        "x",
        None,
        ("k", None),
        ("j", 1),
    ]
    assert len(service.calls) == 4
    assert await _items(aio, _paginator(aio, _Service(_Page()))) == []


@AIO
@pytest.mark.parametrize(
    "token", ["tok-42", {"key": {"nested": [1]}}], ids=["string", "map"]
)
@pytest.mark.parametrize("starting", [False, True], ids=["no-start", "start"])
async def test_same_token_as_its_request_ends_after_its_page_by_default(
    aio: bool, token: Any, starting: bool
) -> None:
    # Each token is an equal but distinct object, so only values are compared.
    if starting:
        # A starting token is compared too: a first page repeating it ends.
        request = _Request(token=deepcopy(token))
        pages = [_page(deepcopy(token))]
    else:
        request = _Request()
        pages = [_page(deepcopy(token)), _page(deepcopy(token))]
    service = _Service(*pages, _page("unexpected"), _page())
    paginator = _paginator(aio, service, request)

    assert await _pages(aio, paginator) == pages
    await _assert_ended(aio, paginator)
    assert service.tokens == ([token] if starting else [None, token])


@AIO
@pytest.mark.parametrize(
    ("token", "end"),
    [("tok", None), ("tok", ""), ({"k": ""}, None), ({"k": ""}, {})],
    ids=["string-none", "string-empty", "map-none", "map-empty"],
)
async def test_repeated_tokens_continue_unless_stopping_on_same_token(
    aio: bool, token: Any, end: Any
) -> None:
    # The first page repeats the starting token, and the second repeats the token
    # its request sent. A map with an empty value has an entry, so is not empty.
    pages = [_page(deepcopy(token)), _page(deepcopy(token)), _page(end)]
    service = _Service(*pages, _page("unexpected"))
    paginator = _paginator(
        aio, service, _Request(token=deepcopy(token)), stop_on_same_token=False
    )

    assert await _pages(aio, paginator) == pages
    await _assert_ended(aio, paginator)
    assert service.tokens == [token, token, token]


@AIO
async def test_map_tokens_are_isolated_from_page_and_request_changes(
    aio: bool,
) -> None:
    first = {"key": {"nested": [1]}}
    service = _Service(_page(first), _page({"key": {"nested": [1]}}), _page())
    paginator = _paginator(aio, service)
    page = await _next(aio, paginator)
    page.wrapper.token["key"]["nested"].append(2)
    await _next(aio, paginator)
    sent = service.tokens[1]
    assert sent == {"key": {"nested": [1]}}
    assert sent is not first
    # The second page repeated the token sent with it, so pagination ended.
    # Changing the sent request, as an interceptor could, doesn't restart it.
    sent["key"]["nested"].append(3)
    await _assert_ended(aio, paginator)
    assert len(service.calls) == 2


@AIO
async def test_initial_map_token_is_isolated_from_the_caller(aio: bool) -> None:
    value = {"nested": [1]}
    initial = {"key": value}
    nested = ["n"]
    service = _Service(_page("a"), _page())
    paginator = _paginator(aio, service, _Request(token=initial, nested=nested))
    # A change after the paginator is made is not sent.
    initial["late"] = {"nested": [9]}
    await _next(aio, paginator)
    (sent, _), *_ = service.calls
    assert sent.token == {"key": {"nested": [1]}}
    assert sent.token is not initial
    # Changing the sent request, as an interceptor could, changes neither the
    # caller's token nor its values. Other members keep their identity.
    sent.token["key"]["nested"].append(2)
    sent.token["extra"] = {}
    assert initial == {"key": {"nested": [1]}, "late": {"nested": [9]}}
    assert initial["key"] is value and value == {"nested": [1]}
    assert sent.nested is nested
    await _pages(aio, paginator)
    assert service.tokens[1] == "a"


@AIO
async def test_request_and_plugins_are_snapshots(aio: bool) -> None:
    nested = ["n"]
    request = _Request(token="start", nested=nested)
    plugin = object()
    plugins = [plugin]
    service = _Service(_page("a"), _page())
    paginator = _paginator(aio, service, request, plugins)
    plugins.append(object())
    await _pages(aio, paginator)

    assert request == _Request(token="start", nested=["n"])
    (first, first_plugins), (second, second_plugins) = service.calls
    assert first is not request and second is not request
    assert first.nested is nested and second.nested is nested
    assert first_plugins == second_plugins == [plugin]
    assert first_plugins is not second_plugins
    assert first_plugins is not plugins


@AIO
@pytest.mark.parametrize(
    "error", [ValueError("boom"), asyncio.CancelledError(), KeyboardInterrupt()]
)
async def test_errors_propagate_and_end_pagination(
    aio: bool, error: BaseException
) -> None:
    service = _Service(_page("a"), error, _page("b"))
    paginator = _paginator(aio, service)
    await _next(aio, paginator)
    with pytest.raises(type(error)) as raised:
        await _next(aio, paginator)
    assert raised.value is error
    await _assert_ended(aio, paginator)
    assert len(service.calls) == 2


async def test_cancelling_an_advance_ends_pagination() -> None:
    started = asyncio.Event()
    calls = 0

    async def operation(request: _Request, *, plugins: list[Any] | None) -> _Page:
        nonlocal calls
        calls += 1
        started.set()
        await asyncio.Event().wait()
        raise AssertionError("not cancelled")

    paginator = AsyncPaginator(
        _Request(), operation, input_token="token", output_token=("wrapper", "token")
    )
    task = asyncio.create_task(anext(paginator))
    await started.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    with pytest.raises(StopAsyncIteration):
        await anext(paginator)
    assert calls == 1


async def test_concurrent_async_advances_are_rejected() -> None:
    release = asyncio.Event()

    async def operation(request: _Request, *, plugins: list[Any] | None) -> _Page:
        await release.wait()
        return _page("a")

    paginator = AsyncPaginator(
        _Request(), operation, input_token="token", output_token=("wrapper", "token")
    )
    first = asyncio.create_task(anext(paginator))
    await asyncio.sleep(0)
    with pytest.raises(PaginationError, match="already"):
        await anext(paginator)
    release.set()
    assert await first == _page("a")
    # The rejected advance did not end pagination.
    release.set()
    assert await anext(paginator) == _page("a")


def test_paginators_without_items_have_no_items_view() -> None:
    service = _Service(_page())
    sync = Paginator(_Request(), service, input_token="t", output_token=("t",))
    aio = AsyncPaginator(
        _Request(), service.call_async, input_token="t", output_token=("t",)
    )
    assert not hasattr(sync, "items") and not hasattr(aio, "items")
