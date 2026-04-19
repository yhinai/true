<div align="center">

# Correct by Construction

**Verification-first control plane for coding agents.**

[![CI](https://github.com/yhinai/true/actions/workflows/ci.yml/badge.svg)](https://github.com/yhinai/true/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](pyproject.toml)
[![Contract](https://img.shields.io/badge/contract-2026--04--18.v2-green.svg)](src/cbc/headless_contract.py)
[![main: PR-gated](https://img.shields.io/badge/main-PR--gated-brightgreen.svg)](#silent-pr-gated-workflow)
[![tests: 249](https://img.shields.io/badge/tests-249_passing-brightgreen.svg)](#)
[![dashboard live](https://img.shields.io/badge/dashboard-live-blueviolet.svg)](https://supabase-true.vercel.app/)
[![autonomous: yes](https://img.shields.io/badge/remediation-autonomous-orange.svg)](#autonomous-remediation-loop)
[![IntelliJ plugin](https://img.shields.io/badge/JetBrains-plugin-000.svg)](plugin/README.md)
[![demo video](https://img.shields.io/badge/demo-video-red.svg)](https://www.youtube.com/watch?v=OOqca_EjjwQ)

</div>

---

## Live Dashboard & Demo

<table>
<tr>
<td width="50%" valign="top">

### 📺 Watch it run

[![CBC demo video](https://img.youtube.com/vi/OOqca_EjjwQ/maxresdefault.jpg)](https://www.youtube.com/watch?v=OOqca_EjjwQ)

End-to-end walkthrough — task in, verdict out, proof in the ledger.

</td>
<td width="50%" valign="top">

### 🎛️ Command Center

**→ [supabase-true.vercel.app](https://supabase-true.vercel.app/)**

Live mission-telemetry dashboard:

- Pulsing telemetry ticker under the hero
- Thermal-printer **live event tail** (SSE + Supabase realtime)
- Full-bleed **Verdict Reel** of recent runs
- Run gallery, KPI row, remediation feed, check suite
- All hydrated from `cbc_runs` + `cbc_run_events` + `cbc_remediations` Supabase tables

</td>
</tr>
</table>

---

## The Idea

LLMs claim. CBC proves.

```mermaid
flowchart LR
    T(["Task"]) --> C["Coder"]
    C --> S["Staged workspace"]
    S --> V{"Verifier"}
    V -- "all checks pass" --> OK([" VERIFIED "])
    V -- "check fails" --> R{"Route"}
    V -- "budget exceeded" --> TO([" TIMED_OUT "])
    V -- "infra error" --> UN([" UNPROVEN "])
    R -- "budget left" --> C
    R -- "exhausted" --> NO([" FALSIFIED "])

    classDef ok fill:#d4edda,stroke:#155724,color:#000
    classDef bad fill:#f8d7da,stroke:#721c24,color:#000
    classDef maybe fill:#fff3cd,stroke:#856404,color:#000
    class OK ok
    class NO,TO bad
    class UN maybe
```

Every change lands in a **staged workspace** (local copy or ConTree branch). Every claim is checked by an **oracle** — pytest, ruff, typecheck, contracts, hypothesis, mutation. Every outcome is recorded in a reproducible `RunLedger`: snapshot lineage, timings, and the exact prompt the agent received.

---

## Four Verdicts

```mermaid
stateDiagram-v2
    [*] --> Attempt
    Attempt --> VERIFIED: all required checks pass
    Attempt --> FALSIFIED: check fails, retries exhausted
    Attempt --> TIMED_OUT: wall budget exceeded
    Attempt --> UNPROVEN: verification could not run
    FALSIFIED --> Attempt: retry if budget
    TIMED_OUT --> Attempt: retry if budget
    VERIFIED --> [*]
    UNPROVEN --> [*]
```

| | Verdict | Meaning |
|---|---|---|
| ✅ | `VERIFIED`  | All required checks pass |
| ❌ | `FALSIFIED` | At least one required check fails |
| ⏱ | `TIMED_OUT` | Attempt exceeded `--max-seconds-per-attempt` |
| ❓ | `UNPROVEN`  | Verification could not run to completion |

---

## Quickstart

```bash
uv sync --extra dev
./scripts/run_compare.sh
uv run cbc run fixtures/oracle_tasks/calculator_bug/task.yaml --mode treatment --json \
    | jq '.verification.status'
# => "VERIFIED"
```

<details>
<summary><b>What it looks like</b> (interactive TTY)</summary>

```console
$ uv run cbc run fixtures/oracle_tasks/calculator_bug/task.yaml --mode treatment
⠋ Running CBC on calculator_bug...
✅ VERIFIED after 2 attempts (1.2s)

                           Verification Report
┏━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━┓
┃ Check        ┃ Status ┃  Duration ┃
┡━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━┩
│ oracle       │ passed │    0.04s  │
│ ruff         │ passed │    0.11s  │
│ pytest       │ passed │    0.83s  │
│ compileall   │ passed │    0.02s  │
└──────────────┴────────┴───────────┘

Ledger: artifacts/runs/fe59a3a27a2d/run_ledger.json
```

</details>

<details>
<summary><b>Force a timeout</b> (proves <code>TIMED_OUT</code>)</summary>

```console
$ uv run cbc run fixtures/oracle_tasks/calculator_bug/task.yaml \
      --max-seconds-per-attempt 0.001 --json | jq '.verification.status'
"TIMED_OUT"
```

</details>

---

## Architecture

```mermaid
flowchart TB
    subgraph CLI["CLI"]
        Main["main.py<br/>Typer"]
        API["api/<br/>FastAPI"]
    end

    subgraph Control["Controller"]
        Orch["orchestrator.py"]
        State["run_state.py"]
        Ledger["ledger_factory.py"]
        Gearbox["gearbox_runner.py"]
        Score["scoring.py"]
    end

    subgraph Model["Model"]
        Codex["codex_exec.py"]
        Replay["replay.py"]
        Prompts["prompts.py"]
    end

    subgraph WS["Workspace"]
        Local["LocalBackend"]
        Contree["ContreeWorkspace"]
    end

    subgraph Verify["Verify"]
        Core["verify/core.py"]
        Oracle["oracle"]
        Lint["ruff"]
        Types["types"]
        Prop["hypothesis"]
        Contract["contracts"]
    end

    subgraph Store["Storage"]
        DB[("cbc.sqlite3")]
        Runs["artifacts/runs"]
    end

    Main --> Orch
    API --> DB
    Orch --> State
    Orch --> Gearbox
    Orch --> Score
    Orch --> Core
    Orch --> Codex
    Orch --> Replay
    Codex --> Prompts
    Orch --> Local
    Gearbox --> Contree
    Core --> Oracle & Lint & Types & Prop & Contract
    Orch --> Ledger
    Ledger --> Runs
    Orch --> DB

    classDef cli fill:#e3f2fd,stroke:#1976d2
    classDef ctrl fill:#fff3e0,stroke:#f57c00
    classDef mdl fill:#e8f5e9,stroke:#388e3c
    classDef ws fill:#fce4ec,stroke:#c2185b
    classDef vf fill:#fff9c4,stroke:#f9a825
    classDef st fill:#eceff1,stroke:#546e7a
    class Main,API cli
    class Orch,State,Ledger,Gearbox,Score ctrl
    class Codex,Replay,Prompts mdl
    class Local,Contree ws
    class Core,Oracle,Lint,Types,Prop,Contract vf
    class DB,Runs st
```

---

## Sandboxing

```mermaid
flowchart LR
    subgraph Local["--sandbox local (default)"]
        direction TB
        S1["Source workspace"] -->|"shutil.copytree"| T1["tempfile.mkdtemp"]
        T1 --> R1["coder writes<br/>verifier runs"]
    end

    subgraph Contree["--sandbox contree"]
        direction TB
        S2["Source workspace"] -->|"file-walk upload"| Base["Base image"]
        Base -->|"branch_async"| B1["Branch a"]
        Base -->|"branch_async"| B2["Branch b"]
        Base -->|"branch_async"| B3["Branch c"]
        B1 & B2 & B3 -.-> Pick["CheckWeights.select"]
    end

    classDef green fill:#e8f5e9,stroke:#388e3c
    classDef blue fill:#e3f2fd,stroke:#1976d2
    class S1,T1,R1 green
    class S2,Base,B1,B2,B3,Pick blue
```

> Local is always available. ConTree unlocks true parallel gearbox via Git-like branches — siblings can't interfere by construction.

---

## Gearbox: Sequential vs Parallel

```mermaid
gantt
    title Wall-clock, 3 candidates x 5s each (illustrative)
    dateFormat ss
    axisFormat %Ss
    section Sequential
    Candidate 1 :c1, 00, 5s
    Candidate 2 :c2, after c1, 5s
    Candidate 3 :c3, after c2, 5s
    Select      :done, after c3, 1s
    section Parallel (contree)
    Candidate 1 :active, p1, 00, 5s
    Candidate 2 :active, p2, 00, 5s
    Candidate 3 :active, p3, 00, 5s
    Select      :done, p4, 05, 1s
```

Measured by `scripts/bench_gearbox_parallel.py` into `reports/gearbox_speedup.json`.

---

## Autonomous Remediation Loop

A FALSIFIED run no longer sits on the floor. A Supabase trigger enqueues it, a GitHub Actions cron dispatches a Codex YOLO remediation, and the successful PR auto-merges — all without a human in the loop.

```mermaid
flowchart LR
    Run["Baseline run<br/>FALSIFIED / TIMED_OUT"] --> Trig["cbc_runs trigger<br/>enqueues cbc_remediations"]
    Trig --> Cron["cbc-remediate-dispatch.yml<br/>cron every 5 min"]
    Cron --> Reap["reap rows stuck<br/>in running &gt;60min"]
    Cron --> Drain["drain queued rows"]
    Drain --> WF["cbc-remediate.yml<br/>workflow_dispatch"]
    WF --> Codex["cbc run --agent=codex<br/>--allow-dangerous-codex<br/>--controller=gearbox<br/>--retry-budget=10"]
    Codex --> Gate{"VERIFIED?"}
    Gate -- yes --> PR["git commit + push<br/>gh pr create<br/>auto-merge armed"]
    Gate -- no  --> Bail["bailed_budget /<br/>bailed_loop / error"]
    PR --> Main["main"]

    classDef g fill:#e8f5e9,stroke:#388e3c
    classDef y fill:#fff3cd,stroke:#856404
    classDef r fill:#f8d7da,stroke:#721c24
    class Main,PR g
    class Cron,Reap,Drain y
    class Bail r
```

| Piece | Path |
|---|---|
| Enqueue trigger | `migrations/supabase/0002_cbc_remediations.sql` |
| Dispatcher script | `scripts/remediate_dispatcher.py` (drain + reap) |
| Dispatcher cron | `.github/workflows/cbc-remediate-dispatch.yml` (5 min) |
| Remediation runner | `.github/workflows/cbc-remediate.yml` |
| Mirror helper | `scripts/remediate_mirror.py` |

Required secrets: `GEMINI_API_KEY` (primary LLM backend — Flash Lite for conflict resolution, Pro for PR review; `OPENAI_API_KEY` is only needed if `live-codex-nightly.yml` is kept enabled for the `@openai/codex` CLI), `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_ANON_KEY`, `POSTGRES_URL_NON_POOLING`. Branch protection keeps the `test` check required — failures still block merge.

---

## Silent PR-gated Workflow

You keep typing `git push origin main`. The system handles the rest.

```mermaid
sequenceDiagram
    autonumber
    actor Dev
    participant Hook as pre-push
    participant GH as GitHub
    participant CI
    participant Main as main

    Dev->>Hook: git push origin main
    Hook->>GH: create pr-auto branch + push
    Hook->>GH: open PR
    Hook->>GH: gh pr merge --auto --squash
    Hook-->>Dev: PR opened, auto-merge armed
    GH->>CI: run tests + refresh snapshots
    CI-->>GH: test passed
    GH->>Main: squash-merge
    Main-->>Dev: landed (no action)
```

```mermaid
flowchart LR
    P["git push main"] --> H["pre-push hook"]
    H --> PR["PR opened"]
    PR --> Gate{"test = pass"}
    Gate -- "yes" --> M["main"]
    Gate -- "no"  --> Re["ci-retry reruns once"]
    Re --> Gate

    classDef g fill:#e8f5e9,stroke:#388e3c
    classDef y fill:#fff3cd,stroke:#856404
    class M,H,PR g
    class Gate,Re y
```

### One-time setup per clone

```bash
ln -sf ../../scripts/git-hooks/pre-push .git/hooks/pre-push
uv tool install pre-commit && uv tool run pre-commit install
```

<details>
<summary><b>Emergency override</b></summary>

```bash
ALLOW_DIRECT_MAIN_PUSH=1 git push origin main
```

Branch protection on the server still rejects unless temporarily disabled.
</details>

---

## Standing Instructions (program.md)

```mermaid
flowchart LR
    A["program.md<br/>repo root"] --> M(("merge"))
    B["task program.md<br/>overrides"] --> M
    M --> I["inject into<br/>coder prompt"]
    I --> L["RunLedger.program_text"]

    classDef d fill:#e3f2fd,stroke:#1976d2
    classDef o fill:#fff3e0,stroke:#f57c00
    classDef out fill:#e8f5e9,stroke:#388e3c
    class A,B d
    class M,I o
    class L out
```

```bash
echo "Prefer defensive coding. Use type hints." > program.md
uv run cbc run fixtures/oracle_tasks/calculator_bug/task.yaml --mode treatment
jq '.program_text' artifacts/runs/*/run_ledger.json | tail -1
```

---

## Install

| Need | Command |
|---|---|
| Minimum | `uv sync --extra dev` |
| + charts | `uv sync --extra dev --extra charts` |
| + ConTree | `uv sync --extra dev --extra contree` |

Python 3.11+ and [uv](https://docs.astral.sh/uv/).

---

## CLI

<details open>
<summary><b><code>cbc run &lt;task.yaml&gt;</code></b></summary>

| Flag | Default | Purpose |
|---|---|---|
| `--mode {baseline,treatment,review}` | `treatment` | Execution mode |
| `--controller {sequential,gearbox}` | `sequential` | Candidate strategy |
| `--sandbox {local,contree}` | `local` | Workspace isolation |
| `--workspace-in-place PATH` | — | Edit a caller-supplied tree in place (mutually exclusive with `--sandbox`); used by the remediation workflow against `$GITHUB_WORKSPACE`. |
| `--agent {codex,replay}` | per task.yaml | Model adapter |
| `--allow-dangerous-codex` | off | Honor `dangerously_bypass_approvals` / `sandbox=danger-full-access` from task YAML. Gated because it disables Codex sandbox. |
| `--max-seconds-per-attempt` | none | Wall-clock budget per attempt |
| `--json` | off | Machine-readable stdout |
| `--stream` | off | NDJSON lifecycle events |

```bash
uv run cbc run <task.yaml> --mode treatment
uv run cbc run <task.yaml> --controller gearbox --sandbox contree --json
uv run cbc run <task.yaml> --max-seconds-per-attempt 60
```

</details>

<details>
<summary><b><code>cbc solve &lt;prompt&gt;</code></b> (zero-config intake)</summary>

```bash
uv run cbc solve "Add a /health endpoint that returns 200"
uv run cbc solve "Fix the Node status badge labels" --verify "node test_status.js" --json
```

</details>

<details>
<summary><b>Benchmarks</b></summary>

```bash
./scripts/run_compare.sh
./scripts/run_expanded_compare.sh
./scripts/run_controller_compare.sh
./scripts/run_poc_compare.sh --simulated --sample-size 2 --seed 42 --repetitions 2
python3 scripts/bench_gearbox_parallel.py
```

</details>

<details>
<summary><b>Review &amp; CI gates</b></summary>

```bash
uv run cbc review-workspace <task.yaml> /path/to/workspace
uv run cbc ci <task.yaml> /path/to/workspace
uv run cbc review-artifact <ledger.json> --json
uv run cbc ci-artifact <ledger.json> --json
```

</details>

<details>
<summary><b><code>cbc api</code></b></summary>

```bash
uv run cbc api
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/runs
curl http://127.0.0.1:8000/benchmarks
```

</details>

---

## Repository Map

```
src/cbc/
├── main.py                  CLI entry (Typer)
├── api/                     FastAPI read surface + Supabase mirror
│   ├── app.py               bearer auth + CORS allowlist
│   ├── routes.py            /health /runs /runs/{id}/mirror /benchmarks
│   ├── streams.py           SSE tail of run_ledger.json
│   ├── store.py             artifact reader (narrow except + logging)
│   └── supabase_writer.py   mirror run + fan events into cbc_run_events
├── controller/
│   ├── orchestrator.py      run_task (sequential + gearbox)
│   ├── run_state.py         RunState, IterationRecord, AttemptTimeout
│   ├── routing.py           RETRY | COMPLETE | ABORT
│   ├── ledger_factory.py    build_final_ledger
│   ├── gearbox_runner.py    asyncio.gather
│   └── scoring.py           tunable CheckWeights
├── model/
│   ├── codex_exec.py        streaming subprocess, sandbox gate
│   ├── replay.py            deterministic replay
│   └── prompts.py           program.md injection
├── prompts/program_loader.py
├── roles/                   coder, planner, explorer, reviewer
├── verify/
│   ├── core.py              parallel ThreadPoolExecutor
│   ├── env_utils.py         scrub_env (drops SUPABASE_*/OPENAI_*/…)
│   └── *_runner.py          shell=False + shlex.split across all runners
├── workspace/
│   ├── backends.py          LocalBackend / InPlaceBackend / SandboxMode
│   ├── contree_adapter.py   ContreeWorkspace
│   └── staging.py           create_workspace_lease
└── storage/
    ├── db.py                SQLite (WAL + busy_timeout)
    ├── runs.py              SQLite index
    └── candidate_lineage.py candidate_snapshots

web/                         Next.js 16 command center
├── app/
│   ├── page.tsx             Hero + Runs + Events + Remediation + Pipeline
│   ├── runs/[id]/           live run detail with SSE + Supabase fallback
│   ├── components/          RunGallery, EventTail, RemediationFeed, …
│   └── globals.css          mission telemetry theme
└── lib/                     supabase.ts, api.ts, useSSE hook

plugin/                      JetBrains plugin (tool window + gutter badges)
├── build.gradle.kts
└── src/main/kotlin/dev/cbc/plugin/

migrations/supabase/
├── 0001_cbc_ledger.sql      cbc_runs + cbc_run_events
└── 0002_cbc_remediations.sql cbc_remediations + enqueue trigger

scripts/
├── remediate_dispatcher.py  drain + reap queue → workflow_dispatch
├── remediate_mirror.py      mirror a completed run ledger
└── bench_gearbox_parallel.py
```

---

## JetBrains Plugin

An IntelliJ-platform plugin (`plugin/`) brings CBC into the editor.

- **CBC tool window** streams `cbc solve --stream` NDJSON events into a live Attempt → Check → Verdict tree.
- **Gutter badges** paint VERIFIED / FALSIFIED / TIMED_OUT / UNPROVEN next to files changed by the latest run.
- **Run CBC on Selection** (`⌃⌥V`) sends editor selection to `cbc solve` and renders the verdict. Plays well with AI Assistant / Codex so CBC is the "verify" button on any suggestion.

```bash
cd plugin
./gradlew buildPlugin          # → build/distributions/cbc-plugin-0.1.0.zip
./gradlew runIde               # sandbox IDE with the plugin loaded
```

Install into your main IDE by unzipping the artifact into `~/Library/Application Support/JetBrains/<IDE-version>/plugins/`.

---

## Supabase Schema

The control plane ships three tables (migrations in `migrations/supabase/`):

| Table | Rows on production | Purpose |
|---|---|---|
| `cbc_runs` | 77 (verified+falsified) | Mirror of every completed `RunLedger` |
| `cbc_run_events` | 1,528 | `run_started` / `attempt_started` / `check_result` / `attempt_verdict` / `run_verdict` |
| `cbc_remediations` | live queue | FALSIFIED/TIMED_OUT rows enqueued by trigger; drained by cron dispatcher |

All three are members of the `supabase_realtime` publication so the dashboard streams inserts live. The `cbc_runs_enqueue_remediation` trigger on `cbc_runs` fires on `verdict IN ('FALSIFIED','TIMED_OUT')` and upserts a queued remediation row with the task path resolved from convention (`fixtures/oracle_tasks/<task_id>/task.yaml`) or the `cbc_tasks` mapping table.

---

## Outputs

| Path | Content |
|---|---|
| `artifacts/runs/<run_id>/` | per-run ledger, transcript, verification report |
| `artifacts/examples/` | checked-in reference runs (CI-gated) |
| `artifacts/cbc.sqlite3` | runs + candidate_snapshots |
| `reports/benchmarks/<id>/` | benchmark comparisons |
| `reports/gearbox_speedup.json` | sequential vs parallel wall-time |

---

## Verification Sweep

```bash
uv run pytest -q
./scripts/run_compare.sh
./scripts/run_expanded_compare.sh
./scripts/run_controller_compare.sh
./scripts/run_poc_compare.sh --simulated --sample-size 2 --seed 42 --repetitions 2
uv run python3 scripts/refresh_examples.py
python3 -m compileall src tests scripts
```

---

## Status

- Headless contract frozen at `2026-04-18.v2`
- CLI, FastAPI, artifacts, benchmark reports — all live
- Replay + live Codex adapters, both reproducible
- Sequential + gearbox controllers; parallel gearbox under ConTree
- Zero-config intake via `cbc solve`
- `main` is PR-gated with silent auto-merge
- **249 tests passing**; fast suite ~10s
- **Live dashboard** at [supabase-true.vercel.app](https://supabase-true.vercel.app/) (Next.js 16 + Supabase)
- **Autonomous remediation loop**: FALSIFIED runs trigger → Codex YOLO → PR → auto-merge
- **JetBrains plugin** ships the tool window, gutter badges, and "Run CBC on Selection"
- Supabase ledger mirror: `cbc_runs`, `cbc_run_events`, `cbc_remediations` (+ enqueue trigger)

---

## Docs

[Demo](docs/DEMO.md) · [Spec](docs/SPEC.md) · [Runbook](docs/RUNBOOK.md) · [Benchmark Plan](docs/BENCHMARK_PLAN.md) · [Status](docs/STATUS.md) · [Roadmap](plan.md) · [AGENTS.md](AGENTS.md) · [CLAUDE.md](CLAUDE.md) · [specs/](docs/superpowers/specs/) · [plans/](docs/superpowers/plans/)
