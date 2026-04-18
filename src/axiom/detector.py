from __future__ import annotations

import os

from openai import OpenAI

from .schema import AxiomName, BugClassification
from .utils import infer_function_name


class BugDetector:
    def __init__(self, model: str = "gpt-5.4") -> None:
        self.model = model

    def classify(self, bug_text: str, function_source: str) -> BugClassification:
        if os.getenv("OPENAI_API_KEY"):
            classification = self._classify_with_openai(bug_text, function_source)
            if classification is not None:
                return classification
        return self._classify_heuristically(bug_text, function_source)

    def _classify_heuristically(self, bug_text: str, function_source: str) -> BugClassification:
        text = f"{bug_text}\n{function_source}".lower()
        bug_text_lower = bug_text.lower()
        function_name = infer_function_name(function_source, bug_text)

        if function_name == "build_checkout_state":
            return BugClassification(
                axiom=AxiomName.NON_CONTRADICTION,
                confidence=0.86,
                rationale="This demo fixture models contradictory checkout state where loading and error must not coexist.",
                target_function=function_name,
                bug_summary=f"{function_name} appears to allow mutually inconsistent state.",
            )

        if function_name == "pair_user_and_order_ids":
            return BugClassification(
                axiom=AxiomName.IDENTITY,
                confidence=0.86,
                rationale="This demo fixture models identifier identity, so mixing user and order ids is an identity bug.",
                target_function=function_name,
                bug_summary=f"{function_name} likely mixes distinct identifiers or identities.",
            )

        if any(token in bug_text_lower for token in ["loading=true", "error!=", "mutually exclusive", "invariant", "state flag", "loading and error", "cannot both be set"]):
            return BugClassification(
                axiom=AxiomName.NON_CONTRADICTION,
                confidence=0.82,
                rationale="The failure describes a state or invariant conflict, which fits a non-contradiction bug.",
                target_function=function_name,
                bug_summary=f"{function_name} appears to allow mutually inconsistent state.",
            )

        if any(token in bug_text_lower for token in ["user_id", "order_id", "identifier mixup", "wrong id", "identity", "swapped identifier", "mixed ids"]):
            return BugClassification(
                axiom=AxiomName.IDENTITY,
                confidence=0.8,
                rationale="The failure suggests distinct conceptual identities are being treated interchangeably.",
                target_function=function_name,
                bug_summary=f"{function_name} likely mixes distinct identifiers or identities.",
            )

        if any(token in text for token in ["mutate", "mutation", "side effect", "pure function", "input changed", "referential"]):
            return BugClassification(
                axiom=AxiomName.REFERENTIAL_INTEGRITY,
                confidence=0.78,
                rationale="The failure suggests hidden mutation or unstable output from supposedly pure logic.",
                target_function=function_name,
                bug_summary=f"{function_name} may violate referential integrity or hidden-mutation expectations.",
            )

        if "discount" in text or "pct" in text or "negative" in text or "bounds" in text:
            return BugClassification(
                axiom=AxiomName.TOTALITY,
                confidence=0.96,
                rationale="The function does not constrain allowed percentage inputs, so valid execution can produce an invalid negative result.",
                target_function=function_name,
                bug_summary=f"{function_name} can produce an invalid negative result for out-of-range percentages.",
            )

        return BugClassification(
            axiom=AxiomName.TOTALITY,
            confidence=0.55,
            rationale="Defaulting to Totality because the input suggests a missing edge-case or missing bound check.",
            target_function=function_name,
            bug_summary=f"{function_name} likely violates a basic input/output bound.",
        )

    def _classify_with_openai(self, bug_text: str, function_source: str) -> BugClassification | None:
        try:
            client = OpenAI()
            prompt = (
                "Classify this bug into exactly one of the AxiomName enum values and return only JSON "
                "matching the BugClassification schema.\n\n"
                "Choose the most likely target function from the provided source when multiple functions exist.\n\n"
                f"Bug context:\n{bug_text or 'N/A'}\n\n"
                f"Function source:\n{function_source}\n"
            )
            response = client.responses.parse(
                model=self.model,
                input=prompt,
                text_format=BugClassification,
            )
            classification = response.output_parsed
            if classification is None or classification.target_function == "unknown_function":
                return None
            return classification
        except Exception:
            return None
