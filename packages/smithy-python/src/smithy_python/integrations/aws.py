# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from types import MappingProxyType

from ..context import GenerationContext
from ..model import Member, Model, Shape, ShapeID
from ..plugins import CodeSection, GeneratorPlugin
from ..settings import GeneratorSettings
from ..symbols import SCHEMA, PythonDependency, Symbol, SymbolProvider
from ..writer import PythonWriter


@dataclass(frozen=True, slots=True)
class AwsQueryProtocol:
    protocol_id = ShapeID.parse("aws.protocols#awsQuery")
    application_protocol = "http"
    protocol_symbol = Symbol(
        name="AwsQueryClientProtocol",
        namespace="smithy_aws_core.aio.protocols",
    )
    dependencies = (
        PythonDependency("smithy-core", "~=0.6.0"),
        PythonDependency("smithy-http", "~=0.4.0"),
        PythonDependency("smithy-aws-core", "~=0.7.0", extras=("xml",)),
    )

    def protocol_expression(self, context: GenerationContext) -> str:
        service = context.service
        if service is None:
            raise ValueError("AWS Query protocol requires a service")
        schema = context.symbol_provider.to_symbol(service).expect_property(SCHEMA)
        version = service.attributes.get("version", "")
        return (
            f"{self.protocol_symbol.name}(_SCHEMA_{schema.name}, version={version!r})"
        )

    def generate_tests(self, context: GenerationContext) -> None:
        from ..generators.protocol_tests import ProtocolTestGenerator

        ProtocolTestGenerator(context, self.protocol_id).run()


@dataclass(frozen=True, slots=True)
class _AwsSymbolProvider:
    delegate: SymbolProvider
    service_id: ShapeID
    client_name: str

    def to_symbol(self, shape: Shape | Member) -> Symbol:
        symbol = self.delegate.to_symbol(shape)
        if isinstance(shape, Shape) and shape.id == self.service_id:
            return replace(symbol, name=self.client_name)
        return symbol

    def to_member_name(self, member: Member, *, container: Shape | None = None) -> str:
        return self.delegate.to_member_name(member, container=container)

    def union_member_symbol(self, container: Shape, member: Member) -> Symbol:
        return self.delegate.union_member_symbol(container, member)


class AwsPlugin(GeneratorPlugin):
    """AWS protocol, signing, endpoint, and user-agent customizations."""

    name = "aws"
    after = ("rest_json",)

    def protocols(self) -> tuple[AwsQueryProtocol, ...]:
        return (AwsQueryProtocol(),)

    def preprocess_model(self, model: Model, settings: GeneratorSettings) -> Model:
        if settings.service is None:
            return model
        service = model.service(settings.service)
        if not service.has_trait("aws.auth#sigv4") or service.has_trait(
            "smithy.api#auth"
        ):
            return model
        updated_service = replace(
            service,
            traits=MappingProxyType(
                {**service.traits, "smithy.api#auth": ["aws.auth#sigv4"]}
            ),
        )
        return model.replace_shapes(
            updated_service if shape.id == service.id else shape for shape in model
        )

    def decorate_symbol_provider(
        self, provider: SymbolProvider, context: GenerationContext
    ) -> SymbolProvider:
        service = context.service
        if service is None:
            return provider
        trait = service.trait("aws.api#service")
        sdk_id = trait.get("sdkId") if isinstance(trait, dict) else None
        if not isinstance(sdk_id, str):
            return provider
        name = re.sub(r"[^A-Za-z0-9_]", "", sdk_id)
        if not name:
            return provider
        if name[0].isdigit():
            name = f"_{name}"
        return _AwsSymbolProvider(
            delegate=provider,
            service_id=service.id,
            client_name=f"{name}Client",
        )

    def write_additional_files(self, context: GenerationContext) -> None:
        service = context.service
        if service is None or not service.has_trait("aws.api#service"):
            return
        context.add_dependency(PythonDependency("smithy-aws-core", "~=0.7.0"))
        writer = PythonWriter()
        writer.import_(
            "smithy_aws_core.interceptors.user_agent",
            "UserAgentInterceptor",
            category="third_party",
        )
        writer.import_(".", "__version__", category="local")
        trait = service.trait("aws.api#service")
        service_id = trait.get("sdkId") if isinstance(trait, dict) else None
        service_id = service_id if isinstance(service_id, str) else service.id.name
        writer.write("def aws_user_agent_plugin(config: object) -> None:")
        writer.write(
            '    """Add AWS SDK identity to the generated client\'s user agent."""'
        )
        writer.write('    interceptors = getattr(config, "interceptors")')
        writer.write("    interceptors.append(")
        writer.write("        UserAgentInterceptor(")
        writer.write('            ua_suffix=getattr(config, "user_agent_extra", None),')
        writer.write('            ua_app_id=getattr(config, "sdk_ua_app_id", None),')
        writer.write("            sdk_version=__version__,")
        writer.write(f"            service_id={service_id!r},")
        writer.write("        )")
        writer.write("    )")
        context.write(
            f"src/{context.settings.module_name}/user_agent.py",
            writer.render(),
            section="aws.user_agent",
            shape=service,
        )

    def intercept_code(
        self, context: GenerationContext, section: CodeSection, code: str
    ) -> str:
        service = context.service
        if service is None or not service.has_trait("aws.api#service"):
            return code
        if section.name == "client.default_plugins":
            return f"{code}        aws_user_agent_plugin,\n"
        return code
