# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from ..context import GenerationContext
from ..model import Shape
from ..symbols import SCHEMA, PythonDependency
from ..writer import PythonWriter


class ConfigGenerator:
    """Generates a transport-agnostic client configuration with HTTP defaults."""

    def __init__(self, context: GenerationContext) -> None:
        self.context = context

    def run(self) -> None:
        if self.context.service is None:
            return
        writer = PythonWriter()
        self._imports(writer)
        service = self.context.service
        schema = self.context.symbol_provider.to_symbol(service).expect_property(SCHEMA)
        writer.import_(
            "._private.schemas",
            f"{schema.name} as _SCHEMA_{schema.name}",
            category="local",
        )

        aws = self._is_aws(service)
        fields = [
            "    endpoint_uri: str | URI | None",
            "    endpoint_resolver: EndpointResolver",
            "    interceptors: list[Interceptor[Any, Any, Any, Any]]",
            "    retry_strategy: RetryStrategy | RetryStrategyOptions | None",
            "    protocol: ClientProtocol[Any, Any] | None",
            "    transport: ClientTransport[Any, Any] | None",
            "    auth_scheme_resolver: AuthSchemeResolver",
            "    auth_schemes: dict[ShapeID, AuthScheme[Any, Any, Any, Any]]",
            "    http_request_config: HTTPRequestConfiguration | None",
        ]
        if aws:
            fields.extend(
                (
                    "    region: str | None",
                    "    aws_access_key_id: str | None",
                    "    aws_secret_access_key: str | None",
                    "    aws_session_token: str | None",
                    "    aws_credentials_identity_resolver: AWSCredentialsResolver | None",
                    "    sdk_ua_app_id: str | None",
                    "    user_agent_extra: str | None",
                )
            )
        writer.write("@dataclass(init=False)")
        writer.write("class Config:")
        writer.write(f'    """Configuration for {service.id.name}."""')
        for field in fields:
            writer.write(field)
        writer.write()
        writer.write("    def __init__(")
        writer.write("        self,")
        writer.write("        *,")
        writer.write("        endpoint_uri: str | URI | None = None,")
        writer.write("        endpoint_resolver: EndpointResolver | None = None,")
        writer.write(
            "        interceptors: list[Interceptor[Any, Any, Any, Any]] | None = None,"
        )
        writer.write(
            "        retry_strategy: RetryStrategy | RetryStrategyOptions | None = None,"
        )
        writer.write("        protocol: ClientProtocol[Any, Any] | None = None,")
        writer.write("        transport: ClientTransport[Any, Any] | None = None,")
        writer.write("        auth_scheme_resolver: AuthSchemeResolver | None = None,")
        writer.write(
            "        auth_schemes: dict[ShapeID, AuthScheme[Any, Any, Any, Any]] | None = None,"
        )
        writer.write(
            "        http_request_config: HTTPRequestConfiguration | None = None,"
        )
        if aws:
            writer.write("        region: str | None = None,")
            writer.write("        aws_access_key_id: str | None = None,")
            writer.write("        aws_secret_access_key: str | None = None,")
            writer.write("        aws_session_token: str | None = None,")
            writer.write(
                "        aws_credentials_identity_resolver: AWSCredentialsResolver | None = None,"
            )
            writer.write("        sdk_ua_app_id: str | None = None,")
            writer.write("        user_agent_extra: str | None = None,")
        writer.write("    ) -> None:")
        writer.write("        self.endpoint_uri = endpoint_uri")
        endpoint = (
            self._endpoint_expression(service) if aws else "StaticEndpointResolver()"
        )
        writer.write(
            f"        self.endpoint_resolver = endpoint_resolver or {endpoint}"
        )
        writer.write("        self.interceptors = list(interceptors or ())")
        writer.write("        self.retry_strategy = retry_strategy")
        expression = (
            self.context.protocol.protocol_expression(self.context)
            if self.context.protocol is not None
            else "None"
        )
        writer.write(f"        self.protocol = protocol or {expression}")
        writer.write(
            "        self.transport = transport or AWSCRTHTTPClient()"
            if aws
            else "        self.transport = transport"
        )
        auth_schemes = self._auth_schemes(service)
        resolver = "DefaultAuthResolver()" if auth_schemes else "NoAuthResolver()"
        writer.write(
            f"        self.auth_scheme_resolver = auth_scheme_resolver or {resolver}"
        )
        if auth_schemes:
            entries = ", ".join(
                f"ShapeID({shape_id!r}): {initializer}"
                for shape_id, initializer in auth_schemes
            )
            writer.write(f"        self.auth_schemes = auth_schemes or {{{entries}}}")
        else:
            writer.write("        self.auth_schemes = auth_schemes or {}")
        writer.write("        self.http_request_config = http_request_config")
        if aws:
            writer.write("        self.region = region")
            writer.write("        self.aws_access_key_id = aws_access_key_id")
            writer.write("        self.aws_secret_access_key = aws_secret_access_key")
            writer.write("        self.aws_session_token = aws_session_token")
            writer.write("        self.sdk_ua_app_id = sdk_ua_app_id")
            writer.write("        self.user_agent_extra = user_agent_extra")
            writer.write("        self.aws_credentials_identity_resolver = (")
            writer.write("            aws_credentials_identity_resolver")
            writer.write("            or ChainedIdentityResolver(")
            writer.write(
                "                resolvers=(StaticCredentialsResolver(), EnvironmentCredentialsResolver())"
            )
            writer.write("            )")
            writer.write("        )")
        writer.write()
        writer.write("    def set_auth_scheme(")
        writer.write("        self, scheme: AuthScheme[Any, Any, Any, Any]")
        writer.write("    ) -> None:")
        writer.write("        self.auth_schemes[scheme.scheme_id] = scheme")
        writer.write()
        writer.write("Plugin: TypeAlias = Callable[[Config], None]")
        writer.write('"""A callable that customizes client configuration."""')

        path = f"src/{self.context.settings.module_name}/config.py"
        self.context.write(path, writer.render(), section="config", shape=service)

    def _imports(self, writer: PythonWriter) -> None:
        service = self.context.service
        if service is None:
            return
        aws = self._is_aws(service)
        auth_schemes = self._auth_schemes(service)
        writer.import_("dataclasses", "dataclass", category="stdlib")
        writer.import_("typing", "Any", category="stdlib")
        writer.import_("typing", "Callable", category="stdlib")
        writer.import_("typing", "TypeAlias", category="stdlib")
        if not aws:
            writer.import_(
                "smithy_core.aio.endpoints",
                "StaticEndpointResolver",
                category="third_party",
            )
        if aws:
            writer.import_(
                "smithy_core.aio.identity",
                "ChainedIdentityResolver",
                category="third_party",
            )
        writer.import_(
            "smithy_core.aio.interfaces", "ClientProtocol", category="third_party"
        )
        writer.import_(
            "smithy_core.aio.interfaces", "ClientTransport", category="third_party"
        )
        writer.import_(
            "smithy_core.aio.interfaces", "EndpointResolver", category="third_party"
        )
        writer.import_(
            "smithy_core.aio.interfaces.auth", "AuthScheme", category="third_party"
        )
        writer.import_(
            "smithy_core.aio.interfaces.retries",
            "RetryStrategy",
            category="third_party",
        )
        writer.import_(
            "smithy_core.auth",
            "DefaultAuthResolver" if auth_schemes else "NoAuthResolver",
            category="third_party",
        )
        writer.import_("smithy_core.interfaces", "URI", category="third_party")
        writer.import_(
            "smithy_core.interfaces.auth", "AuthSchemeResolver", category="third_party"
        )
        writer.import_(
            "smithy_core.interceptors", "Interceptor", category="third_party"
        )
        writer.import_(
            "smithy_core.retries", "RetryStrategyOptions", category="third_party"
        )
        writer.import_("smithy_core.shapes", "ShapeID", category="third_party")
        writer.import_(
            "smithy_http.interfaces", "HTTPRequestConfiguration", category="third_party"
        )
        if self.context.protocol is not None:
            protocol_symbol = self.context.protocol.protocol_symbol
            writer.import_(
                protocol_symbol.namespace,
                protocol_symbol.name,
                category="third_party",
            )
            self.context.add_dependency(*self.context.protocol.dependencies)
        if aws:
            writer.import_(
                "smithy_http.aio.crt", "AWSCRTHTTPClient", category="third_party"
            )
            self.context.add_dependency(
                PythonDependency("smithy-http", "~=0.4.0", extras=("awscrt",))
            )
            writer.import_(
                "smithy_aws_core.auth", "SigV4AuthScheme", category="third_party"
            )
            writer.import_(
                "smithy_aws_core.endpoints.standard_regional",
                "StandardRegionalEndpointsResolver",
                category="third_party",
            )
            writer.import_(
                "smithy_aws_core.identity",
                "AWSCredentialsResolver",
                category="third_party",
            )
            writer.import_(
                "smithy_aws_core.identity",
                "EnvironmentCredentialsResolver",
                category="third_party",
            )
            writer.import_(
                "smithy_aws_core.identity",
                "StaticCredentialsResolver",
                category="third_party",
            )

    def _is_aws(self, service: Shape) -> bool:
        return service.has_trait("aws.api#service")

    def _endpoint_expression(self, service: Shape) -> str:
        trait = service.trait("aws.api#service")
        endpoint_prefix = None
        if isinstance(trait, dict):
            endpoint_prefix = trait.get("endpointPrefix")
        endpoint_prefix = endpoint_prefix or service.id.name.lower()
        return f"StandardRegionalEndpointsResolver(endpoint_prefix={endpoint_prefix!r})"

    def _auth_schemes(self, service: Shape) -> tuple[tuple[str, str], ...]:
        auth = service.trait("smithy.api#auth", [])
        auth_ids: set[str] = (
            {value for value in auth if isinstance(value, str)}
            if isinstance(auth, list)
            else set[str]()
        )
        if service.has_trait("aws.auth#sigv4"):
            auth_ids.add("aws.auth#sigv4")
        result: list[tuple[str, str]] = []
        if "aws.auth#sigv4" in auth_ids:
            trait = service.trait("aws.auth#sigv4")
            name = trait.get("name") if isinstance(trait, dict) else None
            result.append(
                (
                    "aws.auth#sigv4",
                    f"SigV4AuthScheme(service={name or service.id.name.lower()!r})",
                )
            )
        return tuple(result)
