#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""Throughput benchmark: rpcv2Cbor protocol vs awsJson1_0 protocol.

Measures the PROTOCOL layer (``serialize_request`` / ``deserialize_response``), NOT the
raw codec. Both protocol classes subclass ``HttpClientProtocol`` and expose the same two
methods; we build a modeled shape + ``Schema`` + ``APIOperation`` by hand (see
``model.py``) exactly the way a generated client does, then drive the protocol methods
directly with a plain ``time.perf_counter`` loop (no benchmark dependency).

Run via ``make benchmark`` (coverage disabled) or directly:

    uv run pytest packages/smithy-cbor/tests/benchmark --no-cov -s -q
"""

import asyncio
import random
import string
import time
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime

from smithy_aws_core.aio.protocols import AwsJson10ClientProtocol
from smithy_core import URI
from smithy_core.aio.types import AsyncBytesReader
from smithy_core.interfaces import TypedProperties as _TypedPropertiesInterface
from smithy_core.types import TypedProperties
from smithy_http import tuples_to_fields
from smithy_http.aio import HTTPResponse
from smithy_http.aio.protocols import RpcV2CborClientProtocol

from .model import (
    PUT_RECORDS_OPERATION,
    SERVICE,
    Nested,
    PutRecordsInput,
    PutRecordsOutput,
    Record,
)

# Number of records tuned so the CBOR-serialized input body lands near ~8 KB. Verified
# empirically in the test below (assertion guards the target).
_RECORD_COUNT = 31

# perf_counter loop sizing: a warmup to prime code paths and allocator, then a measured
# run large enough to average out scheduler noise.
_WARMUP_ITERS = 200
_MEASURE_ITERS = 3000

_ENDPOINT = URI(host="example.com", path="/")
_RNG_SEED = 0xB0BA


def _rand_string(rng: random.Random, n: int) -> str:
    return "".join(rng.choice(string.ascii_letters) for _ in range(n))


def _make_record(rng: random.Random) -> Record:
    return Record(
        id=_rand_string(rng, 16),
        name=_rand_string(rng, 24),
        count=rng.randint(0, 1_000_000),
        size=rng.randint(0, 2**40),
        ratio=rng.random() * 1000.0,
        weight=rng.uniform(-1e6, 1e6),
        created_at=datetime.fromtimestamp(
            rng.randint(1_000_000_000, 1_800_000_000), tz=UTC
        ),
        nested=Nested(label=_rand_string(rng, 12), score=rng.random()),
        tags=[_rand_string(rng, 8) for _ in range(rng.randint(2, 5))],
        attributes={
            _rand_string(rng, 6): rng.randint(0, 100) for _ in range(rng.randint(2, 5))
        },
    )


def _make_payload() -> tuple[PutRecordsInput, PutRecordsOutput]:
    """The SAME seeded payload is used for both protocols (apples-to-apples)."""
    rng = random.Random(_RNG_SEED)
    records = [_make_record(rng) for _ in range(_RECORD_COUNT)]
    # Input and output share identical shape (list of Record) and identical values.
    return PutRecordsInput(records=records), PutRecordsOutput(records=records)


def _time_ops(fn: Callable[[], object], warmup: int, iters: int) -> float:
    for _ in range(warmup):
        fn()
    start = time.perf_counter()
    for _ in range(iters):
        fn()
    return time.perf_counter() - start


def _time_ops_async(
    fn: Callable[[], Awaitable[object]], warmup: int, iters: int
) -> float:
    async def _run() -> float:
        for _ in range(warmup):
            await fn()
        start = time.perf_counter()
        for _ in range(iters):
            await fn()
        return time.perf_counter() - start

    return asyncio.run(_run())


def _make_response(body: bytes, content_type: str) -> HTTPResponse:
    """A success HTTPResponse stub carrying the wire body, mirroring the response-stub
    pattern in the generated protocol tests (status 200 + fields + body bytes)."""
    return HTTPResponse(
        status=200,
        fields=tuples_to_fields([("content-type", content_type)]),
        body=AsyncBytesReader(body),
    )


class _Measurement:
    __slots__ = ("label", "mb_per_sec", "ops_per_sec")

    def __init__(self, label: str, ops_per_sec: float, mb_per_sec: float) -> None:
        self.label = label
        self.ops_per_sec = ops_per_sec
        self.mb_per_sec = mb_per_sec


def _bench_protocol(
    name: str,
    protocol: RpcV2CborClientProtocol | AwsJson10ClientProtocol,
    content_type: str,
    ctx: _TypedPropertiesInterface,
) -> tuple[_Measurement, _Measurement, int]:
    input_, output = _make_payload()

    # Serialize once to size the payload and to build the response stub body used by
    # the deserialize benchmark.
    request = protocol.serialize_request(
        operation=PUT_RECORDS_OPERATION,
        input=input_,
        endpoint=_ENDPOINT,
        context=ctx,  # type: ignore[arg-type]
    )
    request_body = asyncio.run(request.consume_body_async())
    payload_bytes = len(request_body)

    # The output shape is identical to the input shape, so the wire body a server would
    # return is the same encoding. Produce it via the same protocol/codec.
    response_request = protocol.serialize_request(
        operation=PUT_RECORDS_OPERATION,
        input=PutRecordsInput(records=output.records),
        endpoint=_ENDPOINT,
        context=ctx,  # type: ignore[arg-type]
    )
    response_body = asyncio.run(response_request.consume_body_async())
    response_bytes = len(response_body)

    # --- serialize throughput ---
    def _serialize() -> object:
        return protocol.serialize_request(
            operation=PUT_RECORDS_OPERATION,
            input=input_,
            endpoint=_ENDPOINT,
            context=ctx,  # type: ignore[arg-type]
        )

    ser_elapsed = _time_ops(_serialize, _WARMUP_ITERS, _MEASURE_ITERS)
    ser_ops = _MEASURE_ITERS / ser_elapsed
    ser_mb = (payload_bytes * _MEASURE_ITERS) / ser_elapsed / (1024 * 1024)

    # --- deserialize throughput ---
    async def _deserialize() -> object:
        response = _make_response(response_body, content_type)
        return await protocol.deserialize_response(
            operation=PUT_RECORDS_OPERATION,
            request=request,
            response=response,
            error_registry=PUT_RECORDS_OPERATION.error_registry,
            context=ctx,  # type: ignore[arg-type]
        )

    de_elapsed = _time_ops_async(_deserialize, _WARMUP_ITERS, _MEASURE_ITERS)
    de_ops = _MEASURE_ITERS / de_elapsed
    de_mb = (response_bytes * _MEASURE_ITERS) / de_elapsed / (1024 * 1024)

    return (
        _Measurement(f"{name}-serialize", ser_ops, ser_mb),
        _Measurement(f"{name}-deserialize", de_ops, de_mb),
        payload_bytes,
    )


def test_protocol_throughput() -> None:
    """Compare rpcv2Cbor vs awsJson1_0 protocol ser/deser throughput.

    Run with ``-s`` (as ``make benchmark`` does) to see the table.
    """
    ctx = TypedProperties()

    cbor = RpcV2CborClientProtocol(SERVICE)
    json = AwsJson10ClientProtocol(SERVICE)

    cbor_ser, cbor_de, cbor_bytes = _bench_protocol(
        "cbor", cbor, "application/cbor", ctx
    )
    json_ser, json_de, json_bytes = _bench_protocol(
        "json", json, "application/x-amz-json-1.0", ctx
    )

    # Sanity: both protocols serialize the shared payload and land near the ~8KB target.
    assert 4 * 1024 <= cbor_bytes <= 16 * 1024, cbor_bytes
    assert 4 * 1024 <= json_bytes <= 16 * 1024, json_bytes

    results = [cbor_ser, cbor_de, json_ser, json_de]

    header = f"{'operation':<20}{'ops/sec':>16}{'MB/sec':>14}"
    rule = "-" * len(header)
    lines = [
        "",
        f"Payload: list of {_RECORD_COUNT} Record structs "
        f"(cbor body {cbor_bytes} B, json body {json_bytes} B); "
        f"{_MEASURE_ITERS} measured iterations after {_WARMUP_ITERS} warmup.",
        header,
        rule,
        *(
            f"{r.label:<20}{r.ops_per_sec:>16,.0f}{r.mb_per_sec:>14,.2f}"
            for r in results
        ),
        rule,
        f"{'cbor/json ser ratio':<20}"
        f"{cbor_ser.ops_per_sec / json_ser.ops_per_sec:>16.2f}x",
        f"{'cbor/json deser ratio':<20}"
        f"{cbor_de.ops_per_sec / json_de.ops_per_sec:>16.2f}x",
    ]
    # Emitting the measured table is the whole point of a benchmark; T201 (no prints in
    # library code) does not apply to this reporting driver.
    print("\n".join(lines))  # noqa: T201

    # Guard: all four measured a positive throughput (the harness actually ran).
    for r in results:
        assert r.ops_per_sec > 0
        assert r.mb_per_sec > 0
