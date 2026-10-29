plugins {
    java
    alias(libs.plugins.smithy.gradle.base)
}

repositories {
    mavenLocal()
    mavenCentral()
}

smithy {
    smithyBuildConfigs.set(files(providers.gradleProperty("smithyBuildConfig").get()))
}

val smithyVersion = libs.versions.smithy.asProvider().get()

dependencies {
    // Resolved to the included codegen build's :core and :aws:core projects.
    smithyBuild("software.amazon.smithy.python.codegen:core:0.0.0")
    smithyBuild("software.amazon.smithy.python.codegen.aws:core:0.0.0")

    smithyBuild("software.amazon.smithy:smithy-aws-traits:$smithyVersion")
    smithyBuild("software.amazon.smithy:smithy-aws-iam-traits:$smithyVersion")
    smithyBuild("software.amazon.smithy:smithy-aws-cloudformation-traits:$smithyVersion")
    smithyBuild("software.amazon.smithy:smithy-aws-endpoints:$smithyVersion")
    smithyBuild("software.amazon.smithy:smithy-rules-engine:$smithyVersion")
    smithyBuild("software.amazon.smithy:smithy-protocol-traits:$smithyVersion")
    smithyBuild("software.amazon.smithy:smithy-waiters:$smithyVersion")
    smithyBuild("software.amazon.smithy:smithy-smoke-test-traits:$smithyVersion")
    // Defines aws.test#AwsVendorParams, referenced by service smokeTests traits.
    smithyBuild("software.amazon.smithy:smithy-aws-smoke-test-model:$smithyVersion")
}
