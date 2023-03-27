## Smithy AWS Python Codegen

This package implements AWS-specific code generation plugins to the python generator.
Anything that is specific to AWS MUST be implemented here. Examples include most [AWS
protocols](https://smithy.io/2.0/aws/protocols/index.html)(*),
[sigv4](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_aws-signing.html),
and AWS service customizations. Conversely, any features that are
NOT specific to AWS MUST NOT be implemented here.

*The only exception to this rule is the `RestJson1` protocol implementation, which is
included in the generic generator for now to provide a default supported protocol.

One very important thing to keep in mind when implementing features and integrations
here is that they MUST NOT be coupled wherever possible. For example, a user
MUST be able to use sigv4 even if they aren't using an AWS protocol or even the
[service trait](https://smithy.io/2.0/aws/aws-core.html#aws-api-service-trait).

### Why separate AWS components from the core package and each other?

Smithy is intended to be a generic IDL that can describe a broad range of protocols,
not just AWS protocols. Separating the code generation components forces developers
to provide interfaces capable of achieving that goal and ensures that users only
have to take what they need.

In the future, these components may be moved to an entirely different repository to
strengthen that divide even more.

### When should I change this package?

Any time an AWS component needs to be modified or added. This can include adding
support for new protocols, new auth traits, or new service customizations.
