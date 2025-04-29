#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import pytest
from smithy_aws_core.credentials_resolvers import EnvironmentCredentialsResolver
from smithy_core.exceptions import SmithyIdentityError
from smithy_core.interfaces.identity import IdentityProperties


async def test_no_values_set():
    with pytest.raises(SmithyIdentityError):
        await EnvironmentCredentialsResolver().get_identity(
            identity_properties=IdentityProperties()
        )


async def test_required_values_missing(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AWS_ACCOUNT_ID", "123456789012")

    with pytest.raises(SmithyIdentityError):
        await EnvironmentCredentialsResolver().get_identity(
            identity_properties=IdentityProperties()
        )


async def test_akid_missing(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "secret")

    with pytest.raises(SmithyIdentityError):
        await EnvironmentCredentialsResolver().get_identity(
            identity_properties=IdentityProperties()
        )


async def test_secret_missing(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "akid")

    with pytest.raises(SmithyIdentityError):
        await EnvironmentCredentialsResolver().get_identity(
            identity_properties=IdentityProperties()
        )


async def test_minimum_required(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "akid")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "secret")

    credentials = await EnvironmentCredentialsResolver().get_identity(
        identity_properties=IdentityProperties()
    )
    assert credentials.access_key_id == "akid"
    assert credentials.secret_access_key == "secret"


async def test_all_values(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "akid")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "secret")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "session")
    monkeypatch.setenv("AWS_ACCOUNT_ID", "123456789012")

    credentials = await EnvironmentCredentialsResolver().get_identity(
        identity_properties=IdentityProperties()
    )
    assert credentials.access_key_id == "akid"
    assert credentials.secret_access_key == "secret"
    assert credentials.session_token == "session"
    assert credentials.account_id == "123456789012"
