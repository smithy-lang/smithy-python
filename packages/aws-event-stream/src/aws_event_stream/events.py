# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Serialization and deserialization utilities for the
application/vnd.amazon.eventstream format.

This format is used to frame event stream messages for AWS protocols in a compact
manner.
"""

import datetime
import struct
import uuid
from binascii import crc32
from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass, field
from io import BytesIO
from struct import pack, unpack
from types import MappingProxyType
from typing import Literal, Self

from smithy_core.aio.interfaces import AsyncByteStream
from smithy_core.interfaces import BytesReader
from smithy_core.types import TimestampFormat

from .exceptions import (
    ChecksumMismatch,
    DuplicateHeader,
    InvalidEventBytes,
    InvalidHeadersLength,
    InvalidHeaderValue,
    InvalidHeaderValueLength,
    InvalidIntegerValue,
    InvalidPayloadLength,
)

MAX_HEADERS_LENGTH = 128 * 1024  # 128 Kb
MAX_HEADER_VALUE_BYTE_LENGTH = 32 * 1024 - 1  # 32Kb
MAX_PAYLOAD_LENGTH = 16 * 1024**2  # 16 Mb

# In addition to the header length and payload length, the total length of the
# message includes 12 bytes for the prelude and 4 bytes for the trailing crc.
_MESSAGE_METADATA_SIZE = 16


class Byte(int):
    """An 8-bit integer.

    This is a sentinel class that subclasses int with no additional functionality. It
    may be used to indicate the size of the int so that the appropriate type is used
    during manual header serialization to ensure the data is as compact as possible.

    This type is unnecessary and unused when serializing a SerializeableShape, which is
    able to indicate its size via a schema.
    """


class Short(int):
    """A 16-bit integer.

    This is a sentinel class that subclasses int with no additional functionality. It
    may be used to indicate the size of the int so that the appropriate type is used
    during manual header serialization to ensure the data is as compact as possible.

    This type is unnecessary and unused when serializing a SerializeableShape, which is
    able to indicate its size via a schema.
    """


class Long(int):
    """A 64-bit integer.

    This is a sentinel class that subclasses int with no additional functionality. It
    may be used to indicate the size of the int so that the appropriate type is used
    during manual header serialization to ensure the data is as compact as possible.

    This type is unnecessary and unused when serializing a SerializeableShape, which is
    able to indicate its size via a schema.
    """


type SizedInt = Byte | Short | Long | int
"""A union of integer types that indicate their size.

Each member of the union is a Python int or empty subclass of it, so they can be used
anywhere an int would be used in exactly the same way. The alternative type name may
be used to determine the size. There are four sizes:

* Byte  - 8 bits
* Short - 16 bits
* int   - 32 bits
* Long  - 64 bits

Serialization will fail if the provided values are not within the expected range.

Sizes are not preserved in this way during deserialization.
"""


type HEADER_VALUE = bool | int | bytes | str | datetime.datetime | uuid.UUID
"""A union of valid value types for event headers."""


type HEADERS_DICT = Mapping[str, HEADER_VALUE]
"""A dictionary of event headers."""


@dataclass(frozen=True, kw_only=True)
class EventPrelude:
    """Information sent first as part of an event.

    This includes the sizes of different parts of the event structure, which are used to
    know exactly how many bytes to expect.

    The prelude is always exactly 12 bytes long when serialized.
    """

    total_length: int
    """The total length of the event message.

    This includes:

    * The length of the prelude (always 12 bytes)
    * The length of the headers (between 0b and 128Kb)
    * The length of the payload (between 0b and 16Mb)
    * The length of the trailing crc (always 4 bytes)
    """

    headers_length: int
    """The length of the headers section.

    This value may be between 0 and 128 * 1024.
    """

    crc: int
    """The CRC32 checksum of the prelude.

    The bytes for this value are used when calculating the checksum at the end of the
    event message.
    """

    def __post_init__(self):
        if self.headers_length > MAX_HEADERS_LENGTH:
            raise InvalidHeadersLength(self.headers_length)

        payload_length = self.total_length - self.headers_length - 16
        if payload_length > MAX_PAYLOAD_LENGTH:
            raise InvalidPayloadLength(payload_length)


@dataclass(kw_only=True, eq=False)
class EventMessage:
    """A message that may be sent over an event stream.

    AWS events indicate their semantic structure with the `:message-type` header. This
    may have one of three string values: `event`, `exception`, or `error`.

    `event` messages are modeled data events. In addition to the `:message-type` header,
    they utilize the following headers:

    * `:event-type` - *Required*. This further refines the semantic structure of the
      event, determining what other headers may be set as well as the structure of
      the payload. The value is a string representing one of the event stream union
      member names in the Smithy model for the operation.

      The value may instead be `initial-request` or `initial-response` to indicate that
      the event represents an even stream initial message. These map to the Smithy
      operation input and output, respectively.
    * `:content-type` - A string indicating the media type of the payload.


    `exception` messages are modeled error events. In addition to the `:message-type`
    header, they utilize the following headers:

    * `:exception-type` - *Required*. This further refines the semantic structure of
      the event, determining what other headers may be set as well as the structure of
      the payload. The value is a string representing one of the event stream union
      member names in the Smithy model for the operation.
    * `:content-type` - A string indicating the media type of the payload.


    `error` messages are unmodeled error events. In addition to the `:message-type`
    header, they utilize the following headers:

    * `:error-code` - *Required*. An alphanumeric string containing the name, type, or
      category of the error.
    * `:error-message` - *Required*. A human-readable string containing an error
      message.
    """

    headers: HEADERS_DICT = field(default_factory=dict)
    """The headers present in the event message.

    Sized integer values may be indicated for the purpose of serialization
    using the `Byte`, `Short`, or `Long` types. int values of unspecified size
    will be assumed to be 32-bit.
    """

    payload: bytes = b""
    """The serialized bytes of the message payload."""

    def __post_init__(
        self,
    ) -> None:
        if len(self.payload) > MAX_PAYLOAD_LENGTH:
            raise InvalidPayloadLength(len(self.payload))

    def _get_headers_bytes(self) -> bytes:
        encoder = EventHeaderEncoder()
        encoder.encode_headers(self.headers)
        return encoder.get_result()

    def encode(self) -> bytes:
        return _EventEncoder().encode_bytes(
            headers=self._get_headers_bytes(), payload=self.payload
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, EventMessage):
            return False
        return all(
            [
                self.payload == other.payload,
                self.headers == other.headers,
                self._get_headers_bytes() == other._get_headers_bytes(),
            ]
        )


@dataclass(frozen=True)
class Event:
    """A complete event, including the prelude and trailing crc."""

    prelude: EventPrelude
    """Information sent first as part of an event."""

    message: EventMessage
    """The message portion of the event."""

    crc: int
    """The CRC32 checksum of the event.

    This checksum is computed using the prelude CRC bytes followed by the header bytes
    and then the payload bytes. The initial CRC value is the payload CRC value.
    """

    @classmethod
    def decode(cls, source: BytesReader) -> Self | None:
        """Decode an event from a byte stream.

        :param source: An object to read event bytes from. It must have a `read` method
            that accepts a number of bytes to read.

        :returns: An Event representing the next event on the source, or None if no
            data can be read from the source.
        """

        prelude_bytes = source.read(8)
        if not prelude_bytes:
            # If nothing can be read from the source, return None. If bytes are missing
            # later, that indicates a problem with the source and therefore will result
            # in an exception.
            return None

        prelude_crc_bytes = source.read(4)
        try:
            prelude_crc: int = _DecodeUtils.unpack_uint32(prelude_crc_bytes)[0]
            total_length, headers_length = unpack("!II", prelude_bytes)
        except struct.error as e:
            raise InvalidEventBytes() from e

        _validate_checksum(prelude_bytes, prelude_crc)
        prelude = EventPrelude(
            total_length=total_length, headers_length=headers_length, crc=prelude_crc
        )

        message_bytes = source.read(total_length - _MESSAGE_METADATA_SIZE)
        try:
            crc: int = _DecodeUtils.unpack_uint32(source.read(4))[0]
        except struct.error as e:
            raise InvalidEventBytes() from e

        _validate_checksum(prelude_crc_bytes + message_bytes, crc, prelude_crc)

        headers_bytes = message_bytes[: prelude.headers_length]
        message = EventMessage(
            headers=EventHeaderDecoder(headers_bytes).decode_headers(),
            payload=message_bytes[prelude.headers_length :],
        )
        return cls(prelude, message, crc)

    @classmethod
    async def decode_async(cls, source: AsyncByteStream) -> Self | None:
        """Decode an event from an async byte stream.

        :param source: An object to read event bytes from. It must have a `read` method
            that accepts a number of bytes to read.

        :returns: An Event representing the next event on the source, or None if no
            data can be read from the source.
        """

        prelude_bytes = await source.read(8)
        if not prelude_bytes:
            # If nothing can be read from the source, return None. If bytes are missing
            # later, that indicates a problem with the source and therefore will result
            # in an exception.
            return None

        prelude_crc_bytes = await source.read(4)
        try:
            prelude_crc: int = _DecodeUtils.unpack_uint32(prelude_crc_bytes)[0]
            total_length, headers_length = unpack("!II", prelude_bytes)
        except struct.error as e:
            raise InvalidEventBytes() from e

        _validate_checksum(prelude_bytes, prelude_crc)
        prelude = EventPrelude(
            total_length=total_length, headers_length=headers_length, crc=prelude_crc
        )

        message_bytes = await source.read(total_length - _MESSAGE_METADATA_SIZE)
        try:
            crc: int = _DecodeUtils.unpack_uint32(await source.read(4))[0]
        except struct.error as e:
            raise InvalidEventBytes() from e

        _validate_checksum(prelude_crc_bytes + message_bytes, crc, prelude_crc)

        headers_bytes = message_bytes[: prelude.headers_length]
        message = EventMessage(
            headers=EventHeaderDecoder(headers_bytes).decode_headers(),
            payload=message_bytes[prelude.headers_length :],
        )
        return cls(prelude, message, crc)


class _EventEncoder:
    """A utility class that encodes message bytes into binary events."""

    def encode_bytes(self, *, headers: bytes = b"", payload: bytes = b"") -> bytes:
        """Encode message bytes into a binary event.

        :param headers: The bytes representing the event headers.
        :param payload: The bytes representing the event payload.
        :returns: The fully encoded binary event, including the prelude and trailing
            crc.
        """
        if len(headers) > MAX_HEADERS_LENGTH:
            raise InvalidHeadersLength(len(headers))
        if len(payload) > MAX_PAYLOAD_LENGTH:
            raise InvalidPayloadLength(len(payload))

        prelude_bytes = self._encode_prelude_bytes(headers, payload)
        prelude_crc = self._calculate_checksum(prelude_bytes)
        prelude_crc_bytes = pack("!I", prelude_crc)
        message_bytes = prelude_crc_bytes + headers + payload

        final_crc = self._calculate_checksum(message_bytes, crc=prelude_crc)
        final_crc_bytes = pack("!I", final_crc)
        return prelude_bytes + message_bytes + final_crc_bytes

    def _encode_prelude_bytes(self, headers: bytes, payload: bytes) -> bytes:
        header_length = len(headers)
        total_length = header_length + len(payload) + _MESSAGE_METADATA_SIZE
        return pack("!II", total_length, header_length)

    def _calculate_checksum(self, data: bytes, crc: int = 0) -> int:
        return crc32(data, crc) & 0xFFFFFFFF


class EventHeaderEncoder:
    """A utility class that encodes event headers into bytes."""

    def __init__(self) -> None:
        self._buffer = BytesIO()
        self._keys: set[str] = set()

    def clear(self) -> None:
        """Clear all previously encoded headers."""
        self._buffer = BytesIO()
        self._keys = set()

    def get_result(self) -> bytes:
        """Get all the encoded header bytes."""
        result = self._buffer.getvalue()
        if len(result) > MAX_HEADERS_LENGTH:
            raise InvalidHeadersLength(len(result))
        return result

    def encode_headers(self, headers: HEADERS_DICT) -> None:
        """Encode a map of headers.

        :param headers: A mapping of headers to encode.

            Sized integer values may be indicated using the `Byte`, `Short`, or `Long`
            types. int values of unspecified size will be assumed to be 32-bit.
        """
        for key, value in headers.items():
            match value:
                case bool():
                    self.encode_boolean(key, value)
                case Byte():
                    self.encode_byte(key, value)
                case Short():
                    self.encode_short(key, value)
                case Long():
                    self.encode_long(key, value)
                case int():
                    self.encode_integer(key, value)
                case bytes():
                    self.encode_blob(key, value)
                case str():
                    self.encode_string(key, value)
                case datetime.datetime():
                    self.encode_timestamp(key, value)
                case uuid.UUID():
                    self.encode_uuid(key, value)
                case _:  # type: ignore
                    raise InvalidHeaderValue(value)

    def _encode_key(self, key: str) -> None:
        if key in self._keys:
            raise DuplicateHeader(key)
        self._keys.add(key)

        encoded_key = key.encode("utf-8")
        self._buffer.write(pack("B", len(encoded_key)))
        self._buffer.write(encoded_key)

    def encode_boolean(self, key: str, value: bool):
        """Encode a boolean header.

        :param key: The header key to encode.
        :param value: The boolean value to encode.
        """
        self._encode_key(key)
        if value:
            self._buffer.write(b"\x00")
        else:
            self._buffer.write(b"\x01")

    def encode_byte(self, key: str, value: int) -> None:
        """Encode an 8-bit int header.

        :param key: The header key to encode.
        :param value: The int value to encode.
        """
        self._encode_key(key)
        self._buffer.write(b"\x02")
        try:
            self._buffer.write(pack("!b", value))
        except struct.error as e:
            raise InvalidIntegerValue("byte", value) from e

    def encode_short(self, key: str, value: int) -> None:
        """Encode a 16-bit int header.

        :param key: The header key to encode.
        :param value: The int value to encode.
        """
        self._encode_key(key)
        self._buffer.write(b"\x03")
        try:
            self._buffer.write(pack("!h", value))
        except struct.error as e:
            raise InvalidIntegerValue("short", value) from e

    def encode_integer(self, key: str, value: int) -> None:
        """Encode a 32-bit int header.

        :param key: The header key to encode.
        :param value: The int value to encode.
        """
        self._encode_key(key)
        self._buffer.write(b"\x04")
        try:
            self._buffer.write(pack("!i", value))
        except struct.error as e:
            raise InvalidIntegerValue("integer", value) from e

    def encode_long(self, key: str, value: int) -> None:
        """Encode a 64-bit int header.

        :param key: The header key to encode.
        :param value: The int value to encode.
        """
        self._encode_key(key)
        self._buffer.write(b"\x05")
        try:
            self._buffer.write(pack("!q", value))
        except struct.error as e:
            raise InvalidIntegerValue("long", value) from e

    def encode_blob(self, key: str, value: bytes) -> None:
        """Encode a binary header.

        :param key: The header key to encode.
        :param value: The binary value to encode.
        """
        # Byte arrays are prefaced with a 16bit length, but are restricted
        # to a max length of 2**15 - 1
        if len(value) > MAX_HEADER_VALUE_BYTE_LENGTH:
            raise InvalidHeaderValueLength(len(value))

        self._encode_key(key)
        self._buffer.write(b"\06")
        self._buffer.write(pack("!H", len(value)))
        self._buffer.write(value)

    def encode_string(self, key: str, value: str) -> None:
        """Encode a string header.

        :param key: The header key to encode.
        :param value: The string value to encode.
        """
        utf8_string = value.encode("utf-8")

        # Strings are prefaced with a 16bit length, but are restricted
        # to a max length of 2**15 - 1
        if len(utf8_string) > MAX_HEADER_VALUE_BYTE_LENGTH:
            raise InvalidHeaderValueLength(len(utf8_string))

        self._encode_key(key)
        self._buffer.write(b"\07")
        self._buffer.write(pack("!H", len(utf8_string)))
        self._buffer.write(utf8_string)

    def encode_timestamp(self, key: str, value: datetime.datetime):
        """Encode a timestamp header.

        :param key: The header key to encode.
        :param value: The timestamp value to encode.
        """
        self._encode_key(key)
        timestamp_millis = int(value.timestamp() * 1000)
        self._buffer.write(b"\x08")
        self._buffer.write(pack("!q", timestamp_millis))

    def encode_uuid(self, key: str, value: uuid.UUID):
        """Encode a UUID header.

        :param key: The header key to encode.
        :param value: The UUID value to encode.
        """
        self._encode_key(key)
        self._buffer.write(b"\x09")
        self._buffer.write(value.bytes)


BytesLike = bytes | memoryview


_ArraySize = Literal[1] | Literal[2] | Literal[4]


class _DecodeUtils:
    """Unpacking utility functions used in the decoder.

    All methods on this class take raw bytes and return a tuple containing the value
    parsed from the bytes and the number of bytes consumed to parse that value.
    """

    UINT8_BYTE_FORMAT = "!B"
    UINT16_BYTE_FORMAT = "!H"
    UINT32_BYTE_FORMAT = "!I"
    INT8_BYTE_FORMAT = "!b"
    INT16_BYTE_FORMAT = "!h"
    INT32_BYTE_FORMAT = "!i"
    INT64_BYTE_FORMAT = "!q"

    # uint byte size to unpack format
    UINT_BYTE_FORMAT: Mapping[_ArraySize, str] = MappingProxyType(
        {
            1: UINT8_BYTE_FORMAT,
            2: UINT16_BYTE_FORMAT,
            4: UINT32_BYTE_FORMAT,
        }
    )

    @staticmethod
    def unpack_uint8(data: BytesLike) -> tuple[int, int]:
        """Parse an unsigned 8-bit integer from the bytes.

        :param data: The bytes to parse from.
        :returns: A tuple containing the (parsed integer value, bytes consumed)
        """
        value = unpack(_DecodeUtils.UINT8_BYTE_FORMAT, data[:1])[0]
        return value, 1

    @staticmethod
    def unpack_uint32(data: BytesLike) -> tuple[int, int]:
        """Parse an unsigned 32-bit integer from the bytes.

        :param data: The bytes to parse from.
        :returns: A tuple containing the (parsed integer value, bytes consumed)
        """
        value = unpack(_DecodeUtils.UINT32_BYTE_FORMAT, data[:4])[0]
        return value, 4

    @staticmethod
    def unpack_int8(data: BytesLike):
        """Parse a signed 8-bit integer from the bytes.

        :param data: The bytes to parse from.
        :returns: A tuple containing the (parsed integer value, bytes consumed)
        """
        value = unpack(_DecodeUtils.INT8_BYTE_FORMAT, data[:1])[0]
        return Byte(value), 1

    @staticmethod
    def unpack_int16(data: BytesLike) -> tuple[int, int]:
        """Parse a signed 16-bit integer from the bytes.

        :param data: The bytes to parse from.
        :returns: A tuple containing the (parsed integer value, bytes consumed)
        """
        value = unpack(_DecodeUtils.INT16_BYTE_FORMAT, data[:2])[0]
        return Short(value), 2

    @staticmethod
    def unpack_int32(data: BytesLike) -> tuple[int, int]:
        """Parse a signed 32-bit integer from the bytes.

        :param data: The bytes to parse from.
        :returns: A tuple containing the (parsed integer value, bytes consumed)
        """
        value = unpack(_DecodeUtils.INT32_BYTE_FORMAT, data[:4])[0]
        return value, 4

    @staticmethod
    def unpack_int64(data: BytesLike) -> tuple[int, int]:
        """Parse a signed 64-bit integer from the bytes.

        :param data: The bytes to parse from.
        :returns: A tuple containing the (parsed integer value, bytes consumed)
        """
        value = unpack(_DecodeUtils.INT64_BYTE_FORMAT, data[:8])[0]
        return Long(value), 8

    @staticmethod
    def unpack_byte_array(
        data: BytesLike, length_byte_size: _ArraySize = 2
    ) -> tuple[bytes, int]:
        """Parse a variable length byte array from the bytes.

        The bytes are expected to be in the following format:
            [ length ][0 ... length bytes]
        where length is an unsigned integer represented in the smallest number
        of bytes to hold the maximum length of the array.

        :param data: The bytes to parse from.
        :param length_byte_size: The byte size of the preceding integer that
            represents the length of the array. Supported values are 1, 2, and 4.
        :returns: A tuple containing the (parsed bytes, bytes consumed)
        """
        uint_byte_format = _DecodeUtils.UINT_BYTE_FORMAT[length_byte_size]
        length = unpack(uint_byte_format, data[:length_byte_size])[0]
        if length > MAX_HEADER_VALUE_BYTE_LENGTH:
            raise InvalidHeaderValueLength(length)
        bytes_end = length + length_byte_size
        array_bytes = data[length_byte_size:bytes_end]
        return bytes(array_bytes), bytes_end

    @staticmethod
    def unpack_utf8_string(
        data: BytesLike, length_byte_size: _ArraySize = 2
    ) -> tuple[str, int]:
        """Parse a variable length utf-8 string from the bytes.

        The bytes are expected to be in the following format:
            [ length ][0 ... length bytes]
        where length is an unsigned integer represented in the smallest number
        of bytes to hold the maximum length of the array and the following
        bytes are a valid utf-8 string.

        :param data: The bytes to parse from.
        :param length_byte_size: The byte size of the preceding integer that
            represents the length of the array. Supported values are 1, 2, and 4.
        :returns: A tuple containing the (parsed string, bytes consumed)
        """
        array_bytes, consumed = _DecodeUtils.unpack_byte_array(data, length_byte_size)
        return array_bytes.decode("utf-8"), consumed

    @staticmethod
    def unpack_timestamp(data: BytesLike) -> tuple[datetime.datetime, int]:
        """Parse an 8-byte timestamp from the bytes.

        The bytes are expected to be a signed 64-bit integer representing the number of
        milliseconds since the epoch.

        :param data: The bytes to parse from.
        :returns: A tuple containing the (datetime.datetime, bytes consumed).
        """
        int_value, consumed = _DecodeUtils.unpack_int64(data)
        timestamp_value = TimestampFormat.EPOCH_SECONDS.deserialize(int_value / 1000)
        return timestamp_value, consumed

    @staticmethod
    def unpack_uuid(data: BytesLike) -> tuple[uuid.UUID, int]:
        """Parse a 16-byte uuid from the bytes.

        :param data: The bytes to parse from.
        :returns: A tuple containing the (uuid, bytes consumed).
        """
        return uuid.UUID(bytes=bytes(data[:16])), 16


class EventHeaderDecoder(Iterator[tuple[str, HEADER_VALUE]]):
    """A utility class that decodes headers from bytes."""

    # Maps header type to appropriate unpacking function
    # These unpacking functions return the value and the amount unpacked
    _HEADER_TYPE_MAP: Mapping[int, Callable[[BytesLike], tuple[HEADER_VALUE, int]]] = (
        MappingProxyType(
            {
                # Boolean headers have no data bytes following the type signifier, so they
                # can just return static values.
                0: lambda b: (True, 0),  # boolean_true
                1: lambda b: (False, 0),  # boolean_false
                2: _DecodeUtils.unpack_int8,  # byte
                3: _DecodeUtils.unpack_int16,  # short
                4: _DecodeUtils.unpack_int32,  # integer
                5: _DecodeUtils.unpack_int64,  # long
                6: _DecodeUtils.unpack_byte_array,  # byte_array
                7: _DecodeUtils.unpack_utf8_string,  # string
                8: _DecodeUtils.unpack_timestamp,  # timestamp
                9: _DecodeUtils.unpack_uuid,  # uuid
            }
        )
    )

    def __init__(self, header_bytes: BytesLike) -> None:
        """Initialize an event header decoder.

        :param header_bytes: A bytes or memoryview to read headers from.
        """
        # Use a memoryview here to avoid doing a ton of copies
        if not isinstance(header_bytes, memoryview):
            header_bytes = memoryview(header_bytes)
        if len(header_bytes) > MAX_HEADERS_LENGTH:
            raise InvalidHeadersLength(len(header_bytes))
        self._data = header_bytes

    def decode_headers(self) -> HEADERS_DICT:
        """Decode all remaining headers.

        :returns: A dict containing all remaining headers read from the source.
        """
        result: HEADERS_DICT = {}
        for k, v in self:
            if k in result:
                raise DuplicateHeader(k)
            result[k] = v
        return result

    def decode_header(self) -> tuple[str, HEADER_VALUE]:
        """Decode a single key-value pair from the source.

        :returns: A single key-value pair read from the source.
        """
        key, consumed = _DecodeUtils.unpack_utf8_string(self._data, 1)
        self._advance_data(consumed)

        type, consumed = _DecodeUtils.unpack_uint8(self._data)
        self._advance_data(consumed)

        value_unpacker = self._HEADER_TYPE_MAP[type]
        value, consumed = value_unpacker(self._data)
        self._advance_data(consumed)
        return key, value

    def _advance_data(self, consumed: int):
        self._data = self._data[consumed:]

    def __iter__(self) -> Iterator[tuple[str, HEADER_VALUE]]:
        return self

    def __next__(self) -> tuple[str, HEADER_VALUE]:
        if len(self._data) == 0:
            raise StopIteration()
        return self.decode_header()


def _validate_checksum(data: bytes, checksum: int, crc: int = 0) -> None:
    # To generate the same numeric value across all Python versions and
    # platforms use crc32(data) & 0xffffffff.
    computed_checksum = crc32(data, crc) & 0xFFFFFFFF
    if checksum != computed_checksum:
        raise ChecksumMismatch(checksum, computed_checksum)
