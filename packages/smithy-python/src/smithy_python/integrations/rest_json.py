# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from dataclasses import dataclass

from ..context import GenerationContext
from ..model import ShapeID
from ..plugins import CodeSection, GeneratorPlugin
from ..symbols import SCHEMA, PythonDependency, Symbol


@dataclass(frozen=True, slots=True)
class RestJsonProtocol:
    protocol_id = ShapeID.parse("aws.protocols#restJson1")
    application_protocol = "http"
    protocol_symbol = Symbol(
        name="RestJsonClientProtocol",
        namespace="smithy_aws_core.aio.protocols",
    )
    dependencies = (
        PythonDependency("smithy-core", "~=0.6.0"),
        PythonDependency("smithy-http", "~=0.4.0", extras=("aiohttp",)),
        PythonDependency("smithy-aws-core", "~=0.7.0", extras=("json",)),
    )

    def protocol_expression(self, context: GenerationContext) -> str:
        service = context.service
        if service is None:
            raise ValueError("RestJson protocol requires a service")
        schema = context.symbol_provider.to_symbol(service).expect_property(SCHEMA)
        return f"{self.protocol_symbol.name}(_SCHEMA_{schema.name})"

    def generate_tests(self, context: GenerationContext) -> None:
        from ..generators.protocol_tests import ProtocolTestGenerator

        ProtocolTestGenerator(context, self.protocol_id).run()


class RestJsonPlugin(GeneratorPlugin):
    name = "rest_json"

    def protocols(self) -> tuple[RestJsonProtocol, ...]:
        return (RestJsonProtocol(),)

    def intercept_code(
        self, context: GenerationContext, section: CodeSection, code: str
    ) -> str:
        if (
            section.name == "client.default_plugins"
            and context.protocol is not None
            and context.protocol.application_protocol == "http"
        ):
            return f"{code}        user_agent_plugin,\n"
        return code
