#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import pytest
from smithy_core.exceptions import SmithyIdentityError
from smithy_http.aio.identity.token import AsyncStaticTokenResolver
from smithy_http.identity import TokenIdentity


async def test_returns_fixed_identity() -> None:
    identity = TokenIdentity(token="spam")
    resolver = AsyncStaticTokenResolver(identity)

    assert await resolver.get_identity(properties={}) is identity


async def test_fixed_identity_wins_over_request_properties() -> None:
    identity = TokenIdentity(token="spam")
    resolver = AsyncStaticTokenResolver(identity)

    assert await resolver.get_identity(properties={"token": "eggs"}) is identity


async def test_reads_request_properties() -> None:
    identity = await AsyncStaticTokenResolver().get_identity(
        properties={"token": "spam"}
    )

    assert identity.token == "spam"


async def test_requires_token() -> None:
    with pytest.raises(SmithyIdentityError):
        await AsyncStaticTokenResolver().get_identity(properties={})
