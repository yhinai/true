# ACP Validation

## Goal

Prove that Axiom works end-to-end inside JetBrains AI Chat.

## Manual validation script

1. Open a JetBrains IDE with AI Assistant enabled.
2. Load this repo.
3. Open `Add Custom Agent`, then copy [acp.json](/Users/alhinai/Desktop/TRUE/acp.json:1) into `/Users/alhinai/.jetbrains/acp.json`.
4. Confirm `Axiom` appears in the agent picker.
5. Select `Axiom`.
6. Send one path-driven prompt and one pasted-text prompt.
7. Confirm a full Evidence Ledger is returned.
8. Capture screenshots of:
   - picker
   - selected agent
   - returned ledger

## Suggested prompts

Path-driven:

```text
bug=/absolute/path/to/demo_repo/checkout/discount.py
test=/absolute/path/to/demo_repo/tests/test_discount.py
```

Pasted-text:

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

## Record here after validation

## Fill-In Template

- IDE version:
  - Example: `PyCharm 2026.1`
- AI Assistant version:
  - Example: `AI Assistant plugin 2026.1.x`
- Date validated:
  - Example: `2026-04-18`
- Agent appeared in picker:
  - `Yes / No`
- Path-driven prompt succeeded:
  - `Yes / No`
- Pasted-text prompt succeeded:
  - `Yes / No`
- Final result:
  - `READY / PARTIAL / FAILED`
- Screenshots:
  - picker:
  - selected agent:
  - returned ledger:
- Quirks / workarounds:
  - Example: `Needed to restart AI Assistant after registering acp.json`
- Notes:

## Minimal Reply To Send Back

If you want me to finish this file for you after the IDE run, send exactly this information:

```text
IDE version:
AI Assistant version:
Date:
Agent appeared in picker: Yes/No
Path-driven prompt worked: Yes/No
Pasted-text prompt worked: Yes/No
Screenshots:
- picker:
- selected agent:
- returned ledger:
Quirks/workarounds:
Notes:
```
