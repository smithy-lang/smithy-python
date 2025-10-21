#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from smithy_core import URI
from smithy_http import tuples_to_fields
from smithy_http.aio import HTTPRequest


def create_test_request(
    method: str = "GET",
    host: str = "test.aws.dev",
    path: str | None = None,
    headers: list[tuple[str, str]] | None = None,
    body: bytes = b"",
) -> HTTPRequest:
    """Create test HTTPRequest with defaults.

    :param method: HTTP method (GET, POST, etc.)
    :param host: Host name (e.g., "test.aws.dev")
    :param path: Optional path (e.g., "/users")
    :param headers: Optional headers as list of (name, value) tuples
    :param body: Request body as bytes
    :return: Configured HTTPRequest for testing
    """
    return HTTPRequest(
        destination=URI(host=host, path=path),
        method=method,
        fields=tuples_to_fields(headers or []),
        body=body,
    )
