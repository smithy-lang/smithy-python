#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from typing import Any
from unittest.mock import Mock

import pytest
import urllib3
from smithy_core import URI
from smithy_http import Fields, HTTPRequest
from smithy_http.interfaces import HTTPRequestConfiguration
from smithy_http.urllib3 import Urllib3HTTPClient, Urllib3HTTPClientConfig


def _send(
    config: Urllib3HTTPClientConfig | None = None,
    request_config: HTTPRequestConfiguration | None = None,
) -> Any:
    pool = Mock()
    pool.request.return_value = Mock(
        status=200, headers=urllib3.HTTPHeaderDict(), data=b"", reason="OK"
    )
    client = Urllib3HTTPClient(client_config=config, _pool=pool)
    request = HTTPRequest(
        destination=URI(host="example.com"), method="GET", fields=Fields()
    )
    client.send(request, request_config=request_config)
    return pool.request.call_args.kwargs["timeout"]


def test_requests_time_out_by_default() -> None:
    timeout = _send()
    assert timeout.connect_timeout == 60.0
    assert timeout.read_timeout == 60.0


def test_client_config_sets_the_timeouts() -> None:
    timeout = _send(Urllib3HTTPClientConfig(connect_timeout=1.0, read_timeout=None))
    assert timeout.connect_timeout == 1.0
    assert timeout.read_timeout is None


@pytest.mark.parametrize("client_read_timeout", [None, 30.0])
def test_request_read_timeout_takes_precedence(
    client_read_timeout: float | None,
) -> None:
    timeout = _send(
        Urllib3HTTPClientConfig(read_timeout=client_read_timeout),
        HTTPRequestConfiguration(read_timeout=5.0),
    )
    assert timeout.read_timeout == 5.0
