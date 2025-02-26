#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from collections.abc import AsyncIterable, AsyncIterator
from dataclasses import dataclass

import pytest
from smithy_core import URI
from smithy_core.aio.interfaces.identity import IdentityResolver
from smithy_core.exceptions import SmithyIdentityException
from smithy_core.interfaces.identity import IdentityProperties

from smithy_http import Field, Fields
from smithy_http.aio import HTTPRequest
from smithy_http.aio.auth.apikey import (
    ApiKeyAuthScheme,
    ApiKeyLocation,
    ApiKeySigner,
    ApiKeySigningProperties,
)
from smithy_http.aio.identity.apikey import ApiKeyIdentity, ApiKeyIdentityResolver


@pytest.fixture
def signer() -> ApiKeySigner:
    return ApiKeySigner()


class _FakeBody(AsyncIterable[bytes]):
    def __aiter__(self) -> AsyncIterator[bytes]:
        return self

    async def __anext__(self) -> bytes:
        return b"spam"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, _FakeBody)


def request(query: str | None = None, fields: Fields | None = None) -> HTTPRequest:
    return HTTPRequest(
        destination=URI(host="example.com", query=query),
        body=_FakeBody(),
        method="POST",
        fields=fields or Fields(),
    )


async def test_sign_empty_query(signer: ApiKeySigner) -> None:
    api_key = "spam"
    identity = ApiKeyIdentity(api_key=api_key)
    properties: ApiKeySigningProperties = {
        "name": "eggs",
        "location": ApiKeyLocation.QUERY,
    }

    given = request()
    expected = request(query="eggs=spam")

    actual = await signer.sign(
        http_request=given,
        identity=identity,
        signing_properties=properties,
    )

    assert actual == expected


async def test_sign_non_empty_query(signer: ApiKeySigner) -> None:
    api_key = "spam"
    identity = ApiKeyIdentity(api_key=api_key)
    properties: ApiKeySigningProperties = {
        "name": "eggs",
        "location": ApiKeyLocation.QUERY,
    }

    given = request(query="spam=eggs")
    expected = request(query="spam=eggs&eggs=spam")

    actual = await signer.sign(
        http_request=given,
        identity=identity,
        signing_properties=properties,
    )

    assert actual == expected


async def test_sign_header(signer: ApiKeySigner) -> None:
    api_key = "spam"
    identity = ApiKeyIdentity(api_key=api_key)
    properties: ApiKeySigningProperties = {
        "name": "eggs",
        "location": ApiKeyLocation.HEADER,
    }

    given = request()
    expected = request(fields=Fields([Field(name="eggs", values=["spam"])]))

    actual = await signer.sign(
        http_request=given,
        identity=identity,
        signing_properties=properties,
    )

    assert actual == expected


async def test_sign_header_with_scheme(signer: ApiKeySigner) -> None:
    api_key = "spam"
    identity = ApiKeyIdentity(api_key=api_key)
    properties: ApiKeySigningProperties = {
        "name": "eggs",
        "location": ApiKeyLocation.HEADER,
        "scheme": "Bearer",
    }

    given = request()
    expected = request(fields=Fields([Field(name="eggs", values=["Bearer spam"])]))

    actual = await signer.sign(
        http_request=given,
        identity=identity,
        signing_properties=properties,
    )

    assert actual == expected


@dataclass
class ApiKeyConfig:
    api_key_identity_resolver: (
        IdentityResolver[ApiKeyIdentity, IdentityProperties] | None
    ) = None


async def test_auth_scheme_gets_resolver() -> None:
    scheme = ApiKeyAuthScheme()
    resolver = ApiKeyIdentityResolver(api_key="spam")
    config = ApiKeyConfig(api_key_identity_resolver=resolver)

    assert resolver == scheme.identity_resolver(config=config)


async def test_auth_scheme_missing_resolver() -> None:
    scheme = ApiKeyAuthScheme()
    with pytest.raises(SmithyIdentityException):
        scheme.identity_resolver(config=ApiKeyConfig())
