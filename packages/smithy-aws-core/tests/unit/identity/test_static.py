#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import pytest
from smithy_aws_core.identity import AWSCredentialsIdentity, AWSIdentityProperties
from smithy_aws_core.identity.static import (
    AsyncStaticCredentialsResolver,
    StaticCredentialsResolver,
)
from smithy_core.exceptions import SmithyIdentityError


def test_returns_fixed_identity() -> None:
    identity = AWSCredentialsIdentity(
        access_key_id="akid",
        secret_access_key="secret",
    )
    resolver = StaticCredentialsResolver(identity)

    assert resolver.get_identity(properties={}) is identity


def test_reads_request_properties() -> None:
    resolver = StaticCredentialsResolver()

    identity = resolver.get_identity(
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
def test_requires_both_request_keys(
    properties: AWSIdentityProperties,
) -> None:
    with pytest.raises(SmithyIdentityError):
        StaticCredentialsResolver().get_identity(properties=properties)


async def test_async_twin_delegates_to_sync_body() -> None:
    identity = AWSCredentialsIdentity(
        access_key_id="akid",
        secret_access_key="secret",
    )
    resolver = AsyncStaticCredentialsResolver(identity)

    assert await resolver.get_identity(properties={}) is identity
