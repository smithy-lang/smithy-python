#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from datetime import UTC, datetime, timedelta, timezone

import pytest
from smithy_core.exceptions import SmithyIdentityError
from smithy_http.identity import TokenIdentity
from smithy_http.identity.token import StaticTokenResolver


def test_returns_fixed_identity() -> None:
    identity = TokenIdentity(token="spam")
    resolver = StaticTokenResolver(identity)

    assert resolver.get_identity(properties={}) is identity


def test_fixed_identity_wins_over_request_properties() -> None:
    identity = TokenIdentity(token="spam")
    resolver = StaticTokenResolver(identity)

    assert resolver.get_identity(properties={"token": "eggs"}) is identity


def test_reads_request_properties() -> None:
    identity = StaticTokenResolver().get_identity(properties={"token": "spam"})

    assert identity.token == "spam"
    assert identity.expiration is None


def test_requires_token() -> None:
    with pytest.raises(SmithyIdentityError):
        StaticTokenResolver().get_identity(properties={})


def test_token_hidden_from_repr() -> None:
    identity = TokenIdentity(token="spam")

    assert "spam" not in repr(identity)
    assert "spam" not in str(identity)


def test_expiration_normalized_to_utc() -> None:
    expiration = datetime(2026, 1, 1, 12, tzinfo=timezone(timedelta(hours=2)))
    identity = TokenIdentity(token="spam", expiration=expiration)

    assert identity.expiration is not None
    assert identity.expiration == datetime(2026, 1, 1, 10, tzinfo=UTC)
    assert identity.expiration.tzinfo is UTC


def test_is_expired() -> None:
    assert not TokenIdentity(token="spam").is_expired
    assert not TokenIdentity(
        token="spam", expiration=datetime.now(UTC) + timedelta(hours=1)
    ).is_expired
    assert TokenIdentity(
        token="spam", expiration=datetime.now(UTC) - timedelta(hours=1)
    ).is_expired
