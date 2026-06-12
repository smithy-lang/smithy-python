#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from smithy_http.aio.aiohttp import AIOHTTPClient


def test_does_not_support_duplex_streaming() -> None:
    assert AIOHTTPClient.SUPPORTS_DUPLEX_STREAMING is False
