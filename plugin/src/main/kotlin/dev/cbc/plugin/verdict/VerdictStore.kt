package dev.cbc.plugin.verdict

import com.intellij.openapi.components.Service
import com.intellij.openapi.project.Project
import com.intellij.openapi.vfs.LocalFileSystem
import com.intellij.openapi.vfs.VirtualFile
import dev.cbc.plugin.model.Verdict
import java.nio.file.Path
import java.util.concurrent.ConcurrentHashMap

/**
 * Remembers the latest CBC [Verdict] for the files touched by each run, so the
 * gutter line-marker provider can render a badge on the first line of each
 * changed file.
 *
 * Keyed by absolute file path. Setting a verdict for a path refreshes all line
 * markers via [com.intellij.codeInsight.daemon.DaemonCodeAnalyzer].
 */
@Service(Service.Level.PROJECT)
class VerdictStore(private val project: Project) {
    private val verdicts = ConcurrentHashMap<String, Verdict>()

    fun set(path: Path, verdict: Verdict) {
        verdicts[path.toAbsolutePath().toString()] = verdict
        refresh(path)
    }

    fun clear() {
        val paths = verdicts.keys.toList()
        verdicts.clear()
        paths.forEach { refresh(Path.of(it)) }
    }

    fun get(file: VirtualFile): Verdict? = verdicts[file.path]

    private fun refresh(path: Path) {
        val vf = LocalFileSystem.getInstance().findFileByNioFile(path) ?: return
        com.intellij.openapi.application.ApplicationManager.getApplication().invokeLater {
            com.intellij.codeInsight.daemon.DaemonCodeAnalyzer.getInstance(project).restart()
            @Suppress("UNUSED_EXPRESSION") vf
        }
    }
}
