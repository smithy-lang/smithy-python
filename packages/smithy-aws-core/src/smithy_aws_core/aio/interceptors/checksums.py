#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""The flexible checksums interceptor of asynchronous clients."""

from ...interceptors.checksums import FlexibleChecksumsInterceptor
from .._aws_chunked import AsyncAwsChunkedReader
from ..checksums import AsyncChecksumStream

__all__ = ["AsyncFlexibleChecksumsInterceptor"]


class AsyncFlexibleChecksumsInterceptor(FlexibleChecksumsInterceptor):
    """Adds and validates checksums for operations of asynchronous clients.

    Behaves like :py:class:`FlexibleChecksumsInterceptor`, and also reads
    asynchronous payloads: response payloads are validated with
    :py:class:`AsyncChecksumStream`, and asynchronous request payloads are encoded
    with a trailing checksum as they're sent.
    """

    def __init__(self) -> None:
        """Initialize the interceptor.

        :raises MissingDependencyError: If smithy-aws-checksums isn't installed.
        """
        super().__init__(AsyncChecksumStream, AsyncAwsChunkedReader)
