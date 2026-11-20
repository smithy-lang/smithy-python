# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""SigV4 auth and the default AWS credentials chain."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import TYPE_CHECKING, Final

from .. import exceptions as _exceptions
from .. import model as _model
from .. import models as _models
from .._auth import AuthContribution
from ..dependencies import SMITHY_HTTP
from ..integrations import ClientIntegration, ClientMode
from ..symbols import TypeReference
from ._dependencies import SMITHY_AWS_CORE

if TYPE_CHECKING:
    from ..clients import ClientPlan
    from ..integrations import Part
    from ..writer import PythonWriter

__all__ = ["SIGV4", "AwsSigV4Integration"]


class AwsSigV4Integration(ClientIntegration):
    """SigV4 auth for AWS services with the ``aws.auth#sigv4`` trait.

    Configs default ``auth_schemes`` to the SigV4 scheme for the trait's signing
    name. The credential fields come from ``AwsConfig``. A client whose config has
    no credentials resolver sets the default AWS credentials chain in
    ``_post_setup``, built from the config's profile and region.
    """

    def matches(self, service: _model.ServiceShape) -> bool:
        return service.has_trait(_SERVICE) and service.has_trait(SIGV4.scheme_id)

    def auth_schemes(
        self, service: _model.ServiceShape
    ) -> Mapping[_model.ShapeId, AuthContribution]:
        del service
        return {SIGV4.scheme_id: SIGV4}

    def write_client_methods(
        self,
        writer: PythonWriter,
        plan: ClientPlan,
        mode: ClientMode,
        config: TypeReference,
    ) -> None:
        del plan
        sync = not mode.is_async
        wait = "" if sync else "await "
        chain = (
            _aws("IdentityChain", "identity.chain.resolver")
            if sync
            else _aws("AsyncIdentityChain", "aio.identity.chain")
        )
        http_client = (
            _http("HTTPClient", "interfaces")
            if sync
            else _http("AsyncHTTPClient", "aio.interfaces")
        )
        writer.line()
        writer.line(
            "def " if sync else "async def ",
            "_post_setup(self, config: ",
            config,
            ") -> None:",
        )
        with writer.indent():
            writer.line("if config.aws_credentials_identity_resolver is None:")
            with writer.indent():
                writer.line("config_context = config.resolution_context()")
                writer.line("config_file = None")
                writer.line("profile_name = None")
                writer.line("if config_context is not None:")
                with writer.indent():
                    writer.line(
                        "config_file = ", wait, "config_context.parsed_profiles()"
                    )
                    writer.line(
                        "if config_context.profile_source is ",
                        _CONFIG_SOURCE,
                        ".OVERRIDE:",
                    )
                    with writer.indent():
                        writer.line("profile_name = config_context.profile_name")
                writer.line(
                    "config.aws_credentials_identity_resolver = ",
                    wait,
                    chain,
                    ".create(",
                )
                with writer.indent():
                    writer.line(_CREDENTIALS_IDENTITY, ",")
                    writer.line("config_file=config_file,")
                    writer.line("profile_name=profile_name,")
                    writer.line("region_override=config.region,")
                    writer.line(
                        "http_client=",
                        _CAST,
                        "(",
                        http_client,
                        " | None, config.transport),",
                    )
                writer.line(")")


def _aws(name: str, module: str) -> TypeReference:
    return TypeReference(
        name, f"smithy_aws_core.{module}", dependencies=(SMITHY_AWS_CORE,)
    )


def _http(name: str, module: str) -> TypeReference:
    return TypeReference(name, f"smithy_http.{module}", dependencies=(SMITHY_HTTP,))


def _signing_name(trait: _model.Node) -> str:
    name = trait.get("name") if isinstance(trait, Mapping) else None
    if not isinstance(name, str) or not name:
        raise _exceptions.CodegenError("Invalid aws.auth#sigv4 trait: needs a name")
    return name


def _scheme(reference: TypeReference) -> Callable[[_model.Node], tuple[Part, ...]]:
    def build(trait: _model.Node) -> tuple[Part, ...]:
        quoted = _models._quote(_signing_name(trait))  # pyright: ignore[reportPrivateUsage]
        return (reference, f"(service={quoted})")

    return build


_SERVICE: Final = _model.ShapeId("aws.api", "service")
_CAST: Final = TypeReference("cast", "typing")
_CONFIG_SOURCE: Final = _aws("ConfigSource", "config.types")
_CREDENTIALS_IDENTITY: Final = _aws("AWSCredentialsIdentity", "identity.components")

SIGV4: Final = AuthContribution(
    scheme_id=_model.ShapeId("aws.auth", "sigv4"),
    scheme=_scheme(_aws("SigV4AuthScheme", "auth.sigv4")),
    async_scheme=_scheme(_aws("AsyncSigV4AuthScheme", "aio.auth.sigv4")),
    # AwsConfig declares the credential fields and the credentials resolver.
    fields=(),
)
"""SigV4 auth, from the ``aws.auth#sigv4`` trait."""
