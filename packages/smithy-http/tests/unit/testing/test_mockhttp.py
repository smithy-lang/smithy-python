#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import pytest
from smithy_core.utils import read_streaming_blob
from smithy_http.testing import MockHTTPClient, MockHTTPClientError, create_test_request


def test_queued_responses_fifo():
    mock_client = MockHTTPClient()
    mock_client.add_response(status=404, body=b"not found")
    mock_client.add_response(status=500, body=b"server error")
    request = create_test_request()

    response1 = mock_client.send(request)
    assert response1.status == 404
    assert read_streaming_blob(response1.body) == b"not found"

    response2 = mock_client.send(request)
    assert response2.status == 500
    assert read_streaming_blob(response2.body) == b"server error"

    assert mock_client.call_count == 2
    assert len(mock_client.captured_requests) == 2


def test_raises_without_queued_response():
    with pytest.raises(MockHTTPClientError, match="No responses queued"):
        MockHTTPClient().send(create_test_request())
