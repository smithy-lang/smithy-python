#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pyright: reportPrivateUsage=false
from datetime import UTC, datetime

import pytest

from smithy_core.exceptions import ExpectationNotMetException
from smithy_core.types import JsonBlob, JsonString, TimestampFormat, PathPattern


def test_json_string() -> None:
    json_string = JsonString("{}")
    assert json_string == "{}"
    assert json_string.as_json() == {}
    assert isinstance(json_string, str)


def test_json_string_is_lazy() -> None:
    json_string = JsonString("{}")

    # Since as_json hasn't been called yet, the json shouldn't have been
    # parsed yet.
    assert json_string._json is None

    json_string.as_json()

    # Now that as_json has been called, the parsed result should be
    # cached.
    assert json_string._json == {}


def test_string_from_json_immediately_caches() -> None:
    json_string = JsonString.from_json({})
    assert json_string._json == {}


def test_json_blob() -> None:
    json_blob = JsonBlob(b"{}")
    assert json_blob == b"{}"
    assert json_blob.as_json() == {}
    assert isinstance(json_blob, bytes)


def test_json_blob_is_lazy() -> None:
    json_blob = JsonBlob(b"{}")

    # Since as_json hasn't been called yet, the json shouldn't have been
    # parsed yet.
    assert json_blob._json is None

    json_blob.as_json()

    # Now that as_json has been called, the parsed result should be
    # cached.
    assert json_blob._json == {}


def test_blob_from_json_immediately_caches() -> None:
    json_blob = JsonBlob.from_json({})
    assert json_blob._json == {}


TIMESTAMP_FORMAT_SERIALIZATION_CASES: list[
    tuple[TimestampFormat, float | str, datetime]
] = [
    (
        TimestampFormat.DATE_TIME,
        "2017-01-01T00:00:00Z",
        datetime(2017, 1, 1, tzinfo=UTC),
    ),
    (
        TimestampFormat.EPOCH_SECONDS,
        1483228800,
        datetime(2017, 1, 1, tzinfo=UTC),
    ),
    (
        TimestampFormat.HTTP_DATE,
        "Sun, 01 Jan 2017 00:00:00 GMT",
        datetime(2017, 1, 1, tzinfo=UTC),
    ),
    (
        TimestampFormat.DATE_TIME,
        "2017-01-01T00:00:00.000001Z",
        datetime(2017, 1, 1, microsecond=1, tzinfo=UTC),
    ),
    (
        TimestampFormat.EPOCH_SECONDS,
        1483228800.000001,
        datetime(2017, 1, 1, microsecond=1, tzinfo=UTC),
    ),
    (
        TimestampFormat.DATE_TIME,
        "1969-12-31T23:59:59Z",
        datetime(1969, 12, 31, 23, 59, 59, tzinfo=UTC),
    ),
    (
        TimestampFormat.EPOCH_SECONDS,
        -1,
        datetime(1969, 12, 31, 23, 59, 59, tzinfo=UTC),
    ),
    (
        TimestampFormat.HTTP_DATE,
        "Wed, 31 Dec 1969 23:59:59 GMT",
        datetime(1969, 12, 31, 23, 59, 59, tzinfo=UTC),
    ),
    (
        TimestampFormat.DATE_TIME,
        "2038-01-19T03:14:08Z",
        datetime(2038, 1, 19, 3, 14, 8, tzinfo=UTC),
    ),
    (
        TimestampFormat.EPOCH_SECONDS,
        2147483648,
        datetime(2038, 1, 19, 3, 14, 8, tzinfo=UTC),
    ),
    (
        TimestampFormat.HTTP_DATE,
        "Tue, 19 Jan 2038 03:14:08 GMT",
        datetime(2038, 1, 19, 3, 14, 8, tzinfo=UTC),
    ),
]

TIMESTAMP_FORMAT_DESERIALIZATION_CASES: list[
    tuple[TimestampFormat, float | str, datetime]
] = [
    (
        TimestampFormat.EPOCH_SECONDS,
        "1483228800",
        datetime(2017, 1, 1, tzinfo=UTC),
    ),
    (
        TimestampFormat.EPOCH_SECONDS,
        "1483228800.000001",
        datetime(2017, 1, 1, microsecond=1, tzinfo=UTC),
    ),
    (
        TimestampFormat.EPOCH_SECONDS,
        "-1",
        datetime(1969, 12, 31, 23, 59, 59, tzinfo=UTC),
    ),
    (
        TimestampFormat.EPOCH_SECONDS,
        "2147483648",
        datetime(2038, 1, 19, 3, 14, 8, tzinfo=UTC),
    ),
]
TIMESTAMP_FORMAT_DESERIALIZATION_CASES.extend(TIMESTAMP_FORMAT_SERIALIZATION_CASES)


@pytest.mark.parametrize(
    "format, serialized, deserialized", TIMESTAMP_FORMAT_SERIALIZATION_CASES
)
def test_timestamp_format_serialize(
    format: TimestampFormat, serialized: str | float, deserialized: datetime
):
    assert format.serialize(deserialized) == serialized


@pytest.mark.parametrize(
    "format, serialized, deserialized", TIMESTAMP_FORMAT_DESERIALIZATION_CASES
)
def test_timestamp_format_deserialize(
    format: TimestampFormat, serialized: str | float, deserialized: datetime
):
    assert format.deserialize(serialized) == deserialized


@pytest.mark.parametrize(
    "format, value",
    [
        (TimestampFormat.DATE_TIME, 1),
        (TimestampFormat.HTTP_DATE, 1),
        (TimestampFormat.EPOCH_SECONDS, "foo"),
    ],
)
def test_invalid_timestamp_format_type_raises(
    format: TimestampFormat, value: str | float
):
    with pytest.raises(ExpectationNotMetException):
        format.deserialize(value)


def test_path_pattern_without_labels():
    assert PathPattern("/foo/").format() == "/foo/"


def test_path_pattern_with_normal_label():
    assert PathPattern("/{foo}/").format(foo="foo") == "/foo/"


def test_path_pattern_with_greedy_label():
    assert PathPattern("/{foo+}/").format(foo="foo") == "/foo/"


def test_path_pattern_greedy_label_allows_path_sep():
    assert PathPattern("/{foo+}/").format(foo="foo/bar") == "/foo/bar/"


def test_path_pattern_normal_label_disallows_path_sep():
    with pytest.raises(ValueError):
        PathPattern("/{foo}").format(foo="foo/bar")


@pytest.mark.parametrize(
    "greedy, value",
    [
        (False, ""),
        (True, ""),
        (True, "/"),
        (True, "/foo"),
        (True, "foo/"),
        (True, "/foo/"),
        (True, "foo//bar"),
    ],
)
def test_path_pattern_disallows_empty_segments(greedy: bool, value: str):
    pattern = PathPattern("/{foo+}/" if greedy else "/{foo}/")
    with pytest.raises(ValueError):
        pattern.format(foo=value)
