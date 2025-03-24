from typing import Callable, List

from smithy_aws_core.credentials_resolvers import EnvironmentCredentialsResolver
from smithy_aws_core.identity import AWSCredentialsIdentity, AWSCredentialsResolver
from smithy_core.aio.interfaces.identity import IdentityResolver
from smithy_core.exceptions import SmithyIdentityException
from smithy_core.interfaces.identity import IdentityProperties

import os


def _env_creds_available() -> bool:
    return (
        "AWS_ACCESS_KEY_ID" in os.environ
        and "AWS_SECRET_ACCESS_KEY" in os.environ
    )


def _build_env_creds() -> AWSCredentialsResolver:
    return EnvironmentCredentialsResolver()


type CredentialSource = tuple[Callable[[], bool], Callable[[], AWSCredentialsResolver]]
_DEFAULT_SOURCES: list[CredentialSource] = [(_env_creds_available, _build_env_creds)]


class CredentialsResolverChain(
    IdentityResolver[AWSCredentialsIdentity, IdentityProperties]
):
    """Resolves AWS Credentials from system environment variables."""

    def __init__(self, *, sources: List[CredentialSource] | None = None):
        if sources is None:
            sources = _DEFAULT_SOURCES
        self._sources: List[CredentialSource] = sources
        self._credentials_resolver: AWSCredentialsResolver | None = None

    async def get_identity(
        self, *, identity_properties: IdentityProperties
    ) -> AWSCredentialsIdentity:
        if self._credentials_resolver is not None:
            return await self._credentials_resolver.get_identity(
                identity_properties=identity_properties
            )

        for source in self._sources:
            if source[0]():
                self._credentials_resolver = source[1]()
                return await self._credentials_resolver.get_identity(
                    identity_properties=identity_properties
                )

        raise SmithyIdentityException(
            "None of the configured credentials sources were able to resolve credentials."
        )
