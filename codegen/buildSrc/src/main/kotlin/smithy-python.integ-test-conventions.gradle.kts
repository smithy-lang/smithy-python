configure<SourceSetContainer> {
    val main by getting
    val test by getting
    create("it") {
        compileClasspath += main.output + configurations["testRuntimeClasspath"] + configurations["testCompileClasspath"]
        runtimeClasspath += output + compileClasspath + test.runtimeClasspath + test.output
    }
}

// Add the integ test task
tasks.register<Test>("integ") {
    useJUnitPlatform()
    testClassesDirs = project.the<SourceSetContainer>()["it"].output.classesDirs
    classpath = project.the<SourceSetContainer>()["it"].runtimeClasspath
}

// Run integ tests when testing, can be disabled once more testing is added, and we want to separate them.
tasks["test"].finalizedBy("integ")
