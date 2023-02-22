# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.

import pytest

from smithy_python._private import URI, Field, Fields
from smithy_python._private.http import HTTPRequest
from smithy_python.async_utils import async_list


@pytest.fixture
def sample_request() -> HTTPRequest:
    headers = Fields(
        [
            Field(name="host", values=["aws.amazon.com"]),
            Field(name="user-agent", values=["smithy-python-test"]),
        ]
    )
    return HTTPRequest(
        method="GET",
        destination=URI(host="aws.amazon.com"),
        fields=headers,
        body=async_list([]),
    )
