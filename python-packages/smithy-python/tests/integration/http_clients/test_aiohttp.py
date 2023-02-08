# Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
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

from smithy_python._private.http import HttpRequest
from smithy_python._private.http.aiohttp_client import (
    AioHttpClient,
    AwsCrtHttpClientConfig,
)


async def test_basic_request_local(aws_request: HttpRequest) -> None:
    config = AwsCrtHttpClientConfig()
    session = AioHttpClient(client_config=config)
    response = await session.send(request=aws_request)
    assert response.status == 200
    body = await response.consume_body()
    assert b"aws" in body
    assert response.done
