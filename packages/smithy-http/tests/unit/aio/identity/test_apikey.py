#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import pytest
from smithy_core.exceptions import SmithyIdentityError
from smithy_http.aio.identity.apikey import APIKeyIdentityResolver


async def test_identity_resolver() -> None:
    api_key = "spam"
    resolver = APIKeyIdentityResolver()
    identity = await resolver.get_identity(properties={"api_key": api_key})

    assert identity.api_key == api_key


async def test_missing_api_key() -> None:
    resolver = APIKeyIdentityResolver()

    with pytest.raises(SmithyIdentityError):
        await resolver.get_identity(properties={})
