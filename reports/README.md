# Reports

This directory stores checked-in scaffold outputs for the local benchmark harness.

Generated artifacts currently include:

- fixture smoke summaries for the baseline and treatment configs
- per-task verification JSON and proof-card markdown files
- a compare report that checks the two configs against the same curated subset

The current scripts only verify the fixtures and reference solutions. They do not
yet invoke a Codex adapter or score live agent runs.
