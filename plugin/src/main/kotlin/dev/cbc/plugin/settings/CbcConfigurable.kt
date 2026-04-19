package dev.cbc.plugin.settings

import com.intellij.openapi.options.Configurable
import com.intellij.ui.components.JBTextField
import com.intellij.util.ui.FormBuilder
import javax.swing.JComponent
import javax.swing.JPanel

/**
 * `Settings → Tools → CBC` panel.
 */
class CbcConfigurable : Configurable {
    private val executableField = JBTextField()
    private val extraArgsField = JBTextField()
    private val workingDirField = JBTextField()
    private var panel: JPanel? = null

    override fun getDisplayName(): String = "CBC"

    override fun createComponent(): JComponent {
        val settings = CbcSettings.instance()
        executableField.text = settings.executable
        extraArgsField.text = settings.extraArgs
        workingDirField.text = settings.workingDirectory
        val p = FormBuilder.createFormBuilder()
            .addLabeledComponent("cbc executable:", executableField, 1, false)
            .addLabeledComponent("Extra arguments:", extraArgsField, 1, false)
            .addLabeledComponent("Working directory (empty = project root):", workingDirField, 1, false)
            .addComponentFillVertically(JPanel(), 0)
            .panel
        panel = p
        return p
    }

    override fun isModified(): Boolean {
        val s = CbcSettings.instance()
        return executableField.text != s.executable ||
            extraArgsField.text != s.extraArgs ||
            workingDirField.text != s.workingDirectory
    }

    override fun apply() {
        val s = CbcSettings.instance()
        s.executable = executableField.text.ifBlank { "cbc" }
        s.extraArgs = extraArgsField.text
        s.workingDirectory = workingDirField.text
    }

    override fun reset() {
        val s = CbcSettings.instance()
        executableField.text = s.executable
        extraArgsField.text = s.extraArgs
        workingDirField.text = s.workingDirectory
    }

    override fun disposeUIResources() {
        panel = null
    }
}
