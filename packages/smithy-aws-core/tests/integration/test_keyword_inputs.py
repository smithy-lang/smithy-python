#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""End-to-end keyword operation inputs through a generated client.

Drives the generated restJson1 client (``codegen-output/rest-json-1``), in both
modes, with a stub transport that records each request and returns a canned
response. Checks what a caller writes, what interceptors receive, and what goes
on the wire.
"""

import inspect
import json
import os
import uuid
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any, cast
from urllib.parse import parse_qs

import pytest

pytest.importorskip("restjson")

from restjson import models
from restjson.aio.client import AsyncRestJsonProtocolClient
from restjson.aio.config import AsyncRestJsonProtocolConfig
from restjson.client import RestJsonProtocolClient
from restjson.config import RestJsonProtocolConfig
from restjson.models import (
    AsyncStreamingTraitsInputParams,
    JsonListsInput,
    JsonListsInputParams,
    JsonUnionsInput,
    MyUnionStructureValue,
    MyUnionUnknown,
    StreamingTraitsInputParams,
    StructureListMember,
    TopLevel,
)
from smithy_core.aio.utils import read_streaming_blob_async
from smithy_core.interceptors import Interceptor
from smithy_core.utils import read_streaming_blob
from smithy_http import HTTPResponse, tuples_to_fields


class _Transport:
    """Records every request and answers each with the same JSON body."""

    TIMEOUT_EXCEPTIONS = ()

    def __init__(self, response: bytes = b"{}") -> None:
        self.requests: list[Any] = []
        self.bodies: list[bytes] = []
        # The statuses of the first responses; every later one is a 200.
        self.statuses: list[int] = []
        self._response = response

    def send(self, request: Any, *, request_config: Any = None) -> HTTPResponse:
        self.requests.append(request)
        self.bodies.append(read_streaming_blob(request.body))
        return self._respond()

    def _respond(self) -> HTTPResponse:
        status = self.statuses.pop(0) if self.statuses else 200
        return HTTPResponse(
            status=status,
            fields=tuples_to_fields([("content-type", "application/json")]),
            body=self._response if status == 200 else b'{"__type": "Unmodeled"}',
        )


class _AsyncTransport(_Transport):
    async def send(  # pyright: ignore[reportIncompatibleMethodOverride]
        self, request: Any, *, request_config: Any = None
    ) -> HTTPResponse:
        self.requests.append(request)
        self.bodies.append(await read_streaming_blob_async(request.body))
        return self._respond()


class _Recorder(Interceptor[Any, Any, Any, Any]):
    """Records the input every call hands to the interceptors."""

    def __init__(self) -> None:
        self.inputs: list[Any] = []

    def __deepcopy__(self, memo: dict[int, Any]) -> "_Recorder":
        # The client copies its config; keep recording into this instance.
        return self

    def read_before_execution(self, context: Any) -> None:
        self.inputs.append(context.request)


@pytest.fixture(params=[True, False], ids=["sync", "async"])
def sync(request: pytest.FixtureRequest) -> bool:
    return request.param


@pytest.fixture(autouse=True)
def _clean_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    # Keep the host's AWS settings from changing how the client is configured.
    for name in list(os.environ):
        if name.startswith("AWS_"):
            monkeypatch.delenv(name)


async def _client(
    sync: bool, tmp_path: Path, response: bytes = b"{}"
) -> tuple[Any, _Transport, _Recorder]:
    recorder = _Recorder()
    missing = str(tmp_path / "missing")
    config: dict[str, Any] = {
        "config_file_path": missing,
        "credentials_file_path": missing,
        "region": "us-west-2",
        "endpoint_uri": "https://example.com",
        "aws_access_key_id": "AKID",
        "aws_secret_access_key": "secret",
        "interceptors": [recorder],
    }
    if sync:
        transport = _Transport(response)
        client: Any = RestJsonProtocolClient(
            config=RestJsonProtocolConfig.resolve(transport=transport, **config)
        )
    else:
        transport = _AsyncTransport(response)
        client = AsyncRestJsonProtocolClient(
            config=await AsyncRestJsonProtocolConfig.resolve(
                transport=transport, **config
            )
        )
    return client, transport, recorder


async def _result(call: Any) -> Any:
    """The result of an operation call made on either client."""
    return await call if inspect.isawaitable(call) else call


def _sent_tokens(transport: _Transport) -> list[str]:
    """The idempotency token of each request sent, which is its whole query."""
    tokens: list[str] = []
    for request in transport.requests:
        raw: str = request.destination.query
        query = parse_qs(raw, keep_blank_values=True)
        assert list(query) == ["token"]
        (token,) = query["token"]
        tokens.append(token)
    return tokens


async def test_inline_dictionaries_are_sent_and_reach_interceptors_as_models(
    sync: bool, tmp_path: Path
) -> None:
    client, transport, recorder = await _client(sync, tmp_path)
    model = StructureListMember(a="3", b="4")

    await _result(
        client.json_lists(
            string_list=("foo", "bar"),
            structure_list=[{"a": "1", "b": "2"}, model],
        )
    )

    assert json.loads(transport.bodies[0]) == {
        "stringList": ["foo", "bar"],
        "myStructureList": [
            {"value": "1", "other": "2"},
            {"value": "3", "other": "4"},
        ],
    }
    (received,) = recorder.inputs
    assert type(received) is JsonListsInput
    assert received.string_list == ["foo", "bar"]
    assert received.structure_list == [StructureListMember(a="1", b="2"), model]
    assert received.structure_list[1] is model


async def test_union_is_a_single_key_dictionary(sync: bool, tmp_path: Path) -> None:
    client, transport, recorder = await _client(sync, tmp_path)

    await _result(client.json_unions(contents={"structure_value": {"hi": "hello"}}))

    assert json.loads(transport.bodies[0]) == {
        "contents": {"structureValue": {"hi": "hello"}}
    }
    (received,) = recorder.inputs
    assert type(received) is JsonUnionsInput
    assert type(received.contents) is MyUnionStructureValue


async def test_operation_without_members_takes_no_arguments(
    sync: bool, tmp_path: Path
) -> None:
    client, transport, recorder = await _client(sync, tmp_path)

    await _result(client.no_input_and_no_output())

    assert len(transport.requests) == 1
    assert type(recorder.inputs[0]).__name__ == "NoInputAndNoOutputInput"


async def test_response_model_is_reused_in_a_request(
    sync: bool, tmp_path: Path
) -> None:
    client, transport, recorder = await _client(
        sync, tmp_path, b'{"myStructureList": [{"value": "1", "other": "2"}]}'
    )
    response = await _result(client.json_lists())
    returned = response.structure_list[0]
    before = repr(response)

    await _result(client.json_lists(structure_list=[returned, {"a": "3"}]))

    assert recorder.inputs[1].structure_list[0] is returned
    assert repr(response) == before
    assert json.loads(transport.bodies[1]) == {
        "myStructureList": [{"value": "1", "other": "2"}, {"value": "3"}]
    }


async def test_params_dictionary_unpacks_into_the_call(
    sync: bool, tmp_path: Path
) -> None:
    client, transport, _ = await _client(sync, tmp_path)
    # At runtime the dictionary form is plain dict.
    assert JsonListsInputParams is dict
    params: JsonListsInputParams = {"string_list": ["a"], "integer_list": [1]}

    await _result(client.json_lists(**params))

    assert json.loads(transport.bodies[0]) == {"stringList": ["a"], "integerList": [1]}


async def test_none_is_the_same_as_omitting_a_member(
    sync: bool, tmp_path: Path
) -> None:
    client, transport, _ = await _client(sync, tmp_path)

    await _result(client.json_lists(string_list=None, structure_list=[{"a": None}]))

    assert json.loads(transport.bodies[0]) == {"myStructureList": [{}]}


async def test_required_member_must_be_set(sync: bool, tmp_path: Path) -> None:
    client, transport, _ = await _client(sync, tmp_path)

    with pytest.raises(TypeError, match="hello"):
        await _result(client.constant_query_string())
    with pytest.raises(TypeError, match="missing required member 'hello'"):
        await _result(client.constant_query_string(hello=None))

    assert transport.requests == []


async def test_unset_idempotency_token_is_generated_for_each_call(
    sync: bool, tmp_path: Path
) -> None:
    client, transport, recorder = await _client(sync, tmp_path)

    await _result(client.query_idempotency_token_auto_fill())
    await _result(client.query_idempotency_token_auto_fill(token=None))

    # The token is generated once the interceptors that may change the input have
    # run, so the first hook sees it as the caller left it.
    assert [received.token for received in recorder.inputs] == [None, None]
    # Each call is sent with a generated token of its own.
    first, second = _sent_tokens(transport)
    assert uuid.UUID(first).version == 4
    assert uuid.UUID(second).version == 4
    assert first != second


async def test_generated_idempotency_token_is_the_same_on_every_attempt(
    sync: bool, tmp_path: Path
) -> None:
    client, transport, recorder = await _client(sync, tmp_path)
    # A request timeout is retried.
    transport.statuses = [408, 408]

    await _result(client.query_idempotency_token_auto_fill())

    (received,) = recorder.inputs
    assert received.token is None
    # All three attempts are sent with the one token generated for the call.
    sent = _sent_tokens(transport)
    assert uuid.UUID(sent[0]).version == 4
    assert sent == [sent[0]] * 3


@pytest.mark.parametrize("token", ["t-1", ""])
async def test_given_idempotency_token_is_sent_unchanged(
    sync: bool, tmp_path: Path, token: str
) -> None:
    client, transport, recorder = await _client(sync, tmp_path)

    await _result(client.query_idempotency_token_auto_fill(token=token))

    assert recorder.inputs[0].token == token
    assert transport.requests[0].destination.query == f"token={token}"


async def test_streaming_blob_is_sent_unchanged(sync: bool, tmp_path: Path) -> None:
    client, transport, _ = await _client(sync, tmp_path)

    await _result(client.streaming_traits(foo="Foo", blob=b"blobby blob blob"))

    assert transport.bodies[0] == b"blobby blob blob"
    assert transport.requests[0].fields["x-foo"].as_string() == "Foo"


async def test_streaming_request_unpacks_from_the_form_each_client_accepts(
    tmp_path: Path,
) -> None:
    # The clients are typed here so a type checker checks the unpacked calls too.
    sync_client: RestJsonProtocolClient
    sync_client, sync_transport, _ = await _client(True, tmp_path)
    async_client: AsyncRestJsonProtocolClient
    async_client, async_transport, _ = await _client(False, tmp_path)

    # The plain form holds a body a sync client can send, so either client takes it.
    request: StreamingTraitsInputParams = {"foo": "Foo", "blob": b"body"}
    sync_client.streaming_traits(**request)
    await async_client.streaming_traits(**request)

    async def chunks() -> AsyncIterator[bytes]:
        yield b"async "
        yield b"body"

    # Only the async client can send an async stream, and only its form holds one.
    assert AsyncStreamingTraitsInputParams is dict
    async_request: AsyncStreamingTraitsInputParams = {"foo": "Foo", "blob": chunks()}
    await async_client.streaming_traits(**async_request)

    assert sync_transport.bodies == [b"body"]
    assert async_transport.bodies == [b"body", b"async body"]


async def test_whole_input_object_is_not_accepted(sync: bool, tmp_path: Path) -> None:
    client, transport, _ = await _client(sync, tmp_path)

    with pytest.raises(TypeError):
        await _result(client.json_lists(JsonListsInput(string_list=["a"])))

    assert transport.requests == []


def _invalid_calls() -> list[tuple[str, dict[str, Any], str]]:
    dialog: Any = {"language": "en"}
    return [
        (
            "json_lists",
            {"string_list": "abc"},
            r"Invalid JsonLists input at string_list: expected a list, got str",
        ),
        (
            "json_lists",
            {"structure_list": [{"a": "1"}, {"c": "2"}]},
            r"at structure_list\[1\]: unknown member 'c'",
        ),
        (
            "json_lists",
            {"structure_list": [JsonListsInput()]},
            r"at structure_list\[0\]: expected StructureListMember or a dict, "
            r"got JsonListsInput",
        ),
        # A union dictionary has exactly one key, even if another's value is None.
        (
            "json_unions",
            {"contents": {"string_value": "a", "number_value": None}},
            r"at contents: a MyUnion dict must have exactly one key, got 2",
        ),
        # Models are passed through as they are, but not unchecked.
        (
            "json_unions",
            {"contents": MyUnionUnknown(tag="new")},
            r"at contents: an unknown MyUnion variant cannot be sent",
        ),
        (
            "operation_with_nested_structure",
            {"top_level": TopLevel(dialog=cast(Any, None))},
            r"at top_level: missing required member 'dialog'",
        ),
        (
            "operation_with_nested_structure",
            {"top_level": TopLevel(dialog=dialog)},
            r"at top_level.dialog: expected Dialog, got dict",
        ),
    ]


@pytest.mark.parametrize(("operation", "members", "message"), _invalid_calls())
async def test_invalid_arguments_fail_before_setup_and_interceptors(
    sync: bool,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    operation: str,
    members: dict[str, Any],
    message: str,
) -> None:
    # A client with no config resolves one on its first call. Invalid arguments
    # must fail before that happens.
    def resolve(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("configuration was resolved")

    monkeypatch.setattr(RestJsonProtocolConfig, "resolve", resolve)
    monkeypatch.setattr(AsyncRestJsonProtocolConfig, "resolve", resolve)
    client: Any = RestJsonProtocolClient() if sync else AsyncRestJsonProtocolClient()

    with pytest.raises(TypeError, match=message):
        await _result(getattr(client, operation)(**members))

    # With a config, neither plugins nor interceptors see the invalid call.
    monkeypatch.undo()
    client, transport, recorder = await _client(sync, tmp_path)
    applied: list[Any] = []
    with pytest.raises(TypeError, match=message):
        await _result(getattr(client, operation)(**members, plugins=[applied.append]))
    assert applied == []
    assert recorder.inputs == []
    assert transport.requests == []


async def test_model_holding_a_dictionary_is_left_as_the_caller_built_it(
    sync: bool, tmp_path: Path
) -> None:
    client, _, _ = await _client(sync, tmp_path)
    dialog: Any = {"language": "en"}
    top_level = TopLevel(dialog=dialog)

    with pytest.raises(TypeError, match="expected Dialog, got dict"):
        await _result(client.operation_with_nested_structure(top_level=top_level))

    assert top_level.dialog is dialog
    assert dialog == {"language": "en"}


def test_dictionary_forms_are_importable_without_building_models() -> None:
    assert models.StructureListMemberParams is dict
    assert models.MyUnionParams is dict
    assert models.MyUnionStructureValueParams is dict
    # The prelude's Unit is a union variant here, and has no schema of its own.
    assert models.UnitParams is dict
    with pytest.raises(AttributeError):
        models.NotAShapeParams
