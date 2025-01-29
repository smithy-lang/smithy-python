plugins {
    id("smithy-python.module-conventions")
    id("smithy-python.publishing-conventions")
}

description = "This module provides Python code generation plugins for Smithy"
group = "software.amazon.smithy.python.codegen"

extra["displayName"] = "Smithy :: Python :: Codegen :: Plugins"
extra["moduleName"] = "software.amazon.smithy.python.codegen.plugins"

dependencies {
    subprojects.forEach { api(project(it.path)) }
}
