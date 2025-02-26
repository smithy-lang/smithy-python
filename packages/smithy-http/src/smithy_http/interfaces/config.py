#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from typing import Any

from smithy_core.interfaces import URI
from smithy_core.interfaces.config import Config
from smithy_http.aio.interfaces import HTTPClient, EndpointResolver
from smithy_http.interfaces import HTTPRequestConfiguration


class HttpConfig(Config):
    http_client: HTTPClient
    http_request_config: HTTPRequestConfiguration | None
    endpoint_resolver: EndpointResolver[Any]
    endpoint_uri: str | URI | None
