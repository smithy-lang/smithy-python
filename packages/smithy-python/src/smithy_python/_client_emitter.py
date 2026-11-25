# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Emission of sync and async client and config modules."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Final

from . import _auth, _endpoint_tests, _endpoints, _package, _pagination
from . import dependencies as _dependencies
from . import exceptions as _exceptions
from . import model as _model
from . import models as _models
from . import protocols as _protocols
from .integrations import ClientIntegration, ClientMode, ClientNames, ConfigPlan
from .symbols import TypeReference

if TYPE_CHECKING:
    from .clients import ClientPlan, OperationPlan
    from .generation import ClientSettings, GenerationContext
    from .writer import PythonWriter


def check_supported(
    plan: ClientPlan, integrations: Sequence[ClientIntegration] = ()
) -> None:
    """Reject models that need features generated clients do not support yet.

    :param integrations: The integrations that match the service.
    :raises CodegenError: Naming the first unsupported operation and feature.
    """
    service = plan.selection.service
    assert service is not None  # noqa: S101 - ClientPlan requires a service
    supported = {_NO_AUTH} | {
        scheme.scheme_id for scheme in _auth_schemes(service, integrations)
    }
    for operation, exports in zip(plan.operations, plan.models.operations, strict=True):
        shape = operation.operation
        # The runtime signs with the first scheme the config supports, so an
        # operation needs one, or noAuth, to send a request.
        if not supported.intersection(exports.auth_scheme_ids):
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


def plan_endpoints(
    plan: ClientPlan, integrations: Sequence[ClientIntegration] = ()
) -> _endpoints.EndpointPlan:
    """Lower the service's endpoint rules for its client.

    :param integrations: The integrations that match the service.
    :raises CodegenError: If the rules are unsupported, or a client context
        parameter's config field collides with another config field.
    """
    service = plan.selection.service
    assert service is not None  # noqa: S101 - ClientPlan requires a service
    reserved = set(_CONFIG_FIELDS)
    reserved.update(
        field.name
        for scheme in _auth_schemes(service, integrations)
        for field in scheme.fields
    )
    for integration in integrations:
        reserved.update(integration.config_fields(service))
    return _endpoints.plan_endpoints(
        service,
        reserved=reserved,
        extensions=[
            extension
            for integration in integrations
            for extension in integration.rules_extensions(service)
        ],
    )


def write_client(
    context: GenerationContext[ClientSettings],
    plan: ClientPlan,
    protocol: _protocols.ProtocolContribution,
    endpoints: _endpoints.EndpointPlan,
    paginators: tuple[_pagination.PaginatorPlan | None, ...],
    integrations: Sequence[ClientIntegration] = (),
) -> None:
    """Register client, config, endpoints, and package modules for both modes.

    :param integrations: The integrations that match the service.
    """
    import_name = context.settings.import_name
    directory = import_name.replace(".", "/")
    service = plan.selection.service
    assert service is not None  # noqa: S101 - ClientPlan requires a service
    endpoints_module = f"{import_name}._private.endpoints"
    _endpoints.write_endpoints(
        context.files.python_module(
            f"src/{directory}/_private/endpoints.py", endpoints_module
        ),
        endpoints,
    )
    names = ClientNames(
        client=plan.symbols.service_name,
        config="Config",
        async_client=plan.symbols.aio_service_name,
        async_config="AsyncConfig",
    )
    for integration in integrations:
        names = integration.client_names(service, names)
    sync, aio = _modes(names, protocol)
    for mode in (sync, aio):
        module = f"{import_name}.{mode.directory.replace('/', '.')}"
        _write_config(
            context.files.python_module(
                f"src/{directory}/{mode.directory}config.py", f"{module}config"
            ),
            ConfigPlan(
                plan=plan,
                service=service,
                mode=mode,
                endpoints=endpoints,
                bdd=TypeReference("BDD", endpoints_module),
                auth_schemes=_auth_schemes(service, integrations),
                protocol_settings="_PROTOCOL_SETTINGS",
                host_prefix=any(
                    operation.operation.has_trait(_ENDPOINT)
                    for operation in plan.operations
                ),
            ),
            integrations,
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
            paginators,
            integrations,
        )
    for integration in integrations:
        integration.write_files(context, plan, (sync, aio))
    aio_config = TypeReference(aio.config, f"{import_name}.aio.config")
    _endpoint_tests.write_endpoint_tests(
        context,
        plan,
        endpoints,
        TypeReference(aio.client, f"{import_name}.aio.client"),
        aio_config,
        _new_config(aio, aio_config, integrations),
        {
            name: value
            for integration in integrations
            for name, value in integration.endpoint_test_config(service).items()
        },
        lambda builtin, value: next(
            (
                entry
                for integration in integrations
                if (entry := integration.endpoint_test_builtin(service, builtin, value))
                is not None
            ),
            None,
        ),
    )
    aio_init = context.files.python_module(
        f"src/{directory}/aio/__init__.py", f"{import_name}.aio"
    )
    _write_exports(aio_init, {aio.client: ".client", aio.config: ".config"})
    init = _package.write_package(
        context,
        title=f"{context.settings.package} Client Package",
        description=context.settings.package_description
        or f"{context.settings.package} client package",
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


def _auth_schemes(
    service: _model.ServiceShape, integrations: Sequence[ClientIntegration]
) -> tuple[_auth.AuthContribution, ...]:
    contributions = dict(_auth.DEFAULT_AUTH_SCHEMES)
    for integration in integrations:
        contributions.update(integration.auth_schemes(service))
    return _auth.supported_schemes(service, contributions)


def _new_config(
    mode: ClientMode,
    config: TypeReference,
    integrations: Sequence[ClientIntegration],
) -> tuple[str | TypeReference, ...]:
    parts: tuple[str | TypeReference, ...] = (config,)
    for integration in integrations:
        if (changed := integration.new_config(mode, config)) is not None:
            parts = changed
    return parts


def _modes(
    names: ClientNames, protocol: _protocols.ProtocolContribution
) -> tuple[ClientMode, ClientMode]:
    endpoint_resolver = _core("EndpointResolver", "interfaces")
    return (
        ClientMode(
            directory="",
            config=names.config,
            client=names.client,
            client_base=_core("Client", "client"),
            protocol=protocol.protocol,
            transport=protocol.transport,
            transport_type=_generic(_core("ClientTransport", "interfaces"), _ANY, _ANY),
            auth_scheme=_generic(_core("AuthScheme", "interfaces.auth"), *_ANY4),
            endpoint_resolver=(endpoint_resolver,),
            is_async=False,
        ),
        ClientMode(
            directory="aio/",
            config=names.async_config,
            client=names.async_client,
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
_XML_NAMESPACE: Final = _model.ShapeId("smithy.api", "xmlNamespace")
_ENDPOINT: Final = _model.ShapeId("smithy.api", "endpoint")
HOST_PREFIX_FIELD: Final = (
    "disable_host_prefix_injection",
    "Whether to skip prepending operations' modeled host prefixes to the "
    "endpoint host.",
)
"""The name and documentation of the config field that turns off host prefixes."""
_CONFIG_FIELDS: Final = frozenset(
    {
        "auth_scheme_resolver",
        "auth_schemes",
        HOST_PREFIX_FIELD[0],
        "endpoint_resolver",
        "endpoint_uri",
        "interceptors",
        "protocol",
        "retry_strategy",
        "transport",
    }
)
"""The config fields every client has, which a client context field must not take."""


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
    config: ConfigPlan,
    integrations: Sequence[ClientIntegration],
) -> None:
    plan, service, mode = config.plan, config.service, config.mode
    schemas = f"{plan.settings.import_name}._private.schemas"
    writer.line(config.protocol_settings, " = ", _PROTOCOL_SETTINGS, "(")
    with writer.indent():
        writer.line("namespace=", _models._quote(service.id.namespace), ",")  # pyright: ignore[reportPrivateUsage]
        writer.line("service_target=", _models._quote(service.id.name), ",")  # pyright: ignore[reportPrivateUsage]
        if service.version is not None:
            writer.line("version=", _models._quote(service.version), ",")  # pyright: ignore[reportPrivateUsage]
        # restXml applies the namespace to payloads that don't declare their own.
        xml_namespace = service.get_trait(_XML_NAMESPACE)
        if isinstance(xml_namespace, Mapping) and isinstance(
            uri := xml_namespace.get("uri"), str
        ):
            writer.line("xml_namespace=", _models._quote(uri), ",")  # pyright: ignore[reportPrivateUsage]
        writer.line(
            "service_schema=",
            TypeReference(plan.symbols.schema_name(service.id), schemas),
            ",",
        )
    writer.line(")")
    writer.line()
    writer.line()
    if not any(
        integration.write_config(writer, config) for integration in integrations
    ):
        _write_core_config(writer, config)
    writer.line()
    writer.line()
    writer.line("type Plugin = ", _CALLABLE, "[[", mode.config, "], None]")
    writer.line(
        _models._quote(  # pyright: ignore[reportPrivateUsage]
            "A callable that customizes the client configuration."
        )
    )


def _write_core_config(writer: PythonWriter, config: ConfigPlan) -> None:
    service, mode, endpoints, bdd = (
        config.service,
        config.mode,
        config.endpoints,
        config.bdd,
    )
    client_protocol = _generic(_core("ClientProtocol", "interfaces"), _ANY, _ANY)
    interceptor = _generic(_core("Interceptor", "interceptors"), *_ANY4)
    endpoint_resolver = _join(mode.endpoint_resolver)
    auth_schemes = ("dict[", _SHAPE_ID, ", ", mode.auth_scheme, "]")
    schemes = config.auth_schemes
    auth_fields = [field for scheme in schemes for field in scheme.fields]
    retry = (_RETRY_STRATEGY, " | ", _RETRY_STRATEGY_OPTIONS)
    fields: tuple[tuple[str, tuple[str | TypeReference, ...], str], ...] = (
        *(
            (
                field.name,
                field.async_annotation if mode.is_async else field.annotation,
                field.documentation,
            )
            for field in auth_fields
        ),
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
            "The endpoint URI, read by the endpoint rules as ``SDK::Endpoint``.",
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
        *(
            (field.attribute, (field.type, " | None"), field.documentation)
            for field in endpoints.client_context_fields
        ),
        *(
            ((HOST_PREFIX_FIELD[0], ("bool | None",), HOST_PREFIX_FIELD[1]),)
            if config.host_prefix
            else ()
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
            for field in auth_fields:
                annotation = (
                    field.async_annotation if mode.is_async else field.annotation
                )
                writer.line(field.name, ": ", *annotation, " = None,")
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
            for field in endpoints.client_context_fields:
                writer.line(field.attribute, ": ", field.type, " | None = None,")
            if config.host_prefix:
                writer.line(HOST_PREFIX_FIELD[0], ": bool | None = None,")
        writer.line(") -> None:")
        with writer.indent():
            for field in auth_fields:
                default = field.async_default if mode.is_async else field.default
                writer.line(
                    "self.",
                    field.name,
                    " = ",
                    field.name,
                    *((" or ", *default) if default else ()),
                )
            # The default resolver orders each operation's effective auth schemes,
            # so an operation with noAuth first, such as one with @auth([]), is
            # sent unsigned.
            writer.line(
                "self.auth_scheme_resolver = auth_scheme_resolver or ",
                _DEFAULT_AUTH_RESOLVER,
                "()",
            )
            if not schemes:
                writer.line("self.auth_schemes = auth_schemes or {}")
            else:
                writer.line("self.auth_schemes = auth_schemes or {")
                with writer.indent():
                    for scheme in schemes:
                        build = scheme.async_scheme if mode.is_async else scheme.scheme
                        writer.line(
                            _SHAPE_ID,
                            "(",
                            _models._quote(str(scheme.scheme_id)),  # pyright: ignore[reportPrivateUsage]
                            "): ",
                            *build(service.get_trait(scheme.scheme_id)),
                            ",",
                        )
                writer.line("}")
            writer.line(
                "self.endpoint_resolver = endpoint_resolver or ",
                *endpoints.default_resolver(bdd),
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
            for field in endpoints.client_context_fields:
                writer.line("self.", field.attribute, " = ", field.attribute)
            if config.host_prefix:
                writer.line("self.", HOST_PREFIX_FIELD[0], " = ", HOST_PREFIX_FIELD[0])
        if schemes:
            writer.line()
            writer.line(
                "def set_auth_scheme(self, scheme: ", mode.auth_scheme, ") -> None:"
            )
            with writer.indent():
                writer.line(
                    _models._quote(  # pyright: ignore[reportPrivateUsage]
                        "Set an auth scheme under its scheme ID."
                    )
                )
                writer.line("self.auth_schemes[scheme.scheme_id] = scheme")


def _items(references: tuple[TypeReference, ...]) -> tuple[str | TypeReference, ...]:
    # The items of a tuple literal, with the trailing comma a single item needs.
    parts: list[str | TypeReference] = []
    for reference in references:
        if parts:
            parts.append(", ")
        parts.append(reference)
    if len(references) == 1:
        parts.append(",")
    return tuple(parts)


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
    mode: ClientMode,
    config_module: str,
    service: _model.ServiceShape,
    paginators: tuple[_pagination.PaginatorPlan | None, ...],
    integrations: Sequence[ClientIntegration],
) -> None:
    config = TypeReference(mode.config, config_module)
    plugin = TypeReference("Plugin", config_module)
    models = TypeReference("models", plan.settings.import_name)
    writer.line("class ", mode.client, "(", _generic(mode.client_base, config), "):")
    with writer.indent():
        _models._write_docstring(  # pyright: ignore[reportPrivateUsage]
            writer,
            _models._documentation(service)  # pyright: ignore[reportPrivateUsage]
            or f"Client for {service.id.name}.",
        )
        writer.line()
        plugins = [
            reference
            for integration in integrations
            for reference in integration.client_plugins(
                plan, mode, plan.settings.import_name
            )
        ]
        writer.line("_client_plugins = (", *_items((*plugins, _USER_AGENT_PLUGIN)), ")")
        for operation, export, paginator in zip(
            plan.operations, plan.models.operations, paginators, strict=True
        ):
            _write_operation(writer, plan, mode, operation, export.name, models, plugin)
            if paginator is not None:
                _write_paginator(
                    writer,
                    plan,
                    mode,
                    operation,
                    export.name,
                    models,
                    plugin,
                    paginator,
                )
        writer.line()
        create = _new_config(mode, config, integrations)
        define = "async def " if create[0] == "await " else "def "
        writer.line(define, "_new_config(self) -> ", config, ":")
        with writer.indent():
            writer.line("return ", *create, "()")
        for integration in integrations:
            integration.write_client_methods(writer, plan, mode, config)


def _write_operation(
    writer: PythonWriter,
    plan: ClientPlan,
    mode: ClientMode,
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


def _write_paginator(
    writer: PythonWriter,
    plan: ClientPlan,
    mode: ClientMode,
    operation: OperationPlan,
    constant: str,
    models: TypeReference,
    plugin: TypeReference,
    paginator: _pagination.PaginatorPlan,
) -> None:
    # A plain def in both modes: the async paginator is iterated, not awaited.
    name = paginator.method_name
    dict_name = plan.models.input_dict_names[operation.operation.input]
    page: tuple[str | TypeReference, ...] = (models, ".", operation.output_name)
    if paginator.item_type is None:
        runtime = _core(
            "AsyncPaginator" if mode.is_async else "Paginator",
            "aio.pagination" if mode.is_async else "pagination",
        )
        result: tuple[str | TypeReference, ...] = (runtime, "[", *page, "]")
    else:
        runtime = _core(
            "AsyncItemPaginator" if mode.is_async else "ItemPaginator",
            "aio.pagination" if mode.is_async else "pagination",
        )
        item = _lazy_type(paginator.item_type, models)
        result = (runtime, "[", *page, ", ", *item, "]")
    plugins: tuple[str | TypeReference, ...] = (
        "plugins: list[",
        plugin,
        "] | None = None",
    )
    # An SDK option, never sent to the service.
    stop = "stop_on_same_token: bool = True"
    docs = (
        f"Iterates the pages of the {operation.operation.id.name} operation.\n\n"
        "Each page is the output of one call, sent as iteration reaches it. "
        "The request's token starts the first page. Pagination ends at a page "
        "with no token or an empty one. By default, it also ends, normally, at a "
        "page whose token equals the one its request sent, including the starting "
        "token."
    )
    if paginator.items is not None:
        docs += " ``items()`` iterates the items of each page instead."
    docs += (
        "\n\n:param plugins: Callables that change the configuration for each call "
        "of this traversal only."
        "\n:param stop_on_same_token: Whether to end pagination at a page whose "
        "token equals, by value, the one its request sent. Set to False to keep "
        "requesting pages when tokens repeat, such as when polling for new results. "
        "A page with no token, or an empty one, still ends pagination. This option "
        "is not sent to the service."
    )
    writer.line()
    writer.line("@", _OVERLOAD)
    writer.line("def ", name, "(")
    with writer.indent():
        writer.line("self,")
        writer.line(
            "request: ",
            models,
            ".",
            operation.input_name,
            " | ",
            models,
            ".",
            dict_name,
            ",",
        )
        writer.line("/,")
        writer.line("*,")
        writer.line(*plugins, ",")
        writer.line(stop, ",")
    writer.line(") -> ", *result, ": ...")
    writer.line()
    writer.line("@", _OVERLOAD)
    writer.line("def ", name, "(")
    with writer.indent():
        writer.line("self,")
        writer.line("/,")
        writer.line("*,")
        writer.line(*plugins, ",")
        writer.line(stop, ",")
        writer.line("**kwargs: ", _UNPACK, "[", models, ".", dict_name, "],")
    writer.line(") -> ", *result, ":")
    with writer.indent():
        _models._write_docstring(writer, docs)  # pyright: ignore[reportPrivateUsage]
    writer.line()
    writer.line("def ", name, "(")
    with writer.indent():
        writer.line("self,")
        writer.line("/,")
        writer.line("*args: object,")
        writer.line(*plugins, ",")
        writer.line(stop, ",")
        writer.line("**kwargs: object,")
    writer.line(") -> ", *result, ":")
    with writer.indent():
        writer.line("return ", runtime, "(")
        with writer.indent():
            writer.line("self._build_input(")
            with writer.indent():
                writer.line(
                    "self._select_input(", models, ".", constant, ", args, kwargs),"
                )
                writer.line(models, ".", constant, ",")
            writer.line("),")
            writer.line("self.", operation.method_name, ",")
            writer.line("plugins,")
            writer.line(
                "input_token=",
                _models._quote(paginator.input_token),  # pyright: ignore[reportPrivateUsage]
                ",  # noqa: S106 - a member name, not a secret",
            )
            writer.line("output_token=", _path(paginator.output_token), ",")
            if paginator.items is not None:
                writer.line("items=", _path(paginator.items), ",")
            writer.line("stop_on_same_token=stop_on_same_token,")
        writer.line(")")


def _path(names: tuple[str, ...]) -> str:
    quoted = [_models._quote(name) for name in names]  # pyright: ignore[reportPrivateUsage]
    return f"({quoted[0]},)" if len(quoted) == 1 else f"({', '.join(quoted)})"


def _lazy_type(
    reference: TypeReference, models: TypeReference
) -> tuple[str | TypeReference, ...]:
    """Write a type with model types as attributes of the lazily loaded models."""
    models_module = f"{models.module}.{models.name}"
    parts: list[str | TypeReference] = []
    pending: list[str | TypeReference] = [reference]
    while pending:
        part = pending.pop()
        if isinstance(part, str):
            parts.append(part)
            continue
        if part.module is None:
            parts.append("None")
            continue
        if part.module == models_module:
            parts.extend((models, ".", part.name))
        else:
            parts.append(
                TypeReference(part.name, part.module, dependencies=part.dependencies)
            )
        if part.nullable:
            pending.append(" | None")
        if part.arguments:
            pending.append("]")
            for index in range(len(part.arguments) - 1, -1, -1):
                pending.append(part.arguments[index])
                if index:
                    pending.append(", ")
            pending.append("[")
    return tuple(parts)
