#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from smithy_core.schemas import Schema
from smithy_core.shapes import ShapeID
from smithy_core.traits import Trait, XMLNamespaceTrait, XMLNameTrait

# Code generators may rename shapes (e.g. synthetic operation inputs), recording
# the modeled name in this trait. The modeled name is what appears on the wire.
_ORIGINAL_SHAPE_ID = ShapeID("smithy.synthetic#originalShapeId")


def own_trait[T: Trait](schema: Schema, trait: type[T]) -> T | None:
    """Get a trait that is applied directly to the given schema.

    Member schemas inherit the traits of their targets. For most traits that is
    desirable, but ``@xmlName`` and ``@xmlNamespace`` applied to a structure only
    take effect when that structure is the root of a document. When the structure
    is a member of another shape, the member's own name and namespace apply.
    """
    found = schema.get_trait(trait)
    if found is None:
        return None
    target = schema.member_target
    if target is not None and target.traits.get(trait.id) is found:
        return None
    return found


def member_name(schema: Schema) -> str:
    """Get the XML element name of a member, respecting a directly applied
    ``@xmlName``."""
    if (xml_name := own_trait(schema, XMLNameTrait)) is not None:
        return xml_name.value
    return schema.expect_member_name()


def root_name(schema: Schema) -> str:
    """Get the XML element name for the root of a document.

    When the root is a member (e.g. an ``@httpPayload`` member), the member's
    ``@xmlName`` takes precedence, then the target's ``@xmlName``, then the
    target's shape name. Otherwise the shape's ``@xmlName`` or shape name is used.
    """
    if (xml_name := schema.get_trait(XMLNameTrait)) is not None:
        return xml_name.value
    target = schema.member_target or schema
    original_id = target.get_trait(_ORIGINAL_SHAPE_ID)
    if original_id is not None and isinstance(original_id.document_value, str):
        return ShapeID(original_id.document_value).name
    return target.id.name


def local_name(name: str) -> str:
    """Strip any namespace prefix or URI from an element or attribute name.

    Handles both the ``prefix:name`` form used in ``@xmlName`` values and the
    ``{uri}name`` form used by ElementTree.
    """
    if name.startswith("{"):
        return name.split("}", 1)[1]
    return name.rsplit(":", 1)[-1]


def namespace_attribute(trait: XMLNamespaceTrait) -> tuple[str, str]:
    """Convert an ``@xmlNamespace`` trait into an ``(attribute name, uri)`` pair."""
    if trait.prefix:
        return f"xmlns:{trait.prefix}", trait.uri
    return "xmlns", trait.uri
