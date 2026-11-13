#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""End-to-end duplex event streaming against the generated rpcv2Json client.

The rpcv2Json counterpart of ``test_rpcv2cbor_event_stream``: drives the generated
local client (``codegen-output/my-handwritten-json-model``) over the real CRT HTTP/2
duplex transport against a local HTTP/2 server (``_h2_server.H2BidiServer``) that
referees a game of Simon Says.

The server (Simon) streams a scripted sequence of command events; the client must
send a *move* event echoing the action when and only when the command begins with
``simon says ``, and a *pass* event otherwise. Every turn produces exactly one client
frame, so the referee can advance one command per client frame and assert the client
obeyed. See ``_simon_says`` for the shared game.
"""

import pytest

pytest.importorskip("smithy_json")
pytest.importorskip("my_handwritten_json_model")
pytest.importorskip("awscrt")
pytest.importorskip("h2")
pytest.importorskip("trustme")

import my_handwritten_json_model.models
from my_handwritten_json_model.aio.client import AsyncMyHandwrittenJsonModel
from my_handwritten_json_model.aio.config import AsyncConfig
from smithy_core.types import TimestampFormat
from smithy_http.aio.crt import AWSCRTHTTPClient
from smithy_http.aio.protocols import AsyncRpcV2JsonClientProtocol
from smithy_json import JSONCodec

from ._simon_says import REQUEST_FORMS, GameProtocol, RequestForm, play_simon_says

# codec=None: the referee encodes and decodes event payloads with the client's own
# protocol payload codec, so it cannot drift from what the client puts on the wire.
_RPCV2_JSON = GameProtocol(
    client_class=AsyncMyHandwrittenJsonModel,
    config_class=AsyncConfig,
    models=my_handwritten_json_model.models,
    payload_content_type="application/json",
    smithy_protocol="rpc-v2-json",
)


async def test_client_uses_rpcv2json_codec() -> None:
    # The codec the referee borrows must be the rpcv2Json-configured JSONCodec.
    transport = AWSCRTHTTPClient()
    try:
        protocol = AsyncConfig(transport=transport).protocol
        assert isinstance(protocol, AsyncRpcV2JsonClientProtocol)
        codec = protocol.payload_codec
        assert isinstance(codec, JSONCodec)
        assert codec.media_type == "application/json"
        settings = codec._settings  # pyright: ignore[reportPrivateUsage]
        assert settings.use_json_name is False
        assert settings.use_timestamp_format is False
        assert settings.default_timestamp_format is TimestampFormat.EPOCH_SECONDS
        assert settings.arbitrary_precision_as_string is True
        assert settings.default_namespace == "smithy.python.tests.handwritten.json"
    finally:
        await transport.close()


@pytest.mark.parametrize("request_form", REQUEST_FORMS)
async def test_simon_says_duplex(request_form: RequestForm) -> None:
    await play_simon_says(_RPCV2_JSON, request_form)
