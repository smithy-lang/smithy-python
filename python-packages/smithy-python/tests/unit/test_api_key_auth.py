from dataclasses import dataclass
from typing import AsyncIterable, AsyncIterator

import pytest

from smithy_python._private import URI, Field, Fields
from smithy_python._private.api_key_auth import (
    ApiKeyAuthScheme,
    ApiKeyIdentity,
    ApiKeyIdentityResolver,
    ApiKeyLocation,
    ApiKeySigner,
    ApiKeySigningProperties,
)
from smithy_python._private.http import HTTPRequest
from smithy_python.exceptions import SmithyIdentityException
from smithy_python.interfaces.identity import IdentityProperties, IdentityResolver


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


async def test_identity_resolver() -> None:
    api_key = "spam"
    resolver = ApiKeyIdentityResolver(api_key=api_key)
    identity = await resolver.get_identity(identity_properties={})

    assert identity.api_key == api_key

    resolver = ApiKeyIdentityResolver(api_key=ApiKeyIdentity(api_key=api_key))
    identity = await resolver.get_identity(identity_properties={})

    assert identity.api_key == api_key


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
    api_key_identity_resolver: IdentityResolver[
        ApiKeyIdentity, IdentityProperties
    ] | None = None


async def test_auth_scheme_gets_resolver() -> None:
    scheme = ApiKeyAuthScheme()
    resolver = ApiKeyIdentityResolver(api_key="spam")
    config = ApiKeyConfig(api_key_identity_resolver=resolver)

    assert resolver == scheme.identity_resolver(config=config)


async def test_auth_scheme_missing_resolver() -> None:
    scheme = ApiKeyAuthScheme()
    with pytest.raises(SmithyIdentityException):
        scheme.identity_resolver(config=ApiKeyConfig())
