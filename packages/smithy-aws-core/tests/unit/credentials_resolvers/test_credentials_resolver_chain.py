from dataclasses import dataclass
from unittest.mock import Mock

import pytest
from smithy_aws_core.credentials_resolvers import (
    CredentialsResolverChain,
    IMDSCredentialsResolver,
    StaticCredentialsResolver,
)
from smithy_aws_core.credentials_resolvers.environment import (
    EnvironmentCredentialsSource,
)
from smithy_aws_core.credentials_resolvers.interfaces import (
    AwsCredentialsConfig,
    CredentialsSource,
)
from smithy_aws_core.identity import AWSCredentialsIdentity, AWSCredentialsResolver
from smithy_core.exceptions import SmithyIdentityException
from smithy_core.interfaces.identity import IdentityProperties
from smithy_http.aio.interfaces import HTTPClient


@dataclass
class Config:
    http_client: HTTPClient

    def __init__(self):
        self.http_client = Mock(spec=HTTPClient)  # type: ignore


async def test_no_sources_resolve():
    resolver_chain = CredentialsResolverChain(sources=[], config=Config())
    with pytest.raises(SmithyIdentityException):
        await resolver_chain.get_identity(identity_properties=IdentityProperties())


async def test_env_credentials_resolver_not_set(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("AWS_ACCESS_KEY_ID", raising=False)
    monkeypatch.delenv("AWS_SECRET_ACCESS_KEY", raising=False)
    resolver_chain = CredentialsResolverChain(
        sources=[EnvironmentCredentialsSource()], config=Config()
    )

    with pytest.raises(SmithyIdentityException):
        await resolver_chain.get_identity(identity_properties=IdentityProperties())


async def test_env_credentials_resolver_partial(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "akid")
    monkeypatch.delenv("AWS_SECRET_ACCESS_KEY", raising=False)
    resolver_chain = CredentialsResolverChain(
        sources=[EnvironmentCredentialsSource()], config=Config()
    )

    with pytest.raises(SmithyIdentityException):
        await resolver_chain.get_identity(identity_properties=IdentityProperties())


async def test_default_sources_env_credentials_resolver_success(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "akid")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "secret")
    resolver_chain = CredentialsResolverChain(config=Config())

    credentials = await resolver_chain.get_identity(
        identity_properties=IdentityProperties()
    )
    assert credentials.access_key_id == "akid"
    assert credentials.secret_access_key == "secret"


async def test_default_sources_imds_resolver_success(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("AWS_ACCESS_KEY_ID", raising=False)
    monkeypatch.delenv("AWS_SECRET_ACCESS_KEY", raising=False)

    async def mock_imds_get_identity(
        self: IMDSCredentialsResolver, *, identity_properties: IdentityProperties
    ) -> AWSCredentialsIdentity:
        return AWSCredentialsIdentity(
            access_key_id="akid",
            secret_access_key="secret",
        )

    monkeypatch.setattr(
        "smithy_aws_core.credentials_resolvers.IMDSCredentialsResolver.get_identity",
        mock_imds_get_identity,
    )

    resolver_chain = CredentialsResolverChain(config=Config())

    credentials = await resolver_chain.get_identity(
        identity_properties=IdentityProperties()
    )
    assert credentials.access_key_id == "akid"
    assert credentials.secret_access_key == "secret"


async def test_multiple_sources_one_valid():
    class FailingSource(CredentialsSource):
        def is_available(self, config: AwsCredentialsConfig) -> bool:
            return False

        def build_resolver(
            self, config: AwsCredentialsConfig
        ) -> AWSCredentialsResolver:
            raise RuntimeError("Should not be called")

    static_credentials = AWSCredentialsIdentity(
        access_key_id="valid_akid", secret_access_key="valid_secret"
    )
    static_resolver = StaticCredentialsResolver(credentials=static_credentials)

    class ValidSource(CredentialsSource):
        def is_available(self, config: AwsCredentialsConfig) -> bool:
            return True

        def build_resolver(
            self, config: AwsCredentialsConfig
        ) -> AWSCredentialsResolver:
            return static_resolver

    resolver_chain = CredentialsResolverChain(
        sources=[FailingSource(), ValidSource()], config=Config()
    )

    credentials = await resolver_chain.get_identity(
        identity_properties=IdentityProperties()
    )
    assert credentials.access_key_id == "valid_akid"
    assert credentials.secret_access_key == "valid_secret"


async def test_cached_resolver_used(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "cached_akid")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "cached_secret")
    resolver_chain = CredentialsResolverChain(
        sources=[EnvironmentCredentialsSource()], config=Config()
    )

    credentials1 = await resolver_chain.get_identity(
        identity_properties=IdentityProperties()
    )
    credentials2 = await resolver_chain.get_identity(
        identity_properties=IdentityProperties()
    )

    assert credentials1.access_key_id == credentials2.access_key_id == "cached_akid"
    assert (
        credentials1.secret_access_key
        == credentials2.secret_access_key
        == "cached_secret"
    )


async def test_custom_sources_with_static_credentials():
    static_credentials = AWSCredentialsIdentity(
        access_key_id="static_akid",
        secret_access_key="static_secret",
    )
    static_resolver = StaticCredentialsResolver(credentials=static_credentials)

    class TestStaticSource(CredentialsSource):
        def is_available(self, config: AwsCredentialsConfig) -> bool:
            return True

        def build_resolver(
            self, config: AwsCredentialsConfig
        ) -> AWSCredentialsResolver:
            return static_resolver

    resolver_chain = CredentialsResolverChain(
        sources=[TestStaticSource()],
        config=Config(),  # type: ignore
    )

    credentials = await resolver_chain.get_identity(
        identity_properties=IdentityProperties()
    )
    assert credentials.access_key_id == "static_akid"
    assert credentials.secret_access_key == "static_secret"
