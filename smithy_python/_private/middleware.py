from typing import TypeVar, Callable, Generic, Dict, Any, Optional, List

from smithy_python.interfaces.http import Request

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
    def __init__(self, *, param: Input, request: Request) -> None:
        self.input: Input = param
        self.request: Request = request

class DeserializeInput(Generic[Input]):
    def __init__(self, *, param: Input, request: Request) -> None:
        self.input: Input = param
        self.request: Request = request


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


class SmithyMiddleware(Generic[Input, Output]):
    def __init__(self, middleware: Middleware[Input, Output], name: Optional[str] = None) -> None:
        self.middleware: Middleware[Input, Output] = middleware
        if name is None:
            name = self.__class__.__name__
        self.name: str = name


# Step Handlers
InitializeHandler = Handler[InitializeInput[Input], InitializeOutput[Output]]
SerializeHandler = Handler[SerializeInput[Input], SerializeOutput[Output]]
BuildHandler = Handler[BuildInput[Input], BuildOutput[Output]]
FinalizeHandler = Handler[FinalizeInput[Input], FinalizeOutput[Output]]
DeserializeHandler = Handler[DeserializeInput[Input], DeserializeOutput[Output]]


# Step middlewares
class InitializeMiddleware(SmithyMiddleware[InitializeInput[Input], InitializeOutput[Output]]):
    pass

class SerializeMiddleware(SmithyMiddleware[SerializeInput[Input], SerializeOutput[Output]]):
    pass

class BuildMiddleware(SmithyMiddleware[BuildInput[Input], BuildOutput[Output]]):
    pass

class FinalizeMiddleware(SmithyMiddleware[FinalizeInput[Input], FinalizeOutput[Output]]):
    pass

class DeserializeMiddleware(SmithyMiddleware[DeserializeInput[Input], DeserializeOutput[Output]]):
    pass


MiddlewareType = TypeVar("MiddlewareType", bound=SmithyMiddleware[Any, Any])


class SmithyStep(Generic[MiddlewareType]):
    def __init__(self) -> None:
        self._middlewares: List[MiddlewareType] = []

    @property
    def middlewares(self) -> List[MiddlewareType]:
        # TODO: In the future producing this list may be more difficult
        return list(self._middlewares)

    def _resolve_middleware_position(self, name: Optional[str], default_pos: int) -> int:
        for n, middleware in enumerate(self._middlewares):
            if middleware.name == name:
                return n
        return default_pos

    def add_before(self, middleware: MiddlewareType, name: Optional[str] = None) -> None:
        position = self._resolve_middleware_position(name, 0)
        self._middlewares.insert(position, middleware)

    def add_after(self, middleware: MiddlewareType, name: Optional[str] = None) -> None:
        position = self._resolve_middleware_position(name, len(self._middlewares))
        self._middlewares.insert(position, middleware)


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
        self.initialize: SmithyStep[InitializeMiddleware[Input, Output]] = SmithyStep()
        self.serialize: SmithyStep[SerializeMiddleware[Input, Output]] = SmithyStep()
        self.build: SmithyStep[BuildMiddleware[Input, Output]] = SmithyStep()
        self.finalize: SmithyStep[FinalizeMiddleware[Input, Output]] = SmithyStep()
        self.deserialize: SmithyStep[DeserializeMiddleware[Input, Output]] = SmithyStep()

    def resolve(self, terminal: DeserializeHandler[Input, Output]) -> Handler[Input, Output]:
        return self._build_deserialize_chain(terminal)

    def _build_deserialize_chain(self, terminal: DeserializeHandler[Input, Output]) -> Handler[Input, Output]:
        middlewares = [m.middleware for m in self.deserialize.middlewares]
        deserialize_chain = chain_middleware(terminal, *middlewares)
        def _deserialize_bridge(finalize_in: FinalizeInput[Input]) -> FinalizeOutput[Output]:
            deserialize_in = DeserializeInput(
                param=finalize_in.input,
                request=finalize_in.request,
            )
            deserialize_out = deserialize_chain(deserialize_in)
            return FinalizeOutput(output=deserialize_out.output)
        return self._build_finalize_chain(_deserialize_bridge)

    def _build_finalize_chain(self, terminal: FinalizeHandler[Input, Output]) -> Handler[Input, Output]:
        middlewares = [m.middleware for m in self.finalize.middlewares]
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
        middlewares = [m.middleware for m in self.build.middlewares]
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
        middlewares = [m.middleware for m in self.serialize.middlewares]
        serialize_chain = chain_middleware(terminal, *middlewares)
        def _serialize_bridge(initialize_in: InitializeInput[Input]) -> InitializeOutput[Output]:
            serialize_in = SerializeInput(param=initialize_in.input)
            serialize_out = serialize_chain(serialize_in)
            return InitializeOutput(output=serialize_out.output)
        return self._build_initialize_chain(_serialize_bridge)

    def _build_initialize_chain(self, terminal: InitializeHandler[Input, Output]) -> Handler[Input, Output]:
        middlewares = [m.middleware for m in self.initialize.middlewares]
        initialize_chain = chain_middleware(terminal, *middlewares)
        def _initialize_bridge(param: Input) -> Output:
            initialize_in = InitializeInput(param=param)
            initialize_out = initialize_chain(initialize_in)
            return initialize_out.output
        return _initialize_bridge
