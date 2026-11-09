#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import pytest
from smithy_aws_core.identity.environment import EnvironmentCredentialsResolver
from smithy_core.exceptions import SmithyIdentityError


@pytest.fixture(autouse=True)
def clear_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AWS_ACCOUNT_ID", raising=False)
    monkeypatch.delenv("AWS_SECRET_ACCESS_KEY", raising=False)
    monkeypatch.delenv("AWS_ACCESS_KEY_ID", raising=False)
    monkeypatch.delenv("AWS_SESSION_TOKEN", raising=False)


def test_no_values_set() -> None:
    with pytest.raises(SmithyIdentityError):
        EnvironmentCredentialsResolver().get_identity(properties={})


def test_akid_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "secret")

    with pytest.raises(SmithyIdentityError):
        EnvironmentCredentialsResolver().get_identity(properties={})


def test_secret_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "akid")

    with pytest.raises(SmithyIdentityError):
        EnvironmentCredentialsResolver().get_identity(properties={})


def test_minimum_required(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "akid")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "secret")

    credentials = EnvironmentCredentialsResolver().get_identity(properties={})
    assert credentials.access_key_id == "akid"
    assert credentials.secret_access_key == "secret"


def test_all_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "akid")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "secret")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "session")
    monkeypatch.setenv("AWS_ACCOUNT_ID", "123456789012")

    credentials = EnvironmentCredentialsResolver().get_identity(properties={})
    assert credentials.access_key_id == "akid"
    assert credentials.secret_access_key == "secret"
    assert credentials.session_token == "session"
    assert credentials.account_id == "123456789012"
