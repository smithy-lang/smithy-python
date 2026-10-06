/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.generators;

import java.util.List;
import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.writer.PythonWriter;
import software.amazon.smithy.utils.SmithyUnstableApi;

/**
 * Supplies the resolution backend the generated config classes build on.
 *
 * <p>The core {@link ConfigGenerator} always emits the same three-class shape
 * ({@code _<Svc>ConfigBase} / {@code <Svc>Config} / {@code Async<Svc>Config})
 * with a {@code resolve()} on each. This hook lets a layer such as AWS supply
 * what varies: the base classes those three inherit, extra resolution keyword
 * parameters on {@code resolve()} (e.g. a profile or config-file path), and
 * extra {@code _FIELDS} entries, all without taking over class emission.
 *
 * <p>With no backend provided the generator uses the generic
 * {@code smithy_core.config} base classes and a {@code resolve(**overrides)}
 * signature with no resolution source.
 */
@SmithyUnstableApi
public interface ConfigBackend {

    /** The shared field-carrying base the generated {@code _<Svc>ConfigBase} extends. */
    Symbol baseSymbol();

    /** The synchronous resolve base the generated {@code <Svc>Config} mixes in. */
    Symbol syncConfigSymbol();

    /** The asynchronous resolve base the generated {@code Async<Svc>Config} mixes in. */
    Symbol asyncConfigSymbol();

    /** The TypedDict the generated per-service overrides TypedDict extends. */
    Symbol overridesBaseSymbol();

    /**
     * Extra keyword parameters threaded through {@code resolve()} to the resolution
     * context (e.g. {@code profile}, {@code config_file_path}).
     *
     * <p>Each is emitted both as a {@code resolve()} parameter and forwarded to
     * {@code _resolve}/{@code _resolve_async} as a keyword of the same name.
     */
    List<ResolveParam> resolveParams();

    /**
     * Writes extra {@code _FIELDS} entries after the generated service fields.
     *
     * <p>Typically spreads the base class {@code _FIELDS} and overrides a few
     * entries with resolution-source-aware resolvers.
     */
    void writeExtraFields(GenerationContext context, PythonWriter writer);

    /**
     * Whether the backend's base class already defines this field in its own
     * {@code _FIELDS} / overrides.
     *
     * <p>The generator skips emitting a {@code _FIELDS} entry and an overrides-TypedDict
     * key for such a field, since {@link #writeExtraFields} contributes it (usually by
     * spreading the base {@code _FIELDS}). The field declaration is still emitted so the
     * dataclass carries the attribute.
     */
    default boolean isPredefinedField(String name) {
        return false;
    }

    /** A single extra {@code resolve()} keyword parameter: its name and type expression. */
    record ResolveParam(String name, Symbol type) {}
}
