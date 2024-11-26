"""Binary Event Stream support for the application/vnd.amazon.eventstream format."""

from typing import Any

from smithy_core.exceptions import SmithyException

_MAX_HEADERS_LENGTH = 128 * 1024  # 128 Kb
_MAX_PAYLOAD_LENGTH = 16 * 1024**2  # 16 Mb


class EventError(SmithyException):
    """Base error for all errors thrown during event stream handling."""


class UnmodeledEventError(EventError):
    """Unmodeled event error was read from the event stream.

    These classes of errors tend to be internal server errors or other unexpected errors
    on the service side.
    """

    code: str
    """A code identifying the class of error."""

    message: str
    """The explanation of the error sent over the event stream."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"Received unmodeled event error: {code} - {message}")


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


class InvalidIntegerValue(EventError):
    def __init__(self, size: str, value: int):
        message = (
            f"Invalid {size} value: {value}. The Byte, Short, and Long types may be "
            f"used to specify the size of the int. Unspecified ints are assumed to "
            f"be 32-bit."
        )
        super().__init__(message)


class InvalidEventBytes(EventError):
    def __init__(self) -> None:
        message = "Invalid event bytes."
        super().__init__(message)


class MissingInitialResponse(EventError):
    def __init__(self) -> None:
        super().__init__("Expected an initial response, but none was found.")
