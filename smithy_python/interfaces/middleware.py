from typing import Any, Callable, List, Mapping, Optional, TypeVar
from typing_extensions import Protocol


# These are generic represenations for things we either haven't
# implemented yet, or need further thought on typing.
GenericStepInput = TypeVar("GenericStepInput")
GenericStepOutput = TypeVar("GenericStepOutput")
OperationInput = TypeVar("OperationInput")
OperationOutput = TypeVar("OperationOutput")


class Stack(Protocol):
    """A Stack defines a vertical of functionality. This can be the full
    life-cyle for a fundamental process such as signing, network communication,
    system io, etc.

    These are composable and modifiable by the end user to allow interface
    evolution for varied requirements. These will utilize Python's `Protocol`
    type to define high level interfaces which can be implemented and
    interchanged by anyone.
    """

    def build(self) -> None:
        """Creates default sequential order in which steps are to be run.

        Steps can be inserted, reordered and removed in custom Stacks by
        overwriting the `build` method.
        """
        pass

    def run_stack(
        self, stack_input: OperationInput, context: Optional[Mapping[str, Any]]
    ) -> OperationOutput:
        """Execute a series of steps defined in the build method"""
        pass


class Middleware(Protocol):
    """Middleware to provide custom functionality at as part of a Step
    in a Stack.

    :param middleware_id: Unique string identifier for the middleware.
        Generated from the class name by default.
    """

    middleware_id: str

    def run_middleware(
        self,
        step_input: GenericStepInput,
        context: Optional[Mapping[str, Any]],
        callbacks: Optional[List["Middleware"]],
    ) -> GenericStepOutput:
        pass


class Step(Protocol):
    """A Step is a conceptual grouping of middlewares, operating together
    to accomplish the larger goal of the Step. This allows users to create
    logical subsequences of events that are triggered in the Stack. These
    can exist as a single component of a Stack, or be sequentially chained
    by setting a `next_step`.

    Some examples of this is a Build Step that constructuts objects required
    for the stack operation, or a Finalization Step that does post-processing
    tasks.

    :param middlewares: A sequential collection of middlewares to be executed
    :param next_step: Another Step object to be called once this is complete
    """

    middlewares: List[Middleware]
    next_step: Optional["Step"]

    def run_step(
        self, step_input: GenericStepInput, context: Optional[Mapping[str, Any]]
    ) -> GenericStepOutput:
        pass

    def add_before(
        self, middleware: Middleware, middleware_id: Optional[str] = None
    ) -> None:
        pass

    def add_after(
        self, middleware: Middleware, middleware_id: Optional[str] = None
    ) -> None:
        pass

    def set_next_step(self, step: "Step") -> None:
        pass


class AsyncStack(Protocol):
    """A Stack defines a vertical of functionality. This can be the full
    life-cyle for a fundamental process such as signing, network communication,
    system io, etc.

    These are composable and modifiable by the end user to allow interface
    evolution for varied requirements. These will utilize Python's `Protocol`
    type to define high level interfaces which can be implemented and
    interchanged by anyone.
    """

    async def build(self) -> None:
        """Creates default sequential order in which steps are to be run.

        Steps can be inserted, reordered and removed in custom Stacks by
        overwriting the `build` method.
        """
        pass

    async def run_stack(
        self, stack_input: OperationInput, context: Optional[Mapping[str, Any]]
    ) -> OperationOutput:
        """Execute a series of steps defined in the build method"""
        pass


class AsyncMiddleware(Protocol):
    """Middleware to provide custom functionality at as part of a Step
    in a Stack.

    :param middleware_id: Unique string identifier for the middleware.
        Generated from the class name by default.
    """

    middleware_id: str

    async def run_middleware(
        self,
        step_input: GenericStepInput,
        context: Optional[Mapping[str, Any]],
        callbacks: Optional[List[Middleware]],
    ) -> GenericStepOutput:
        pass


class AsyncStep(Protocol):
    """A Step is a conceptual grouping of middlewares, operating together
    to accomplish the larger goal of the Step. This allows users to create
    logical subsequences of events that are triggered in the Stack. These
    can exist as a single component of a Stack, or be sequentially chained
    by setting a `next_step`.

    Some examples of this is a Build Step that constructuts objects required
    for the stack operation, or a Finalization Step that does post-processing
    tasks.

    :param middlewares: A sequential collection of middlewares to be executed
    :param next_step: Another Step object to be called once this is complete
    """

    middlewares: List[AsyncMiddleware]
    next_step: Optional["Step"]

    async def run_step(
        self, step_input: GenericStepInput, context: Optional[Mapping[str, Any]]
    ) -> GenericStepOutput:
        pass

    def add_before(
        self, middleware: Middleware, middleware_id: Optional[str] = None
    ) -> None:
        pass

    def add_after(
        self, middleware: Middleware, middleware_id: Optional[str] = None
    ) -> None:
        pass

    def set_next_step(self, step: "Step") -> None:
        pass
