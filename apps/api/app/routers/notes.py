from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.clinical import Visit, VisitNote
from app.schemas.clinical import NoteSignRequest, VisitNoteCreate, VisitNoteOut

router = APIRouter(tags=["notes"])


@router.post(
    "/visits/{visit_id}/notes",
    response_model=VisitNoteOut,
    status_code=status.HTTP_201_CREATED,
)
def create_visit_note(
    visit_id: UUID,
    body: VisitNoteCreate,
    db: Session = Depends(get_db),
) -> VisitNote:
    visit = db.get(Visit, visit_id)
    if visit is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Visit not found")

    note = VisitNote(
        tenant_id=visit.tenant_id,
        visit_id=visit_id,
        subjective=body.subjective,
        objective=body.objective,
        assessment=body.assessment,
        plan=body.plan,
        full_note=body.full_note or "",
        ai_generated=body.ai_generated,
        note_status="DRAFT",
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


@router.put("/notes/{note_id}/sign", response_model=VisitNoteOut)
def sign_note(
    note_id: UUID,
    body: NoteSignRequest,
    db: Session = Depends(get_db),
) -> VisitNote:
    note = db.get(VisitNote, note_id)
    if note is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Note not found")

    if note.note_status.upper() == "SIGNED":
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail="Note is already signed",
        )

    note.note_status = "SIGNED"
    note.signed_at = datetime.now(tz=UTC)
    note.signed_by = body.signed_by
    db.add(note)
    db.commit()
    db.refresh(note)
    return note
