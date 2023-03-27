## Smithy Python Codegen Test

This package is a hand-written Smithy package that generates a python client. The
shapes in this package are intended to exercise as many parts of the generator as
possible to ensure they generate valid code that passes mypy checks. For
example, there are cases that ensure that we're properly escaping shape names that
would collide with built in types (e.g. a shape called `Exception` would collide with
the builtin of the same name if it weren't escaped).

This package does not contain any actual unit tests. Mypy passing and python not
failing to parse the output is the intended test. For actual unit tests, see the
[`smithy-python-protocol-test` package
](https://github.com/awslabs/smithy-python/tree/develop/codegen/smithy-python-protocol-test).

### When should I change this package?

Any time an issue is discovered where the code generator generates invalid code
from a valid model. A similar shape should then be added to this package's Smithy
model. That shape then MUST be connected to the service, for example by adding it to
the output of an operation already attached to the service. If the shape isn't
connected in this way, it will be stripped from the model before code generation and
therefore will not be generated.
