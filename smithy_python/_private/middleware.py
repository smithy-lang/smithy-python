# Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.


from typing import TypeVar, Callable, Generic, Dict, Any, Optional, List, Awaitable

from smithy_python.interfaces.http import Request, Response
from smithy_python._private.collection import SmithyCollection

Input = TypeVar("Input")
Output = TypeVar("Output")

# A "handler" is a generic function over some input/output
Handler = Callable[[Input], Output]

# A "middleware" is higher order function that can link two handlers by
# creating a new handler via a closure given the next handler in the chain
Middleware = Callable[[Handler[Input, Output]], Handler[Input, Output]]

def chain_middleware(terminal: Handler[Input, Output], *args: Middleware[Input, Output]) -> Handler[Input, Output]:
    middlewares = list(args)
    # Reverse the middlewares to build up the chain from the last handler
    middlewares.reverse()
    # Last handler is special as it returns a real response to end the chain
    handler = terminal
    for middleware in middlewares:
        handler = middleware(handler)
    return handler


# Step Inputs
class InitializeInput(Generic[Input]):
    def __init__(self, *, param: Input) -> None:
        self.input: Input = param

class SerializeInput(Generic[Input]):
    def __init__(self, *, param: Input, request: Optional[Request] = None) -> None:
        self.input: Input = param
        self.request: Optional[Request] = request

class BuildInput(Generic[Input]):
    def __init__(self, *, param: Input, request: Request) -> None:
        self.input: Input = param
        self.request: Request = request

class FinalizeInput(Generic[Input]):
    def __init__(self, *, param: Input, request: Request, response: Optional[Response] = None) -> None:
        self.input: Input = param
        self.request: Request = request
        self.response: Optional[Response] = response

class DeserializeInput(Generic[Input]):
    def __init__(self, *, param: Input, request: Request, response: Response) -> None:
        self.input: Input = param
        self.request: Request = request
        self.response: Response = response


# Step Outputs
class InitializeOutput(Generic[Output]):
    def __init__(self, *, output: Output) -> None:
        self.output: Output = output

class SerializeOutput(Generic[Output]):
    def __init__(self, *, output: Output) -> None:
        self.output: Output = output

class BuildOutput(Generic[Output]):
    def __init__(self, *, output: Output) -> None:
        self.output: Output = output

class FinalizeOutput(Generic[Output]):
    def __init__(self, *, output: Output) -> None:
        self.output: Output = output

class DeserializeOutput(Generic[Output]):
    def __init__(self, *, output: Output) -> None:
        self.output: Output = output


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

# Steps
InitializeStep = SmithyCollection[InitializeMiddleware[Input, Output]]
SerializeStep = SmithyCollection[SerializeMiddleware[Input, Output]]
BuildStep = SmithyCollection[BuildMiddleware[Input, Output]]
FinalizeStep = SmithyCollection[FinalizeMiddleware[Input, Output]]
DeserializeStep = SmithyCollection[DeserializeMiddleware[Input, Output]]


class SmithyStack(Generic[Input, Output]):
    """A SmithyStack is composed of five high level Steps. The occur in
    sequential order and each step can implement any number of ordered
    middlewares.

    The steps are as follows:

    initialize: The initialize step is any middlewares that need to be utilized
        before the input is acted upon by the stack. You can think of this as
        a pre-step.

    serialize: The serialize step is where all serialization occurs. Any
        transformation required before transmission should be done here.

    build: The build step is where all components are assembled for
        transmission to the end destination. e.g. Request construction,
        data assembly, etc.

    finalize: The finalize step is where any required post-processing
        is performed prior to transmission.

    deserialize: The deserialize step is where data is handed off to
        an external component and any response is processed into an
        expected format.
    """
    def __init__(self) -> None:
        self.initialize: InitializeStep[Input, Output] = SmithyCollection()
        self.serialize: SerializeStep[Input, Output] = SmithyCollection()
        self.build: BuildStep[Input, Output] = SmithyCollection()
        self.finalize: FinalizeStep[Input, Output] = SmithyCollection()
        self.deserialize: DeserializeStep[Input, Output] = SmithyCollection()

    def resolve(self, terminal: DeserializeHandler[Input, Output]) -> Handler[Input, Output]:
        return self._build_deserialize_chain(terminal)

    def _build_deserialize_chain(self, terminal: DeserializeHandler[Input, Output]) -> Handler[Input, Output]:
        middlewares = [m.entry for m in self.deserialize.entries]
        deserialize_chain = chain_middleware(terminal, *middlewares)
        def _deserialize_bridge(finalize_in: FinalizeInput[Input]) -> FinalizeOutput[Output]:
            assert finalize_in.response is not None
            deserialize_in = DeserializeInput(
                param=finalize_in.input,
                request=finalize_in.request,
                response=finalize_in.response,
            )
            deserialize_out = deserialize_chain(deserialize_in)
            return FinalizeOutput(output=deserialize_out.output)
        return self._build_finalize_chain(_deserialize_bridge)

    def _build_finalize_chain(self, terminal: FinalizeHandler[Input, Output]) -> Handler[Input, Output]:
        middlewares = [m.entry for m in self.finalize.entries]
        finalize_chain = chain_middleware(terminal, *middlewares)
        def _finalize_bridge(build_in: BuildInput[Input]) -> BuildOutput[Output]:
            finalize_in = FinalizeInput(
                param=build_in.input,
                request=build_in.request,
            )
            finalize_out = finalize_chain(finalize_in)
            return BuildOutput(output=finalize_out.output)
        return self._build_build_chain(_finalize_bridge)

    def _build_build_chain(self, terminal: BuildHandler[Input, Output]) -> Handler[Input, Output]:
        middlewares = [m.entry for m in self.build.entries]
        build_chain = chain_middleware(terminal, *middlewares)
        def _build_bridge(serialize_in: SerializeInput[Input]) -> SerializeOutput[Output]:
            assert serialize_in.request is not None
            build_in = BuildInput(
                param=serialize_in.input,
                request=serialize_in.request,
            )
            build_out = build_chain(build_in)
            return SerializeOutput(output=build_out.output)
        return self._build_serialize_chain(_build_bridge)

    def _build_serialize_chain(self, terminal: SerializeHandler[Input, Output]) -> Handler[Input, Output]:
        middlewares = [m.entry for m in self.serialize.entries]
        serialize_chain = chain_middleware(terminal, *middlewares)
        def _serialize_bridge(initialize_in: InitializeInput[Input]) -> InitializeOutput[Output]:
            serialize_in = SerializeInput(param=initialize_in.input)
            serialize_out = serialize_chain(serialize_in)
            return InitializeOutput(output=serialize_out.output)
        return self._build_initialize_chain(_serialize_bridge)

    def _build_initialize_chain(self, terminal: InitializeHandler[Input, Output]) -> Handler[Input, Output]:
        middlewares = [m.entry for m in self.initialize.entries]
        initialize_chain = chain_middleware(terminal, *middlewares)
        def _initialize_bridge(param: Input) -> Output:
            initialize_in = InitializeInput(param=param)
            initialize_out = initialize_chain(initialize_in)
            return initialize_out.output
        return _initialize_bridge

# Async middleware primitives
AsyncHandler = Handler[Input, Awaitable[Output]]
AsyncMiddleware = Middleware[Input, Awaitable[Output]]

# AsyncStep Handlers
AsyncInitializeHandler = AsyncHandler[InitializeInput[Input], InitializeOutput[Output]]
AsyncSerializeHandler = AsyncHandler[SerializeInput[Input], SerializeOutput[Output]]
AsyncBuildHandler = AsyncHandler[BuildInput[Input], BuildOutput[Output]]
AsyncFinalizeHandler = AsyncHandler[FinalizeInput[Input], FinalizeOutput[Output]]
AsyncDeserializeHandler = AsyncHandler[DeserializeInput[Input], DeserializeOutput[Output]]

# AsyncStep middlewares
AsyncInitializeMiddleware = AsyncMiddleware[InitializeInput[Input], InitializeOutput[Output]]
AsyncSerializeMiddleware = AsyncMiddleware[SerializeInput[Input], SerializeOutput[Output]]
AsyncBuildMiddleware = AsyncMiddleware[BuildInput[Input], BuildOutput[Output]]
AsyncFinalizeMiddleware = AsyncMiddleware[FinalizeInput[Input], FinalizeOutput[Output]]
AsyncDeserializeMiddleware = AsyncMiddleware[DeserializeInput[Input], DeserializeOutput[Output]]

# Async Steps
AsyncInitializeStep = SmithyCollection[AsyncInitializeMiddleware[Input, Output]]
AsyncSerializeStep = SmithyCollection[AsyncSerializeMiddleware[Input, Output]]
AsyncBuildStep = SmithyCollection[AsyncBuildMiddleware[Input, Output]]
AsyncFinalizeStep = SmithyCollection[AsyncFinalizeMiddleware[Input, Output]]
AsyncDeserializeStep = SmithyCollection[AsyncDeserializeMiddleware[Input, Output]]

class AsyncSmithyStack(Generic[Input, Output]):
    """A SmithyStack is composed of five high level Steps. The occur in
    sequential order and each step can implement any number of ordered
    middlewares.

    The steps are as follows:

    initialize: The initialize step is any middlewares that need to be utilized
        before the input is acted upon by the stack. You can think of this as
        a pre-step.

    serialize: The serialize step is where all serialization occurs. Any
        transformation required before transmission should be done here.

    build: The build step is where all components are assembled for
        transmission to the end destination. e.g. Request construction,
        data assembly, etc.

    finalize: The finalize step is where any required post-processing
        is performed prior to transmission.

    deserialize: The deserialize step is where data is handed off to
        an external component and any response is processed into an
        expected format.
    """
    def __init__(self) -> None:
        self.initialize: AsyncInitializeStep[Input, Output] = SmithyCollection()
        self.serialize: AsyncSerializeStep[Input, Output] = SmithyCollection()
        self.build: AsyncBuildStep[Input, Output] = SmithyCollection()
        self.finalize: AsyncFinalizeStep[Input, Output] = SmithyCollection()
        self.deserialize: AsyncDeserializeStep[Input, Output] = SmithyCollection()

    def resolve(self, terminal: AsyncDeserializeHandler[Input, Output]) -> AsyncHandler[Input, Output]:
        return self._build_deserialize_chain(terminal)

    def _build_deserialize_chain(self, terminal: AsyncDeserializeHandler[Input, Output]) -> AsyncHandler[Input, Output]:
        middlewares = [m.entry for m in self.deserialize.entries]
        deserialize_chain = chain_middleware(terminal, *middlewares)
        async def _deserialize_bridge(finalize_in: FinalizeInput[Input]) -> FinalizeOutput[Output]:
            assert finalize_in.response is not None
            deserialize_in = DeserializeInput(
                param=finalize_in.input,
                request=finalize_in.request,
                response=finalize_in.response,
            )
            deserialize_out = await deserialize_chain(deserialize_in)
            return FinalizeOutput(output=deserialize_out.output)
        return self._build_finalize_chain(_deserialize_bridge)

    def _build_finalize_chain(self, terminal: AsyncFinalizeHandler[Input, Output]) -> AsyncHandler[Input, Output]:
        middlewares = [m.entry for m in self.finalize.entries]
        finalize_chain = chain_middleware(terminal, *middlewares)
        async def _finalize_bridge(build_in: BuildInput[Input]) -> BuildOutput[Output]:
            finalize_in = FinalizeInput(
                param=build_in.input,
                request=build_in.request,
            )
            finalize_out = await finalize_chain(finalize_in)
            return BuildOutput(output=finalize_out.output)
        return self._build_build_chain(_finalize_bridge)

    def _build_build_chain(self, terminal: AsyncBuildHandler[Input, Output]) -> AsyncHandler[Input, Output]:
        middlewares = [m.entry for m in self.build.entries]
        build_chain = chain_middleware(terminal, *middlewares)
        async def _build_bridge(serialize_in: SerializeInput[Input]) -> SerializeOutput[Output]:
            assert serialize_in.request is not None
            build_in = BuildInput(
                param=serialize_in.input,
                request=serialize_in.request,
            )
            build_out = await build_chain(build_in)
            return SerializeOutput(output=build_out.output)
        return self._build_serialize_chain(_build_bridge)

    def _build_serialize_chain(self, terminal: AsyncSerializeHandler[Input, Output]) -> AsyncHandler[Input, Output]:
        middlewares = [m.entry for m in self.serialize.entries]
        serialize_chain = chain_middleware(terminal, *middlewares)
        async def _serialize_bridge(initialize_in: InitializeInput[Input]) -> InitializeOutput[Output]:
            serialize_in = SerializeInput(param=initialize_in.input)
            serialize_out = await serialize_chain(serialize_in)
            return InitializeOutput(output=serialize_out.output)
        return self._build_initialize_chain(_serialize_bridge)

    def _build_initialize_chain(self, terminal: AsyncInitializeHandler[Input, Output]) -> AsyncHandler[Input, Output]:
        middlewares = [m.entry for m in self.initialize.entries]
        initialize_chain = chain_middleware(terminal, *middlewares)
        async def _initialize_bridge(param: Input) -> Output:
            initialize_in = InitializeInput(param=param)
            initialize_out = await initialize_chain(initialize_in)
            return initialize_out.output
        return _initialize_bridge
