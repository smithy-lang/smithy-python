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
The `python-packages` directory contains the source code for the handwritten python
components.

This repository does *not* contain any generated clients, such as for S3 or other
AWS services. Rather, these are the tools that facilitate the generation of those
clients and non-AWS Smithy clients.

### How do I use this to create a client?

The first step is to create a Smithy package. If this is your first time working
with Smithy, follow [this quickstart guide](https://smithy.io/2.0/quickstart.html)
to learn the basics and create a simple Smithy model.

Once you have a service defined in Smithy, you will need to define what protocol
it uses. Currently, the only supported protocol is
[restJson1](https://smithy.io/2.0/aws/protocols/aws-restjson1-protocol.html).
This is a protocol based on AWS services, but is broadly applicable to any
service that uses rest bindings with a JSON body type. Simply add the protocol
trait to your service shape, and you'll be ready.

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
            "software.amazon.smithy:smithy-model:[1.54.0,2.0)",
            "software.amazon.smithy:smithy-aws-traits:[1.54.0,2.0)",
            "software.amazon.smithy.python.codegen:core:0.0.1"
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

With both files your project directory should look like this:
```
.
├── model
│   └── main.smithy
└── smithy-build.json
```


The code generator libraries have not been published yet, so
you'll need to build it yourself. To build and run the generator, you will need
the following prerequisites installed in your environment:

* [uv](https://docs.astral.sh/uv/)
* The [Smithy CLI](https://smithy.io/2.0/guides/smithy-cli/cli_installation.html)
* JDK 17 or newer
* make
* [pandoc](https://pandoc.org/installing.html) CLI

This project uses [uv](https://docs.astral.sh/uv/) for managing all things python.
Once you have it installed, run the following command to check that it's ready to use:

```shell
uv --help
```

With `uv` installed, run `make install` from the root of this repository. This will
set up your workspace with all of the dependencies and tools needed to build the
project. For more information on the underlying process, see the 
"Using repository tooling" section.

> [!TIP]
> Make sure to run the following command as directed before proceeding:
>```shell
> source .venv/bin/activate
> ```
> This will activate the [virtual environment](https://docs.python.org/3/library/venv.html)
> in your current shell.

With your workspace set up and activated, run the following command to install the
the codegen libraries locally:

```shell
cd codegen && ./gradlew publishToMavenLocal
```

Finally, change into your smithy project's directory, run `smithy build`, and you'll
have a generated client! The client can be found in
`build/smithy/client/python-client-codegen`. The following is a snippet showing how
you might use it:

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

#### pandoc CLI

Smithy [documentation traits](https://smithy.io/2.0/spec/documentation-traits.html#documentation-trait) are modeled in one of two formats:

- **Raw HTML** for AWS services  
- **CommonMark** for all other Smithy-based services (may include embedded HTML)

The code generator uses [pandoc](https://pandoc.org/) to normalize and convert this 
content into Markdown suitable for Google-style Python docstrings.

#### Is Java really required?

Only for now. Once the generator has been published, the Smithy CLI will be able
to run it without a separate Java installation. Similarly, once the python
helper libraries have been published you won't need to install them locally.

### How do I generate types for shapes without a client?

If all you want are concrete Python classes for the shapes in your Smithy model,
all you need to do is replace `python-client-codegen` with
`python-type-codegen` when following the steps above. Your `smithy-build.json`
would now look like:

```json
{
    "version": "1.0",
    "sources": ["model"],
    "maven": {
        "dependencies": [
            "software.amazon.smithy:smithy-model:[1.54.0,2.0)",
            "software.amazon.smithy.python.codegen.plugins:types:0.0.1"
        ]
    },
    "projections": {
        "shapes": {
            "plugins": {
                "python-type-codegen": {
                    "service": "com.example#EchoService",
                    "module": "echo",
                    "moduleVersion": "0.0.1"
                }
            }
        }
    }
}
```

The module with the generated shape classes can be found in
`build/smithy/client/python-type-codegen` after you run `smithy-build`.

Unlike when generating a client, a service shape is not required for shape
generation. If a service is not provided then every shape found in the model
will be generated. Any naming conflicts may be resolved by using the
[`renameShapes` transform](https://smithy.io/2.0/guides/smithy-build-json.html#renameshapes)
(or renaming the shapes in the model of course).

The set of shapes generated can also be constrained by using the
[`includeShapesBySelector` transform](https://smithy.io/2.0/guides/smithy-build-json.html#includeshapesbyselector).
For example, to generate only shapes within the `com.example` namespace:

```json
{
    "version": "1.0",
    "sources": ["model"],
    "maven": {
        "dependencies": [
            "software.amazon.smithy:smithy-model:[1.54.0,2.0)",
            "software.amazon.smithy.python.codegen.plugins:types:0.0.1"
        ]
    },
    "projections": {
        "shapes": {
            "transforms": [
                {
                    "name": "includeShapesBySelector",
                    "args": {
                        "selector": "[id|namespace = 'com.example']"
                    }
                }
            ],
            "plugins": {
                "python-type-codegen": {
                    "module": "echo",
                    "moduleVersion": "0.0.1"
                }
            }
        }
    }
}
```

Input and output shapes (shapes with the `@input` or `@output` traits and
operation inputs / outputs created as part of an operation definition) are not
generated by default. To generate these shapes anyway, set the
`generateInputsAndOutputs` property to `true`.

```json
{
    "version": "1.0",
    "sources": ["model"],
    "maven": {
        "dependencies": [
            "software.amazon.smithy:smithy-model:[1.54.0,2.0)",
            "software.amazon.smithy.python.codegen.plugins:types:0.0.1"
        ]
    },
    "projections": {
        "shapes": {
            "plugins": {
                "python-type-codegen": {
                    "module": "echo",
                    "moduleVersion": "0.0.1",
                    "generateInputsAndOutputs": true
                }
            }
        }
    }
}
```

You can also generate both a client package and a shape package in one build,
but they won't depend on each other. To do this, just add both plugins in the
projection, or create a projection for each plugin. Below is an example showing
both plugins in one projection:

```json
{
    "version": "1.0",
    "sources": ["model"],
    "maven": {
        "dependencies": [
            "software.amazon.smithy:smithy-model:[1.54.0,2.0)",
            "software.amazon.smithy:smithy-aws-traits:[1.54.0,2.0)",
            "software.amazon.smithy.python.codegen:core:0.0.1",
            "software.amazon.smithy.python.codegen.plugins:types:0.0.1"
        ]
    },
    "projections": {
        "client": {
            "plugins": {
                "python-client-codegen": {
                    "service": "com.example#EchoService",
                    "module": "echo",
                    "moduleVersion": "0.0.1"
                },
                "python-type-codegen": {
                    "service": "com.example#EchoService",
                    "module": "echo",
                    "moduleVersion": "0.0.1"
                }
            }
        }
    }
}
```

### Core Modules and Interfaces

* `smithy-core` provides transport-agnostic core modules and interfaces
  required to build a service client. This includes things like retry
  strategies, URI interfaces, shared types, etc.
* `smithy-http` provides HTTP core modules and interfaces required to build
  HTTP service clients, including optional HTTP client implementations.
  Currently it provides two async HTTP clients that are useable with the
  `aiohttp` or `awscrt` optional dependency sets respectively.
* `smithy-aws-core` provides implementations of `smithy-core` interfaces for
  AWS, such as SigV4 signers.

### What are the design goals of this project?

* **Components must be modular** - Most importantly, these building blocks
need to be composable and reusable across a wide variety of use cases,
including use cases beyond an AWS SDK. Interfaces such as credential resolvers,
request signing, data models, serialization, etc. should all be reusable across
many contexts.

* **Components should be well documented and publicly exported** - Both AWS and
customers should have a high level of confidence that the building blocks we're
creating are well-supported, understood, and maintained. Customers should not
have to hack on internal or undocumented interfaces to achieve their goals.

* **Components must be typed** - All the buildings blocks we create must be
typed and usable via `pyright`. Given the nature of gradual typing, it is paramount
that foundational components and interfaces be typed to preserve the integrity
of the typing system.

* **Components should be consistent with other AWS SDKs** - When building
interfaces or libraries that overlap with the required functionality of other
AWS SDKs we should strive to be consistent with other SDKs as our default
stance. This project will heavily draw inspiration from the precedents set
by the [smithy-typescript](https://github.com/awslabs/smithy-typescript/) and
[smithy-go](https://github.com/aws/smithy-go) packages.

### How can I contribute?

We're currently heavily investing in writing proposals and documenting the
design decisions made. Feedback on the
[proposed designs and interfaces](https://github.com/smithy-lang/smithy-python/tree/develop/designs)
is extremely helpful at this stage to ensure we're providing functional and
ergonomic interfaces that meet customer expectations.

### Using repository tooling

This repository is intended to contain the source for multiple Python and Java
packages, so the process of development may be a bit different from what you're
familiar with.

#### Java - gradle

The Java-based code generation uses Gradle, which is a fairly common Java build
tool that natively supports building, testing, and publishing multiple packages
in one place. If you've used Gradle before, then there's nothing in this repo
that will surprise you.

If you haven't used Gradle before, don't worry - it's pretty easy to use. You
will need to have JDK 17 or newer installed, but that's the only thing you need
to install yourself. We recommend the
[Corretto](https://docs.aws.amazon.com/corretto/latest/corretto-17-ug/downloads-list.html)
distribution, but any JDK that's at least version 17 will work.

To build and run all the Java packages, simply run `./gradlew clean build` from
the `codegen` directory. If this is the first time you have run this
(or if you didn't already run `make install`), it will download Gradle onto your
system to run along with any dependencies of the Java packages.

For more details on working on the code generator, see the readme in the
`codegen` directory.

#### Python - uv

Building multiple python packages in a single repo is a little less common than
it is for Java or some other languages. If you've kept up with python tooling lately,
you've likely heard of uv.

TODO: uv section

#### Common commands - make

There is also a `Makefile` that bridges the Python and Java build systems together to
make common workflows simple, single commands. The most important commands are:

TODO: make section

To see what targets are available, run `make help` or examine the file directly.

## Security issue notifications

If you discover a potential security issue in this project we ask that you
notify AWS/Amazon Security via our
[vulnerability reporting page](http://aws.amazon.com/security/vulnerability-reporting/).
Please do **not** create a public GitHub issue.

## License

This project is licensed under the Apache-2.0 License.
