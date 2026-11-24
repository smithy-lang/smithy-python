#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import shutil
from pathlib import Path

import pytest

pytest.importorskip("restjson")

from restjson.aio.client import AsyncRestJsonProtocolClient
from restjson.aio.config import AsyncRestJsonProtocolConfig
from restjson.client import RestJsonProtocolClient
from restjson.models import SimpleScalarPropertiesInput, StreamingTraitsInput
from smithy_core.aio.utils import read_streaming_blob_async
from smithy_http.aio.testing import AsyncMockHTTPClient
from smithy_test import HTTPMockError, HTTPRecordError
from smithy_test.aio import instrument_async

_JSON = [("Content-Type", "application/json")]


def _live(*responses: tuple[int, list[tuple[str, str]], bytes]) -> AsyncMockHTTPClient:
    transport = AsyncMockHTTPClient()
    for status, headers, body in responses:
        transport.add_response(status, headers, body)
    return transport


async def _client(
    transport: AsyncMockHTTPClient | None = None,
) -> AsyncRestJsonProtocolClient:
    return AsyncRestJsonProtocolClient(
        await AsyncRestJsonProtocolConfig.resolve(
            region="us-west-2",
            aws_access_key_id="real",
            aws_secret_access_key="real",
            **({"transport": transport} if transport else {}),
        )
    )


async def _scalar(client: AsyncRestJsonProtocolClient) -> str | None:
    output = await client.simple_scalar_properties(
        SimpleScalarPropertiesInput(string_value="value")
    )
    return output.string_value


async def _stream(client: AsyncRestJsonProtocolClient) -> bytes:
    output = await client.streaming_traits(StreamingTraitsInput(blob=b""))
    assert output.blob is not None
    return await read_streaming_blob_async(output.blob)


async def test_records_and_replays_by_operation(tmp_path: Path) -> None:
    path = tmp_path / "recording.py"
    live = await _client(
        _live(
            (200, _JSON, b'{"stringValue": "first"}'),
            (200, [], b"payload"),
            (200, _JSON, b'{"stringValue": "second"}'),
        )
    )
    async with live:
        async with await instrument_async(live, path=path, mode="record"):
            assert await _scalar(live) == "first"
            assert await _stream(live) == b"payload"
            assert await _scalar(live) == "second"

    replayed = await _client()
    async with replayed:
        async with await instrument_async(replayed, path=path, mode="playback"):
            assert await _stream(replayed) == b"payload"
            assert await _scalar(replayed) == "first"
            assert await _scalar(replayed) == "second"


async def test_record_keeps_the_stream_readable(tmp_path: Path) -> None:
    client = await _client(_live((200, [], b"payload")))

    async with client:
        async with await instrument_async(
            client, path=tmp_path / "recording.py", mode="record"
        ):
            output = await client.streaming_traits(StreamingTraitsInput(blob=b""))

        assert output.blob is not None
        assert not isinstance(output.blob, bytes)
        assert await read_streaming_blob_async(output.blob) == b"payload"


async def test_mode_chooses_record_or_playback(tmp_path: Path) -> None:
    path = tmp_path / "recording.py"
    live = await _client(_live((200, _JSON, b'{"stringValue": "live"}')))
    async with live:
        async with await instrument_async(live, path=path, mode="record"):
            assert await _scalar(live) == "live"

    replayed = await _client()
    async with replayed:
        async with await instrument_async(replayed, path=path, mode="playback"):
            assert await _scalar(replayed) == "live"
            with pytest.raises(HTTPMockError, match="call 2 of"):
                await _scalar(replayed)


async def test_replay_without_a_recording_says_how_to_record(tmp_path: Path) -> None:
    async with await _client() as client:
        with pytest.raises(HTTPRecordError, match="SMITHY_PYTHON_TEST_MODE=record"):
            await instrument_async(
                client, path=tmp_path / "missing.py", mode="playback"
            )


async def test_rejects_an_event_stream_response(tmp_path: Path) -> None:
    headers = [("Content-Type", "application/vnd.amazon.eventstream")]
    live = await _client(_live((200, headers, b"")))

    async with live:
        with pytest.raises(HTTPRecordError, match="event stream"):
            async with await instrument_async(
                live, path=tmp_path / "recording.py", mode="record"
            ):
                await _scalar(live)


async def test_rejects_a_sync_client() -> None:
    with pytest.raises(TypeError, match=r"smithy_test\.instrument\(\)"):
        await instrument_async(
            RestJsonProtocolClient(), path=Path("x.py"), mode="record"
        )  # type: ignore[arg-type]


async def test_default_path_works_when_awaited(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SMITHY_PYTHON_TEST_MODE", "record")
    live = await _client(_live((200, _JSON, b'{"stringValue": "x"}')))
    expected = (
        Path(__file__).parent
        / "recordings"
        / "test_default_path_works_when_awaited"
        / "rest_json_protocol.py"
    )

    try:
        async with live:
            async with await instrument_async(live):
                assert await _scalar(live) == "x"
        assert expected.exists()
    finally:
        shutil.rmtree(expected.parent.parent, ignore_errors=True)
