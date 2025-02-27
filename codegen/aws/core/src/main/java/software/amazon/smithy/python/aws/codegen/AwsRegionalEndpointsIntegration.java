package software.amazon.smithy.python.aws.codegen;

import java.util.Optional;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.shapes.ServiceShape;
import software.amazon.smithy.python.codegen.integrations.EndpointsGenerator;
import software.amazon.smithy.python.codegen.integrations.PythonIntegration;

public class AwsRegionalEndpointsIntegration implements PythonIntegration {
    @Override
    public Optional<EndpointsGenerator> getEndpointsGenerator(Model model, ServiceShape service) {
        return Optional.of(new AwsRegionalEndpointsGenerator());
    }
}
