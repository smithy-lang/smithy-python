/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen;

import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.TreeSet;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.knowledge.KnowledgeIndex;
import software.amazon.smithy.model.shapes.Shape;
import software.amazon.smithy.model.shapes.ShapeId;
import software.amazon.smithy.model.traits.AuthDefinitionTrait;
import software.amazon.smithy.model.traits.DefaultTrait;
import software.amazon.smithy.model.traits.EndpointTrait;
import software.amazon.smithy.model.traits.ErrorTrait;
import software.amazon.smithy.model.traits.EventHeaderTrait;
import software.amazon.smithy.model.traits.EventPayloadTrait;
import software.amazon.smithy.model.traits.HostLabelTrait;
import software.amazon.smithy.model.traits.HttpErrorTrait;
import software.amazon.smithy.model.traits.HttpHeaderTrait;
import software.amazon.smithy.model.traits.HttpLabelTrait;
import software.amazon.smithy.model.traits.HttpPayloadTrait;
import software.amazon.smithy.model.traits.HttpPrefixHeadersTrait;
import software.amazon.smithy.model.traits.HttpQueryParamsTrait;
import software.amazon.smithy.model.traits.HttpQueryTrait;
import software.amazon.smithy.model.traits.HttpResponseCodeTrait;
import software.amazon.smithy.model.traits.HttpTrait;
import software.amazon.smithy.model.traits.IdempotencyTokenTrait;
import software.amazon.smithy.model.traits.JsonNameTrait;
import software.amazon.smithy.model.traits.LengthTrait;
import software.amazon.smithy.model.traits.MediaTypeTrait;
import software.amazon.smithy.model.traits.PatternTrait;
import software.amazon.smithy.model.traits.ProtocolDefinitionTrait;
import software.amazon.smithy.model.traits.RangeTrait;
import software.amazon.smithy.model.traits.RequestCompressionTrait;
import software.amazon.smithy.model.traits.RequiredTrait;
import software.amazon.smithy.model.traits.RequiresLengthTrait;
import software.amazon.smithy.model.traits.SensitiveTrait;
import software.amazon.smithy.model.traits.SparseTrait;
import software.amazon.smithy.model.traits.StreamingTrait;
import software.amazon.smithy.model.traits.TimestampFormatTrait;
import software.amazon.smithy.model.traits.Trait;
import software.amazon.smithy.model.traits.UniqueItemsTrait;
import software.amazon.smithy.model.traits.XmlAttributeTrait;
import software.amazon.smithy.model.traits.XmlFlattenedTrait;
import software.amazon.smithy.model.traits.XmlNameTrait;
import software.amazon.smithy.model.traits.XmlNamespaceTrait;
import software.amazon.smithy.utils.SetUtils;
import software.amazon.smithy.utils.SmithyInternalApi;

/**
 * Decides which traits are emitted into generated schemas, per the schema serialization specification.
 *
 * <p>Ported from smithy-typescript's SchemaTraitFilterIndex; see the inline notes for traits
 * included here but not there, because smithy-python reads them off the schema at runtime.
 */
@SmithyInternalApi
public final class SchemaTraitFilterIndex implements KnowledgeIndex {

    // smithy-python reads this at runtime via schema.traits.get(...) in rpcv2Cbor unit detection.
    private static final ShapeId ORIGINAL_SHAPE_ID = ShapeId.from("smithy.synthetic#originalShapeId");

    // Traits a protocol/auth meta-trait references but that must still never reach a schema.
    private static final Set<ShapeId> EXCLUDED_TRAITS = SetUtils.of();

    // only included in server-side-validation mode; see enableConstraintTraits().
    private static final Set<ShapeId> CONSTRAINT_TRAITS = SetUtils.of(
            LengthTrait.ID,
            RangeTrait.ID,
            PatternTrait.ID,
            UniqueItemsTrait.ID);

    // The constructor's meta-trait scan contributes the rest.
    private final Set<ShapeId> includedTraits = new HashSet<>(
            SetUtils.of(
                    SparseTrait.ID,
                    SensitiveTrait.ID,
                    IdempotencyTokenTrait.ID,
                    DefaultTrait.ID, // runtime populates default values
                    RequiredTrait.ID, // runtime enforcement
                    TimestampFormatTrait.ID, // read per-member by smithy_http / smithy_aws_core serde
                    ORIGINAL_SHAPE_ID, // rpcv2Cbor unit detection
                    RequestCompressionTrait.ID, // read at runtime
                    JsonNameTrait.ID,
                    MediaTypeTrait.ID,
                    XmlAttributeTrait.ID,
                    XmlFlattenedTrait.ID,
                    XmlNameTrait.ID,
                    XmlNamespaceTrait.ID,
                    StreamingTrait.ID,
                    EndpointTrait.ID,
                    ErrorTrait.ID,
                    RequiresLengthTrait.ID,
                    EventHeaderTrait.ID,
                    EventPayloadTrait.ID,
                    HttpErrorTrait.ID,
                    HttpTrait.ID,
                    HttpHeaderTrait.ID,
                    HttpQueryTrait.ID,
                    HttpLabelTrait.ID,
                    HttpPayloadTrait.ID,
                    HttpPrefixHeadersTrait.ID,
                    HttpQueryParamsTrait.ID,
                    HttpResponseCodeTrait.ID,
                    HostLabelTrait.ID));

    private final Map<Shape, Boolean> cache = new HashMap<>();
    private final Model model;

    SchemaTraitFilterIndex(Model model) {
        Set<Shape> definitionTraits = new TreeSet<>();
        definitionTraits.addAll(model.getShapesWithTrait(ProtocolDefinitionTrait.class));
        definitionTraits.addAll(model.getShapesWithTrait(AuthDefinitionTrait.class));

        for (Shape shape : definitionTraits) {
            shape.getTrait(ProtocolDefinitionTrait.class)
                    .ifPresent(protocolDefinitionTrait -> protocolDefinitionTrait.getTraits()
                            .forEach(traitShapeId -> {
                                if (!EXCLUDED_TRAITS.contains(traitShapeId)) {
                                    includedTraits.add(traitShapeId);
                                }
                            }));
        }

        this.model = model;
        for (Shape shape : model.toSet()) {
            cache.put(shape, hasSchemaTraits(shape));
        }
    }

    public static SchemaTraitFilterIndex of(Model model) {
        return model.getKnowledge(SchemaTraitFilterIndex.class, SchemaTraitFilterIndex::new);
    }

    // server-side-validation mode: add constraint traits and rebuild the cache.
    public void enableConstraintTraits() {
        includedTraits.addAll(CONSTRAINT_TRAITS);
        cache.clear();
        for (Shape shape : model.toSet()) {
            cache.put(shape, hasSchemaTraits(shape));
        }
    }

    public boolean includeTrait(ShapeId traitShapeId) {
        return includedTraits.contains(traitShapeId) || SchemaTraitExtension.INSTANCE.contains(traitShapeId);
    }

    public boolean hasSchemaTraits(Shape shape) {
        return hasSchemaTraits(shape, 0);
    }

    // depth guard: a recursive shape closure could otherwise loop.
    private boolean hasSchemaTraits(Shape shape, int depth) {
        if (cache.containsKey(shape)) {
            return cache.get(shape);
        }
        if (depth > 20) {
            return false;
        }
        boolean hasSchemaTraits = shape.getAllTraits()
                .values()
                .stream()
                .map(Trait::toShapeId)
                .anyMatch(this::includeTrait);

        if (hasSchemaTraits) {
            cache.put(shape, true);
            return true;
        }

        boolean membersHaveSchemaTraits = shape.getAllMembers()
                .values()
                .stream()
                .anyMatch(ms -> hasSchemaTraits(ms, depth + 1));
        // getShape (not expectShape): synthetic targets such as Unit may be stripped from the model.
        boolean targetHasSchemaTraits = shape.asMemberShape()
                .flatMap(ms -> model.getShape(ms.getTarget()))
                .map(target -> hasSchemaTraits(target, depth + 1))
                .orElse(false);

        cache.put(shape, membersHaveSchemaTraits || targetHasSchemaTraits);
        return cache.get(shape);
    }
}
