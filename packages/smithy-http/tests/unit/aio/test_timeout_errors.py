#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from typing import TYPE_CHECKING

import pytest
from smithy_core.aio.interfaces import ErrorInfo

if TYPE_CHECKING:
    from smithy_http.aio.aiohttp import AIOHTTPClient
    from smithy_http.aio.crt import AWSCRTHTTPClient

try:
    from smithy_http.aio.aiohttp import AIOHTTPClient

    has_aiohttp = True
except ImportError:
    has_aiohttp = False

try:
    from smithy_http.aio.crt import AWSCRTHTTPClient

    has_crt = True
except ImportError:
    has_crt = False


@pytest.mark.skipif(not has_aiohttp, reason="aiohttp not available")
class TestAIOHTTPTimeoutErrorHandling:
    """Test timeout error handling for AIOHTTPClient."""

    @pytest.fixture
    async def client(self) -> "AIOHTTPClient":
        return AIOHTTPClient()

    @pytest.mark.asyncio
    async def test_timeout_error_detection(self, client: "AIOHTTPClient") -> None:
        """Test timeout error detection for standard TimeoutError."""
        timeout_err = TimeoutError("Connection timed out")
        result = client.get_error_info(timeout_err)
        assert result == ErrorInfo(is_timeout_error=True, fault="client")

    @pytest.mark.asyncio
    async def test_non_timeout_error_detection(self, client: "AIOHTTPClient") -> None:
        """Test non-timeout error detection."""
        other_err = ValueError("Not a timeout")
        result = client.get_error_info(other_err)
        assert result == ErrorInfo(is_timeout_error=False, fault="client")


@pytest.mark.skipif(not has_crt, reason="AWS CRT not available")
class TestAWSCRTTimeoutErrorHandling:
    """Test timeout error handling for AWSCRTHTTPClient."""

    @pytest.fixture
    def client(self) -> "AWSCRTHTTPClient":
        return AWSCRTHTTPClient()

    def test_timeout_error_detection(self, client: "AWSCRTHTTPClient") -> None:
        """Test timeout error detection for standard TimeoutError."""
        timeout_err = TimeoutError("Connection timed out")
        result = client.get_error_info(timeout_err)
        assert result == ErrorInfo(is_timeout_error=True, fault="client")

    def test_non_timeout_error_detection(self, client: "AWSCRTHTTPClient") -> None:
        """Test non-timeout error detection."""
        other_err = ValueError("Not a timeout")
        result = client.get_error_info(other_err)
        assert result == ErrorInfo(is_timeout_error=False, fault="client")
