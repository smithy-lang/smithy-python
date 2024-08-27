# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import datetime
import uuid
from io import BytesIO

import pytest

from aws_event_stream.events import (
    MAX_HEADER_VALUE_BYTE_LENGTH,
    MAX_PAYLOAD_LENGTH,
    Byte,
    Event,
    EventMessage,
    EventPrelude,
    Long,
    Short,
)
from aws_event_stream.exceptions import (
    ChecksumMismatch,
    DuplicateHeader,
    InvalidHeadersLength,
    InvalidHeaderValueLength,
    InvalidPayloadLength,
)

EMPTY_MESSAGE = (
    (
        b"\x00\x00\x00\x10"  # total length
        b"\x00\x00\x00\x00"  # headers length
        b"\x05\xc2\x48\xeb"  # prelude crc
        b"\x7D\x98\xc8\xff"  # message crc
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
]

CORRUPTED_HEADERS_LENGTH = (
    (
        b"\x00\x00\x00\x3d"  # total length
        b"\xFF\x00\x01\x02"  # headers length
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
        b"\xfd\x52\x8c\x5A"  # prelude crc
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
        b"\xFF\x00\x01\x02"  # headers length
        b"\x15\x83\xf5\xc2"  # prelude crc
        b"\x0ccontent-type\x07\x00\x10application/json"  # headers
        b"{'foo':'bar'}"  # payload
        b"\x2F\x37\x7f\x5d"  # message crc
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

# Tuples of encoded messages and their expected exception
NEGATIVE_CASES = [
    CORRUPTED_LENGTH,  # standard
    CORRUPTED_PAYLOAD,  # standard
    CORRUPTED_HEADERS,  # standard
    CORRUPTED_HEADERS_LENGTH,  # standard
    DUPLICATE_HEADER,
    INVALID_HEADERS_LENGTH,
    INVALID_HEADER_VALUE_LENGTH,
    INVALID_PAYLOAD_LENGTH,
]


@pytest.mark.parametrize("encoded,expected", POSITIVE_CASES)
def test_decode(encoded: bytes, expected: Event):
    assert Event.decode(BytesIO(encoded)) == expected


@pytest.mark.parametrize("expected,event", POSITIVE_CASES)
def test_encode(expected: bytes, event: Event):
    assert event.message.encode() == expected


@pytest.mark.parametrize(
    "encoded,expected",
    NEGATIVE_CASES,
    ids=[
        "corrupted-length",
        "corrupted-payload",
        "corrupted-headers",
        "corrupted-headers-length",
        "duplicate-header",
        "invalid-headers-length",
        "invalid-header-value-length",
        "invalid-payload-length",
    ],
)
def test_negative_cases(encoded: bytes, expected: type[Exception]):
    with pytest.raises(expected):
        Event.decode(BytesIO(encoded))
