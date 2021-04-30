from typing import Any, Callable, List, Mapping, Optional, TypeVar

from smithy_python.interfaces.middleware import (
    GenericStepInput,
    GenericStepOutput,
    OperationInput,
    OperationOutput,
    Middleware,
    Step,
    Stack,
)


class SDKMiddleware(Middleware):
    def __init__(self, middleware_id: Optional[str] = None) -> None:
        if middleware_id is None:
            middleware_id = self.__class__.__name__
        self.middleware_id = middleware_id


class InitializeMiddleware(SDKMiddleware):
    """Middleware to be used in the InitializationStep"""

    pass


class SerializeMiddleware(SDKMiddleware):
    """Middleware to be used in the SerializeStep"""

    pass


class BuildMiddleware(SDKMiddleware):
    """Middleware to be used in the BuildStep"""

    pass


class FinalizeMiddleware(SDKMiddleware):
    """Middleware to be used in the FinalizeStep"""

    pass


class DeserializeMiddleware(SDKMiddleware):
    """Middleware to be used in the DeserializeStep"""

    pass


class StepTransitionMiddleware(SDKMiddleware):
    def __init__(self, step: Step, middleware_id: Optional[str] = None) -> None:
        if middleware_id is None:
            middleware_id = self.__class__.__name__
        self.middleware_id = middleware_id
        self._step = step

    def run_middleware(
        self,
        step_input: GenericStepInput,
        context: Optional[Mapping[str, Any]],
        callbacks: Optional[List[Middleware]],
    ) -> GenericStepOutput:
        return self._step.run_step(step_input, context)


class SDKStep(Step):

    _middleware_type = SDKMiddleware

    def __init__(
        self,
        middlewares: Optional[List[Middleware]] = None,
        next_step: Optional[Step] = None,
    ) -> None:
        if middlewares is None:
            middlewares = []
        self.middlewares = middlewares
        self.next_step = next_step

    def run_step(
        self, operation_input: OperationInput, context: Optional[Mapping[str, Any]]
    ) -> OperationOutput:

        execution_chain: List[Middleware] = self.middlewares.copy()
        if self.next_step:
            execution_chain.append(StepTransitionMiddleware(self.next_step))
        if execution_chain:
            middleware = execution_chain.pop(0)
            return middleware.run_middleware(operation_input, context, execution_chain)
        return OperationOutput()  # TODO: This is wrong

    def _resolve_middleware_position(
        self, middleware_id: Optional[str], default_pos: int
    ) -> int:
        for n, middleware in enumerate(self.middlewares):
            if middleware.middleware_id == middleware_id:
                return n
        return default_pos

    def _validate_middleware(self, middleware: Middleware) -> None:
        if not isinstance(middleware, self._middleware_type):
            raise ValueError(
                "Incompatible middleware added to Initialize Step, expected"
                "%s but received %s"
                % (self._middleware_type.__name__, type(middleware))
            )

    def add_before(
        self, middleware: Middleware, middleware_id: Optional[str] = None
    ) -> None:
        self._validate_middleware(middleware)
        position = self._resolve_middleware_position(middleware_id, 0)
        self.middlewares.insert(position, middleware)

    def add_after(
        self, middleware: Middleware, middleware_id: Optional[str] = None
    ) -> None:
        self._validate_middleware(middleware)
        position = self._resolve_middleware_position(middleware_id, -1)
        self.middlewares.insert(position, middleware)

    def set_next_step(self, step: Step) -> None:
        self.next_step = step


# These are the concrete steps used for the SDK Stack
class InitializeStep(SDKStep):
    _middleware_type = InitializeMiddleware


class SerializeStep(SDKStep):
    _middleware_type = SerializeMiddleware


class BuildStep(SDKStep):
    _middleware_type = BuildMiddleware


class FinalizeStep(SDKStep):
    _middleware_type = FinalizeMiddleware


class DeserializeStep(SDKStep):
    _middleware_type = DeserializeMiddleware


class SDKStack(Stack):
    """An SDKStack is composed of five high level Steps. The occur in
    sequential order and each step can implement any number of ordered
    middlewares.

    The steps are as follows:

    initializer: The initializer is any middlewares that need to be utilized
        before the input is acted upon by the stack. You can think of this as
        a pre-step.

    serializer: The serializer step is where all serialization occurs. Any
        transformation required before transmission should be done here.

    builder: The builder step is where all components are assembled for
        transmission to the end destination. e.g. Request construction,
        data assembly, etc.

    finalizer: The finalizer step is where any required post-processing
        is performed prior to transmission.

    deserializer: The deserialize step is where data is handed off to
        an external component and any response is processed into an
        expected format.
    """

    def __init__(self) -> None:
        self.initializer: InitializeStep = InitializeStep()
        self.serializer: SerializeStep = SerializeStep()
        self.builder: BuildStep = BuildStep()
        self.finalizer: FinalizeStep = FinalizeStep()
        self.deserializer: DeserializeStep = DeserializeStep()

    def build(self) -> None:
        self.initializer.set_next_step(self.serializer)
        self.serializer.set_next_step(self.builder)
        self.builder.set_next_step(self.finalizer)
        self.finalizer.set_next_step(self.deserializer)

    def run_stack(
        self, stack_input: OperationInput, context: Optional[Mapping[str, Any]]
    ) -> OperationOutput:
        stack_output = self.initializer.run_step(stack_input, context)
        return OperationOutput.from_step_ouput(stack_output)
