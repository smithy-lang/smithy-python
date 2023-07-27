## Smithy Python

**WARNING: All interfaces are subject to change.**

We are in the early stages of beginning work on low-level Python SDK modules
that aim to provide basic, reusable, and composable interfaces for lower level
SDK tasks. Using these modules customers should be able to generate
asynchronous service client implementations based on services defined using
[Smithy](https://smithy.io/).

This code generator, and the clients it generates, are unstable and should not
be used in production systems yet. Several features, such as detailed logging,
have not been implemented yet.

### What is this repository?

This repository contains two major components:

1) Smithy code generators for Python
2) Core modules and interfaces for building service clients in Python

These components facilitate generating clients for any [Smithy](https://smithy.io/)
service. The `codegen` directory contains the source code for generating clients.
The `python-packages` directory contains the source code for the hand-written python
components.

This repository does *not* contain any generated clients, such as for S3 or other
AWS services. Rather, these are the tools that facilitate the generation of those
clients and non-AWS Smithy clients.

### How do I use this?

The first step is to create a Smithy pacakge. If this is your first time working
with Smithy, follow [this quickstart guide](https://smithy.io/2.0/quickstart.html)
to learn the basics and create a simple Smithy model.

Once you have a service defined in Smithy, you will need to define what protocol
it uses. Currently the only supported protocol is
[restJson1](https://smithy.io/2.0/aws/protocols/aws-restjson1-protocol.html).
This is a protocol based on AWS services, but is broadly applicable to any
service that uses rest bindings with a JSON body type. Simply add the protocol
trait to your service shape and you'll be ready.

The following is a basic example service model that echoes messages sent to it.
To use this model to generate a client, save it to a file called `main.smithy`
in a folder called `model`.

```smithy
$version: "2.0"

namespace com.example

use aws.protocols#restJson1

/// Echoes input
@restJson1
service EchoService {
    version: "2006-03-01"
    operations: [EchoMessage]
}

@http(uri: "/echo", method: "POST")
operation EchoMessage {
    input := {
        @httpHeader("x-echo-message")
        message: String
    }
    output := {
        message: String
    }
}
```

You also will need a build configuration file named `smithy-build.json`, which
for this example service should look the following json. For more information on
this file, see the
[smithy-build docs](https://smithy.io/2.0/guides/building-models/build-config.html).

```json
{
    "version": "1.0",
    "sources": ["model"],
    "maven": {
        "dependencies": [
            "software.amazon.smithy:smithy-model:[1.34.0,2.0)",
            "software.amazon.smithy:smithy-aws-traits:[1.34.0,2.0)",
            "software.amazon.smithy.python:smithy-python-codegen:0.1.0"
        ]
    },
    "projections": {
        "client": {
            "plugins": {
                "python-client-codegen": {
                    "service": "com.example#EchoService",
                    "module": "echo",
                    "moduleVersion": "0.0.1"
                }
            }
        }
    }
}
```

The code generator, `smithy-python-codegen`, hasn't been published yet, so
you'll need to build it yourself. To build and run the generator you will need
the following prerequisites:

* Python 3.11 or newer
  * (optional) Install [black](https://black.readthedocs.io/en/stable/) in your
    environment to have the generated output be auto-formatted.
* The [Smithy CLI](https://smithy.io/2.0/guides/smithy-cli/cli_installation.html)
* JDK 17 or newer
* make

Now run `make install-components` from the root of this repository. This will
install the python dependencies in your environment and make the code generator
available locally. For more information on the underlying build process, see the
"Using repository tooling" section.

Now from your model directory run `smithy build` and you'll have a generated
client! The client can be found in `build/smithy/client/python-client-codegen`.
The following is a snippet showing how you might use it:

```python
import asyncio

from echo.client import EchoService
from echo.config import Config
from echo.models import EchoMessageInput


async def main() -> None:
    client = EchoService(Config(endpoint_uri="https://example.com/"))
    response = await client.echo_message(EchoMessageInput(message="spam"))
    print(response.message)


if __name__ == "__main__":
    asyncio.run(main())
```

#### Is Java really required?

Only for now. Once the generator has been published, the Smithy CLI will be able
to run the it without a separate Java installation. Similarly, once the python
helper libraries have been published you won't need to install them manually.

### Core Modules and Interfaces

The `smithy-python` package provides the core modules and interfaces required
to build a service client. These basic modules include things like:
an HTTP/1.1 and HTTP/2 client implementation, retry strategies, etc.

The `aws-smithy-python` package provides implementations of those interfaces
for AWS, such as sigv4 signers.

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
will need to have JDK 17 or newer installed, but that's the only thing you need
to install yourself. We recommend the
[Coretto](https://docs.aws.amazon.com/corretto/latest/corretto-17-ug/downloads-list.html)
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
may be unfamiliar with the tooling. The tool we're using is called
[pants](https://www.pantsbuild.org), and you use it pretty similarly to how you
use Gradle.

Like Gradle, pants provides a wrapper script that downloads its dependencies as
needed. Currently, pants requires python 3.7, 3.8, or 3.9 to run, so one of
those must be available on your path. (It doesn't have to be the version that
is linked to `python` or `python3`, it just needs `python3.9` etc.) It is,
however, fully capable of building and working with code that uses newer python
versions like we do. This repository uses a minimum python version of 3.11
for all its packages, so you will need that too to work on it.

Pants provides a number of python commands it calls goals, documented
[here](https://www.pantsbuild.org/docs/python-goals). In short:

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

There are other commands as well that you can find in the
[docs](https://www.pantsbuild.org/docs/python-goals), but these are the ones
you'll use the most.

Important to note is those pairs of colons. These are pants
[targets](https://www.pantsbuild.org/docs/targets#target-addresses). The double
colon is a special target that means "everything". So running exactly what's
listed above will run those goals on every python file or other relevant file.
You can also target just `smithy_python`, for example, with
`./pants check python-packages/smithy-python/smithy_python:source`, or even
individual files with something like
`./pants check python-packages/smithy-python/smithy_python/interfaces/http.py:../source`.
To list what targets are available in a directory, run
`./pants list path/to/dir:`. For more detailed information, see the
[docs](https://www.pantsbuild.org/docs/targets#target-addresses).

#### Common commands - make

There is also a `Makefile` that bridges the Python and Java build systems together to
make common workflows simple, single commands. The two most important commands are:

* `make install-components` which builds and installs the Java generator and the python
  packages. The generator is published to maven local and the python packages are
  installed into the active python environment. This command is most useful for those
  who simply want to run the generator and use a generated client.v
* `make test-protocols` which runs all the protocol tests. It will first (re)install
  all necessary components to ensure that the latest is being used. This is most useful
  for developers working on the generator and python packages.

To see what else available, run `make help` or examine the file directly.

## Security issue notifications

If you discover a potential security issue in this project we ask that you
notify AWS/Amazon Security via our
[vulnerability reporting page](http://aws.amazon.com/security/vulnerability-reporting/).
Please do **not** create a public github issue.

## License

This project is licensed under the Apache-2.0 License.
