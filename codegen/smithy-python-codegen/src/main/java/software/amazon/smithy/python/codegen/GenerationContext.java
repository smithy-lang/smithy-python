/*
 * Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License").
 * You may not use this file except in compliance with the License.
 * A copy of the License is located at
 *
 *   http://aws.amazon.com/apache2.0
 *
 * or in the "license" file accompanying this file. This file is distributed
 * on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
 * express or implied. See the License for the specific language governing
 * permissions and limitations under the License.
 */

package software.amazon.smithy.python.codegen;

import software.amazon.smithy.build.FileManifest;
import software.amazon.smithy.codegen.core.CodegenContext;
import software.amazon.smithy.codegen.core.SymbolProvider;
import software.amazon.smithy.codegen.core.WriterDelegator;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.utils.SmithyBuilder;
import software.amazon.smithy.utils.SmithyUnstableApi;
import software.amazon.smithy.utils.ToSmithyBuilder;

/**
 * Holds context related to code generation.
 */
@SmithyUnstableApi
public final class GenerationContext
        implements CodegenContext<PythonSettings, PythonWriter>, ToSmithyBuilder<GenerationContext> {

    private final Model model;
    private final PythonSettings settings;
    private final SymbolProvider symbolProvider;
    private final FileManifest fileManifest;
    private final PythonDelegator delegator;

    private GenerationContext(Builder builder) {
        model = builder.model;
        settings = builder.settings;
        symbolProvider = builder.symbolProvider;
        fileManifest = builder.fileManifest;
        delegator = builder.delegator;
    }

    @Override
    public Model model() {
        return model;
    }

    @Override
    public PythonSettings settings() {
        return settings;
    }

    @Override
    public SymbolProvider symbolProvider() {
        return symbolProvider;
    }

    @Override
    public FileManifest fileManifest() {
        return fileManifest;
    }

    @Override
    public WriterDelegator<PythonWriter> writerDelegator() {
        return delegator;
    }

    /**
     * @return Returns a builder.
     */
    public static Builder builder() {
        return new Builder();
    }

    @Override
    public SmithyBuilder<GenerationContext> toBuilder() {
        return builder()
                .model(model)
                .settings(settings)
                .symbolProvider(symbolProvider)
                .fileManifest(fileManifest)
                .writerDelegator(delegator);
    }

    /**
     * Builds {@link GenerationContext}s.
     */
    public static final class Builder implements SmithyBuilder<GenerationContext> {
        private Model model;
        private PythonSettings settings;
        private SymbolProvider symbolProvider;
        private FileManifest fileManifest;
        private PythonDelegator delegator;

        @Override
        public GenerationContext build() {
            return new GenerationContext(this);
        }

        /**
         * @param model The model being generated.
         * @return Returns the builder.
         */
        public Builder model(Model model) {
            this.model = model;
            return this;
        }

        /**
         * @param settings The resolved settings for the generator.
         * @return Returns the builder.
         */
        public Builder settings(PythonSettings settings) {
            this.settings = settings;
            return this;
        }

        /**
         * @param symbolProvider The finalized symbol provider for the generator.
         * @return Returns the builder.
         */
        public Builder symbolProvider(SymbolProvider symbolProvider) {
            this.symbolProvider = symbolProvider;
            return this;
        }

        /**
         * @param fileManifest The file manifest being used in the generator.
         * @return Returns the builder.
         */
        public Builder fileManifest(FileManifest fileManifest) {
            this.fileManifest = fileManifest;
            return this;
        }

        /**
         * @param delegator The writer delegator to use in the generator.
         * @return Returns the builder.
         */
        public Builder writerDelegator(PythonDelegator delegator) {
            this.delegator = delegator;
            return this;
        }
    }
}
