from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ClaimReadinessEvaluation:
    readiness_score: float
    readiness_status: str
    missing_note_flag: bool
    missing_diagnosis_flag: bool
    missing_cpt_flag: bool
    documentation_support_status: str
    recommendation: str


def evaluate_charge_workflow(
    *,
    has_signed_note: bool,
    has_any_note: bool,
    has_diagnosis: bool,
    has_procedure: bool,
) -> ClaimReadinessEvaluation:
    """
    Scoring (Phase 1B):
    - 100: signed note + at least one diagnosis + at least one procedure.
    - 80: any note present but not signed, and diagnosis + procedure both present.
    - 50: otherwise (missing documentation pieces / unsigned incomplete paths).
    READY when score >= 90, else NEEDS_REVIEW.
    """
    missing_diagnosis = not has_diagnosis
    missing_cpt = not has_procedure
    missing_note_flag = not has_any_note

    if has_signed_note and has_diagnosis and has_procedure:
        score = 100.0
    elif has_any_note and (not has_signed_note) and has_diagnosis and has_procedure:
        score = 80.0
    else:
        score = 50.0

    status = "READY" if score >= 90.0 else "NEEDS_REVIEW"

    if has_signed_note:
        doc_status = "SUPPORTED"
    else:
        doc_status = "NEEDS_REVIEW"

    recommendation = _build_recommendation(
        has_signed_note=has_signed_note,
        has_any_note=has_any_note,
        has_diagnosis=has_diagnosis,
        has_procedure=has_procedure,
    )

    return ClaimReadinessEvaluation(
        readiness_score=score,
        readiness_status=status,
        missing_note_flag=missing_note_flag,
        missing_diagnosis_flag=missing_diagnosis,
        missing_cpt_flag=missing_cpt,
        documentation_support_status=doc_status,
        recommendation=recommendation,
    )


def _build_recommendation(
    *,
    has_signed_note: bool,
    has_any_note: bool,
    has_diagnosis: bool,
    has_procedure: bool,
) -> str:
    parts: list[str] = []
    if not has_any_note:
        parts.append("Create a visit note to support billing.")
    elif not has_signed_note:
        parts.append("Sign the visit note to achieve supported documentation.")
    if not has_diagnosis:
        parts.append("Add at least one ICD-10 diagnosis.")
    if not has_procedure:
        parts.append("Add at least one CPT procedure / service line.")
    if not parts:
        return "Documentation appears complete for claim routing."
    return " ".join(parts)
