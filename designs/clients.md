# Smithy Python Client Specification

## Abstract

This document will describe the high-level client interfaces that will be
provided as part of the smithy-python package. These interfaces will serve
as the basis for implementing extensible code generated service clients
from Smithy models.

## Motivation

A Smithy SDK is composed of an collection of tools that enable creating
isolated, pluggable components. These pieces require some level of
orchestration to work together, share configuration, and track
inter-operational state. This is typically done by a high-level client which
houses these components and ensures they coordinate correctly.

During some initial testing we created a model for what a next generation
Client might look like for the [Amazon Transcribe Streaming SDK](https://github.com/awslabs/amazon-transcribe-streaming-sdk/blob/908364e5bb8a301fdf26fe01f4ff83fb62659c06/amazon_transcribe/client.py#L41).
This was modeled much more closely to the concepts in Boto3 and Botocore
which are dynamically generated at runtime from models. One of our
learnings from this was we’re exposing too many low-level options at
the Client interface. Going forward, our plan is to store this kind of
functionality at the Middleware level. This allows for a simplified client
entry point for basic usage while exposing extensible interfaces for more
advanced customization.

## Specification

A Smithy Client in the Python SDK will be the primary orchestration layer for
composing related functionality for a given service. Each client will take
input for at least 2 concepts allowing for the minimum viable client.

* **Context:** The SDK context is an object composed of resources and definitions
    used to bootstrap the client and middleware. This contains definitions for
    additional Middleware modifications, custom components and the Middleware
    context. This will also be used to manage things like configuring event loops
    for Async clients.

* **Configuration:** This is an object containing a collection of runtime
    settings for the client. This may include things such as variable
    IO/threading settings, service-level runtime settings
    (i.e. use_dualstack), hook specifications, logger configuration, and
    client identity. The key distinction here between Context and Configuration
    is the former is build time information, the latter is runtime.

### High-level Client

For a high-level example, a general Client might look something like this:

```python
class AsyncSmithyClient:
    """
    A high level class for orchestrating async call stacks and operations
    """
    def __init__(
        self,
        *,
        context: Optional[SDKContext] = None,
        config: Optional[ClientConfig] = None,
    ):
        self.context = set_default(context, SDKContext())
        self.config_provider = ConfigProvider(config)


class SDKContext:
    def __init__(
       self,
       *,
       middleware: Optional[
           dict[middleware.Step, list[tuple[Callable, MiddlewarePosition]]]
       ] = None,
       middleware_context: Optional[dict[str, Any]] = None,
       event_loop: Optional[asyncio.BaseEventLoop] = None,
       ...
   ):
       self.middleware = middleware
       self.middleware_context = middleware_context
       self.event_loop = event_loop
       ...

def set_default(value: Any, default_value: Any) -> Any:
    if value is None:
        return default_value
    return value
```

**NOTE:** ClientConfig defined below in [Configuration][#configuration].


The client offloads a majority of the functionality to our middleware layer
which will be composed per operation. The middleware stacks will be defined
via code gen but can be further modified via the context. This will be
accomplished by building the middleware chain with every operation
invocation, allowing it to change between calls if needed. When a client
is declared with operations, that will serve as a thin layer for the
middleware chain where arguments are accepted only as keyword arguments,
then forwarded to the middleware API as a SmithyInput object.

As a Smithy Client becomes more specific, such as in the case of an AWS SDK,
you will see specific extensions encapsulated in the ClientConfig, and
SDKContext objects. These were previously handled via top-level client
arguments which will be avoided going forward. The benefits of this change
is flexibility of both client usage and function signature growth. When
establishing a client in Boto3, it became locked to a region via the
`region_name` argument. This required creating multiple clients for simple
tasks like replicating an object to multiple regions. Instead, you’ll now
be able to create a single ClientConfig that can be used across multiple
clients if needed. You may also perform operation specific updates, such
as changing the region, to allow a single client to interact cross-region.

Other components such as credentials, signing and endpoint resolution will
be handled by the code generator via appropriate provider classes used in
relevant middleware. Updates for these components will be handled via
overrides in the client or operation context.

An example of a more specific client, such as one for Amazon S3, might
look something like this:

```python
class AsyncS3Client:
    """
    An async client for interacting with AWS' S3 service APIs.
    """
    def __init__(
        self,
        *,
        context: Optional[SDKContext] = None,
        config: Optional[ClientConfig] = None,
    ):
        self.service_name = "s3",
        self.context = set_default(context, SDKContext())
        self.config_provider = ConfigProvider(config)

    async def list_buckets(
        self,
        *,
        context: Optional[SDKContext] = None,
        config: Optional[ClientConfig] = None,
    ) -> S3ListBucketResponse:
        config = self.config_provider.resolve_config(config)
        middleware = AsyncSmithyStack[S3ListBucketInput, S3ListBucketResponse]()
        middleware.serialize.add_after(
            serialize_parameters
        )
        middleware.build.add_after(
            build_request
        )
        middleware.finalize.add_after(
            sign_request
        )
        middleware.finalize.add_after(
            send_request
        )
        finalize_middleware(middleware, context)

        stack_input = S3ListBucketInput(input={})
        middleware_context = context.middleware_context
        middleware_context.config.update(config)

        return await middleware.resolve(
            deserialize_response, context=middleware_context
        )(stack_input)

    async def put_object(
        self,
        *,
        bucket: str,
        key: str,
        config: S3Config,
        context: S3Context,
        acl: Optional[S3ACLEnum] = None,
        body: Optional[BinaryInputType] = None,
        cache_control: Optional[str] = None,
        content_disposition: Optional[str] = None,
        content_encoding: Optional[str] = None,
        content_language: Optional[str] = None,
        content_length: Optional[int] = None,
        content_md5: Optional[str] = None,
        content_type: Optional[str] = None,
        checksum_algorithm: Optional[S3ChecksumEnum] = None,
        checksum_crc32: Optional[str] = None,
        checksum_crc32c: Optional[str] = None,
        checksum_sha1: Optional[str] = None,
        checksum_sha256: Optional[str] = None,
        expected_bucket_owner: Optional[str] = None,
        expires: Optional[datetime] = None,
        grant_full_control: Optional[str] = None,
        grant_read: Optional[str] = None,
        grant_read_acp: Optional[str] = None,
        grant_write_acp: Optional[str] = None,
        metadata: Optional[dict[str, str]] = None,
        server_side_encryption: Optional[S3SSETypeEnum] = None,
        storage_class: Optional[S3StorageClassEnum] = None,
        website_redirect_location: Optional[str] = None,
        sse_customer_algorithm: Optional[str] = None,
        sse_customer_key: Optional[str] = None,
        sse_kms_key_id: Optional[str] = None,
        sse_kms_encryption_context: Optional[str] = None,
        bucket_key_enabled: Optional[bool] = None,
        request_payer: Optional[str] = None,
        tagging: Optional[str] = None,
        object_lock_mode: Optional[S3ObjectLockModeEnum] = None,
        object_lock_retain_until: Optional[datetime] = None,
        object_lock_legal_hold_status: Optional[S3ObjectLockLegalHoldStatusEnum] = None,
    ) -> S3PutObjectResponse:

        middleware = AsyncSmithyStack[S3PutBucketInput, S3ListBucketResponse]()

        middleware.serialize.add_after(serialize_parameters)
        middleware.build.add_after(build_request)
        middleware.finalize.add_after(sign_request)
        middleware.finalize.add_after(send_request)
        # Apply middleware customizations
        finalize_middleware(middleware, context)

        stack_input = S3PutObjectInput(
            params=dict(
                bucket=bucket,
                key=key,
                acl=acl,
                body=body,
                cache_control=cache_control,
                content_disposition=content_disposition,
                content_encoding=content_encoding,
                content_language=content_language,
                **kwargs,
            ),
            config=config,
        )

        return await stack.resolve(deserialize_response, context={})(stack_input)
```

### Configuration

Configuration for the client will be handled as a cascading chain of precedence.
When a client is established, a ConfigProvider will be initialized with any
client-level configuration provided. This provider will establish a canonical
view of available configurations from four primary areas:

1. The client’s default settings determined by code gen
2. Environment configurations (Environment Variables and Config files)
3. A user-provided ClientConfig
4. A user-provided OperationConfig

These sources are listed in precedence order from least-specific to most-specific.
The provider will use this information to establish its config model per operation.
This allows for dynamic behavior as the environment is modified over the
lifecycle of the client but prevents mid-operation disruptions. When an operation
is invoked, the config will be derived in the same manner the middleware
stack is constructed.

Through the four levels of precedence there will be varied scopes of what
configurations are available. The environment may not have the same
granularity as the operation config due to some options not making sense
globally. These scopes will be determined at code generation time, where
the ClientConfig will be a superset of non-service specific settings.

An example ConfigProvider and its components might look something like this:

```python
class ConfigProvider:
    def __init__(self, *, client_config: ClientConfig):
        self.client_config = config
        self.environment_config = EnvironmentConfigProvider()

    async def resolve_config(
        self,
        *,
        operation_config: Optional[OperationConfig] = None
    ):
        """Resolve full configuration for a given operation call."""
        config = ClientConfig()
        env_config = await self.environment_config.resolve()
        config.update(env_config)
        config.update(self.client_config)
        config.update(operation_config)
        return config

class EnvironmentConfigProvider:
    def __init__(self):
        # We can have non-AWS specific env vars like
        # CURL_CA_BUNDLE, HTTPS_PROXY, etc. in a generic
        # EnvironmentConfigProvider for Smithy.
        self.variable_mapping = {
            "AWS_REGION": "region",
            "AWS_CONFIG_FILE": "config_file",
            "AWS_PROFILE": "profile",
            ...
        }

    async def resolve(self):
        config = EnvironmentConfig()
        for env_var, client_var in self.variable_mapping.items():
            if env_var in os.environ:
                config[client_var] = os.environ[env_var]
        return config

class ClientConfig:
    def __init__(
        self,
        *,
        region: str,
        use_dualstack: Optional[bool] = False,
        use_fips: Optional[bool] = False,
        credentials: Optional[Credentials] = None,
        ...
   ):
       self.region = region
       self.use_dualstack = use_dualstack
       self.use_fips = use_fips
       self.credentials = credentials
       ...

   def __getitem__(self, config_name):
       if hasattr(self, config_name):
           return getattr(self, config_name)
       raise KeyError(f'{config_name} is not a valid config option')

   def __setitem__(self, config_name, config_value):
       if hasattr(self, config_name):
           setattr(self, config_name, config_value)
       raise KeyError(f'{config_name} is not a valid config option')
```

### Middleware Composition

When a client is code generated, it will have all of its operations created
with their default middleware stacks. Which middleware are included in
the operation stack will vary based on supported behavior such as S3’s
Multi-Region Access Points. This will result in different signing and
build middlewares being generated to accommodate the nuanced composition
based on user input. Users can modify these default stacks to extend or
update functionality using their context, either at client creation or
operation invocation time.

An example middleware stack can be seen above in our ListBucket example:

```python

        # Initialize the stack with input and output types
        # This includes 5 steps (Initialize, Serialize, Build, Finalize, Deserialize)
        middleware = AsyncSmithyStack[S3ListBucketInput, S3ListBucketResponse]()

         # Now we add service/operation specific middlewares via code gen
        middleware.serialize.add_after(
            serialize_parameters # Use S3-specific serializer
        )
        middleware.build.add_after(
            build_request # Add specific metadata like S3 Checksums
        )
        middleware.finalize.add_after(
            # Account for signature variances based on resource target
            # i.e. MRAP (sigv4 vs sigv4a)
            sign_request
        )
        middleware.finalize.add_after(
            # Handle functionality like multi-part upload
            # or 100 continue
            send_request
        )
        # Add any middleware customizations
        finalize_middleware(middleware, context)
```

An example of what one of these middleware might look like would be:

```python
@before # Syntactic sugar to simplify middleware wrapping (see below)
async def sign_request(
    finalize_input: FinalizeInput[S3ListBucketInput],
) -> None:
    # Create our credential provider based on the config
    credential_resolver = CredentialProvider(finalize_input.context.get('config'))
    credentials = credential_resolver.get_credentials()

    # Resolve signer at runtime, potentially affected by previous middleware
    signer = SignerResolver(finalize_input.context.get('config')).resolve()
    signature = await signer.sign(
        credentials=credentials,
        url=finalize_input.request.url,
        headers=finalize_input.request.headers,
        body=finalize_input.request.body,
    )
    # Apply signature in place
    apply_signature(finalize_input.request, signature)

def before(
    func: AsyncHandler[Input, None]
) -> SmithyEntry[AsyncMiddleware[Input, Any]]:
    """A void-handler that occurs before the rest of the chain.
    Does not provide the response.
    """

    def _middleware(next_handler: AsyncHandler[Input, Any]) -> AsyncHandler[Input, Any]:
        async def _handler(param: Input) -> Any:
            await func(param)
            return await next_handler(param)

        return _handler

    smithy_entry: SmithyEntry[AsyncMiddleware[Input, Any]] = SmithyEntry(
        entry=_middleware, name=func.__name__,
    )
    return smithy_entry
```

Now let’s say we want to add our own custom Retry handler as a middleware
layer. This can be done by handing either the client or the operation an
list of ordered callback functions which mutate our middleware stack.

```python
async def retry_request(input: Input, next_handler: Middleware) -> Output:
    return next_handler(input)

def retry_request(
    next_handler: AsyncFinalizeHandler[S3ListBucketInput, S3ListBucketOutput]
) -> AsyncFinalizeHandler[S3ListBucketInput, S3ListBucketOutput]:
     """Retry Middleware Handler"""

    async def _retry_request_standard(
        finalize_input: FinalizeInput[S3ListBucketInput],
    ) -> FinalizeOutput[S3ListBucketOutput]:
        # Something like StandardRetryStrategy()
        retry_strategy = finalize_input.context['retryStrategy']

        # We can either take an operation configured partition
        # or compute it ourselves. It currently operates as an
        # arbitrary bucket identifier. This could als be created
        # by another middleware.
        token = await retry_strategy.acquireRetryToken(
            finalize_input.context['retryPartition'],
            finalize_input.context['retryTimeout']
        )
        response = await next_handler(finalize_input)

        while is_retryable(response):
            error_type = await resolve_error_type(response, RetryErrorType)
            try:
                # BackoffStrategy is used as part of waitForRetry
                await retry_strategy.waitForRetry(token, error_type)
                response = await next_handler(finalize_input)
            except RetryError as e:
                response = RetryFailureResponse(e, finalize_input)

        if is_successful(response):
            retry_strategy.recordSuccess(token)
        return response

    return _retry_request_standard

def my_middleware_callback(middleware: SmithyStack) -> None:
    entry = SmithyEntry(retry_request, name="retry_request")
    middleware.finalize.add_before(entry)

# Now we wire it up to our operation

context = SDKContext(
    middleware_updates=[
        my_middleware_callback,
        ...
    ]
)

s3_client = AsyncS3Client()

# Default middleware chain
# serialize_parameters -> build_request -> sign_request -> send_request
buckets = await s3_client.list_buckets()

# Call with ListBucket with retries
# serialize_parameters -> build_request -> retry_request -> sign_req -> send_req
buckets = await s3_client.list_buckets(context=context)
```


Now that we’ve added the retry handler into the chain, any failures in
sign_request or send_request will recurse back up the chain. Our new
middleware can intercept these failed responses and determine if they can be
retried. On a retryable response, the middleware will call sign_request again
to reinvoke the rest of the middleware chain. All state for this will be
managed within the middleware context.

### Synchronicity

For the initial implementation of the Smithy Python SDK, we’ve chosen to focus
solely on an async client. The intent here is to solve a growing demand for
an Async Python SDK and ensure we have the right primitives in place for this
paradigm.  There will likely still be a desire for synchronous implementations
which we’ll use community feedback to assess. At this time, we don’t intend to
use asyncio wrappers to generate faux-sync interfaces around our async clients
due to unexpected interactions with the event loop. Previous attempts at this
approach have led to unexpected failure states when code that’s expected to
be “synchronous” is run in an environment without an event loop or specific
threading contexts.

The implications of this are still being explored. However, it’s worth noting
future synchronous client generation may require a separate stack of components
to avoid relying on any event loop.


## FAQ/Open Questions

*Q: Where does the Config live in the Middleware stack? (Open)*

A: TBD.

When the configuration is resolved for an operation, it needs to be passed into
the middleware stack for use. Middleware is currently only defined to have a
“Context” bucket for anything and everything. This is likely going to be
conflated with the client level context, even the two are technically disjoint.
Passing the config in as part of the Middleware context feels odd, should it
be a top-level parameter for a Middleware Stack along with context?

*Q: What primitives are we missing in the middleware stack? (Open)*
A: TBD.

Currently, we have some issues with the middleware interfaces for how new
middleware are added. Once a single middleware exists in a Step, it’s not
possible to do absolute assertions (i.e. put this at the front of the list).
It requires explicit knowledge of each middleware name. We should consider
allowing absolute insertion at the beginning and end of the step.

I’d propose the concept of a MiddlewarePosition which might help us
accomplish this. This object is the composition of an directional enum
(middleware.BEFORE and middleware.AFTER) along with an optional middleware
name. Inclusion of a middleware name will set the position relative.
Otherwise, BEFORE defaults to first position and AFTER defaults to
last position.

*Q: How will we handle clients using multiple protocols?*

A: Clients supporting more than one protocol/serialization format will need
to construct multiple middleware stacks. Each will be stored on the client
with a designation for the protocol to be used. This does pose some issues
for “global” middleware changes where the end user wants to inject a change
once and have it applied to all stacks. We may need a concept of something
like a middleware chain collection, that all clients rely on, containing 1
or more chains. This could support collection-wide operations such as updates
and deletes.

We don’t intend to handle multiple protocols at this time. This piece would
be handled by code gen if needed.

*Q: Where does signing occur and where are the signers created/stored?*

A: Signing in the context of the middlewares is kind of odd. We’ll typically
have only one signer per service, but that’s not necessarily true anymore in
the cases of S3 and Eventbridge. To accomodate this, most middleware stacks
will be generated with a signing step that contains a SigningProvider. This
can be used based on information derived from the context and request to
retrieve and instantiate a signer. This will be done at runtime for each
operation since the middleware stack is recreated with each invocation.
This also allows for dynamic signing substitution if needed.
