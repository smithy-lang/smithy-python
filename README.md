## Smithy Python

**WARNING: All interfaces are subject to change.**

We are in the very early stages of beginning work on low-level Python SDK
modules that aim to provide basic, reusable, and composable interfaces for
lower level SDK tasks. Using these modules customers should be able to generate
synchronous and asynchronous service client or server implementations based on
services defined using [Smithy](https://smithy.io/).

### What is this repository?

This repository contains two major components:

1) Smithy code generators for Python
2) Core modules and interfaces for building service clients in Python

### Smithy Code Generators

[Smithy](https://smithy.io/) is a protocol-agnostic interface
definition language that provides a
[code generation framework](https://github.com/awslabs/smithy/tree/main/smithy-codegen-core)
for building service clients, servers, and documentation. The `codegen` directory
contains the source code for generating these tools. See the code generation
[README](https://github.com/awslabs/smithy-python/blob/develop/codegen/README.md)
for more information.

### Core Modules and Interfaces

The `smithy-python` package provides the core modules and interfaces required
to build a service client or server. These basic modules include things like:
an HTTP/1.1 and HTTP/2 client implementation, retry strategies, etc.

### What are the design goals of this project?

* **Components must be modular** - Most importantly, these building blocks
need to be composable and reusable across a wide variety of use cases,
including use cases beyond an AWS SDK. Interfaces such as credential resolvers,
request signing, data models, serialization, etc. should all be reusable across
many different contexts.

* **Components should be well documented and publicly exported** - Both AWS and
customers should have a high level of confidence that the building blocks we're
creating are well supported, understood, and maintained. Customers should not
have to hack on internal or undocumented interfaces to achieve their goals.

* **Components must support all concurrency paradigms** - As `asyncio` and
other asynchronous frameworks begin to gain prominence in the Python community
we need to ensure the interfaces and abstractions we're building can work
across many different concurrency paradigms without requiring rewrites.

* **Components must be typed** - All of the buildings blocks we create must be
typed and usable via `mypy`. Given the nature of gradual typing it's paramount
that foundational components and interfaces be typed to preserve the integrity
of the typing system.

* **Components should be consistent with other AWS SDKs** - When building
interfaces or libraries that overlap with the required functionality of other
AWS SDKs we should strive to be consistent with other SDKs as our deafult
stance. This project will heavily draw insipiration from the precedents set
by the [smithy-typescript](https://github.com/awslabs/smithy-typescript/) and
[smithy-go](https://github.com/aws/smithy-go) packages.

### How can I contribute?

We're currently heavily investing in writing proposals and documenting the
design decisions made. Feedback on the
[proposed designs and interfaces](https://github.com/awslabs/smithy-python/tree/develop/designs)
is extremely helpful at this stage to ensure we're providing functional and
ergonomic interfaces that meet customer expectations.

### Using repository tooling

This repository is intended to contain the source for multiple Python and Java
packages, so the process of development may be a bit different than what you're
familiar with.

#### Java - gradle

The Java-based code generation uses Gradle, which is a fairly common Java build
tool that natively supports building, testing, and publishing multiple packages
in one place. If you've used Gradle before, then there's nothing in this repo
that will surprise you.

If you haven't used Gradle before, don't worry - it's pretty easy to use. You
will need to have JDK 17 or newer installed, but that's the only thing you
need to install yourself. We recommend the [Coretto]
(https://docs.aws.amazon.com/corretto/latest/corretto-17-ug/downloads-list.html)
distribution, but any JDK that's at least version 17 will work.

To build and run all the Java packages, simply run `./gradlew clean build` from
the `codegen` directory. If this is the first time you have run this, it will
download Gradle onto your system to run along with any dependencies of the Java
packages.

For more details on working on the code generator, see the readme in the
`codegen` directory.

#### Python - pants

Building multiple python packages in a single repo is a little less common than
it is for Java or some other languages, so even if you're a python expert you
may be unfamiliar with the tooling. The tool we're using is called [pants]
(https://www.pantsbuild.org), and you use it pretty similarly to how you use
Gradle.

Like Gradle, pants provides a wrapper script that downloads its dependencies as
needed. Currently, pants requires python 3.7, 3.8, or 3.9 to run, so one of
those must be available on your path. (It doesn't have to be the version that
is linked to `python` or `python3`, it just needs `python3.9` etc.) It is,
however, fully capable of building and working with code that uses newer python
versions like we do. This repository uses a minimum python version of 3.11
for all its packages, so you will need that too to work on it.

Pants provides a number of python commands it calls goals, documente [here]
(https://www.pantsbuild.org/docs/python-goals). In short:

* `./pants fmt ::` - This will run our formatters on all of the python library
  code. Use this before you make a commit.
* `./pants lint ::` - This will run our linters on all of the python library
  code. You should also use this before you make a commit, and particularly
  before you make a pull request.
* `./pants check ::` - This will run mypy on all of the python library code.
  This should be used regularly, and must pass for any pull request.
* `./pants test ::` - This will run all of the tests written for the python
  library code. Use this as often as you'd run pytest or any other testing
  tool. Under the hood, we are using pytest.

There are other commands as well that you can find in the [docs]
(https://www.pantsbuild.org/docs/python-goals), but these are the one you'll
use the most.

Important to note is those pairs of colons. These are pants [targets]
(https://www.pantsbuild.org/docs/targets#target-addresses). The double colon is
a special target that means "everything". So running exactly what's listed
above will run those goals on every python file or other relevant file. You can
also target just `smithy_python`, for example, with
`./pants check python-packages/smithy-python/smithy_python:source`, or even
individual files with something like
`./pants check python-packages/smithy-python/smithy_python/interfaces/http.py:../source`.
To list what targets are available in a directory, run
`./pants list path/to/dir:`. For more detailed information, see the [docs]
(https://www.pantsbuild.org/docs/targets#target-addresses).

## License

This project is licensed under the Apache-2.0 License.
