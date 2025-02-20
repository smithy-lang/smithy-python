import org.gradle.api.DefaultTask
import org.gradle.api.provider.Property
import org.gradle.api.tasks.Input
import org.gradle.api.tasks.TaskAction
import org.gradle.api.tasks.options.Option
import org.gradle.kotlin.dsl.invoke
import org.gradle.kotlin.dsl.register

tasks {
    register<SizeAnalysisTask>("analyzeSize") {
        group = "reporting"
        description = "Analyzes the size of a configuration (default: 'runtimeClasspath')"
    }
}

/**
 * A task for analyzing the size of artifacts (most likely the runtime JAR).
 * Very useful for seeing the size of dependencies being brought in.
 */
abstract class SizeAnalysisTask : DefaultTask() {
    @get:Input
    @get:Option(
        option = "configuration",
        description = "The project configuration to analyze (default: 'runtimeClasspath')")
    abstract val configuration: Property<String>

    init {
        configuration.convention("runtimeClasspath")
    }

    @TaskAction
    fun analyze() {
        val selectedConfig = project.configurations.getByName(configuration.get())

        println("\n📦 Dependency Size Analysis: '${selectedConfig.name}'")
        println("═".repeat(65))

        selectedConfig
            .sortedByDescending { it.length() }
            .forEach { dep ->
                val size = when {
                    dep.length() >= 1_048_576 -> "%.2f MB".format(dep.length() / 1_048_576.0)
                    dep.length() >= 1024 -> "%.2f KB".format(dep.length() / 1024.0)
                    else -> "${dep.length()} B"
                }
                println("  *  ${dep.name.take(48).padEnd(48)} │ $size")
            }

        val totalMb = selectedConfig.sumOf { it.length() } / 1_048_576.0
        println("─".repeat(65))
        println("""🏷️ Total size: %.2f MB""".format(totalMb))
    }
}
