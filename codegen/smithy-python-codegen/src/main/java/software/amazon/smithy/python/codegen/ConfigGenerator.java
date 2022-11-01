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

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.python.codegen.integration.PythonIntegration;
import software.amazon.smithy.python.codegen.integration.RuntimeClientPlugin;

/**
 * Generates the client's config object.
 */
final class ConfigGenerator implements Runnable {

    // This list contains any fields that should unconditionally be added to every
    // config object. This should be as minimal as possible, and importantly should
    // not contain any HTTP related config since Smithy is transport agnostic.
    private static final List<ConfigField> BASE_FIELDS = Arrays.asList(
            new ConfigField(
                "interceptors",
                Symbol.builder()
                        .name("list[Interceptor]")
                        .addReference(Symbol.builder()
                                .name("Interceptor")
                                .namespace("smithy_python.interfaces.interceptor", ".")
                                .addDependency(SmithyPythonDependency.SMITHY_PYTHON)
                                .build())
                        .build(),
                true,
                "The list of interceptors, which are hooks that are called during the execution of a request."
            )
    );

    private final GenerationContext context;

    ConfigGenerator(GenerationContext context) {
        this.context = context;
    }

    @Override
    public void run() {
        var config = CodegenUtils.getConfigSymbol(context.settings());
        context.writerDelegator().useFileWriter(
                config.getDefinitionFile(), config.getNamespace(), this::generateConfig);

        // Generate the plugin symbol. This is just a callable. We could do something
        // like have a class to implement, but that seems unnecessarily burdensome for
        // a single function.
        var plugin = CodegenUtils.getPluginSymbol(context.settings());
        context.writerDelegator().useFileWriter(plugin.getDefinitionFile(), plugin.getNamespace(), writer -> {
            writer.addStdlibImport("typing", "Callable");
            writer.addStdlibImport("typing", "TypeAlias");
            writer.writeComment("A callable that allows customizing the config object on each request.");
            writer.write("$L: TypeAlias = Callable[[$T], None]", plugin.getName(), config);
        });
    }

    private void generateConfig(PythonWriter writer) {
        var symbol = CodegenUtils.getConfigSymbol(context.settings());

        // Initialize the list of config fields with our base fields. Here a new
        // list is constructed because that base list is immutable.
        var fields = new ArrayList<>(BASE_FIELDS);

        // Add any relevant config fields from plugins.
        for (PythonIntegration integration : context.integrations()) {
            for (RuntimeClientPlugin plugin : integration.getClientPlugins()) {
                fields.addAll(plugin.getConfigFields());
            }
        }

        writer.addStdlibImport("dataclasses", "dataclass");
        writer.write("@dataclass(kw_only=True)");
        writer.openBlock("class $L:", "", symbol.getName(), () -> {
            writer.writeDocs(() -> {
                writer.write("Configuration for $L\n", context.settings().getService().getName());

                // This way of using iterators lets us easily have different behavior for the
                // last field, namely to not add an extra blank line.
                var iter = fields.iterator();
                while (iter.hasNext()) {
                    // Write out the documentation for the fields.
                    var field = iter.next();
                    writer.write(writer.formatDocs(String.format(
                            ":param %s: %s", field.name(), field.documentation())));
                    if (iter.hasNext()) {
                        // Put a blank line between fields, but don't leave one at the end of the doc string.
                        writer.write("");
                    }
                }
            });

            for (ConfigField field : fields) {
                var formatString = "$L: $T";
                if (field.isOptional()) {
                    // We *could* provide a hook to set a default value, but that's a bit awkward and fraught with
                    // footgun issues. Instead, people can set a default using `plugins` which are capable of
                    // modifying the config object.
                    formatString += " | None = None";
                }
                writer.write(formatString, field.name(), field.type());
            }
        });
    }
}
