#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import asyncio
import json
from datetime import UTC, datetime
from typing import TypeGuard, cast

from smithy_core.aio.interfaces.identity import IdentityResolver
from smithy_core.exceptions import SmithyIdentityError

from .components import AWSCredentialsIdentity, AWSIdentityProperties


def _is_command_list(command: object) -> TypeGuard[list[str]]:
    if not isinstance(command, list) or not command:
        return False
    return all(isinstance(argument, str) for argument in cast(list[object], command))


class ProcessCredentialsResolver(
    IdentityResolver[AWSCredentialsIdentity, AWSIdentityProperties]
):
    """Resolves AWS Credentials from a process."""

    def __init__(
        self,
        command: list[str],
        *,
        timeout: float | None = None,
    ) -> None:
        if not _is_command_list(command):
            raise ValueError("command must be a non-empty list of strings")
        self._command = list(command)
        self._timeout = timeout
        self._credentials: AWSCredentialsIdentity | None = None

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
        except OSError as e:
            raise SmithyIdentityError(f"Credential process failed to start: {e}") from e

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=self._timeout
            )
        except TimeoutError as e:
            if process.returncode is None:
                try:
                    process.kill()
                except ProcessLookupError:
                    pass
            await process.wait()
            raise SmithyIdentityError(
                f"Credential process timed out after {self._timeout} seconds"
            ) from e

        if process.returncode != 0:
            raise SmithyIdentityError(
                f"Credential process failed with exit code {process.returncode}: "
                f"{stderr.decode('utf-8', errors='replace')}"
            )
        try:
            creds = json.loads(stdout.decode("utf-8"))
        except json.JSONDecodeError as e:
            raise SmithyIdentityError(
                f"Failed to parse credential process output: {e}"
            ) from e

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
            dt = datetime.fromisoformat(expiration)
            expiration = dt.astimezone(UTC) if dt.tzinfo else dt.replace(tzinfo=UTC)

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

    async def invalidate(self) -> None:
        """Discard cached credentials so the next resolution reruns the process."""
        self._credentials = None
