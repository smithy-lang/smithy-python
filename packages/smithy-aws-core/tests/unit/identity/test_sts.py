#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pyright: reportPrivateUsage=false
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest
from smithy_aws_core._private.nested_clients.aws_sdk_sts.models import (
    AssumedRoleUser,
    AssumeRoleOutput,
    Credentials,
)
from smithy_aws_core.identity.environment import EnvironmentCredentialsResolver
from smithy_aws_core.identity.sts import (
    AssumeRoleCredentialsResolver,
    _account_id_from_arn,
)
from smithy_core.exceptions import SmithyIdentityError
from smithy_http.testing import MockHTTPClient

ROLE_ARN = "arn:aws:iam::123456789012:role/MyRole"
ASSUMED_ROLE_ARN = "arn:aws:sts::123456789012:assumed-role/MyRole/session"
MFA_SERIAL = "arn:aws:iam::123456789012:mfa/device"
ACCESS_KEY_ID = "test-access-key"
SECRET_ACCESS_KEY = "test-secret-key"
SESSION_TOKEN = "test-session-token"


def _future_expiry() -> datetime:
    return datetime.now(UTC) + timedelta(hours=1)


def _past_expiry() -> datetime:
    return datetime.now(UTC) - timedelta(hours=1)


def _valid_output(
    *, access_key_id: str = ACCESS_KEY_ID, expiration: datetime | None = None
) -> AssumeRoleOutput:
    """An AssumeRole response with valid credentials and assumed-role user"""
    return AssumeRoleOutput(
        credentials=Credentials(
            access_key_id=access_key_id,
            secret_access_key=SECRET_ACCESS_KEY,
            session_token=SESSION_TOKEN,
            expiration=expiration or _future_expiry(),
        ),
        assumed_role_user=AssumedRoleUser(assumed_role_id="id", arn=ASSUMED_ROLE_ARN),
    )


def _mock_sts_client(
    resolver: AssumeRoleCredentialsResolver, *responses: AssumeRoleOutput
) -> AsyncMock:
    """Attach a mock STS client returning one response per AssumeRole call"""
    client = AsyncMock()
    client.assume_role.side_effect = list(responses)
    resolver._sts_client = client
    return client


def _assume_role_response_body() -> bytes:
    return (
        "<AssumeRoleResponse><AssumeRoleResult>"
        "<Credentials>"
        "<AccessKeyId>sts-akid</AccessKeyId>"
        "<SecretAccessKey>sts-secret</SecretAccessKey>"
        "<SessionToken>sts-token</SessionToken>"
        "<Expiration>2030-01-01T00:00:00Z</Expiration>"
        "</Credentials>"
        "<AssumedRoleUser>"
        "<AssumedRoleId>id:session</AssumedRoleId>"
        f"<Arn>{ASSUMED_ROLE_ARN}</Arn>"
        "</AssumedRoleUser>"
        "</AssumeRoleResult></AssumeRoleResponse>"
    ).encode()


@pytest.mark.parametrize(
    "arn,expected",
    [
        (ASSUMED_ROLE_ARN, "123456789012"),
        ("arn:aws:sts:::assumed-role/MyRole/session", None),  # empty account field
        ("not-an-arn", None),  # too few segments
        (None, None),
    ],
)
def test_account_id_from_arn(arn: str | None, expected: str | None):
    assert _account_id_from_arn(arn) == expected


async def test_resolves_identity_from_assume_role():
    expiration = _future_expiry()
    resolver = AssumeRoleCredentialsResolver(
        source_resolver=AsyncMock(), role_arn=ROLE_ARN
    )
    _mock_sts_client(resolver, _valid_output(expiration=expiration))

    identity = await resolver.get_identity(properties={})

    assert identity.access_key_id == ACCESS_KEY_ID
    assert identity.secret_access_key == SECRET_ACCESS_KEY
    assert identity.session_token == SESSION_TOKEN
    assert identity.expiration == expiration
    assert identity.account_id == "123456789012"


async def test_assume_role_signed_with_source_credentials(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "source-akid")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "source-secret")

    http_client = MockHTTPClient()
    http_client.add_response(body=_assume_role_response_body())

    resolver = AssumeRoleCredentialsResolver(
        source_resolver=EnvironmentCredentialsResolver(),
        role_arn=ROLE_ARN,
        region="us-east-1",
        http_client=http_client,
    )

    identity = await resolver.get_identity(properties={})

    # The resolved identity is the STS-issued credential
    assert identity.access_key_id == "sts-akid"
    assert identity.session_token == "sts-token"

    # The request was signed with the source credentials
    [request] = http_client.captured_requests
    authorization = request.fields["Authorization"].as_string()
    assert "Credential=source-akid/" in authorization


async def test_missing_credentials_raises():
    resolver = AssumeRoleCredentialsResolver(
        source_resolver=AsyncMock(), role_arn=ROLE_ARN
    )
    _mock_sts_client(resolver, AssumeRoleOutput(credentials=None))

    with pytest.raises(
        SmithyIdentityError, match="STS AssumeRole response missing Credentials"
    ):
        await resolver.get_identity(properties={})


async def test_valid_credentials_reused():
    resolver = AssumeRoleCredentialsResolver(
        source_resolver=AsyncMock(), role_arn=ROLE_ARN
    )
    sts_client = _mock_sts_client(
        resolver,
        _valid_output(access_key_id="test-access-key-1"),
        _valid_output(access_key_id="test-access-key-2"),
    )

    identity_one = await resolver.get_identity(properties={})
    identity_two = await resolver.get_identity(properties={})

    # The cached identity is returned without a second STS call
    assert identity_one is identity_two
    assert sts_client.assume_role.call_count == 1


async def test_expired_credentials_refreshed():
    resolver = AssumeRoleCredentialsResolver(
        source_resolver=AsyncMock(), role_arn=ROLE_ARN
    )
    sts_client = _mock_sts_client(
        resolver,
        _valid_output(access_key_id="test-access-key-1", expiration=_past_expiry()),
        _valid_output(access_key_id="test-access-key-2"),
    )

    identity_one = await resolver.get_identity(properties={})
    identity_two = await resolver.get_identity(properties={})

    # The cached identity is refreshed with a second STS call
    assert identity_one is not identity_two
    assert identity_one.access_key_id == "test-access-key-1"
    assert identity_two.access_key_id == "test-access-key-2"
    assert sts_client.assume_role.call_count == 2


async def test_assume_role_request_uses_settings():
    resolver = AssumeRoleCredentialsResolver(
        source_resolver=AsyncMock(),
        role_arn=ROLE_ARN,
        role_session_name="test-session-name",
        external_id="test-external-id",
        duration_seconds=1000,
    )
    sts_client = _mock_sts_client(resolver, _valid_output())

    await resolver.get_identity(properties={})

    request = sts_client.assume_role.call_args.args[0]
    assert request.role_arn == ROLE_ARN
    assert request.role_session_name == "test-session-name"
    assert request.external_id == "test-external-id"
    assert request.duration_seconds == 1000


async def test_role_session_name_generated_when_unset():
    resolver = AssumeRoleCredentialsResolver(
        source_resolver=AsyncMock(), role_arn=ROLE_ARN
    )
    sts_client = _mock_sts_client(resolver, _valid_output())

    await resolver.get_identity(properties={})

    request = sts_client.assume_role.call_args.args[0]
    assert request.role_session_name.startswith("aws-sdk-python-")


async def test_role_session_name_stable_across_refreshes():
    resolver = AssumeRoleCredentialsResolver(
        source_resolver=AsyncMock(), role_arn=ROLE_ARN
    )
    sts_client = _mock_sts_client(
        resolver,
        _valid_output(expiration=_past_expiry()),
        _valid_output(),
    )

    await resolver.get_identity(properties={})
    await resolver.get_identity(properties={})

    first, second = sts_client.assume_role.call_args_list
    assert first.args[0].role_session_name == second.args[0].role_session_name


async def test_mfa_serial_and_token_code_sent():
    code_provider = AsyncMock(return_value="111111")
    resolver = AssumeRoleCredentialsResolver(
        source_resolver=AsyncMock(),
        role_arn=ROLE_ARN,
        mfa_serial=MFA_SERIAL,
        mfa_code_provider=code_provider,
    )
    sts_client = _mock_sts_client(resolver, _valid_output())

    await resolver.get_identity(properties={})

    request = sts_client.assume_role.call_args.args[0]
    assert request.serial_number == MFA_SERIAL
    assert request.token_code == "111111"
    code_provider.assert_awaited_once_with(MFA_SERIAL)


async def test_mfa_code_provider_invoked_on_each_refresh():
    code_provider = AsyncMock(side_effect=["111111", "222222"])
    resolver = AssumeRoleCredentialsResolver(
        source_resolver=AsyncMock(),
        role_arn=ROLE_ARN,
        mfa_serial=MFA_SERIAL,
        mfa_code_provider=code_provider,
    )
    sts_client = _mock_sts_client(
        resolver,
        _valid_output(expiration=_past_expiry()),
        _valid_output(),
    )

    await resolver.get_identity(properties={})
    await resolver.get_identity(properties={})

    # A fresh, single-use code is fetched for each assume call
    assert code_provider.await_count == 2
    first, second = sts_client.assume_role.call_args_list
    assert first.args[0].token_code == "111111"
    assert second.args[0].token_code == "222222"


def test_mfa_serial_without_provider_raises():
    with pytest.raises(
        ValueError,
        match="mfa_code_provider is required when mfa_serial is set",
    ):
        AssumeRoleCredentialsResolver(
            source_resolver=AsyncMock(),
            role_arn=ROLE_ARN,
            mfa_serial=MFA_SERIAL,
        )
