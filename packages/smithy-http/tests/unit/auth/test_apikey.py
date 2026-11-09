#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import pytest
from smithy_core import URI
from smithy_core.traits import APIKeyLocation
from smithy_http import Field, Fields, HTTPRequest
from smithy_http.auth.apikey import APIKeySigner
from smithy_http.identity import APIKeyIdentity


def _request(destination: URI, fields: Fields | None = None) -> HTTPRequest:
    return HTTPRequest(
        destination=destination, body=b"", method="GET", fields=fields or Fields()
    )


DESTINATION = URI(
    scheme="https",
    username="user",
    password="secret",
    host="example.com",
    port=8443,
    path="/resource",
    query="spam=eggs",
    fragment="frag",
)


@pytest.mark.parametrize(
    "location, expected",
    [
        (
            APIKeyLocation.QUERY,
            _request(
                URI(
                    scheme="https",
                    username="user",
                    password="secret",
                    host="example.com",
                    port=8443,
                    path="/resource",
                    query="spam=eggs&eggs=key",
                    fragment="frag",
                )
            ),
        ),
        (
            APIKeyLocation.HEADER,
            _request(DESTINATION, Fields([Field(name="eggs", values=["key"])])),
        ),
    ],
)
def test_sign_preserves_destination(
    location: APIKeyLocation, expected: HTTPRequest
) -> None:
    signer = APIKeySigner(name="eggs", location=location)
    actual = signer.sign(
        request=_request(DESTINATION),
        identity=APIKeyIdentity(api_key="key"),
        properties={},
    )
    assert actual == expected
