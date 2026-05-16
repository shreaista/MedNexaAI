from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ClaimReadinessEvaluation:
    readiness_score: float
    readiness_status: str
    missing_note: bool
    missing_diagnosis: bool
    missing_cpt: bool


def evaluate_claim_readiness(
    *,
    has_note: bool,
    has_diagnosis: bool,
    has_procedure: bool,
) -> ClaimReadinessEvaluation:
    """Score visit documentation for downstream claim submission."""
    complete = has_note and has_diagnosis and has_procedure
    score = 80.0 if complete else 50.0
    status = "READY" if score >= 80 else "NEEDS_REVIEW"
    return ClaimReadinessEvaluation(
        readiness_score=score,
        readiness_status=status,
        missing_note=not has_note,
        missing_diagnosis=not has_diagnosis,
        missing_cpt=not has_procedure,
    )
