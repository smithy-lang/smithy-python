#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass

import pytest
from smithy_core import URI
from smithy_core.exceptions import SmithyIdentityError
from smithy_core.interfaces.identity import IdentityResolver
from smithy_core.traits import HTTPBearerAuthTrait
from smithy_core.types import TypedProperties
from smithy_http import Field, Fields, HTTPRequest
from smithy_http.auth.bearer import BearerAuthScheme, BearerSigner
from smithy_http.exceptions import SmithyHTTPError
from smithy_http.identity import TokenIdentity, TokenIdentityProperties
from smithy_http.identity.token import StaticTokenResolver

DESTINATION = URI(
    scheme="https",
    username="user",
    password="secret",
    host="example.com",
    port=8443,
    path="/resource",
    query="spam=eggs",
    fragment="frag",
)


def _request(
    destination: URI = DESTINATION, fields: Fields | None = None
) -> HTTPRequest:
    return HTTPRequest(
        destination=destination, body=b"", method="GET", fields=fields or Fields()
    )


# Signing cases from the token-providers SEP.
@pytest.mark.parametrize(
    "token, fields",
    [
        ("mF_9.B5f-4.1JqM", None),
        ("eW91J3JlIG5vdCBzdXBwb3NlZCB0byBkZWNvZGUgdGhpcyE=", None),
        (
            "mF_9.B5f-4.1JqM",
            Fields([Field(name="Authorization", values=["Bearer foo"])]),
        ),
    ],
)
def test_sign_sets_authorization_header(token: str, fields: Fields | None) -> None:
    actual = BearerSigner().sign(
        request=_request(fields=fields),
        identity=TokenIdentity(token=token),
        properties={},
    )

    expected = _request(
        fields=Fields([Field(name="Authorization", values=[f"Bearer {token}"])])
    )
    assert actual == expected


def test_sign_preserves_destination_and_other_fields() -> None:
    fields = Fields([Field(name="X-Spam", values=["eggs"])])
    actual = BearerSigner().sign(
        request=_request(fields=fields),
        identity=TokenIdentity(token="token"),
        properties={},
    )

    assert actual.destination == DESTINATION
    assert actual.fields["X-Spam"].values == ["eggs"]
    assert actual.fields["Authorization"].values == ["Bearer token"]


def test_sign_accepts_uppercase_scheme() -> None:
    destination = URI(scheme="HTTPS", host="example.com")
    actual = BearerSigner().sign(
        request=_request(destination),
        identity=TokenIdentity(token="spam"),
        properties={},
    )

    assert actual.fields["Authorization"].values == ["Bearer spam"]


def test_sign_requires_https() -> None:
    with pytest.raises(SmithyHTTPError, match="https"):
        BearerSigner().sign(
            request=_request(URI(scheme="http", host="example.com")),
            identity=TokenIdentity(token="spam"),
            properties={},
        )


@dataclass
class _Config:
    token: str | None = None
    token_identity_resolver: (
        IdentityResolver[TokenIdentity, TokenIdentityProperties] | None
    ) = None


def test_scheme_id() -> None:
    assert BearerAuthScheme().scheme_id == HTTPBearerAuthTrait.id
    assert BearerAuthScheme.from_trait(HTTPBearerAuthTrait()).scheme_id == (
        HTTPBearerAuthTrait.id
    )


def test_identity_properties_from_config() -> None:
    scheme = BearerAuthScheme()
    context = TypedProperties({"config": _Config(token="spam")})

    assert scheme.identity_properties(context=context) == {"token": "spam"}


@pytest.mark.parametrize(
    "context", [TypedProperties(), TypedProperties({"config": _Config()})]
)
def test_identity_properties_without_token(context: TypedProperties) -> None:
    assert BearerAuthScheme().identity_properties(context=context) == {}


def test_identity_resolver_from_config() -> None:
    resolver = StaticTokenResolver()
    context = TypedProperties({"config": _Config(token_identity_resolver=resolver)})

    assert BearerAuthScheme().identity_resolver(context=context) is resolver


def test_identity_resolver_missing() -> None:
    with pytest.raises(SmithyIdentityError):
        BearerAuthScheme().identity_resolver(context=TypedProperties())


def test_signer_properties_empty() -> None:
    assert BearerAuthScheme().signer_properties(context=TypedProperties()) == {}


def test_scheme_signs_end_to_end() -> None:
    config = _Config(token="spam", token_identity_resolver=StaticTokenResolver())
    context = TypedProperties({"config": config})
    scheme = BearerAuthScheme()

    identity = scheme.identity_resolver(context=context).get_identity(
        properties=scheme.identity_properties(context=context)
    )
    signed = scheme.signer().sign(
        request=_request(),
        identity=identity,
        properties=scheme.signer_properties(context=context),
    )

    assert signed.fields["Authorization"].values == ["Bearer spam"]
