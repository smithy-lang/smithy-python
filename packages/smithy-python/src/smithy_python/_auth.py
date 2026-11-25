# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Auth scheme contributions to generated clients, keyed by auth trait ID.

A contribution names the runtime auth schemes a client's configs default to, how
each is built from the service's auth trait, and the config fields its identity
resolver reads.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final

from . import dependencies as _dependencies
from . import exceptions as _exceptions
from . import model as _model
from . import models as _models
from .symbols import TypeReference

type Part = str | TypeReference
"""A piece of a generated line."""


@dataclass(frozen=True, slots=True)
class ConfigField:
    """A config field an auth scheme reads, in its sync and async forms."""

    name: str
    annotation: tuple[Part, ...]
    async_annotation: tuple[Part, ...]
    documentation: str
    default: tuple[Part, ...] = ()
    """The value the field defaults to when unset, or nothing for None."""

    async_default: tuple[Part, ...] = ()


@dataclass(frozen=True, slots=True)
class AuthContribution:
    """The runtime parts a generated client uses for one modeled auth scheme."""

    scheme_id: _model.ShapeId
    scheme: Callable[[_model.Node], tuple[Part, ...]]
    """The sync auth scheme built from the service's auth trait value."""

    async_scheme: Callable[[_model.Node], tuple[Part, ...]]
    fields: tuple[ConfigField, ...]


def supported_schemes(
    service: _model.ServiceShape,
    contributions: Mapping[_model.ShapeId, AuthContribution] | None = None,
) -> tuple[AuthContribution, ...]:
    """The contributions for the auth traits on a service, in shape ID order."""
    contributions = DEFAULT_AUTH_SCHEMES if contributions is None else contributions
    return tuple(
        contributions[trait_id]
        for trait_id in sorted(service.traits, key=str)
        if trait_id in contributions
    )


def _http(name: str, module: str) -> TypeReference:
    return TypeReference(
        name, f"smithy_http.{module}", dependencies=(_dependencies.SMITHY_HTTP,)
    )


def _core(name: str, module: str) -> TypeReference:
    return TypeReference(
        name, f"smithy_core.{module}", dependencies=(_dependencies.SMITHY_CORE,)
    )


def _api_key_arguments(trait: _model.Node) -> tuple[Part, ...]:
    if not isinstance(trait, Mapping):
        raise _exceptions.CodegenError("Invalid httpApiKeyAuth trait")
    name = trait.get("name")
    location = trait.get("in")
    scheme = trait.get("scheme")
    if not isinstance(name, str) or location not in ("header", "query"):
        raise _exceptions.CodegenError(
            "Invalid httpApiKeyAuth trait: needs a name and an in of header or query"
        )
    if scheme is not None and not isinstance(scheme, str):
        raise _exceptions.CodegenError("Invalid httpApiKeyAuth trait: bad scheme")
    arguments: tuple[Part, ...] = (
        "(name=",
        _quote(name),
        ", location=",
        _API_KEY_LOCATION,
        ".",
        location.upper(),
    )
    if scheme is not None:
        arguments += (", scheme=", _quote(scheme))
    return (*arguments, ")")


def _quote(value: str) -> str:
    return _models._quote(value)  # pyright: ignore[reportPrivateUsage]


_API_KEY_LOCATION: Final = _core("APIKeyLocation", "traits")
_API_KEY_IDENTITY: Final = _http("APIKeyIdentity", "identity")
_API_KEY_IDENTITY_PROPERTIES: Final = _http("APIKeyIdentityProperties", "identity")
_API_KEY_ARGUMENTS: Final = (
    "[",
    _API_KEY_IDENTITY,
    ", ",
    _API_KEY_IDENTITY_PROPERTIES,
    "]",
)

HTTP_API_KEY_AUTH: Final = AuthContribution(
    scheme_id=_model.ShapeId("smithy.api", "httpApiKeyAuth"),
    scheme=lambda trait: (
        _http("APIKeyAuthScheme", "auth.apikey"),
        *_api_key_arguments(trait),
    ),
    async_scheme=lambda trait: (
        _http("AsyncAPIKeyAuthScheme", "aio.auth.apikey"),
        *_api_key_arguments(trait),
    ),
    fields=(
        ConfigField(
            name="api_key",
            annotation=("str | None",),
            async_annotation=("str | None",),
            documentation="The API key to send along with requests.",
        ),
        ConfigField(
            name="api_key_identity_resolver",
            annotation=(
                _core("IdentityResolver", "interfaces.identity"),
                *_API_KEY_ARGUMENTS,
                " | None",
            ),
            async_annotation=(
                _core("AsyncIdentityResolver", "aio.interfaces.identity"),
                *_API_KEY_ARGUMENTS,
                " | None",
            ),
            documentation="Resolves the API key.",
            default=(_http("APIKeyIdentityResolver", "identity.apikey"), "()"),
            async_default=(
                _http("AsyncAPIKeyIdentityResolver", "aio.identity.apikey"),
                "()",
            ),
        ),
    ),
)
"""API key auth, from the ``smithy.api#httpApiKeyAuth`` trait."""

_TOKEN_IDENTITY: Final = _http("TokenIdentity", "identity")
_TOKEN_IDENTITY_PROPERTIES: Final = _http("TokenIdentityProperties", "identity")
_TOKEN_ARGUMENTS: Final = (
    "[",
    _TOKEN_IDENTITY,
    ", ",
    _TOKEN_IDENTITY_PROPERTIES,
    "]",
)

TOKEN_IDENTITY_RESOLVER: Final = ConfigField(
    name="token_identity_resolver",
    annotation=(
        _core("IdentityResolver", "interfaces.identity"),
        *_TOKEN_ARGUMENTS,
        " | None",
    ),
    async_annotation=(
        _core("AsyncIdentityResolver", "aio.interfaces.identity"),
        *_TOKEN_ARGUMENTS,
        " | None",
    ),
    documentation="Resolves the bearer token.",
    default=(_http("StaticTokenResolver", "identity.token"), "()"),
    async_default=(_http("AsyncStaticTokenResolver", "aio.identity.token"), "()"),
)
"""The bearer token resolver field, defaulting to the static resolver."""

HTTP_BEARER_AUTH: Final = AuthContribution(
    scheme_id=_model.ShapeId("smithy.api", "httpBearerAuth"),
    # The trait has no parameters, so the scheme takes none.
    scheme=lambda trait: (_http("BearerAuthScheme", "auth.bearer"), "()"),
    async_scheme=lambda trait: (
        _http("AsyncBearerAuthScheme", "aio.auth.bearer"),
        "()",
    ),
    fields=(
        ConfigField(
            name="token",
            annotation=("str | None",),
            async_annotation=("str | None",),
            documentation="The bearer token to send along with requests.",
        ),
        TOKEN_IDENTITY_RESOLVER,
    ),
)
"""Bearer token auth, from the ``smithy.api#httpBearerAuth`` trait."""

DEFAULT_AUTH_SCHEMES: Final[Mapping[_model.ShapeId, AuthContribution]] = (
    MappingProxyType(
        {
            HTTP_API_KEY_AUTH.scheme_id: HTTP_API_KEY_AUTH,
            HTTP_BEARER_AUTH.scheme_id: HTTP_BEARER_AUTH,
        }
    )
)
"""The auth schemes generated clients support, by auth trait ID."""
