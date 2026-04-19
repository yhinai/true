package dev.cbc.plugin.stream

import com.google.gson.Gson
import com.google.gson.reflect.TypeToken
import dev.cbc.plugin.model.CbcEvent
import dev.cbc.plugin.model.Verdict

/**
 * Parses a single NDJSON line emitted by `cbc ... --stream` into a [CbcEvent].
 *
 * The parser is lenient: malformed / empty lines yield `null` instead of throwing,
 * and unknown fields are preserved in [CbcEvent.raw] so the tool window can
 * still show them verbatim.
 */
object NdjsonParser {
    private val gson = Gson()
    private val mapType = object : TypeToken<Map<String, Any?>>() {}.type

    fun parseLine(line: String): CbcEvent? {
        val trimmed = line.trim()
        if (trimmed.isEmpty() || !trimmed.startsWith("{")) return null
        val raw: Map<String, Any?> = try {
            gson.fromJson(trimmed, mapType) ?: return null
        } catch (_: Exception) {
            return null
        }
        val type = raw["type"]?.toString() ?: return null
        val attempt = (raw["attempt"] as? Number)?.toInt()
        val candidateId = raw["candidate_id"]?.toString() ?: raw["candidate_role"]?.toString()
        val verdict = raw["verdict"]?.toString()?.let { Verdict.parse(it) }
        return CbcEvent(
            type = type,
            attempt = attempt,
            candidateId = candidateId,
            verdict = verdict,
            raw = raw,
        )
    }
}
