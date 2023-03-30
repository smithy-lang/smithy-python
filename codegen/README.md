## Smithy Python

This project defines the [Smithy](https://smithy.io/) code generators for Python
clients.

### Prerequisites

* JDK 17 or newer is required to run the code generator. The
  [Coretto](https://docs.aws.amazon.com/corretto/latest/corretto-17-ug/downloads-list.html)
  distribution is recommended.

#### Optional Prerequisites - Python

* Python 3.11 is required to run the generated code, but not run the generator.
  If it is present on the path, the generator will use it for linting and
  formatting.
* Use of a [Python virtual environment](https://docs.python.org/3/library/venv.html)
  is highly recommended.
* If `black` is installed in the version of python found on the path, it will
  be used to format the generated code.
* If `mypy` is installed in the version of python found on the path, it will
  be used to check the generated code. For mypy to pass, the `smithy_python`
  package will need to be installed. To install those into your active environment,
  run `make install-python-components` from the repository root.

### Building the generator

The code generator uses the [gradle](https://gradle.org) build system, accessed
via the gradle wrapper `gradlew`. To build the generator, simply run
`./gradlew clean build`. Alternatively, run `make smithy-build` from the repo
root. To run the protocol tests, run `make test-protocols`.

**WARNING: All interfaces are subject to change.**

### Where should I get started?

The best place to start is the [Smithy documentation](https://smithy.io/) to understand
what Smithy is and how this project relates to it. In particular, the [Creating a
Smithy Code Generator](https://smithy.io/2.0/guides/building-codegen/index.html) guide
covers the overall design of Smithy generators.


[`PythonClientCodegenPlugin`
](https://github.com/awslabs/smithy-python/blob/develop/codegen/smithy-python-codegen/src/main/java/software/amazon/smithy/python/codegen/PythonClientCodegenPlugin.java),
a [Smithy build plugin
](https://smithy.io/2.0/guides/building-codegen/creating-codegen-repo.html#creating-a-smithy-build-plugin),
is the entry point where this code generator links to the Smithy build process
(see also: [SmithyBuildPlugin javadoc
](https://smithy.io/javadoc/1.26.1/software/amazon/smithy/build/SmithyBuildPlugin.html)).
This class doesn't do much by itself, but everything flows from here.

Another good place to start is [`DirectedPythonCodegen`
](https://github.com/awslabs/smithy-python/blob/develop/codegen/smithy-python-codegen/src/main/java/software/amazon/smithy/python/codegen/DirectedPythonCodegen.java).
This is an implementation of Smithy's [directed codegen interface
](https://smithy.io/javadoc/1.26.1/software/amazon/smithy/codegen/core/directed/DirectedCodegen.html)
, which enables us to make use of shared orchestration code and provides a more guided
path to generating a client. This class is the heart of the generator, everything else
follows from here. For example, you could look here to find out how Smithy structures
are generated into Python objects. Most of the code that does that is somewhere else,
but it's called directly from here. This class is constructed by `PythonCodegenPlugin`
and handed off to a [`CodegenDirector`
](https://smithy.io/javadoc/1.26.1/software/amazon/smithy/codegen/core/directed/CodegenDirector.html)
which calls its public methods.

One more possible starting point is [`SymbolVisitor`
](https://github.com/awslabs/smithy-python/blob/develop/codegen/smithy-python-codegen/src/main/java/software/amazon/smithy/python/codegen/SymbolVisitor.java).
This class is responsible for taking a Smithy shape and determining what its
name in Python should be, where it should be defined in Python, what dependencies
it has, and attaching any other important properties that are needed for generating
the python types. See the [smithy docs
](https://smithy.io/2.0/guides/building-codegen/decoupling-codegen-with-symbols.html)
for more details on the symbol provider concept.

Finally, you might look at the [`integration` package
](https://github.com/awslabs/smithy-python/tree/develop/codegen/smithy-python-codegen/src/main/java/software/amazon/smithy/python/codegen/integration).
This package is what provides [plugins
](https://smithy.io/2.0/guides/building-codegen/making-codegen-pluggable.html)
to the python generator. Anything that implements [`PythonIntegration`
](https://github.com/awslabs/smithy-python/blob/develop/codegen/smithy-python-codegen/src/main/java/software/amazon/smithy/python/codegen/integration/PythonIntegration.java)
which is present on the Java classpath can hook into the code generation process.
Crucially, this is how protocol implementations are implemented and how default
runtime customizations are added. See
[`RestJsonIntegration`](https://github.com/awslabs/smithy-python/blob/develop/codegen/smithy-python-codegen/src/main/java/software/amazon/smithy/python/codegen/integration/RestJsonIntegration.java)
for an example of a protocol implementation.

## License

This project is licensed under the Apache-2.0 License.
