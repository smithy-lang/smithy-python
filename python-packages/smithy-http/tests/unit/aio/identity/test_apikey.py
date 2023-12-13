#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from smithy_http.aio.identity.apikey import ApiKeyIdentity, ApiKeyIdentityResolver


async def test_identity_resolver() -> None:
    api_key = "spam"
    resolver = ApiKeyIdentityResolver(api_key=api_key)
    identity = await resolver.get_identity(identity_properties={})

    assert identity.api_key == api_key

    resolver = ApiKeyIdentityResolver(api_key=ApiKeyIdentity(api_key=api_key))
    identity = await resolver.get_identity(identity_properties={})

    assert identity.api_key == api_key
