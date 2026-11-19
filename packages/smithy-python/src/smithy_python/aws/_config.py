# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""AWS client names, config classes, and the AWS user agent plugin."""

from __future__ import annotations

from collections.abc import Collection, Mapping
from typing import TYPE_CHECKING, Final

from .. import dependencies as _dependencies
from .. import exceptions as _exceptions
from .. import model as _model
from .. import models as _models
from ..integrations import ClientIntegration, ClientMode, ClientNames, ConfigPlan
from ..symbols import TypeReference
from ._dependencies import SMITHY_AWS_CORE

if TYPE_CHECKING:
    from ..clients import ClientPlan
    from ..generation import ClientSettings, GenerationContext
    from ..integrations import Part
    from ..writer import PythonWriter

__all__ = ["AwsConfigIntegration"]


class AwsConfigIntegration(ClientIntegration):
    """Clients and configs of services with the ``aws.api#service`` trait.

    The configs subclass ``AwsConfig`` and ``AsyncAwsConfig``, so they resolve
    from environment variables and shared config files, and a client creates its
    default config with ``resolve()``. Clients and configs are named for the
    service's SDK ID, and clients send the AWS user agent.
    """

    def matches(self, service: _model.ServiceShape) -> bool:
        return service.has_trait(_SERVICE)

    def client_names(
        self, service: _model.ServiceShape, names: ClientNames
    ) -> ClientNames:
        name = _sdk_id(service).replace(" ", "")
        name = name[:1].upper() + name[1:]
        return ClientNames(
            client=f"{name}Client",
            config=f"{name}Config",
            async_client=f"Async{name}Client",
            async_config=f"Async{name}Config",
        )

    def config_fields(self, service: _model.ServiceShape) -> Collection[str]:
        del service
        return _BASE_FIELDS

    def write_config(self, writer: PythonWriter, config: ConfigPlan) -> bool:
        _write_config(writer, config)
        return True

    def new_config(self, mode: ClientMode, config: TypeReference) -> tuple[Part, ...]:
        return ("await ", config, ".resolve") if mode.is_async else (config, ".resolve")

    def client_plugins(
        self, plan: ClientPlan, mode: ClientMode, package: str
    ) -> tuple[TypeReference, ...]:
        del plan
        return (TypeReference(_PLUGIN, _user_agent_module(package, mode)),)

    def write_files(
        self,
        context: GenerationContext[ClientSettings],
        plan: ClientPlan,
        modes: tuple[ClientMode, ClientMode],
    ) -> None:
        package = context.settings.import_name
        service = plan.selection.service
        assert service is not None  # noqa: S101 - ClientPlan requires a service
        for mode in modes:
            module = _user_agent_module(package, mode)
            writer = context.files.python_module(
                f"src/{module.replace('.', '/')}.py", module
            )
            config = TypeReference(
                mode.config, f"{package}.{mode.directory.replace('/', '.')}config"
            )
            writer.line("def ", _PLUGIN, "(config: ", config, ") -> None:")
            with writer.indent():
                writer.line(_quote("Send the AWS user agent with every request."))
                writer.line("config.interceptors.append(")
                with writer.indent():
                    writer.line(_USER_AGENT_INTERCEPTOR, "(")
                    with writer.indent():
                        writer.line("ua_suffix=config.user_agent_extra,")
                        writer.line("ua_app_id=config.sdk_ua_app_id,")
                        writer.line(
                            "sdk_version=", TypeReference("__version__", package), ","
                        )
                        writer.line(
                            "service_id=",
                            _quote(_sdk_id(service).replace(" ", "_")),
                            ",",
                        )
                    writer.line(")")
                writer.line(")")


def _aws(name: str, module: str) -> TypeReference:
    return TypeReference(
        name, f"smithy_aws_core.{module}", dependencies=(SMITHY_AWS_CORE,)
    )


def _core(name: str, module: str) -> TypeReference:
    return TypeReference(
        name, f"smithy_core.{module}", dependencies=(_dependencies.SMITHY_CORE,)
    )


def _generic(reference: TypeReference, *arguments: TypeReference) -> TypeReference:
    return TypeReference(
        reference.name,
        reference.module,
        arguments=arguments,
        dependencies=reference.dependencies,
    )


def _quote(value: str) -> str:
    return _models._quote(value)  # pyright: ignore[reportPrivateUsage]


def _sdk_id(service: _model.ServiceShape) -> str:
    trait = service.get_trait(_SERVICE)
    sdk_id = trait.get("sdkId") if isinstance(trait, Mapping) else None
    if not isinstance(sdk_id, str) or not sdk_id.strip():
        raise _exceptions.CodegenError(
            f"Service {service.id} has an aws.api#service trait without an sdkId"
        )
    return sdk_id


def _user_agent_module(package: str, mode: ClientMode) -> str:
    return f"{package}.{mode.directory.replace('/', '.')}user_agent"


def _write_config(writer: PythonWriter, config: ConfigPlan) -> None:
    service, mode, endpoints = config.service, config.mode, config.endpoints
    sync = not mode.is_async
    base = (
        _aws("AwsConfig", "config.aws_config")
        if sync
        else _aws("AsyncAwsConfig", "aio.config.aws_config")
    )
    overrides_base = (
        _aws("AwsConfigOverrides", "config.aws_config")
        if sync
        else _aws("AsyncAwsConfigOverrides", "aio.config.aws_config")
    )
    file_system = (
        _aws("FileSystem", "config.filesystem")
        if sync
        else _aws("AsyncFileSystem", "aio.config.filesystem")
    )
    settings = config.protocol_settings
    client_protocol = _generic(_core("ClientProtocol", "interfaces"), _ANY, _ANY)
    protocol_input = (
        client_protocol,
        " | ",
        _generic(_core("ProtocolConstructor", "interfaces"), client_protocol),
    )
    endpoint_resolver = _join(mode.endpoint_resolver)
    auth_schemes = ("dict[", _SHAPE_ID, ", ", mode.auth_scheme, "]")
    auth_fields = [field for scheme in config.auth_schemes for field in scheme.fields]
    # Fields the base config lacks: (name, annotation, documentation, FieldSpec).
    fields: list[tuple[str, tuple[Part, ...], str, tuple[Part, ...]]] = [
        (
            "endpoint_resolver",
            (*endpoint_resolver, " | None"),
            "Resolves the endpoint of each operation.",
            (
                "default_factory=lambda: ",
                _BDD_ENDPOINT_RESOLVER,
                "(",
                config.bdd,
                ")",
            ),
        ),
        (
            "protocol",
            (client_protocol, " | None"),
            "Serializes requests and deserializes responses.",
            (
                "default_factory=lambda: ",
                mode.protocol,
                f"({settings}), converter=lambda p: p({settings}) "
                "if isinstance(p, type) else p",
            ),
        ),
        (
            "auth_schemes",
            (*auth_schemes, " | None"),
            "Auth schemes by auth scheme ID.",
            ("default_factory=lambda: ", *_default_auth_schemes(config)),
        ),
        (
            "auth_scheme_resolver",
            (_AUTH_SCHEME_RESOLVER, " | None"),
            "Determines the auth scheme for each operation.",
            # The default resolver orders each operation's effective auth schemes,
            # so an operation with noAuth first is sent unsigned.
            ("default_factory=", _DEFAULT_AUTH_RESOLVER),
        ),
        *(
            (
                field.name,
                field.annotation if sync else field.async_annotation,
                field.documentation,
                _field_default(field.default if sync else field.async_default),
            )
            for field in auth_fields
        ),
        *(
            (
                field.attribute,
                (field.type, " | None"),
                field.documentation,
                ("default=None",),
            )
            for field in endpoints.client_context_fields
        ),
    ]
    overrides = f"_{mode.config}Overrides"
    writer.line("class ", overrides, "(", overrides_base, ", total=False):")
    with writer.indent():
        writer.line(_quote(f"Explicit field values {mode.config}.resolve accepts."))
        writer.line()
        for name, annotation, _docs, _spec in fields:
            if name == "protocol":
                writer.line(name, ": ", *protocol_input, " | None")
            else:
                writer.line(name, ": ", *annotation)
    writer.line()
    writer.line()
    # repr=False keeps the base __repr__, which leaves out credentials.
    writer.line("@", _DATACLASS, "(kw_only=True, repr=False, init=False)")
    writer.line("class ", mode.config, "(", base, "):")
    with writer.indent():
        writer.line(_quote(f"Configuration for {mode.client}."))
        writer.line()
        interceptor = _generic(_core("Interceptor", "interceptors"), *_ANY4)
        writer.line(
            "interceptors: list[",
            interceptor,
            "] = ",
            _FIELD,
            "(default_factory=list[",
            interceptor,
            "])",
        )
        writer.line(_quote("Hooks called during the execution of a request."))
        for name, annotation, docs, _spec in fields:
            writer.line()
            writer.line(name, ": ", *annotation, " = None")
            writer.line(_quote(docs))
        writer.line()
        writer.line("_FIELDS: ", _CLASS_VAR, "[dict[str, ", _FIELD_SPEC, "]] = {")
        with writer.indent():
            writer.line("**", base, "._FIELDS,")
            writer.line(
                '"endpoint_uri": ',
                _FIELD_SPEC,
                "(default=None, resolver=",
                _ENDPOINT_URI_RESOLVER,
                "(",
                _quote(_sdk_id(service).replace(" ", "_").lower()),
                ").program),",
            )
            for name, _annotation, _docs, spec in fields:
                writer.line(_quote(name), ": ", _FIELD_SPEC, "(", *spec, "),")
            writer.line(
                '"transport": ',
                _FIELD_SPEC,
                "(default_factory=lambda: ",
                mode.transport,
                "()),",
            )
        writer.line("}")
        if config.auth_schemes:
            writer.line()
            writer.line(
                "def set_auth_scheme(self, scheme: ", mode.auth_scheme, ") -> None:"
            )
            with writer.indent():
                writer.line(_quote("Set an auth scheme under its scheme ID."))
                writer.line("auth_schemes = dict(self.auth_schemes or {})")
                writer.line("auth_schemes[scheme.scheme_id] = scheme")
                writer.line("self.auth_schemes = auth_schemes")
        writer.line()
        writer.line("@classmethod")
        define = "def " if sync else "async def "
        writer.line(
            define, "resolve(  # pyright: ignore[reportIncompatibleMethodOverride]"
        )
        with writer.indent():
            writer.line("cls,")
            writer.line("*,")
            writer.line("profile: str | None = None,")
            writer.line("fs: ", file_system, " | None = None,")
            writer.line("config_file_path: str | None = None,")
            writer.line("credentials_file_path: str | None = None,")
            writer.line("**overrides: ", _UNPACK, "[", overrides, "],")
        writer.line(") -> ", _SELF, ":")
        with writer.indent():
            writer.line(
                _quote(
                    "Resolve the config from overrides, the environment, and "
                    "config files."
                )
            )
            writer.line("return ", "" if sync else "await ", "cls._resolve(")
            with writer.indent():
                writer.line("profile=profile,")
                writer.line("fs=fs,")
                writer.line("config_file_path=config_file_path,")
                writer.line("credentials_file_path=credentials_file_path,")
                writer.line("overrides=overrides,")
            writer.line(")")


def _default_auth_schemes(config: ConfigPlan) -> tuple[Part, ...]:
    parts: list[Part] = ["{"]
    for scheme in config.auth_schemes:
        build = scheme.async_scheme if config.mode.is_async else scheme.scheme
        if len(parts) > 1:
            parts.append(", ")
        parts.extend(
            (
                _SHAPE_ID,
                "(",
                _quote(str(scheme.scheme_id)),
                "): ",
                *build(config.service.get_trait(scheme.scheme_id)),
            )
        )
    parts.append("}")
    return tuple(parts)


def _field_default(default: tuple[Part, ...]) -> tuple[Part, ...]:
    return ("default_factory=lambda: ", *default) if default else ("default=None",)


def _join(references: tuple[TypeReference, ...]) -> tuple[Part, ...]:
    parts: list[Part] = []
    for reference in references:
        if parts:
            parts.append(" | ")
        parts.append(reference)
    return tuple(parts)


_SERVICE: Final = _model.ShapeId("aws.api", "service")
_PLUGIN: Final = "aws_user_agent_plugin"
# The fields AwsConfig and AsyncAwsConfig declare, and those every generated AWS
# config adds.
_BASE_FIELDS: Final = frozenset(
    {
        "aws_access_key_id",
        "aws_credentials_identity_resolver",
        "aws_secret_access_key",
        "aws_session_token",
        "endpoint_uri",
        "http_request_config",
        "interceptors",
        "max_attempts",
        "region",
        "retry_mode",
        "retry_strategy",
        "sdk_ua_app_id",
        "transport",
        "user_agent_extra",
    }
)
_ANY: Final = TypeReference("Any", "typing")
_ANY4: Final = (_ANY, _ANY, _ANY, _ANY)
_CLASS_VAR: Final = TypeReference("ClassVar", "typing")
_SELF: Final = TypeReference("Self", "typing")
_UNPACK: Final = TypeReference("Unpack", "typing")
_DATACLASS: Final = TypeReference("dataclass", "dataclasses")
_FIELD: Final = TypeReference("field", "dataclasses")
_FIELD_SPEC: Final = _aws("FieldSpec", "config.types")
_ENDPOINT_URI_RESOLVER: Final = _aws("EndpointUriResolver", "config.resolvers")
_USER_AGENT_INTERCEPTOR: Final = _aws("UserAgentInterceptor", "interceptors.user_agent")
_SHAPE_ID: Final = _core("ShapeID", "shapes")
_AUTH_SCHEME_RESOLVER: Final = _core("AuthSchemeResolver", "interfaces.auth")
_DEFAULT_AUTH_RESOLVER: Final = _core("DefaultAuthResolver", "auth")
_BDD_ENDPOINT_RESOLVER: Final = _core("BddEndpointResolver", "endpoints")
