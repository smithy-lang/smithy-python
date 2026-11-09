# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import io
from collections.abc import AsyncIterable
from hashlib import sha256
from inspect import iscoroutinefunction
from typing import Any, TypeGuard

from .._http import AWSRequest
from .._sigv4 import SigV4SignerBase, SigV4SigningProperties, hash_sync_body
from ..interfaces.identity import AWSCredentialsIdentity
from ..interfaces.io import ConditionallySeekable
from ._io import AsyncBytesReader
from ._program import run_program_async
from .interfaces.io import AsyncSeekable

__all__ = ("AsyncSigV4Signer",)


class AsyncSigV4Signer(SigV4SignerBase):
    """Request signer for applying the AWS Signature Version 4 algorithm.

    Signs requests with sync or async bodies.
    """

    async def sign(
        self,
        *,
        request: AWSRequest,
        identity: AWSCredentialsIdentity,
        properties: SigV4SigningProperties,
    ) -> AWSRequest:
        """Generate and apply a SigV4 Signature to a copy of the supplied request.

        :param request: An AWSRequest to sign prior to sending to the service.
        :param identity: A set of credentials representing an AWS Identity or role
            capacity.
        :param properties: SigV4SigningProperties to define signing primitives such as
            the target service, region, and date.
        """
        return await run_program_async(self._sign(request, identity, properties))

    async def canonical_request(
        self, *, signing_properties: SigV4SigningProperties, request: AWSRequest
    ) -> str:
        """Build the SigV4 canonical request.

        See :py:meth:`aws_sdk_signers.SigV4Signer.canonical_request`.

        :param signing_properties:
            SigV4SigningProperties to define signing primitives such as
            the target service, region, and date.
        :param request:
            An AWSRequest to use for generating a SigV4 signature.
        """
        return await run_program_async(
            self._canonical_request(signing_properties, request)
        )

    async def _hash_body(self, request: AWSRequest) -> str:
        body = request.body
        if not isinstance(body, AsyncIterable):
            return hash_sync_body(request)

        checksum = sha256()
        if _is_async_seekable(body):
            position = body.tell()
            async for chunk in body:  # type: ignore
                checksum.update(chunk)  # type: ignore
            await body.seek(position)
        else:
            buffer = io.BytesIO()
            async for chunk in body:
                buffer.write(chunk)
                checksum.update(chunk)
            buffer.seek(0)
            request.body = AsyncBytesReader(buffer)
        return checksum.hexdigest()


def _is_async_seekable(body: Any) -> TypeGuard[AsyncSeekable]:
    if isinstance(body, ConditionallySeekable):
        return body.seekable()
    return isinstance(body, AsyncSeekable) and iscoroutinefunction(body.seek)
