package dev.cbc.plugin.run

import com.intellij.execution.configurations.GeneralCommandLine
import com.intellij.openapi.application.ApplicationManager
import com.intellij.openapi.components.Service
import com.intellij.openapi.diagnostic.Logger
import com.intellij.openapi.project.Project
import dev.cbc.plugin.model.CbcEvent
import dev.cbc.plugin.model.Verdict
import dev.cbc.plugin.settings.CbcSettings
import dev.cbc.plugin.stream.NdjsonParser
import dev.cbc.plugin.verdict.VerdictStore
import java.io.BufferedReader
import java.io.InputStreamReader
import java.nio.charset.StandardCharsets
import java.nio.file.Path
import java.util.concurrent.CopyOnWriteArrayList
import java.util.concurrent.atomic.AtomicReference

/**
 * Runs `cbc solve --stream <prompt> ...` in a background thread and forwards
 * parsed [CbcEvent]s to registered [Listener]s.
 *
 * One run at a time per project: starting a new run cancels the previous one.
 */
@Service(Service.Level.PROJECT)
class CbcRunService(private val project: Project) {
    private val log = Logger.getInstance(CbcRunService::class.java)
    private val current = AtomicReference<Process?>(null)
    private val listeners = CopyOnWriteArrayList<Listener>()

    interface Listener {
        fun onStarted(commandLine: String) {}
        fun onEvent(event: CbcEvent) {}
        fun onStderr(line: String) {}
        fun onFinished(exitCode: Int, finalVerdict: Verdict?) {}
    }

    fun addListener(l: Listener) { listeners.add(l) }
    fun removeListener(l: Listener) { listeners.remove(l) }

    fun isRunning(): Boolean = current.get()?.isAlive == true

    fun cancel() {
        current.getAndSet(null)?.destroyForcibly()
    }

    /**
     * Start a new run. Returns `false` if a previous run is still active; the
     * caller should [cancel] first.
     */
    fun solve(prompt: String): Boolean {
        if (isRunning()) return false
        val settings = CbcSettings.instance()
        val wd = settings.workingDirectory.ifBlank { project.basePath ?: "." }
        val cmd = GeneralCommandLine().apply {
            exePath = settings.executable
            addParameter("solve")
            addParameter(prompt)
            addParameter("--stream")
            settings.extraArgs
                .split(Regex("\\s+"))
                .filter { it.isNotBlank() }
                .forEach { addParameter(it) }
            setWorkDirectory(wd)
            charset = StandardCharsets.UTF_8
        }
        val process = try {
            cmd.createProcess()
        } catch (e: Exception) {
            log.warn("Failed to launch cbc: ${cmd.commandLineString}", e)
            listeners.forEach { it.onStderr("Failed to launch cbc: ${e.message}") }
            listeners.forEach { it.onFinished(-1, null) }
            return false
        }
        current.set(process)
        val commandLineString = cmd.commandLineString
        listeners.forEach { it.onStarted(commandLineString) }

        // stdout: NDJSON parsing loop
        pumpAsync("cbc-stdout-$project") {
            val finalVerdict = AtomicReference<Verdict?>(null)
            BufferedReader(InputStreamReader(process.inputStream, StandardCharsets.UTF_8)).use { reader ->
                reader.lineSequence().forEach { line ->
                    val event = NdjsonParser.parseLine(line) ?: return@forEach
                    if (event.type == "verification.completed" && event.verdict != null) {
                        finalVerdict.set(event.verdict)
                    }
                    applyVerdictSideEffects(event)
                    ApplicationManager.getApplication().invokeLater {
                        listeners.forEach { it.onEvent(event) }
                    }
                }
            }
            val exit = try { process.waitFor() } catch (_: InterruptedException) { -1 }
            current.compareAndSet(process, null)
            ApplicationManager.getApplication().invokeLater {
                listeners.forEach { it.onFinished(exit, finalVerdict.get()) }
            }
        }

        // stderr: drain so the process doesn't block
        pumpAsync("cbc-stderr-$project") {
            BufferedReader(InputStreamReader(process.errorStream, StandardCharsets.UTF_8)).use { reader ->
                reader.lineSequence().forEach { line ->
                    ApplicationManager.getApplication().invokeLater {
                        listeners.forEach { it.onStderr(line) }
                    }
                }
            }
        }
        return true
    }

    /**
     * When a `verification.completed` event carries a changed file list, record
     * the verdict against each file so the gutter provider can render badges.
     */
    private fun applyVerdictSideEffects(event: CbcEvent) {
        val verdict = event.verdict ?: return
        val changed = (event.raw["changed_files"] as? List<*>)
            ?: (event.raw["files"] as? List<*>)
            ?: return
        val store = project.getService(VerdictStore::class.java) ?: return
        val base = project.basePath?.let { Path.of(it) }
        changed.filterIsInstance<String>().forEach { rel ->
            val p = if (base != null) base.resolve(rel) else Path.of(rel)
            store.set(p, verdict)
        }
    }

    private fun pumpAsync(name: String, body: () -> Unit) {
        val t = Thread(body, name)
        t.isDaemon = true
        t.start()
    }
}
