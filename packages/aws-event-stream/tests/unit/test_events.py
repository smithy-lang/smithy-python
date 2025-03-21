# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
# pyright: reportPrivateUsage=false
import datetime
import uuid
from io import BytesIO

import pytest
from aws_event_stream.events import (
    MAX_HEADER_VALUE_BYTE_LENGTH,
    MAX_HEADERS_LENGTH,
    MAX_PAYLOAD_LENGTH,
    Byte,
    Event,
    EventHeaderDecoder,
    EventHeaderEncoder,
    EventMessage,
    EventPrelude,
    Long,
    Short,
)
from aws_event_stream.events import _EventEncoder as EventEncoder
from aws_event_stream.exceptions import (
    ChecksumMismatch,
    DuplicateHeader,
    InvalidEventBytes,
    InvalidHeadersLength,
    InvalidHeaderValueLength,
    InvalidIntegerValue,
    InvalidPayloadLength,
)
from smithy_core.aio.types import AsyncBytesReader

EMPTY_MESSAGE = (
    (
        b"\x00\x00\x00\x10"  # total length
        b"\x00\x00\x00\x00"  # headers length
        b"\x05\xc2\x48\xeb"  # prelude crc
        b"\x7d\x98\xc8\xff"  # message crc
    ),
    Event(
        prelude=EventPrelude(
            total_length=0x10,
            headers_length=0,
            crc=0x05C248EB,
        ),
        message=EventMessage(
            headers={},
            payload=b"",
        ),
        crc=0x7D98C8FF,
    ),
)

TRUE_HEADER = (
    (
        b"\x00\x00\x00\x16"  # total length
        b"\x00\x00\x00\x06"  # headers length
        b"\x63\xe1\x18\x7e"  # prelude crc
        b"\x04true\x00"  # headers
        b"\xf1\xe7\xbc\xd7"  # message crc
    ),
    Event(
        prelude=EventPrelude(
            total_length=0x16,
            headers_length=0x6,
            crc=0x63E1187E,
        ),
        message=EventMessage(
            headers={"true": True},
        ),
        crc=0xF1E7BCD7,
    ),
)

FALSE_HEADER = (
    (
        b"\x00\x00\x00\x17"  # total length
        b"\x00\x00\x00\x07"  # headers length
        b"\x29\x86\x01\x58"  # prelude crc
        b"\x05false\x01"  # headers
        b"\x52\x31\x7e\xf4"  # message crc
    ),
    Event(
        prelude=EventPrelude(
            total_length=0x17,
            headers_length=0x7,
            crc=0x29860158,
        ),
        message=EventMessage(
            headers={"false": False},
        ),
        crc=0x52317EF4,
    ),
)

BYTE_HEADER = (
    (
        b"\x00\x00\x00\x17"  # total length
        b"\x00\x00\x00\x07"  # headers length
        b"\x29\x86\x01\x58"  # prelude crc
        b"\x04byte\x02\xff"  # headers
        b"\xc2\xf8\x69\xdc"  # message crc
    ),
    Event(
        prelude=EventPrelude(
            total_length=0x17,
            headers_length=0x7,
            crc=0x29860158,
        ),
        message=EventMessage(
            headers={"byte": Byte(-1)},
        ),
        crc=0xC2F869DC,
    ),
)

SHORT_HEADER = (
    (
        b"\x00\x00\x00\x19"  # total length
        b"\x00\x00\x00\x09"  # headers length
        b"\x71\x0e\x92\x3e"  # prelude crc
        b"\x05short\x03\xff\xff"  # headers
        b"\xb2\x7c\xb6\xcc"  # message crc
    ),
    Event(
        prelude=EventPrelude(
            total_length=0x19,
            headers_length=0x9,
            crc=0x710E923E,
        ),
        message=EventMessage(
            headers={"short": Short(-1)},
        ),
        crc=0xB27CB6CC,
    ),
)

INTEGER_HEADER = (
    (
        b"\x00\x00\x00\x1d"  # total length
        b"\x00\x00\x00\x0d"  # headers length
        b"\x83\xe3\xf0\xe7"  # prelude crc
        b"\x07integer\x04\xff\xff\xff\xff"  # headers
        b"\x8b\x8e\x12\xeb"  # message crc
    ),
    Event(
        prelude=EventPrelude(
            total_length=0x1D,
            headers_length=0xD,
            crc=0x83E3F0E7,
        ),
        message=EventMessage(
            headers={"integer": -1},
            payload=b"",
        ),
        crc=0x8B8E12EB,
    ),
)

LONG_HEADER = (
    (
        b"\x00\x00\x00\x1e"  # total length
        b"\x00\x00\x00\x0e"  # headers length
        b"\x5d\x4a\xdb\x8d"  # prelude crc
        b"\x04long\x05\xff\xff\xff\xff\xff\xff\xff\xff"  # headers
        b"\x4b\xc2\x32\xda"  # message crc
    ),
    Event(
        prelude=EventPrelude(
            total_length=0x1E,
            headers_length=0xE,
            crc=0x5D4ADB8D,
        ),
        message=EventMessage(
            headers={"long": Long(-1)},
        ),
        crc=0x4BC232DA,
    ),
)

BYTE_ARRAY_HEADER = (
    (
        b"\x00\x00\x00\x1e"  # total length
        b"\x00\x00\x00\x0e"  # headers length
        b"\x5d\x4a\xdb\x8d"  # prelude crc
        b"\x05bytes\x06\x00\x05bytes"  # headers
        b"\xa1\x64\x4d\xbf"  # message crc
    ),
    Event(
        prelude=EventPrelude(
            total_length=0x1E,
            headers_length=0xE,
            crc=0x5D4ADB8D,
        ),
        message=EventMessage(
            headers={"bytes": b"bytes"},
        ),
        crc=0xA1644DBF,
    ),
)

STRING_HEADER = (
    (
        b"\x00\x00\x00\x20"  # total length
        b"\x00\x00\x00\x10"  # headers length
        b"\xb9\x54\xe0\x09"  # prelude crc
        b"\x06string\x07\x00\x06string"  # headers
        b"\x4c\x8d\x9e\x14"  # message crc
    ),
    Event(
        prelude=EventPrelude(
            total_length=0x20,
            headers_length=0x10,
            crc=0xB954E009,
        ),
        message=EventMessage(
            headers={"string": "string"},
        ),
        crc=0x4C8D9E14,
    ),
)

TIMESTAMP_HEADER = (
    (
        b"\x00\x00\x00\x23"  # total length
        b"\x00\x00\x00\x13"  # headers length
        b"\x67\xfd\xcb\x63"  # prelude crc
        b"\x09timestamp\x08\x00\x00\x00\x00\x00\x00\x00\x08"  # headers
        b"\x8d\x45\x33\xee"  # message crc
    ),
    Event(
        prelude=EventPrelude(
            total_length=0x23,
            headers_length=0x13,
            crc=0x67FDCB63,
        ),
        message=EventMessage(
            headers={
                "timestamp": datetime.datetime(
                    1970, 1, 1, 0, 0, 0, 8000, tzinfo=datetime.UTC
                )
            },
        ),
        crc=0x8D4533EE,
    ),
)

UUID_HEADER = (
    (
        b"\x00\x00\x00\x26"  # total length
        b"\x00\x00\x00\x16"  # headers length
        b"\xdf\x77\xb0\x9c"  # prelude crc
        b"\x04uuid\t0123456789abcdef"  # headers
        b"\xc9\x06\xb8\x65"  # message crc
    ),
    Event(
        prelude=EventPrelude(
            total_length=0x26,
            headers_length=0x16,
            crc=0xDF77B09C,
        ),
        message=EventMessage(
            headers={"uuid": uuid.UUID(bytes=b"0123456789abcdef")},
        ),
        crc=0xC906B865,
    ),
)

PAYLOAD_NO_HEADERS = (
    (
        b"\x00\x00\x00\x1d"  # total length
        b"\x00\x00\x00\x00"  # headers length
        b"\xfd\x52\x8c\x5a"  # prelude crc
        b"{'foo':'bar'}"  # payload
        b"\xc3\x65\x39\x36"  # message crc
    ),
    Event(
        prelude=EventPrelude(
            total_length=0x1D,
            headers_length=0,
            crc=0xFD528C5A,
        ),
        message=EventMessage(
            headers={},
            payload=b"{'foo':'bar'}",
        ),
        crc=0xC3653936,
    ),
)

PAYLOAD_ONE_STR_HEADER = (
    (
        b"\x00\x00\x00\x3d"  # total length
        b"\x00\x00\x00\x20"  # headers length
        b"\x07\xfd\x83\x96"  # prelude crc
        b"\x0ccontent-type\x07\x00\x10application/json"  # headers
        b"{'foo':'bar'}"  # payload
        b"\x8d\x9c\x08\xb1"  # message crc
    ),
    Event(
        prelude=EventPrelude(
            total_length=0x3D,
            headers_length=0x20,
            crc=0x07FD8396,
        ),
        message=EventMessage(
            headers={"content-type": "application/json"},
            payload=b"{'foo':'bar'}",
        ),
        crc=0x8D9C08B1,
    ),
)

ALL_HEADERS_TYPES = (
    (
        b"\x00\x00\x00\x62"  # total length
        b"\x00\x00\x00\x52"  # headers length
        b"\x03\xb5\xcb\x9c"  # prelude crc
        b"\x010\x00"  # boolean true
        b"\x011\x01"  # boolean false
        b"\x012\x02\x02"  # byte
        b"\x013\x03\x00\x03"  # short
        b"\x014\x04\x00\x00\x00\x04"  # int
        b"\x015\x05\x00\x00\x00\x00\x00\x00\x00\x05"  # long
        b"\x016\x06\x00\x05bytes"  # bytes
        b"\x017\x07\x00\x04utf8"  # string
        b"\x018\x08\x00\x00\x00\x00\x00\x00\x00\x08"  # timestamp
        b"\x019\x090123456789abcdef"  # uuid
        b"\x63\x35\x36\x71"  # message crc
    ),
    Event(
        prelude=EventPrelude(
            total_length=0x62,
            headers_length=0x52,
            crc=0x03B5CB9C,
        ),
        message=EventMessage(
            headers={
                "0": True,
                "1": False,
                "2": Byte(0x02),
                "3": Short(0x03),
                "4": 0x04,
                "5": Long(0x05),
                "6": b"bytes",
                "7": "utf8",
                "8": datetime.datetime(1970, 1, 1, 0, 0, 0, 8000, tzinfo=datetime.UTC),
                "9": uuid.UUID(bytes=b"0123456789abcdef"),
            },
            payload=b"",
        ),
        crc=0x63353671,
    ),
)

ERROR_EVENT_MESSAGE = (
    (
        b"\x00\x00\x00\x52"  # total length
        b"\x00\x00\x00\x42"  # headers length
        b"\xbf\x23\x63\x7e"  # prelude crc
        b"\x0d:message-type\x07\x00\x05error"
        b"\x0b:error-code\x07\x00\x04code"
        b"\x0e:error-message\x07\x00\x07message"
        b"\x6b\x6c\xea\x3d"  # message crc
    ),
    Event(
        prelude=EventPrelude(
            total_length=0x52,
            headers_length=0x42,
            crc=0xBF23637E,
        ),
        message=EventMessage(
            headers={
                ":message-type": "error",
                ":error-code": "code",
                ":error-message": "message",
            },
        ),
        crc=0x6B6CEA3D,
    ),
)

EMPTY_SOURCE = (b"", None)

# Tuples of encoded messages and their expected decoded output
POSITIVE_CASES = [
    EMPTY_MESSAGE,  # standard
    TRUE_HEADER,
    FALSE_HEADER,
    BYTE_HEADER,
    SHORT_HEADER,
    INTEGER_HEADER,  # standard
    LONG_HEADER,
    BYTE_ARRAY_HEADER,
    STRING_HEADER,
    TIMESTAMP_HEADER,
    UUID_HEADER,
    PAYLOAD_NO_HEADERS,  # standard
    PAYLOAD_ONE_STR_HEADER,  # standard
    ALL_HEADERS_TYPES,  # standard
    ERROR_EVENT_MESSAGE,
    EMPTY_SOURCE,
]

CORRUPTED_HEADERS_LENGTH = (
    (
        b"\x00\x00\x00\x3d"  # total length
        b"\xff\x00\x01\x02"  # headers length
        b"\x07\xfd\x83\x96"  # prelude crc
        b"\x0ccontent-type\x07\x00\x10application/json"  # headers
        b"{'foo':'bar'}"  # payload
        b"\x8d\x9c\x08\xb1"  # message crc
    ),
    ChecksumMismatch,
)

CORRUPTED_HEADERS = (
    (
        b"\x00\x00\x00\x3d"  # total length
        b"\x00\x00\x00\x20"  # headers length
        b"\x07\xfd\x83\x96"  # prelude crc
        b"\x0ccontent+type\x07\x00\x10application/json"  # headers
        b"{'foo':'bar'}"  # payload
        b"\x8d\x9c\x08\xb1"  # message crc
    ),
    ChecksumMismatch,
)

CORRUPTED_LENGTH = (
    (
        b"\x01\x00\x00\x1d"  # total length
        b"\x00\x00\x00\x00"  # headers length
        b"\xfd\x52\x8c\x5a"  # prelude crc
        b"{'foo':'bar'}"  # payload
        b"\xc3\x65\x39\x36"  # message crc
    ),
    ChecksumMismatch,
)

CORRUPTED_PAYLOAD = (
    (
        b"\x00\x00\x00\x1d"  # total length
        b"\x00\x00\x00\x00"  # headers length
        b"\xfd\x52\x8c\x5a"  # prelude crc
        b"{'foo':'bar'\x8d"  # payload
        b"\xc3\x65\x39\x36"  # message crc
    ),
    ChecksumMismatch,
)

DUPLICATE_HEADER = (
    (
        b"\x00\x00\x00\x24"  # total length
        b"\x00\x00\x00\x14"  # headers length
        b"\x4b\xb9\x82\xd0"  # prelude crc
        b"\x04test\x04asdf\x04test\x04asdf"  # headers
        b"\xf3\xf4\x75\x63"  # message crc
    ),
    DuplicateHeader,
)

INVALID_HEADERS_LENGTH = (
    (
        b"\x00\x00\x00\x3d"  # total length
        b"\xff\x00\x01\x02"  # headers length
        b"\x15\x83\xf5\xc2"  # prelude crc
        b"\x0ccontent-type\x07\x00\x10application/json"  # headers
        b"{'foo':'bar'}"  # payload
        b"\x2f\x37\x7f\x5d"  # message crc
    ),
    InvalidHeadersLength,
)


INVALID_HEADER_VALUE_LENGTH = (
    b"\x00\x00\x80\x1c"  # total length
    + b"\x00\x00\x80\x0c"  # headers length
    + b"\xec\xb7\x65\x52"  # prelude crc
    + b"\x08too-long\x06\x80\x00"
    + b"0" * (MAX_HEADER_VALUE_BYTE_LENGTH + 1)  # headers
    + b"\x7e\x41\x46\xee",  # message crc
    InvalidHeaderValueLength,
)

INVALID_PAYLOAD_LENGTH = (
    b"\x01\x00\x00\x11"  # total length
    + b"\x00\x00\x00\x00"  # headers length
    + b"\xf4\x08\x61\xc5"  # prelude crc
    + b"0" * (MAX_PAYLOAD_LENGTH + 1)  # payload
    + b"\x2a\xb4\xc5\xa5",  # message crc
    InvalidPayloadLength,
)

TRUNCATED_PRELUDE = (b"\x00", InvalidEventBytes)

MISSING_PRELUDE_CRC_BYTES = (b"\x00\x00\x00\x16", InvalidEventBytes)

MISSING_MESSAGE_CRC_BYTES = (
    (
        b"\x00\x00\x00\x10"  # total length
        b"\x00\x00\x00\x00"  # headers length
        b"\x05\xc2\x48\xeb"  # prelude crc
    ),
    InvalidEventBytes,
)

# Tuples of encoded messages and their expected exception
NEGATIVE_CASES = {
    "corrupted-length": CORRUPTED_LENGTH,  # standard
    "corrupted-payload": CORRUPTED_PAYLOAD,  # standard
    "corrupted-headers": CORRUPTED_HEADERS,  # standard
    "corrupted-headers-length": CORRUPTED_HEADERS_LENGTH,  # standard
    "duplicate-header": DUPLICATE_HEADER,
    "invalid-headers-length": INVALID_HEADERS_LENGTH,
    "invalid-header-value-length": INVALID_HEADER_VALUE_LENGTH,
    "invalid-payload-length": INVALID_PAYLOAD_LENGTH,
    "truncated-prelude": TRUNCATED_PRELUDE,
    "missing-prelude-crc-bytes": MISSING_PRELUDE_CRC_BYTES,
    "missing-message-crc-bytes": MISSING_MESSAGE_CRC_BYTES,
}


@pytest.mark.parametrize("encoded,expected", POSITIVE_CASES)
def test_decode(encoded: bytes, expected: Event | None):
    assert Event.decode(BytesIO(encoded)) == expected


@pytest.mark.parametrize("encoded,expected", POSITIVE_CASES)
async def test_decode_async(encoded: bytes, expected: Event | None):
    assert await Event.decode_async(AsyncBytesReader(encoded)) == expected


@pytest.mark.parametrize(
    "expected,event", [c for c in POSITIVE_CASES if c[1] is not None]
)
def test_encode(expected: bytes, event: Event):
    assert event.message.encode() == expected


@pytest.mark.parametrize(
    "encoded,expected", NEGATIVE_CASES.values(), ids=NEGATIVE_CASES.keys()
)
def test_negative_cases(encoded: bytes, expected: type[Exception]):
    with pytest.raises(expected):
        Event.decode(BytesIO(encoded))


@pytest.mark.parametrize(
    "encoded,expected", NEGATIVE_CASES.values(), ids=NEGATIVE_CASES.keys()
)
async def test_negative_cases_async(encoded: bytes, expected: type[Exception]):
    with pytest.raises(expected):
        await Event.decode_async(AsyncBytesReader(encoded))


def test_event_prelude_rejects_long_headers():
    headers_length = MAX_HEADERS_LENGTH + 1
    total_length = headers_length + 16
    with pytest.raises(InvalidHeadersLength):
        EventPrelude(total_length=total_length, headers_length=headers_length, crc=1)


def test_event_prelude_rejects_long_payload():
    total_length = MAX_PAYLOAD_LENGTH + 17
    with pytest.raises(InvalidPayloadLength):
        EventPrelude(total_length=total_length, headers_length=0, crc=1)


def test_event_message_rejects_long_payload():
    payload = b"0" * (MAX_PAYLOAD_LENGTH + 1)
    with pytest.raises(InvalidPayloadLength):
        EventMessage(payload=payload)


def test_event_message_rejects_long_header_value():
    headers = {"foo": b"0" * (MAX_HEADER_VALUE_BYTE_LENGTH + 1)}
    with pytest.raises(InvalidHeaderValueLength):
        EventMessage(headers=headers).encode()


def test_event_encoder_rejects_long_headers():
    long_value = b"0" * (MAX_HEADER_VALUE_BYTE_LENGTH - 1)
    long_headers = b""
    for i in range(5):
        long_headers += b"\x01" + str(i).encode("utf-8") + b"\x06\x7f\xfe" + long_value

    with pytest.raises(InvalidHeadersLength):
        EventEncoder().encode_bytes(headers=long_headers)


def test_event_encoder_rejects_long_payload():
    payload = b"0" * (MAX_PAYLOAD_LENGTH + 1)
    with pytest.raises(InvalidPayloadLength):
        EventEncoder().encode_bytes(payload=payload)


def test_event_encoder_encodes_bytes():
    expected = (
        b"\x00\x00\x00\x3d"  # total length
        b"\x00\x00\x00\x20"  # headers length
        b"\x07\xfd\x83\x96"  # prelude crc
        b"\x0ccontent-type\x07\x00\x10application/json"  # headers
        b"{'foo':'bar'}"  # payload
        b"\x8d\x9c\x08\xb1"  # message crc
    )
    headers = b"\x0ccontent-type\x07\x00\x10application/json"
    payload = b"{'foo':'bar'}"
    actual = EventEncoder().encode_bytes(headers=headers, payload=payload)
    assert actual == expected


def test_encode_boolean_header():
    encoder = EventHeaderEncoder()
    encoder.encode_boolean("foo", True)
    assert encoder.get_result() == b"\x03foo\x00"

    encoder.clear()
    encoder.encode_boolean("foo", False)
    assert encoder.get_result() == b"\x03foo\x01"


def test_encode_byte_header():
    encoder = EventHeaderEncoder()
    encoder.encode_byte("foo", 1)
    assert encoder.get_result() == b"\x03foo\x02\x01"


def test_encode_too_long_byte_header():
    encoder = EventHeaderEncoder()
    with pytest.raises(InvalidIntegerValue):
        encoder.encode_byte("foo", 2**7)


def test_encode_short_header():
    encoder = EventHeaderEncoder()
    encoder.encode_short("foo", 1)
    assert encoder.get_result() == b"\x03foo\x03\x00\x01"


def test_encode_too_long_short_header():
    encoder = EventHeaderEncoder()
    with pytest.raises(InvalidIntegerValue):
        encoder.encode_short("foo", 2**15)


def test_encode_int_header():
    encoder = EventHeaderEncoder()
    encoder.encode_integer("foo", 1)
    assert encoder.get_result() == b"\x03foo\x04\x00\x00\x00\x01"


def test_encode_too_long_int_header():
    encoder = EventHeaderEncoder()
    with pytest.raises(InvalidIntegerValue):
        encoder.encode_integer("foo", 2**31)


def test_encode_long_header():
    encoder = EventHeaderEncoder()
    encoder.encode_long("foo", 1)
    assert encoder.get_result() == b"\x03foo\x05\x00\x00\x00\x00\x00\x00\x00\x01"


def test_encode_too_long_long_header():
    encoder = EventHeaderEncoder()
    with pytest.raises(InvalidIntegerValue):
        encoder.encode_long("foo", 2**63)


def test_encode_blob_header():
    encoder = EventHeaderEncoder()
    encoder.encode_blob("foo", b"bytes")
    assert encoder.get_result() == b"\x03foo\x06\x00\x05bytes"


def test_encode_string_header():
    encoder = EventHeaderEncoder()
    encoder.encode_string("foo", "string")
    assert encoder.get_result() == b"\x03foo\x07\x00\x06string"


def test_encode_timestamp_header():
    encoder = EventHeaderEncoder()
    encoder.encode_timestamp(
        "foo", datetime.datetime(1970, 1, 1, 0, 0, 0, 8000, tzinfo=datetime.UTC)
    )
    assert encoder.get_result() == b"\x03foo\x08\x00\x00\x00\x00\x00\x00\x00\x08"


def test_encode_uuid_header():
    encoder = EventHeaderEncoder()
    encoder.encode_uuid("foo", uuid.UUID(bytes=b"0123456789abcdef"))
    assert encoder.get_result() == b"\x03foo\x090123456789abcdef"


def test_decode_bool_header():
    actual = EventHeaderDecoder(b"\x03foo\x00").decode_header()
    assert actual == ("foo", True)

    actual = EventHeaderDecoder(b"\x03foo\x01").decode_header()
    assert actual == ("foo", False)


def test_decode_byte_header():
    actual = EventHeaderDecoder(b"\x03foo\x02\x01").decode_header()
    assert actual == ("foo", 1)


def test_decode_short_header():
    actual = EventHeaderDecoder(b"\x03foo\x03\x00\x01").decode_header()
    assert actual == ("foo", 1)


def test_decode_integer_header():
    actual = EventHeaderDecoder(b"\x03foo\x04\x00\x00\x00\x01").decode_header()
    assert actual == ("foo", 1)


def test_decode_long_header():
    actual = EventHeaderDecoder(
        b"\x03foo\x05\x00\x00\x00\x00\x00\x00\x00\x01"
    ).decode_header()
    assert actual == ("foo", 1)


def test_decode_blob_header():
    actual = EventHeaderDecoder(b"\x03foo\x06\x00\x05bytes").decode_header()
    assert actual == ("foo", b"bytes")


def test_decode_string_header():
    actual = EventHeaderDecoder(b"\x03foo\x07\x00\x06string").decode_header()
    assert actual == ("foo", "string")


def test_decode_timestamp_header():
    actual = EventHeaderDecoder(
        b"\x03foo\x08\x00\x00\x00\x00\x00\x00\x00\x08"
    ).decode_header()
    assert actual == (
        "foo",
        datetime.datetime(1970, 1, 1, 0, 0, 0, 8000, tzinfo=datetime.UTC),
    )


def test_decode_uuid_header():
    actual = EventHeaderDecoder(b"\x03foo\x090123456789abcdef").decode_header()
    assert actual == ("foo", uuid.UUID(bytes=b"0123456789abcdef"))
