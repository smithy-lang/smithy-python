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

# mypy: allow-untyped-defs
# mypy: allow-incomplete-defs

import pytest

from smithy_python._private.http import Field, FieldPosition, Fields


def test_field_single_valued_basics() -> None:
    field = Field("fname", ["fval"], FieldPosition.HEADER)
    assert field.name == "fname"
    assert field.kind == FieldPosition.HEADER
    assert field.value == ["fval"]
    assert field.get_value() == "fval"
    assert field.get_value_list() == ["fval"]


def test_field_multi_valued_basics() -> None:
    field = Field("fname", ["fval1", "fval2"], FieldPosition.HEADER)
    assert field.name == "fname"
    assert field.kind == FieldPosition.HEADER
    assert field.value == ["fval1", "fval2"]
    assert field.get_value() == "fval1,fval2"
    assert field.get_value_list() == ["fval1", "fval2"]


@pytest.mark.parametrize(
    "values,expected",
    [
        (["val1"], "val1"),
        (["val1", "val2"], "val1,val2"),
        (["©väl", "val2"], "©väl,val2"),
        # Values containing commas must be double-quoted.
        (["val1,", "val2"], '"val1,",val2'),
        (["v,a,l,1", "val2"], '"v,a,l,1",val2'),
        # ... but if the value is already quoted, it will not be quoted again.
        (['"v,a,l,1"', "val2"], '"v,a,l,1",val2'),
        # In strings the got quoted, pre-existing double quotes are escaped with a
        # single backslash. The second backslash below is for escaping the actual
        # backslash in the string for Python.
        (["slc", '4,196"'], 'slc,"4,196\\""'),
        # ... unless they appear at the beginning AND end of the value, i.e. the value
        # is already quoted.
        (['"quoted"', "val2"], '"quoted",val2'),
        # If the value is already quoted, additional quotes contained within do not get
        # escaped.
        (['"""', "val2"], '""",val2'),
        # Backslashes are also escaped. The following case is a single backslash getting
        # serialized into two backslashes. Python escaping accounts for each actual
        # backslash being written as two.
        (["foo,bar\\", "val2"], '"foo,bar\\\\",val2'),
    ],
)
def test_field_serialization(values, expected):
    field = Field(name="_", value=values)
    assert field.get_value() == expected


@pytest.mark.parametrize(
    "f1,f2",
    [
        (
            Field("fname", ["fval1", "fval2"], FieldPosition.TRAILER),
            Field("fname", ["fval1", "fval2"], FieldPosition.TRAILER),
        ),
        (
            Field("fname", ["fval1", "fval2"]),
            Field("fname", ["fval1", "fval2"]),
        ),
        (
            Field("fname"),
            Field("fname"),
        ),
    ],
)
def test_field_equality(f1, f2) -> None:
    assert f1 == f2


@pytest.mark.parametrize(
    "f1,f2",
    [
        (
            Field("fname", ["fval1", "fval2"], FieldPosition.HEADER),
            Field("fname", ["fval1", "fval2"], FieldPosition.TRAILER),
        ),
        (
            Field("fname", ["fval1", "fval2"], FieldPosition.HEADER),
            Field("fname", ["fval2", "fval1"], FieldPosition.HEADER),
        ),
        (
            Field("fname", ["fval1", "fval2"], FieldPosition.HEADER),
            Field("fname", ["fval1"], FieldPosition.HEADER),
        ),
        (
            Field("fname1", ["fval1", "fval2"], FieldPosition.HEADER),
            Field("fname2", ["fval1", "fval2"], FieldPosition.HEADER),
        ),
    ],
)
def test_field_inqueality(f1, f2) -> None:
    assert f1 != f2


@pytest.mark.parametrize(
    "fs1,fs2",
    [
        (
            Fields([Field(name="fname", value=["fval1", "fval2"])]),
            Fields([Field(name="fname", value=["fval1", "fval2"])]),
        ),
    ],
)
def test_fields_equality(fs1, fs2) -> None:
    assert fs1 == fs2


@pytest.mark.parametrize(
    "fs1,fs2",
    [
        (
            Fields(),
            Fields([Field(name="fname")]),
        ),
        (
            Fields([Field(name="fname1")]),
            Fields([Field(name="fname2")]),
        ),
        (
            Fields(encoding="utf-1"),
            Fields(encoding="utf-2"),
        ),
        (
            Fields([Field(name="fname", value=["val1"])]),
            Fields([Field(name="fname", value=["val2"])]),
        ),
        (
            Fields([Field(name="fname", value=["val2", "val1"])]),
            Fields([Field(name="fname", value=["val1", "val2"])]),
        ),
        (
            Fields([Field(name="f1"), Field(name="f2")]),
            Fields([Field(name="f2"), Field(name="f1")]),
        ),
    ],
)
def test_fields_inequality(fs1, fs2) -> None:
    assert fs1 != fs2


def test_repeated_initial_field_names() -> None:
    with pytest.raises(ValueError):
        Fields(
            [
                Field(name="fname1", value=["val1"]),
                Field(name="fname1", value=["val2"]),
            ]
        )
