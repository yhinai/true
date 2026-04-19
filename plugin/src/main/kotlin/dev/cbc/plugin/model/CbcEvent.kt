package dev.cbc.plugin.model

/**
 * A single NDJSON line emitted by `cbc solve --stream` / `cbc run --stream`.
 *
 * The orchestrator emits a flat JSON object with at least a `type` field;
 * additional fields depend on the event. Known event types include:
 *
 * - `adapter.started`          (attempt, candidate_role)
 * - `verification.started`     (attempt, candidate_id?)
 * - `verification.completed`   (attempt, verdict)
 *
 * We keep the raw payload so unknown keys round-trip into the UI.
 */
data class CbcEvent(
    val type: String,
    val attempt: Int?,
    val candidateId: String?,
    val verdict: Verdict?,
    val raw: Map<String, Any?>,
) {
    fun summary(): String {
        val parts = mutableListOf(type)
        attempt?.let { parts += "attempt=$it" }
        candidateId?.let { parts += "candidate=$it" }
        verdict?.let { parts += "verdict=${it.display}" }
        return parts.joinToString(" ")
    }
}
