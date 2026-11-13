#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from io import BytesIO
from types import SimpleNamespace
from typing import Any

import pytest

pytest.importorskip("restjson")

from restjson.aio.client import AsyncRestJsonProtocolClient
from restjson.client import RestJsonProtocolClient
from restjson.config import RestJsonProtocolConfig
from restjson.models import (
    AllQueryStringTypesInput,
    SimpleScalarPropertiesInput,
    StreamingTraitsInput,
)
from smithy_core.utils import read_streaming_blob
from smithy_http.urllib3 import Urllib3HTTPClient
from smithy_test import HTTPMockError, HTTPMockMismatchError, mock


def _client() -> RestJsonProtocolClient:
    return RestJsonProtocolClient(RestJsonProtocolConfig.resolve(region="us-west-2"))


def _call(client: RestJsonProtocolClient, foo: str = "bar") -> Any:
    return client.simple_scalar_properties(
        SimpleScalarPropertiesInput(foo=foo, string_value="value")
    )


def test_matches_every_component_and_responds() -> None:
    client = _client()
    controller = mock(client)

    def has_string_value(body: bytes) -> None:
        assert b'"stringValue":"value"' in body

    controller.expect_request(
        method="PUT",
        scheme="https",
        hostname="/^restjson\\.us-west-2\\./",
        path="/SimpleScalarProperties",
        headers={"X-Foo": "bar", "Content-Type": lambda v: v.startswith("app")},
        body=has_string_value,
    ).respond_with(headers={"X-Foo": "response"}, body='{"stringValue": "hi"}')

    output = client.simple_scalar_properties(
        SimpleScalarPropertiesInput(foo="bar", string_value="value")
    )

    assert output.foo == "response"
    assert output.string_value == "hi"
    assert len(controller.requests) == 1
    assert controller.requests[0].body == b'{"stringValue":"value"}'


def test_responds_with_a_stream() -> None:
    client = _client()
    mock(client).expect_request().respond_with(body=BytesIO(b"streamed"))

    output = client.streaming_traits(StreamingTraitsInput(blob=b""))

    assert read_streaming_blob(output.blob) == b"streamed"


def test_matches_query_entries() -> None:
    client = _client()
    controller = mock(client)
    controller.expect_request(
        query={"String": "Hello there", "StringList": "a,b,c"}
    ).respond_with()

    client.all_query_string_types(
        AllQueryStringTypesInput(
            query_string="Hello there", query_string_list=["a", "b", "c"]
        )
    )


def test_returns_none_without_response() -> None:
    client = _client()
    mock(client).expect_request(path="/SimpleScalarProperties")

    assert _call(client) is None


def test_responds_in_turn_then_repeats_last() -> None:
    client = _client()
    mock(client).expect_request().times(4).respond_with(
        headers={"X-Foo": "1"}
    ).respond_with(headers={"X-Foo": "2"})

    assert [_call(client).foo for _ in range(4)] == ["1", "2", "2", "2"]


def test_matches_expectations_in_order_then_repeats_last() -> None:
    client = _client()
    controller = mock(client)
    controller.expect_request(headers={"X-Foo": "a"}).times(2)
    controller.expect_request(headers={"X-Foo": "b"})

    for foo in ["a", "a", "b", "b", "b"]:
        assert _call(client, foo) is None
    with pytest.raises(HTTPMockMismatchError, match="Request 6 didn't match"):
        _call(client, "a")


def test_raises_without_expectations() -> None:
    client = _client()
    mock(client)

    with pytest.raises(HTTPMockError, match="no requests were expected"):
        _call(client)


def test_reports_every_mismatch() -> None:
    client = _client()
    mock(client).expect_request(
        method="GET",
        path="/^\\/Other/",
        headers={"X-Missing": "value"},
        body=lambda body: False,
    )

    with pytest.raises(HTTPMockMismatchError) as error:
        _call(client)

    message = str(error.value)
    assert "method: expected 'GET', got 'PUT'" in message
    assert "path: expected" in message
    assert "headers['X-Missing']: missing" in message
    assert "body: expected" in message


def test_reports_matcher_errors() -> None:
    client = _client()

    def fails(body: bytes) -> None:
        raise AssertionError("bad body")

    mock(client).expect_request(body=fails)

    with pytest.raises(HTTPMockMismatchError, match="bad body") as error:
        _call(client)
    assert isinstance(error.value.__cause__, AssertionError)


def test_replaces_credentials() -> None:
    config = RestJsonProtocolConfig.resolve(
        region="us-west-2", aws_access_key_id="real", aws_secret_access_key="real"
    )
    client = RestJsonProtocolClient(config)
    mock(client).expect_request(
        headers={
            "Authorization": "/Credential=HTTP_MOCK//",
            "X-Amz-Security-Token": "HTTP_MOCK",
        }
    )

    _call(client)

    assert config.aws_access_key_id == "real"
    assert client._config.aws_access_key_id == "HTTP_MOCK"  # pyright: ignore[reportPrivateUsage]


def test_replaces_credentials_from_the_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AWS_REGION", "us-west-2")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "real")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "real")
    client = RestJsonProtocolClient()
    mock(client).expect_request(headers={"Authorization": "/Credential=HTTP_MOCK//"})

    _call(client)


def test_takes_over_a_client_after_setup() -> None:
    client = _client()
    client._ensure_setup()  # pyright: ignore[reportPrivateUsage]
    mock(client).expect_request(headers={"Authorization": "/Credential=HTTP_MOCK//"})

    assert _call(client) is None


def test_ignores_transports_from_operation_plugins() -> None:
    client = _client()
    mock(client).expect_request()

    def plugin(config: RestJsonProtocolConfig) -> None:
        config.transport = Urllib3HTTPClient()

    assert (
        client.simple_scalar_properties(SimpleScalarPropertiesInput(), plugins=[plugin])
        is None
    )


def test_exits_when_every_expectation_is_met() -> None:
    client = _client()
    with mock(client) as controller:
        controller.expect_request(headers={"X-Foo": "a"}).times(2)
        controller.expect_request(headers={"X-Foo": "b"}).times(2)

        for foo in ["a", "a", "b", "b", "b"]:
            _call(client, foo)


def test_raises_on_exit_with_unmet_expectations() -> None:
    client = _client()
    with pytest.raises(HTTPMockMismatchError) as error:
        with mock(client) as controller:
            controller.expect_request().times(2)
            controller.expect_request().times(3)
            controller.expect_request()

            for _ in range(3):
                _call(client)

    message = str(error.value)
    assert "Expectation 2: matched 1 of 3 requests" in message
    assert "Expectation 3: matched 0 of 1 requests" in message
    assert "Expectation 1" not in message


def test_reports_the_error_raised_in_the_block() -> None:
    client = _client()
    with pytest.raises(ValueError, match="in the block"):
        with mock(client) as controller:
            controller.expect_request()
            raise ValueError("in the block")


def test_allows_unmet_expectations_without_a_context_manager() -> None:
    mock(_client()).expect_request().times(2)


def test_rejects_an_async_client() -> None:
    client = AsyncRestJsonProtocolClient()

    with pytest.raises(TypeError, match="mock_async"):
        mock(client)  # type: ignore[arg-type]


def test_rejects_a_client_with_changed_internals() -> None:
    class Changed(RestJsonProtocolClient):
        def _build_call(self, input: Any, operation: Any, **kwargs: Any) -> Any:
            return super()._build_call(input, operation, **kwargs)

    with pytest.raises(TypeError, match="_build_call takes"):
        mock(Changed(RestJsonProtocolConfig.resolve(region="us-west-2")))


def test_rejects_a_config_with_partial_aws_credentials() -> None:
    client = _client()
    client._config = SimpleNamespace(  # pyright: ignore[reportPrivateUsage, reportAttributeAccessIssue]
        transport=None, aws_credentials_identity_resolver=None
    )

    with pytest.raises(TypeError, match="AWS credential fields"):
        mock(client)
