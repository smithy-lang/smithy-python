#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import pytest
from smithy_aws_core.identity import AWSCredentialsIdentity, AWSIdentityProperties
from smithy_aws_core.identity.static import StaticCredentialsResolver
from smithy_core.exceptions import SmithyIdentityError


async def test_returns_fixed_identity() -> None:
    identity = AWSCredentialsIdentity(
        access_key_id="akid",
        secret_access_key="secret",
    )
    resolver = StaticCredentialsResolver(identity)

    assert await resolver.get_identity(properties={}) is identity


async def test_reads_request_properties() -> None:
    resolver = StaticCredentialsResolver()

    identity = await resolver.get_identity(
        properties={
            "access_key_id": "akid",
            "secret_access_key": "secret",
            "session_token": "token",
        }
    )

    assert identity.access_key_id == "akid"
    assert identity.secret_access_key == "secret"
    assert identity.session_token == "token"


@pytest.mark.parametrize(
    "properties",
    [
        {},
        {"access_key_id": "akid"},
        {"secret_access_key": "secret"},
    ],
)
async def test_requires_both_request_keys(
    properties: AWSIdentityProperties,
) -> None:
    with pytest.raises(SmithyIdentityError):
        await StaticCredentialsResolver().get_identity(properties=properties)
