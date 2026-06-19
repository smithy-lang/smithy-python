#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import asyncio
import uuid
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from smithy_core.aio.interfaces import ClientTransport
from smithy_core.aio.interfaces.identity import IdentityResolver
from smithy_core.exceptions import SmithyIdentityError

from .components import (
    AWSCredentialsIdentity,
    AWSCredentialsResolver,
    AWSIdentityProperties,
)

if TYPE_CHECKING:
    from .._private.nested_clients.aws_sdk_sts.client import STSClient

DEFAULT_STS_REGION = "us-east-1"

type MfaCodeProvider = Callable[[str], Awaitable[str]]
"""An async callback to provide MFA token codes.

It receives the MFA device's serial number and returns the current token code
(e.g. from a prompt, TOTP generator, or secrets store). It must return a fresh,
single-use code each time.
"""


def _account_id_from_arn(arn: str | None) -> str | None:
    """Extract account ID from an ARN."""
    if arn is None:
        return None
    parts = arn.split(":")
    if len(parts) < 5 or not parts[4]:
        return None
    return parts[4]


class AssumeRoleCredentialsResolver(
    IdentityResolver[AWSCredentialsIdentity, AWSIdentityProperties]
):
    """Resolves AWS credentials from an STS ``AssumeRole`` call."""

    def __init__(
        self,
        source_resolver: AWSCredentialsResolver,
        role_arn: str,
        role_session_name: str | None = None,
        external_id: str | None = None,
        duration_seconds: int | None = None,
        region: str | None = None,
        http_client: ClientTransport[Any, Any] | None = None,
        mfa_serial: str | None = None,
        mfa_code_provider: MfaCodeProvider | None = None,
    ) -> None:
        self._source_resolver = source_resolver
        self._role_arn = role_arn
        self._role_session_name = (
            role_session_name or f"aws-sdk-python-{uuid.uuid4().hex[:8]}"
        )
        self._external_id = external_id
        self._duration_seconds = duration_seconds
        self._region = region or DEFAULT_STS_REGION
        self._http_client = http_client
        if mfa_serial is not None and mfa_code_provider is None:
            raise ValueError("mfa_code_provider is required when mfa_serial is set.")
        self._mfa_serial = mfa_serial
        self._mfa_code_provider = mfa_code_provider
        self._credentials: AWSCredentialsIdentity | None = None
        self._sts_client: STSClient | None = None
        self._refresh_lock = asyncio.Lock()

    async def get_identity(
        self, *, properties: AWSIdentityProperties
    ) -> AWSCredentialsIdentity:
        if self._credentials is not None and self._is_fresh(self._credentials):
            return self._credentials
        async with self._refresh_lock:
            if self._credentials is not None and self._is_fresh(self._credentials):
                return self._credentials
            self._credentials = await self._call_assume_role()
            return self._credentials

    def _is_fresh(self, credentials: AWSCredentialsIdentity) -> bool:
        return (
            credentials.expiration is not None
            and datetime.now(UTC) < credentials.expiration
        )

    async def _call_assume_role(self) -> AWSCredentialsIdentity:
        # Lazy import to avoid a circular import during module initialization
        from .._private.nested_clients.aws_sdk_sts.client import STSClient
        from .._private.nested_clients.aws_sdk_sts.config import Config
        from .._private.nested_clients.aws_sdk_sts.models import AssumeRoleInput

        if self._sts_client is None:
            self._sts_client = STSClient(
                config=Config(
                    region=self._region,
                    aws_credentials_identity_resolver=self._source_resolver,
                    transport=self._http_client,
                )
            )

        token_code = None
        if self._mfa_serial is not None and self._mfa_code_provider is not None:
            token_code = await self._mfa_code_provider(self._mfa_serial)

        response = await self._sts_client.assume_role(
            AssumeRoleInput(
                role_arn=self._role_arn,
                role_session_name=self._role_session_name,
                duration_seconds=self._duration_seconds,
                external_id=self._external_id,
                serial_number=self._mfa_serial,
                token_code=token_code,
            )
        )

        creds = response.credentials
        if creds is None:
            raise SmithyIdentityError("STS AssumeRole response missing Credentials")

        account_id = None
        if response.assumed_role_user is not None:
            account_id = _account_id_from_arn(response.assumed_role_user.arn)

        return AWSCredentialsIdentity(
            access_key_id=creds.access_key_id,
            secret_access_key=creds.secret_access_key,
            session_token=creds.session_token,
            expiration=creds.expiration,
            account_id=account_id,
        )
