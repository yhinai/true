package dev.cbc.plugin.toolwindow

import com.intellij.openapi.project.Project
import com.intellij.openapi.ui.Messages
import com.intellij.ui.JBColor
import com.intellij.ui.components.JBScrollPane
import com.intellij.ui.treeStructure.Tree
import com.intellij.util.ui.JBUI
import dev.cbc.plugin.model.CbcEvent
import dev.cbc.plugin.model.Verdict
import dev.cbc.plugin.run.CbcRunService
import dev.cbc.plugin.verdict.VerdictStore
import java.awt.BorderLayout
import java.awt.Component
import java.awt.FlowLayout
import javax.swing.JButton
import javax.swing.JLabel
import javax.swing.JPanel
import javax.swing.JTree
import javax.swing.SwingConstants
import javax.swing.tree.DefaultMutableTreeNode
import javax.swing.tree.DefaultTreeCellRenderer
import javax.swing.tree.DefaultTreeModel

/**
 * Swing panel hosted inside the `CBC` tool window.
 *
 * Shows a live tree populated from NDJSON events emitted by
 * `cbc solve --stream`. Structure:
 *
 * ```
 * Run (commandLine)
 *  ├ Attempt 1
 *  │  ├ adapter.started candidate=primary
 *  │  ├ verification.started
 *  │  └ verification.completed verdict=FALSIFIED
 *  └ Attempt 2
 *     └ …
 * ```
 */
class CbcToolWindowPanel(private val project: Project) : CbcRunService.Listener {
    private val rootNode = DefaultMutableTreeNode("CBC — idle")
    private val treeModel = DefaultTreeModel(rootNode)
    private val tree = Tree(treeModel).apply {
        isRootVisible = true
        cellRenderer = VerdictAwareRenderer()
    }
    private val statusLabel = JLabel("Idle", SwingConstants.LEFT).apply {
        border = JBUI.Borders.empty(4, 8)
    }
    private val runButton = JButton("Run prompt…").apply {
        addActionListener { promptAndRun() }
    }
    private val cancelButton = JButton("Cancel").apply {
        isEnabled = false
        addActionListener {
            project.getService(CbcRunService::class.java).cancel()
        }
    }
    private val clearButton = JButton("Clear").apply {
        addActionListener { reset("CBC — idle") }
    }

    private val attemptNodes = mutableMapOf<Int, DefaultMutableTreeNode>()

    val component: JPanel = JPanel(BorderLayout()).apply {
        val toolbar = JPanel(FlowLayout(FlowLayout.LEFT, 4, 4)).apply {
            add(runButton)
            add(cancelButton)
            add(clearButton)
        }
        add(toolbar, BorderLayout.NORTH)
        add(JBScrollPane(tree), BorderLayout.CENTER)
        add(statusLabel, BorderLayout.SOUTH)
    }

    init {
        project.getService(CbcRunService::class.java).addListener(this)
    }

    // ---- Listener ----

    override fun onStarted(commandLine: String) {
        reset("Running: $commandLine")
        rootNode.userObject = "CBC — running"
        treeModel.nodeChanged(rootNode)
        runButton.isEnabled = false
        cancelButton.isEnabled = true
        statusLabel.text = "Running…"
        statusLabel.foreground = JBColor.foreground()
    }

    override fun onEvent(event: CbcEvent) {
        val parent = event.attempt?.let { attemptNode(it) } ?: rootNode
        val child = DefaultMutableTreeNode(EventRow(event))
        parent.add(child)
        treeModel.reload(parent)
        expandAll()
    }

    override fun onStderr(line: String) {
        // Surface stderr in the status label without spamming the tree.
        statusLabel.text = line.take(200)
        statusLabel.foreground = JBColor.GRAY
    }

    override fun onFinished(exitCode: Int, finalVerdict: Verdict?) {
        runButton.isEnabled = true
        cancelButton.isEnabled = false
        val label = if (finalVerdict != null) {
            "Finished · verdict=${finalVerdict.display} · exit=$exitCode"
        } else {
            "Finished · exit=$exitCode"
        }
        statusLabel.text = label
        statusLabel.foreground = finalVerdict?.color ?: JBColor.foreground()
        rootNode.userObject = "CBC — $label"
        treeModel.nodeChanged(rootNode)
    }

    // ---- Helpers ----

    private fun attemptNode(attempt: Int): DefaultMutableTreeNode =
        attemptNodes.getOrPut(attempt) {
            val node = DefaultMutableTreeNode("Attempt $attempt")
            rootNode.add(node)
            treeModel.reload(rootNode)
            node
        }

    private fun reset(rootLabel: String) {
        attemptNodes.clear()
        rootNode.removeAllChildren()
        rootNode.userObject = rootLabel
        treeModel.reload(rootNode)
        project.getService(VerdictStore::class.java).clear()
    }

    private fun expandAll() {
        var i = 0
        while (i < tree.rowCount) {
            tree.expandRow(i)
            i++
        }
    }

    private fun promptAndRun() {
        val prompt = Messages.showInputDialog(
            project,
            "Prompt for `cbc solve`:",
            "Run CBC",
            Messages.getQuestionIcon(),
        ) ?: return
        if (prompt.isBlank()) return
        runPrompt(prompt)
    }

    /** Entry point used by [dev.cbc.plugin.actions.RunCbcOnSelectionAction]. */
    fun runPrompt(prompt: String) {
        val service = project.getService(CbcRunService::class.java)
        if (service.isRunning()) {
            Messages.showWarningDialog(project, "A CBC run is already in progress.", "CBC")
            return
        }
        service.solve(prompt)
    }

    private data class EventRow(val event: CbcEvent) {
        override fun toString(): String = event.summary()
    }

    private class VerdictAwareRenderer : DefaultTreeCellRenderer() {
        override fun getTreeCellRendererComponent(
            tree: JTree?, value: Any?, sel: Boolean, expanded: Boolean,
            leaf: Boolean, row: Int, hasFocus: Boolean,
        ): Component {
            val c = super.getTreeCellRendererComponent(tree, value, sel, expanded, leaf, row, hasFocus)
            val eventRow = (value as? DefaultMutableTreeNode)?.userObject as? EventRow
            val verdict = eventRow?.event?.verdict
            if (verdict != null && !sel) {
                foreground = verdict.color
            }
            return c
        }
    }
}
