from dataclasses import dataclass
from typing import Any, Literal, cast
from urllib.parse import urlencode

import pytest

import smithy_python.interfaces.http as http_interface
from smithy_python._private.http import URI
from smithy_python.mux import (
    HttpBindingMux,
    PathGreedySegment,
    PathLabelSegment,
    PathLiteralSegment,
    QueryLiteralSegment,
    QueryValueSegment,
    ServiceCoordinate,
    UriSpec,
)


class TestURL(URI):
    def __init__(self, path: str = "/", query: list[tuple[str, str]] | None = None):
        query_str = urlencode(query) if query is not None else ""
        super().__init__(
            host="com.example",
            path=path,
            scheme="https",
            query=query_str,
        )


@dataclass(init=False)
class TestRequest:
    url: http_interface.URI
    method: str
    headers: http_interface.HeadersList
    body: Any

    def __init__(self, method: str = "GET", url: http_interface.URI | None = None):
        self.headers = []
        self.method = method
        self.url = url or TestURL()
        self.body = None


class TestUriSpec:
    coordinate = ServiceCoordinate("MyService", "MyOperation")

    def test_matches_method(self) -> None:
        spec = UriSpec(self.coordinate, "GET")
        assert spec.match(TestRequest("GET"))
        assert not spec.match(TestRequest("PUT"))

    def test_matches_path_literal(self) -> None:
        spec = UriSpec(
            target=self.coordinate, path_segments=[PathLiteralSegment("foo")]
        )
        assert spec.match(TestRequest(url=TestURL("/foo")))
        assert not spec.match(TestRequest(url=TestURL("/bar")))
        assert not spec.match(TestRequest(url=TestURL("/")))
        assert not spec.match(TestRequest(url=TestURL("")))
        assert not spec.match(TestRequest(url=TestURL("/foo/bar")))

    def test_handles_leading_and_trailing_slashes(self) -> None:
        spec = UriSpec(
            target=self.coordinate, path_segments=[PathLiteralSegment("foo")]
        )
        assert spec.match(TestRequest(url=TestURL("foo")))
        assert spec.match(TestRequest(url=TestURL("/foo")))
        assert spec.match(TestRequest(url=TestURL("/foo/")))
        assert spec.match(TestRequest(url=TestURL("foo/")))

    def test_matches_path_label(self) -> None:
        spec = UriSpec(target=self.coordinate, path_segments=[PathLabelSegment()])
        assert spec.match(TestRequest(url=TestURL("/foo")))
        assert spec.match(TestRequest(url=TestURL("/bar")))
        assert not spec.match(TestRequest(url=TestURL("/")))
        assert not spec.match(TestRequest(url=TestURL("/foo/bar")))

    def test_matches_greedy_label(self) -> None:
        spec = UriSpec(target=self.coordinate, path_segments=[PathGreedySegment()])
        assert spec.match(TestRequest(url=TestURL("/foo")))
        assert spec.match(TestRequest(url=TestURL("/foo/bar")))
        assert spec.match(TestRequest(url=TestURL("/foo/bar/baz")))
        assert not spec.match(TestRequest(url=TestURL("/")))

    def test_matches_segment_after_greedy_label(self) -> None:
        spec = UriSpec(
            target=self.coordinate,
            path_segments=[PathGreedySegment(), PathLiteralSegment("spam")],
        )
        assert spec.match(TestRequest(url=TestURL("/foo/spam")))
        assert spec.match(TestRequest(url=TestURL("/foo/bar/spam")))
        assert spec.match(TestRequest(url=TestURL("/foo/bar/baz/spam")))
        assert not spec.match(TestRequest(url=TestURL("/foo/bar")))

    def test_matches_query_literal(self) -> None:
        spec = UriSpec(
            target=self.coordinate, query_segments=[QueryLiteralSegment("foo", "bar")]
        )
        assert spec.match(TestRequest(url=TestURL(query=[("foo", "bar")])))
        assert not spec.match(TestRequest(url=TestURL(query=[("foo", "baz")])))
        assert not spec.match(TestRequest(url=TestURL(query=[("foo", "")])))
        assert not spec.match(
            TestRequest(url=TestURL(query=[("foo", "bar"), ("foo", "baz")]))
        )

    def test_matches_query_literal_with_empty_value(self) -> None:
        spec = UriSpec(
            target=self.coordinate, query_segments=[QueryLiteralSegment("foo", "")]
        )
        assert spec.match(TestRequest(url=TestURL(query=[("foo", "")])))
        assert not spec.match(TestRequest(url=TestURL(query=[("foo", "bar")])))
        assert not spec.match(
            TestRequest(url=TestURL(query=[("foo", ""), ("foo", "bar")]))
        )

    def test_matches_query_literal_with_null_value(self) -> None:
        spec = UriSpec(
            target=self.coordinate, query_segments=[QueryLiteralSegment("foo", None)]
        )
        assert spec.match(TestRequest(url=TestURL(query=[("foo", "")])))
        assert not spec.match(TestRequest(url=TestURL(query=[("foo", "bar")])))
        assert not spec.match(
            TestRequest(url=TestURL(query=[("foo", ""), ("foo", "bar")]))
        )

    def test_matches_query_value(self) -> None:
        spec = UriSpec(
            target=self.coordinate, query_segments=[QueryValueSegment("foo")]
        )
        assert spec.match(TestRequest(url=TestURL(query=[("foo", "")])))
        assert spec.match(TestRequest(url=TestURL(query=[("foo", "bar")])))
        assert spec.match(TestRequest(url=TestURL(query=[("foo", "baz")])))
        assert spec.match(
            TestRequest(url=TestURL(query=[("foo", "bar"), ("foo", "baz")]))
        )

    def test_matches_multiple_query(self) -> None:
        spec = UriSpec(
            target=self.coordinate,
            query_segments=[
                QueryLiteralSegment("spam", "eggs"),
                QueryValueSegment("foo"),
            ],
        )
        assert spec.match(
            TestRequest(url=TestURL(query=[("spam", "eggs"), ("foo", "bar")]))
        )
        assert not spec.match(TestRequest(url=TestURL(query=[("spam", "eggs")])))
        assert not spec.match(
            TestRequest(url=TestURL(query=[("spam", "wrong"), ("foo", "bar")]))
        )

    def test_matches_path_and_query(self) -> None:
        spec = UriSpec(
            target=self.coordinate,
            path_segments=[PathLiteralSegment("foo")],
            query_segments=[QueryLiteralSegment("spam", "eggs")],
        )
        assert spec.match(
            TestRequest(url=TestURL(path="/foo", query=[("spam", "eggs")]))
        )
        assert not spec.match(
            TestRequest(url=TestURL(path="/bar", query=[("spam", "eggs")]))
        )
        assert not spec.match(
            TestRequest(url=TestURL(path="/foo", query=[("spam", "wrong")]))
        )


TEST_SERVICE = Literal["Test"]
TEST_OPERATIONS = Literal[
    "A", "LessSpecificA", "Greedy", "MiddleGreedy", "Delete", "QueryKeyOnly"
]


def _coordinate(o: TEST_OPERATIONS) -> ServiceCoordinate[TEST_SERVICE, TEST_OPERATIONS]:
    return ServiceCoordinate(cast(TEST_SERVICE, "Test"), o)


@pytest.fixture()
def mux_fixture() -> HttpBindingMux[TEST_SERVICE, TEST_OPERATIONS]:
    return HttpBindingMux(
        [
            UriSpec(
                _coordinate("A"),
                path_segments=[
                    PathLiteralSegment("a"),
                    PathLabelSegment(),
                    PathLabelSegment(),
                ],
            ),
            UriSpec(
                _coordinate("LessSpecificA"),
                path_segments=[
                    PathLiteralSegment("a"),
                    PathLabelSegment(),
                    PathGreedySegment(),
                ],
            ),
            UriSpec(
                _coordinate("Greedy"),
                path_segments=[PathLiteralSegment("greedy"), PathGreedySegment()],
            ),
            UriSpec(
                _coordinate("MiddleGreedy"),
                path_segments=[
                    PathLiteralSegment("mg"),
                    PathGreedySegment(),
                    PathLiteralSegment("y"),
                    PathLiteralSegment("z"),
                ],
            ),
            UriSpec(
                _coordinate("Delete"),
                method="DELETE",
                query_segments=[
                    QueryLiteralSegment("foo", "bar"),
                    QueryValueSegment("baz"),
                ],
            ),
            UriSpec(
                _coordinate("QueryKeyOnly"),
                path_segments=[PathLiteralSegment("query_key_only")],
                query_segments=[QueryLiteralSegment("foo", "")],
            ),
        ]
    )


@pytest.mark.parametrize(
    ["expected_operation", "req"],
    [
        ("LessSpecificA", TestRequest(url=TestURL(path="/a/b/c/d"))),
        ("LessSpecificA", TestRequest(url=TestURL(path="/a/b/c/d/e"))),
        ("A", TestRequest(url=TestURL(path="/a/b/c"))),
        ("A", TestRequest(url=TestURL(path="/a/b/c/"))),
        ("A", TestRequest(url=TestURL(path="/a/b/c", query=[("abc", "def")]))),
        ("A", TestRequest(url=TestURL(path="/a/b/c", query=[("abc", "")]))),
        ("Greedy", TestRequest(url=TestURL(path="/greedy/a/b/c/d"))),
        (
            "Greedy",
            TestRequest(url=TestURL(path="/greedy/a/b/c/d", query=[("abc", "def")])),
        ),
        ("MiddleGreedy", TestRequest(url=TestURL(path="/mg/a/x/y/z"))),
        (
            "MiddleGreedy",
            TestRequest(url=TestURL(path="/mg/a/b/c/d/y/z", query=[("abc", "def")])),
        ),
        (
            "MiddleGreedy",
            TestRequest(url=TestURL(path="/mg/a/b/y/c/d/y/z", query=[("abc", "def")])),
        ),
        (
            "MiddleGreedy",
            TestRequest(url=TestURL(path="/mg/a/b/y/z/d/y/z", query=[("abc", "def")])),
        ),
        (
            "Delete",
            TestRequest(
                method="DELETE", url=TestURL(query=[("foo", "bar"), ("baz", "quux")])
            ),
        ),
        # TODO: is this right?
        # (
        #     "Delete",
        #     TestRequest(
        #         method="DELETE",
        #         url=TestURL(query=[("foo", "bar"), ("foo", "corge"), ("baz", "quux")]),
        #     ),
        # ),
        (
            "Delete",
            TestRequest(
                method="DELETE", url=TestURL(query=[("foo", "bar"), ("baz", "")])
            ),
        ),
        (
            "Delete",
            TestRequest(
                method="DELETE",
                url=TestURL(query=[("foo", "bar"), ("baz", "quux"), ("baz", "grault")]),
            ),
        ),
        # TODO: is this right?
        # (
        #     "QueryKeyOnly",
        #     TestRequest(url=TestURL(path="/query_key_only", query=[("foo", "bar")])),
        # ),
        (
            "QueryKeyOnly",
            TestRequest(url=TestURL(path="/query_key_only", query=[("foo", "")])),
        ),
    ],
)
def test_mux_match(
    mux_fixture: HttpBindingMux[TEST_SERVICE, TEST_OPERATIONS],
    expected_operation: TEST_OPERATIONS,
    req: http_interface.Request,
) -> None:
    match = mux_fixture.match(req)
    assert match and match.operation == expected_operation


@pytest.mark.parametrize(
    "req",
    [
        TestRequest(method="POST", url=TestURL(path="/a/b/c")),
        TestRequest(method="PUT", url=TestURL(path="/a/b/c")),
        TestRequest(method="PATCH", url=TestURL(path="/a/b/c")),
        TestRequest(method="OPTIONS", url=TestURL(path="/a/b/c")),
        TestRequest(url=TestURL(path="/a")),
        TestRequest(url=TestURL(path="/a/b")),
        TestRequest(url=TestURL(path="/greedy")),
        TestRequest(url=TestURL(path="/greedy/")),
        TestRequest(url=TestURL(path="/mg")),
        TestRequest(url=TestURL(path="/mg/q")),
        TestRequest(url=TestURL(path="/mg/z")),
        TestRequest(url=TestURL(path="/mg/y/z")),
        TestRequest(url=TestURL(path="/mg/a/z")),
        TestRequest(url=TestURL(path="/mg/a/y/z/a")),
        TestRequest(url=TestURL(path="/mg/a/y/a")),
        TestRequest(url=TestURL(path="/mg/a/b/z/c")),
        TestRequest(method="DELETE", url=TestURL(query=[("foo", "bar")])),
        TestRequest(method="DELETE", url=TestURL(query=[("baz", "quux")])),
        TestRequest(method="DELETE"),
    ],
)
def test_mux_miss(
    mux_fixture: HttpBindingMux[TEST_SERVICE, TEST_OPERATIONS],
    req: http_interface.Request,
) -> None:
    assert not mux_fixture.match(req)
