package dev.cbc.plugin.model

import java.awt.Color

/**
 * The four terminal verdict states emitted by the CBC orchestrator.
 * Anything we don't recognise is mapped to [UNKNOWN] so the UI keeps working
 * against future orchestrator releases.
 */
enum class Verdict(val display: String, val color: Color) {
    VERIFIED("VERIFIED", Color(0x2E, 0xA0, 0x43)),
    FALSIFIED("FALSIFIED", Color(0xCF, 0x22, 0x2E)),
    TIMED_OUT("TIMED_OUT", Color(0xBF, 0x83, 0x00)),
    UNPROVEN("UNPROVEN", Color(0x8B, 0x94, 0x9E)),
    UNKNOWN("UNKNOWN", Color(0x8B, 0x94, 0x9E));

    companion object {
        fun parse(raw: String?): Verdict = when (raw?.uppercase()) {
            "VERIFIED" -> VERIFIED
            "FALSIFIED" -> FALSIFIED
            "TIMED_OUT", "TIMEOUT" -> TIMED_OUT
            "UNPROVEN" -> UNPROVEN
            else -> UNKNOWN
        }
    }
}
