#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# mypy: allow-untyped-defs
# mypy: allow-incomplete-defs

import pytest

from smithy_http import Field, Fields
from smithy_http.interfaces import FieldPosition


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
    "field,expected_repr",
    [
        (
            Field(name="fname", values=["fval1", "fval2"], kind=FieldPosition.HEADER),
            "Field(name='fname', value=['fval1', 'fval2'], kind=<FieldPosition.HEADER: 0>)",
        ),
        (
            Field(name="fname", kind=FieldPosition.TRAILER),
            "Field(name='fname', value=[], kind=<FieldPosition.TRAILER: 1>)",
        ),
        (
            Field(name="fname"),
            "Field(name='fname', value=[], kind=<FieldPosition.HEADER: 0>)",
        ),
    ],
)
def test_field_repr(field: Field, expected_repr: str) -> None:
    assert repr(field) == expected_repr


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


@pytest.mark.parametrize(
    "fields,expected_length",
    [
        (Fields(), 0),
        (Fields([Field(name="fname1")]), 1),
        (Fields(encoding="utf-1"), 0),
        (Fields([Field(name="fname", values=["val2", "val1"])]), 1),
        (Fields([Field(name="f1"), Field(name="f2")]), 2),
    ],
)
def test_fields_length_value(fields: Fields, expected_length: int) -> None:
    assert len(fields) == expected_length


@pytest.mark.parametrize(
    "fields,expected_repr",
    [
        (
            Fields([Field(name="fname1")]),
            (
                "Fields(OrderedDict({'fname1': Field(name='fname1', value=[], "
                "kind=<FieldPosition.HEADER: 0>)}))"
            ),
        ),
    ],
)
def test_fields_repr(fields: Field, expected_repr: str) -> None:
    assert repr(fields) == expected_repr


@pytest.mark.parametrize(
    "fields,key,contained",
    [
        (Fields(), "bad_key", False),
        (Fields([Field(name="fname1")]), "FNAME1", True),
        (Fields([Field(name="fname1")]), "fname1", True),
        (Fields([Field(name="fname2")]), "fname1", False),
        (Fields([Field(name="f1"), Field(name="f2")]), "f1", True),
        (Fields([Field(name="f1"), Field(name="f2")]), "f3", False),
    ],
)
def test_fields_contains(fields: Fields, key: str, contained: bool) -> None:
    assert (key in fields) is contained


@pytest.mark.parametrize(
    "fields,key,expected",
    [
        (Fields(), "bad_key", None),
        (Fields([Field(name="fname1")]), "FNAME1", Field(name="fname1")),
        (Fields([Field(name="fname1")]), "fname1", Field(name="fname1")),
        (Fields([Field(name="fname2")]), "fname1", None),
        (Fields([Field(name="f1"), Field(name="f2")]), "f1", Field(name="f1")),
        (Fields([Field(name="f1"), Field(name="f2")]), "f2", Field(name="f2")),
        (Fields([Field(name="f1"), Field(name="f2")]), "f3", None),
    ],
)
def test_fields_getitem(fields: Fields, key: str, expected: Field | None) -> None:
    assert fields.get(key) == expected


def test_fields_get_index() -> None:
    fields = Fields([Field(name="f1"), Field(name="f2")])
    assert fields["f1"] == Field(name="f1")


def test_fields_get_missing_index() -> None:
    fields = Fields([Field(name="fname1")])
    with pytest.raises(KeyError):
        fields["fname2"]


@pytest.mark.parametrize(
    "fields,field",
    [
        (Fields(), Field(name="fname1")),
        (Fields([Field(name="fname1", values=["1", "2"])]), Field(name="fname1")),
        (Fields([Field(name="f1"), Field(name="f2")]), Field(name="f3")),
    ],
)
def test_fields_setitem(fields: Fields, field: Field) -> None:
    fields[field.name] = field
    assert field.name in fields
    assert fields[field.name] == field


@pytest.mark.parametrize(
    "fields,field",
    [
        (Fields(), Field(name="fname1")),
        (Fields([Field(name="fname1", values=["1", "2"])]), Field(name="fname1")),
        (Fields([Field(name="f1"), Field(name="f2")]), Field(name="f3")),
    ],
)
def test_fields_set_field(fields: Fields, field: Field) -> None:
    fields.set_field(field)
    assert field.name in fields
    assert fields[field.name] == field


@pytest.mark.parametrize(
    "fields,field_name,expected_keys",
    [
        (Fields([Field(name="fname1", values=["1", "2"])]), "fname1", []),
        (Fields([Field(name="f1"), Field(name="f2")]), "f2", ["f1"]),
    ],
)
def test_fields_delitem(
    fields: Fields, field_name: str, expected_keys: list[str]
) -> None:
    assert field_name in fields
    del fields[field_name]
    assert field_name not in fields

    # Ensure we don't delete anything unexpected
    assert len(fields) == len(expected_keys)
    for key in expected_keys:
        assert key in fields


def test_fields_delitem_missing() -> None:
    fields = Fields([Field(name="fname1")])
    with pytest.raises(KeyError):
        del fields["fname2"]
