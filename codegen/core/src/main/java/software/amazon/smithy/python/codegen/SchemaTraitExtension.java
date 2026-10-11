/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen;

import java.util.HashMap;
import java.util.Map;
import software.amazon.smithy.model.shapes.ShapeId;
import software.amazon.smithy.model.traits.Trait;
import software.amazon.smithy.utils.SmithyInternalApi;

/**
 * Customizable inclusion list augmenting the traits emitted into schemas.
 *
 * <p>Required by the schema serialization specification: implementations MUST allow extending the
 * included-trait set via a code generator API, and MUST allow a custom renderer per trait value.
 */
@SmithyInternalApi
public final class SchemaTraitExtension {

    public static final SchemaTraitExtension INSTANCE = new SchemaTraitExtension();

    private final Map<ShapeId, TraitRenderer> customization = new HashMap<>();

    private SchemaTraitExtension() {}

    public void add(ShapeId traitShapeId, TraitRenderer traitRenderer) {
        customization.put(traitShapeId, traitRenderer);
    }

    public String render(Trait trait) {
        return customization.get(trait.toShapeId()).render(trait);
    }

    public boolean contains(Trait trait) {
        return contains(trait.toShapeId());
    }

    public boolean contains(ShapeId trait) {
        return customization.containsKey(trait);
    }

    public interface TraitRenderer {
        String render(Trait trait);
    }
}
