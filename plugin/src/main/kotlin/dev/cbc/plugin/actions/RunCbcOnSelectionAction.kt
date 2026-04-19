package dev.cbc.plugin.actions

import com.intellij.openapi.actionSystem.AnAction
import com.intellij.openapi.actionSystem.AnActionEvent
import com.intellij.openapi.actionSystem.CommonDataKeys
import com.intellij.openapi.actionSystem.ActionUpdateThread
import com.intellij.openapi.ui.Messages
import com.intellij.openapi.wm.ToolWindowManager
import dev.cbc.plugin.toolwindow.CbcToolWindowPanel

/**
 * Sends the current editor selection to `cbc solve --stream` via
 * [dev.cbc.plugin.run.CbcRunService] and makes sure the CBC tool window
 * is visible so the user can watch the attempt/check/verdict tree update
 * live.
 *
 * This is the integration surface for AI Assistant / Codex: the user
 * triggers a Codex suggestion, selects the produced code (or the whole file),
 * and runs this action to have CBC verify the suggestion deterministically.
 */
class RunCbcOnSelectionAction : AnAction() {
    override fun getActionUpdateThread(): ActionUpdateThread = ActionUpdateThread.BGT

    override fun update(e: AnActionEvent) {
        val editor = e.getData(CommonDataKeys.EDITOR)
        val hasSelection = editor?.selectionModel?.hasSelection() == true
        e.presentation.isEnabled = e.project != null && (hasSelection || editor != null)
    }

    override fun actionPerformed(e: AnActionEvent) {
        val project = e.project ?: return
        val editor = e.getData(CommonDataKeys.EDITOR)
        val selected = editor?.selectionModel?.selectedText?.takeIf { it.isNotBlank() }
        val prompt = selected?.let { buildPrompt(it) } ?: run {
            Messages.showInfoMessage(
                project,
                "Select some code first — it will be sent to `cbc solve` as the prompt.",
                "CBC",
            )
            return
        }

        val twm = ToolWindowManager.getInstance(project)
        val tw = twm.getToolWindow("CBC")
        tw?.activate(null, true)

        // Find the panel hosted inside the tool window content and delegate.
        val content = tw?.contentManager?.contents?.firstOrNull()
        val panel = content?.component as? javax.swing.JPanel
        val cbcPanel = panel?.let { findPanel(it) }
        if (cbcPanel == null) {
            // Fallback: drive the service directly.
            project.getService(dev.cbc.plugin.run.CbcRunService::class.java).solve(prompt)
        } else {
            cbcPanel.runPrompt(prompt)
        }
    }

    private fun buildPrompt(selection: String): String =
        "Verify and, if needed, fix the following code (produced by AI Assistant / Codex). " +
            "Make tests, lint, and type checks pass without weakening them:\n\n" +
            selection.trim()

    /** Tool-window contents wrap our panel; locate it by type. */
    private fun findPanel(root: java.awt.Container): CbcToolWindowPanel? {
        // Our factory installs a JPanel built by CbcToolWindowPanel.component.
        // The panel object itself isn't a component, so we can't recover it
        // directly — return null and let the caller fall back to the service.
        return null
    }
}
