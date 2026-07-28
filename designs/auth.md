# Identity and Authentication

Smithy services may define any number of authentication schemes via traits and
configure which schemes are available and prioritized on a per-operation basis.
This document describes how an auth scheme is configured and picked at runtime.

## Auth Schemes

Everything to do with an auth scheme is contained within an implementation of
the `AuthScheme` Protocol. These implementations construct the
[identity resolvers](#identity-resolvers) and [signers](#signers) as well as the
extra properties needed for identity resolution and signing.

Each `AuthScheme` has a `scheme_id`, which is the Smithy shape ID of the auth
scheme.

```python
class AuthScheme[R: Request, I: Identity, IP: Mapping[str, Any], SP: Mapping[str, Any]](
    Protocol
):
    scheme_id: ShapeID

    def identity_properties(self, *, context: _TypedProperties) -> IP:
        ...

    def identity_resolver(
        self, *, context: _TypedProperties
    ) -> IdentityResolver[I, IP]:
        ...

    def signer_properties(self, *, context: _TypedProperties) -> SP:
        ...

    def signer(self) -> Signer[R, I, SP]:
        ...

    def event_signer(self, *, request: R) -> EventSigner[I, SP] | None:
        return None
```

`AuthScheme` implementations SHOULD cache identity resolvers and signers if
possible.

### Auth Scheme Resolution

Services and operation may support any number of auth schemes, each of which may
or may not be availble for a number of reasons, such as not being configured. An
`AuthSchemeResolver` is used to figure out which auth scheme to use for each
request.

```python
class AuthSchemeResolver(Protocol):
    def resolve_auth_scheme(
        self, *, auth_parameters: AuthParams[Any, Any]
    ) -> Sequence[AuthOption]:
        ...

class AuthOption(Protocol):
    scheme_id: ShapeID
    identity_properties: TypedProperties
    signer_properties: TypedProperties

@dataclass(kw_only=True, frozen=True)
class AuthParams[I: SerializeableShape, O: DeserializeableShape]:
    protocol_id: ShapeID
    operation: APIOperation[I, O]
    context: TypedProperties
```

The resolver is given the ID of the protocol being used by the client, the
schema of the operation being invoked, and the operation invocation context. It
returns a priority-ordered list of auth schemes to pick from, along with
optional overrides for identity and signer properties.

The client will pick the first auth scheme in the list that has an entry in the
`auth_schemes` [configuration](#configuration) dict and which is able to resolve
an identity.

The resolver itself is stored in the service's [configuration](#configuration)
object, and may be replaced with a custom implemenatation. Default
implementations are generated based on the modeled auth traits.

## Identity

Each auth scheme is associated with an identity type, such as an API key or
username and password. In the AWS context, this is the access key id, secret
access key, and optionally the session token.

Identities MAY be shared between multiple auth schemes. For example, the AWS
sigv4 and sigv4a auth schemes use the same AWS identity.

In Python, each identity type MUST implement the following `Protocol`:

```python
@runtime_checkable
class Identity(Protocol):

    expiration: datetime | None = None

    @property
    def is_expired(self) -> bool:
        if self.expiration is None:
            return False
        return datetime.now(tz=UTC) >= self.expiration
```

An `Identity` may be derived from any number of sources, such as configuration
properties or environement variables. These different sources are loaded by an
[`IdentityResolver`](#identity-resolvers).

### Identity Resolvers

Identity resolvers are responsible for contructiong an `Identity` for a request.

```python
class IdentityResolver[I: Identity, IP: Mapping[str, Any]](Protocol):

    async def get_identity(self, *, properties: IP) -> I:
        ...
```

Each identity source SHOULD have its own identity resolver implementation. If an
`Identity` is supported by multiple `IdentityResolver`s, those resolver SHOULD
be prioritized to provide a stable resolution strategy. A
`ChainedIdentityResolver` implementation is provided that implements this
behavior generically.

The `get_identity` function takes only one (keyword-only) argument - a mapping
of properties that is refined by the `IP` generic parameter. The identity
properties are contructed by the `AuthScheme`'s `identity_properties` method.

Identity resolvers are constructed by the `AuthScheme`'s `identity_resolver`
method.

## Signers

Signers are responsible for signing transport requests so that they can be
authenticated by the server. They are given the transport request to sign, the
resolved identity, and a property mapping that is used for any additional
configuration needed. The signing properties are constructed by the
`AuthScheme`'s `signer_properties` method.

```python
class Signer[R: Request, I, SP: Mapping[str, Any]](Protocol):
    async def sign(self, *, request: R, identity: I, properties: SP) -> R:
        ...
```

Signers are constructed by the `AuthScheme`'s `signer` method.

Signers MAY modify the given request and return it, or construct a new signed
request.

### Event Signers

Auh schemes MAY also have an associated event signer, which signs events that
are sent to a server. They behave in the same way as normal signers, except that
they sign an event instead of a transport request. The properties passed to this
signing method are identical to those pased to the request signer.

```python
class EventSigner[I, SP: Mapping[str, Any]](Protocol):

    # TODO: add a protocol type for events
    async def sign(self, *, event: Any, identity: I, properties: SP) -> Any:
        ...
```

## Configuration

All services with at least one auth trait will have the following properites on
their configuration object.

```python
class AuthConfig[R: Request](Protocol):
    auth_scheme_resolver: AuthSchemeResolver
    auth_schemes: dict[ShapeID, AuthScheme[R, Any, Any, Any]]
```
