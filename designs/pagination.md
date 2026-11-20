# Pagination

## Summary

This document proposes generating a `paginate_<operation>` method for each
operation with Smithy's `@paginated` trait. These methods return lazy, typed
iterators over complete response pages. When the model identifies an item
collection, the paginator also provides `.items()` to iterate over that
collection across pages. Ordinary operation methods continue to make a single
request.

## Motivation

Customers currently have to read continuation tokens and pass them into
subsequent requests. Each loop must preserve the original parameters, handle
the service's token type, and continue through empty pages when a token is
present. For example, paginating a DynamoDB scan requires:

```python
start_key = None
while True:
    page = await client.scan(
        table_name="orders",
        exclusive_start_key=start_key,
    )
    for item in page.items or []:
        process(item)
    start_key = page.last_evaluated_key
    if not start_key:
        break
```

The model already describes how to make the next request. Generated pagination
methods remove this repeated code without changing response models or requiring
customers to look up an operation by name.

## Proposal

### Response pages

Each paginated operation gets a method with a `paginate_` prefix. It accepts the
same input parameters and per-call plugins as the ordinary operation:

```python
async for page in client.paginate_scan(table_name="orders", limit=100):
    for item in page.items or []:
        process(item)
    print(page.response_metadata.request_id)
```

Each page is the operation's output model, including response metadata and any
additional result collections. Requests run through the normal client pipeline,
so authentication, retries, interceptors, and operation plugins apply to each
page.

The factory validates the input but sends no request. The first request is sent
when iteration starts, and subsequent pages are fetched only as needed. Neither
`paginate_scan()` nor `.items()` is awaited; `async for` awaits each advance.

### Items

When the model identifies an item collection, customers can iterate over its
items directly:

```python
async for item in client.paginate_scan(table_name="orders", limit=100).items():
    process(item)
```

The iterator's item type is available to type checkers. Lists yield their
elements; maps yield `(key, value)` pairs. Items are not merged or deduplicated
across pages.

Some operations do not identify an item collection. These paginators have no
`.items()` method, and type checkers flag attempts to call it. Page iteration
still works. Customers select the collection they want rather than the SDK
choosing one:

```python
async for page in s3.paginate_list_objects_v2(bucket="reports"):
    for obj in page.contents or []:
        process(obj)
```

### Synchronous clients

Synchronous clients expose the same methods, consumed with `for`:

```python
for item in client.paginate_scan(table_name="orders").items():
    process(item)
```

### Iterator lifetime

This proposal uses single-use iterators. Pages and `.items()` consume the same
traversal; a second loop does not restart it. Customers create a new paginator
for another pass. Responses are not cached.

Breaking out of a loop sends no further requests. The paginator does not own or
close the client, which must remain open during iteration. Service errors and
cancellation propagate to the caller and end the traversal.

### Page size and continuation

Page-size and starting-token parameters retain their modeled names. DynamoDB's
`limit`, for example, is a per-request limit, not a total item limit. Customers
can start from a saved service token using the ordinary input parameter. The
paginator does not modify caller-owned inputs or yielded responses.

An empty item collection does not end pagination while a continuation token
remains. Pagination ends when the output token is absent or empty. Consecutive
repeated output tokens raise `PaginationError` after yielding the repeated page.

This proposal does not add total-item limits, combined results, or encoded SDK
resume tokens. AWS-specific termination flags and other pagination rules not
represented by the Smithy trait require separate customization.

### Alternatives considered

* `iter_<operation>` is shorter, but does not distinguish page iteration from
  item iteration. `paginate_` names the additional behavior without adding a
  second method family.
* Item-first iteration makes the common item case shorter, but the model does
  not always identify a collection. Page-first iteration has the same meaning
  for every paginated operation and preserves all response fields.
* Reusable iterables could start independent requests on each pass. This
  proposal instead uses an explicit new factory call to restart, avoiding
  repeated network requests from looping over the same object again.
