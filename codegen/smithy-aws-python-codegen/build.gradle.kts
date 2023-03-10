/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */

description = "Generates AWS Python code from Smithy models"
extra["displayName"] = "Smithy :: AWS :: Python :: Codegen"
extra["moduleName"] = "software.amazon.smithy.aws.python.codegen"

val smithyVersion: String by project

buildscript {
    val smithyVersion: String by project

    repositories {
        mavenLocal()
        mavenCentral()
    }
    dependencies {
        "classpath"("software.amazon.smithy:smithy-cli:$smithyVersion")
    }
}

dependencies {
    implementation(project(":smithy-python-codegen"))
    implementation("software.amazon.smithy:smithy-aws-traits:$smithyVersion")
}
