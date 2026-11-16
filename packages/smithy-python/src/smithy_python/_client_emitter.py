# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Emission of sync and async client and config modules."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from . import _package
from . import dependencies as _dependencies
from . import exceptions as _exceptions
from . import model as _model
from . import models as _models
from . import protocols as _protocols
from .symbols import TypeReference

if TYPE_CHECKING:
    from .clients import ClientPlan, OperationPlan
    from .generation import ClientSettings, GenerationContext
    from .writer import PythonWriter


def check_supported(plan: ClientPlan) -> None:
    """Reject models that need features generated clients do not support yet.

    :raises CodegenError: Naming the first unsupported operation and feature.
    """
    service = plan.selection.service
    assert service is not None  # noqa: S101 - ClientPlan requires a service
    for trait_id in _RULE_TRAITS:
        if service.has_trait(trait_id):
            raise _exceptions.CodegenError(
                f"Service {service.id} uses {trait_id}, which client generation "
                "does not support yet. Use a static endpoint."
            )
    for operation, exports in zip(plan.operations, plan.models.operations, strict=True):
        shape = operation.operation
        if _NO_AUTH not in exports.auth_scheme_ids:
            schemes = ", ".join(map(str, exports.auth_scheme_ids))
            raise _exceptions.CodegenError(
                f"Operation {shape.id} requires auth ({schemes}), which client "
                "generation does not support yet"
            )
        for io in (shape.input, shape.output):
            for member in plan.model.get_shape(io).members.values():
                if plan.model.get_target(member).has_trait("streaming"):
                    raise _exceptions.CodegenError(
                        f"Operation {shape.id} streams {member.id}, which client "
                        "generation does not support yet"
                    )


def write_client(
    context: GenerationContext[ClientSettings],
    plan: ClientPlan,
    protocol: _protocols.ProtocolContribution,
) -> None:
    """Register client, config, and package modules for both modes."""
    package = context.settings.package
    directory = package.replace(".", "/")
    service = plan.selection.service
    assert service is not None  # noqa: S101 - ClientPlan requires a service
    sync, aio = _modes(plan, protocol)
    for mode in (sync, aio):
        module = f"{package}.{mode.directory.replace('/', '.')}"
        _write_config(
            context.files.python_module(
                f"src/{directory}/{mode.directory}config.py", f"{module}config"
            ),
            plan,
            mode,
            service,
        )
        _write_client(
            context.files.python_module(
                f"src/{directory}/{mode.directory}client.py",
                f"{module}client",
                future_annotations=True,
            ),
            plan,
            mode,
            f"{module}config",
            service,
        )
    aio_init = context.files.python_module(
        f"src/{directory}/aio/__init__.py", f"{package}.aio"
    )
    _write_exports(aio_init, {aio.client: ".client", aio.config: ".config"})
    init = _package.write_package(
        context,
        title=f"{package} Client Package",
        description=context.settings.package_description or f"{package} client package",
    )
    _write_exports(
        init,
        {
            sync.client: ".client",
            sync.config: ".config",
            aio.client: ".aio.client",
            aio.config: ".aio.config",
        },
    )


def _core(name: str, module: str) -> TypeReference:
    return TypeReference(
        name, f"smithy_core.{module}", dependencies=(_dependencies.SMITHY_CORE,)
    )


def _typing(name: str) -> TypeReference:
    return TypeReference(name, "typing")


_ANY: Final = _typing("Any")
_ANY4: Final = (_ANY, _ANY, _ANY, _ANY)
_CAST: Final = _typing("cast")
_OVERLOAD: Final = _typing("overload")
_UNPACK: Final = _typing("Unpack")
_TYPE_CHECKING: Final = _typing("TYPE_CHECKING")
_CALLABLE: Final = TypeReference("Callable", "collections.abc")
_DATACLASS: Final = TypeReference("dataclass", "dataclasses")
_IMPORT_MODULE: Final = TypeReference("import_module", "importlib")
_PROTOCOL_SETTINGS: Final = _core("ProtocolSettings", "interfaces")
_PROTOCOL_CONSTRUCTOR: Final = _core("ProtocolConstructor", "interfaces")
_URI: Final = _core("URI", "interfaces")
_AUTH_SCHEME_RESOLVER: Final = _core("AuthSchemeResolver", "interfaces.auth")
_DEFAULT_AUTH_RESOLVER: Final = _core("DefaultAuthResolver", "auth")
_STATIC_ENDPOINT_RESOLVER: Final = _core("StaticEndpointResolver", "endpoints")
_RETRY_STRATEGY: Final = _core("RetryStrategy", "interfaces.retries")
_RETRY_STRATEGY_OPTIONS: Final = _core("RetryStrategyOptions", "retries")
_SHAPE_ID: Final = _core("ShapeID", "shapes")
_USER_AGENT_PLUGIN: Final = TypeReference(
    "user_agent_plugin",
    "smithy_http.plugins",
    dependencies=(_dependencies.SMITHY_HTTP,),
)


def _generic(reference: TypeReference, *arguments: TypeReference) -> TypeReference:
    return TypeReference(
        reference.name,
        reference.module,
        arguments=arguments,
        dependencies=reference.dependencies,
    )


@dataclass(frozen=True, slots=True)
class _Mode:
    """Names and runtime types that differ between the sync and async client."""

    directory: str
    config: str
    client: str
    client_base: TypeReference
    protocol: TypeReference
    transport: TypeReference
    transport_type: TypeReference
    auth_scheme: TypeReference
    endpoint_resolver: tuple[TypeReference, ...]
    is_async: bool


def _modes(
    plan: ClientPlan, protocol: _protocols.ProtocolContribution
) -> tuple[_Mode, _Mode]:
    endpoint_resolver = _core("EndpointResolver", "interfaces")
    return (
        _Mode(
            directory="",
            config="Config",
            client=plan.symbols.service_name,
            client_base=_core("Client", "client"),
            protocol=protocol.protocol,
            transport=protocol.transport,
            transport_type=_generic(_core("ClientTransport", "interfaces"), _ANY, _ANY),
            auth_scheme=_generic(_core("AuthScheme", "interfaces.auth"), *_ANY4),
            endpoint_resolver=(endpoint_resolver,),
            is_async=False,
        ),
        _Mode(
            directory="aio/",
            config="AsyncConfig",
            client=plan.symbols.aio_service_name,
            client_base=_core("AsyncClient", "aio.client"),
            protocol=protocol.async_protocol,
            transport=protocol.async_transport,
            transport_type=_generic(
                _core("AsyncClientTransport", "aio.interfaces"), _ANY, _ANY
            ),
            auth_scheme=_generic(
                _core("AsyncAuthScheme", "aio.interfaces.auth"), *_ANY4
            ),
            endpoint_resolver=(
                endpoint_resolver,
                _core("AsyncEndpointResolver", "aio.interfaces"),
            ),
            is_async=True,
        ),
    )


_NO_AUTH: Final = _model.ShapeId("smithy.api", "noAuth")
_RULE_TRAITS: Final = (
    _model.ShapeId("smithy.rules", "endpointRuleSet"),
    _model.ShapeId("smithy.rules", "endpointBdd"),
)


def _write_exports(writer: PythonWriter, exports: dict[str, str]) -> None:
    # Importing the package builds no client: each export loads on first use.
    writer.line()
    writer.line("if ", _TYPE_CHECKING, ":")
    with writer.indent():
        for name, module in exports.items():
            writer.line("from ", module, " import ", name)
    writer.line()
    writer.line("__all__ = [", ", ".join(map(_models._quote, exports)), "]")  # pyright: ignore[reportPrivateUsage]
    writer.line()
    writer.line("_EXPORTS = {")
    with writer.indent():
        for name, module in exports.items():
            writer.line(_models._quote(name), ": ", _models._quote(module), ",")  # pyright: ignore[reportPrivateUsage]
    writer.line("}")
    writer.line()
    writer.line()
    writer.line("def __getattr__(name: str) -> ", _ANY, ":")
    with writer.indent():
        writer.line("if name in _EXPORTS:")
        with writer.indent():
            writer.line(
                "return getattr(", _IMPORT_MODULE, "(_EXPORTS[name], __name__), name)"
            )
        writer.line(
            'raise AttributeError(f"module {__name__!r} has no attribute {name!r}")'
        )


def _write_config(
    writer: PythonWriter,
    plan: ClientPlan,
    mode: _Mode,
    service: _model.ServiceShape,
) -> None:
    client_protocol = _generic(_core("ClientProtocol", "interfaces"), _ANY, _ANY)
    interceptor = _generic(_core("Interceptor", "interceptors"), *_ANY4)
    schemas = f"{plan.settings.package}._private.schemas"
    writer.line("_PROTOCOL_SETTINGS = ", _PROTOCOL_SETTINGS, "(")
    with writer.indent():
        writer.line("namespace=", _models._quote(service.id.namespace), ",")  # pyright: ignore[reportPrivateUsage]
        writer.line("service_target=", _models._quote(service.id.name), ",")  # pyright: ignore[reportPrivateUsage]
        if service.version is not None:
            writer.line("version=", _models._quote(service.version), ",")  # pyright: ignore[reportPrivateUsage]
        writer.line(
            "service_schema=",
            TypeReference(plan.symbols.schema_name(service.id), schemas),
            ",",
        )
    writer.line(")")
    writer.line()
    writer.line()
    endpoint_resolver = _join(mode.endpoint_resolver)
    auth_schemes = ("dict[", _SHAPE_ID, ", ", mode.auth_scheme, "]")
    retry = (_RETRY_STRATEGY, " | ", _RETRY_STRATEGY_OPTIONS)
    fields: tuple[tuple[str, tuple[str | TypeReference, ...], str], ...] = (
        (
            "auth_scheme_resolver",
            (_AUTH_SCHEME_RESOLVER,),
            "Determines the auth scheme for each operation.",
        ),
        ("auth_schemes", auth_schemes, "Auth schemes by auth scheme ID."),
        (
            "endpoint_resolver",
            endpoint_resolver,
            "Resolves the endpoint of each operation.",
        ),
        (
            "endpoint_uri",
            ("str | ", _URI, " | None"),
            "The static URI requests are sent to.",
        ),
        (
            "interceptors",
            ("list[", interceptor, "]"),
            "Hooks called during the execution of a request.",
        ),
        (
            "protocol",
            (client_protocol,),
            "Serializes requests and deserializes responses.",
        ),
        (
            "retry_strategy",
            (*retry, " | None"),
            "The retry strategy, or options to create one.",
        ),
        (
            "transport",
            (mode.transport_type,),
            "Sends requests, such as an HTTP client.",
        ),
    )
    writer.line("@", _DATACLASS, "(init=False)")
    writer.line("class ", mode.config, ":")
    with writer.indent():
        writer.line(_models._quote(f"Configuration for {mode.client}."))  # pyright: ignore[reportPrivateUsage]
        for name, annotation, docs in fields:
            writer.line()
            writer.line(name, ": ", *annotation)
            writer.line(_models._quote(docs))  # pyright: ignore[reportPrivateUsage]
        writer.line()
        writer.line("def __init__(")
        with writer.indent():
            writer.line("self,")
            writer.line("*,")
            writer.line(
                "auth_scheme_resolver: ", _AUTH_SCHEME_RESOLVER, " | None = None,"
            )
            writer.line("auth_schemes: ", *auth_schemes, " | None = None,")
            writer.line("endpoint_resolver: ", *endpoint_resolver, " | None = None,")
            writer.line("endpoint_uri: str | ", _URI, " | None = None,")
            writer.line("interceptors: list[", interceptor, "] | None = None,")
            writer.line(
                "protocol: ",
                client_protocol,
                " | ",
                _generic(_PROTOCOL_CONSTRUCTOR, client_protocol),
                " | None = None,",
            )
            writer.line("retry_strategy: ", *retry, " | None = None,")
            writer.line("transport: ", mode.transport_type, " | None = None,")
        writer.line(") -> None:")
        with writer.indent():
            writer.line(
                "self.auth_scheme_resolver = auth_scheme_resolver or ",
                _DEFAULT_AUTH_RESOLVER,
                "()",
            )
            writer.line("self.auth_schemes = auth_schemes or {}")
            writer.line(
                "self.endpoint_resolver = endpoint_resolver or ",
                _STATIC_ENDPOINT_RESOLVER,
                "()",
            )
            writer.line("self.endpoint_uri = endpoint_uri")
            writer.line("self.interceptors = interceptors or []")
            writer.line("if isinstance(protocol, type):")
            with writer.indent():
                writer.line("protocol = protocol(_PROTOCOL_SETTINGS)")
            writer.line(
                "self.protocol = ",
                _CAST,
                "(",
                client_protocol,
                ", protocol) or ",
                mode.protocol,
                "(_PROTOCOL_SETTINGS)",
            )
            writer.line("self.retry_strategy = retry_strategy")
            writer.line("self.transport = transport or ", mode.transport, "()")
    writer.line()
    writer.line()
    writer.line("type Plugin = ", _CALLABLE, "[[", mode.config, "], None]")
    writer.line(
        _models._quote(  # pyright: ignore[reportPrivateUsage]
            "A callable that customizes the client configuration."
        )
    )


def _join(references: tuple[TypeReference, ...]) -> tuple[str | TypeReference, ...]:
    parts: list[str | TypeReference] = []
    for reference in references:
        if parts:
            parts.append(" | ")
        parts.append(reference)
    return tuple(parts)


def _write_client(
    writer: PythonWriter,
    plan: ClientPlan,
    mode: _Mode,
    config_module: str,
    service: _model.ServiceShape,
) -> None:
    config = TypeReference(mode.config, config_module)
    plugin = TypeReference("Plugin", config_module)
    models = TypeReference("models", plan.settings.package)
    writer.line("class ", mode.client, "(", _generic(mode.client_base, config), "):")
    with writer.indent():
        _models._write_docstring(  # pyright: ignore[reportPrivateUsage]
            writer,
            _models._documentation(service)  # pyright: ignore[reportPrivateUsage]
            or f"Client for {service.id.name}.",
        )
        writer.line()
        writer.line("_client_plugins = (", _USER_AGENT_PLUGIN, ",)")
        for operation, export in zip(
            plan.operations, plan.models.operations, strict=True
        ):
            _write_operation(writer, plan, mode, operation, export.name, models, plugin)
        writer.line()
        writer.line("def _new_config(self) -> ", config, ":")
        with writer.indent():
            writer.line("return ", config, "()")


def _write_operation(
    writer: PythonWriter,
    plan: ClientPlan,
    mode: _Mode,
    operation: OperationPlan,
    constant: str,
    models: TypeReference,
    plugin: TypeReference,
) -> None:
    name = operation.method_name
    input_name = operation.input_name
    dict_name = plan.models.input_dict_names[operation.operation.input]
    output: tuple[str | TypeReference, ...] = (models, ".", operation.output_name)
    plugins: tuple[str | TypeReference, ...] = (
        "plugins: list[",
        plugin,
        "] | None = None",
    )
    define = "async def " if mode.is_async else "def "
    docs = _models._documentation(operation.operation)  # pyright: ignore[reportPrivateUsage]
    writer.line()
    writer.line("@", _OVERLOAD)
    writer.line(define, name, "(")
    with writer.indent():
        writer.line("self,")
        writer.line(
            "request: ", models, ".", input_name, " | ", models, ".", dict_name, ","
        )
        writer.line("/,")
        writer.line("*,")
        writer.line(*plugins, ",")
    writer.line(") -> ", *output, ": ...")
    writer.line()
    writer.line("@", _OVERLOAD)
    writer.line(define, name, "(")
    with writer.indent():
        writer.line("self,")
        writer.line("/,")
        writer.line("*,")
        writer.line(*plugins, ",")
        writer.line("**kwargs: ", _UNPACK, "[", models, ".", dict_name, "],")
    writer.line(") -> ", *output, ":")
    with writer.indent():
        _models._write_docstring(  # pyright: ignore[reportPrivateUsage]
            writer,
            (docs or f"Invokes the {operation.operation.id.name} operation.")
            + "\n\n:param plugins: Callables that change the configuration for "
            "this call only.",
        )
    writer.line()
    writer.line(define, name, "(")
    with writer.indent():
        writer.line("self, /, *args: object, ", *plugins, ", **kwargs: object")
    writer.line(") -> ", *output, ":")
    with writer.indent():
        writer.line("return ", "await " if mode.is_async else "", "self._invoke(")
        with writer.indent():
            writer.line(
                "self._select_input(", models, ".", constant, ", args, kwargs),"
            )
            writer.line(models, ".", constant, ",")
            writer.line("[],")
            writer.line("plugins,")
        writer.line(")")
