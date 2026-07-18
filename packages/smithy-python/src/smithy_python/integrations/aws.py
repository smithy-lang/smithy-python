# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from dataclasses import dataclass

from ..context import GenerationContext
from ..model import ShapeID
from ..plugins import CodeSection, GeneratorPlugin
from ..symbols import SCHEMA, PythonDependency, Symbol
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
        PythonDependency("smithy-http", "~=0.4.0", extras=("aiohttp",)),
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


class AwsPlugin(GeneratorPlugin):
    """AWS protocol, signing, endpoint, and user-agent customizations."""

    name = "aws"
    after = ("rest_json",)

    def protocols(self) -> tuple[AwsQueryProtocol, ...]:
        return (AwsQueryProtocol(),)

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
