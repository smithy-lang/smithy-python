/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
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

import java.util.Collection;
import java.util.LinkedHashSet;
import java.util.Set;
import software.amazon.smithy.codegen.core.SymbolReference;
import software.amazon.smithy.model.knowledge.ServiceIndex;
import software.amazon.smithy.model.knowledge.TopDownIndex;
import software.amazon.smithy.model.shapes.OperationShape;
import software.amazon.smithy.model.shapes.ServiceShape;
import software.amazon.smithy.model.traits.DocumentationTrait;
import software.amazon.smithy.model.traits.StringTrait;
import software.amazon.smithy.python.codegen.integration.PythonIntegration;
import software.amazon.smithy.python.codegen.integration.RuntimeClientPlugin;
import software.amazon.smithy.python.codegen.sections.InitializeHttpAuthParametersSection;
import software.amazon.smithy.python.codegen.sections.ResolveEndpointSection;
import software.amazon.smithy.python.codegen.sections.ResolveIdentitySection;
import software.amazon.smithy.python.codegen.sections.SendRequestSection;
import software.amazon.smithy.python.codegen.sections.SignRequestSection;

/**
 * Generates the actual client and implements operations.
 */
final class ClientGenerator implements Runnable {

    private final GenerationContext context;
    private final ServiceShape service;

    ClientGenerator(GenerationContext context, ServiceShape service) {
        this.context = context;
        this.service = service;
    }

    @Override
    public void run() {
        context.writerDelegator().useShapeWriter(service, this::generateService);
    }

    private void generateService(PythonWriter writer) {
        var serviceSymbol = context.symbolProvider().toSymbol(service);
        var configSymbol = CodegenUtils.getConfigSymbol(context.settings());
        var pluginSymbol = CodegenUtils.getPluginSymbol(context.settings());

        writer.addStdlibImport("typing", "TypeVar");
        writer.write("""
            Input = TypeVar("Input")
            Output = TypeVar("Output")
            """);

        writer.openBlock("class $L:", "", serviceSymbol.getName(), () -> {
            var docs = service.getTrait(DocumentationTrait.class)
                    .map(StringTrait::getValue)
                    .orElse("Client for " + serviceSymbol.getName());
            writer.writeDocs(() -> {
                writer.write("""
                        $L

                        :param config: Optional configuration for the client. Here you can set things like the
                        endpoint for HTTP services or auth credentials.

                        :param plugins: A list of callables that modify the configuration dynamically. These
                        can be used to set defaults, for example.""", docs);
            });

            var defaultPlugins = new LinkedHashSet<SymbolReference>();

            for (PythonIntegration integration : context.integrations()) {
                for (RuntimeClientPlugin runtimeClientPlugin : integration.getClientPlugins()) {
                    if (runtimeClientPlugin.matchesService(context.model(), service)) {
                        runtimeClientPlugin.getPythonPlugin().ifPresent(defaultPlugins::add);
                    }
                }
            }

            writer.write("""
                    def __init__(self, config: $1T | None = None, plugins: list[$2T] | None = None):
                        self._config = config or $1T()

                        client_plugins: list[$2T] = [
                            $3C
                        ]
                        if plugins:
                            client_plugins.extend(plugins)

                        for plugin in client_plugins:
                            plugin(self._config)
                    """, configSymbol, pluginSymbol, writer.consumer(w -> writeDefaultPlugins(w, defaultPlugins)));

            var topDownIndex = TopDownIndex.of(context.model());
            for (OperationShape operation : topDownIndex.getContainedOperations(service)) {
                generateOperation(writer, operation);
            }
        });

        if (context.protocolGenerator() != null) {
            generateOperationExecutor(writer);
        }
    }

    private void generateOperationExecutor(PythonWriter writer) {
        var transportRequest = context.applicationProtocol().requestType();
        var transportResponse = context.applicationProtocol().responseType();
        var errorSymbol = CodegenUtils.getServiceError(context.settings());
        var pluginSymbol = CodegenUtils.getPluginSymbol(context.settings());
        var configSymbol = CodegenUtils.getConfigSymbol(context.settings());

        writer.addStdlibImport("typing", "Callable");
        writer.addStdlibImport("typing", "Awaitable");
        writer.addStdlibImport("typing", "cast");
        writer.addStdlibImport("copy", "deepcopy");
        writer.addStdlibImport("asyncio", "sleep");

        writer.addDependency(SmithyPythonDependency.SMITHY_PYTHON);
        writer.addImport("smithy_python.exceptions", "SmithyRetryException");
        writer.addImport("smithy_python.interfaces.interceptor", "Interceptor");
        writer.addImport("smithy_python.interfaces.interceptor", "InterceptorContext");
        writer.addImport("smithy_python.interfaces.retries", "RetryErrorInfo");
        writer.addImport("smithy_python.interfaces.retries", "RetryErrorType");

        writer.indent();
        writer.write("""
                async def _execute_operation(
                    self,
                    input: Input,
                    plugins: list[$1T],
                    serialize: Callable[[Input, $5T], Awaitable[$2T]],
                    deserialize: Callable[[$3T, $5T], Awaitable[Output]],
                    config: $5T,
                    operation_name: str,
                ) -> Output:
                    try:
                        return await self._handle_execution(
                            input, plugins, serialize, deserialize, config, operation_name
                        )
                    except Exception as e:
                        # Make sure every exception that we throw is an instance of $4T so
                        # customers can reliably catch everything we throw.
                        if not isinstance(e, $4T):
                            raise $4T(e) from e
                        raise e

                async def _handle_execution(
                    self,
                    input: Input,
                    plugins: list[$1T],
                    serialize: Callable[[Input, $5T], Awaitable[$2T]],
                    deserialize: Callable[[$3T, $5T], Awaitable[Output]],
                    config: $5T,
                    operation_name: str,
                ) -> Output:
                    context: InterceptorContext[Input, None, None, None] = InterceptorContext(
                        request=input,
                        response=None,
                        transport_request=None,
                        transport_response=None,
                    )
                    _client_interceptors = config.interceptors
                    client_interceptors = cast(
                        list[Interceptor[Input, Output, $2T, $3T]], _client_interceptors
                    )
                    interceptors = client_interceptors

                    try:
                        # Step 1a: Invoke read_before_execution on client-level interceptors
                        for interceptor in client_interceptors:
                            interceptor.read_before_execution(context)

                        # Step 1b: Run operation-level plugins
                        config = deepcopy(config)
                        for plugin in plugins:
                            plugin(config)

                        _client_interceptors = config.interceptors
                        interceptors = cast(
                            list[Interceptor[Input, Output, $2T, $3T]],
                            _client_interceptors,
                        )

                        # Step 1c: Invoke the read_before_execution hooks on newly added
                        # interceptors.
                        for interceptor in interceptors:
                            if interceptor not in client_interceptors:
                                interceptor.read_before_execution(context)

                        # Step 2: Invoke the modify_before_serialization hooks
                        for interceptor in interceptors:
                            context._request = interceptor.modify_before_serialization(context)

                        # Step 3: Invoke the read_before_serialization hooks
                        for interceptor in interceptors:
                            interceptor.read_before_serialization(context)

                        # Step 4: Serialize the request
                        context_with_transport_request = cast(
                            InterceptorContext[Input, None, $2T, None], context
                        )
                        context_with_transport_request._transport_request = await serialize(
                            context_with_transport_request.request, config
                        )

                        # Step 5: Invoke read_after_serialization
                        for interceptor in interceptors:
                            interceptor.read_after_serialization(context_with_transport_request)

                        # Step 6: Invoke modify_before_retry_loop
                        for interceptor in interceptors:
                            context_with_transport_request._transport_request = (
                                interceptor.modify_before_retry_loop(context_with_transport_request)
                            )

                        # Step 7: Acquire the retry token.
                        retry_strategy = config.retry_strategy
                        retry_token = retry_strategy.acquire_initial_retry_token()

                        while True:
                            # Make an attempt, creating a copy of the context so we don't pass
                            # around old data.
                            context_with_response = await self._handle_attempt(
                                deserialize,
                                interceptors,
                                context_with_transport_request.copy(),
                                config,
                                operation_name,
                            )

                            # We perform this type-ignored re-assignment because `context` needs
                            # to point at the latest context so it can be generically handled
                            # later on. This is only an issue here because we've created a copy,
                            # so we're no longer simply pointing at the same object in memory
                            # with different names and type hints. It is possible to address this
                            # without having to fall back to the type ignore, but it would impose
                            # unnecessary runtime costs.
                            context = context_with_response  # type: ignore

                            if isinstance(context_with_response.response, Exception):
                                # Step 7u: Reacquire retry token if the attempt failed
                                try:
                                    retry_token = retry_strategy.refresh_retry_token_for_retry(
                                        token_to_renew=retry_token,
                                        error_info=RetryErrorInfo(
                                            # TODO: Determine the error type.
                                            error_type=RetryErrorType.CLIENT_ERROR,
                                        )
                                    )
                                except SmithyRetryException:
                                    raise context_with_response.response
                                await sleep(retry_token.retry_delay)
                            else:
                                # Step 8: Invoke record_success
                                retry_strategy.record_success(token=retry_token)
                                break
                    except Exception as e:
                        if context.response is not None:
                            # config.logger.exception(f"Exception occurred while handling: {context.response}")
                            pass
                        context._response = e

                    # At this point, the context's request will have been definitively set, and
                    # The response will be set either with the modeled output or an exception. The
                    # transport_request and transport_response may be set or None.
                    execution_context = cast(
                        InterceptorContext[Input, Output, $2T | None, $3T | None], context
                    )
                    return await self._finalize_execution(interceptors, execution_context)

                async def _handle_attempt(
                    self,
                    deserialize: Callable[[$3T, $5T], Awaitable[Output]],
                    interceptors: list[Interceptor[Input, Output, $2T, $3T]],
                    context: InterceptorContext[Input, None, $2T, None],
                    config: $5T,
                    operation_name: str,
                ) -> InterceptorContext[Input, Output, $2T, $3T | None]:
                    try:
                        # assert config.interceptors is not None
                        # Step 7a: Invoke read_before_attempt
                        for interceptor in interceptors:
                            interceptor.read_before_attempt(context)

                """, pluginSymbol, transportRequest, transportResponse, errorSymbol, configSymbol);

        boolean supportsAuth = !ServiceIndex.of(context.model()).getAuthSchemes(service).isEmpty();
        writer.pushState(new ResolveIdentitySection());
        if (context.applicationProtocol().isHttpProtocol() && supportsAuth) {
            writer.pushState(new InitializeHttpAuthParametersSection());
            writer.write("""
                        # Step 7b: Invoke service_auth_scheme_resolver.resolve_auth_scheme
                        auth_parameters: $1T = $1T(
                            operation=operation_name,
                            ${2C|}
                        )

                """, CodegenUtils.getHttpAuthParamsSymbol(context.settings()),
                writer.consumer(this::initializeHttpAuthParameters));
            writer.popState();

            writer.addDependency(SmithyPythonDependency.SMITHY_PYTHON);
            writer.addImport("smithy_python.interfaces.identity", "Identity");
            writer.addImports("smithy_python.interfaces.auth", Set.of("HTTPSigner", "HTTPAuthOption"));
            writer.addStdlibImport("typing", "Any");
            writer.write("""
                        auth_options = config.http_auth_scheme_resolver.resolve_auth_scheme(
                            auth_parameters=auth_parameters
                        )
                        auth_option: HTTPAuthOption | None = None
                        for option in auth_options:
                            if option.scheme_id in config.http_auth_schemes:
                                auth_option = option

                        signer: HTTPSigner[Any, Any] | None = None
                        identity: Identity | None = None

                        if auth_option:
                            auth_scheme = config.http_auth_schemes[auth_option.scheme_id]

                            # Step 7c: Invoke auth_scheme.identity_resolver
                            identity_resolver = auth_scheme.identity_resolver(config=config)

                            # Step 7d: Invoke auth_scheme.signer
                            signer = auth_scheme.signer

                            # Step 7e: Invoke identity_resolver.get_identity
                            identity = await identity_resolver.get_identity(
                                identity_properties=auth_option.identity_properties
                            )

                """);
        }
        writer.popState();

        writer.pushState(new ResolveEndpointSection());
        if (context.applicationProtocol().isHttpProtocol()) {
            writer.addDependency(SmithyPythonDependency.SMITHY_PYTHON);
            // TODO: implement the endpoints 2.0 spec and remove the hard-coded handling of static params.
            writer.addImport("smithy_python._private.http", "StaticEndpointParams");
            writer.addImport("smithy_python._private", "URI");
            writer.write("""
                        # Step 7f: Invoke endpoint_resolver.resolve_endpoint
                        if config.endpoint_resolver is None:
                            raise $1T(
                                "No endpoint_resolver found on the operation config."
                            )
                        if config.endpoint_uri is None:
                            raise $1T(
                                "No endpoint_uri found on the operation config."
                            )

                        endpoint = await config.endpoint_resolver.resolve_endpoint(
                            StaticEndpointParams(uri=config.endpoint_uri)
                        )
                        if not endpoint.uri.path:
                            path = ""
                        elif endpoint.uri.path.endswith("/"):
                            path = endpoint.uri.path[:-1]
                        else:
                            path = endpoint.uri.path
                        if context.transport_request.destination.path:
                            path += context.transport_request.destination.path
                        context._transport_request.destination = URI(
                            scheme=endpoint.uri.scheme,
                            host=context.transport_request.destination.host + endpoint.uri.host,
                            path=path,
                            query=context.transport_request.destination.query,
                        )
                        context._transport_request.fields.extend(endpoint.headers)

                """, errorSymbol);
        }
        writer.popState();

        writer.write("""
                        # Step 7g: Invoke modify_before_signing
                        for interceptor in interceptors:
                            context._transport_request = interceptor.modify_before_signing(context)

                        # Step 7h: Invoke read_before_signing
                        for interceptor in interceptors:
                            interceptor.read_before_signing(context)

                """);

        writer.pushState(new SignRequestSection());
        if (context.applicationProtocol().isHttpProtocol() && supportsAuth) {
            writer.write("""
                        # Step 7i: sign the request
                        if auth_option and signer:
                            context._transport_request = await signer.sign(
                                http_request=context.transport_request,
                                identity=identity,
                                signing_properties=auth_option.signer_properties,
                            )
                """);
        }
        writer.popState();

        writer.write("""
                        # Step 7j: Invoke read_after_signing
                        for interceptor in interceptors:
                            interceptor.read_after_signing(context)

                        # Step 7k: Invoke modify_before_transmit
                        for interceptor in interceptors:
                            context._transport_request = interceptor.modify_before_transmit(context)

                        # Step 7l: Invoke read_before_transmit
                        for interceptor in interceptors:
                            interceptor.read_before_transmit(context)

                """);

        writer.pushState(new SendRequestSection());
        if (context.applicationProtocol().isHttpProtocol()) {
            writer.addDependency(SmithyPythonDependency.SMITHY_PYTHON);
            writer.addImport("smithy_python.interfaces.http", "HTTPRequestConfiguration");
            writer.write("""
                        # Step 7m: Invoke http_client.send
                        request_config = config.http_request_config or HTTPRequestConfiguration()
                        context_with_response = cast(
                            InterceptorContext[Input, None, $1T, $2T], context
                        )
                        context_with_response._transport_response = await config.http_client.send(
                            request=context_with_response.transport_request,
                            request_config=request_config,
                        )

                """, transportRequest, transportResponse);
        }
        writer.popState();

        writer.write("""
                        # Step 7n: Invoke read_after_transmit
                        for interceptor in interceptors:
                            interceptor.read_after_transmit(context_with_response)

                        # Step 7o: Invoke modify_before_deserialization
                        for interceptor in interceptors:
                            context_with_response._transport_response = (
                                interceptor.modify_before_deserialization(context_with_response)
                            )

                        # Step 7p: Invoke read_before_deserialization
                        for interceptor in interceptors:
                            interceptor.read_before_deserialization(context_with_response)

                        # Step 7q: deserialize
                        context_with_output = cast(
                            InterceptorContext[Input, Output, $1T, $2T],
                            context_with_response,
                        )
                        context_with_output._response = await deserialize(
                            context_with_output._transport_response, config
                        )

                        # Step 7r: Invoke read_after_deserialization
                        for interceptor in interceptors:
                            interceptor.read_after_deserialization(context_with_output)
                    except Exception as e:
                        if context.response is not None:
                            # config.logger.exception(f"Exception occurred while handling: {context.response}")
                            pass
                        context._response = e

                    # At this point, the context's request and transport_request have definitively been set,
                    # the response is either set or an exception, and the transport_resposne is either set or
                    # None. This will also be true after _finalize_attempt because there is no opportunity
                    # there to set the transport_response.
                    attempt_context = cast(
                        InterceptorContext[Input, Output, $1T, $2T | None], context
                    )
                    return await self._finalize_attempt(interceptors, attempt_context)

                async def _finalize_attempt(
                    self,
                    interceptors: list[Interceptor[Input, Output, $1T, $2T]],
                    context: InterceptorContext[Input, Output, $1T, $2T | None],
                ) -> InterceptorContext[Input, Output, $1T, $2T | None]:
                    # Step 7s: Invoke modify_before_attempt_completion
                    try:
                        for interceptor in interceptors:
                            context._response = interceptor.modify_before_attempt_completion(
                                context
                            )
                    except Exception as e:
                        if context.response is not None:
                            # config.logger.exception(f"Exception occurred while handling: {context.response}")
                            pass
                        context._response = e

                    # Step 7t: Invoke read_after_attempt
                    for interceptor in interceptors:
                        try:
                            interceptor.read_after_attempt(context)
                        except Exception as e:
                            if context.response is not None:
                                # config.logger.exception(f"Exception occurred while handling: {context.response}")
                                pass
                            context._response = e

                    return context

                async def _finalize_execution(
                    self,
                    interceptors: list[Interceptor[Input, Output, $1T, $2T]],
                    context: InterceptorContext[Input, Output, $1T | None, $2T | None],
                ) -> Output:
                    try:
                        # Step 9: Invoke modify_before_completion
                        for interceptor in interceptors:
                            context._response = interceptor.modify_before_completion(context)

                        # Step 10: Invoke trace_probe.dispatch_events
                        try:
                            pass
                        except Exception as e:
                            # log and ignore exceptions
                            # config.logger.exception(f"Exception occurred while dispatching trace events: {e}")
                            pass
                    except Exception as e:
                        if context.response is not None:
                            # config.logger.exception(f"Exception occurred while handling: {context.response}")
                            pass
                        context._response = e

                    # Step 11: Invoke read_after_execution
                    for interceptor in interceptors:
                        try:
                            interceptor.read_after_execution(context)
                        except Exception as e:
                            if context.response is not None:
                                # config.logger.exception(f"Exception occurred while handling: {context.response}")
                                pass
                            context._response = e

                    # Step 12: Return / throw
                    if isinstance(context.response, Exception):
                        raise context.response

                    # We may want to add some aspects of this context to the output types so we can
                    # return it to the end-users.
                    return context.response
                """, transportRequest, transportResponse);
        writer.dedent();
    }

    private void initializeHttpAuthParameters(PythonWriter writer) {
        var derived = new LinkedHashSet<DerivedProperty>();
        for (PythonIntegration integration : context.integrations()) {
            for (RuntimeClientPlugin plugin : integration.getClientPlugins()) {
                if (plugin.matchesService(context.model(), service)
                        && plugin.getAuthScheme().isPresent()
                        && plugin.getAuthScheme().get().getApplicationProtocol().isHttpProtocol()) {
                    derived.addAll(plugin.getAuthScheme().get().getAuthProperties());
                }
            }
        }

        for (DerivedProperty property : derived) {
            var source = property.source().scopeLocation();
            if (property.initializationFunction().isPresent()) {
                writer.write("$L=$T($L),", property.name(), property.initializationFunction().get(), source);
            } else if (property.sourcePropertyName().isPresent()) {
                writer.write("$L=$L.$L,", property.name(), source, property.sourcePropertyName().get());
            }
        }
    }

    private void writeDefaultPlugins(PythonWriter writer, Collection<SymbolReference> plugins) {
        for (SymbolReference plugin : plugins) {
            writer.write("$T,", plugin);
        }
    }

    /**
     * Generates the function for a single operation.
     */
    private void generateOperation(PythonWriter writer, OperationShape operation) {
        var operationSymbol = context.symbolProvider().toSymbol(operation);
        var pluginSymbol = CodegenUtils.getPluginSymbol(context.settings());

        var input = context.model().expectShape(operation.getInputShape());
        var inputSymbol = context.symbolProvider().toSymbol(input);

        var output = context.model().expectShape(operation.getOutputShape());
        var outputSymbol = context.symbolProvider().toSymbol(output);

        writer.openBlock("async def $L(self, input: $T, plugins: list[$T] | None = None) -> $T:", "",
                operationSymbol.getName(), inputSymbol, pluginSymbol, outputSymbol, () -> {
            writer.writeDocs(() -> {
                var docs = operation.getTrait(DocumentationTrait.class)
                        .map(StringTrait::getValue)
                        .orElse(String.format("Invokes the %s operation.", operation.getId().getName()));

                var inputDocs = input.getTrait(DocumentationTrait.class)
                        .map(StringTrait::getValue)
                        .orElse("The operation's input.");

                writer.write("""
                        $L

                        :param input: $L

                        :param plugins: A list of callables that modify the configuration dynamically.
                        Changes made by these plugins only apply for the duration of the operation
                        execution and will not affect any other operation invocations.""", docs, inputDocs);
            });

            var defaultPlugins = new LinkedHashSet<SymbolReference>();
            for (PythonIntegration integration : context.integrations()) {
                for (RuntimeClientPlugin runtimeClientPlugin : integration.getClientPlugins()) {
                    if (runtimeClientPlugin.matchesOperation(context.model(), service, operation)) {
                        runtimeClientPlugin.getPythonPlugin().ifPresent(defaultPlugins::add);
                    }
                }
            }
            writer.write("""
                operation_plugins = [
                    $C
                ]
                if plugins:
                    operation_plugins.extend(plugins)
                """, writer.consumer(w -> writeDefaultPlugins(w, defaultPlugins)));

            if (context.protocolGenerator() == null) {
                writer.write("raise NotImplementedError()");
            } else {
                var protocolGenerator = context.protocolGenerator();
                var serSymbol = protocolGenerator.getSerializationFunction(context, operation);
                var deserSymbol = protocolGenerator.getDeserializationFunction(context, operation);
                writer.write("""
                    return await self._execute_operation(
                        input=input,
                        plugins=operation_plugins,
                        serialize=$T,
                        deserialize=$T,
                        config=self._config,
                        operation_name=$S,
                    )
                    """, serSymbol, deserSymbol, operation.getId().getName());
            }
        });
    }
}
