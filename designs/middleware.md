# Abstract

This document will describe the middleware interfaces that will be provided as
part of the smithy-python package. These interfaces will serve as the basis for
implementing extensible code generated service clients from Smithy models.

# Motivation

The service clients generated as part of a Smithy SDK have many operations that
have largely shared logic and interfaces and look something like the following:

```python
def operation(param: OperationInput) -> OperationOutput:
    endpoint = resolve_endpoint()
    headers, body = serialize_params(params)
    request = create_request(endpoint, headers, body)
    request_signature = sign_request(request)
    request.headers.update(request_signature)
    while retry:
        response = send_http_request(request)
    return deserialize_response(response)
```

By implementing the above logic as a middleware stack we can produce highly
extensible service clients by breaking up operations into discrete pieces of
the request/response lifecycle logic as independent middleware, where
additional custom logic can be registered in between the default steps.

```python
def operation(param: OperationInput) -> OperationOutput:
    middlewares = [
        resolve_endpoint_middleware,
        serialize_params_middleware,
        create_request_middleware,
        sign_request_middleware,
        send_request_middleware,
    ]
    # Build up a chain of handlers to go from OperationInput -> OperationOutput
    chain = middleware_chain(deserialize_response_handler, *middlewares)
    return chain(params)
```

# Specification

## Middleware Primitives

To begin we'll define the core mechanisms powering Smithy middleware using two
simple interfaces "handlers" and "middleware":

### Handlers

Handlers are a function over a generic input and output, and will typically
have a reference to the next handler in the middleware chain to continue the
execution of the chain. Defined in Python as:

```python
Input = TypeVar("Input")
Output = TypeVar("Output")

# A "handler" is a generic function over some input/output
Handler = Callable[[Input], Output]
```

### Middleware

Middleware is a higher-order function that creates a closure over a handler
providing the context of the next handler in the middleware chain to be called.
In other words, middleware is a factory function that connects two handlers of
the same interface to produce a new handler. Defined in Python as:

```python
# A "middleware" is higher order function that can link two handlers by
# creating a new handler via a closure given the next handler in the chain
Middleware = Callable[[Handler[Input, Output]], Handler[Input, Output]]
```

### Middleware Chain

A middleware chain is simply a list of middleware that have been resolved to a
single handler. There are a few ways to do this but the basic interface we will
be using to generate a handler from a list of middleware is as follows:

```python
def chain_middleware(
    terminal: Handler[Input, Output], *args: Middleware[Input, Output]
) -> Handler[Input, Output]:
    ...
```

In addition to the list of middleware, we take a "terminal" handler. This is a
bare handler that is used directly to end the middleware chain. While it is
possible to implement the chain without a terminal handler, it imposes
unnecessary constraints on the middleware and handler definitions such as
requiring the handler to understand if it's last, or requiring the handler to
understand if there is a next handler to call. The last handler is ultimately
responsible for constructing and returning the Output object and thus has no
intention of calling the next handler. Given this unique property, it makes
sense to treat the terminal handler as slightly special and guarantee that the
last handler registered in the chain is one that understands how to terminate
the chain.

### Middleware Example

Given the definition of a `Handler` and `Middleware` the simplest middleware
definition looks something like the following:

```python
# In practice Input & Output will be concrete types
# middleware is of type Middleware[Input, Output]
def middleware(next_handler: Handler[Input, Output]) -> Handler[Input, Output]:
    def handler(param: Input) -> Output:
        # Perform handler logic before the next handler
        result = next_handler(param)
        # Perform handler logic after the next handler
        return result
    return handler
```

Note that this is the simplest middleware definition and not the most ergonomic
or easy to use. Because we've defined handlers and middleware as generic
aliases over a `Callable` the ultimate interface used is completely up to the
end user so long as it is compatible with the `Callable` interface defined. As
we begin to implement middleware and patterns emerge we can provide helper
methods, decorators, or more declarative class based interfaces that implement
the `Callable` interface to make defining middleware more ergonomic.

### Middleware Chain Example

Given these definitions, we could define the original `operation` in the
motivation section as follows:

```python
def operation(param: OperationInput) -> OperationOutput:
    middlewares = [
        resolve_endpoint_middleware,
        serialize_params_middleware,
        create_request_middleware,
        sign_request_middleware,
        send_request_middleware,
    ]
    # Buildup a chain of handlers to go from OperationInput -> OperationOutput
    chain = chain_middleware(deserialize_response_handler, *middlewares)
    return chain(param)
```

If we expose the list of middlewares, end users of the `operation` function
could inject or remove middleware to modify the behavior of the function at
runtime.

## Smithy Stack

The base middleware definitions are completely generic and can be used to
implement any function. However, in the context of a Smithy service client
we know that middleware will be used in a specific use case to facilitate
performing a request/response lifecycle against an API. To do this, we can
leverage the generic middleware definitions and begin to enforce some structure
onto the usage of middleware within smithy-python. To do this we will introduce
an additional interface known as a `SmithyStack`.

### SmithyCollection & SmithyEntry

Thus far all examples of a middleware chain have used a plain Python `list` to
define the collection of middleware. In practice, we need a more sophisticated
interface that better supports more complex use cases for adding and removing
middleware to the stack, and generating the ordered list of middleware. To do
this we will introduce two new interfaces: `SmithyEntry` and
`SmithyCollection`.

A `SmithyEntry` is a generic wrapper over some value, tagging it with a
specific name. Defined in Python as:

```python
EntryType = TypeVar("EntryType")

class SmithyEntry(Generic[EntryType]):
    entry: EntryType
    name: str
```

A `SmithyCollection` is a generic collection of `SmithyEntry` that can be used
to add or remove entries, and ultimately produce an ordered list of the
entries. Defined in Python as:

```python
class SmithyCollection(Generic[EntryType]):
    @property
    def entries(self) -> List[SmithyEntry[EntryType]]:
        # Generate the ordered list of entries
        ...

    def add_before(
        self, entry: SmithyEntry[EntryType], name: Optional[str] = None
    ) -> None:
        # Insert this entry before another entry, or first by default
        ...

    def add_after(
        self, entry: SmithyEntry[EntryType], name: Optional[str] = None
    ) -> None:
        # Insert this entry after another entry, or last by default
        ...
```

For now, the interface will be minimal allowing for inserting before or after
other entries and a property to produce the ordered list of entries. Over time
we can continue to build on these interfaces to introduce additional metadata
such as tags, and additional methods on the collection to allow for more
complex operations such as merges, or more nuanced relationships.

### SmithyStack

A `SmithyStack` is an opinionated interface for defining a handler over a
service operation's input/output and makes certain assertions about the
request/response lifecycle. These assumptions provide a solid framework for
defining, registering, and building a middleware chain. This stack interface
closely resembles the middleware stack interfaces exposed by
[smithy-typescript][smithy-typescript-stack] and [smithy-go][smithy-go-stack],
only deviating where necessary to work within the constraints of typing in
Python.

Conceptually, a `SmithyStack` is broken up into five concrete steps:
initialize, serialize, build, finalize, and deserialize:

* Initialize - Makes any modifications to the input parameter that is needed
  to prepare it for serialization.
* Serialize - Converts the input parameter into a [`Request`][http-interfaces]
  object.
* Build - Further modifies the built `Request` with more stable aspects of the
  request such as the `User-Agent` header, etc.
* Finalize - Finalizes the request by adding any last modifications to the
  request that may be unstable such as signatures, and ultimately resolves the
  request into a [`Response`][http-interfaces].
* Deserialize - Converts the `Response` object into the appropriate output
  object for the operation.

By formalizing these steps, we can provide more concrete interfaces for what
the input and output of a middleware definition for a particular step is. The
following define the generic inputs and outputs of the steps in Python:

```python
Context = Dict[Any, Any]

# Step Inputs
class InitializeInput(Generic[Input]):
    input: Input
    context: Context

class SerializeInput(Generic[Input]):
    input: Input
    context: Context
    request: Optional[Request]

class BuildInput(Generic[Input]):
    input: Input
    context: Context
    request: Request

class FinalizeInput(Generic[Input]):
    input: Input
    context: Context
    request: Request
    response: Optional[Response]

class DeserializeInput(Generic[Input]):
    input: Input
    context: Context
    request: Request
    response: Response

# Step Outputs
class InitializeOutput(Generic[Output]):
    output: Output

class SerializeOutput(Generic[Output]):
    output: Output

class BuildOutput(Generic[Output]):
    output: Output

class FinalizeOutput(Generic[Output]):
    output: Output

class DeserializeOutput(Generic[Output]):
    output: Output
```

In general, the input and output steps build up on top of each other as you go
through the steps. However, it's important to note that these are objects are
discrete and can have completely independent interfaces. This gives us the
flexibility to only expose the exact context for that step that we expect the
step to need.

For convenience, we can also define typing aliases for how handlers and
middleware are defined:

```python
# Step Handlers
InitializeHandler = Handler[InitializeInput[Input], InitializeOutput[Output]]
SerializeHandler = Handler[SerializeInput[Input], SerializeOutput[Output]]
BuildHandler = Handler[BuildInput[Input], BuildOutput[Output]]
FinalizeHandler = Handler[FinalizeInput[Input], FinalizeOutput[Output]]
DeserializeHandler = Handler[DeserializeInput[Input], DeserializeOutput[Output]]

# Step Middlewares
InitializeMiddleware = Middleware[InitializeInput[Input], InitializeOutput[Output]]
SerializeMiddleware = Middleware[SerializeInput[Input], SerializeOutput[Output]]
BuildMiddleware = Middleware[BuildInput[Input], BuildOutput[Output]]
FinalizeMiddleware = Middleware[FinalizeInput[Input], FinalizeOutput[Output]]
DeserializeMiddleware = Middleware[DeserializeInput[Input], DeserializeOutput[Output]]
```

Next we can formalize a Smithy "step" more concretely by combining the step
inputs and outputs with the `SmithyCollection` interface:

```python
# Steps
InitializeStep = SmithyCollection[InitializeMiddleware[Input, Output]]
SerializeStep = SmithyCollection[SerializeMiddleware[Input, Output]]
BuildStep = SmithyCollection[BuildMiddleware[Input, Output]]
FinalizeStep = SmithyCollection[FinalizeMiddleware[Input, Output]]
DeserializeStep = SmithyCollection[DeserializeMiddleware[Input, Output]]
```

Now tying everything together we can define a `SmithyStack` as follows:

```python
class SmithyStack(Generic[Input, Output]):
    initialize: InitializeStep[Input, Output]
    serialize: SerializeStep[Input, Output]
    build: BuildStep[Input, Output]
    finalize: FinalizeStep[Input, Output]
    deserialize: DeserializeStep[Input, Output]

    def resolve(
        self,
        terminal: DeserializeHandler[Input, Output],
        context: Optional[Context] = None,
    ) -> Handler[Input, Output]:
        # Create a middleware chain for each step, and combine them to create
        # a single handler over the Input and Output type.
        ...
```

The `SmithyStack` will handle registering middleware to the steps through the
`SmithyCollection` interface. The `resolve` method will handle creating a
single handler from all of the middleware chains of each independent step,
automatically injecting shims to bridge the gap between steps, and enforcing
that any expectations of a step have been fulfilled. For example, the stack
will enforce that a middleware has populated the request field before the build
step, etc. which allows middleware at the build step to not have to worry about
checking if the request has been populated.

### SmithyStack Example

The following is a concrete example showing what usage of a `SmithyStack` looks
like:

```python
def serialize_request(
    next_handler: SerializeHandler[OperationInput, OperationOutput]
) -> SerializeHandler[OperationInput, OperationOutput]:
    def _serialize_request(
        serialize: SerializeInput[OperationInput],
    ) -> SerializeOutput[OperationOutput]:
        request: Request = convert_to_request(serialize.input)
        serialize.request = request
        return next_handler(serialize)

    return _serialize_request


def operation(param: OperationInput) -> OperationOutput:
    stack = SmithyStack[OperationInput, OperationOutput]()
    # register middleware
    stack.serialize.add_after(SmithyEntry(serialize_request, name="serialize_request"))
    ...
    # Provide any context needed by the middleware, e.g. configuration,
    # credential resolver, endpoint resolver, etc.
    context: Context = {}
    handler = stack.resolve(deserialize_response, context)
    return handler(param)
```

As noted before, this is the simplest/most verbose definition. As we begin to
see patterns emerge we can provide simplified interfaces that automatically
construct a `SmithyEntry` via helper functions, decorators, classes, etc.

## Async Middleware

Because the definition of the synchronous handlers and middleware are generic,
it's straightforward to extend them to support asynchronous definitions:

```python
# Async middleware primitives
AsyncHandler = Handler[Input, Awaitable[Output]]

AsyncMiddleware = Middleware[Input, Awaitable[Output]]
```

Consequently, this definition bleeds down the typing and there are async
variants of the step specific handler, middleware, and step interfaces:

```python
# AsyncStep Handlers
AsyncInitializeHandler = AsyncHandler[InitializeInput[Input], InitializeOutput[Output]]
AsyncSerializeHandler = AsyncHandler[SerializeInput[Input], SerializeOutput[Output]]
AsyncBuildHandler = AsyncHandler[BuildInput[Input], BuildOutput[Output]]
AsyncFinalizeHandler = AsyncHandler[FinalizeInput[Input], FinalizeOutput[Output]]
AsyncDeserializeHandler = AsyncHandler[
    DeserializeInput[Input], DeserializeOutput[Output]
]

# AsyncStep middlewares
AsyncInitializeMiddleware = AsyncMiddleware[
    InitializeInput[Input], InitializeOutput[Output]
]
AsyncSerializeMiddleware = AsyncMiddleware[
    SerializeInput[Input], SerializeOutput[Output]
]
AsyncBuildMiddleware = AsyncMiddleware[BuildInput[Input], BuildOutput[Output]]
AsyncFinalizeMiddleware = AsyncMiddleware[FinalizeInput[Input], FinalizeOutput[Output]]
AsyncDeserializeMiddleware = AsyncMiddleware[
    DeserializeInput[Input], DeserializeOutput[Output]
]

# Async Steps
AsyncInitializeStep = SmithyCollection[AsyncInitializeMiddleware[Input, Output]]
AsyncSerializeStep = SmithyCollection[AsyncSerializeMiddleware[Input, Output]]
AsyncBuildStep = SmithyCollection[AsyncBuildMiddleware[Input, Output]]
AsyncFinalizeStep = SmithyCollection[AsyncFinalizeMiddleware[Input, Output]]
AsyncDeserializeStep = SmithyCollection[AsyncDeserializeMiddleware[Input, Output]]
```

For clarity, these aliases are simply for convenience and async middleware can
all be directly defined using the base handler and middleware definitions.

In contrast, a distinct interface for an async `SmithyStack` does need to
exist:

```python
class AsyncSmithyStack(Generic[Input, Output]):
    initialize: AsyncInitializeStep[Input, Output]
    serialize: AsyncSerializeStep[Input, Output]
    build: AsyncBuildStep[Input, Output]
    finalize: AsyncFinalizeStep[Input, Output]
    deserialize: AsyncDeserializeStep[Input, Output]

    def resolve(
        self,
        terminal: AsyncDeserializeHandler[Input, Output],
        context: Optional[Context] = None,
    ) -> AsyncHandler[Input, Output]:
        # Create a middleware chain for each step, and combine them to create
        # a single handler over the Input and Output type.
        ...
```

# FAQs

## Why make `SmithyEntry` and `SmithyCollection` generic?

These interfaces were originally broken out and decoupled from middleware
entirely as more tightly coupling the two interfaces was causing issues making
the collection definition shared across all of the steps. The simplest way to
make the collection generic across all steps was to decouple them entirely.
This also has some additional benefits:

* The definitions of middleware logic is completely decoupled from the metadata
  surrouding those middleware. This keeps the base middleware definition very
  flexible.
* The collection definition doesn't need to be coupled to middleware. This
  allows the definition to be potentially reused in other contexts.

## Why are the `mypy` errors so verbose?

Because `mypy` flattens type aliases, the typing errors can get quite verbose
for some of the higher level abstractions (e.g. `SmithyStack`). This is a
[known issue][mypy-alias-errors].

## Why have discrete fields for each step on the stack?

Alternatives where the stack is forced to be more homogenous across steps
ultimately lead to disabling type checking. Typescript's implementation of the
stack treats all middleware more generically and the "step" is just metadata
that's used when sorting the list of middlewares. This has the unfortunate
consequence that parts of the stack middleware construction are not typed or
the type checking is disabled. Another factor is `mypy` seems to be more strict
in regards to covariance / contravariance which makes it not feasible to
construct compatible input / output definitions for the steps.  This means even
if we could define compatible input / output objects for each step, we still
need explicit handlers bridging the steps anyways.

## Why is Context a generic dictionary?

The context for now is defined as a generic dictionary to provide the most
flexibility as we work out the more concrete aspects of a stack's execution
context. It's likely the step inputs will have a more formalized field that
represents a stack's execution context including typed references to things
like the client's credential resolver, endpoint resolver, etc. Even once we add
a more formal context, the generic context is still useful for external
middleware to have a place to store context it wants to share between
middleware across different steps.

## Why are `AsyncMiddleware` not async functions?

A middleware function's sole purpose is to provide a closure over a handler,
providing a reference to the next handler in the chain. I cannot think of a
good reason that this logic would need to be asynchronous and it has some
benefits in that the asynchronous and synchronous middleware definitions are
the same. This means that even for asynchronous middleware the modification
and construction of the stack handler is completely synchronous in both cases.

[smithy-go-stack]: https://github.com/aws/smithy-go/blob/main/middleware/stack.go
[smithy-typescript-stack]: https://github.com/aws/aws-sdk-js-v3/blob/main/packages/middleware-stack/src/MiddlewareStack.ts
[http-interfaces]: https://github.com/awslabs/smithy-python/blob/develop/designs/http-interfaces.md#request-and-response-interfaces
[mypy-alias-errors]: https://github.com/python/mypy/issues/2968
