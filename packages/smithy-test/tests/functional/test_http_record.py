#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import base64
import shutil
from io import BytesIO
from pathlib import Path
from urllib.parse import quote

import pytest

pytest.importorskip("restjson")

from restjson.client import RestJsonProtocolClient
from restjson.config import RestJsonProtocolConfig
from restjson.models import SimpleScalarPropertiesInput, StreamingTraitsInput
from smithy_core.utils import read_streaming_blob
from smithy_http.testing.mockhttp import MockHTTPClient
from smithy_test import (
    HTTPMockError,
    HTTPMockMismatchError,
    HTTPRecordError,
    instrument,
)


def _live(*responses: tuple[int, list[tuple[str, str]], bytes]) -> MockHTTPClient:
    transport = MockHTTPClient()
    for status, headers, body in responses:
        transport.add_response(status, headers, body)
    return transport


def _client(transport: MockHTTPClient | None = None) -> RestJsonProtocolClient:
    return RestJsonProtocolClient(
        RestJsonProtocolConfig.resolve(
            region="us-west-2",
            aws_access_key_id="real",
            aws_secret_access_key="real",
            **({"transport": transport} if transport else {}),
        )
    )


_JSON = [("Content-Type", "application/json")]


def _scalar(client: RestJsonProtocolClient) -> str | None:
    return client.simple_scalar_properties(
        SimpleScalarPropertiesInput(string_value="value")
    ).string_value


def _stream(client: RestJsonProtocolClient) -> bytes:
    output = client.streaming_traits(StreamingTraitsInput(blob=b""))
    assert output.blob is not None
    return read_streaming_blob(output.blob)


def test_records_and_replays_by_operation(tmp_path: Path) -> None:
    path = tmp_path / "recording.py"
    live = _client(
        _live(
            (200, _JSON, b'{"stringValue": "first"}'),
            (200, [], b"payload"),
            (200, _JSON, b'{"stringValue": "second"}'),
        )
    )
    with instrument(live, path=path, mode="record"):
        assert _scalar(live) == "first"
        assert _stream(live) == b"payload"
        assert _scalar(live) == "second"

    replayed = _client()
    with instrument(replayed, path=path, mode="playback"):
        # A different order than the one recorded.
        assert _stream(replayed) == b"payload"
        assert _scalar(replayed) == "first"
        assert _scalar(replayed) == "second"


def test_record_keeps_the_stream_readable(tmp_path: Path) -> None:
    client = _client(_live((200, [], b"payload")))

    with instrument(client, path=tmp_path / "recording.py", mode="record"):
        output = client.streaming_traits(StreamingTraitsInput(blob=b""))

    assert output.blob is not None
    assert not isinstance(output.blob, bytes)
    assert read_streaming_blob(output.blob) == b"payload"


def test_does_not_write_when_the_block_raises(tmp_path: Path) -> None:
    path = tmp_path / "recording.py"
    client = _client(_live((200, _JSON, b"{}")))

    with pytest.raises(RuntimeError):
        with instrument(client, path=path, mode="record"):
            _scalar(client)
            raise RuntimeError

    assert not path.exists()


def test_mode_chooses_record_or_playback(tmp_path: Path) -> None:
    path = tmp_path / "recording.py"
    live = _client(_live((200, _JSON, b'{"stringValue": "live"}')))
    with instrument(live, path=path, mode="record"):
        assert _scalar(live) == "live"

    replayed = _client()
    with instrument(replayed, path=path, mode="playback"):
        assert _scalar(replayed) == "live"


def test_environment_variable_selects_the_mode(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "recording.py"
    monkeypatch.setenv("SMITHY_PYTHON_TEST_MODE", "record")
    live = _client(_live((200, _JSON, b"{}")))

    with instrument(live, path=path):
        _scalar(live)

    assert path.exists()


def test_argument_beats_the_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SMITHY_PYTHON_TEST_MODE", "record")

    with pytest.raises(HTTPRecordError, match="No recording"):
        instrument(_client(), path=tmp_path / "missing.py", mode="playback")


def test_defaults_to_playback(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SMITHY_PYTHON_TEST_MODE", raising=False)

    with pytest.raises(HTTPRecordError, match="No recording"):
        instrument(_client(), path=tmp_path / "missing.py")


@pytest.mark.parametrize("source", ["argument", "environment"])
def test_rejects_an_unknown_mode(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, source: str
) -> None:
    if source == "environment":
        monkeypatch.setenv("SMITHY_PYTHON_TEST_MODE", "replay")
        with pytest.raises(ValueError, match="SMITHY_PYTHON_TEST_MODE"):
            instrument(_client(), path=tmp_path / "x.py")
    else:
        with pytest.raises(ValueError, match="mode must be"):
            instrument(_client(), path=tmp_path / "x.py", mode="replay")  # type: ignore[arg-type]


def test_replay_without_a_recording_says_how_to_record(tmp_path: Path) -> None:
    with pytest.raises(HTTPRecordError, match="SMITHY_PYTHON_TEST_MODE=record"):
        instrument(_client(), path=tmp_path / "missing.py", mode="playback")


def test_replay_raises_past_the_recorded_calls(tmp_path: Path) -> None:
    path = tmp_path / "recording.py"
    live = _client(_live((200, _JSON, b"{}")))
    with instrument(live, path=path, mode="record"):
        _scalar(live)

    replayed = _client()
    with instrument(replayed, path=path, mode="playback"):
        _scalar(replayed)
        with pytest.raises(HTTPMockError, match="call 2 of SimpleScalarProperties"):
            _scalar(replayed)


def test_replay_raises_on_exit_when_a_call_is_missing(tmp_path: Path) -> None:
    path = tmp_path / "recording.py"
    live = _client(_live((200, _JSON, b"{}")))
    with instrument(live, path=path, mode="record"):
        _scalar(live)

    with pytest.raises(HTTPMockMismatchError, match="called 0 of 1 expected times"):
        with instrument(_client(), path=path, mode="playback"):
            pass


def test_replay_raises_for_an_unrecorded_operation(tmp_path: Path) -> None:
    path = tmp_path / "recording.py"
    live = _client(_live((200, _JSON, b"{}")))
    with instrument(live, path=path, mode="record"):
        _scalar(live)

    replayed = _client()
    with instrument(replayed, path=path, mode="playback") as controller:
        _scalar(replayed)
        with pytest.raises(HTTPMockError, match="StreamingTraits, which has no"):
            _stream(replayed)
        assert controller is not None


def test_scrubs_what_identifies_an_account(tmp_path: Path) -> None:
    path = tmp_path / "recording.py"
    body = (
        b'{"stringValue": "arn:aws:iam::210987654321:role/r AKIAABCDEFGHIJKLMNOP '
        b'10.1.2.3 a@b.com", "secretAccessKey": "hunter2"}'
    )
    live = _client(
        _live(
            (
                200,
                [*_JSON, ("x-amz-request-id", "abc"), ("Date", "now")],
                body,
            )
        )
    )
    with instrument(live, path=path, mode="record"):
        _scalar(live)

    source = path.read_text()
    for leaked in ("210987654321", "AKIAABCDEFGHIJKLMNOP", "10.1.2.3", "a@b.com"):
        assert leaked not in source
    assert "hunter2" not in source
    assert "'abc'" not in source
    assert "Date" not in source
    assert "RECORDED-REQUEST-ID" in source


def test_keeps_a_payload_covered_by_a_checksum(tmp_path: Path) -> None:
    path = tmp_path / "recording.py"
    body = b'{"stringValue": "owner 210987654321"}'
    headers = [*_JSON, ("x-amz-checksum-crc32", "AAAAAA==")]
    live = _client(_live((200, headers, body)))
    with instrument(live, path=path, mode="record"):
        _scalar(live)

    assert "210987654321" in path.read_text()


def test_rejects_an_event_stream_response(tmp_path: Path) -> None:
    headers = [("Content-Type", "application/vnd.amazon.eventstream")]
    live = _client(_live((200, headers, b"")))

    with pytest.raises(HTTPRecordError, match="event stream"):
        with instrument(live, path=tmp_path / "recording.py", mode="record"):
            _scalar(live)


def test_rejects_an_async_client(tmp_path: Path) -> None:
    from restjson.aio.client import AsyncRestJsonProtocolClient

    with pytest.raises(TypeError, match=r"instrument_async\(\)"):
        instrument(AsyncRestJsonProtocolClient(), path=tmp_path / "x.py", mode="record")  # type: ignore[arg-type]


def test_expect_operation_answers_by_operation() -> None:
    from smithy_test import mock

    client = _client()
    controller = mock(client)
    controller.expect_operation("StreamingTraits").respond_with(body=BytesIO(b"s"))
    controller.expect_operation("SimpleScalarProperties").respond_with(
        body='{"stringValue": "v"}'
    )

    assert _scalar(client) == "v"
    assert _stream(client) == b"s"


def test_writes_structured_bodies_as_indented_literals(tmp_path: Path) -> None:
    path = tmp_path / "recording.py"
    live = _client(
        _live(
            (
                200,
                [*_JSON, ("Content-Length", "31")],
                b'{"stringValue":"hi","nested":{"a":[1,2]}}',
            )
        )
    )
    with instrument(live, path=path, mode="record"):
        _scalar(live)

    source = path.read_text()
    assert 'r"""' in source
    assert '                "stringValue": "hi",' in source
    assert "'Content-Length': '" in source
    assert "'31'" not in source
    replayed = _client()
    with instrument(replayed, path=path, mode="playback"):
        assert _scalar(replayed) == "hi"


def test_writes_xml_bodies_as_indented_literals() -> None:
    from smithy_test._private.http_mock import CURRENT_OPERATION
    from smithy_test._private.http_record import ResponseLog

    xml = (
        b'<?xml version="1.0" encoding="UTF-8"?>\n<R xmlns="urn:x"><A>1</A>'
        b"<B><C>2</C></B></R>"
    )
    log = ResponseLog()
    token = CURRENT_OPERATION.set("Op")
    try:
        log.add(200, [("Content-Type", "application/xml")], xml)
    finally:
        CURRENT_OPERATION.reset(token)

    source = log.source()
    assert '<?xml version="1.0" encoding="UTF-8"?>' in source
    assert "                  <C>2</C>" in source
    namespace: dict[str, object] = {}
    exec(source, namespace)
    assert callable(namespace["install"])


_KEY_ID = "AKIAIOSFODNN7EXAMPLE"
_SECRET = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
_ACCOUNT = "987654321098"


def _signed_client(transport: MockHTTPClient) -> RestJsonProtocolClient:
    return RestJsonProtocolClient(
        RestJsonProtocolConfig.resolve(
            region="us-west-2",
            aws_access_key_id=_KEY_ID,
            aws_secret_access_key=_SECRET,
            transport=transport,
        )
    )


def test_known_credentials_never_reach_a_recording(tmp_path: Path) -> None:
    path = tmp_path / "recording.py"
    body = f'{{"stringValue": "{_KEY_ID} {_ACCOUNT}"}}'.encode()
    live = _signed_client(_live((200, [*_JSON, ("x-echo", _KEY_ID)], body)))

    with instrument(live, path=path, mode="record", redact=[_ACCOUNT]):
        _scalar(live)

    source = path.read_text()
    for value in (_KEY_ID, _ACCOUNT):
        assert value not in source


def test_refuses_a_recording_that_would_leak_a_known_value(tmp_path: Path) -> None:
    path = tmp_path / "recording.py"
    headers = [*_JSON, ("x-amz-checksum-crc32", "AAAAAA==")]
    body = f'{{"stringValue": "{_ACCOUNT}"}}'.encode()
    live = _signed_client(_live((200, headers, body)))

    with pytest.raises(HTTPRecordError, match="redact value 1") as error:
        with instrument(live, path=path, mode="record", redact=[_ACCOUNT]):
            _scalar(live)

    assert _ACCOUNT not in str(error.value)
    assert not path.exists()


@pytest.mark.parametrize(
    "leak",
    [
        ("body", _SECRET),
        ("body", _SECRET.replace("/", "\\/")),
        ("x-echo", quote(_SECRET, safe="")),
        ("body", base64.b64encode(_SECRET.encode()).decode()),
    ],
)
def test_refuses_a_recording_that_has_the_secret_key(
    tmp_path: Path, leak: tuple[str, str]
) -> None:
    where, value = leak
    path = tmp_path / "recording.py"
    headers = list(_JSON)
    body = b"{}"
    if where == "body":
        body = f'{{"stringValue": "{value}"}}'.encode()
    else:
        headers.append((where, value))
    live = _signed_client(_live((200, headers, body)))

    with pytest.raises(HTTPRecordError, match="secret access key") as error:
        with instrument(live, path=path, mode="record"):
            _scalar(live)

    assert _SECRET not in str(error.value)
    assert not path.exists()


def test_refusal_holds_even_if_the_test_catches_the_error(tmp_path: Path) -> None:
    path = tmp_path / "recording.py"
    body = f'{{"stringValue": "{_SECRET}"}}'.encode()
    live = _signed_client(_live((200, _JSON, body), (200, _JSON, b"{}")))

    with pytest.raises(HTTPRecordError, match="secret access key"):
        with instrument(live, path=path, mode="record"):
            with pytest.raises(HTTPRecordError):
                _scalar(live)
            _scalar(live)

    assert not path.exists()


@pytest.mark.parametrize(
    ("label", "value"),
    [
        ("redact value 1", base64.b64encode(_ACCOUNT.encode()).decode()),
        ("access key ID", base64.b64encode(_KEY_ID.encode()).decode().rstrip("=")),
    ],
)
def test_refuses_what_it_can_only_replace_in_plain_text(
    tmp_path: Path, label: str, value: str
) -> None:
    path = tmp_path / "recording.py"
    body = f'{{"stringValue": "{value}"}}'.encode()
    live = _signed_client(_live((200, _JSON, body)))

    with pytest.raises(HTTPRecordError, match=label):
        with instrument(live, path=path, mode="record", redact=[_ACCOUNT]):
            _scalar(live)

    assert not path.exists()


def test_scrubs_who_a_role_session_belongs_to(tmp_path: Path) -> None:
    path = tmp_path / "recording.py"
    body = (
        b'{"stringValue": "arn:aws:sts::210987654321:assumed-role/Admin/jane-session '
        b'AROAABCDEFGHIJKLMNOPQ:jane-session arn:aws:iam::210987654321:user/jane"}'
    )
    live = _client(_live((200, _JSON, body)))

    with instrument(live, path=path, mode="record"):
        _scalar(live)

    source = path.read_text()
    assert "jane" not in source
    assert "assumed-role/Recor/recorded-ses:" not in source
    assert "assumed-role/Recor/recorded-ses " in source
    assert "AROARECORDED000000001:recorded-ses " in source
    assert "Admin" not in source


def test_replaces_accounts_with_the_approved_example_ids(tmp_path: Path) -> None:
    path = tmp_path / "recording.py"
    body = b'{"stringValue": "arn::111011101110: arn::222022202220: 111011101110"}'
    live = _client(_live((200, _JSON, body)))

    with instrument(live, path=path, mode="record"):
        _scalar(live)

    source = path.read_text()
    assert "arn::123456789012: arn::111122223333: 123456789012" in source


def test_refuses_more_accounts_than_approved_ids(tmp_path: Path) -> None:
    accounts = " ".join(f"{n:012d}" for n in range(1, 16))
    live = _client(_live((200, _JSON, f'{{"stringValue": "{accounts}"}}'.encode())))

    with pytest.raises(HTTPRecordError, match="approved example IDs"):
        with instrument(live, path=tmp_path / "recording.py", mode="record"):
            _scalar(live)


def test_replaces_uuids_with_dummies_of_the_same_length(tmp_path: Path) -> None:
    path = tmp_path / "recording.py"
    first = "0a1b2c3d-4e5f-4a6b-8c7d-123456789012"
    second = "AAAAAAAA-BBBB-4CCC-9DDD-EEEEEEEEEEEE"
    body = f'{{"stringValue": "{first} {second} {first} 210987654321"}}'.encode()
    live = _client(_live((200, _JSON, body)))

    with instrument(live, path=path, mode="record"):
        _scalar(live)

    source = path.read_text()
    dummy = "00000000-0000-4000-8000-"
    assert f"{dummy}000000000001 {dummy}000000000002 {dummy}000000000001" in source
    # The last group of a UUID is not mistaken for an account ID.
    assert "123456789012 " not in source.replace(dummy + "000000000001", "")
    assert source.count("123456789012") == 1
    assert "'Content-Length'" not in source


def test_default_path_names_the_test_and_the_client(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SMITHY_PYTHON_TEST_MODE", "record")
    live = _client(_live((200, _JSON, b"{}")))

    with instrument(live):
        _scalar(live)

    expected = (
        Path(__file__).parent
        / "recordings"
        / "test_default_path_names_the_test_and_the_client"
        / "rest_json_protocol.py"
    )
    try:
        assert expected.exists()
    finally:
        shutil.rmtree(expected.parent.parent, ignore_errors=True)


def test_default_path_needs_a_named_function() -> None:
    with pytest.raises(ValueError, match="Pass the path"):
        (lambda: instrument(_client(), mode="playback"))()


def test_recomputes_the_body_checksum_header_when_the_body_changes(
    tmp_path: Path,
) -> None:
    import zlib

    path = tmp_path / "recording.py"
    body = b'{"stringValue":"arn::210987654321:"}'
    headers = [*_JSON, ("x-amz-crc32", str(zlib.crc32(body)))]
    live = _client(_live((200, headers, body)))

    with instrument(live, path=path, mode="record"):
        _scalar(live)

    namespace: dict[str, object] = {}
    exec(path.read_text(), namespace)
    from smithy_test import HTTPMockController

    controller = HTTPMockController()
    namespace["install"](controller)  # type: ignore[operator]
    status, response_headers, response_body = controller._operations[  # pyright: ignore[reportPrivateUsage]
        "SimpleScalarProperties"
    ][0]._respond()
    crc = dict(response_headers)["x-amz-crc32"]
    assert crc == str(zlib.crc32(response_body))  # type: ignore[arg-type]
    assert status == 200


def test_does_not_take_a_timestamp_for_an_account_id(tmp_path: Path) -> None:
    path = tmp_path / "recording.py"
    body = b'{"stringValue": "1.795550537012E9 2.123456789012 acct 210987654321."}'
    live = _client(_live((200, _JSON, body)))

    with instrument(live, path=path, mode="record"):
        _scalar(live)

    source = path.read_text()
    assert "1.795550537012E9" in source or "1795550537.012" in source
    assert "2.123456789012" in source
    assert "acct 123456789012." in source
