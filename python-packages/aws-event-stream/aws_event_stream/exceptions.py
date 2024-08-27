"""Binary Event Stream support for the application/vnd.amazon.eventstream format."""

from typing import Any

_MAX_HEADERS_LENGTH = 128 * 1024  # 128 Kb
_MAX_PAYLOAD_LENGTH = 16 * 1024**2  # 16 Mb


class ParserError(Exception):
    """Base binary flow encoding parsing exception."""


class DuplicateHeader(ParserError):
    """Duplicate header found in the event."""

    def __init__(self, header: str):
        message = f'Duplicate header present: "{header}"'
        super().__init__(message)


class InvalidHeadersLength(ParserError):
    """Headers length is longer than the maximum."""

    def __init__(self, length: int):
        message = (
            f"Header length of {length} exceeded the maximum of {_MAX_HEADERS_LENGTH}"
        )
        super().__init__(message)


class InvalidPayloadLength(ParserError):
    """Payload length is longer than the maximum."""

    def __init__(self, length: int):
        message = (
            f"Payload length of {length} exceeded the maximum of {_MAX_PAYLOAD_LENGTH}"
        )
        super().__init__(message)


class ChecksumMismatch(ParserError):
    """Calculated checksum did not match the expected checksum."""

    def __init__(self, expected: int, calculated: int):
        message = f"Checksum mismatch: expected 0x{expected:08x}, calculated 0x{calculated:08x}"
        super().__init__(message)


class NoInitialResponseError(ParserError):
    """An event of type initial-response was not received.

    This exception is raised when the event stream produced no events or the first event
    in the stream was not of the initial-response type.
    """

    def __init__(self):
        message = "First event was not of the initial-response type"
        super().__init__(message)


class SerializationError(Exception):
    """Base binary flow encoding serialization exception."""


class InvalidHeaderValue(SerializationError):
    def __init__(self, value: Any):
        message = f"Invalid header value type: {type(value)}"
        super().__init__(message)
        self.value = value


class HeaderBytesExceedMaxLength(SerializationError):
    def __init__(self, length: int):
        message = (
            f"Headers exceeded max serialization "
            f"length of 128 KiB at {length} bytes"
        )
        super().__init__(message)


class HeaderValueBytesExceedMaxLength(SerializationError):
    def __init__(self, length: int):
        message = (
            f"Header bytes value exceeds max serialization "
            f"length of (32 KiB - 1) at {length} bytes"
        )
        super().__init__(message)


class PayloadBytesExceedMaxLength(SerializationError):
    def __init__(self, length: int):
        message = (
            f"Payload exceeded max serialization " f"length of 16 MiB at {length} bytes"
        )
        super().__init__(message)
