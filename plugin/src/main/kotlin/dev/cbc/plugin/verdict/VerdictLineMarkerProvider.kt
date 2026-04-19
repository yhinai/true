package dev.cbc.plugin.verdict

import com.intellij.codeInsight.daemon.LineMarkerInfo
import com.intellij.codeInsight.daemon.LineMarkerProvider
import com.intellij.openapi.editor.markup.GutterIconRenderer
import com.intellij.openapi.project.Project
import com.intellij.openapi.util.IconLoader
import com.intellij.openapi.util.TextRange
import com.intellij.psi.PsiElement
import com.intellij.psi.PsiFile
import com.intellij.ui.JBColor
import dev.cbc.plugin.model.Verdict
import java.awt.Color
import java.awt.Component
import java.awt.Graphics
import java.awt.Graphics2D
import java.awt.RenderingHints
import javax.swing.Icon

/**
 * Places a colored CBC verdict badge in the left gutter of the very first
 * PSI leaf of a file whenever that file has a verdict recorded by
 * [VerdictStore].
 */
class VerdictLineMarkerProvider : LineMarkerProvider {
    override fun getLineMarkerInfo(element: PsiElement): LineMarkerInfo<*>? {
        // Only attach one marker per file — anchor to the first leaf we see.
        val file: PsiFile = element.containingFile ?: return null
        if (element.textRange?.startOffset != 0) return null
        if (element.firstChild != null) return null
        val vf = file.virtualFile ?: return null
        val project: Project = file.project
        val store = project.getService(VerdictStore::class.java) ?: return null
        val verdict = store.get(vf) ?: return null
        return LineMarkerInfo(
            element,
            TextRange(element.textRange.startOffset, element.textRange.startOffset),
            VerdictIcon(verdict),
            { "CBC verdict: ${verdict.display}" },
            null,
            GutterIconRenderer.Alignment.LEFT,
        ) { "CBC: ${verdict.display}" }
    }
}

/** Small rounded badge rendered at gutter size. */
private class VerdictIcon(private val verdict: Verdict) : Icon {
    override fun paintIcon(c: Component?, g: Graphics, x: Int, y: Int) {
        val g2 = g.create() as Graphics2D
        try {
            g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON)
            g2.color = JBColor(verdict.color, verdict.color.darker())
            g2.fillRoundRect(x, y + 2, iconWidth, iconHeight - 4, 6, 6)
            g2.color = Color.WHITE
            g2.drawString(verdict.display.first().toString(), x + 3, y + iconHeight - 4)
        } finally {
            g2.dispose()
        }
    }

    override fun getIconWidth(): Int = 12
    override fun getIconHeight(): Int = 14
}
