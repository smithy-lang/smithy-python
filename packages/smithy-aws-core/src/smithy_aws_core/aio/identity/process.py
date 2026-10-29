#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import asyncio

from smithy_core.aio.interfaces.identity import AsyncIdentityResolver
from smithy_core.exceptions import SmithyIdentityError

from ...identity.components import AWSCredentialsIdentity, AWSIdentityProperties
from ...identity.process import (
    _ProcessCredentialsResolverBase,  # pyright: ignore[reportPrivateUsage]
)

__all__ = ["AsyncProcessCredentialsResolver"]


class AsyncProcessCredentialsResolver(
    _ProcessCredentialsResolverBase,
    AsyncIdentityResolver[AWSCredentialsIdentity, AWSIdentityProperties],
):
    """Resolves AWS Credentials from a process.

    :param command: The process command and arguments to execute, as a
        non-empty list of strings.
    :param timeout: Maximum time in seconds to wait for the process to complete.
    :param account_id: Fallback account ID to associate with the resolved
        credentials when the process output does not include an ``AccountId``.
    """

    async def get_identity(
        self, *, properties: AWSIdentityProperties
    ) -> AWSCredentialsIdentity:
        if (cached := self._cached()) is not None:
            return cached

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
            raise self._timeout_error() from e

        return self._credentials_from_output(process.returncode, stdout, stderr)
