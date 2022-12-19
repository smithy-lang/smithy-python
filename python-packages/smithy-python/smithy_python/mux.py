import functools
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any, Generic, TypeVar
from urllib.parse import parse_qs

from smithy_python.interfaces.http import Request

# Represents an operation name
OP = TypeVar("OP")

# Represents a service name
S = TypeVar("S")


@dataclass()
class ServiceCoordinate(Generic[S, OP]):
    """Identifies an operation on a service."""

    service: S
    operation: OP


@dataclass()
class PathLiteralSegment:
    """Represents a path segment that has a static value."""

    value: str


@dataclass()
class PathLabelSegment:
    """Represents a path segment that has a single variable value."""


@dataclass()
class PathGreedySegment:
    """Represents one or more path segments with variable values."""


PathSegment = PathLiteralSegment | PathLabelSegment | PathGreedySegment


@dataclass()
class QueryLiteralSegment:
    """Represents a query key with a static value."""

    key: str
    value: str | None


@dataclass()
class QueryValueSegment:
    """Represents a query key with a variable value."""

    key: str


QuerySegment = QueryLiteralSegment | QueryValueSegment


@functools.total_ordering
class UriSpec(Generic[S, OP]):
    _EMPTY_PATHS = ("", "/")

    def __init__(
        self,
        target: ServiceCoordinate[S, OP],
        method: str = "GET",
        path_segments: list[PathSegment] | None = None,
        query_segments: list[QuerySegment] | None = None,
    ):
        """Represents the conditions to identify a single operation.

        :param target: The service and operation that this spec targets.
        :param method: The expected HTTP method for the operation.
        :param path_segments: A list of the expected path segments for the operation.
        :param query_segments: A list of the expected query segments for the operation.
        """
        self._method = method
        self._path_segments = path_segments or []
        self._query_segments = query_segments or []
        self._rank = len(self._path_segments) + len(self._query_segments)
        self._target = target

    @property
    def target(self) -> ServiceCoordinate[S, OP]:
        """Returns the target service and operation for the spec."""
        return self._target

    def match(self, request: Request) -> bool:
        """Determines whether a given request satisfies the operation's spec.

        :param request: The request to inspect.
        :return: True if the request matches the operation's spec.
        """
        if request.method != self._method:
            return False

        if request.url.path is None or request.url.path in self._EMPTY_PATHS:
            # Both of these cases would produce [''] after a split, which isn't
            # what we want because they both represent the 0 segment case.
            request_path_segments = []
        else:
            request_path_segments = request.url.path.strip("/").split("/")

        request_path_index = 0
        for i, segment in enumerate(self._path_segments):
            if request_path_index >= len(request_path_segments):
                return False

            path_segment = request_path_segments[request_path_index]
            match segment:
                case PathLiteralSegment():
                    if segment.value != path_segment:
                        return False
                    request_path_index += 1
                case PathLabelSegment():
                    request_path_index += 1
                case PathGreedySegment():
                    # Greedy labels can consume any number of segments, so we can just
                    # immediately advance to the last X segments of the request, where
                    # X is the number of defined segments remaining.
                    remaining_segments = len(self._path_segments) - i - 1
                    new_path_index = len(request_path_segments) - remaining_segments
                    if new_path_index == request_path_index:
                        # Greedy labels must consume at least one segment.
                        return False
                    request_path_index = new_path_index

        if request_path_index < len(request_path_segments):
            # We have no more defined path segments, but still have segments left in
            # the URI.
            return False

        if len(self._query_segments) == 0:
            return True

        if not request.url.query:
            return False

        query_map = parse_qs(request.url.query, keep_blank_values=True)
        for query_segment in self._query_segments:
            if query_segment.key not in query_map:
                return False

            if isinstance(query_segment, QueryLiteralSegment):
                # Convert any None's to empty strings. A protocol could
                # theoretically treat them differently, but for now we don't.
                if query_segment.value is None:
                    segment_value = [""]
                elif isinstance(query_segment.value, str):
                    segment_value = [query_segment.value]
                else:
                    segment_value = query_segment.value
                query_value = query_map[query_segment.key] or ""
                if segment_value != query_value:
                    return False

        return True

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, UriSpec):
            return NotImplemented
        return all(
            [
                self._method == other._method,
                self._target == other.target,
                self._path_segments == other._path_segments,
                self._query_segments == other._query_segments,
            ]
        )

    def __lt__(self, other: Any) -> bool:
        if not isinstance(other, UriSpec):
            return NotImplemented
        return self._rank < other._rank


class HttpBindingMux(Generic[S, OP]):
    def __init__(self, specs: Iterable[UriSpec[S, OP]]):
        """
        Contains the specs for every operation in a service and handles matching
        requests against them.

        :param specs: An iterable containing one UriSpec for each operation in the
            service.
        """
        self._specs: list[UriSpec[S, OP]] = sorted(specs)

    def match(self, request: Request) -> ServiceCoordinate[S, OP] | None:
        for spec in self._specs:
            if spec.match(request):
                return spec.target
        return None
