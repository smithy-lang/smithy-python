#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
# pyright: reportPrivateUsage=false
from collections.abc import Iterable
from pathlib import Path
from types import TracebackType
from typing import Any, Self

from smithy_core.aio.client import AsyncClient
from smithy_core.aio.types import AsyncBytesProvider, AsyncBytesReader
from smithy_core.aio.utils import close_async, read_streaming_blob_async
from smithy_http import HTTPResponse
from smithy_http.interfaces import HTTPRequest, HTTPRequestConfiguration

from .._private.errors import HTTPRecordError
from .._private.http_mock import take_over
from .._private.http_record import (
    RecordMode,
    ResponseLog,
    default_recording_path,
    load_installer,
    resolve_mode,
)
from .._private.scrub import TextScrubber
from ._tracking import track_operation
from .http_mock import AsyncHTTPMockController, mock_async

__all__ = ["AsyncHTTPRecorder", "instrument_async"]


async def instrument_async[C](
    client: AsyncClient[C],
    *,
    path: str | Path | None = None,
    mode: RecordMode | None = None,
    scrubbers: Iterable[TextScrubber] = (),
    redact: Iterable[str] = (),
) -> "AsyncHTTPRecorder | AsyncHTTPMockController":
    """Record a test against the live service, or play back what it recorded.

    Used as an async context manager, the same test body runs in both modes.
    Playback answers each operation from its recorded responses. Record mode writes
    them on exit.

    :param path: The recording. Defaults to ``recordings/<test function>/<client>.py``
        next to the file of the function that awaits this, such as
        ``recordings/test_list_buckets/s3.py``.
    :param mode: ``"record"`` or ``"playback"``. Defaults to the
        SMITHY_PYTHON_TEST_MODE environment variable, then to playback.
    :param scrubbers: Functions applied to recorded text after the built-in scrubbing.
    :param redact: Values, such as an account ID, that must not appear in a recording.
        They are replaced, and the recording is refused if one stays. The access key
        ID and session token that sign the requests are always treated this way.
    :raises ValueError: If the mode isn't ``record`` or ``playback``.
    :raises HTTPRecordError: If playing back and there's no recording at the path.
    :raises TypeError: If the client isn't an async client this can take over.
    """
    path = path if path is not None else default_recording_path(client, 1)
    if resolve_mode(mode) == "record":
        return _start(client, path, scrubbers, redact)
    install = load_installer(path)
    controller = await mock_async(client)
    install(controller)
    return controller


class AsyncHTTPRecorder:
    """Keeps the responses of a client taken over by :py:func:`instrument_async`.

    Used as an async context manager, it writes the recording on exit unless the block
    raised.
    """

    def __init__(
        self,
        path: str | Path | None = None,
        scrubbers: Iterable[TextScrubber] = (),
        redact: Iterable[str] = (),
    ) -> None:
        self._path = path
        self._log = ResponseLog(scrubbers, redact)
        self._transport = _AsyncRecordingTransport(self._log)

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if exc_type is None and self._path is not None:
            self.write(self._path)

    def source(self) -> str:
        """Render the recording as the Python module that replays it."""
        return self._log.source()

    def write(self, path: str | Path) -> None:
        """Write the recording to a file."""
        self._log.write(path)


def _start[C](
    client: AsyncClient[C],
    path: str | Path | None,
    scrubbers: Iterable[TextScrubber],
    redact: Iterable[str],
) -> "AsyncHTTPRecorder":
    if not isinstance(client, AsyncClient):  # pyright: ignore[reportUnnecessaryIsInstance]
        raise TypeError(
            f"instrument_async() takes an async client, got {type(client).__name__}. Use "
            "smithy_test.instrument() for sync clients."
        )
    recorder = AsyncHTTPRecorder(path, scrubbers, redact)
    take_over(client, recorder._transport, track_operation, _install)
    return recorder


class _AsyncRecordingTransport:
    """Sends requests with the transport it replaced and records the responses."""

    def __init__(self, log: ResponseLog) -> None:
        self._log = log
        self._inner: Any = None

    def __deepcopy__(self, memo: Any) -> Self:
        return self

    def __getattr__(self, name: str) -> Any:
        if name.startswith("__") or self._inner is None:
            raise AttributeError(name)
        return getattr(self._inner, name)

    def adopt(self, transport: Any) -> None:
        if self._inner is None:
            self._inner = transport

    async def send(
        self,
        request: HTTPRequest,
        *,
        request_config: HTTPRequestConfiguration | None = None,
    ) -> HTTPResponse:
        if self._inner is None:
            raise HTTPRecordError(
                "The recording transport has no transport to send with."
            )
        if isinstance(request.body, AsyncBytesProvider):
            raise HTTPRecordError("Event stream requests can't be recorded.")
        self._log.learn(_header_values(request))
        response = await self._inner.send(request, request_config=request_config)
        headers = [
            (field.name, value)
            for field in response.fields
            if field.kind == "header"
            for value in field.values
        ]
        self._log.check(headers)
        # The client gets a new stream over the same bytes, so what it reads is what
        # the service sent.
        data = await read_streaming_blob_async(response.body)
        await close_async(response.body)
        self._log.add(response.status, headers, data)
        return HTTPResponse(
            status=response.status,
            fields=response.fields,
            body=AsyncBytesReader(data),
            reason=response.reason,
        )

    async def close(self) -> None:
        if (close := getattr(self._inner, "close", None)) is not None:
            await close()


class _LearningResolver:
    """Hands out the identities of the resolver it wraps and tells the log about them."""

    def __init__(self, inner: Any, log: ResponseLog) -> None:
        self._inner = inner
        self._log = log

    def __deepcopy__(self, memo: Any) -> Self:
        return self

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)

    async def get_identity(self, *, properties: Any) -> Any:
        identity = await self._inner.get_identity(properties=properties)
        self._log.learn_identity(identity)
        return identity


def _install(config: Any, transport: _AsyncRecordingTransport) -> None:
    if not hasattr(config, "transport"):
        raise TypeError(
            f"{type(config).__name__} has no transport; it can't be recorded."
        )
    if config.transport is not transport:
        transport.adopt(config.transport)
    config.transport = transport
    resolver = getattr(config, "aws_credentials_identity_resolver", None)
    if resolver is not None and not isinstance(resolver, _LearningResolver):
        config.aws_credentials_identity_resolver = _LearningResolver(
            resolver, transport._log
        )


def _header_values(request: HTTPRequest) -> list[tuple[str, str]]:
    return [(f.name, v) for f in request.fields if f.kind == "header" for v in f.values]
