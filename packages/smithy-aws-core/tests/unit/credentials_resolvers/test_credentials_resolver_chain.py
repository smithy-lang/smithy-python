import pytest
import os

from smithy_aws_core.credentials_resolvers import CredentialsResolverChain, StaticCredentialsResolver
from smithy_aws_core.identity import AWSCredentialsIdentity
from smithy_core.exceptions import SmithyIdentityException
from smithy_core.interfaces.identity import IdentityProperties


async def test_no_sources_resolve():
    resolver_chain = CredentialsResolverChain(sources=[])
    with pytest.raises(SmithyIdentityException):
        await resolver_chain.get_identity(identity_properties=IdentityProperties())


async def test_env_credentials_resolver_not_set(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("AWS_ACCESS_KEY_ID", raising=False)
    monkeypatch.delenv("AWS_SECRET_ACCESS_KEY", raising=False)
    resolver_chain = CredentialsResolverChain()

    with pytest.raises(SmithyIdentityException):
        await resolver_chain.get_identity(identity_properties=IdentityProperties())


async def test_env_credentials_resolver_partial(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "akid")
    monkeypatch.delenv("AWS_SECRET_ACCESS_KEY", raising=False)
    resolver_chain = CredentialsResolverChain()

    with pytest.raises(SmithyIdentityException):
        await resolver_chain.get_identity(identity_properties=IdentityProperties())


async def test_env_credentials_resolver_success(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "akid")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "secret")
    resolver_chain = CredentialsResolverChain()

    credentials = await resolver_chain.get_identity(identity_properties=IdentityProperties())
    assert credentials.access_key_id == "akid"
    assert credentials.secret_access_key == "secret"


async def test_custom_sources_with_static_credentials():
    static_credentials = AWSCredentialsIdentity(
        access_key_id="static_akid",
        secret_access_key="static_secret",
    )
    static_resolver = StaticCredentialsResolver(credentials=static_credentials)
    resolver_chain = CredentialsResolverChain(
        sources=[(lambda: False, lambda: None), (lambda: True, lambda: static_resolver)])

    credentials = await resolver_chain.get_identity(identity_properties=IdentityProperties())
    assert credentials.access_key_id == "static_akid"
    assert credentials.secret_access_key == "static_secret"

