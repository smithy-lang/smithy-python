from smithy_core.deserializers import DeserializeableShape, ShapeDeserializer
from smithy_core.documents import Document
from smithy_core.schemas import Schema
from smithy_core.shapes import ShapeID, ShapeType
from smithy_core.type_registry import TypeRegistry
import pytest


class TestTypeRegistry:
    def test_get(self):
        registry = TypeRegistry({ShapeID("com.example#Test"): TestShape})

        result = registry.get(ShapeID("com.example#Test"))

        assert result == TestShape

    def test_get_sub_registry(self):
        sub_registry = TypeRegistry({ShapeID("com.example#Test"): TestShape})
        registry = TypeRegistry({}, sub_registry)

        result = registry.get(ShapeID("com.example#Test"))

        assert result == TestShape

    def test_get_no_match(self):
        registry = TypeRegistry({ShapeID("com.example#Test"): TestShape})

        with pytest.raises(KeyError, match="Unknown shape: com.example#Test2"):
            registry.get(ShapeID("com.example#Test2"))

    def test_deserialize(self):
        shape_id = ShapeID("com.example#Test")
        registry = TypeRegistry({shape_id: TestShape})

        result = registry.deserialize(Document("abc123", schema=TestShape.schema))

        assert isinstance(result, TestShape) and result.value == "abc123"


class TestShape(DeserializeableShape):
    schema = Schema(id=ShapeID("com.example#Test"), shape_type=ShapeType.STRING)

    def __init__(self, value: str):
        self.value = value

    @classmethod
    def deserialize(cls, deserializer: ShapeDeserializer) -> "TestShape":
        return TestShape(deserializer.read_string(schema=TestShape.schema))
