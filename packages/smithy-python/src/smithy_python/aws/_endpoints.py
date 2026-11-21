# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""The AWS endpoint rules extension and the config fields its built-ins read."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from .. import model as _model
from .. import models as _models
from .._endpoints import RulesExtension
from ..integrations import ClientIntegration
from ..symbols import TypeReference
from ._dependencies import SMITHY_AWS_CORE

if TYPE_CHECKING:
    from ..integrations import Part

__all__ = [
    "AWS_RULES_EXTENSION",
    "BUILTIN_FIELDS",
    "AwsEndpointsIntegration",
    "BuiltinField",
    "builtin_fields",
    "static_credentials",
]


@dataclass(frozen=True, slots=True)
class BuiltinField:
    """A config field the AWS rules extension binds a built-in to."""

    name: str
    default: str | None
    """The field's default, or None."""

    resolver: TypeReference
    """The program that resolves the field from the environment and profile."""

    validator: TypeReference | None = None


class AwsEndpointsIntegration(ClientIntegration):
    """The AWS rules extension, for AWS services and rules that use AWS parts.

    The default endpoint resolver gets ``AWS_RULES_EXTENSION``, which adds the
    ``aws.*`` functions and binds the ``AWS::*`` built-ins to config fields. In
    generated endpoint tests of AWS services, those built-ins set their fields.
    """

    def matches(self, service: _model.ServiceShape) -> bool:
        return service.has_trait(_SERVICE) or _uses_aws_rules(service)

    def rules_extensions(
        self, service: _model.ServiceShape
    ) -> tuple[RulesExtension, ...]:
        del service
        return (AWS_RULES_EXTENSION,)

    def endpoint_test_builtin(
        self, service: _model.ServiceShape, builtin: str, value: _model.Node
    ) -> tuple[str, tuple[Part, ...]] | None:
        # Only AWS configs have fields for the AWS built-ins.
        if not service.has_trait(_SERVICE):
            return None
        if builtin == _REGION:
            return ("region", (_literal(value),))
        if (field := BUILTIN_FIELDS.get(builtin)) is not None:
            return (field.name, (_literal(value),))
        # The account ID is read from the identity, so the test credentials
        # carry it.
        if builtin == _ACCOUNT_ID and isinstance(value, str):
            return ("aws_credentials_identity_resolver", static_credentials(value))
        return None


def builtin_fields(
    service: _model.ServiceShape,
) -> tuple[tuple[Mapping[str, _model.Node], BuiltinField], ...]:
    """The config field of each built-in the service's rules declare.

    :returns: Each rules parameter definition with its field, in trait order.
    """
    trait = service.get_trait(_ENDPOINT_BDD)
    parameters = trait.get("parameters") if isinstance(trait, Mapping) else None
    if not isinstance(parameters, Mapping):
        return ()
    fields: list[tuple[Mapping[str, _model.Node], BuiltinField]] = []
    for definition in parameters.values():
        if not isinstance(definition, Mapping):
            continue
        builtin = definition.get("builtIn")
        if isinstance(builtin, str) and (field := BUILTIN_FIELDS.get(builtin)):
            fields.append((definition, field))
    return tuple(fields)


def static_credentials(account_id: str | None = None) -> tuple[Part, ...]:
    """An async static credentials resolver with test credentials."""
    arguments = (
        'access_key_id="test-access-key-id", secret_access_key="test-secret-access-key"'
    )
    if account_id is not None:
        arguments += f", account_id={_quote(account_id)}"
    return (_STATIC_CREDENTIALS, "(", _CREDENTIALS_IDENTITY, f"({arguments}))")


def _aws(name: str, module: str) -> TypeReference:
    return TypeReference(
        name, f"smithy_aws_core.{module}", dependencies=(SMITHY_AWS_CORE,)
    )


def _quote(value: str) -> str:
    return _models._quote(value)  # pyright: ignore[reportPrivateUsage]


def _literal(value: _model.Node) -> str:
    if isinstance(value, bool):
        return "True" if value else "False"
    if isinstance(value, str):
        return _quote(value)
    return "None" if value is None else repr(value)


def _uses_aws_rules(service: _model.ServiceShape) -> bool:
    trait = service.get_trait(_ENDPOINT_BDD)
    if not isinstance(trait, Mapping):
        return False
    parameters = trait.get("parameters")
    if isinstance(parameters, Mapping):
        for definition in parameters.values():
            builtin = (
                definition.get("builtIn") if isinstance(definition, Mapping) else None
            )
            if isinstance(builtin, str) and builtin.startswith("AWS::"):
                return True
    return _calls_aws_function(trait.get("conditions"))


def _calls_aws_function(node: _model.Node) -> bool:
    if isinstance(node, Mapping):
        function = node.get("fn")
        if isinstance(function, str) and function.startswith("aws."):
            return True
        return any(_calls_aws_function(value) for value in node.values())
    if isinstance(node, tuple):
        return any(_calls_aws_function(item) for item in node)
    return False


_SERVICE: Final = _model.ShapeId("aws.api", "service")
_ENDPOINT_BDD: Final = _model.ShapeId("smithy.rules", "endpointBdd")
_REGION: Final = "AWS::Region"
_ACCOUNT_ID: Final = "AWS::Auth::AccountId"
_STATIC_CREDENTIALS: Final = _aws(
    "AsyncStaticCredentialsResolver", "aio.identity.static"
)
_CREDENTIALS_IDENTITY: Final = _aws("AWSCredentialsIdentity", "identity.components")

AWS_RULES_EXTENSION: Final = RulesExtension(
    reference=_aws("AWS_RULES_EXTENSION", "endpoints"),
    functions=frozenset(
        {"aws.partition", "aws.parseArn", "aws.isVirtualHostableS3Bucket"}
    ),
)
"""``smithy_aws_core.endpoints.AWS_RULES_EXTENSION``."""

# Keep in sync with AWS_RULES_EXTENSION in smithy_aws_core.endpoints, and with
# AwsEndpointRulesIntegration.BUILT_IN_FIELDS in the Java generator.
BUILTIN_FIELDS: Final[Mapping[str, BuiltinField]] = {
    "AWS::UseFIPS": BuiltinField(
        "use_fips_endpoint",
        None,
        _aws("resolve_use_fips_endpoint_program", "config.resolvers"),
    ),
    "AWS::UseDualStack": BuiltinField(
        "use_dualstack_endpoint",
        None,
        _aws("resolve_use_dualstack_endpoint_program", "config.resolvers"),
    ),
    # The SDKs and Tools Reference Guide default.
    "AWS::Auth::AccountIdEndpointMode": BuiltinField(
        "account_id_endpoint_mode",
        "preferred",
        _aws("resolve_account_id_endpoint_mode_program", "config.resolvers"),
        _aws("validate_account_id_endpoint_mode", "config.validators"),
    ),
}
"""The config fields AWS configs add for built-ins, besides ``region``."""
