#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from io import BytesIO

import pytest

pytest.importorskip("my_handwritten_model")
pytest.importorskip("smithy_cbor")

from my_handwritten_model import models
from my_handwritten_model.aio.client import AsyncMyHandwrittenModel
from my_handwritten_model.aio.config import AsyncConfig
from smithy_aws_event_stream.events import Event, EventMessage
from smithy_cbor import CBORCodec
from smithy_core.serializers import SerializeableShape
from smithy_test import HTTPMockError, HTTPMockMismatchError
from smithy_test.aio import mock_async


async def test_duplex_stream_is_answered_while_the_client_sends() -> None:
    async with _client() as client:
        async with await mock_async(client) as controller:
            controller.expect_request(
                path="/service/MyHandwrittenModel/operation/TradeEventStream",
                body=lambda body: _event_types(body) == ["initial-request", "alpha"],
            ).respond_with(
                headers=_EVENT_STREAM_HEADERS,
                body=_frame(
                    "initial-response", models.TradeEventStreamOutput(greeting="hi")
                )
                + _frame("alpha", models.Alpha(id="from-service")),
            )

            async with await client.trade_event_stream(
                models.TradeEventStreamInput(session_id="session")
            ) as stream:
                await stream.input_stream.send(
                    models.TradeEventsAlpha(value=models.Alpha(id="from-client"))
                )
                output, events = await stream.await_output()
                received = [event async for event in events]

    assert output.greeting == "hi"
    assert received == [models.TradeEventsAlpha(value=models.Alpha(id="from-service"))]
    assert _event_types(controller.requests[0].body) == ["initial-request", "alpha"]


async def test_duplex_stream_closes_before_its_output_is_awaited() -> None:
    async with _client() as client:
        async with await mock_async(client) as controller:
            controller.expect_request().respond_with(
                headers=_EVENT_STREAM_HEADERS,
                body=_frame("initial-response", models.TradeEventStreamOutput()),
            )

            async with await client.trade_event_stream(
                models.TradeEventStreamInput()
            ) as stream:
                await stream.input_stream.send(
                    models.TradeEventsBeta(value=models.Unit())
                )

    assert _event_types(controller.requests[0].body) == ["initial-request", "beta"]


async def test_input_stream() -> None:
    async with _client() as client:
        async with await mock_async(client) as controller:
            controller.expect_request(
                body=lambda body: _event_types(body) == ["initial-request", "log"]
            ).respond_with(
                headers={**_EVENT_STREAM_HEADERS, "content-type": "application/cbor"},
                body=_CODEC.serialize(models.PublishEventsOutput(event_count=1)),
            )

            async with await client.publish_events(
                models.PublishEventsInput(channel="channel")
            ) as stream:
                await stream.input_stream.send(
                    models.PublishEventStreamLog(value=models.LogEvent(message="hi"))
                )
                await stream.input_stream.close()
                output = await stream.await_output()

    assert output.event_count == 1


async def test_output_stream() -> None:
    async with _client() as client:
        async with await mock_async(client) as controller:
            controller.expect_request(
                body=lambda body: b"channel" in body
            ).respond_with(
                headers=_EVENT_STREAM_HEADERS,
                body=_frame(
                    "initial-response",
                    models.SubscribeToEventsOutput(subscription_id="subscription"),
                )
                + _frame("notification", models.NotificationEvent(topic="topic")),
            )

            async with await client.subscribe_to_events(
                models.SubscribeToEventsInput(channel="channel")
            ) as stream:
                received = [event async for event in stream.output_stream]

    assert stream.output.subscription_id == "subscription"
    assert received == [
        models.SubscribeEventStreamNotification(
            value=models.NotificationEvent(topic="topic")
        )
    ]


async def test_reports_a_stream_body_mismatch_on_exit() -> None:
    async with _client() as client:
        with pytest.raises(HTTPMockMismatchError, match="Request 1 didn't match"):
            async with await mock_async(client) as controller:
                controller.expect_request(
                    body=lambda body: "gamma" in _event_types(body)
                ).respond_with(
                    headers=_EVENT_STREAM_HEADERS,
                    body=_frame("initial-response", models.TradeEventStreamOutput()),
                )

                async with await client.trade_event_stream(
                    models.TradeEventStreamInput()
                ) as stream:
                    await stream.input_stream.send(
                        models.TradeEventsBeta(value=models.Unit())
                    )


async def test_reports_an_unclosed_stream_on_exit() -> None:
    async with _client() as client:
        with pytest.raises(HTTPMockMismatchError, match="wasn't closed"):
            async with await mock_async(client) as controller:
                controller.expect_request().respond_with(
                    headers=_EVENT_STREAM_HEADERS,
                    body=_frame("initial-response", models.TradeEventStreamOutput()),
                )

                stream = await client.trade_event_stream(models.TradeEventStreamInput())
                await stream.await_output()


async def test_raises_when_a_stream_has_no_response() -> None:
    async with _client() as client:
        controller = await mock_async(client)
        controller.expect_request()

        stream = await client.trade_event_stream(models.TradeEventStreamInput())
        with pytest.raises(HTTPMockError, match="respond_with"):
            await stream.await_output()
        await stream.input_stream.close()


async def test_raises_a_request_mismatch_from_the_output() -> None:
    async with _client() as client:
        controller = await mock_async(client)
        controller.expect_request(path="/elsewhere")

        stream = await client.trade_event_stream(models.TradeEventStreamInput())
        with pytest.raises(HTTPMockMismatchError, match="path"):
            await stream.await_output()
        await stream.input_stream.close()


_CODEC = CBORCodec()

_EVENT_STREAM_HEADERS = {
    "smithy-protocol": "rpc-v2-cbor",
    "content-type": "application/vnd.amazon.eventstream",
}


def _client() -> AsyncMyHandwrittenModel:
    return AsyncMyHandwrittenModel(AsyncConfig(endpoint_uri="https://localhost"))


def _frame(event_type: str, shape: SerializeableShape) -> bytes:
    return EventMessage(
        headers={
            ":message-type": "event",
            ":event-type": event_type,
            ":content-type": "application/cbor",
        },
        payload=_CODEC.serialize(shape),
    ).encode()


def _event_types(body: bytes) -> list[str]:
    source = BytesIO(body)
    types: list[str] = []
    while (event := Event.decode(source)) is not None:
        types.append(str(event.message.headers[":event-type"]))
    return types
