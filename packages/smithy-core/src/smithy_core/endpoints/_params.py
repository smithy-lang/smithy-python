#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""Endpoint parameter plans: how a call's config, input and operation traits become
the parameter values an endpoint BDD is evaluated with."""

import logging
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

from .._model_naming import member_field_name, to_snake_case
from ..exceptions import EndpointResolutionError
from ..interfaces import TypedProperties as _TypedProperties
from ..schemas import APIOperation
from ..traits import (
    ContextParamTrait,
    OperationContextParamsTrait,
    RequiredTrait,
    StaticContextParamsTrait,
)
from ._types import (
    ENDPOINT_PARAMETERS,
    BuiltinBinding,
    BuiltinGetter,
    EndpointResolverParams,
    RulesExtension,
    StaticEndpointConfig,
)

_LOGGER = logging.getLogger(__name__)


class ParamPlan:
    """Plan to find each endpoint parameter's value, for any operation of a BDD."""

    def __init__(
        self,
        parameters: Sequence[tuple[Any, ...]],
        extensions: Sequence[RulesExtension] = (),
    ) -> None:
        """Build the sources every operation shares.

        A client context parameter is read from its own config field, even when it is
        also a built-in. A built-in no extension binds takes its default.

        :param parameters: The rules parameters, in BDD order.
        :param extensions: Extensions whose built-in bindings apply, beyond the standard
            library, which always applies.
        """
        redefined = [
            name
            for extension in extensions
            for name in extension.builtins
            if name in _STANDARD_BUILTINS
        ]
        if redefined:
            raise EndpointResolutionError(
                f"Endpoint rules extensions redefine standard built-ins: {', '.join(redefined)}"
            )
        builtins: dict[str, BuiltinBinding] = dict(_STANDARD_BUILTINS)
        for extension in extensions:
            builtins.update(extension.builtins)
        slots: dict[str, int] = {}
        names: list[str] = []
        defaults: list[Any] = []
        required: list[int] = []
        arrays: list[int] = []
        builtin_attributes: list[tuple[int, str]] = []
        builtin_getters: list[tuple[int, BuiltinGetter]] = []
        client_context_attributes: list[tuple[int, str]] = []
        for slot, parameter in enumerate(parameters):
            name, type_, is_required, default, builtin, client_context = parameter
            slots[name] = slot
            names.append(name)
            defaults.append(default)
            if is_required and default is None:
                required.append(slot)
            if type_ == "stringArray":
                arrays.append(slot)
            if client_context:
                client_context_attributes.append((slot, _config_attribute(name)))
            elif builtin is not None:
                binding = builtins.get(builtin)
                if binding is None:
                    _LOGGER.debug(
                        "No extension binds the built-in %s; endpoint parameter %s"
                        " takes its default",
                        builtin,
                        name,
                    )
                elif isinstance(binding, str):
                    builtin_attributes.append((slot, binding))
                else:
                    builtin_getters.append((slot, binding))

        self._slots = slots
        # Sources by operation identity, holding the operation so its id stays valid.
        self._operations: dict[int, tuple[Any, _OperationSources]] = {}

        self.defaults: tuple[Any, ...] = tuple(defaults)
        """Each parameter's default, else None."""

        self.builtin_attributes: tuple[tuple[int, str], ...] = tuple(builtin_attributes)
        """(slot, config attribute) for built-ins bound to an attribute."""

        self.builtin_getters: tuple[tuple[int, BuiltinGetter], ...] = tuple(
            builtin_getters
        )
        """(slot, getter) for built-ins bound to a getter."""

        self.client_context_attributes: tuple[tuple[int, str], ...] = tuple(
            client_context_attributes
        )
        """(slot, config attribute) for client context parameters."""

        self.required: tuple[int, ...] = tuple(required)
        """Slots of required parameters with no default."""

        self.arrays: tuple[int, ...] = tuple(arrays)
        """Slots of stringArray parameters, normalized to tuples without None."""

        self.names: tuple[str, ...] = tuple(names)
        """Parameter names by slot, for errors."""

    def bind(self, params: EndpointResolverParams[Any]) -> tuple[Any, ...]:
        """The parameter values for one call, in BDD order.

        :param params: The call's operation, input, and context. The context holds
            the client config under ``"config"``.
        :raises EndpointResolutionError: If a required value is missing, or a required
            context parameter member is unset or blank.
        """
        operation = params.operation
        input = params.input
        context = params.context
        config = context["config"]
        entry = self._operations.get(id(operation))
        if entry is not None and entry[0] is operation:
            sources = entry[1]
        else:
            sources = self._add_operation(operation)
        values = list(self.defaults)
        for slot, attribute in self.builtin_attributes:
            value = getattr(config, attribute, None)
            if value is not None:
                values[slot] = value
        for slot, getter in self.builtin_getters:
            value = getter(config, context)
            if value is not None:
                values[slot] = value
        for slot, attribute in self.client_context_attributes:
            value = getattr(config, attribute, None)
            if value is not None:
                values[slot] = value
        for slot, path in sources.operation_paths:
            value = path(input)
            if value is not None:
                values[slot] = value
        for attribute in sources.unread_required:
            value = getattr(input, attribute, None)
            if value is None or (type(value) is str and not value.strip()):
                raise EndpointResolutionError(
                    f"Required input member {attribute} must not be unset or blank"
                )
        for slot, attribute, required in sources.input_fields:
            value = getattr(input, attribute, None)
            if required and (
                value is None or (type(value) is str and not value.strip())
            ):
                raise EndpointResolutionError(
                    f"Required input member {attribute} must not be unset or blank"
                )
            if value is not None:
                values[slot] = value
        for slot, value in sources.static_values:
            values[slot] = value
        overrides = context.get(ENDPOINT_PARAMETERS)
        if overrides:
            slots = self._slots
            defaults = self.defaults
            for name, value in overrides.items():
                slot = slots.get(name)
                if slot is not None:
                    values[slot] = defaults[slot] if value is None else value
        for slot in self.arrays:
            value = values[slot]
            if value is not None:
                if not isinstance(value, list | tuple):
                    raise EndpointResolutionError(
                        f"Endpoint parameter {self.names[slot]} must be a list"
                        f" of strings, not {type(value).__name__}"
                    )
                values[slot] = tuple([v for v in value if v is not None])  # pyright: ignore[reportUnknownArgumentType, reportUnknownVariableType]
        for slot in self.required:
            if values[slot] is None:
                raise EndpointResolutionError(
                    f"Missing required endpoint parameter: {self.names[slot]}"
                )
        return tuple(values)

    def _add_operation(self, operation: APIOperation[Any, Any]) -> "_OperationSources":
        """Read the sources an operation's schema traits add, and keep them."""
        slots = self._slots

        operation_paths: list[tuple[int, Callable[[Any], Any]]] = []
        operation_params = operation.schema.get_trait(OperationContextParamsTrait)
        if operation_params is not None:
            from .. import _jmespath

            for name, path in operation_params.paths.items():
                slot = slots.get(name)
                if slot is not None:
                    operation_paths.append((slot, _jmespath.compile(path)))

        input_fields: list[tuple[int, str, bool]] = []
        unread_required: list[str] = []
        for member in operation.input_schema.members.values():
            context_param = member.get_trait(ContextParamTrait)
            if context_param is None:
                continue
            attribute = _input_attribute(member.expect_member_name())
            required = RequiredTrait in member
            slot = slots.get(context_param.name)
            if slot is not None:
                input_fields.append((slot, attribute, required))
            elif required:
                unread_required.append(attribute)

        static_values: list[tuple[int, Any]] = []
        static_params = operation.schema.get_trait(StaticContextParamsTrait)
        if static_params is not None:
            for name, value in static_params.values.items():
                slot = slots.get(name)
                if slot is not None:
                    if isinstance(value, list):
                        value = tuple(value)
                    static_values.append((slot, value))

        sources = _OperationSources(
            operation_paths=tuple(operation_paths),
            input_fields=tuple(input_fields),
            unread_required=tuple(unread_required),
            static_values=tuple(static_values),
        )
        self._operations[id(operation)] = (operation, sources)
        return sources


@dataclass(frozen=True, slots=True)
class _OperationSources:
    """The parameter sources one operation's schema traits add."""

    operation_paths: tuple[tuple[int, Callable[[Any], Any]], ...]
    """(slot, compiled path) for operationContextParams."""

    input_fields: tuple[tuple[int, str, bool], ...]
    """(slot, input attribute, whether required) for contextParam members."""

    unread_required: tuple[str, ...]
    """Input attributes of required contextParam members the rules don't read."""

    static_values: tuple[tuple[int, Any], ...]
    """(slot, value) for staticContextParams."""


def _config_attribute(parameter: str) -> str:
    return to_snake_case(parameter)


def _input_attribute(member: str) -> str:
    return member_field_name(
        member, is_error=False, carries_response_metadata=False, is_enum=False
    )


def _endpoint_uri(
    config: StaticEndpointConfig, context: _TypedProperties
) -> str | None:
    value = config.endpoint_uri
    if value is None or isinstance(value, str):
        return value
    return value.build()


_STANDARD_BUILTINS: Mapping[str, BuiltinGetter] = MappingProxyType(
    {"SDK::Endpoint": _endpoint_uri}
)
"""The standard built-ins: ``SDK::Endpoint`` reads the config's ``endpoint_uri``."""
