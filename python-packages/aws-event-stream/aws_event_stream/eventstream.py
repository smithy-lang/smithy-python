# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Binary Event Stream support for the application/vnd.amazon.eventstream format."""

import datetime
import uuid
from binascii import crc32
from collections.abc import AsyncIterator, Callable, Mapping
from dataclasses import dataclass
from struct import pack, unpack
from typing import Any, Protocol

from .exceptions import (
    ChecksumMismatch,
    DuplicateHeader,
    HeaderBytesExceedMaxLength,
    HeaderValueBytesExceedMaxLength,
    InvalidHeadersLength,
    InvalidHeaderValue,
    InvalidPayloadLength,
    ParserError,
    PayloadBytesExceedMaxLength,
)
from .structures import BufferableByteStream

# byte length of the prelude (total_length + header_length + prelude_crc)
_PRELUDE_LENGTH = 12
_MAX_HEADERS_LENGTH = 128 * 1024  # 128 Kb
_MAX_HEADER_VALUE_BYTE_LENGTH = 32 * 1024 - 1
_MAX_PAYLOAD_LENGTH = 16 * 1024**2  # 16 Mb

HEADER_VALUE = bool | bytes | int | str


@dataclass
class HeaderValue[T]:
    """A data class for explicit header serialization.

    This is used to represent types that Python doesn't natively have distinctions for,
    notably fixed-size integers.
    """

    value: T


class Int8HeaderValue(HeaderValue[int]):
    """Value that should be explicitly serialized as an int8."""


class Int16HeaderValue(HeaderValue[int]):
    """Value that should be explicitly serialized as an int16."""


class Int32HeaderValue(HeaderValue[int]):
    """Value that should be explicitly serialized as an int32."""


class Int64HeaderValue(HeaderValue[int]):
    """Value that should be explicitly serialized as an int64."""


type NumericHeaderValue = Int8HeaderValue | Int16HeaderValue | Int32HeaderValue | Int64HeaderValue


# Possible types for serializing headers differs from possible types returned when decoding
HEADER_SERIALIZATION_VALUE = (
    bool | bytes | int | str | uuid.UUID | datetime.datetime | NumericHeaderValue
)
HEADERS_SERIALIZATION_DICT = Mapping[str, HEADER_SERIALIZATION_VALUE]


class EventStreamMessageSerializer:
    DEFAULT_INT_TYPE: type[NumericHeaderValue] = Int32HeaderValue

    def serialize(self, headers: HEADERS_SERIALIZATION_DICT, payload: bytes) -> bytes:
        # TODO: Investigate preformance of this once we can make requests
        if len(payload) > _MAX_PAYLOAD_LENGTH:
            raise PayloadBytesExceedMaxLength(len(payload))

        # The encoded headers are variable length and this length
        # is required to generate the prelude, generate the headers first
        encoded_headers = self.encode_headers(headers)
        if len(encoded_headers) > _MAX_HEADERS_LENGTH:
            raise HeaderBytesExceedMaxLength(len(encoded_headers))
        prelude_bytes = self._encode_prelude(encoded_headers, payload)

        # Calculate the prelude_crc and it's byte representation
        prelude_crc = self._calculate_checksum(prelude_bytes)
        prelude_crc_bytes = pack("!I", prelude_crc)
        messages_bytes = prelude_crc_bytes + encoded_headers + payload

        # Calculate the checksum continuing from the prelude crc
        final_crc = self._calculate_checksum(messages_bytes, crc=prelude_crc)
        final_crc_bytes = pack("!I", final_crc)
        return prelude_bytes + messages_bytes + final_crc_bytes

    def encode_headers(self, headers: HEADERS_SERIALIZATION_DICT) -> bytes:
        encoded = b""
        for key, val in headers.items():
            encoded += self._encode_header_key(key)
            encoded += self._encode_header_val(val)
        return encoded

    def _encode_header_key(self, key: str) -> bytes:
        enc = key.encode("utf-8")
        return pack("B", len(enc)) + enc

    def _encode_header_val(self, val: HEADER_SERIALIZATION_VALUE) -> bytes:
        # Handle booleans first to avoid being viewed as ints
        if val is True:
            return b"\x00"
        elif val is False:
            return b"\x01"

        if isinstance(val, int):
            val = self.DEFAULT_INT_TYPE(val)

        match val:
            case Int8HeaderValue():
                return b"\x02" + pack("!b", val.value)
            case Int16HeaderValue():
                return b"\x03" + pack("!h", val.value)
            case Int32HeaderValue():
                return b"\x04" + pack("!i", val.value)
            case Int64HeaderValue():
                return b"\x05" + pack("!q", val.value)
            case bytes():
                # Byte arrays are prefaced with a 16bit length, but are restricted
                # to a max length of 2**15 - 1, enforce this explicitly
                if len(val) > _MAX_HEADER_VALUE_BYTE_LENGTH:
                    raise HeaderValueBytesExceedMaxLength(len(val))
                return b"\x06" + pack("!H", len(val)) + val
            case str():
                utf8_string = val.encode("utf-8")
                # Strings are prefaced with a 16bit length, but are restricted
                # to a max length of 2**15 - 1, enforce this explicitly
                if len(utf8_string) > _MAX_HEADER_VALUE_BYTE_LENGTH:
                    raise HeaderValueBytesExceedMaxLength(len(utf8_string))
                return b"\x07" + pack("!H", len(utf8_string)) + utf8_string
            case datetime.datetime():
                ms_timestamp = int(val.timestamp() * 1000)
                return b"\x08" + pack("!q", ms_timestamp)
            case uuid.UUID():
                return b"\x09" + val.bytes

        raise InvalidHeaderValue(val)

    def _encode_prelude(self, encoded_headers: bytes, payload: bytes) -> bytes:
        header_length = len(encoded_headers)
        payload_length = len(payload)
        total_length = header_length + payload_length + 16
        return pack("!II", total_length, header_length)

    def _calculate_checksum(self, data: bytes, crc: int = 0) -> int:
        return crc32(data, crc) & 0xFFFFFFFF


class BaseEvent:
    """Base class for typed events sent over event stream with service.

    :param payload: bytes payload to be sent with event
    :param event_payload: boolean stating if event has a payload
    """

    def __init__(self, payload: bytes, event_payload: bool | None = None):
        self.payload = payload
        self.event_payload = event_payload
        self.event = True


class BaseStream:
    """Base class for EventStream established between client and Transcribe Service.

    These streams will always be established automatically by the client.
    """

    def __init__(
        self,
        input_stream: Any = None,
        event_serializer: Any = None,
        eventstream_serializer: Any = None,
        event_signer: Any = None,
        initial_signature: Any = None,
        credential_resolver: Any = None,
    ):
        if input_stream is None:
            input_stream = BufferableByteStream()
        self._input_stream: BufferableByteStream = input_stream
        # TODO: Cant type due to circular import
        self._event_serializer = event_serializer
        if eventstream_serializer is None:
            eventstream_serializer = EventStreamMessageSerializer()
        self._eventstream_serializer = eventstream_serializer
        self._event_signer = event_signer
        self._prior_signature: Any = initial_signature
        self._credential_resolver = credential_resolver

    async def send_event(self, event: BaseEvent):
        headers, payload = self._event_serializer.serialize(event)
        event_bytes = self._eventstream_serializer.serialize(headers, payload)
        signed_bytes = await self._sign_event(event_bytes)
        self._input_stream.write(signed_bytes)

    async def end_stream(self):
        signed_bytes = await self._sign_event(b"")
        self._input_stream.write(signed_bytes)
        self._input_stream.end_stream()

    async def _sign_event(self, event_bytes: bytes):
        creds = await self._credential_resolver.get_credentials()
        signed_headers = self._event_signer.sign(
            event_bytes, self._prior_signature, creds
        )
        self._prior_signature = signed_headers.get(":chunk-signature")
        return self._eventstream_serializer.serialize(signed_headers, event_bytes)


class DecodeUtils:
    """Unpacking utility functions used in the decoder.

    All methods on this class take raw bytes and return  a tuple containing the value
    parsed from the bytes and the number of bytes consumed to parse that value.
    """

    UINT8_BYTE_FORMAT = "!B"
    UINT16_BYTE_FORMAT = "!H"
    UINT32_BYTE_FORMAT = "!I"
    INT8_BYTE_FORMAT = "!b"
    INT16_BYTE_FORMAT = "!h"
    INT32_BYTE_FORMAT = "!i"
    INT64_BYTE_FORMAT = "!q"
    PRELUDE_BYTE_FORMAT = "!III"

    # uint byte size to unpack format
    UINT_BYTE_FORMAT = {
        1: UINT8_BYTE_FORMAT,
        2: UINT16_BYTE_FORMAT,
        4: UINT32_BYTE_FORMAT,
    }

    @staticmethod
    def unpack_true(data: bytes) -> tuple[bool, int]:
        """This method consumes none of the provided bytes and returns True.

        :param data: The bytes to parse from. This is ignored in this method.
        :returns: The tuple (True, 0)
        """
        return True, 0

    @staticmethod
    def unpack_false(data: bytes) -> tuple[bool, int]:
        """This method consumes none of the provided bytes and returns False.

        :param data: The bytes to parse from. This is ignored in this method.
        :returns: The tuple (False, 0)
        """
        return False, 0

    @staticmethod
    def unpack_uint8(data: bytes) -> tuple[int, int]:
        """Parse an unsigned 8-bit integer from the bytes.

        :param data: The bytes to parse from.
        :returns: A tuple containing the (parsed integer value, bytes consumed)
        """
        value = unpack(DecodeUtils.UINT8_BYTE_FORMAT, data[:1])[0]
        return value, 1

    @staticmethod
    def unpack_uint32(data: bytes) -> tuple[int, int]:
        """Parse an unsigned 32-bit integer from the bytes.

        :param data: The bytes to parse from.
        :returns: A tuple containing the (parsed integer value, bytes consumed)
        """
        value = unpack(DecodeUtils.UINT32_BYTE_FORMAT, data[:4])[0]
        return value, 4

    @staticmethod
    def unpack_int8(data: bytes):
        """Parse a signed 8-bit integer from the bytes.

        :param data: The bytes to parse from.
        :returns: A tuple containing the (parsed integer value, bytes consumed)
        """
        value = unpack(DecodeUtils.INT8_BYTE_FORMAT, data[:1])[0]
        return value, 1

    @staticmethod
    def unpack_int16(data: bytes) -> tuple[int, int]:
        """Parse a signed 16-bit integer from the bytes.

        :param data: The bytes to parse from.
        :returns: A tuple containing the (parsed integer value, bytes consumed)
        """
        value = unpack(DecodeUtils.INT16_BYTE_FORMAT, data[:2])[0]
        return value, 2

    @staticmethod
    def unpack_int32(data: bytes) -> tuple[int, int]:
        """Parse a signed 32-bit integer from the bytes.

        :param data: The bytes to parse from.
        :returns: A tuple containing the (parsed integer value, bytes consumed)
        """
        value = unpack(DecodeUtils.INT32_BYTE_FORMAT, data[:4])[0]
        return value, 4

    @staticmethod
    def unpack_int64(data: bytes) -> tuple[int, int]:
        """Parse a signed 64-bit integer from the bytes.

        :param data: The bytes to parse from.
        :returns: A tuple containing the (parsed integer value, bytes consumed)
        """
        value = unpack(DecodeUtils.INT64_BYTE_FORMAT, data[:8])[0]
        return value, 8

    @staticmethod
    def unpack_byte_array(data: bytes, length_byte_size: int = 2) -> tuple[bytes, int]:
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
        uint_byte_format = DecodeUtils.UINT_BYTE_FORMAT[length_byte_size]
        length = unpack(uint_byte_format, data[:length_byte_size])[0]
        bytes_end = length + length_byte_size
        array_bytes = data[length_byte_size:bytes_end]
        return array_bytes, bytes_end

    @staticmethod
    def unpack_utf8_string(data: bytes, length_byte_size: int = 2) -> tuple[str, int]:
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
        array_bytes, consumed = DecodeUtils.unpack_byte_array(data, length_byte_size)
        return array_bytes.decode("utf-8"), consumed

    @staticmethod
    def unpack_uuid(data: bytes) -> tuple[bytes, int]:
        """Parse a 16-byte uuid from the bytes.

        :param data: The bytes to parse from.
        :returns: A tuple containing the (uuid bytes, bytes consumed).
        """
        return data[:16], 16

    @staticmethod
    def unpack_prelude(data: bytes) -> tuple[tuple[Any, ...], int]:
        """Parse the prelude for an event stream message from the bytes.

        The prelude for an event stream message has the following format:
            [total_length][header_length][prelude_crc]
        where each field is an unsigned 32-bit integer.

        :param data: The bytes to parse from.
        :returns: A tuple of ((total_length, headers_length, prelude_crc),
            consumed)
        """
        return (unpack(DecodeUtils.PRELUDE_BYTE_FORMAT, data), _PRELUDE_LENGTH)


def _validate_checksum(data: bytes, checksum: int, crc: int = 0) -> None:
    # To generate the same numeric value across all Python versions and
    # platforms use crc32(data) & 0xffffffff.
    computed_checksum = crc32(data, crc) & 0xFFFFFFFF
    if checksum != computed_checksum:
        raise ChecksumMismatch(checksum, computed_checksum)


class MessagePrelude:
    """Represents the prelude of an event stream message."""

    def __init__(self, total_length: int, headers_length: int, crc: int):
        self.total_length = total_length
        self.headers_length = headers_length
        self.crc = crc

    @property
    def payload_length(self) -> int:
        """Calculates the total payload length.

        The extra minus 4 bytes is for the message CRC.
        """
        return self.total_length - self.headers_length - _PRELUDE_LENGTH - 4

    @property
    def payload_end(self) -> int:
        """Calculates the byte offset for the end of the message payload.

        The extra minus 4 bytes is for the message CRC.
        """
        return self.total_length - 4

    @property
    def headers_end(self) -> int:
        """Calculates the byte offset for the end of the message headers."""
        return _PRELUDE_LENGTH + self.headers_length


class EventStreamMessage:
    """Represents an event stream message."""

    def __init__(
        self,
        prelude: MessagePrelude,
        headers: dict[str, HEADER_VALUE],
        payload: bytes,
        crc: int,
    ):
        self.prelude = prelude
        self.headers = headers
        self.payload = payload
        self.crc = crc

    def to_response_dict(self, status_code: int = 200) -> dict[str, Any]:
        message_type = self.headers.get(":message-type")
        if message_type == "error" or message_type == "exception":
            status_code = 400
        return {
            "status_code": status_code,
            "headers": self.headers,
            "body": self.payload,
        }


class EventStreamHeaderParser:
    """Parses the event headers from an event stream message.

    Expects all of the header data upfront and creates a dictionary of headers to
    return. This object can be reused multiple times to parse the headers from multiple
    event stream messages.
    """

    # Maps header type to appropriate unpacking function
    # These unpacking functions return the value and the amount unpacked
    _HEADER_TYPE_MAP: dict[int, Callable[[bytes], tuple[HEADER_VALUE, int]]] = {
        # boolean_true
        0: DecodeUtils.unpack_true,
        # boolean_false
        1: DecodeUtils.unpack_false,
        # byte
        2: DecodeUtils.unpack_int8,
        # short
        3: DecodeUtils.unpack_int16,
        # integer
        4: DecodeUtils.unpack_int32,
        # long
        5: DecodeUtils.unpack_int64,
        # byte_array
        6: DecodeUtils.unpack_byte_array,
        # string
        7: DecodeUtils.unpack_utf8_string,
        # timestamp
        8: DecodeUtils.unpack_int64,
        # uuid
        9: DecodeUtils.unpack_uuid,
    }

    def __init__(self):
        self._data: Any = None

    def parse(self, data: bytes) -> dict[str, HEADER_VALUE]:
        """Parses the event stream headers from an event stream message.

        :param data: The bytes that correspond to the headers section of an event stream
            message.
        :returns: A dictionary of header key, value pairs.
        """
        self._data = data
        return self._parse_headers()

    def _parse_headers(self) -> dict[str, HEADER_VALUE]:
        headers: dict[str, HEADER_VALUE] = {}
        while self._data:
            name, value = self._parse_header()
            if name in headers:
                raise DuplicateHeader(name)
            headers[name] = value
        return headers

    def _parse_header(self) -> tuple[str, HEADER_VALUE]:
        name = self._parse_name()
        value = self._parse_value()
        return name, value

    def _parse_name(self) -> str:
        name, consumed = DecodeUtils.unpack_utf8_string(self._data, 1)
        self._advance_data(consumed)
        return name

    def _parse_type(self) -> int:
        type, consumed = DecodeUtils.unpack_uint8(self._data)
        self._advance_data(consumed)
        return type

    def _parse_value(self) -> HEADER_VALUE:
        header_type = self._parse_type()
        value_unpacker = self._HEADER_TYPE_MAP[header_type]
        value, consumed = value_unpacker(self._data)
        self._advance_data(consumed)
        return value

    def _advance_data(self, consumed: int):
        self._data = self._data[consumed:]


class EventStreamBuffer:
    """Streaming based event stream buffer.

    A buffer class that wraps bytes from an event stream providing parsed messages as
    they become available via an iterable interface.
    """

    def __init__(self):
        self._data: bytes = b""
        self._prelude: MessagePrelude | None = None
        self._header_parser = EventStreamHeaderParser()

    def add_data(self, data: bytes):
        """Add data to the buffer.

        :param data: The bytes to add to the buffer to be used when parsing.
        """
        self._data += data

    def _validate_prelude(self, prelude: MessagePrelude):
        if prelude.headers_length > _MAX_HEADERS_LENGTH:
            raise InvalidHeadersLength(prelude.headers_length)

        if prelude.payload_length > _MAX_PAYLOAD_LENGTH:
            raise InvalidPayloadLength(prelude.payload_length)

    def _parse_prelude(self) -> MessagePrelude:
        prelude_bytes = self._data[:_PRELUDE_LENGTH]
        raw_prelude, _ = DecodeUtils.unpack_prelude(prelude_bytes)
        prelude = MessagePrelude(*raw_prelude)
        self._validate_prelude(prelude)

        # The minus 4 removes the prelude crc from the bytes to be checked
        _validate_checksum(prelude_bytes[: _PRELUDE_LENGTH - 4], prelude.crc)
        return prelude

    def _parse_headers(self) -> dict[str, HEADER_VALUE]:
        if not self._prelude:
            raise ParserError("Attempted to parse headers with missing prelude.")
        header_bytes = self._data[_PRELUDE_LENGTH : self._prelude.headers_end]
        return self._header_parser.parse(header_bytes)

    def _parse_payload(self) -> bytes:
        if not self._prelude:
            raise ParserError("Attempted to parse payload with missing prelude.")
        prelude = self._prelude
        payload_bytes = self._data[prelude.headers_end : prelude.payload_end]
        return payload_bytes

    def _parse_message_crc(self) -> int:
        if not self._prelude:
            raise ParserError("Attempted to parse crc with missing prelude.")
        prelude = self._prelude
        crc_bytes = self._data[prelude.payload_end : prelude.total_length]
        message_crc, _ = DecodeUtils.unpack_uint32(crc_bytes)
        return message_crc

    def _parse_message_bytes(self) -> bytes:
        if not self._prelude:
            raise ParserError("Attempted to parse message with missing prelude.")
        # The minus 4 includes the prelude crc to the bytes to be checked
        message_bytes = self._data[_PRELUDE_LENGTH - 4 : self._prelude.payload_end]
        return message_bytes

    def _validate_message_crc(self) -> int:
        if not self._prelude:
            raise ParserError("Attempted to parse message with missing prelude.")
        message_crc = self._parse_message_crc()
        message_bytes = self._parse_message_bytes()
        _validate_checksum(message_bytes, message_crc, crc=self._prelude.crc)
        return message_crc

    def _parse_message(self) -> EventStreamMessage:
        if not self._prelude:
            raise ParserError("Attempted to parse message with missing prelude.")
        crc = self._validate_message_crc()
        headers = self._parse_headers()
        payload = self._parse_payload()
        message = EventStreamMessage(self._prelude, headers, payload, crc)
        self._prepare_for_next_message()
        return message

    def _prepare_for_next_message(self):
        if not self._prelude:
            raise ParserError("Attempted to parse message with missing prelude.")
        # Advance the data and reset the current prelude
        self._data = self._data[self._prelude.total_length :]
        self._prelude = None

    def next(self) -> EventStreamMessage:
        """Provides the next available message parsed from the stream."""
        if len(self._data) < _PRELUDE_LENGTH:
            raise StopIteration()

        if self._prelude is None:
            self._prelude = self._parse_prelude()

        if len(self._data) < self._prelude.total_length:
            raise StopIteration()

        return self._parse_message()

    def __next__(self):
        return self.next()

    def __iter__(self):
        return self


class EventParser(Protocol):
    def parse(self, event: EventStreamMessage) -> Any: ...


class EventStream:
    """Wrapper class for an event stream body.

    This wraps the underlying streaming body, parsing it for individual events and
    yielding them as they come available through the async iterator interface.
    """

    def __init__(self, raw_stream: Any, parser: EventParser):
        self._raw_stream = raw_stream
        self._parser = parser
        self._event_generator: AsyncIterator[EventStreamMessage] = (
            self._create_raw_event_generator()
        )

    async def __aiter__(self):
        async for event in self._event_generator:
            parsed_event = self._parser.parse(event)
            yield parsed_event

    async def _create_raw_event_generator(self) -> AsyncIterator[EventStreamMessage]:
        event_stream_buffer = EventStreamBuffer()
        async for chunk in self._raw_stream.chunks():
            event_stream_buffer.add_data(chunk)
            for event in event_stream_buffer:
                yield event
