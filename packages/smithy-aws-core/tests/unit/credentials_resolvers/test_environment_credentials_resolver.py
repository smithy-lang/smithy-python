#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import pytest

from smithy_aws_core.credentials_resolvers import EnvironmentCredentialsResolver
from smithy_core.exceptions import SmithyIdentityException
from smithy_core.interfaces.identity import IdentityProperties


async def test_no_values_set():
    with pytest.raises(SmithyIdentityException):
        await EnvironmentCredentialsResolver().get_identity(
            identity_properties=IdentityProperties()
        )


async def test_required_values_missing(monkeypatch):  # type: ignore
    monkeypatch.setenv("AWS_ACCOUNT_ID", "123456789012")  # type: ignore

    with pytest.raises(SmithyIdentityException):
        await EnvironmentCredentialsResolver().get_identity(
            identity_properties=IdentityProperties()
        )


async def test_akid_missing(monkeypatch):  # type: ignore
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "secret")  # type: ignore

    with pytest.raises(SmithyIdentityException):
        await EnvironmentCredentialsResolver().get_identity(
            identity_properties=IdentityProperties()
        )


async def test_secret_missing(monkeypatch):  # type: ignore
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "akid")  # type: ignore

    with pytest.raises(SmithyIdentityException):
        await EnvironmentCredentialsResolver().get_identity(
            identity_properties=IdentityProperties()
        )


async def test_minimum_required(monkeypatch):  # type: ignore
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "akid")  # type: ignore
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "secret")  # type: ignore

    credentials = await EnvironmentCredentialsResolver().get_identity(
        identity_properties=IdentityProperties()
    )
    assert credentials.access_key_id == "akid"
    assert credentials.secret_access_key == "secret"


async def test_all_values(monkeypatch):  # type: ignore
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "akid")  # type: ignore
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "secret")  # type: ignore
    monkeypatch.setenv("AWS_SESSION_TOKEN", "session")  # type: ignore
    monkeypatch.setenv("AWS_ACCOUNT_ID", "123456789012")  # type: ignore

    credentials = await EnvironmentCredentialsResolver().get_identity(
        identity_properties=IdentityProperties()
    )
    assert credentials.access_key_id == "akid"
    assert credentials.secret_access_key == "secret"
    assert credentials.session_token == "session"
    assert credentials.account_id == "123456789012"
