/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License").
 * You may not use this file except in compliance with the License.
 * A copy of the License is located at
 *
 *  http://aws.amazon.com/apache2.0
 *
 * or in the "license" file accompanying this file. This file is distributed
 * on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
 * express or implied. See the License for the specific language governing
 * permissions and limitations under the License.
 */

description = "Smithy framework errors for Smithy Java"
extra["displayName"] = "Smithy :: Python :: Protocol :: Test"
extra["moduleName"] = "software.amazon.smithy.python.protocol.test"

// TODO: Create a smithy-python protocol convention plugin once we have a better idea of what it looks like
plugins {
    java
    alias(libs.plugins.smithy.gradle.base)
}

repositories {
    mavenLocal()
    mavenCentral()
}

dependencies {
    implementation(project(":core"))
    implementation(libs.smithy.aws.protocol.tests)
}
