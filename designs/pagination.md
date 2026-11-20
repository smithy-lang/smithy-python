# Modeled pagination

Generated clients expose each operation with the Smithy `@paginated` trait as a
lazy iterator over complete modeled responses. The ordinary operation method is
unchanged and still makes one request.

## User interface

Each paginated operation gets a `paginate_<operation>` factory beside its
ordinary method. It takes the same input as that method: one positional input
model or dictionary, or the input's members as keyword arguments, plus
`plugins`.

```python
from weather import Config, Weather
from weather.models import ListCitiesInput

with Weather(Config(endpoint_uri="https://weather.example")) as client:
    # One request, as before.
    first = client.list_cities(page_size=50)

    # No request until iteration starts. Each page is a ListCitiesOutput.
    for page in client.paginate_list_cities(page_size=50):
        print(page.next_token, len(page.items))

    # The operation models its items, so its paginator can flatten them.
    for city in client.paginate_list_cities(page_size=50).items():
        print(city.name)

    # A model or a dictionary works too. A token in it is used for the
    # first request, so a traversal can resume from a saved service token.
    saved_token = first.next_token
    request = ListCitiesInput(page_size=50, next_token=saved_token)
    for page in client.paginate_list_cities(request):
        ...
```

The async client has the same factory. It is a plain `def`, not a coroutine,
and returns an async iterator:

```python
from weather import AsyncConfig, AsyncWeather

async with AsyncWeather(AsyncConfig(endpoint_uri="https://weather.example")) as client:
    async for page in client.paginate_list_cities(page_size=50):
        ...
    async for city in client.paginate_list_cities(page_size=50).items():
        ...
```

Factories return runtime generic types, not per-operation classes:

| Operation models `items` | Sync client                  | Async client                      |
| ------------------------ | ---------------------------- | --------------------------------- |
| No                       | `Paginator[Page]`            | `AsyncPaginator[Page]`            |
| Yes                      | `ItemPaginator[Page, Item]`  | `AsyncItemPaginator[Page, Item]`  |

`Paginator[Page]` is an `Iterator[Page]`. `ItemPaginator` adds
`items() -> Iterator[Item]`. The async twins live in `smithy_core.aio.pagination`
and are `AsyncIterator`s. Only operations that model `items` have an `items()`
method, so its absence is visible to type checkers. For a list, `items()` yields
the list's elements. For a map, it yields `(key, value)` tuples, as
`dict.items()` does. Sparse collections keep their `None` values.

A paginator is single-use, like any Python iterator. `iter(pages) is pages`, and
traversing again needs a new factory call. `items()` draws pages from the same
paginator, so mixing page and item iteration interleaves them as two views of
one iterator would. Advancing an async paginator while another advance on it is
still awaiting raises `PaginationError`.

Page size and the starting token stay the modeled input members, such as
`page_size` or `max_results` and `next_token`. The factory adds no SDK-level
options.

## Semantics

**Which operations.** An operation is paginated only if it carries the
`@paginated` trait itself. The service's `@paginated` trait supplies defaults
for each setting the operation omits. `items` and `pageSize` are optional.
Operations bound to resources are included.

**Requests.** The factory checks and builds the input model synchronously, with
the ordinary method's rules, and raises the same `TypeError`s. It does not set up
the client, run plugins, or send anything. It takes a shallow copy of the
built input. Neither the caller's model nor their dictionary is modified, and
nested values keep their identity; they are not deep-copied. Changing nested
input values during iteration is unsupported. Each page is requested with a
fresh shallow copy of that snapshot, with only the input token member replaced.
The first request sends the caller's input token, if any, unchanged. A map input
token is deep-copied when the factory is called, so later changes to the
caller's map don't reach the requests, and each request gets its own copy of it.

Each page is requested through the ordinary operation method. Retries,
interceptors, auth, endpoints, and per-operation default plugins all run for
every page. The factory copies the `plugins` list it was given, and each page
gets its own copy of that list. Client plugins still run once, at client setup.

**Responses.** Each page is the operation's output, unchanged, including its
response metadata. Token and item paths are walked through nested structure
members by their generated Python names. A missing optional structure along the
path means no token, or no items. The next token is read before the page is
returned. A map token is deep-copied, so changes to the yielded page do not
change the next request. Each request also gets its own copy, so an interceptor
that changes a request's token does not change the token the next page is
compared with. A string token needs no copy. Pages with no items are returned
and do not end pagination.

**Ending.** Pagination ends when the output token is missing, `None`, an empty
string, or an empty map. If two consecutive responses return the same nonempty
token, the second page is still returned. The next advance then raises
`PaginationError` without sending a request. The error message does not contain
the token. This compares each output token only with the previous output token,
so an input token equal to the first output token is not an error. The
paginator keeps only the previous token. It does not detect longer cycles.

**Errors.** Service errors, `CancelledError`, and pagination errors propagate
unchanged. After any of them the paginator is exhausted, and later advances
raise `StopIteration` or `StopAsyncIteration` without sending a request.
Breaking out of a loop sends no further requests. A paginator never closes the
client, and it does nothing in the background.

## Implementation

The pagination rules live once in a private `smithy_core._pagination` module:
building each request, reading tokens and items, deciding to continue, and the
repeated-token check. `smithy_core.pagination` and `smithy_core.aio.pagination`
hold the sync and async adapters, per [async and sync
duality](async-and-sync-duality.md). `PaginationError` is a `SmithyError` in
`smithy_core.exceptions`.

Generated factories pass the runtime the built input, the bound ordinary
operation method, the `plugins` argument, and a generated description:
`input_token`, the input token's Python member name, and `output_token` and
`items`, paths of Python member names. Runtime schemas need not retain the
trait. The factory's return annotation supplies the item type, which the
runtime can't infer.

Factory names come from the operation's generated method name with a
`paginate_` prefix. Ordinary operation names are allocated first and never
change. Then each paginator name gets trailing underscores until it is free of
operation names, inherited client members, and other paginator names. All
preferred paginator names are reserved before any is suffixed, so allocation
does not depend on operation order. Generated modules import runtime and typing
names under aliases chosen by the writer, so model names cannot shadow them.

The native generator resolves the effective trait while generating the client.
It assumes a valid model and checks only what it needs to generate code.
Generation fails, naming the operation, if the effective trait has no input or
output token, the input token is not an input member, a token or items path
names a member missing from a structure or passes through a non-structure, the
output token targets neither a string nor a map, or the items target neither a
list nor a map. Page size is not checked or used: it stays an ordinary input
member. Native generation still rejects streaming operations, so it cannot
generate a paginator for one. The generator imports no runtime packages and
stays standard-library only.

The Java generator generates the same factories. It reads the effective
settings from Smithy's `PaginatedIndex`, which also checks that they resolve to
members, and maps member names through `PythonSymbolProvider`. It names
factories by the same allocation, with `close` as the inherited client member,
and allocates paginator names in shape ID order. It generates no factory for
event stream operations, or for operations with a streaming input member:
requests can't be replayed from a stream input.

## Differences from botocore

botocore's `client.get_paginator(name).paginate(...)` is built from separate
paginator JSON files and covers controls Smithy models don't. This design
follows the Smithy trait instead.

| botocore                                                     | Here                                                                  |
| ------------------------------------------------------------ | --------------------------------------------------------------------- |
| `get_paginator("list_cities")` string lookup                 | A typed method per operation                                          |
| `PaginationConfig` `MaxItems`, `PageSize`, `StartingToken`   | The modeled page size and token members only                          |
| Opaque resume tokens that encode mid-page offsets            | The service's own token, read from a page                             |
| `build_full_result()` merges pages                           | No merging. Pages are complete outputs                                |
| JMESPath result and token expressions, `more_results` flags  | Member paths from the trait. The token alone decides when to continue |
| Several result keys, compound input tokens                   | One items path, one token member                                      |
| A repeated token raises after its page                       | The same, compared with the previous output token only                |
| Map tokens, such as DynamoDB keys, are supported             | Also supported, and deep-copied before its page is returned           |

botocore AWS paginators that rely on `more_results`, compound tokens, or
expression tokens are not reproduced from Smithy models. They need their own
customization design.

## Non-goals

- Limits on the total number of items or pages, and item slicing.
- Resume tokens beyond the service's own token.
- Prefetching, background tasks, or any resources the paginator owns.
- Collecting or merging pages.
- JMESPath or other expression evaluation.
- Termination rules specific to particular services.
- Cycle detection beyond consecutive repeated tokens.
- Replaying streaming inputs.
