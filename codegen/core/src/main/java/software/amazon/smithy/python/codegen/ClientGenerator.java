/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen;

import static software.amazon.smithy.python.codegen.SymbolProperties.OPERATION_METHOD;

import java.util.Collection;
import java.util.LinkedHashSet;
import java.util.Set;
import software.amazon.smithy.codegen.core.SymbolProvider;
import software.amazon.smithy.codegen.core.SymbolReference;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.knowledge.EventStreamIndex;
import software.amazon.smithy.model.knowledge.EventStreamInfo;
import software.amazon.smithy.model.knowledge.ServiceIndex;
import software.amazon.smithy.model.knowledge.TopDownIndex;
import software.amazon.smithy.model.shapes.OperationShape;
import software.amazon.smithy.model.shapes.ServiceShape;
import software.amazon.smithy.model.shapes.Shape;
import software.amazon.smithy.model.traits.DocumentationTrait;
import software.amazon.smithy.model.traits.StringTrait;
import software.amazon.smithy.python.codegen.integrations.PythonIntegration;
import software.amazon.smithy.python.codegen.integrations.RuntimeClientPlugin;
import software.amazon.smithy.python.codegen.sections.*;
import software.amazon.smithy.python.codegen.writer.PythonWriter;
import software.amazon.smithy.utils.SmithyInternalApi;

/**
 * Generates the actual client and implements operations.
 */
@SmithyInternalApi
final class ClientGenerator implements Runnable {

    private final GenerationContext context;
    private final Model model;
    private final ServiceShape service;
    private final SymbolProvider symbolProvider;

    ClientGenerator(GenerationContext context, ServiceShape service) {
        this.context = context;
        this.symbolProvider = context.symbolProvider();
        this.model = context.model();
        this.service = service;
    }

    @Override
    public void run() {
        context.writerDelegator().useShapeWriter(service, this::generateService);
    }

    private void generateService(PythonWriter writer) {
        var serviceSymbol = symbolProvider.toSymbol(service);
        var configSymbol = CodegenUtils.getConfigSymbol(context.settings());
        var pluginSymbol = CodegenUtils.getPluginSymbol(context.settings());
        writer.addLogger();

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
                for (RuntimeClientPlugin runtimeClientPlugin : integration.getClientPlugins(context)) {
                    if (runtimeClientPlugin.matchesService(model, service)) {
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

            var topDownIndex = TopDownIndex.of(model);
            var eventStreamIndex = EventStreamIndex.of(model);
            for (OperationShape operation : topDownIndex.getContainedOperations(service)) {
                if (eventStreamIndex.getInputInfo(operation).isPresent()
                        || eventStreamIndex.getOutputInfo(operation).isPresent()) {
                    generateEventStreamOperation(writer, operation);
                } else {
                    generateOperation(writer, operation);
                }
            }
        });

        if (context.protocolGenerator() != null) {
            generateOperationExecutor(writer);
        }
    }

    private void generateOperationExecutor(PythonWriter writer) {
        writer.pushState();

        var hasStreaming = hasEventStream();
        writer.putContext("hasEventStream", hasStreaming);
        if (hasStreaming) {
            writer.addImport("smithy_core.deserializers", "ShapeDeserializer");
            writer.addStdlibImport("typing", "Any");
        }

        var transportRequest = context.applicationProtocol().requestType();
        var transportResponse = context.applicationProtocol().responseType();
        var errorSymbol = CodegenUtils.getServiceError(context.settings());
        var pluginSymbol = CodegenUtils.getPluginSymbol(context.settings());
        var configSymbol = CodegenUtils.getConfigSymbol(context.settings());

        writer.addStdlibImport("typing", "Callable");
        writer.addStdlibImport("typing", "Awaitable");
        writer.addStdlibImport("typing", "cast");
        writer.addStdlibImport("copy", "deepcopy");
        writer.addStdlibImport("copy", "copy");
        writer.addStdlibImport("asyncio");
        writer.addStdlibImports("asyncio", Set.of("sleep", "Future"));
        writer.addStdlibImport("dataclasses", "replace");

        writer.addDependency(SmithyPythonDependency.SMITHY_CORE);
        writer.addImport("smithy_core.exceptions", "SmithyRetryException");
        writer.addImports("smithy_core.interceptors",
                Set.of("Interceptor",
                        "InterceptorChain",
                        "InputContext",
                        "OutputContext",
                        "RequestContext",
                        "ResponseContext"));
        writer.addImports("smithy_core.interfaces.retries", Set.of("RetryErrorInfo", "RetryErrorType"));
        writer.addImport("smithy_core.interfaces.exceptions", "HasFault");
        writer.addImport("smithy_core.types", "TypedProperties");
        writer.addImport("smithy_core.serializers", "SerializeableShape");
        writer.addImport("smithy_core.deserializers", "DeserializeableShape");
        writer.addImport("smithy_core.schemas", "APIOperation");

        writer.indent();
        writer.write("""
                def _classify_error(
                    self,
                    *,
                    error: Exception,
                    context: ResponseContext[Any, $1T, $2T | None]
                ) -> RetryErrorInfo:
                    logger.debug("Classifying error: %s", error)
                """, transportRequest, transportResponse);
        writer.indent();

        if (context.applicationProtocol().isHttpProtocol()) {
            writer.addDependency(SmithyPythonDependency.SMITHY_HTTP);
            writer.write("""
                    if not isinstance(error, HasFault) and not context.transport_response:
                        return RetryErrorInfo(error_type=RetryErrorType.TRANSIENT)

                    if context.transport_response:
                        if context.transport_response.status in [429, 503]:
                            retry_after = None
                            retry_header = context.transport_response.fields["retry-after"]
                            if retry_header and retry_header.values:
                                retry_after = float(retry_header.values[0])
                            return RetryErrorInfo(error_type=RetryErrorType.THROTTLING, retry_after_hint=retry_after)

                        if context.transport_response.status >= 500:
                            return RetryErrorInfo(error_type=RetryErrorType.SERVER_ERROR)

                    """);
        }

        writer.write("""
                error_type = RetryErrorType.CLIENT_ERROR
                if isinstance(error, HasFault) and error.fault == "server":
                    error_type = RetryErrorType.SERVER_ERROR

                return RetryErrorInfo(error_type=error_type)

                """);
        writer.dedent();

        if (hasStreaming) {
            writer.addStdlibImports("typing", Set.of("Any", "Awaitable"));
            writer.addStdlibImport("asyncio");

            writer.addImports("smithy_core.aio.eventstream",
                    Set.of(
                            "InputEventStream",
                            "OutputEventStream",
                            "DuplexEventStream"));
            writer.addImport("smithy_core.aio.interfaces.eventstream", "EventReceiver");
            writer.write(
                    """
                            async def _input_stream[Input: SerializeableShape, Output: DeserializeableShape](
                                self,
                                input: Input,
                                plugins: list[$1T],
                                serialize: Callable[[Input, $4T], Awaitable[$2T]],
                                deserialize: Callable[[$3T, $4T], Awaitable[Output]],
                                config: $4T,
                                operation: APIOperation[Input, Output],
                            ) -> Any:
                                request_future = Future[RequestContext[Any, $2T]]()
                                awaitable_output = asyncio.create_task(self._execute_operation(
                                    input, plugins, serialize, deserialize, config, operation,
                                    request_future=request_future
                                ))
                                request_context = await request_future
                                ${5C|}
                                return InputEventStream[Any, Any](
                                    input_stream=publisher,
                                    output_future=awaitable_output,
                                )

                            async def _output_stream[Input: SerializeableShape, Output: DeserializeableShape](
                                self,
                                input: Input,
                                plugins: list[$1T],
                                serialize: Callable[[Input, $4T], Awaitable[$2T]],
                                deserialize: Callable[[$3T, $4T], Awaitable[Output]],
                                config: $4T,
                                operation: APIOperation[Input, Output],
                                event_deserializer: Callable[[ShapeDeserializer], Any],
                            ) -> Any:
                                response_future = Future[$3T]()
                                output = await self._execute_operation(
                                    input, plugins, serialize, deserialize, config, operation,
                                    response_future=response_future
                                )
                                transport_response = await response_future
                                ${6C|}
                                return OutputEventStream[Any, Any](
                                    output_stream=receiver,
                                    output=output
                                )

                            async def _duplex_stream[Input: SerializeableShape, Output: DeserializeableShape](
                                self,
                                input: Input,
                                plugins: list[$1T],
                                serialize: Callable[[Input, $4T], Awaitable[$2T]],
                                deserialize: Callable[[$3T, $4T], Awaitable[Output]],
                                config: $4T,
                                operation: APIOperation[Input, Output],
                                event_deserializer: Callable[[ShapeDeserializer], Any],
                            ) -> Any:
                                request_future = Future[RequestContext[Any, $2T]]()
                                response_future = Future[$3T]()
                                awaitable_output = asyncio.create_task(self._execute_operation(
                                    input, plugins, serialize, deserialize, config, operation,
                                    request_future=request_future,
                                    response_future=response_future
                                ))
                                request_context = await request_future
                                ${5C|}
                                output_future = asyncio.create_task(self._wrap_duplex_output(
                                    response_future, awaitable_output, config, operation,
                                    event_deserializer
                                ))
                                return DuplexEventStream[Any, Any, Any](
                                    input_stream=publisher,
                                    output_future=output_future,
                                )

                            async def _wrap_duplex_output[Input: SerializeableShape, Output: DeserializeableShape](
                                self,
                                response_future: Future[$3T],
                                awaitable_output: Future[Any],
                                config: $4T,
                                operation: APIOperation[Input, Output],
                                event_deserializer: Callable[[ShapeDeserializer], Any],
                            ) -> tuple[Any, EventReceiver[Any]]:
                                transport_response = await response_future
                                ${6C|}
                                return await awaitable_output, receiver
                            """,
                    pluginSymbol,
                    transportRequest,
                    transportResponse,
                    configSymbol,
                    writer.consumer(w -> context.protocolGenerator().wrapInputStream(context, w)),
                    writer.consumer(w -> context.protocolGenerator().wrapOutputStream(context, w)));
        }
        writer.addStdlibImport("typing", "Any");
        writer.addStdlibImport("asyncio", "iscoroutine");
        writer.write(
                """
                        async def _execute_operation[Input: SerializeableShape, Output: DeserializeableShape](
                            self,
                            input: Input,
                            plugins: list[$1T],
                            serialize: Callable[[Input, $5T], Awaitable[$2T]],
                            deserialize: Callable[[$3T, $5T], Awaitable[Output]],
                            config: $5T,
                            operation: APIOperation[Input, Output],
                            request_future: Future[RequestContext[Any, $2T]] | None = None,
                            response_future: Future[$3T] | None = None,
                        ) -> Output:
                            try:
                                return await self._handle_execution(
                                    input, plugins, serialize, deserialize, config, operation,
                                    request_future, response_future,
                                )
                            except Exception as e:
                                if request_future is not None and not request_future.done():
                                    request_future.set_exception($4T(e))
                                if response_future is not None and not response_future.done():
                                    response_future.set_exception($4T(e))

                                # Make sure every exception that we throw is an instance of $4T so
                                # customers can reliably catch everything we throw.
                                if not isinstance(e, $4T):
                                    raise $4T(e) from e
                                raise

                        async def _handle_execution[Input: SerializeableShape, Output: DeserializeableShape](
                            self,
                            input: Input,
                            plugins: list[$1T],
                            serialize: Callable[[Input, $5T], Awaitable[$2T]],
                            deserialize: Callable[[$3T, $5T], Awaitable[Output]],
                            config: $5T,
                            operation: APIOperation[Input, Output],
                            request_future: Future[RequestContext[Any, $2T]] | None,
                            response_future: Future[$3T] | None,
                        ) -> Output:
                            operation_name = operation.schema.id.name
                            logger.debug('Making request for operation "%s" with parameters: %s', operation_name, input)
                            config = deepcopy(config)
                            for plugin in plugins:
                                plugin(config)

                            input_context = InputContext(request=input, properties=TypedProperties({"config": config}))
                            transport_request: $2T | None = None
                            output_context: OutputContext[Input, Output, $2T | None, $3T | None] | None = None

                            client_interceptors = cast(
                                list[Interceptor[Input, Output, $2T, $3T]], list(config.interceptors)
                            )
                            interceptor_chain = InterceptorChain(client_interceptors)

                            try:
                                # Step 1: Invoke read_before_execution
                                interceptor_chain.read_before_execution(input_context)

                                # Step 2: Invoke the modify_before_serialization hooks
                                input_context = replace(
                                    input_context,
                                    request=interceptor_chain.modify_before_serialization(input_context)
                                )

                                # Step 3: Invoke the read_before_serialization hooks
                                interceptor_chain.read_before_serialization(input_context)

                                # Step 4: Serialize the request
                                logger.debug("Serializing request for: %s", input_context.request)
                                transport_request = await serialize(input_context.request, config)
                                request_context = RequestContext(
                                    request=input_context.request,
                                    transport_request=transport_request,
                                    properties=input_context.properties,
                                )
                                logger.debug("Serialization complete. Transport request: %s", request_context.transport_request)

                                # Step 5: Invoke read_after_serialization
                                interceptor_chain.read_after_serialization(request_context)

                                # Step 6: Invoke modify_before_retry_loop
                                request_context = replace(
                                    request_context,
                                    transport_request=interceptor_chain.modify_before_retry_loop(request_context)
                                )

                                # Step 7: Acquire the retry token.
                                retry_strategy = config.retry_strategy
                                retry_token = retry_strategy.acquire_initial_retry_token()

                                while True:
                                    # Make an attempt
                                    output_context = await self._handle_attempt(
                                        deserialize,
                                        interceptor_chain,
                                        replace(
                                          request_context,
                                          transport_request = copy(request_context.transport_request)
                                        ),
                                        config,
                                        operation,
                                        request_future,
                                    )

                                    if isinstance(output_context.response, Exception):
                                        # Step 7u: Reacquire retry token if the attempt failed
                                        try:
                                            retry_token = retry_strategy.refresh_retry_token_for_retry(
                                                token_to_renew=retry_token,
                                                error_info=self._classify_error(
                                                    error=output_context.response,
                                                    context=output_context,
                                                )
                                            )
                                        except SmithyRetryException:
                                            raise output_context.response
                                        logger.debug(
                                            "Retry needed. Attempting request #%s in %.4f seconds.",
                                            retry_token.retry_count + 1,
                                            retry_token.retry_delay
                                        )
                                        await sleep(retry_token.retry_delay)
                                        current_body = output_context.transport_request.body
                                        if (seek := getattr(current_body, "seek", None)) is not None:
                                            if iscoroutine((result := seek(0))):
                                                await result
                                    else:
                                        # Step 8: Invoke record_success
                                        retry_strategy.record_success(token=retry_token)
                                        if response_future is not None:
                                            response_future.set_result(
                                                output_context.transport_response  # type: ignore
                                            )
                                        break
                            except Exception as e:
                                if output_context is not None:
                                    logger.exception("Exception occurred while handling: %s", output_context.response)
                                    output_context = replace(output_context, response=e)
                                else:
                                    output_context = OutputContext(
                                        request=input_context.request,
                                        response=e,
                                        transport_request=transport_request,
                                        transport_response=None,
                                        properties=input_context.properties
                                    )

                            return await self._finalize_execution(interceptor_chain, output_context)

                        async def _handle_attempt[Input: SerializeableShape, Output: DeserializeableShape](
                            self,
                            deserialize: Callable[[$3T, $5T], Awaitable[Output]],
                            interceptor: Interceptor[Input, Output, $2T, $3T],
                            context: RequestContext[Input, $2T],
                            config: $5T,
                            operation: APIOperation[Input, Output],
                            request_future: Future[RequestContext[Input, $2T]] | None,
                        ) -> OutputContext[Input, Output, $2T, $3T | None]:
                            transport_response: $3T | None = None
                            try:
                                # Step 7a: Invoke read_before_attempt
                                interceptor.read_before_attempt(context)

                        """,
                pluginSymbol,
                transportRequest,
                transportResponse,
                errorSymbol,
                configSymbol);

        boolean supportsAuth = !ServiceIndex.of(model).getAuthSchemes(service).isEmpty();
        writer.pushState(new ResolveIdentitySection());
        if (context.applicationProtocol().isHttpProtocol() && supportsAuth) {
            writer.pushState(new InitializeHttpAuthParametersSection());
            writer.write("""
                            # Step 7b: Invoke service_auth_scheme_resolver.resolve_auth_scheme
                            auth_parameters: $1T = $1T(
                                operation=operation.schema.id.name,
                                ${2C|}
                            )

                    """,
                    CodegenUtils.getHttpAuthParamsSymbol(context.settings()),
                    writer.consumer(this::initializeHttpAuthParameters));
            writer.popState();

            writer.addDependency(SmithyPythonDependency.SMITHY_CORE);
            writer.addDependency(SmithyPythonDependency.SMITHY_HTTP);
            writer.addImport("smithy_core.interfaces.identity", "Identity");
            writer.addImports("smithy_http.aio.interfaces.auth", Set.of("HTTPSigner", "HTTPAuthOption"));
            writer.addStdlibImport("typing", "Any");
            writer.write("""
                            auth_options = config.http_auth_scheme_resolver.resolve_auth_scheme(
                                auth_parameters=auth_parameters
                            )
                            auth_option: HTTPAuthOption | None = None
                            for option in auth_options:
                                if option.scheme_id in config.http_auth_schemes:
                                    auth_option = option
                                    break

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
        writer.addDependency(SmithyPythonDependency.SMITHY_CORE);
        writer.addDependency(SmithyPythonDependency.SMITHY_HTTP);
        writer.addImport("smithy_core", "URI");
        writer.addImport("smithy_core.endpoints", "EndpointResolverParams");
        writer.write("""
                        # Step 7f: Invoke endpoint_resolver.resolve_endpoint
                        endpoint_resolver_parameters = EndpointResolverParams(
                            operation=operation,
                            input=context.request,
                            context=context.properties
                        )
                        logger.debug("Calling endpoint resolver with parameters: %s", endpoint_resolver_parameters)
                        endpoint = await config.endpoint_resolver.resolve_endpoint(
                            endpoint_resolver_parameters
                        )
                        logger.debug("Endpoint resolver result: %s", endpoint)
                        if not endpoint.uri.path:
                            path = ""
                        elif endpoint.uri.path.endswith("/"):
                            path = endpoint.uri.path[:-1]
                        else:
                            path = endpoint.uri.path
                        if context.transport_request.destination.path:
                            path += context.transport_request.destination.path
                        context.transport_request.destination = URI(
                            scheme=endpoint.uri.scheme,
                            host=context.transport_request.destination.host + endpoint.uri.host,
                            path=path,
                            port=endpoint.uri.port,
                            query=context.transport_request.destination.query,
                        )
                """);
        if (context.applicationProtocol().isHttpProtocol()) {
            writer.write("""
                            if (headers := endpoint.properties.get("headers")) is not None:
                                context.transport_request.fields.extend(headers)
                    """);
        }
        writer.popState();

        writer.write("""
                        # Step 7g: Invoke modify_before_signing
                        context = replace(
                            context,
                            transport_request=interceptor.modify_before_signing(context)
                        )

                        # Step 7h: Invoke read_before_signing
                        interceptor.read_before_signing(context)

                """);

        writer.pushState(new SignRequestSection());
        if (context.applicationProtocol().isHttpProtocol() && supportsAuth) {
            writer.addStdlibImport("re");
            writer.addStdlibImport("typing", "Any");
            writer.addImport("smithy_core.interfaces.identity", "Identity");
            writer.addImport("smithy_core.types", "PropertyKey");
            writer.write("""
                            # Step 7i: sign the request
                            if auth_option and signer:
                                logger.debug("HTTP request to sign: %s", context.transport_request)
                                logger.debug(
                                    "Signer properties: %s",
                                    auth_option.signer_properties
                                )
                                context = replace(
                                    context,
                                    transport_request= await signer.sign(
                                        http_request=context.transport_request,
                                        identity=identity,
                                        signing_properties=auth_option.signer_properties,
                                    )
                                )
                                logger.debug("Signed HTTP request: %s", context.transport_request)

                                # TODO - Move this to separate resolution/population function
                                fields = context.transport_request.fields
                                auth_value = fields["Authorization"].as_string()  # type: ignore
                                signature = re.split("Signature=", auth_value)[-1]  # type: ignore
                                context.properties["signature"] = signature.encode('utf-8')

                                identity_key: PropertyKey[Identity | None] = PropertyKey(
                                    key="identity",
                                    value_type=Identity | None  # type: ignore
                                )
                                sp_key: PropertyKey[dict[str, Any]] = PropertyKey(
                                    key="signer_properties",
                                    value_type=dict[str, Any]  # type: ignore
                                )
                                context.properties[identity_key] = identity
                                context.properties[sp_key] = auth_option.signer_properties
                    """);
        }
        writer.popState();

        writer.write("""
                        # Step 7j: Invoke read_after_signing
                        interceptor.read_after_signing(context)

                        # Step 7k: Invoke modify_before_transmit
                        context = replace(
                            context,
                            transport_request=interceptor.modify_before_transmit(context)
                        )

                        # Step 7l: Invoke read_before_transmit
                        interceptor.read_before_transmit(context)

                """);

        writer.pushState(new SendRequestSection());
        if (context.applicationProtocol().isHttpProtocol()) {
            writer.addDependency(SmithyPythonDependency.SMITHY_HTTP);
            writer.addImport("smithy_http.interfaces", "HTTPRequestConfiguration");
            writer.write("""
                            # Step 7m: Invoke http_client.send
                            request_config = config.http_request_config or HTTPRequestConfiguration()
                            logger.debug("HTTP request config: %s", request_config)
                            logger.debug("Sending HTTP request: %s", context.transport_request)

                            if request_future is not None:
                                response_task = asyncio.create_task(config.http_client.send(
                                    request=context.transport_request,
                                    request_config=request_config,
                                ))
                                request_future.set_result(context)
                                transport_response = await response_task
                            else:
                                transport_response = await config.http_client.send(
                                    request=context.transport_request,
                                    request_config=request_config,
                                )

                            response_context = ResponseContext(
                                request=context.request,
                                transport_request=context.transport_request,
                                transport_response=transport_response,
                                properties=context.properties
                            )
                            logger.debug("Received HTTP response: %s", response_context.transport_response)

                    """);
        }
        writer.popState();

        writer.write("""
                        # Step 7n: Invoke read_after_transmit
                        interceptor.read_after_transmit(response_context)

                        # Step 7o: Invoke modify_before_deserialization
                        response_context = replace(
                            response_context,
                            transport_response=interceptor.modify_before_deserialization(response_context)
                        )

                        # Step 7p: Invoke read_before_deserialization
                        interceptor.read_before_deserialization(response_context)

                        # Step 7q: deserialize
                        logger.debug("Deserializing transport response: %s", response_context.transport_response)
                        output = await deserialize(
                            response_context.transport_response, config
                        )
                        output_context = OutputContext(
                            request=response_context.request,
                            response=output,
                            transport_request=response_context.transport_request,
                            transport_response=response_context.transport_response,
                            properties=response_context.properties
                        )
                        logger.debug("Deserialization complete. Response: %s", output_context.response)

                        # Step 7r: Invoke read_after_deserialization
                        interceptor.read_after_deserialization(output_context)
                    except Exception as e:
                        output_context: OutputContext[Input, Output, $1T, $2T] = OutputContext(
                            request=context.request,
                            response=e,  # type: ignore
                            transport_request=context.transport_request,
                            transport_response=transport_response,
                            properties=context.properties
                        )

                    return await self._finalize_attempt(interceptor, output_context)

                async def _finalize_attempt[Input: SerializeableShape, Output: DeserializeableShape](
                    self,
                    interceptor: Interceptor[Input, Output, $1T, $2T],
                    context: OutputContext[Input, Output, $1T, $2T | None],
                ) -> OutputContext[Input, Output, $1T, $2T | None]:
                    # Step 7s: Invoke modify_before_attempt_completion
                    try:
                        context = replace(
                            context,
                            response=interceptor.modify_before_attempt_completion(context)
                        )
                    except Exception as e:
                        logger.exception("Exception occurred while handling: %s", context.response)
                        context = replace(context, response=e)

                    # Step 7t: Invoke read_after_attempt
                    try:
                        interceptor.read_after_attempt(context)
                    except Exception as e:
                        context = replace(context, response=e)

                    return context

                async def _finalize_execution[Input: SerializeableShape, Output: DeserializeableShape](
                    self,
                    interceptor: Interceptor[Input, Output, $1T, $2T],
                    context: OutputContext[Input, Output, $1T | None, $2T | None],
                ) -> Output:
                    try:
                        # Step 9: Invoke modify_before_completion
                        context = replace(
                            context,
                            response=interceptor.modify_before_completion(context)
                        )

                        # Step 10: Invoke trace_probe.dispatch_events
                        try:
                            pass
                        except Exception as e:
                            # log and ignore exceptions
                            logger.exception("Exception occurred while dispatching trace events: %s", e)
                            pass
                    except Exception as e:
                        logger.exception("Exception occurred while handling: %s", context.response)
                        context = replace(context, response=e)

                    # Step 11: Invoke read_after_execution
                    try:
                        interceptor.read_after_execution(context)
                    except Exception as e:
                        context = replace(context, response=e)

                    # Step 12: Return / throw
                    if isinstance(context.response, Exception):
                        raise context.response

                    # We may want to add some aspects of this context to the output types so we can
                    # return it to the end-users.
                    return context.response
                """, transportRequest, transportResponse);
        writer.dedent();
        writer.popState();
    }

    private boolean hasEventStream() {
        var streamIndex = EventStreamIndex.of(model);
        var topDownIndex = TopDownIndex.of(model);
        for (OperationShape operation : topDownIndex.getContainedOperations(context.settings().service())) {
            if (streamIndex.getInputInfo(operation).isPresent() || streamIndex.getOutputInfo(operation).isPresent()) {
                return true;
            }
        }
        return false;
    }

    private void initializeHttpAuthParameters(PythonWriter writer) {
        var derived = new LinkedHashSet<DerivedProperty>();
        for (PythonIntegration integration : context.integrations()) {
            for (RuntimeClientPlugin plugin : integration.getClientPlugins(context)) {
                if (plugin.matchesService(model, service)
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
        var operationSymbol = symbolProvider.toSymbol(operation);
        var operationMethodSymbol = operationSymbol.expectProperty(OPERATION_METHOD);
        var pluginSymbol = CodegenUtils.getPluginSymbol(context.settings());

        var input = model.expectShape(operation.getInputShape());
        var inputSymbol = symbolProvider.toSymbol(input);

        var output = model.expectShape(operation.getOutputShape());
        var outputSymbol = symbolProvider.toSymbol(output);

        writer.pushState(new OperationSection(service, operation));
        writer.openBlock("async def $L(self, input: $T, plugins: list[$T] | None = None) -> $T:",
                "",
                operationMethodSymbol.getName(),
                inputSymbol,
                pluginSymbol,
                outputSymbol,
                () -> {
                    writeSharedOperationInit(writer, operation, input);

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
                                    operation=$T,
                                )
                                """, serSymbol, deserSymbol, operationSymbol);
                    }
                });
        writer.popState();
    }

    private void writeSharedOperationInit(PythonWriter writer, OperationShape operation, Shape input) {
        writer.writeDocs(() -> {
            var docs = writer.formatDocs(operation.getTrait(DocumentationTrait.class)
                    .map(StringTrait::getValue)
                    .orElse(String.format("Invokes the %s operation.",
                            operation.getId().getName())));

            var inputDocs = input.getTrait(DocumentationTrait.class)
                    .map(StringTrait::getValue)
                    .orElse("The operation's input.");

            writer.write("""
                    :param input: $L

                    :param plugins: A list of callables that modify the configuration dynamically.
                        Changes made by these plugins only apply for the duration of the operation
                        execution and will not affect any other operation invocations.

                        $L
                        """, inputDocs, docs);
        });

        var defaultPlugins = new LinkedHashSet<SymbolReference>();
        for (PythonIntegration integration : context.integrations()) {
            for (RuntimeClientPlugin runtimeClientPlugin : integration.getClientPlugins(context)) {
                if (runtimeClientPlugin.matchesOperation(model, service, operation)) {
                    runtimeClientPlugin.getPythonPlugin().ifPresent(defaultPlugins::add);
                }
            }
        }
        writer.write("""
                operation_plugins: list[Plugin] = [
                    $C
                ]
                if plugins:
                    operation_plugins.extend(plugins)
                """, writer.consumer(w -> writeDefaultPlugins(w, defaultPlugins)));

    }

    private void generateEventStreamOperation(PythonWriter writer, OperationShape operation) {
        writer.pushState();
        writer.addDependency(SmithyPythonDependency.SMITHY_CORE);
        var operationSymbol = symbolProvider.toSymbol(operation);
        writer.putContext("operation", operationSymbol);
        var operationMethodSymbol = operationSymbol.expectProperty(OPERATION_METHOD);
        writer.putContext("operationName", operationMethodSymbol.getName());
        var pluginSymbol = CodegenUtils.getPluginSymbol(context.settings());
        writer.putContext("plugin", pluginSymbol);

        var input = model.expectShape(operation.getInputShape());
        var inputSymbol = symbolProvider.toSymbol(input);
        writer.putContext("input", inputSymbol);

        var eventStreamIndex = EventStreamIndex.of(model);
        var inputStreamSymbol = eventStreamIndex.getInputInfo(operation)
                .map(EventStreamInfo::getEventStreamTarget)
                .map(symbolProvider::toSymbol)
                .orElse(null);
        writer.putContext("inputStream", inputStreamSymbol);

        var output = model.expectShape(operation.getOutputShape());
        var outputSymbol = symbolProvider.toSymbol(output);
        writer.putContext("output", outputSymbol);

        var outputStreamSymbol = eventStreamIndex.getOutputInfo(operation)
                .map(EventStreamInfo::getEventStreamTarget)
                .map(symbolProvider::toSymbol)
                .orElse(null);
        writer.putContext("outputStream", outputStreamSymbol);

        writer.putContext("hasProtocol", context.protocolGenerator() != null);
        if (context.protocolGenerator() != null) {
            var serSymbol = context.protocolGenerator().getSerializationFunction(context, operation);
            writer.putContext("serSymbol", serSymbol);
            var deserSymbol = context.protocolGenerator().getDeserializationFunction(context, operation);
            writer.putContext("deserSymbol", deserSymbol);
        } else {
            writer.putContext("serSymbol", null);
            writer.putContext("deserSymbol", null);
        }

        if (inputStreamSymbol != null) {
            if (outputStreamSymbol != null) {
                writer.write("""
                        async def ${operationName:L}(
                            self,
                            input: ${input:T},
                            plugins: list[${plugin:T}] | None = None
                        ) -> DuplexEventStream[${inputStream:T}, ${outputStream:T}, ${output:T}]:
                            ${C|}
                            ${^hasProtocol}
                            raise NotImplementedError()
                            ${/hasProtocol}
                            ${?hasProtocol}
                            return await self._duplex_stream(
                                input=input,
                                plugins=operation_plugins,
                                serialize=${serSymbol:T},
                                deserialize=${deserSymbol:T},
                                config=self._config,
                                operation=${operation:T},
                                event_deserializer=$T().deserialize,
                            )  # type: ignore
                            ${/hasProtocol}
                        """,
                        writer.consumer(w -> writeSharedOperationInit(w, operation, input)),
                        outputStreamSymbol.expectProperty(SymbolProperties.DESERIALIZER));
            } else {
                writer.addImport("smithy_core.aio.eventstream", "InputEventStream");
                writer.write("""
                        async def ${operationName:L}(
                            self,
                            input: ${input:T},
                            plugins: list[${plugin:T}] | None = None
                        ) -> InputEventStream[${inputStream:T}, ${output:T}]:
                            ${C|}
                            ${^hasProtocol}
                            raise NotImplementedError()
                            ${/hasProtocol}
                            ${?hasProtocol}
                            return await self._input_stream(
                                input=input,
                                plugins=operation_plugins,
                                serialize=${serSymbol:T},
                                deserialize=${deserSymbol:T},
                                config=self._config,
                                operation=${operation:T},
                            )  # type: ignore
                            ${/hasProtocol}
                        """, writer.consumer(w -> writeSharedOperationInit(w, operation, input)));
            }
        } else {
            writer.write("""
                    async def ${operationName:L}(
                        self,
                        input: ${input:T},
                        plugins: list[${plugin:T}] | None = None
                    ) -> OutputEventStream[${outputStream:T}, ${output:T}]:
                        ${C|}
                        ${^hasProtocol}
                        raise NotImplementedError()
                        ${/hasProtocol}
                        ${?hasProtocol}
                        return await self._output_stream(
                            input=input,
                            plugins=operation_plugins,
                            serialize=${serSymbol:T},
                            deserialize=${deserSymbol:T},
                            config=self._config,
                            operation=${operation:T},
                            event_deserializer=$T().deserialize,
                        )  # type: ignore
                        ${/hasProtocol}
                    """,
                    writer.consumer(w -> writeSharedOperationInit(w, operation, input)),
                    outputStreamSymbol.expectProperty(SymbolProperties.DESERIALIZER));
        }

        writer.popState();
    }
}
