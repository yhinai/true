package dev.cbc.plugin.settings

import com.intellij.openapi.application.ApplicationManager
import com.intellij.openapi.components.PersistentStateComponent
import com.intellij.openapi.components.Service
import com.intellij.openapi.components.State
import com.intellij.openapi.components.Storage
import com.intellij.util.xmlb.XmlSerializerUtil

/**
 * Persisted plugin settings. Exposed via `Settings → Tools → CBC`.
 */
@Service(Service.Level.APP)
@State(name = "CbcSettings", storages = [Storage("cbc.xml")])
class CbcSettings : PersistentStateComponent<CbcSettings.State> {
    data class State(
        var executable: String = "cbc",
        var extraArgs: String = "--controller gearbox --agent codex",
        var workingDirectory: String = "",
    )

    private var state = State()

    override fun getState(): State = state

    override fun loadState(value: State) {
        XmlSerializerUtil.copyBean(value, state)
    }

    var executable: String
        get() = state.executable
        set(value) { state.executable = value }

    var extraArgs: String
        get() = state.extraArgs
        set(value) { state.extraArgs = value }

    var workingDirectory: String
        get() = state.workingDirectory
        set(value) { state.workingDirectory = value }

    companion object {
        fun instance(): CbcSettings =
            ApplicationManager.getApplication().getService(CbcSettings::class.java)
    }
}
