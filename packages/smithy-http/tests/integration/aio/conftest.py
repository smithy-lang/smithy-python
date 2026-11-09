#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import pytest
from smithy_core import URI
from smithy_core.aio.utils import list_async
from smithy_http import Field, Fields, HTTPRequest


@pytest.fixture
def sample_request() -> HTTPRequest:
    headers = Fields(
        [
            Field(name="host", values=["aws.amazon.com"]),
            Field(name="user-agent", values=["smithy-python-test"]),
        ]
    )
    b: list[bytes] = []
    return HTTPRequest(
        method="GET",
        destination=URI(host="aws.amazon.com"),
        fields=headers,
        body=list_async(b),
    )
