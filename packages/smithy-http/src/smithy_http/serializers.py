from asyncio import iscoroutinefunction
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import datetime
from decimal import Decimal
from io import BytesIO
from typing import TYPE_CHECKING, Any
from urllib.parse import quote as urlquote

from smithy_core import URI
from smithy_core.codecs import Codec
from smithy_core.schemas import Schema
from smithy_core.serializers import (
    InterceptingSerializer,
    MapSerializer,
    ShapeSerializer,
    SpecificShapeSerializer,
)
from smithy_core.shapes import ShapeType
from smithy_core.traits import (
    EndpointTrait,
    HostLabelTrait,
    HTTPErrorTrait,
    HTTPHeaderTrait,
    HTTPLabelTrait,
    HTTPPayloadTrait,
    HTTPPrefixHeadersTrait,
    HTTPQueryParamsTrait,
    HTTPQueryTrait,
    HTTPResponseCodeTrait,
    HTTPTrait,
    MediaTypeTrait,
    StreamingTrait,
    TimestampFormatTrait,
)
from smithy_core.types import PathPattern, TimestampFormat
from smithy_core.utils import serialize_float

from . import tuples_to_fields
from .aio import HTTPRequest as _HTTPRequest
from .aio import HTTPResponse as _HTTPResponse
from .aio.interfaces import HTTPRequest, HTTPResponse
from .utils import join_query_params

if TYPE_CHECKING:
    from smithy_core.aio.interfaces import StreamingBlob as AsyncStreamingBlob


__all__ = ["HTTPRequestSerializer", "HTTPResponseSerializer"]


class HTTPRequestSerializer(SpecificShapeSerializer):
    """Binds a serializable shape to an HTTP request.

    The resultant HTTP request is not immediately sendable. In particular, the host of
    the destination URI is incomplete and MUST be suffixed before sending.
    """

    def __init__(
        self,
        payload_codec: Codec,
        http_trait: HTTPTrait,
        endpoint_trait: EndpointTrait | None = None,
    ) -> None:
        """Initialize an HTTPRequestSerializer.

        :param payload_codec: The codec to use to serialize the HTTP payload, if one is
            present.
        :param http_trait: The HTTP trait of the operation being handled.
        :param endpoint_trait: The optional endpoint trait of the operation being
            handled.
        """
        self._http_trait = http_trait
        self._endpoint_trait = endpoint_trait
        self._payload_codec = payload_codec
        self.result: HTTPRequest | None = None

    @contextmanager
    def begin_struct(self, schema: Schema) -> Iterator[ShapeSerializer]:
        payload: Any
        binding_serializer: HTTPRequestBindingSerializer

        host_prefix = ""
        if self._endpoint_trait is not None:
            host_prefix = self._endpoint_trait.host_prefix

        content_type = self._payload_codec.media_type

        if (payload_member := self._get_payload_member(schema)) is not None:
            if payload_member.shape_type in (ShapeType.BLOB, ShapeType.STRING):
                content_type = (
                    "application/octet-stream"
                    if payload_member.shape_type is ShapeType.BLOB
                    else "text/plain"
                )
                payload_serializer = RawPayloadSerializer()
                binding_serializer = HTTPRequestBindingSerializer(
                    payload_serializer, self._http_trait.path, host_prefix
                )
                yield binding_serializer
                payload = payload_serializer.payload
            else:
                if (media_type := payload_member.get_trait(MediaTypeTrait)) is not None:
                    content_type = media_type.value
                payload = BytesIO()
                payload_serializer = self._payload_codec.create_serializer(payload)
                binding_serializer = HTTPRequestBindingSerializer(
                    payload_serializer, self._http_trait.path, host_prefix
                )
                yield binding_serializer
        else:
            if self._get_eventstreaming_member(schema) is not None:
                content_type = "application/vnd.amazon.eventstream"
            payload = BytesIO()
            payload_serializer = self._payload_codec.create_serializer(payload)
            with payload_serializer.begin_struct(schema) as body_serializer:
                binding_serializer = HTTPRequestBindingSerializer(
                    body_serializer, self._http_trait.path, host_prefix
                )
                yield binding_serializer

        if (
            seek := getattr(payload, "seek", None)
        ) is not None and not iscoroutinefunction(seek):
            seek(0)

        # TODO: conditional on empty-ness and based on the protocol
        headers = binding_serializer.header_serializer.headers
        headers.append(("content-type", content_type))

        self.result = _HTTPRequest(
            method=self._http_trait.method,
            destination=URI(
                host=binding_serializer.host_prefix_serializer.host_prefix,
                path=binding_serializer.path_serializer.path,
                query=join_query_params(
                    params=binding_serializer.query_serializer.query_params,
                    prefix=self._http_trait.query or "",
                ),
            ),
            fields=tuples_to_fields(headers),
            body=payload,
        )

    def _get_payload_member(self, schema: Schema) -> Schema | None:
        for member in schema.members.values():
            if HTTPPayloadTrait in member:
                return member
        return None

    def _get_eventstreaming_member(self, schema: Schema) -> Schema | None:
        for member in schema.members.values():
            if (
                member.get_trait(StreamingTrait) is not None
                and member.shape_type is ShapeType.UNION
            ):
                return member
        return None


class HTTPRequestBindingSerializer(InterceptingSerializer):
    """Delegates HTTP request bindings to binding-location-specific serializers."""

    def __init__(
        self,
        payload_serializer: ShapeSerializer,
        path_pattern: PathPattern,
        host_prefix_pattern: str,
    ) -> None:
        """Initialize an HTTPRequestBindingSerializer.

        :param payload_serializer: The :py:class:`ShapeSerializer` to use to serialize
            the payload, if necessary.
        :param path_pattern: The pattern used to construct the path.
        :host_prefix_pattern: The pattern used to construct the host prefix.
        """
        self._payload_serializer = payload_serializer
        self.header_serializer = HTTPHeaderSerializer()
        self.query_serializer = HTTPQuerySerializer()
        self.path_serializer = HTTPPathSerializer(path_pattern)
        self.host_prefix_serializer = HostPrefixSerializer(
            payload_serializer, host_prefix_pattern
        )

    def before(self, schema: Schema) -> ShapeSerializer:
        if HTTPHeaderTrait in schema or HTTPPrefixHeadersTrait in schema:
            return self.header_serializer
        if HTTPQueryTrait in schema or HTTPQueryParamsTrait in schema:
            return self.query_serializer
        if HTTPLabelTrait in schema:
            return self.path_serializer
        if HostLabelTrait in schema:
            return self.host_prefix_serializer

        return self._payload_serializer

    def after(self, schema: Schema) -> None:
        pass


class HTTPResponseSerializer(SpecificShapeSerializer):
    """Binds a serializable shape to an HTTP response."""

    def __init__(
        self,
        payload_codec: Codec,
        http_trait: HTTPTrait,
    ) -> None:
        """Initialize an HTTPResponseSerializer.

        :param payload_codec: The codec to use to serialize the HTTP payload, if one is
            present.
        :param http_trait: The HTTP trait of the operation being handled.
        """
        self._http_trait = http_trait
        self._payload_codec = payload_codec
        self.result: HTTPResponse | None = None

    @contextmanager
    def begin_struct(self, schema: Schema) -> Iterator[ShapeSerializer]:
        payload: Any
        binding_serializer: HTTPResponseBindingSerializer

        if (payload_member := self._get_payload_member(schema)) is not None:
            if payload_member.shape_type in (ShapeType.BLOB, ShapeType.STRING):
                payload_serializer = RawPayloadSerializer()
                binding_serializer = HTTPResponseBindingSerializer(payload_serializer)
                yield binding_serializer
                payload = payload_serializer.payload
            else:
                payload = BytesIO()
                payload_serializer = self._payload_codec.create_serializer(payload)
                binding_serializer = HTTPResponseBindingSerializer(payload_serializer)
                yield binding_serializer
        else:
            payload = BytesIO()
            payload_serializer = self._payload_codec.create_serializer(payload)
            with payload_serializer.begin_struct(schema) as body_serializer:
                binding_serializer = HTTPResponseBindingSerializer(body_serializer)
                yield binding_serializer

        if (
            seek := getattr(payload, "seek", None)
        ) is not None and not iscoroutinefunction(seek):
            seek(0)

        default_code = self._http_trait.code
        explicit_code = binding_serializer.response_code_serializer.response_code
        if (http_error_trait := schema.get_trait(HTTPErrorTrait)) is not None:
            default_code = http_error_trait.code

        self.result = _HTTPResponse(
            fields=tuples_to_fields(binding_serializer.header_serializer.headers),
            body=payload,
            status=explicit_code or default_code,
        )

    def _get_payload_member(self, schema: Schema) -> Schema | None:
        for member in schema.members.values():
            if HTTPPayloadTrait in member:
                return member
        return None


class HTTPResponseBindingSerializer(InterceptingSerializer):
    """Delegates HTTP response bindings to binding-location-specific serializers."""

    def __init__(self, payload_serializer: ShapeSerializer) -> None:
        """Initialize an HTTPResponseBindingSerializer.

        :param payload_serializer: The :py:class:`ShapeSerializer` to use to serialize
            the payload, if necessary.
        """
        self._payload_serializer = payload_serializer
        self.header_serializer = HTTPHeaderSerializer()
        self.response_code_serializer = HTTPResponseCodeSerializer()

    def before(self, schema: Schema) -> ShapeSerializer:
        if HTTPHeaderTrait in schema or HTTPPrefixHeadersTrait in schema:
            return self.header_serializer
        if HTTPResponseCodeTrait in schema:
            return self.response_code_serializer

        return self._payload_serializer

    def after(self, schema: Schema) -> None:
        pass


class RawPayloadSerializer(SpecificShapeSerializer):
    """Binds properties of serializable shape to an HTTP payload."""

    payload: "AsyncStreamingBlob | None"
    """The serialized payload.

    This will only be non-null after serialization.
    """

    def __init__(self) -> None:
        """Initialize a RawPayloadSerializer."""
        self.payload: AsyncStreamingBlob | None = None

    def write_string(self, schema: Schema, value: str) -> None:
        self.payload = value.encode("utf-8")

    def write_blob(self, schema: Schema, value: bytes) -> None:
        self.payload = value

    def write_data_stream(self, schema: Schema, value: "AsyncStreamingBlob") -> None:
        self.payload = value


class HTTPHeaderSerializer(SpecificShapeSerializer):
    """Binds properties of a serializable shape to HTTP headers."""

    headers: list[tuple[str, str]]
    """A list of serialized headers.

    This should only be accessed after serialization.
    """

    def __init__(
        self, key: str | None = None, headers: list[tuple[str, str]] | None = None
    ) -> None:
        """Initialize an HTTPHeaderSerializer.

        :param key: An optional key to specifically write. If not set, the
            :py:class:`HTTPHeaderTrait` will be checked instead. Required when
            collecting list entries.
        :param headers: An optional list of header tuples to append to. If not
            set, one will be created.
        """
        self.headers: list[tuple[str, str]] = headers if headers is not None else []
        self._key = key

    @contextmanager
    def begin_list(self, schema: Schema, size: int) -> Iterator[ShapeSerializer]:
        key = self._key or schema.expect_trait(HTTPHeaderTrait).key
        delegate = HTTPHeaderSerializer(key=key, headers=self.headers)
        yield delegate

    @contextmanager
    def begin_map(self, schema: Schema, size: int) -> Iterator[MapSerializer]:
        prefix = schema.expect_trait(HTTPPrefixHeadersTrait).prefix
        yield HTTPHeaderMapSerializer(prefix, self.headers)

    def write_boolean(self, schema: Schema, value: bool) -> None:
        key = self._key or schema.expect_trait(HTTPHeaderTrait).key
        self.headers.append((key, "true" if value else "false"))

    def write_byte(self, schema: Schema, value: int) -> None:
        key = self._key or schema.expect_trait(HTTPHeaderTrait).key
        self.headers.append((key, str(value)))

    def write_short(self, schema: Schema, value: int) -> None:
        key = self._key or schema.expect_trait(HTTPHeaderTrait).key
        self.headers.append((key, str(value)))

    def write_integer(self, schema: Schema, value: int) -> None:
        key = self._key or schema.expect_trait(HTTPHeaderTrait).key
        self.headers.append((key, str(value)))

    def write_long(self, schema: Schema, value: int) -> None:
        key = self._key or schema.expect_trait(HTTPHeaderTrait).key
        self.headers.append((key, str(value)))

    def write_big_integer(self, schema: Schema, value: int) -> None:
        key = self._key or schema.expect_trait(HTTPHeaderTrait).key
        self.headers.append((key, str(value)))

    def write_float(self, schema: Schema, value: float) -> None:
        key = self._key or schema.expect_trait(HTTPHeaderTrait).key
        self.headers.append((key, str(value)))

    def write_double(self, schema: Schema, value: float) -> None:
        key = self._key or schema.expect_trait(HTTPHeaderTrait).key
        self.headers.append((key, str(value)))

    def write_big_decimal(self, schema: Schema, value: Decimal) -> None:
        key = self._key or schema.expect_trait(HTTPHeaderTrait).key
        self.headers.append((key, str(value.canonical())))

    def write_string(self, schema: Schema, value: str) -> None:
        key = self._key or schema.expect_trait(HTTPHeaderTrait).key
        self.headers.append((key, value))

    def write_timestamp(self, schema: Schema, value: datetime) -> None:
        key = self._key or schema.expect_trait(HTTPHeaderTrait).key
        format = TimestampFormat.HTTP_DATE
        if (trait := schema.get_trait(TimestampFormatTrait)) is not None:
            format = trait.format
        self.headers.append((key, str(format.serialize(value))))


class HTTPHeaderMapSerializer(MapSerializer):
    """Binds a mapping property of a serializeable shape to multiple HTTP headers."""

    def __init__(self, prefix: str, headers: list[tuple[str, str]]) -> None:
        """Initialize an HTTPHeaderMapSerializer.

        :param prefix: The prefix to prepend to each of the map keys.
        :param headers: The list of header tuples to append to.
        """
        self._prefix = prefix
        self._headers = headers
        self._delegate = CapturingSerializer()

    def entry(self, key: str, value_writer: Callable[[ShapeSerializer], None]):
        value_writer(self._delegate)
        assert self._delegate.result is not None  # noqa: S101
        self._headers.append((self._prefix + key, self._delegate.result))


class CapturingSerializer(SpecificShapeSerializer):
    """Directly passes along a string through a serializer."""

    result: str | None
    """The captured string.

    This will only be set after the serializer has been used.
    """

    def __init__(self) -> None:
        self.result = None

    def write_string(self, schema: Schema, value: str) -> None:
        self.result = value


class HTTPQuerySerializer(SpecificShapeSerializer):
    """Binds properties of a serializable shape to HTTP URI query params."""

    def __init__(
        self, key: str | None = None, params: list[tuple[str, str]] | None = None
    ) -> None:
        """Initialize an HTTPQuerySerializer.

        :param key: An optional key to specifically write. If not set, the
            :py:class:`HTTPQueryTrait` will be checked instead. Required when
            collecting list or map entries.
        :param headers: An optional list of header tuples to append to. If not
            set, one will be created.
        """
        self.query_params: list[tuple[str, str]] = params if params is not None else []
        self._key = key

    @contextmanager
    def begin_list(self, schema: Schema, size: int) -> Iterator[ShapeSerializer]:
        key = self._key or schema.expect_trait(HTTPQueryTrait).key
        yield HTTPQuerySerializer(key=key, params=self.query_params)

    @contextmanager
    def begin_map(self, schema: Schema, size: int) -> Iterator[MapSerializer]:
        yield HTTPQueryMapSerializer(self.query_params)

    def write_boolean(self, schema: Schema, value: bool) -> None:
        key = self._key or schema.expect_trait(HTTPQueryTrait).key
        self.query_params.append((key, "true" if value else "false"))

    def write_byte(self, schema: Schema, value: int) -> None:
        self.write_integer(schema, value)

    def write_short(self, schema: Schema, value: int) -> None:
        self.write_integer(schema, value)

    def write_integer(self, schema: Schema, value: int) -> None:
        key = self._key or schema.expect_trait(HTTPQueryTrait).key
        self.query_params.append((key, str(value)))

    def write_long(self, schema: Schema, value: int) -> None:
        self.write_integer(schema, value)

    def write_big_integer(self, schema: Schema, value: int) -> None:
        self.write_integer(schema, value)

    def write_float(self, schema: Schema, value: float) -> None:
        key = self._key or schema.expect_trait(HTTPQueryTrait).key
        self.query_params.append((key, serialize_float(value)))

    def write_double(self, schema: Schema, value: float) -> None:
        self.write_float(schema, value)

    def write_big_decimal(self, schema: Schema, value: Decimal) -> None:
        key = self._key or schema.expect_trait(HTTPQueryTrait).key
        self.query_params.append((key, serialize_float(value)))

    def write_string(self, schema: Schema, value: str) -> None:
        key = self._key or schema.expect_trait(HTTPQueryTrait).key
        self.query_params.append((key, urlquote(value, safe="")))

    def write_timestamp(self, schema: Schema, value: datetime) -> None:
        key = self._key or schema.expect_trait(HTTPQueryTrait).key
        format = TimestampFormat.DATE_TIME
        if (trait := schema.get_trait(TimestampFormatTrait)) is not None:
            format = trait.format
        self.query_params.append((key, str(format.serialize(value))))


class HTTPPathSerializer(SpecificShapeSerializer):
    """Binds properties of a serializable shape to the HTTP URI path."""

    def __init__(self, path_pattern: PathPattern) -> None:
        """Initialize an HTTPPathSerializer.

        :param path_pattern: The pattern to bind properties to. This is also used to
            detect greedy labels, which have different escaping requirements.
        """
        self._path_pattern = path_pattern
        self._path_params: dict[str, str] = {}

    @property
    def path(self) -> str:
        """Get the formatted path.

        This must not be accessed before serialization is complete, otherwise an
        exception will be raised.
        """
        return self._path_pattern.format(**self._path_params)

    def write_boolean(self, schema: Schema, value: bool) -> None:
        self._path_params[schema.expect_member_name()] = "true" if value else "false"

    def write_byte(self, schema: Schema, value: int) -> None:
        self.write_integer(schema, value)

    def write_short(self, schema: Schema, value: int) -> None:
        self.write_integer(schema, value)

    def write_integer(self, schema: Schema, value: int) -> None:
        self._path_params[schema.expect_member_name()] = str(value)

    def write_long(self, schema: Schema, value: int) -> None:
        self.write_integer(schema, value)

    def write_big_integer(self, schema: Schema, value: int) -> None:
        self.write_integer(schema, value)

    def write_float(self, schema: Schema, value: float) -> None:
        self._path_params[schema.expect_member_name()] = serialize_float(value)

    def write_double(self, schema: Schema, value: float) -> None:
        self.write_float(schema, value)

    def write_big_decimal(self, schema: Schema, value: Decimal) -> None:
        self._path_params[schema.expect_member_name()] = serialize_float(value)

    def write_string(self, schema: Schema, value: str) -> None:
        key = schema.expect_member_name()
        if key in self._path_pattern.greedy_labels:
            value = urlquote(value)
        else:
            value = urlquote(value, safe="")
        self._path_params[schema.expect_member_name()] = value

    def write_timestamp(self, schema: Schema, value: datetime) -> None:
        format = TimestampFormat.DATE_TIME
        if (trait := schema.get_trait(TimestampFormatTrait)) is not None:
            format = trait.format
        self._path_params[schema.expect_member_name()] = urlquote(
            str(format.serialize(value))
        )


class HTTPQueryMapSerializer(MapSerializer):
    """Binds properties of a serializable shape to a map of HTTP query params."""

    def __init__(self, query_params: list[tuple[str, str]]) -> None:
        """Initialize an HTTPQueryMapSerializer.

        :param query_params: The list of query param tuples to append to.
        """
        self._query_params = query_params
        self._delegate = CapturingSerializer()

    def entry(self, key: str, value_writer: Callable[[ShapeSerializer], None]):
        value_writer(self._delegate)
        assert self._delegate.result is not None  # noqa: S101
        self._query_params.append((key, urlquote(self._delegate.result, safe="")))


class HostPrefixSerializer(SpecificShapeSerializer):
    """Binds properites of a serializable shape to the HTTP URI host.

    These properties are also bound to the payload.
    """

    def __init__(
        self, payload_serializer: ShapeSerializer, host_prefix_pattern: str
    ) -> None:
        """Initialize a HostPrefixSerializer.

        :param host_prefix_pattern: The pattern to bind properties to.
        :param payload_serializer: The payload serializer to additionally write
            properties to.
        """
        self._prefix_params: dict[str, str] = {}
        self._host_prefix_pattern = host_prefix_pattern
        self._payload_serializer = payload_serializer

    @property
    def host_prefix(self) -> str:
        """The formatted host prefix.

        This must not be accessed before serialization is complete, otherwise an
        exception will be raised.
        """
        return self._host_prefix_pattern.format(**self._prefix_params)

    def write_string(self, schema: Schema, value: str) -> None:
        self._payload_serializer.write_string(schema, value)
        self._prefix_params[schema.expect_member_name()] = urlquote(value, safe=".")


class HTTPResponseCodeSerializer(SpecificShapeSerializer):
    """Binds properties of a serializable shape to the HTTP response code."""

    response_code: int | None
    """The bound response code, or None if one hasn't been bound."""

    def __init__(self) -> None:
        """Initialize an HTTPResponseCodeSerializer."""
        self.response_code: int | None = None

    def write_byte(self, schema: Schema, value: int) -> None:
        self.response_code = value

    def write_short(self, schema: Schema, value: int) -> None:
        self.response_code = value

    def write_integer(self, schema: Schema, value: int) -> None:
        self.response_code = value
