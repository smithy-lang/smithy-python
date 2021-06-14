## Smithy Python

**WARNING: All interfaces are subject to change.**

We are in the very early stages of beginning work on low-level Python SDK
modules that aim to provide basic, reusable, and composable interfaces for
lower level SDK tasks. Using these modules customers should be able to generate
synchronous and asynchronous service client or server implementations based on
services defined using [Smithy](https://awslabs.github.io/smithy/).

### What is this repository?

This repository contains two major components:

1) Smithy code generators for Python
2) Core modules and interfaces for building service clients in Python

### Smithy Code Generators

[Smithy](https://awslabs.github.io/smithy/) is a protocol-agnostic interface
definition language that provides a
[code generation framework](https://github.com/awslabs/smithy/tree/main/smithy-codegen-core)
for building service clients, servers, and documentation. The `codegen` directory
contains the source code for generating these tools. See the code generation
[README](https://github.com/awslabs/smithy-python/blob/develop/codegen/README.md)
for more information.

### Core Modules and Interfacse

The `smithy-python` package provides the core modules and interfaces required
to build a service client or server. These basic modules include things like:
an HTTP/1.1 and HTTP/2 client implementation, a generic middleware
implementation, etc.

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

## License

This project is licensed under the Apache-2.0 License.
