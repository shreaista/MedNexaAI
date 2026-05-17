from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.clinical import ClinicalVisit, VisitNote
from app.models.core import Provider
from app.schemas.clinical import NoteCreatedOut, NoteSignBody, NoteSignedOut, VisitNoteCreate

router = APIRouter(tags=["notes"])


@router.post(
    "/visits/{visit_id}/notes",
    response_model=NoteCreatedOut,
    status_code=status.HTTP_201_CREATED,
)
def create_visit_note(
    visit_id: UUID,
    body: VisitNoteCreate,
    db: Session = Depends(get_db),
) -> NoteCreatedOut:
    visit = db.get(ClinicalVisit, visit_id)
    if visit is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Visit not found")

    if body.tenant_id != visit.tenant_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Tenant mismatch for visit")

    if body.patient_id != visit.patient_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Patient mismatch for visit")

    provider = db.get(Provider, body.provider_id)
    if provider is None or provider.tenant_id != body.tenant_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Invalid provider for tenant")

    # Defaults: NOT_REVIEWED for clinician-authored drafts; flagged when AI-assisted.
    ai_review = "PENDING_AI_REVIEW" if body.ai_generated else "NOT_REVIEWED"

    note = VisitNote(
        tenant_id=body.tenant_id,
        visit_id=visit_id,
        patient_id=body.patient_id,
        provider_id=body.provider_id,
        subjective=body.subjective,
        objective=body.objective,
        assessment=body.assessment,
        plan=body.plan,
        full_note=body.full_note if body.full_note is not None else "",
        ai_generated=body.ai_generated,
        note_status="DRAFT",
        ai_review_status=ai_review,
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return NoteCreatedOut(note_id=note.note_id, note_status=note.note_status)


@router.put("/notes/{note_id}/sign", response_model=NoteSignedOut)
def sign_note(note_id: UUID, body: NoteSignBody, db: Session = Depends(get_db)) -> NoteSignedOut:
    note = db.get(VisitNote, note_id)
    if note is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Note not found")

    if note.note_status.upper() == "SIGNED":
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Note already signed")

    note.note_status = "SIGNED"
    note.signed_at = datetime.now(tz=UTC)
    note.signed_by = body.signed_by
    note.ai_review_status = "HUMAN_REVIEWED"
    db.add(note)
    db.commit()
    db.refresh(note)

    if note.signed_at is None:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Note signing did not persist signed_at.")

    return NoteSignedOut(
        note_id=note.note_id,
        note_status=note.note_status,
        signed_at=note.signed_at,
    )
