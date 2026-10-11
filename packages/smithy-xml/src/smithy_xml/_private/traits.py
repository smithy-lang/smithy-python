#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from smithy_core.schemas import Schema
from smithy_core.shapes import ShapeID
from smithy_core.traits import ORIGINAL_SHAPE_ID, Trait, XMLNameTrait


def direct_trait[T: Trait](schema: Schema, trait: type[T]) -> T | None:
    """Get a trait applied to the member itself rather than inherited from its target.

    Member schemas carry their target's traits, but a structure's ``@xmlName`` or
    ``@xmlNamespace`` only applies where the structure is the root element; members
    targeting it keep their own names.
    """
    value = schema.get_trait(trait)
    if value is None or schema.member_target is None:
        return value
    # Member schemas share their target's trait instances, so identity separates an
    # inherited trait from one applied to the member that happens to be equal.
    if schema.member_target.get_trait(trait) is value:
        return None
    return value


def member_xml_name(schema: Schema) -> str:
    """Get the XML element name for a member, respecting its own ``@xmlName``."""
    if (xml_name := direct_trait(schema, XMLNameTrait)) is not None:
        return xml_name.value
    return schema.expect_member_name()


def root_xml_name(schema: Schema) -> str:
    """Get the element name of a top-level shape or an ``@httpPayload`` member.

    These peek through to the target's ``@xmlName`` and shape name. Synthesized
    operation inputs and outputs use the name of the shape they were created from.
    """
    if (xml_name := schema.get_trait(XMLNameTrait)) is not None:
        return xml_name.value
    if schema.member_target is not None:
        schema = schema.member_target
    if (original := schema.traits.get(ORIGINAL_SHAPE_ID)) is not None:
        return ShapeID(original.document_value).name  # type: ignore
    return schema.id.name
