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
    TradeEventsBeta,
    TradeEventStreamInput,
    TradeEventStreamOutput,
    Unit,
)
from smithy_aws_event_stream.events import Event
from smithy_cbor import CBORCodec
from smithy_core import URI
from smithy_http.aio.crt import (
    AWSCRTHTTPClient,
    AWSCRTHTTPClientConfig,
)

from ._h2_server import H2BidiServer, ServerStream

_CODEC = CBORCodec()

# The scripted game. Each entry is (command text, whether Simon ordered it). A
# well-behaved client MOVES (echoes the action) on the ordered ones and PASSES on
# the rest. The action is the command text with any "simon says " prefix stripped.
_SIMON_SAYS = "simon says "
_SCRIPT: list[str] = [
    "simon says touch your nose",
    "jump",
    "simon says raise your left hand",
    "simon says spin around",
    "clap twice",
    "sit down",
    "simon says take one step forward",
]


def _action(command: str) -> str:
    return command.removeprefix(_SIMON_SAYS)


def _ordered(command: str) -> bool:
    return command.startswith(_SIMON_SAYS)


def _simon_referee() -> "tuple[object, list[str]]":
    """Build the server-side referee and the list it records the client's moves in.

    The referee sends the initial-response, then one command per turn, validating the
    client's reply to the previous command before issuing the next. ``moves`` ends up
    holding one entry per turn: the moved action, or ``"<pass>"``.
    """
    moves: list[str] = []
    state = {"turn": -1}

    async def referee(frame: Event | None, stream: ServerStream) -> bool:
        turn = state["turn"]

        if frame is None:
            # Open the game: initial-response, then the first command.
            stream.send(
                "initial-response",
                _CODEC.serialize(shape=TradeEventStreamOutput(greeting="lets play")),
            )
            state["turn"] = 0
            stream.send("alpha", _CODEC.serialize(shape=Alpha(id=_SCRIPT[0])))
            return False

        # A client frame is the reply to command `turn`. alpha = a move carrying the
        # action id; beta = a pass. Record it, then issue the next command or finish.
        event_type = str(frame.message.headers.get(":event-type"))
        if event_type == "alpha":
            deser = _CODEC.create_deserializer(frame.message.payload)
            moves.append(Alpha.deserialize(deser).id or "")
        elif event_type == "beta":
            moves.append("<pass>")
        else:
            moves.append(f"<unexpected:{event_type}>")

        turn += 1
        state["turn"] = turn
        if turn >= len(_SCRIPT):
            stream.end()
            return True
        stream.send("alpha", _CODEC.serialize(shape=Alpha(id=_SCRIPT[turn])))
        return False

    return referee, moves


async def _client(server: H2BidiServer) -> tuple[MyHandwrittenModel, AWSCRTHTTPClient]:
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


async def test_simon_says_duplex() -> None:
    referee, moves = _simon_referee()
    async with H2BidiServer(referee) as server:
        client, transport = await _client(server)

        stream = await client.trade_event_stream(
            TradeEventStreamInput(session_id="player-1")
        )
        output, output_stream = await stream.await_output()
        assert output.greeting == "lets play"

        # Player loop: for each command Simon streams, move iff ordered, else pass.
        async for command in _commands(output_stream):
            if _ordered(command):
                await stream.input_stream.send(
                    TradeEventsAlpha(value=Alpha(id=_action(command)))
                )
            else:
                await stream.input_stream.send(TradeEventsBeta(value=Unit()))
        await stream.input_stream.close()

        await transport.close()

    expected = [_action(cmd) if _ordered(cmd) else "<pass>" for cmd in _SCRIPT]
    assert moves == expected
    # Every ordered command was obeyed and no pass leaked a move onto the wire.
    assert [m for m in moves if m != "<pass>"] == [
        _action(cmd) for cmd in _SCRIPT if _ordered(cmd)
    ]


async def _commands(output_stream: AsyncIterator[object]) -> AsyncIterator[str]:
    async for event in output_stream:
        assert isinstance(event, TradeEventsAlpha)
        yield event.value.id or ""
