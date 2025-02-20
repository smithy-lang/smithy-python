import com.github.spotbugs.snom.Effort
import java.util.regex.Pattern
import org.gradle.api.Project
import org.gradle.kotlin.dsl.the

plugins {
    `java-library`
    id("com.adarshr.test-logger")
    id("com.github.spotbugs")
    id("com.diffplug.spotless")
}

// Workaround per: https://github.com/gradle/gradle/issues/15383
val Project.libs get() = the<org.gradle.accessors.dm.LibrariesForLibs>()

java {
    toolchain {
        languageVersion = JavaLanguageVersion.of(17)
    }
}

tasks.withType<JavaCompile>() {
    options.encoding = "UTF-8"
}

tasks.withType<Javadoc>() {
    options.encoding = "UTF-8"
}

/*
 * Common test configuration
 * ===============================
 */
dependencies {
    testImplementation(platform(libs.junit.bom))
    testImplementation(libs.junit.jupiter.api)
    testRuntimeOnly(libs.junit.jupiter.engine)
    testImplementation(libs.junit.jupiter.params)
    compileOnly("com.github.spotbugs:spotbugs-annotations:${spotbugs.toolVersion.get()}")
    testCompileOnly("com.github.spotbugs:spotbugs-annotations:${spotbugs.toolVersion.get()}")
}

tasks.withType<Test> {
    useJUnitPlatform()
}

testlogger {
    showExceptions = true
    showStackTraces = true
    showFullStackTraces = false
    showCauses = true
    showSummary = false
    showPassed = false
    showSkipped = false
    showFailed = true
    showOnlySlow = false
    showStandardStreams = true
    showPassedStandardStreams = false
    showSkippedStandardStreams = false
    showFailedStandardStreams = true
    logLevel = LogLevel.WARN
}

/*
 * Formatting
 * ==================
 * see: https://github.com/diffplug/spotless/blob/main/plugin-gradle/README.md#java
 */
spotless {
    java {
        // Enforce a common license header on all files
        licenseHeaderFile("${project.rootDir}/config/spotless/license-header.txt")
            .onlyIfContentMatches("^((?!SKIPLICENSECHECK)[\\s\\S])*\$")
        indentWithSpaces()
        endWithNewline()

        eclipse().configFile("${project.rootDir}/config/spotless/formatting.xml")

        // Fixes for some strange formatting applied by eclipse:
        // see: https://github.com/kamkie/demo-spring-jsf/blob/bcacb9dc90273a5f8d2569470c5bf67b171c7d62/build.gradle.kts#L159
        custom("Lambda fix") { it.replace("} )", "})").replace("} ,", "},") }
        custom("Long literal fix") { Pattern.compile("([0-9_]+) [Ll]").matcher(it).replaceAll("\$1L") }

        // Static first, then everything else alphabetically
        removeUnusedImports()
        importOrder("\\#", "")

        // Ignore generated generated code for formatter check
        targetExclude("**/build/**/*.*")
    }

    // Formatting for build.gradle.kts files
    kotlinGradle {
        ktlint()
        indentWithSpaces()
        trimTrailingWhitespace()
        endWithNewline()
    }
}

/*
 * Spotbugs
 * ====================================================
 *
 * Run spotbugs against source files and configure suppressions.
 */
// Configure the spotbugs extension.
spotbugs {
    effort = Effort.MAX
    excludeFilter = file("${project.rootDir}/config/spotbugs/filter.xml")
}

// We don't need to lint tests.
tasks.named("spotbugsTest") {
    enabled = false
}

tasks {
    spotlessCheck {
        dependsOn(tasks.spotlessApply)
    }
}

/*
 * Repositories
 * ================================
 */
repositories {
    mavenLocal()
    mavenCentral()
}
