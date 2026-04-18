from __future__ import annotations

from axiom.agent import AxiomAgent
from axiom.pipeline import PipelineInput


class RecordingPipeline:
    def __init__(self) -> None:
        self.inputs: list[PipelineInput] = []

    def run_and_render(self, pipeline_input: PipelineInput, force_unproven: bool = False) -> str:
        self.inputs.append(pipeline_input)
        return "ledger"


def test_agent_routes_pasted_failing_test_as_context_only() -> None:
    pipeline = RecordingPipeline()
    agent = AxiomAgent()
    agent.pipeline = pipeline
    prompt = """
```python
def apply_discount(price: float, pct: int) -> float:
    return price * (100 - pct) / 100
```

```text
def test_apply_discount_rejects_percentages_above_100():
    with pytest.raises(ValueError):
        apply_discount(100, 150)
```
"""
    assert agent._handle_prompt(prompt) == "ledger"
    assert len(pipeline.inputs) == 1
    assert pipeline.inputs[0].run_tests is False
    assert "pytest.raises" in (pipeline.inputs[0].bug_text or "")


def test_agent_returns_clear_error_for_ambiguous_path_mode() -> None:
    agent = AxiomAgent()
    response = agent._handle_prompt("bug=/tmp/source.py\nstacktrace=/tmp/trace.txt\n")
    assert "only supports" in response
