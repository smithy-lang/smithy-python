/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen;

import java.util.HashSet;
import java.util.Set;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.knowledge.KnowledgeIndex;
import software.amazon.smithy.model.knowledge.NullableIndex;
import software.amazon.smithy.model.shapes.ShapeId;
import software.amazon.smithy.utils.SmithyInternalApi;

/**
 * Knowledge index of all shapes that are the target of a python-required structure member,
 * i.e. the shapes that may need a synthesized default during client error correction.
 *
 * <p>Computed once per model and cached via {@link Model#getKnowledge}.
 */
@SmithyInternalApi
public final class RequiredMemberTargetIndex implements KnowledgeIndex {

    private final Set<ShapeId> targets = new HashSet<>();

    private RequiredMemberTargetIndex(Model model) {
        var index = NullableIndex.of(model);
        for (var struct : model.getStructureShapes()) {
            for (var member : struct.members()) {
                if (CodegenUtils.isRequiredMember(index, member)) {
                    targets.add(member.getTarget());
                }
            }
        }
    }

    public static RequiredMemberTargetIndex of(Model model) {
        return model.getKnowledge(RequiredMemberTargetIndex.class, RequiredMemberTargetIndex::new);
    }

    /**
     * @param shape The shape to check.
     * @return Returns whether the shape is the target of any python-required structure member.
     */
    public boolean isRequiredMemberTarget(ShapeId shape) {
        return targets.contains(shape);
    }
}
