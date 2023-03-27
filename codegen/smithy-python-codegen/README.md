## Smithy Python Codegen

This package implements generic Smithy Python client generation. This includes, but is
not limited to, the following capabilities:

* Generating Python data types from Smithy shapes.
* Generating fully functional clients for Smithy services.
* Generating serializers and deserializers for generic protocols.
* Providing interfaces for implementing protocols and customizing of all code
  generation.

This package MUST NOT include any components that are only applicable to a particular
organization. For example, [sigv4
](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_aws-signing.html)
(an AWS HTTP authorization mechanism) support MUST NOT be implemented in this package
since it isn't generally applicable outside of AWS.

### When should I change this package?

Any time one of the above capabilities needs to change. For example, if the plugin
mechanism for the code generator is missing some features then [`PythonIntegration`
](https://github.com/awslabs/smithy-python/blob/develop/codegen/smithy-python-codegen/src/main/java/software/amazon/smithy/python/codegen/integration/PythonIntegration.java)
likely needs to be changed.
