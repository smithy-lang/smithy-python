plugins {
    id("smithy-python.module-conventions")
    id("smithy-python.integ-test-conventions")
}

description = "This module provides the core codegen functionality for Smithy Python"
group = "software.amazon.smithy.python.codegen"

extra["displayName"] = "Smithy :: Python :: Codegen"
extra["moduleName"] = "software.amazon.smithy.python.codegen"

dependencies {
    api(libs.smithy.codegen)
    implementation(libs.smithy.waiters)
    implementation(libs.smithy.protocol.test.traits)
    // We have this because we're using RestJson1 as a 'generic' protocol.
    implementation(libs.smithy.aws.traits)
}
