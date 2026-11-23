# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Extension points that let a provider change the clients a service generates.

A :class:`ClientIntegration` applies to the services it matches. It can rename the
clients and configs, replace the config classes, add client plugins and modules, and
change how a client creates its default config. Integrations keep provider code,
such as AWS config resolution, out of the core generator.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING

from ._endpoints import RulesExtension
from .symbols import TypeReference

if TYPE_CHECKING:
    from . import _auth, _endpoints
    from . import model as _model
    from .clients import ClientPlan
    from .generation import ClientSettings, GenerationContext
    from .writer import PythonWriter

__all__ = [
    "ClientIntegration",
    "ClientMode",
    "ClientNames",
    "ConfigPlan",
    "Part",
    "RulesExtension",
]

type Part = str | TypeReference
"""A piece of a generated line."""


@dataclass(frozen=True, slots=True)
class ClientNames:
    """The client and config class names of a generated package."""

    client: str
    config: str
    async_client: str
    async_config: str


@dataclass(frozen=True, slots=True)
class ClientMode:
    """Names and runtime types that differ between the sync and async client."""

    directory: str
    """The package-relative directory of the mode's modules, ``""`` or ``"aio/"``."""

    config: str
    client: str
    client_base: TypeReference
    protocol: TypeReference
    transport: TypeReference
    transport_type: TypeReference
    auth_scheme: TypeReference
    endpoint_resolver: tuple[TypeReference, ...]
    is_async: bool


@dataclass(frozen=True, slots=True)
class ConfigPlan:
    """Everything a config class for one mode is built from."""

    plan: ClientPlan
    service: _model.ServiceShape
    mode: ClientMode
    endpoints: _endpoints.EndpointPlan
    bdd: TypeReference
    """The ``BDD`` constant of the generated endpoints module."""

    auth_schemes: tuple[_auth.AuthContribution, ...]
    """The supported auth schemes the service models, in shape ID order."""

    protocol_settings: str
    """The name of the module-level ``ProtocolSettings`` constant."""


class ClientIntegration:
    """Changes the clients generated for the services it matches.

    Every method has a default that changes nothing, so an integration overrides
    only what it needs.
    """

    def matches(self, service: _model.ServiceShape) -> bool:
        """Whether the integration applies to a service."""
        del service
        return False

    def client_names(
        self, service: _model.ServiceShape, names: ClientNames
    ) -> ClientNames:
        """The class names of the service's clients and configs."""
        del service
        return names

    def auth_schemes(
        self, service: _model.ServiceShape
    ) -> Mapping[_model.ShapeId, _auth.AuthContribution]:
        """Auth schemes the integration supports, by auth trait ID.

        They join the core auth schemes for the services the integration matches.
        """
        del service
        return {}

    def config_fields(self, service: _model.ServiceShape) -> Collection[str]:
        """Config fields the integration declares, which a client context
        parameter's field must not take."""
        del service
        return ()

    def write_config(self, writer: PythonWriter, config: ConfigPlan) -> bool:
        """Write the mode's config class in place of the core one.

        :returns: Whether the integration wrote the class.
        """
        del writer, config
        return False

    def new_config(
        self, mode: ClientMode, config: TypeReference
    ) -> tuple[Part, ...] | None:
        """The callable that creates a default config, called with keyword fields.

        A client calls it with no arguments when it has no config. An async mode
        may begin the parts with ``"await "``. None leaves the callable as the
        config class or an earlier integration set it.
        """
        del mode, config
        return None

    def rules_extensions(
        self, service: _model.ServiceShape
    ) -> tuple[RulesExtension, ...]:
        """Rules extensions the default endpoint resolver uses.

        Their functions join the standard library the rules may call.
        """
        del service
        return ()

    def endpoint_test_config(
        self, service: _model.ServiceShape
    ) -> Mapping[str, tuple[Part, ...]]:
        """Config fields every generated endpoint test sets, as expressions.

        A config that resolves from the environment, for example, may need a
        region and credentials. A test case's own fields replace these.
        """
        del service
        return {}

    def endpoint_test_builtin(
        self, service: _model.ServiceShape, builtin: str, value: _model.Node
    ) -> tuple[str, tuple[Part, ...]] | None:
        """The config field and expression that set a built-in in an endpoint test.

        None if the integration doesn't set the built-in. A test case that sets a
        built-in no integration sets, to a value other than its default, is
        skipped.
        """
        del service, builtin, value
        return None

    def write_client_methods(
        self,
        writer: PythonWriter,
        plan: ClientPlan,
        mode: ClientMode,
        config: TypeReference,
    ) -> None:
        """Write extra methods at the end of the mode's client class.

        :param config: The mode's config class.
        """
        del writer, plan, mode, config

    def client_plugins(
        self, plan: ClientPlan, mode: ClientMode, package: str
    ) -> tuple[TypeReference, ...]:
        """Plugins every client of the mode applies, before the core ones."""
        del plan, mode, package
        return ()

    def write_files(
        self,
        context: GenerationContext[ClientSettings],
        plan: ClientPlan,
        modes: tuple[ClientMode, ClientMode],
    ) -> None:
        """Register any extra modules, such as the modules of client plugins."""
        del context, plan, modes
