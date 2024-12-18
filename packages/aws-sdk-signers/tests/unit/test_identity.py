from datetime import UTC, datetime, timedelta

import pytest
from aws_sdk_signers import AWSCredentialIdentity


@pytest.mark.parametrize(
    "access_key_id,secret_access_key,session_token,expiration",
    [
        (
            "AKID1234EXAMPLE",
            "SECRET1234",
            None,
            None,
        ),
        (
            "AKID1234EXAMPLE",
            "SECRET1234",
            "SESS_TOKEN_1234",
            None,
        ),
        (
            "AKID1234EXAMPLE",
            "SECRET1234",
            None,
            datetime(2024, 5, 1, 0, 0, 0, tzinfo=UTC),
        ),
        (
            "AKID1234EXAMPLE",
            "SECRET1234",
            "SESS_TOKEN_1234",
            datetime(2024, 5, 1, 0, 0, 0, tzinfo=UTC),
        ),
    ],
)
def test_aws_credential_identity(
    access_key_id: str,
    secret_access_key: str,
    session_token: str | None,
    expiration: datetime | None,
) -> None:
    creds = AWSCredentialIdentity(
        access_key_id=access_key_id,
        secret_access_key=secret_access_key,
        session_token=session_token,
        expiration=expiration,
    )
    assert creds.access_key_id == access_key_id
    assert creds.secret_access_key == secret_access_key
    assert creds.session_token == session_token
    assert creds.expiration == expiration


@pytest.mark.parametrize(
    "access_key_id,secret_access_key,session_token,expiration,is_expired",
    [
        (
            "AKID1234EXAMPLE",
            "SECRET1234",
            "SESS_TOKEN_1234",
            None,
            False,
        ),
        (
            "AKID1234EXAMPLE",
            "SECRET1234",
            None,
            datetime(2024, 5, 1, 0, 0, 0, tzinfo=UTC),
            True,
        ),
        (
            "AKID1234EXAMPLE",
            "SECRET1234",
            "SESS_TOKEN_1234",
            datetime.now(UTC) + timedelta(hours=1),
            False,
        ),
    ],
)
def test_aws_credential_identity_expired(
    access_key_id: str,
    secret_access_key: str,
    session_token: str | None,
    expiration: datetime | None,
    is_expired: bool,
) -> None:
    creds = AWSCredentialIdentity(
        access_key_id=access_key_id,
        secret_access_key=secret_access_key,
        session_token=session_token,
        expiration=expiration,
    )
    assert creds.is_expired is is_expired
