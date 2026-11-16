#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from collections.abc import Callable
from copy import copy
from types import FunctionType
from typing import Any, ClassVar, cast, get_overloads

from .deserializers import DeserializeableShape
from .exceptions import ExpectationNotMetError, ResourceLifecycleError
from .interceptors import InterceptorChain
from .program import Program
from .retries import RETRY_STRATEGY, RetryStrategyResolver
from .schemas import APIOperation
from .serializers import SerializeableShape
from .types import PropertyKey, TypedProperties

__all__ = ["OPERATION", "ClientBase"]

OPERATION = PropertyKey(key="operation", value_type=APIOperation[Any, Any])
"""The operation being invoked by the call."""

_CLOSED_MESSAGE = "Cannot invoke an operation on a client that has been closed."


class ClientBase[C]:
    """Client machinery shared by the sync and async clients.

    Setup and call preparation are programs (see ``smithy_core.program``) whose
    effects are the mode-specific hooks, so each mode only supplies the hooks, its
    lock, and its program driver.
    """

    _client_plugins: ClassVar[tuple[Callable[[Any], None], ...]] = ()
    _pipeline_type: ClassVar[type[Any]]
    _call_type: ClassVar[type[Any]]

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        # A generated operation method is overloaded: it takes its whole request, or
        # its members as keyword arguments. Its documentation is written once, on the
        # keyword overload, which the generator writes last and where editors find
        # the documentation of each argument. The implementation gets the same
        # documentation so that help() shows it too.
        for value in vars(cls).values():
            if isinstance(value, FunctionType) and value.__doc__ is None:
                docs = [o.__doc__ for o in get_overloads(value) if o.__doc__]
                if docs:
                    value.__doc__ = docs[-1]

    def __init__(
        self,
        config: C | None = None,
        plugins: list[Callable[[C], None]] | None = None,
    ) -> None:
        """
        :param config: Optional configuration for the client. Here you can set things
            like the endpoint for HTTP services or auth credentials.
        :param plugins: A list of callables applied once to the client's base
            configuration. Their changes are inherited by every operation invocation.
        """
        self._config: Any = config
        self._plugins = plugins
        self._setup_done = False
        self._closed = False
        self._transport: Any = None
        self._retry_strategy_resolver = RetryStrategyResolver()

    def _new_config(self) -> Any:
        """Effect: create the config used when none is passed to the constructor."""
        raise NotImplementedError

    def _post_setup(self, config: C) -> Any:
        """Effect: finish setup that depends on the plugin-applied config."""
        return None

    def _resolve_retry_strategy(self, config: Any) -> Any:
        """Effect: resolve the retry strategy for a call."""
        return self._retry_strategy_resolver.resolve_retry_strategy(
            retry_strategy=config.retry_strategy,
            retry_mode=getattr(config, "retry_mode", None),
            max_attempts=getattr(config, "max_attempts", None),
        )

    def _build_call[I: SerializeableShape, O: DeserializeableShape](
        self,
        input: I,
        operation: APIOperation[I, O],
        *,
        config: Any,
        retry_strategy: Any,
    ) -> tuple[Any, Any]:
        """Build the pipeline and call from a resolved config and retry strategy."""
        pipeline = self._pipeline_type(
            protocol=config.protocol, transport=config.transport
        )
        context = TypedProperties({"config": config})
        context[RETRY_STRATEGY] = retry_strategy
        context[OPERATION] = operation
        call = self._call_type(
            input=input,
            operation=operation,
            context=context,
            interceptor=InterceptorChain(config.interceptors),
            auth_scheme_resolver=config.auth_scheme_resolver,
            supported_auth_schemes=config.auth_schemes,
            endpoint_resolver=config.endpoint_resolver,
            retry_strategy=retry_strategy,
        )
        return pipeline, call

    def _select_input[I: SerializeableShape, O: DeserializeableShape](
        self,
        operation: APIOperation[I, O],
        args: tuple[object, ...],
        members: dict[str, object],
    ) -> I | dict[str, Any]:
        """Choose what a generated operation method's input is built from.

        The method takes either its whole request, positionally, as the input model
        or its dictionary form, or the request's members as keyword arguments. The
        result is handed to ``_invoke`` or ``_prepare_call``, which build the model.
        A model is checked here and used as it is.

        :param operation: The operation being called.
        :param args: The method's positional arguments, after ``self``.
        :param members: The method's keyword arguments, other than ``plugins``.
        :raises TypeError: If more than one positional argument is given, the request
            is given with keyword arguments, the request is not the operation's input
            model or a dict, or the model doesn't fit the operation's input.
        """
        if len(args) == 0:
            return members
        name = operation.schema.id.name
        if len(args) != 1:
            raise TypeError(
                f"{name} takes at most one positional argument, its request, "
                f"but {len(args)} were given"
            )
        if members:
            raise TypeError(f"{name} takes its request or keyword arguments, not both")
        request = args[0]
        if isinstance(request, dict):
            return cast("dict[str, Any]", request)
        input_type = operation.input
        if isinstance(request, input_type):
            operation.model_registry.check_input(operation.input_schema, request, name)
            return request
        raise TypeError(
            f"{name} takes a {input_type.__name__} or a dict as its request, "
            f"got {'None' if request is None else type(request).__name__}"
        )

    def _build_input[I: SerializeableShape, O: DeserializeableShape](
        self, input: I | dict[str, Any] | None, operation: APIOperation[I, O]
    ) -> I:
        """Build the input model from the keyword arguments of an operation call.

        Runs before any client setup, so a call with invalid arguments fails without
        resolving configuration. An input that is already a model is used as given.

        :raises TypeError: If the keyword arguments don't fit the operation's input.
        """
        if input is None:
            return operation.input()
        if isinstance(input, dict):
            return operation.model_registry.build_input(
                operation.input_schema, input, operation.schema.id.name
            )
        return input

    def _raise_if_closed(self) -> None:
        if self._closed:
            raise ResourceLifecycleError(_CLOSED_MESSAGE)

    def _close(self) -> Program[None]:
        """Close the transport once; callers hold the setup lock."""
        if self._closed:
            return
        self._closed = True
        if self._setup_done and self._transport is not None:
            if (close := getattr(self._transport, "close", None)) is not None:
                yield close

    def _setup(self) -> Program[C]:
        """Resolve the client's base config once; callers hold the setup lock."""
        self._raise_if_closed()
        if not self._setup_done:
            if self._config is None:
                config = yield self._new_config
            else:
                # Copy so plugins don't mutate the caller's config.
                config = _copy_config(self._config)
            for plugin in self._client_plugins:
                plugin(config)
            for plugin in self._plugins or ():
                plugin(config)
            # Publish state only after setup fully succeeds, so a failed _post_setup
            # leaves the caller's config untouched (no re-applied plugins) and the
            # transport closeable.
            yield lambda: self._post_setup(config)
            self._transport = config.transport
            self._config = config
            self._setup_done = True
        return self._config

    def _prepare[I: SerializeableShape, O: DeserializeableShape](
        self,
        config: Any,
        input: I,
        operation: APIOperation[I, O],
        default_plugins: list[Callable[[C], None]],
        plugins: list[Callable[[C], None]] | None,
    ) -> Program[Any]:
        if default_plugins or plugins:
            # Keep operation-plugin mutations scoped to this call.
            config = _copy_config(config)
            for plugin in default_plugins:
                plugin(config)
            for plugin in plugins or ():
                plugin(config)
        if (
            config.protocol is None
            or config.transport is None
            or config.endpoint_resolver is None
            or config.auth_scheme_resolver is None
            or config.auth_schemes is None
        ):
            raise ExpectationNotMetError(
                "protocol, transport, endpoint_resolver, auth_scheme_resolver,"
                " and auth_schemes MUST be set on the config to make calls."
            )
        retry_strategy = yield lambda: self._resolve_retry_strategy(config)
        return self._build_call(
            input, operation, config=config, retry_strategy=retry_strategy
        )


def _copy_config[T](config: T) -> T:
    """Copy a config and its container fields, sharing the components they hold.

    Configured components such as interceptors, resolvers and retry strategies
    carry state the caller expects to observe, so they must not be copied.

    CAUTION: a plugin that mutates a component in place, rather than replacing
    it, changes the caller's component.
    """
    new = copy(config)
    for name, value in list(vars(new).items()):
        if isinstance(value, list | dict | set):
            # CAUTION: object.__setattr__ skips AwsConfig.__setattr__, which would
            # record the copy as a plugin override and reject credential fields.
            object.__setattr__(new, name, copy(cast(Any, value)))
    return new
