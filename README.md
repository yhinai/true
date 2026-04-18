# Axiom

Codex generates. Axiom proves.

Axiom is a Python-first ACP agent with a mandatory CLI fallback. It takes a failing test, stacktrace, or bug report, proposes a minimal patch, derives `icontract` contracts, runs CrossHair, and returns an Evidence Ledger with one honest status:

- `VERIFIED`
- `FALSIFIED`
- `UNPROVEN`

## Golden path

The primary demo bug is a Totality violation in `demo_repo/checkout/discount.py`. The original implementation can return a negative result when `pct > 100`. Axiom patches that function by adding explicit bounds checks, generates simple contracts, verifies them with CrossHair, and runs the planted pytest.

Optional secondary demo bugs are also present:

- `demo_repo/checkout/order.py` includes a Non-Contradiction example where loading and error can coexist.
- `demo_repo/checkout/fulfillment.py` includes an Identity example where user and order identifiers are mixed.

Track: Testing & Debugging Code

## Setup

```bash
python3 -m venv .venv
./.venv/bin/python -m ensurepip --upgrade
./.venv/bin/python -m pip install -e .
```

## Commands

```bash
make test
make verify-crosshair
make demo
make demo-falsified
make demo-unproven
make demo-non-contradiction
make demo-identity
make verify-acp
PYTHONPATH=src ./.venv/bin/python scripts/smoke_openai.py
```

## CLI usage

Mode 1: failing test + function file

```bash
PYTHONPATH=src ./.venv/bin/python -m axiom.cli \
  --bug demo_repo/checkout/discount.py \
  --test demo_repo/tests/test_discount.py
```

Mode 2: stacktrace + function file

```bash
PYTHONPATH=src ./.venv/bin/python -m axiom.cli \
  --stacktrace path/to/stacktrace.txt \
  --function demo_repo/checkout/discount.py
```

Optional mode 3: bug report + function file

```bash
PYTHONPATH=src ./.venv/bin/python -m axiom.cli \
  --bug-report path/to/bug_report.txt \
  --function demo_repo/checkout/discount.py
```

Use `--force-unproven` to demo the honest timeout/unproven path without changing the bug.
Use `--verify-original` to verify the original buggy source and render a `FALSIFIED` ledger with a concrete counterexample.

Optional secondary demo commands:

```bash
make demo-non-contradiction
make demo-identity
```

Equivalent direct CLI commands:

```bash
PYTHONPATH=src ./.venv/bin/python -m axiom.cli \
  --bug demo_repo/checkout/order.py \
  --test demo_repo/tests/test_checkout_state.py

PYTHONPATH=src ./.venv/bin/python -m axiom.cli \
  --bug demo_repo/checkout/fulfillment.py \
  --test demo_repo/tests/test_identity.py
```

## ACP usage

`src/axiom/agent.py` provides a minimal ACP stdio agent. In JetBrains AI Chat, use `Add Custom Agent`, then paste the checked-in [acp.json](/Users/alhinai/Desktop/TRUE/acp.json:1) contents into `/Users/alhinai/.jetbrains/acp.json`. After that, send either file-path syntax or pasted bug context.

Path-driven fallback:

```text
bug=/absolute/path/to/demo_repo/checkout/discount.py
test=/absolute/path/to/demo_repo/tests/test_discount.py
```

Other supported path-driven combinations:

```text
function=/absolute/path/to/demo_repo/checkout/discount.py
stacktrace=/absolute/path/to/stacktrace.txt
```

```text
function=/absolute/path/to/demo_repo/checkout/discount.py
bug_report=/absolute/path/to/bug_report.txt
```

Pasted-text flow:

````text
```python
def apply_discount(price: float, pct: int) -> float:
    return price * (100 - pct) / 100
```

```text
Traceback (most recent call last):
AssertionError: discount should not go negative for pct > 100
```
````

See [docs/ACP_VALIDATION.md](/Users/alhinai/Desktop/TRUE/docs/ACP_VALIDATION.md:1) for the validation checklist and [docs/CLOSEOUT_CHECKLIST.md](/Users/alhinai/Desktop/TRUE/docs/CLOSEOUT_CHECKLIST.md:1) for remaining closeout gates.

## Limitations

- JetBrains ACP validation still requires a manual IDE run.
- Live OpenAI validation requires a real `OPENAI_API_KEY`.
- The detector and patcher are still intentionally narrow and optimized for the demo fixtures first.
- The project targets Python `3.12+` as declared in [pyproject.toml](/Users/alhinai/Desktop/TRUE/pyproject.toml:1).
- Pasted ACP tests and stacktraces are used as analysis context; runnable pytest execution still requires a file-backed `--test` path or `bug=...` + `test=...`.
