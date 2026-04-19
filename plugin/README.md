# CBC IntelliJ Plugin

A JetBrains IDE plugin that surfaces [Correct by Construction (CBC)](../README.md)
verdicts directly inside IntelliJ-based IDEs.

## Features

- **CBC tool window** — streams `cbc solve --stream` NDJSON lifecycle events
  into a live `Attempt → Check → Verdict` tree.
- **Gutter verdict badges** — on files touched by the latest run, each changed
  file shows a colored `VERIFIED / FALSIFIED / TIMED_OUT / UNPROVEN` badge
  next to the top of the file.
- **Run CBC on selection** action — right-click selected code (or use
  `Tools → CBC → Run CBC on selection`) to send the selection as a prompt to
  `cbc solve`. When the built-in AI Assistant / Codex agent is active, the
  plugin forwards the same prompt so CBC acts as the "verify" button for any
  Codex suggestion.

## Requirements

- IntelliJ-based IDE 2024.2+ (IDEA, PyCharm, WebStorm, …)
- `cbc` CLI on `PATH` (`uv pip install -e .` at the repo root, or `uv run cbc`)
- Optional: AI Assistant plugin with Codex enabled

## Build

```bash
cd plugin
./gradlew buildPlugin          # → build/distributions/cbc-plugin-*.zip
./gradlew runIde               # launches a sandbox IDE with the plugin loaded
```

## Configuration

`Settings → Tools → CBC`:

- **`cbc` executable** — defaults to `cbc`. Set to `uv` (with working dir
  pointing at the repo) if you run via `uv run cbc`.
- **Extra arguments** — e.g. `--controller gearbox --agent codex`.
- **Working directory** — defaults to the currently open project root.

## Stream protocol

The plugin consumes the NDJSON stream emitted by `cbc solve --stream` /
`cbc run --stream`. Each line is a JSON object with at minimum:

```json
{"type": "verification.started", "attempt": 1, "candidate_id": "primary"}
{"type": "verification.completed", "attempt": 1, "verdict": "FALSIFIED"}
{"type": "adapter.started", "attempt": 2, "candidate_role": "primary"}
```

Unknown event types are displayed verbatim so the plugin stays forward
compatible with new orchestrator events.
