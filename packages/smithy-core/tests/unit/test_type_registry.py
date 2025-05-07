import pytest
from smithy_core.deserializers import DeserializeableShape, ShapeDeserializer
from smithy_core.documents import Document, TypeRegistry
from smithy_core.prelude import STRING
from smithy_core.schemas import Schema
from smithy_core.shapes import ShapeID
from smithy_core.traits import RequiredTrait


def test_get():
    registry = TypeRegistry({ShapeID("com.example#Test"): TestShape})

    result = registry[ShapeID("com.example#Test")]

    assert result == TestShape


def test_contains():
    registry = TypeRegistry({ShapeID("com.example#Test"): TestShape})

    assert ShapeID("com.example#Test") in registry


def test_get_sub_registry():
    sub_registry = TypeRegistry({ShapeID("com.example#Test"): TestShape})
    registry = TypeRegistry({}, sub_registry)

    result = registry[ShapeID("com.example#Test")]

    assert result == TestShape


def test_contains_sub_registry():
    sub_registry = TypeRegistry({ShapeID("com.example#Test"): TestShape})
    registry = TypeRegistry({}, sub_registry)

    assert ShapeID("com.example#Test") in registry


def test_get_no_match():
    registry = TypeRegistry({ShapeID("com.example#Test"): TestShape})

    with pytest.raises(KeyError, match="Unknown shape: com.example#Test2"):
        registry[ShapeID("com.example#Test2")]


def test_contains_no_match():
    registry = TypeRegistry({ShapeID("com.example#Test"): TestShape})

    assert ShapeID("com.example#Test2") not in registry


def test_deserialize():
    shape_id = ShapeID("com.example#Test")
    registry = TypeRegistry({shape_id: TestShape})

    result = registry.deserialize(Document("abc123", schema=TestShape.schema))

    assert isinstance(result, TestShape) and result.value == "abc123"


class TestShape(DeserializeableShape):
    __test__ = False
    schema = Schema.collection(
        id=ShapeID("com.example#Test"),
        members={"value": {"index": 0, "target": STRING, "traits": [RequiredTrait()]}},
    )

    def __init__(self, value: str):
        self.value = value

    @classmethod
    def deserialize(cls, deserializer: ShapeDeserializer) -> "TestShape":
        return TestShape(
            value=deserializer.read_string(schema=cls.schema.members["value"])
        )
