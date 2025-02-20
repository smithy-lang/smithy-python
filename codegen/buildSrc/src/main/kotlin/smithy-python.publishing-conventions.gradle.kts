import org.gradle.api.publish.maven.MavenPublication
import org.gradle.kotlin.dsl.extra
import org.gradle.kotlin.dsl.provideDelegate

plugins {
    `maven-publish`
    signing
}

/*
 * Staging repository
 * ====================================================
 *
 * Configure publication to staging repo
 */
publishing {
    repositories {
        maven {
            name = "stagingRepository"
            url = rootProject.layout.buildDirectory.dir("staging").get().asFile.toURI()
        }
    }
    // Add license spec to all maven publications
    publications {
        afterEvaluate {
            create<MavenPublication>("mavenJava") {
                from(components["java"])

                val displayName: String by extra
                pom {
                    name.set(displayName)
                    description.set(project.description)
                    url.set("https://github.com/smithy-lang/smithy-python")
                    licenses {
                        license {
                            name.set("Apache License 2.0")
                            url.set("http://www.apache.org/licenses/LICENSE-2.0.txt")
                            distribution.set("repo")
                        }
                    }
                    developers {
                        developer {
                            id.set("smithy")
                            name.set("Smithy")
                            organization.set("Amazon Web Services")
                            organizationUrl.set("https://aws.amazon.com")
                            roles.add("developer")
                        }
                    }
                    scm {
                        url.set("https://github.com/smithy-lang/smithy-python.git")
                    }
                }
            }
        }
    }
}

signing {
    setRequired {
        // signing is required only if the artifacts are to be published to a maven repository
        gradle.taskGraph.allTasks.any { it is PublishToMavenRepository }
    }

    // Don't sign the artifacts if we didn't get a key and password to use.
    if (project.hasProperty("signingKey") && project.hasProperty("signingPassword")) {
        signing {
            useInMemoryPgpKeys(
                project.properties["signingKey"].toString(),
                project.properties["signingPassword"].toString())
            sign(publishing.publications)
        }
    }
}
