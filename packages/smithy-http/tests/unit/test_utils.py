#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import pytest
from smithy_core.exceptions import SmithyException

from smithy_http.utils import join_query_params, split_header


@pytest.mark.parametrize(
    "given, expected",
    [
        ("", []),
        (",", []),
        (", ,,", []),
        ('"\\""', ['"']),
        ('"\\\\"', ["\\"]),
        ('"\\a"', ["a"]),
        ("a,b,c", ["a", "b", "c"]),
        ("a, b, c", ["a", "b", "c"]),
        ("1, 2, 3", ["1", "2", "3"]),
        ("true, false, true", ["true", "false", "true"]),
        ("    foo    ,     bar    ", ["foo", "bar"]),
        ('"    foo    ","     bar    "', ["    foo    ", "     bar    "]),
        ("foo,bar", ["foo", "bar"]),
        ("foo ,bar,", ["foo", "bar"]),
        ("foo , ,bar,charlie", ["foo", "bar", "charlie"]),
        ('"b,c", "\\"def\\"", a', ["b,c", '"def"', "a"]),
    ],
)
def test_split_header(given: str, expected: list[str]) -> None:
    assert split_header(given) == expected


@pytest.mark.parametrize(
    "given, expected",
    [
        (
            "Mon, 16 Dec 2019 23:48:18 GMT, Mon, 16 Dec 2019 23:48:18 GMT",
            ["Mon, 16 Dec 2019 23:48:18 GMT", "Mon, 16 Dec 2019 23:48:18 GMT"],
        ),
        (
            '"Mon, 16 Dec 2019 23:48:18 GMT", Mon, 16 Dec 2019 23:48:18 GMT',
            ["Mon, 16 Dec 2019 23:48:18 GMT", "Mon, 16 Dec 2019 23:48:18 GMT"],
        ),
    ],
)
def test_split_imf_fixdate_header(given: str, expected: list[str]) -> None:
    assert split_header(given, handle_unquoted_http_date=True) == expected


@pytest.mark.parametrize(
    "given",
    [
        ('"'),
        ('",foo'),
        ('"foo" bar'),
    ],
)
def test_split_header_raises(given: str) -> None:
    with pytest.raises(SmithyException):
        split_header(given)


@pytest.mark.parametrize(
    "given, expected",
    [
        ([("foo", None)], "foo"),
        ([("foo&bar", None)], "foo%26bar"),
        ([("foo", "")], "foo="),
        ([("foo&bar", "")], "foo%26bar="),
        ([("foo", "bar")], "foo=bar"),
        ([("foo&bar", "spam&eggs")], "foo%26bar=spam%26eggs"),
        ([("foo", "bar"), ("spam", "eggs")], "foo=bar&spam=eggs"),
        (
            [("foo&bar", "spam&eggs"), ("foo&bar", "spam&eggs")],
            "foo%26bar=spam%26eggs&foo%26bar=spam%26eggs",
        ),
    ],
)
def test_join_query_params(given: list[tuple[str, str | None]], expected: str) -> None:
    assert join_query_params(given) == expected


def test_join_query_params_adds_and_if_prefix_non_empty() -> None:
    actual = join_query_params(params=[("spam", "eggs")], prefix="foo")
    assert actual == "foo&spam=eggs"
