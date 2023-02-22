# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
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

from smithy_python._private import Field, FieldPosition, Fields


def test_field_single_valued_basics() -> None:
    field = Field(name="fname", values=["fval"], kind=FieldPosition.HEADER)
    assert field.name == "fname"
    assert field.kind == FieldPosition.HEADER
    assert field.values == ["fval"]
    assert field.as_string() == "fval"
    assert field.as_tuples() == [("fname", "fval")]


def test_field_multi_valued_basics() -> None:
    field = Field(name="fname", values=["fval1", "fval2"], kind=FieldPosition.HEADER)
    assert field.name == "fname"
    assert field.kind == FieldPosition.HEADER
    assert field.values == ["fval1", "fval2"]
    assert field.as_string() == "fval1, fval2"
    assert field.as_tuples() == [("fname", "fval1"), ("fname", "fval2")]


@pytest.mark.parametrize(
    "values,expected",
    [
        # Single-valued fields are serialized without any quoting or escaping.
        (["val1"], "val1"),
        (['"val1"'], '"val1"'),
        (['"'], '"'),
        (['val"1'], 'val"1'),
        (["val\\1"], "val\\1"),
        # Multi-valued fields are joined with one comma and one space as separator.
        (["val1", "val2"], "val1, val2"),
        (["val1", "val2", "val3", "val4"], "val1, val2, val3, val4"),
        (["©väl", "val2"], "©väl, val2"),
        # Values containing commas must be double-quoted.
        (["val1", "val2,val3", "val4"], 'val1, "val2,val3", val4'),
        (["v,a,l,1", "val2"], '"v,a,l,1", val2'),
        # In strings that get quoted, pre-existing double quotes are escaped with a
        # single backslash. The second backslash below is for escaping the actual
        # backslash in the string for Python.
        (["slc", '4,196"'], 'slc, "4,196\\""'),
        (['"val1"', "val2"], '"\\"val1\\"", val2'),
        (["val1", '"'], 'val1, "\\""'),
        (['val1:2",val3:4"', "val5"], '"val1:2\\",val3:4\\"", val5'),
        # If quoting happens, backslashes are also escaped. The following case is a
        # single backslash getting serialized into two backslashes. Python escaping
        # accounts for each actual backslash being written as two.
        (["foo,bar\\", "val2"], '"foo,bar\\\\", val2'),
    ],
)
def test_field_serialization(values: list[str], expected: str):
    field = Field(name="_", values=values)
    assert field.as_string() == expected


@pytest.mark.parametrize(
    "f1,f2",
    [
        (
            Field(name="fname", values=["fval1", "fval2"], kind=FieldPosition.TRAILER),
            Field(name="fname", values=["fval1", "fval2"], kind=FieldPosition.TRAILER),
        ),
        (
            Field(name="fname", values=["fval1", "fval2"]),
            Field(name="fname", values=["fval1", "fval2"]),
        ),
        (
            Field(name="fname"),
            Field(name="fname"),
        ),
    ],
)
def test_field_equality(f1: Field, f2: Field) -> None:
    assert f1 == f2


@pytest.mark.parametrize(
    "f1,f2",
    [
        (
            Field(name="fname", values=["fval1", "fval2"], kind=FieldPosition.HEADER),
            Field(name="fname", values=["fval1", "fval2"], kind=FieldPosition.TRAILER),
        ),
        (
            Field(name="fname", values=["fval1", "fval2"], kind=FieldPosition.HEADER),
            Field(name="fname", values=["fval2", "fval1"], kind=FieldPosition.HEADER),
        ),
        (
            Field(name="fname", values=["fval1", "fval2"], kind=FieldPosition.HEADER),
            Field(name="fname", values=["fval1"], kind=FieldPosition.HEADER),
        ),
        (
            Field(name="fname1", values=["fval1", "fval2"], kind=FieldPosition.HEADER),
            Field(name="fname2", values=["fval1", "fval2"], kind=FieldPosition.HEADER),
        ),
    ],
)
def test_field_inqueality(f1: Field, f2: Field) -> None:
    assert f1 != f2


@pytest.mark.parametrize(
    "fs1,fs2",
    [
        (
            Fields([Field(name="fname", values=["fval1", "fval2"])]),
            Fields([Field(name="fname", values=["fval1", "fval2"])]),
        ),
    ],
)
def test_fields_equality(fs1: Fields, fs2: Fields) -> None:
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
            Fields([Field(name="fname", values=["val1"])]),
            Fields([Field(name="fname", values=["val2"])]),
        ),
        (
            Fields([Field(name="fname", values=["val2", "val1"])]),
            Fields([Field(name="fname", values=["val1", "val2"])]),
        ),
        (
            Fields([Field(name="f1"), Field(name="f2")]),
            Fields([Field(name="f2"), Field(name="f1")]),
        ),
    ],
)
def test_fields_inequality(fs1: Fields, fs2: Fields) -> None:
    assert fs1 != fs2


@pytest.mark.parametrize(
    "initial_fields",
    [
        [
            Field(name="fname1", values=["val1"]),
            Field(name="fname1", values=["val2"]),
        ],
        # uniqueness is checked _after_ normaling field names
        [
            Field(name="fNaMe1", values=["val1"]),
            Field(name="fname1", values=["val2"]),
        ],
    ],
)
def test_repeated_initial_field_names(initial_fields: list[Field]) -> None:
    with pytest.raises(ValueError):
        Fields(initial_fields)
