# Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.


import pytest

from smithy_python.exceptions import SmithyException
from smithy_python.httputils import split_header


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
