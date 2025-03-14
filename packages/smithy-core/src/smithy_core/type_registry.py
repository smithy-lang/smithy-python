#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from smithy_core.deserializers import (
    DeserializeableShape,
)  # TODO: fix typo in deserializable
from smithy_core.documents import Document
from smithy_core.shapes import ShapeID


# A registry for on-demand deserialization of types by using a mapping of shape IDs to their deserializers.
# TODO: protocol? Also, move into documents.py?
class TypeRegistry:
    def __init__(
        self,
        types: dict[ShapeID, type[DeserializeableShape]],
        sub_registry: "TypeRegistry | None" = None,
    ):
        self._types = types
        self._sub_registry = sub_registry

    def get(self, shape: ShapeID) -> type[DeserializeableShape]:
        if shape in self._types:
            return self._types[shape]
        if self._sub_registry is not None:
            return self._sub_registry.get(shape)
        raise KeyError(f"Unknown shape: {shape}")

    def deserialize(self, document: Document) -> DeserializeableShape:
        return document.as_shape(self.get(document.discriminator))
