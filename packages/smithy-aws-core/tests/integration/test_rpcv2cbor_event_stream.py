#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""End-to-end duplex event streaming against the generated rpcv2Cbor client.

Drives the generated local client (``codegen-output/my-handwritten-model``) over the
real CRT HTTP/2 duplex transport against a local HTTP/2 server
(``_h2_server.H2BidiServer``) that referees a game of Simon Says.

The game makes the bidirectional exchange prove its own thoroughness. The server
(Simon) streams a scripted sequence of command events; each command's payload either
begins with ``simon says `` or does not. The client (the test's player loop) must send
a *move* event echoing the action when and only when Simon said so, and a *pass* event
otherwise. Because every turn produces exactly one client frame, the exchange is
deterministic: the referee advances one command per client frame and asserts the
client obeyed. A client that never put its events on the wire, or obeyed the wrong
commands, fails -- which a single ``initial-request``-only assertion could not catch.

The game itself lives in ``_simon_says`` and is shared with the rpcv2Json variant
(``test_rpcv2json_event_stream``).
"""

import pytest

pytest.importorskip("smithy_cbor")
pytest.importorskip("my_handwritten_model")
pytest.importorskip("awscrt")
pytest.importorskip("h2")
pytest.importorskip("trustme")

import my_handwritten_model.models
from my_handwritten_model.aio.client import AsyncMyHandwrittenModel
from my_handwritten_model.aio.config import AsyncConfig
from smithy_cbor import CBORCodec

from ._simon_says import REQUEST_FORMS, GameProtocol, RequestForm, play_simon_says

_RPCV2_CBOR = GameProtocol(
    client_class=AsyncMyHandwrittenModel,
    config_class=AsyncConfig,
    models=my_handwritten_model.models,
    codec=CBORCodec(),
    payload_content_type="application/cbor",
    smithy_protocol="rpc-v2-cbor",
)


@pytest.mark.parametrize("request_form", REQUEST_FORMS)
async def test_simon_says_duplex(request_form: RequestForm) -> None:
    await play_simon_says(_RPCV2_CBOR, request_form)
