plugins {
    id("smithy-python.module-conventions")
    id("smithy-python.integ-test-conventions")
}

description = "This module provides the core aws codegen functionality for Smithy Python"
group = "software.amazon.smithy.python.codegen.aws"

extra["displayName"] = "Smithy :: Python :: AWS :: Codegen"
extra["moduleName"] = "software.amazon.smithy.python.aws.codegen"

dependencies {
    implementation(project(":core"))
    implementation(libs.smithy.aws.traits)
    implementation("org.jsoup:jsoup:1.19.1")
}
