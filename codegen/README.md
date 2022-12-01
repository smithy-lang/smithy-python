## Smithy Python

Smithy code generators for Python.

### Prerequisites

* JDK 17 or newer is required to run the code generator. The
  [Coretto](https://docs.aws.amazon.com/corretto/latest/corretto-17-ug/downloads-list.html)
  distribution is recommended.

#### Optional Prerequisites - Python

* Python 3.11 is required to run the generated code, but not run the generator.
  If it is present on the path, the generator will use it for linting and
  formatting.
* If `black` is installed in the version of python found on the path, it will
  be used to format the generated code.
* If `mypy` is installed in the version of python found on the path, it will
  be used to check the generated code. For mypy to pass, the `smithy_python`
  package will need to be installed. To install those, run the following in
  the repository root:

  ```
  ./pants package ::
  pip3 install dist/*.whl
  ```

### Building the generator

The code generator uses the [gradle](https://gradle.org) build system, accessed
via the gradle wrapper `gradlew`. To build the generator, simply run
`./gradlew clean build`. This will also run the generator on the
`smithy-python-codegen-test` repo.

**WARNING: All interfaces are subject to change.**

## License

This project is licensed under the Apache-2.0 License.
