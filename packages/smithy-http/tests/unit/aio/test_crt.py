#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from copy import deepcopy
from io import BytesIO

from smithy_core import URI
from smithy_http import Fields
from smithy_http.aio import HTTPRequest
from smithy_http.aio.crt import AWSCRTHTTPClient


def test_deepcopy_client() -> None:
    """Test that AWSCRTHTTPClient can be deep copied."""
    client = AWSCRTHTTPClient()
    deepcopy(client)


def test_client_marshal_request() -> None:
    """Test that HTTPRequest is correctly marshaled to CRT HttpRequest."""
    client = AWSCRTHTTPClient()
    request = HTTPRequest(
        method="GET",
        destination=URI(
            host="example.com", path="/path", query="key1=value1&key2=value2"
        ),
        body=BytesIO(),
        fields=Fields(),
    )
    crt_request = client._marshal_request(request)  # type: ignore
    assert crt_request.headers.get("host") == "example.com"  # type: ignore
    assert crt_request.headers.get("accept") == "*/*"  # type: ignore
    assert crt_request.method == "GET"  # type: ignore
    assert crt_request.path == "/path?key1=value1&key2=value2"  # type: ignore
