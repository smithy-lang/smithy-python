#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""A protocol-agnostic game of Simon Says, played over a duplex event stream.

Drives a generated rpcv2 client over the real CRT HTTP/2 duplex transport against a
local HTTP/2 server (``_h2_server.H2BidiServer``) that referees the game. The test
modules supply the protocol: the generated client and its models, the payload codec,
the event payload content type, and the ``Smithy-Protocol`` header value.

The game makes the bidirectional exchange prove its own thoroughness. The server
(Simon) streams a scripted sequence of command events; each command's payload either
begins with ``simon says `` or does not. The client (the player loop) must send a
*move* event echoing the action when and only when Simon said so, and a *pass* event
otherwise. Because every turn produces exactly one client frame, the exchange is
deterministic: the referee advances one command per client frame and asserts the
client obeyed. A client that never put its events on the wire, or obeyed the wrong
commands, fails -- which a single ``initial-request``-only assertion could not catch.
"""

from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass
from types import ModuleType
from typing import Any, Literal

from smithy_aws_event_stream.events import Event
from smithy_core import URI
from smithy_core.codecs import Codec
from smithy_http.aio.crt import AWSCRTHTTPClient, AWSCRTHTTPClientConfig

from ._h2_server import H2BidiServer, ServerStream

# The scripted game. A well-behaved client MOVES (echoes the action) on the commands
# Simon ordered and PASSES on the rest. The action is the command text with any
# "simon says " prefix stripped.
SIMON_SAYS = "simon says "
SCRIPT: list[str] = [
    "simon says touch your nose",
    "jump",
    "simon says raise your left hand",
    "simon says spin around",
    "clap twice",
    "sit down",
    "simon says take one step forward",
]


@dataclass(frozen=True)
class GameProtocol:
    """Everything protocol-specific the game needs.

    ``models`` is the generated ``<module>.models`` module, which must expose the
    duplex ``TradeEventStream`` shapes (``Alpha``, ``Unit``, ``TradeEventsAlpha``,
    ``TradeEventsBeta``, ``TradeEventStreamInput``, ``TradeEventStreamOutput``).
    ``codec`` is what the referee encodes and decodes event payloads with; it must be
    configured exactly as the client protocol's payload codec. When ``None``, the
    referee uses the constructed client's own ``config.protocol.payload_codec``.
    """

    client_class: Any
    config_class: Any
    models: ModuleType
    payload_content_type: str
    smithy_protocol: str
    codec: Codec | None = None


RequestForm = Literal["keywords", "model", "params"]
"""How the game's request is passed: as keyword arguments, or whole and positionally
as the input model or its dictionary form."""

REQUEST_FORMS: tuple[RequestForm, ...] = ("keywords", "model", "params")


def action(command: str) -> str:
    return command.removeprefix(SIMON_SAYS)


def ordered(command: str) -> bool:
    return command.startswith(SIMON_SAYS)


def expected_moves() -> list[str]:
    return [action(cmd) if ordered(cmd) else "<pass>" for cmd in SCRIPT]


def simon_referee(
    models: ModuleType, codec: "Callable[[], Codec]"
) -> "tuple[Any, list[str]]":
    """Build the server-side referee and the list it records the client's moves in.

    The referee sends the initial-response, then one command per turn, validating the
    client's reply to the previous command before issuing the next. ``moves`` ends up
    holding one entry per turn: the moved action, or ``"<pass>"``. ``codec`` is
    resolved on each turn, so it may be bound after the server is started.
    """
    moves: list[str] = []
    state = {"turn": -1}

    async def referee(frame: Event | None, stream: ServerStream) -> bool:
        turn = state["turn"]
        payload_codec = codec()

        if frame is None:
            # Open the game: initial-response, then the first command.
            stream.send(
                "initial-response",
                payload_codec.serialize(
                    models.TradeEventStreamOutput(greeting="lets play")
                ),
            )
            state["turn"] = 0
            stream.send("alpha", payload_codec.serialize(models.Alpha(id=SCRIPT[0])))
            return False

        # A client frame is the reply to command `turn`. alpha = a move carrying the
        # action id; beta = a pass. Record it, then issue the next command or finish.
        event_type = str(frame.message.headers.get(":event-type"))
        if event_type == "alpha":
            deser = payload_codec.create_deserializer(frame.message.payload)
            moves.append(models.Alpha.deserialize(deser).id or "")
        elif event_type == "beta":
            moves.append("<pass>")
        else:
            moves.append(f"<unexpected:{event_type}>")

        turn += 1
        state["turn"] = turn
        if turn >= len(SCRIPT):
            stream.end()
            return True
        stream.send("alpha", payload_codec.serialize(models.Alpha(id=SCRIPT[turn])))
        return False

    return referee, moves


async def play_simon_says(
    protocol: GameProtocol, request_form: RequestForm = "keywords"
) -> None:
    """Play one full game and assert the client obeyed every command.

    ``request_form`` is how the operation's request is passed; every form starts
    the same game.
    """
    models = protocol.models
    bound: dict[str, Codec] = {}
    if protocol.codec is not None:
        bound["codec"] = protocol.codec
    referee, moves = simon_referee(models, lambda: bound["codec"])
    async with H2BidiServer(
        referee,
        payload_content_type=protocol.payload_content_type,
        smithy_protocol=protocol.smithy_protocol,
    ) as server:
        transport = AWSCRTHTTPClient(
            client_config=AWSCRTHTTPClientConfig(
                force_http_2=True, trust_store_path=str(server.ca_cert_path)
            )
        )
        config = protocol.config_class(
            endpoint_uri=URI(host=server.host, port=server.port, scheme="https"),
            transport=transport,
        )
        # Default to the codec the client itself will use for event payloads.
        bound.setdefault("codec", config.protocol.payload_codec)
        client = protocol.client_class(config)

        if request_form == "keywords":
            stream = await client.trade_event_stream(session_id="player-1")
        elif request_form == "model":
            stream = await client.trade_event_stream(
                models.TradeEventStreamInput(session_id="player-1")
            )
        else:
            stream = await client.trade_event_stream({"session_id": "player-1"})
        output, output_stream = await stream.await_output()
        assert output.greeting == "lets play"

        # Player loop: for each command Simon streams, move iff ordered, else pass.
        async for command in _commands(protocol, output_stream):
            if ordered(command):
                await stream.input_stream.send(
                    models.TradeEventsAlpha(value=models.Alpha(id=action(command)))
                )
            else:
                await stream.input_stream.send(
                    models.TradeEventsBeta(value=models.Unit())
                )
        await stream.input_stream.close()

        await transport.close()

    expected = expected_moves()
    assert moves == expected
    # Every ordered command was obeyed and no pass leaked a move onto the wire.
    assert [m for m in moves if m != "<pass>"] == [
        action(cmd) for cmd in SCRIPT if ordered(cmd)
    ]
    # The server saw the initial-request, then exactly one move/pass frame per turn.
    assert server.received_event_types == ["initial-request"] + [
        "alpha" if ordered(cmd) else "beta" for cmd in SCRIPT
    ]
    # Every frame -- including the empty-structure passes -- was encoded with the
    # protocol's codec.
    assert server.received_content_types == [protocol.payload_content_type] * len(
        server.received_event_types
    )


async def _commands(
    protocol: GameProtocol, output_stream: AsyncIterator[object]
) -> AsyncIterator[str]:
    async for event in output_stream:
        assert isinstance(event, protocol.models.TradeEventsAlpha)
        yield event.value.id or ""
