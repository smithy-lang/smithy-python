#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass

import pytest
from smithy_core.aio.interfaces.identity import AsyncIdentityResolver
from smithy_core.exceptions import SmithyIdentityError
from smithy_core.types import TypedProperties
from smithy_http.aio.auth.bearer import AsyncBearerAuthScheme
from smithy_http.aio.identity.token import AsyncStaticTokenResolver
from smithy_http.identity import TokenIdentity, TokenIdentityProperties


@dataclass
class _Config:
    token: str | None = None
    token_identity_resolver: (
        AsyncIdentityResolver[TokenIdentity, TokenIdentityProperties] | None
    ) = None


async def test_auth_scheme_gets_resolver() -> None:
    resolver = AsyncStaticTokenResolver()
    context = TypedProperties({"config": _Config(token_identity_resolver=resolver)})

    assert AsyncBearerAuthScheme().identity_resolver(context=context) is resolver


async def test_auth_scheme_missing_resolver() -> None:
    with pytest.raises(SmithyIdentityError):
        AsyncBearerAuthScheme().identity_resolver(context=TypedProperties())


async def test_resolves_token_end_to_end() -> None:
    config = _Config(token="spam", token_identity_resolver=AsyncStaticTokenResolver())
    context = TypedProperties({"config": config})
    scheme = AsyncBearerAuthScheme()

    identity = await scheme.identity_resolver(context=context).get_identity(
        properties=scheme.identity_properties(context=context)
    )

    assert identity.token == "spam"
