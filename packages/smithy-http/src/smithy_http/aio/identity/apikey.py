#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from smithy_core.aio.interfaces.identity import IdentityResolver
from smithy_core.identity import Identity
from smithy_core.interfaces.identity import IdentityProperties


class ApiKeyIdentity(Identity):
    """The identity for auth that uses an api key."""

    def __init__(self, *, api_key: str) -> None:
        super().__init__(expiration=None)
        self.api_key = api_key


class ApiKeyIdentityResolver(IdentityResolver[ApiKeyIdentity, IdentityProperties]):
    """Loads the api key identity from the configuration."""

    def __init__(self, *, api_key: str | ApiKeyIdentity) -> None:
        """
        :param api_key: The API key to authenticate with.
        """
        match api_key:
            case str():
                self._identity = ApiKeyIdentity(api_key=api_key)
            case ApiKeyIdentity():
                self._identity = api_key

    async def get_identity(
        self, *, identity_properties: IdentityProperties
    ) -> ApiKeyIdentity:
        """Load the user's api key identity from this resolver.

        :param identity_properties: Properties used to help determine the identity to
            return.
        :returns: The api key identity.
        """
        return self._identity
