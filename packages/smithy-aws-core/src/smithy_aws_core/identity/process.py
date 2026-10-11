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
    """Resolves AWS Credentials from a process.

    :param command: The process command and arguments to execute, as a
        non-empty list of strings.
    :param timeout: Maximum time in seconds to wait for the process to complete.
    :param account_id: Fallback account ID to associate with the resolved
        credentials when the process output does not include an ``AccountId``.
    """

    def __init__(
        self,
        command: list[str],
        *,
        timeout: float | None = None,
        account_id: str | None = None,
    ) -> None:
        if not _is_command_list(command):
            raise ValueError("command must be a non-empty list of strings")
        self._command = list(command)
        self._timeout = timeout
        self._account_id = account_id
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
        # These exceptions retain the full process output, which may contain
        # credentials. Suppress chaining to avoid exposing it in tracebacks.
        try:
            decoded = stdout.decode("utf-8")
            creds = json.loads(decoded)
        except UnicodeDecodeError as e:
            raise SmithyIdentityError(
                "Credential process output is not valid UTF-8 "
                f"at byte {e.start}: {e.reason}"
            ) from None
        except json.JSONDecodeError as e:
            raise SmithyIdentityError(
                "Credential process output is not valid JSON "
                f"at line {e.lineno}, column {e.colno}: {e.msg}"
            ) from None

        if not isinstance(creds, dict):
            raise SmithyIdentityError(
                "Credential process output must be a JSON object, "
                f"got {type(creds).__name__}"
            )
        creds = cast(dict[str, object], creds)

        version = creds.get("Version")
        if version != 1:
            raise SmithyIdentityError(
                f"Unsupported version '{version}' for credential process provider, supported versions: 1"
            )
        access_key_id = self._get_string_field(creds, "AccessKeyId")
        secret_access_key = self._get_string_field(creds, "SecretAccessKey")
        session_token = self._get_string_field(creds, "SessionToken")
        expiration = self._get_string_field(creds, "Expiration")
        # Prefer the process output's AccountId, falling back to the profile's
        # aws_account_id when the process omits it.
        account_id = self._get_string_field(creds, "AccountId") or self._account_id

        if expiration is not None:
            try:
                dt = datetime.fromisoformat(expiration)
            except (TypeError, ValueError) as e:
                raise SmithyIdentityError(
                    "Invalid credential process Expiration; "
                    f"expected an ISO 8601 string: {e}"
                ) from e
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

    @staticmethod
    def _get_string_field(creds: dict[str, object], key: str) -> str | None:
        value = creds.get(key)
        if value is not None and not isinstance(value, str):
            raise SmithyIdentityError(
                f"Credential process output field '{key}' must be a string, "
                f"got {type(value).__name__}"
            )
        return value
