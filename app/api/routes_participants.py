"""Routes for participant management (Excel import, list, RGPD delete)."""
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.dependencies import require_module
from app.db.database import get_db
from app.models.participant import Participant
from app.schemas.participant import ParticipantImportResult, ParticipantOut
from app.services.participant_service import import_participants_from_excel
from app.services.rgpd_service import delete_bib_photos

router = APIRouter(prefix="/api/events/{event_id}/participants", tags=["Participants"])
_tri_user = require_module("TRI")


@router.post("/import", response_model=ParticipantImportResult)
async def import_participants(
    event_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _=Depends(_tri_user),
):
    """Import participants from an Excel file (.xlsx)."""
    if not file.filename or not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Format invalide. Utilisez un fichier .xlsx")

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:  # 10MB limit
        raise HTTPException(status_code=400, detail="Fichier trop volumineux (max 10 Mo)")

    result = import_participants_from_excel(db, event_id, content)
    return result


@router.get("", response_model=list[ParticipantOut])
def list_participants(
    event_id: int,
    db: Session = Depends(get_db),
    _=Depends(_tri_user),
):
    """List all participants for an event."""
    return (
        db.query(Participant)
        .filter(Participant.event_id == event_id)
        .order_by(Participant.bib_number)
        .all()
    )


@router.delete("/rgpd/{bib_number}")
def rgpd_delete(
    event_id: int,
    bib_number: str,
    db: Session = Depends(get_db),
    _=Depends(_tri_user),
):
    """RGPD: delete all photos for a bib number (web + files)."""
    result = delete_bib_photos(db, event_id, bib_number, delete_files=True)
    if result["detections_removed"] == 0 and result["web_photos_removed"] == 0:
        raise HTTPException(status_code=404, detail=f"Aucune photo trouvee pour le dossard {bib_number}")
    return result
