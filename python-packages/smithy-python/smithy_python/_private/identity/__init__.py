# Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
# http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.
import hashlib
from datetime import datetime, timedelta
from typing import Any

from ...exceptions import SmithyIdentityException
from ...interfaces import identity as identity_interfaces
from ..http import Request


class Identity:
    def __init__(self, expiration: datetime | None = None):
        if expiration is None:
            self._expiration = datetime.now() + timedelta(minutes=60)

    @property
    def is_expired(self) -> bool:
        return datetime.now() > self.expiration

    @property
    def expiration(self) -> datetime:
        return self._expiration


class TokenIdentity(Identity):
    def __init__(self, token: str, expiration: datetime | None = None):
        super().__init__(expiration)
        self._token = token

    @property
    def token(self) -> str:
        return self._token


class LoginIdentity(Identity):
    def __init__(
        self, username: str, password: str, expiration: datetime | None = None
    ):
        super().__init__(expiration)
        self._username = username
        self._password = password

    @property
    def username(self) -> str:
        return self._username

    @property
    def password(self) -> str:
        return self._password


class AnonymousIdentity(Identity):
    def __init__(self, expiration: datetime | None = None):
        super().__init__(expiration)


class IdentityResolver:
    async def get_identity(self, identity_properties: dict[str, Any]) -> Identity:
        raise NotImplementedError


class HttpSigner:

    IDENTITY_CLS: type[identity_interfaces.IdentityType]

    def sign(
        self,
        http_request: Request,
        identity: identity_interfaces.IdentityType,
        identity_properties: dict[str, Any],
    ) -> Request:
        if not isinstance(identity, self.IDENTITY_CLS):
            raise SmithyIdentityException(
                f"Expected {self.IDENTITY_CLS} but got {type(identity)}"
            )
        http_request.headers.extend([(k, v) for k, v in identity_properties.items()])
        return http_request


class AnonymousSigner(HttpSigner):

    IDENTITY_CLS = AnonymousIdentity

    def sign(
        self,
        http_request: Request,
        identity: identity_interfaces.AnonymousIdentity,
        identity_properties: dict[str, Any],
    ) -> Request:
        super().sign(http_request, identity, identity_properties)
        return http_request


class BearerSigner(HttpSigner):

    IDENTITY_CLS = TokenIdentity

    def sign(
        self,
        http_request: Request,
        identity: identity_interfaces.TokenIdentity,
        identity_properties: dict[str, Any],
    ) -> Request:
        super().sign(http_request, identity, identity_properties)
        http_request.headers["Authorization"] = f"Bearer {identity.token}"
        return http_request


class ApiKeySigner(HttpSigner):

    IDENTITY_CLS = TokenIdentity

    def sign(
        self,
        http_request: Request,
        identity: identity_interfaces.TokenIdentity,
        identity_properties: dict[str, Any],
    ) -> Request:
        super().sign(http_request, identity, identity_properties)
        http_request.headers["X-Api-Key"] = identity.token

        return http_request


class HttpBasicSigner(HttpSigner):

    IDENTITY_CLS = LoginIdentity

    def sign(
        self,
        http_request: Request,
        identity: identity_interfaces.LoginIdentity,
        identity_properties: dict[str, Any],
    ) -> Request:
        super().sign(http_request, identity, identity_properties)
        user_pass = f"{identity.username}:{identity.password}"
        encoded_user_pass = hashlib.sha256(user_pass.encode("utf-8")).hexdigest()
        http_request.headers["Authorization"] = encoded_user_pass
        return http_request


class HttpDigestSigner(HttpSigner):

    IDENTITY_CLS = LoginIdentity

    def sign(
        self,
        http_request: Request,
        identity: identity_interfaces.LoginIdentity,
        identity_properties: dict[str, Any],
    ) -> Request:
        super().sign(http_request, identity, identity_properties)
        user_pass = f"{identity.username}:{identity.password}"
        encoded_user_pass = hashlib.sha256(user_pass.encode("utf-8")).hexdigest()
        http_request.headers["Authorization"] = encoded_user_pass
        return http_request
