#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from collections.abc import AsyncIterable, AsyncIterator
from dataclasses import dataclass

import pytest
from smithy_core import URI
from smithy_core.aio.interfaces.identity import AsyncIdentityResolver
from smithy_core.exceptions import SmithyIdentityError
from smithy_core.types import TypedProperties
from smithy_http import Field, Fields
from smithy_http.aio import HTTPRequest
from smithy_http.aio.auth.apikey import (
    APIKeyIdentityProperties,
    APIKeyLocation,
    AsyncAPIKeyAuthScheme,
    AsyncAPIKeySigner,
)
from smithy_http.aio.identity.apikey import AsyncAPIKeyIdentityResolver
from smithy_http.identity import APIKeyIdentity


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


async def test_sign_empty_query() -> None:
    api_key = "spam"
    identity = APIKeyIdentity(api_key=api_key)
    signer = AsyncAPIKeySigner(name="eggs", location=APIKeyLocation.QUERY)

    given = request()
    expected = request(query="eggs=spam")

    actual = await signer.sign(
        request=given,
        identity=identity,
        properties={},
    )

    assert actual == expected


async def test_sign_non_empty_query() -> None:
    api_key = "spam"
    identity = APIKeyIdentity(api_key=api_key)
    signer = AsyncAPIKeySigner(name="eggs", location=APIKeyLocation.QUERY)

    given = request(query="spam=eggs")
    expected = request(query="spam=eggs&eggs=spam")

    actual = await signer.sign(
        request=given,
        identity=identity,
        properties={},
    )

    assert actual == expected


async def test_sign_header() -> None:
    api_key = "spam"
    identity = APIKeyIdentity(api_key=api_key)
    signer = AsyncAPIKeySigner(name="eggs", location=APIKeyLocation.HEADER)

    given = request()
    expected = request(fields=Fields([Field(name="eggs", values=["spam"])]))

    actual = await signer.sign(
        request=given,
        identity=identity,
        properties={},
    )

    assert actual == expected


async def test_sign_header_with_scheme() -> None:
    api_key = "spam"
    identity = APIKeyIdentity(api_key=api_key)
    signer = AsyncAPIKeySigner(
        name="eggs", location=APIKeyLocation.HEADER, scheme="Bearer"
    )

    given = request()
    expected = request(fields=Fields([Field(name="eggs", values=["Bearer spam"])]))

    actual = await signer.sign(
        request=given,
        identity=identity,
        properties={},
    )

    assert actual == expected


@dataclass
class ApiKeyConfig:
    api_key_identity_resolver: (
        AsyncIdentityResolver[APIKeyIdentity, APIKeyIdentityProperties] | None
    ) = None


async def test_auth_scheme_gets_resolver() -> None:
    scheme = AsyncAPIKeyAuthScheme(name="eggs", location=APIKeyLocation.QUERY)
    resolver = AsyncAPIKeyIdentityResolver()
    config = ApiKeyConfig(api_key_identity_resolver=resolver)
    properties = TypedProperties({"config": config})

    assert resolver == scheme.identity_resolver(context=properties)


async def test_auth_scheme_missing_resolver() -> None:
    scheme = AsyncAPIKeyAuthScheme(name="eggs", location=APIKeyLocation.QUERY)
    with pytest.raises(SmithyIdentityError):
        scheme.identity_resolver(context=TypedProperties())
