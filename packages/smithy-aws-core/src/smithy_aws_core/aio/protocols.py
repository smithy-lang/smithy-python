# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from smithy_http.aio.protocols import (
    AsyncHttpEventStreamMixin,
    AsyncRpcEventStreamMixin,
)

from ..protocols import (
    AwsJson10ClientProtocol,
    AwsJson11ClientProtocol,
    RestJsonClientProtocol,
    RestXmlClientProtocol,
)

__all__ = [
    "AsyncAwsJson10ClientProtocol",
    "AsyncAwsJson11ClientProtocol",
    "AsyncRestJsonClientProtocol",
    "AsyncRestXmlClientProtocol",
]


class AsyncRestJsonClientProtocol(AsyncHttpEventStreamMixin, RestJsonClientProtocol):
    """An implementation of the aws.protocols#restJson1 protocol with event streams."""


class AsyncRestXmlClientProtocol(AsyncHttpEventStreamMixin, RestXmlClientProtocol):
    """An implementation of the aws.protocols#restXml protocol with event streams."""


class AsyncAwsJson10ClientProtocol(AsyncRpcEventStreamMixin, AwsJson10ClientProtocol):
    """An implementation of the aws.protocols#awsJson1_0 protocol with event streams."""


class AsyncAwsJson11ClientProtocol(AsyncRpcEventStreamMixin, AwsJson11ClientProtocol):
    """An implementation of the aws.protocols#awsJson1_1 protocol with event streams."""
