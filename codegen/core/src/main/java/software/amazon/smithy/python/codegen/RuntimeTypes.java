/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen;

import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.utils.SmithyUnstableApi;

/**
 * Pre-defined Symbol constants for all framework types used across generators.
 *
 * <p>Using these symbols with the {@code $T} formatter ensures that all framework type
 * references participate in the writer's collision detection system. When a service model
 * defines a shape with the same name as a framework type, the writer will automatically
 * alias the import to avoid shadowing.
 */
@SmithyUnstableApi
public final class RuntimeTypes {

    // smithy_core.schemas
    public static final Symbol SCHEMA = createSymbol("schemas", "Schema", SmithyPythonDependency.SMITHY_CORE);
    public static final Symbol API_OPERATION =
            createSymbol("schemas", "APIOperation", SmithyPythonDependency.SMITHY_CORE);

    // smithy_core.shapes
    public static final Symbol SHAPE_ID = createSymbol("shapes", "ShapeID", SmithyPythonDependency.SMITHY_CORE);
    public static final Symbol SHAPE_TYPE = createSymbol("shapes", "ShapeType", SmithyPythonDependency.SMITHY_CORE);

    // smithy_core.serializers
    public static final Symbol SHAPE_SERIALIZER =
            createSymbol("serializers", "ShapeSerializer", SmithyPythonDependency.SMITHY_CORE);

    // smithy_core.deserializers
    public static final Symbol SHAPE_DESERIALIZER =
            createSymbol("deserializers", "ShapeDeserializer", SmithyPythonDependency.SMITHY_CORE);

    // smithy_core.documents
    public static final Symbol DOCUMENT = createSymbol("documents", "Document", SmithyPythonDependency.SMITHY_CORE);
    public static final Symbol TYPE_REGISTRY =
            createSymbol("documents", "TypeRegistry", SmithyPythonDependency.SMITHY_CORE);

    // smithy_core.exceptions
    public static final Symbol MODELED_ERROR =
            createSymbol("exceptions", "ModeledError", SmithyPythonDependency.SMITHY_CORE);
    public static final Symbol SERIALIZATION_ERROR =
            createSymbol("exceptions", "SerializationError", SmithyPythonDependency.SMITHY_CORE);
    public static final Symbol EXPECTATION_NOT_MET_ERROR =
            createSymbol("exceptions", "ExpectationNotMetError", SmithyPythonDependency.SMITHY_CORE);

    // smithy_core.traits
    public static final Symbol TRAIT = createSymbol("traits", "Trait", SmithyPythonDependency.SMITHY_CORE);
    public static final Symbol API_KEY_LOCATION =
            createSymbol("traits", "APIKeyLocation", SmithyPythonDependency.SMITHY_CORE);

    // smithy_core.auth
    public static final Symbol AUTH_PARAMS = createSymbol("auth", "AuthParams", SmithyPythonDependency.SMITHY_CORE);
    public static final Symbol AUTH_OPTION = createSymbol("auth", "AuthOption", SmithyPythonDependency.SMITHY_CORE);

    // Note: AuthOption from smithy_core.interfaces.auth has the same simple name as
    // AuthOption from smithy_core.auth. The collision resolver will automatically
    // disambiguate them with module-based aliases.
    public static final Symbol AUTH_OPTION_INTERFACE =
            createSymbol("interfaces.auth", "AuthOption", SmithyPythonDependency.SMITHY_CORE);

    // smithy_core.retries
    public static final Symbol RETRY_STRATEGY_RESOLVER =
            createSymbol("retries", "RetryStrategyResolver", SmithyPythonDependency.SMITHY_CORE);
    public static final Symbol RETRY_STRATEGY_OPTIONS =
            createSymbol("retries", "RetryStrategyOptions", SmithyPythonDependency.SMITHY_CORE);
    public static final Symbol SIMPLE_RETRY_STRATEGY =
            createSymbol("retries", "SimpleRetryStrategy", SmithyPythonDependency.SMITHY_CORE);

    // smithy_core.interfaces.retries
    public static final Symbol RETRY_STRATEGY =
            createSymbol("interfaces.retries", "RetryStrategy", SmithyPythonDependency.SMITHY_CORE);

    // smithy_core.types
    public static final Symbol TYPED_PROPERTIES =
            createSymbol("types", "TypedProperties", SmithyPythonDependency.SMITHY_CORE);

    // smithy_core.interceptors
    public static final Symbol INTERCEPTOR_CHAIN =
            createSymbol("interceptors", "InterceptorChain", SmithyPythonDependency.SMITHY_CORE);
    public static final Symbol INTERCEPTOR =
            createSymbol("interceptors", "Interceptor", SmithyPythonDependency.SMITHY_CORE);

    // smithy_core.aio.client
    public static final Symbol CLIENT_CALL =
            createSymbol("aio.client", "ClientCall", SmithyPythonDependency.SMITHY_CORE);
    public static final Symbol REQUEST_PIPELINE =
            createSymbol("aio.client", "RequestPipeline", SmithyPythonDependency.SMITHY_CORE);

    // smithy_core.aio.eventstream
    public static final Symbol DUPLEX_EVENT_STREAM =
            createSymbol("aio.eventstream", "DuplexEventStream", SmithyPythonDependency.SMITHY_CORE);
    public static final Symbol INPUT_EVENT_STREAM =
            createSymbol("aio.eventstream", "InputEventStream", SmithyPythonDependency.SMITHY_CORE);
    public static final Symbol OUTPUT_EVENT_STREAM =
            createSymbol("aio.eventstream", "OutputEventStream", SmithyPythonDependency.SMITHY_CORE);

    // smithy_core.aio.interfaces
    public static final Symbol ASYNC_BYTE_STREAM =
            createSymbol("aio.interfaces", "AsyncByteStream", SmithyPythonDependency.SMITHY_CORE);
    public static final Symbol ENDPOINT_RESOLVER =
            createSymbol("aio.interfaces", "EndpointResolver", SmithyPythonDependency.SMITHY_CORE);

    // smithy_core.aio.endpoints
    public static final Symbol STATIC_ENDPOINT_RESOLVER =
            createSymbol("aio.endpoints", "StaticEndpointResolver", SmithyPythonDependency.SMITHY_CORE);

    // smithy_core.aio.types
    public static final Symbol ASYNC_BYTES_READER =
            createSymbol("aio.types", "AsyncBytesReader", SmithyPythonDependency.SMITHY_CORE);

    // smithy_core.aio.utils
    public static final Symbol ASYNC_LIST = createSymbol("aio.utils", "async_list", SmithyPythonDependency.SMITHY_CORE);

    // smithy_http
    public static final Symbol TUPLES_TO_FIELDS =
            createSymbol("", "tuples_to_fields", SmithyPythonDependency.SMITHY_HTTP);

    // Note: HTTPResponse from smithy_http.aio has the same simple name as HTTPResponse
    // from smithy_http.aio.interfaces. The collision resolver will automatically
    // disambiguate them with module-based aliases.
    public static final Symbol HTTP_RESPONSE_IMPL =
            createSymbol("aio", "HTTPResponse", SmithyPythonDependency.SMITHY_HTTP);

    // smithy_http.interfaces
    public static final Symbol HTTP_REQUEST_CONFIGURATION =
            createSymbol("interfaces", "HTTPRequestConfiguration", SmithyPythonDependency.SMITHY_HTTP);
    public static final Symbol HTTP_CLIENT_CONFIGURATION =
            createSymbol("interfaces", "HTTPClientConfiguration", SmithyPythonDependency.SMITHY_HTTP);

    // smithy_http.aio.interfaces
    public static final Symbol HTTP_REQUEST =
            createSymbol("aio.interfaces", "HTTPRequest", SmithyPythonDependency.SMITHY_HTTP);
    public static final Symbol HTTP_RESPONSE =
            createSymbol("aio.interfaces", "HTTPResponse", SmithyPythonDependency.SMITHY_HTTP);

    // smithy_http.aio.crt
    public static final Symbol AWS_CRT_HTTP_CLIENT =
            createSymbol("aio.crt", "AWSCRTHTTPClient", SmithyPythonDependency.SMITHY_HTTP);

    // smithy_http.aio.aiohttp
    public static final Symbol AIOHTTP_CLIENT =
            createSymbol("aio.aiohttp", "AIOHTTPClient", SmithyPythonDependency.SMITHY_HTTP);

    // smithy_http.aio.identity.apikey
    public static final Symbol API_KEY_IDENTITY_RESOLVER =
            createSymbol("aio.identity.apikey", "APIKeyIdentityResolver", SmithyPythonDependency.SMITHY_HTTP);

    // smithy_aws_core.aio.protocols 
    public static final Symbol REST_JSON_CLIENT_PROTOCOL = createSymbol(
            "aio.protocols",
            "RestJsonClientProtocol",
            SmithyPythonDependency.SMITHY_AWS_CORE);

    // smithy_aws_core.identity 
    public static final Symbol STATIC_CREDENTIALS_RESOLVER = createSymbol(
            "identity",
            "StaticCredentialsResolver",
            SmithyPythonDependency.SMITHY_AWS_CORE);

    private RuntimeTypes() {}

    private static Symbol createSymbol(String module, String name, PythonDependency dependency) {
        var namespace = module.isEmpty() ? dependency.packageName() : dependency.packageName() + "." + module;
        return Symbol.builder()
                .name(name)
                .namespace(namespace, ".")
                .addDependency(dependency)
                .build();
    }
}
