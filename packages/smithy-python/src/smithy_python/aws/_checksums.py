# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Flexible checksums for AWS services with the ``aws.protocols#httpChecksum`` trait.

As in the Java generator's ``AwsFlexibleChecksumsIntegration``, clients apply a
plugin that adds the runtime's checksum interceptor. Their configs get
``request_checksum_calculation`` when an operation calculates request checksums,
and ``response_checksum_validation`` when one validates response checksums.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from .. import model as _model
from .. import models as _models
from ..dependencies import Dependency
from ..integrations import ClientIntegration, ClientMode
from ..symbols import TypeReference
from ._dependencies import SMITHY_AWS_CORE

if TYPE_CHECKING:
    from ..clients import ClientPlan
    from ..generation import ClientSettings, GenerationContext
    from ..integrations import Part

__all__ = ["AwsChecksumsIntegration", "ChecksumField", "checksum_fields"]

_SERVICE: Final = _model.ShapeId("aws.api", "service")
_HTTP_CHECKSUM: Final = _model.ShapeId("aws.protocols", "httpChecksum")
_PLUGIN: Final = "flexible_checksums_plugin"


@dataclass(frozen=True, slots=True)
class ChecksumField:
    """A checksum setting's config field."""

    name: str
    type: TypeReference
    documentation: str

    @property
    def spec(self) -> tuple[Part, ...]:
        """The field's ``FieldSpec`` arguments."""
        return (
            'default="when_supported", resolver=',
            _aws(f"resolve_{self.name}_program", "config.resolvers"),
            ", validator=",
            _aws(f"validate_{self.name}", "config.validators"),
        )


_REQUEST: Final = ChecksumField(
    "request_checksum_calculation",
    TypeReference(
        "RequestChecksumCalculation",
        "smithy_aws_core.config.types",
        dependencies=(SMITHY_AWS_CORE,),
    ),
    "When to calculate request checksums: `when_supported` (the default) or "
    "`when_required`, only when the operation requires one or the request sets an "
    "algorithm.",
)
_RESPONSE: Final = ChecksumField(
    "response_checksum_validation",
    TypeReference(
        "ResponseChecksumValidation",
        "smithy_aws_core.config.types",
        dependencies=(SMITHY_AWS_CORE,),
    ),
    "When to validate response checksums: `when_supported` (the default) or "
    "`when_required`, only when the request enables validation.",
)


class AwsChecksumsIntegration(ClientIntegration):
    """Flexible checksums, for AWS services with ``httpChecksum`` operations."""

    def matches(self, service: _model.ServiceShape) -> bool:
        # The operations are checked when fields and plugins are planned.
        return service.has_trait(_SERVICE)

    def config_fields(self, service: _model.ServiceShape) -> Collection[str]:
        del service
        return (_REQUEST.name, _RESPONSE.name)

    def client_plugins(
        self, plan: ClientPlan, mode: ClientMode, package: str
    ) -> tuple[TypeReference, ...]:
        if not _traits(plan):
            return ()
        return (TypeReference(_PLUGIN, _module(package, mode)),)

    def write_files(
        self,
        context: GenerationContext[ClientSettings],
        plan: ClientPlan,
        modes: tuple[ClientMode, ClientMode],
    ) -> None:
        if not _traits(plan):
            return
        package = context.settings.import_name
        for mode in modes:
            module = _module(package, mode)
            writer = context.files.python_module(
                f"src/{module.replace('.', '/')}.py", module
            )
            config = TypeReference(
                mode.config, f"{package}.{mode.directory.replace('/', '.')}config"
            )
            interceptor = (
                _checksums("AsyncFlexibleChecksumsInterceptor", "aio.interceptors")
                if mode.is_async
                else _checksums("FlexibleChecksumsInterceptor", "interceptors")
            )
            writer.line("def ", _PLUGIN, "(config: ", config, ") -> None:")
            with writer.indent():
                writer.line(
                    _quote("Add and validate the checksums the operations model.")
                )
                writer.line("config.interceptors.append(", interceptor, "())")


def checksum_fields(plan: ClientPlan) -> tuple[ChecksumField, ...]:
    """The checksum settings that have an effect on a client, in order."""
    traits = _traits(plan)
    fields: list[ChecksumField] = []
    if any(
        trait.get("requestChecksumRequired") is True
        or isinstance(trait.get("requestAlgorithmMember"), str)
        for trait in traits
    ):
        fields.append(_REQUEST)
    if any(
        trait.get("responseAlgorithms")
        and isinstance(trait.get("requestValidationModeMember"), str)
        for trait in traits
    ):
        fields.append(_RESPONSE)
    return tuple(fields)


def _traits(plan: ClientPlan) -> tuple[Mapping[str, _model.Node], ...]:
    return tuple(
        trait
        for operation in plan.operations
        if isinstance(trait := operation.operation.get_trait(_HTTP_CHECKSUM), Mapping)
    )


def _module(package: str, mode: ClientMode) -> str:
    return f"{package}.{mode.directory.replace('/', '.')}checksums"


def _aws(name: str, module: str) -> TypeReference:
    return TypeReference(
        name, f"smithy_aws_core.{module}", dependencies=(SMITHY_AWS_CORE,)
    )


def _checksums(name: str, module: str) -> TypeReference:
    return TypeReference(
        name,
        f"smithy_aws_core.{module}.checksums",
        dependencies=(
            Dependency(
                package=SMITHY_AWS_CORE.package,
                specifier=SMITHY_AWS_CORE.specifier,
                group="runtime",
                extras=("checksums",),
            ),
        ),
    )


def _quote(value: str) -> str:
    return _models._quote(value)  # pyright: ignore[reportPrivateUsage]
