#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""End-to-end event streaming against the generated rpcv2Cbor client.

It drives the generated local client (``codegen-output/my-handwritten-model``) over the real CRT
HTTP/2 duplex transport against a local HTTP/2 server (``_h2_server.H2BidiServer``)
that performs a genuine bidirectional exchange. The client writes the
initial-request frame and an input event while the server concurrently streams
back an initial-response frame and an output event.
"""

from collections.abc import AsyncIterator

import pytest

pytest.importorskip("smithy_cbor")
pytest.importorskip("my_handwritten_model")
pytest.importorskip("awscrt")
pytest.importorskip("h2")
pytest.importorskip("trustme")

from my_handwritten_model.client import MyHandwrittenModel
from my_handwritten_model.config import Config
from my_handwritten_model.models import (
    Alpha,
    TradeEventsAlpha,
    TradeEventStreamInput,
    TradeEventStreamOutput,
)
from smithy_cbor import CBORCodec
from smithy_core import URI
from smithy_http.aio.crt import (
    AWSCRTHTTPClient,
    AWSCRTHTTPClientConfig,
)

from ._h2_server import H2BidiServer, encode_event

_CODEC = CBORCodec()


def _response_frames() -> bytes:
    initial_response = encode_event(
        "initial-response",
        _CODEC.serialize(shape=TradeEventStreamOutput(greeting="welcome")),
    )
    output_event = encode_event("alpha", _CODEC.serialize(shape=Alpha(id="trade-1")))
    return initial_response + output_event


def _client(server: H2BidiServer) -> tuple[MyHandwrittenModel, AWSCRTHTTPClient]:
    transport = AWSCRTHTTPClient(
        client_config=AWSCRTHTTPClientConfig(
            force_http_2=True, trust_store_path=str(server.ca_cert_path)
        )
    )
    client = MyHandwrittenModel(
        Config(
            endpoint_uri=URI(host=server.host, port=server.port, scheme="https"),
            transport=transport,
        )
    )
    return client, transport


async def test_duplex_event_stream_round_trip() -> None:
    async with H2BidiServer(_response_frames()) as server:
        client, transport = _client(server)

        stream = await client.trade_event_stream(
            TradeEventStreamInput(session_id="s-1")
        )
        await stream.input_stream.send(TradeEventsAlpha(value=Alpha(id="client-1")))
        await stream.input_stream.close()

        output, output_stream = await stream.await_output()
        assert output.greeting == "welcome"

        received = await _first(output_stream)
        assert isinstance(received, TradeEventsAlpha)
        assert received.value.id == "trade-1"

        assert server.received_event_types[0] == "initial-request"

        # Drop the connection so the server's handler loop exits and the server
        # shuts down without waiting on a lingering h2 stream.
        await transport.close()


async def _first(output_stream: AsyncIterator[object]) -> object:
    async for event in output_stream:
        return event
    raise AssertionError("output stream yielded no events")
