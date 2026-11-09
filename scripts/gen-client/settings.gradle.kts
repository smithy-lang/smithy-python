rootProject.name = "gen-client"

// Substitutes this checkout's codegen for the published jars, so no mavenLocal publish is needed.
includeBuild("../../codegen")

dependencyResolutionManagement {
    versionCatalogs {
        create("libs") {
            from(files("../../codegen/gradle/libs.versions.toml"))
        }
    }
}
