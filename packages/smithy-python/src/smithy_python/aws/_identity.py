# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""SigV4 and bearer token auth, with the default AWS identity chains."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import replace
from typing import TYPE_CHECKING, Final

from .. import exceptions as _exceptions
from .. import model as _model
from .. import models as _models
from .._auth import HTTP_BEARER_AUTH as _CORE_BEARER_AUTH
from .._auth import TOKEN_IDENTITY_RESOLVER, AuthContribution
from ..dependencies import SMITHY_HTTP
from ..integrations import ClientIntegration, ClientMode
from ..symbols import TypeReference
from ._dependencies import SMITHY_AWS_CORE

if TYPE_CHECKING:
    from ..clients import ClientPlan
    from ..integrations import Part
    from ..writer import PythonWriter

__all__ = ["AWS_HTTP_BEARER_AUTH", "SIGV4", "AwsIdentityIntegration"]


class AwsIdentityIntegration(ClientIntegration):
    """Identity resolution for AWS services with ``aws.auth#sigv4`` or
    ``smithy.api#httpBearerAuth``.

    Configs default ``auth_schemes`` to the SigV4 scheme for the trait's signing
    name, the bearer scheme, or both. The credential fields come from
    ``AwsConfig``; the bearer fields are ``token`` and ``token_identity_resolver``.
    A client's ``_post_setup`` fills each identity resolver the config leaves
    unset: the default AWS credentials chain, and for bearer auth the static
    token resolver when the config has a ``token`` or else the default AWS token
    provider chain. Both chains read the config's profile, region, and transport.
    """

    def matches(self, service: _model.ServiceShape) -> bool:
        return service.has_trait(_SERVICE) and any(
            service.has_trait(scheme.scheme_id) for scheme in _SCHEMES
        )

    def auth_schemes(
        self, service: _model.ServiceShape
    ) -> Mapping[_model.ShapeId, AuthContribution]:
        del service
        return {scheme.scheme_id: scheme for scheme in _SCHEMES}

    def write_client_methods(
        self,
        writer: PythonWriter,
        plan: ClientPlan,
        mode: ClientMode,
        config: TypeReference,
    ) -> None:
        service = plan.selection.service
        assert service is not None  # noqa: S101 - ClientPlan requires a service
        sync = not mode.is_async
        define = "def " if sync else "async def "
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
        static_token = (
            _http("StaticTokenResolver", "identity.token")
            if sync
            else _http("AsyncStaticTokenResolver", "aio.identity.token")
        )

        def write_chain(resolver: str, identity: TypeReference) -> None:
            writer.line(
                "config_file, profile_name = ",
                wait,
                "self._profile_overrides(config)",
            )
            writer.line("config.", resolver, " = ", wait, chain, ".create(")
            with writer.indent():
                writer.line(identity, ",")
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

        writer.line()
        writer.line(define, "_post_setup(self, config: ", config, ") -> None:")
        with writer.indent():
            if service.has_trait(SIGV4.scheme_id):
                writer.line("if config.aws_credentials_identity_resolver is None:")
                with writer.indent():
                    write_chain(
                        "aws_credentials_identity_resolver", _CREDENTIALS_IDENTITY
                    )
            if service.has_trait(AWS_HTTP_BEARER_AUTH.scheme_id):
                if service.has_trait(SIGV4.scheme_id):
                    writer.line()
                # A configured token gets the static resolver, which reads it from
                # the identity properties the bearer scheme supplies. Otherwise the
                # default token provider chain is consulted, as every AWS SDK does.
                writer.line("if config.token_identity_resolver is None:")
                with writer.indent():
                    writer.line("if config.token is not None:")
                    with writer.indent():
                        writer.line(
                            "config.token_identity_resolver = ", static_token, "()"
                        )
                    writer.line("else:")
                    with writer.indent():
                        write_chain("token_identity_resolver", _TOKEN_IDENTITY)
        # Shared by every identity chain the client builds: the parsed config
        # file and the explicit profile override, if any.
        writer.line()
        writer.line(define, "_profile_overrides(")
        with writer.indent():
            writer.line("self, config: ", config)
        writer.line(") -> tuple[", _MERGED_CONFIG, " | None, str | None]:")
        with writer.indent():
            writer.line("config_context = config.resolution_context()")
            writer.line("config_file = None")
            writer.line("profile_name = None")
            writer.line("if config_context is not None:")
            with writer.indent():
                writer.line("config_file = ", wait, "config_context.parsed_profiles()")
                writer.line(
                    "if config_context.profile_source is ", _CONFIG_SOURCE, ".OVERRIDE:"
                )
                with writer.indent():
                    writer.line("profile_name = config_context.profile_name")
            writer.line("return config_file, profile_name")


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
_MERGED_CONFIG: Final = _aws("MergedConfig", "config.merged_config")
_CREDENTIALS_IDENTITY: Final = _aws("AWSCredentialsIdentity", "identity.components")
_TOKEN_IDENTITY: Final = _http("TokenIdentity", "identity")

SIGV4: Final = AuthContribution(
    scheme_id=_model.ShapeId("aws.auth", "sigv4"),
    scheme=_scheme(_aws("SigV4AuthScheme", "auth.sigv4")),
    async_scheme=_scheme(_aws("AsyncSigV4AuthScheme", "aio.auth.sigv4")),
    # AwsConfig declares the credential fields and the credentials resolver.
    fields=(),
)
"""SigV4 auth, from the ``aws.auth#sigv4`` trait."""

AWS_HTTP_BEARER_AUTH: Final = replace(
    _CORE_BEARER_AUTH,
    # The resolver defaults to None so _post_setup can choose between the static
    # resolver and the token provider chain.
    fields=tuple(
        replace(field, default=(), async_default=())
        if field.name == TOKEN_IDENTITY_RESOLVER.name
        else field
        for field in _CORE_BEARER_AUTH.fields
    ),
)
"""Bearer token auth for AWS services, which fall back to the token chain."""

_SCHEMES: Final = (SIGV4, AWS_HTTP_BEARER_AUTH)
