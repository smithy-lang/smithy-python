#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import asyncio
import json
from dataclasses import dataclass
from datetime import UTC, datetime

from smithy_core.aio.interfaces.identity import IdentityResolver
from smithy_core.exceptions import SmithyIdentityError

from smithy_aws_core.identity.components import (
    AWSCredentialsIdentity,
    AWSIdentityProperties,
)

_DEFAULT_TIMEOUT = 30


@dataclass
class ProcessCredentialsConfig:
    """Configuration for process credential retrieval operations."""

    timeout: int = _DEFAULT_TIMEOUT


class ProcessCredentialsResolver(
    IdentityResolver[AWSCredentialsIdentity, AWSIdentityProperties]
):
    """Resolves AWS Credentials from a process."""

    def __init__(
        self,
        command: list[str],
        config: ProcessCredentialsConfig | None = None,
    ):
        if not command:
            raise ValueError("command must be a non-empty list")
        self._command = command
        self._config = config or ProcessCredentialsConfig()
        self._credentials = None

    async def get_identity(
        self, *, properties: AWSIdentityProperties
    ) -> AWSCredentialsIdentity:
        if self._credentials is not None:
            # Long-term credentials (no expiration) should always be reused
            if self._credentials.expiration is None:
                return self._credentials
            # Temporary credentials should be reused if not expired
            if datetime.now(UTC) < self._credentials.expiration:
                return self._credentials

        try:
            process = await asyncio.create_subprocess_exec(
                *self._command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=self._config.timeout
            )
        except TimeoutError as e:
            raise SmithyIdentityError(
                f"Credential process timed out after {self._config.timeout} seconds"
            ) from e

        if process.returncode != 0:
            raise SmithyIdentityError(
                f"Credential process failed with non-zero exit code: {stderr.decode('utf-8')}"
            )
        creds = json.loads(stdout.decode("utf-8"))

        version = creds.get("Version")
        if version is None or version != 1:
            raise SmithyIdentityError(
                f"Unsupported version '{version}' for credential process provider, supported versions: 1"
            )
        access_key_id = creds.get("AccessKeyId")
        secret_access_key = creds.get("SecretAccessKey")
        session_token = creds.get("SessionToken")
        expiration = creds.get("Expiration")
        account_id = creds.get("AccountId")

        if isinstance(expiration, str):
            expiration = datetime.fromisoformat(expiration).replace(tzinfo=UTC)

        if access_key_id is None or secret_access_key is None:
            raise SmithyIdentityError(
                "AccessKeyId and SecretAccessKey are required for process credentials"
            )

        self._credentials = AWSCredentialsIdentity(
            access_key_id=access_key_id,
            secret_access_key=secret_access_key,
            session_token=session_token,
            expiration=expiration,
            account_id=account_id,
        )
        return self._credentials
