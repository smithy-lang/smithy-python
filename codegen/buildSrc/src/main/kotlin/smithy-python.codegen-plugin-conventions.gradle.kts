import org.gradle.api.Project

plugins {
    id("smithy-python.module-conventions")
    id("smithy-python.integ-test-conventions")
}

// Workaround per: https://github.com/gradle/gradle/issues/15383
val Project.libs get() = the<org.gradle.accessors.dm.LibrariesForLibs>()

group = "software.amazon.smithy.python.codegen.plugins"

dependencies {
    implementation(libs.smithy.codegen)
    implementation(project(":core"))

    // Avoid circular dependency in codegen core
    if (project.name != "core") {
        api(project(":core"))
    }
}

val generatedSrcDir = layout.buildDirectory.dir("generated-src").get()

// Add generated sources to integration test sources
sourceSets {
    named("it") {
        java {
            srcDir(generatedSrcDir)
        }
    }
}

// Ensure integ tests are executed as part of test suite
tasks["test"].finalizedBy("integ")
