#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import pytest
from smithy_core.aio.interfaces import ErrorInfo

try:
    from smithy_http.aio.aiohttp import AIOHTTPClient

    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False

try:
    from smithy_http.aio.crt import AWSCRTHTTPClient

    HAS_CRT = True
except ImportError:
    HAS_CRT = False


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not available")
class TestAIOHTTPTimeoutErrorHandling:
    """Test timeout error handling for AIOHTTPClient."""

    @pytest.fixture
    async def client(self):
        return AIOHTTPClient()

    @pytest.mark.asyncio
    async def test_timeout_error_detection(self, client):
        """Test timeout error detection for standard TimeoutError."""
        timeout_err = TimeoutError("Connection timed out")
        result = client.get_error_info(timeout_err)
        assert result == ErrorInfo(is_timeout_error=True, fault="client")

    @pytest.mark.asyncio
    async def test_non_timeout_error_detection(self, client):
        """Test non-timeout error detection."""
        other_err = ValueError("Not a timeout")
        result = client.get_error_info(other_err)
        assert result == ErrorInfo(is_timeout_error=False, fault="client")


@pytest.mark.skipif(not HAS_CRT, reason="AWS CRT not available")
class TestAWSCRTTimeoutErrorHandling:
    """Test timeout error handling for AWSCRTHTTPClient."""

    @pytest.fixture
    def client(self):
        return AWSCRTHTTPClient()

    def test_timeout_error_detection(self, client):
        """Test timeout error detection for standard TimeoutError."""
        timeout_err = TimeoutError("Connection timed out")
        result = client.get_error_info(timeout_err)
        assert result == ErrorInfo(is_timeout_error=True, fault="client")

    def test_non_timeout_error_detection(self, client):
        """Test non-timeout error detection."""
        other_err = ValueError("Not a timeout")
        result = client.get_error_info(other_err)
        assert result == ErrorInfo(is_timeout_error=False, fault="client")
