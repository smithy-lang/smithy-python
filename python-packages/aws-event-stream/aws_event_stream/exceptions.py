"""Binary Event Stream support for the application/vnd.amazon.eventstream format."""

from dataclasses import dataclass
from typing import Any

from smithy_core.exceptions import SmithyException

_MAX_HEADERS_LENGTH = 128 * 1024  # 128 Kb
_MAX_PAYLOAD_LENGTH = 16 * 1024**2  # 16 Mb


class EventError(SmithyException):
    pass


@dataclass
class UnexpectedEventError(EventError):
    code: str
    message: str


class DuplicateHeader(EventError):
    """Duplicate header found in the event."""

    def __init__(self, header: str):
        message = f'Duplicate header present: "{header}"'
        super().__init__(message)


class InvalidHeadersLength(EventError):
    """Headers length is longer than the maximum."""

    def __init__(self, length: int):
        message = (
            f"Header length of {length} exceeded the maximum of {_MAX_HEADERS_LENGTH}"
        )
        super().__init__(message)


class InvalidHeaderValueLength(EventError):
    def __init__(self, length: int):
        message = (
            f"Header bytes value exceeds max serialization "
            f"length of (32 KiB - 1) at {length} bytes"
        )
        super().__init__(message)


class InvalidHeaderValue(EventError):
    def __init__(self, value: Any):
        message = f"Invalid header value type: {type(value)}"
        super().__init__(message)
        self.value = value


class InvalidPayloadLength(EventError):
    """Payload length is longer than the maximum."""

    def __init__(self, length: int):
        message = (
            f"Payload length of {length} exceeded the maximum of {_MAX_PAYLOAD_LENGTH}"
        )
        super().__init__(message)


class ChecksumMismatch(EventError):
    """Calculated checksum did not match the expected checksum."""

    def __init__(self, expected: int, calculated: int):
        message = f"Checksum mismatch: expected 0x{expected:08x}, calculated 0x{calculated:08x}"
        super().__init__(message)
