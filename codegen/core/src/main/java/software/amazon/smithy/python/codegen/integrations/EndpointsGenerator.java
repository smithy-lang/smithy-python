package software.amazon.smithy.python.codegen.integrations;

import java.util.List;
import software.amazon.smithy.python.codegen.ConfigProperty;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.writer.PythonWriter;

/**
 *
 */
public interface EndpointsGenerator {

    List<ConfigProperty> endpointsConfig(GenerationContext context);

    void generateEndpoints(GenerationContext context, PythonWriter writer);
}
