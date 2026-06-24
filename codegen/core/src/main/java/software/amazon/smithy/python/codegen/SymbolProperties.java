/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen;

import java.util.List;
import software.amazon.smithy.codegen.core.Property;
import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.codegen.core.SymbolReference;
import software.amazon.smithy.model.shapes.Shape;
import software.amazon.smithy.utils.SmithyUnstableApi;

/**
 * Contains properties that may be added to symbols by smithy-python.
 */
@SmithyUnstableApi
public final class SymbolProperties {

    /**
     * Contains the shape that the symbol represents.
     */
    public static final Property<Shape> SHAPE = Property.named("shape");

    /**
     * Contains a symbol reference pointing to the shape's schema symbol.
     *
     * <p>The referenced is aliased with a leading underscore so that the schema
     * isn't re-exported.
     */
    public static final Property<SymbolReference> SCHEMA = Property.named("schema");

    /**
     * Contains a boolean representing whether the symbol represents a part of the Python standard library.
     */
    public static final Property<Boolean> STDLIB = Property.named("stdlib");

    /**
     * Contains a symbol representing the class containing known enum values for the symbol.
     *
     * <p>In type signatures, the base int or str is used instead for forwards compatibility.
     */
    public static final Property<Symbol> ENUM_SYMBOL = Property.named("enumSymbol");

    /**
     * Contains a symbol representing the unknown variant of a union.
     */
    public static final Property<Symbol> UNION_UNKNOWN = Property.named("unknown");

    /**
     * Contains a boolean indicating whether the symbol dependency is a link dependency.
     *
     * <p>A link dependency is a dependency that would be specified in a {@code pyproject.toml}
     * or {@code requirements.txt} with a link to the package source rather than a name and
     * version number.
     */
    public static final Property<Boolean> IS_LINK = Property.named("isLink");

    /**
     * Contains a list of optional dependencies that the symbol dependency has.
     */
    public static final Property<List<String>> OPTIONAL_DEPENDENCIES = Property.named("optionalDependencies");

    /**
     * Contains a symbol pointing to the shape's serializer method. This is only used for
     * lists and maps.
     */
    public static final Property<Symbol> SERIALIZER = Property.named("serializer");

    /**
     * Contains a symbol pointing to the shape's deserializer method. This is only used for
     * lists, maps, and unions.
     */
    public static final Property<Symbol> DESERIALIZER = Property.named("deserializer");

    /**
     * Contains a symbol pointing to an operation shape's method in the client. This is
     * only used for operations.
     */
    public static final Property<Symbol> OPERATION_METHOD = Property.named("operationMethod");

    /**
     * Whether a symbol is importable (i.e. an instance method is not "importable")
     */
    public static final Property<Boolean> IMPORTABLE = Property.named("nonImportable");

    private SymbolProperties() {}
}
