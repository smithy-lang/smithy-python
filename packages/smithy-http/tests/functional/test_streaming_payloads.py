#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from io import BytesIO

import pytest

pytest.importorskip("restjson")

from restjson.aio.client import AsyncRestJsonProtocolClient
from restjson.aio.config import AsyncRestJsonProtocolConfig
from restjson.client import RestJsonProtocolClient
from restjson.config import RestJsonProtocolConfig
from restjson.models import StreamingTraitsRequireLengthInput
from smithy_core.aio.types import AsyncBytesReader
from smithy_core.exceptions import SerializationError
from smithy_core.interfaces import StreamingBlob
from smithy_test import HTTPMockController, HTTPMockExpectation, mock
from smithy_test.aio import mock_async

PAYLOAD = b'{"hello":"world"}'


def test_streaming_payloads_are_sent_the_same() -> None:
    client = RestJsonProtocolClient(RestJsonProtocolConfig.resolve(region="us-west-2"))
    with mock(client) as controller:
        _expect_payload(controller).times(3)

        for blob in _blobs():
            client.streaming_traits_require_length(
                StreamingTraitsRequireLengthInput(blob=blob)
            )


async def test_async_streaming_payloads_are_sent_the_same() -> None:
    config = await AsyncRestJsonProtocolConfig.resolve(region="us-west-2")
    async with AsyncRestJsonProtocolClient(config) as client:
        with await mock_async(client) as controller:
            _expect_payload(controller).times(3)

            for blob in _blobs():
                await client.streaming_traits_require_length(
                    StreamingTraitsRequireLengthInput(blob=blob)
                )


async def test_unsized_streams_are_rejected_before_sending() -> None:
    config = await AsyncRestJsonProtocolConfig.resolve(region="us-west-2")
    async with AsyncRestJsonProtocolClient(config) as client:
        controller = await mock_async(client)
        _expect_payload(controller)

        with pytest.raises(SerializationError, match="content length"):
            await client.streaming_traits_require_length(
                StreamingTraitsRequireLengthInput(blob=AsyncBytesReader(PAYLOAD))
            )

    assert controller.requests == []


def _blobs() -> list[StreamingBlob]:
    return [PAYLOAD, bytearray(PAYLOAD), BytesIO(PAYLOAD)]


def _expect_payload(controller: HTTPMockController) -> HTTPMockExpectation:
    return controller.expect_request(
        method="POST",
        path="/StreamingTraitsRequireLength",
        headers={
            "Content-Type": "application/octet-stream",
            "Content-Length": str(len(PAYLOAD)),
        },
        body=PAYLOAD.decode(),
    )
