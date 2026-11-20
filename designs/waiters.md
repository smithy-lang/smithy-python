# Waiters

## Summary

This document proposes generating a `wait_until_<waiter>` method for each
waiter defined with Smithy's `@waitable` trait. Each method polls an operation
until an acceptor reports success or failure, or until the caller's time limit
passes. The waiter definitions stay in the operation schemas. One shared
runtime evaluates them for synchronous, asynchronous, and dynamic clients.

## Motivation

Many resources take time to reach a usable state after they are created,
changed, or deleted. Customers currently write the polling loop themselves.
Each loop must classify responses and errors, choose delays, and stop at a
deadline. For example, waiting for a new DynamoDB table to become active
requires:

```python
deadline = time.monotonic() + 300
while True:
    try:
        response = await client.describe_table(table_name="orders")
    except ResourceNotFoundException:
        pass
    else:
        if response.table and response.table.table_status == "ACTIVE":
            break
    if time.monotonic() >= deadline:
        raise TimeoutError("The orders table did not become active.")
    await asyncio.sleep(20)
```

The model already describes the states to wait for and the delays between
attempts. Generated waiter methods remove this repeated code and give every
waiter the same timing and error behavior.

## Proposal

### Waiting

Each waiter gets a method named `wait_until_` followed by the snake_case waiter
name. It accepts the same input parameters and per-call plugins as the
operation it polls. It also requires the maximum number of seconds to wait:

```python
await client.wait_until_table_exists(table_name="orders", max_wait_time=300)
```

The first request is sent immediately. Requests run through the normal client
pipeline, so authentication, retries, interceptors, and plugins apply to each
attempt. The client's retry strategy handles throttling and transient errors
within an attempt. Only the attempt's final result reaches the acceptors.

On success, the method returns the output that matched. Waiters that succeed on
an error, such as `TableNotExists` on `ResourceNotFoundException`, return
`None`. The return type follows the waiter's success acceptors. It is the
operation's output, `None`, or their union when a waiter can succeed either way.

```python
output = await ec2.wait_until_instance_running(
    instance_ids=[instance_id], max_wait_time=600
)
for reservation in output.reservations or []:
    process(reservation)
```

### Wait time and delays

`max_wait_time` has no default. The Smithy specification requires callers to
choose it, so no waiter can run for an unbounded time. The limit covers both
request time and delays, measured with a monotonic clock.

Delays between attempts use the specification's exponential backoff with full
jitter. They start at the waiter's `minDelay` and grow toward its `maxDelay`,
which default to 2 and 120 seconds. Customers can replace either bound for a
call:

```python
await client.wait_until_table_exists(
    table_name="orders", max_wait_time=600, min_delay=5, max_delay=30
)
```

All three values are seconds as floats, like other timeouts in smithy-python.
Invalid values, such as a `min_delay` above `max_delay`, raise `ValueError`
before any request is sent. When the next delay would leave `min_delay` or less
before the limit, the waiter waits out the remaining time and makes one last
attempt. Its response is still checked against the acceptors.

The waiter doesn't cancel a request that is in flight at the limit, because the
specification schedules the last attempt at that moment. Client timeouts bound
each request. Async callers that need a hard limit can wrap the call in
`asyncio.timeout()`. Cancellation propagates to the caller and ends the wait.

### Failures

Waiters raise an exception for every outcome other than success. Both waiter
exceptions are in `smithy_core.exceptions` and inherit from `WaiterError`, a
`SmithyError`:

* `WaiterFailureError` means an acceptor moved the waiter to its failure state.
  For example, an EC2 instance terminated while the caller waited for it to
  run. When the acceptor has a modeled `message`, the exception message
  includes it.
* `WaiterTimeoutError` means the limit passed before any acceptor reported
  success or failure. It also inherits from the built-in `TimeoutError`.

Both exceptions carry the number of attempts and the last output, when the
last attempt returned one. When the last attempt raised an error, that error is
the exception's `__cause__`.

```python
try:
    await ec2.wait_until_instance_running(
        instance_ids=[instance_id], max_wait_time=600
    )
except WaiterFailureError as error:
    print(f"The instance failed to start after {error.attempts} attempts.")
```

An error that no acceptor matches ends the wait. It propagates unchanged, as it
would from the operation, so `except` clauses that name a service error still
apply. A missing permission, for example, raises the service's access error on
the first attempt.

### Matching

Acceptors are checked in model order after each attempt. The first match
decides the transition. When nothing matches, the waiter retries after a
successful response and raises the error after a failed one.

Paths use the member names in the model, such as `Table.TableStatus`. They are
evaluated against the output object directly, with each member name mapped to
its Python attribute. Enum members compare by value. A path through a missing
member produces null, which no comparator matches. `allStringEquals` and
`anyStringEquals` don't match an empty list. `inputOutput` paths see an object
with `input` and `output` members.

The evaluator is `smithy_core._jmespath`, which already compiles operation
context parameter paths. Waiters extend it with comparisons, boolean operators,
filter projections, literals, and functions such as `length`. The generator
compiles every waiter expression and fails on any that the evaluator doesn't
support.

`errorType` matches when the expected name equals either the error's modeled
shape name or the error code the service returned. Error codes are required in
practice. EC2 models no errors, so its waiters match codes such as
`InvalidInstanceID.NotFound`. IAM waiters use both `NoSuchEntityException`, the
shape name, and `NoSuchEntity`, its awsQuery code. Protocols currently keep an
unmodeled error's code only in its message. This proposal adds an `error_code`
field to `ResponseMetadata`, which protocols set on every error.

### Model-driven runtime

Generated clients keep the `smithy.waiters#waitable` trait in each operation's
schema. A generated method passes the runtime its operation and waiter name.
The runtime reads the acceptors and delays from the schema. A dynamic client
can use the same runtime to wait on any modeled waiter without generated code.

Acceptor evaluation and delay calculation live in one shared state machine.
`smithy_core.waiters` and `smithy_core.aio.waiters` adapt it to blocking and
async calls. AWS clients record the `WAITER` feature ID in the User-Agent of
each attempt.

### Synchronous clients

Synchronous clients expose the same methods, which block between attempts:

```python
client.wait_until_table_exists(table_name="orders", max_wait_time=300)
```

### Names and documentation

Smithy requires waiter names to be unique within a service, ignoring case.
Waiter methods that conflict with other client methods are escaped like other
runtime conflicts. `max_wait_time`, `min_delay`, and `max_delay` are reserved
input member names on waitable operations, in the same way as `plugins`. No
AWS input uses them today.

A waiter's documentation becomes its method's docstring. Deprecated waiters are
marked with `@deprecated` from PEP 702. Type checkers flag their use. Calling
one emits a `DeprecationWarning`.

This proposal does not add attempt limits or user-defined waiters.

### Alternatives considered

* A `get_waiter("table_exists")` lookup, as in boto3, names waiters with
  strings. Type checkers can't check the name, the input, or the result.
* A waiter object per waiter, as in smithy-java, adds a step before each wait.
  Its settings fit in keyword arguments, which `functools.partial` can preset.
* Fixed delays and attempt counts, as in botocore, make the total wait depend
  on request latency. The Smithy specification defines a time limit and
  jittered backoff.
* A result object with the final state and attempt count, as in TypeScript and
  Swift, lengthens the common success case. The waiter exceptions carry the
  attempt count where it helps diagnose a problem.
* Compiling matchers to Python during generation, as Go, Rust, TypeScript, and
  Kotlin do, would keep the definitions only in generated code. Dynamic clients
  could not wait without that code.
* Wrapping unmatched errors in a waiter exception, as botocore and Rust do,
  would hide the service error from `except` clauses that name it.
