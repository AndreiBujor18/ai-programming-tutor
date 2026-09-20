from __future__ import annotations

from pathlib import Path

from ai_programming_tutor.catalog import get_exercise
from ai_programming_tutor.diagnosis import diagnose
from ai_programming_tutor.hints import get_hint
from ai_programming_tutor.models import DiagnosisCandidate, TutorResponse
from ai_programming_tutor.runner import CRunner
from ai_programming_tutor.solutions import cpp_features


class TutorService:
    def __init__(self, runner: CRunner | None = None, model_path: Path | None = None) -> None:
        self.runner = runner or CRunner()
        self.model_bundle = None
        if model_path is not None:
            from ai_programming_tutor.baseline import load_model

            self.model_bundle = load_model(model_path)

    def submit(
        self, exercise_id: str, source: str, hint_level: int = 1, *, dialect: str = "c17"
    ) -> TutorResponse:
        if hint_level not in {1, 2, 3}:
            raise ValueError("Hint level must be 1, 2, or 3.")
        if dialect not in {"c17", "cpp17"}:
            raise ValueError("Dialect must be c17 or cpp17.")
        exercise = get_exercise(exercise_id)
        evaluation = self.runner.evaluate(source, exercise, dialect=dialect)
        # The 13-category classifier was trained on C17; it is not validated on C++.
        if dialect == "cpp17":
            candidates = () if evaluation.all_passed else (
                DiagnosisCandidate(
                    category="compilation_error" if not evaluation.compilation.succeeded else "unknown",
                    confidence=0.0,
                    evidence=(
                        "C++ submissions have compiler and test feedback only; "
                        "the C bug classifier is not validated here."
                    ),
                ),
            )
        else:
            candidates = diagnose(source, evaluation)
        if (
            dialect == "c17"
            and self.model_bundle is not None
            and evaluation.compilation.succeeded
            and not evaluation.all_passed
        ):
            from ai_programming_tutor.baseline import predict_candidates

            candidates = _merge_candidates(
                predict_candidates(self.model_bundle, source, evaluation), candidates
            )
        hint = get_hint(candidates[0].category, hint_level) if candidates else None
        features = cpp_features(source)
        warning = None
        if features:
            warning = (
                "This submission uses C++ features (" + ", ".join(features)
                + "). The current PCLP1 prototype is intentionally limited to classic C17; "
                "C++ syntax is outside this version's personalization scope."
            )
        return TutorResponse(evaluation, candidates, hint_level, hint, dialect, warning)


def _merge_candidates(
    ml_candidates: tuple[DiagnosisCandidate, ...],
    rule_candidates: tuple[DiagnosisCandidate, ...],
) -> tuple[DiagnosisCandidate, ...]:
    """Combine model probabilities with transparent rule evidence."""
    ml_by_label = {candidate.category: candidate for candidate in ml_candidates}
    rules_by_label = {candidate.category: candidate for candidate in rule_candidates}
    labels = set(ml_by_label) | set(rules_by_label)
    merged = []
    for label in labels:
        ml = ml_by_label.get(label)
        rule = rules_by_label.get(label)
        score = 0.68 * (ml.confidence if ml else 0.0) + 0.32 * (rule.confidence if rule else 0.0)
        evidence_parts = []
        if ml:
            evidence_parts.append(ml.evidence)
        if rule:
            evidence_parts.append(rule.evidence)
        merged.append(
            DiagnosisCandidate(
                category=label, confidence=round(score, 4), evidence=" ".join(evidence_parts)
            )
        )
    return tuple(sorted(merged, key=lambda candidate: candidate.confidence, reverse=True)[:3])
