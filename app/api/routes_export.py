"""Routes for CSV exports and ZIP pack downloads."""
import io

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.dependencies import require_module
from app.db.database import get_db
from app.services.export_service import (
    export_photo_count_csv,
    export_photos_per_bib_csv,
    generate_bib_pack_zip,
)

router = APIRouter(prefix="/api/events/{event_id}/export", tags=["Export"])
_tri_user = require_module("TRI")


@router.get("/photos-per-bib")
def export_photos_per_bib(
    event_id: int,
    db: Session = Depends(get_db),
    _=Depends(_tri_user),
):
    """Export CSV: one line per photo (dossard, nom, prenom, photo)."""
    csv_content = export_photos_per_bib_csv(db, event_id)
    return StreamingResponse(
        io.StringIO(csv_content),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=photos_par_dossard_{event_id}.csv"},
    )


@router.get("/photo-count")
def export_photo_count(
    event_id: int,
    db: Session = Depends(get_db),
    _=Depends(_tri_user),
):
    """Export CSV: one line per bib (dossard, nom, prenom, nombre_photos)."""
    csv_content = export_photo_count_csv(db, event_id)
    return StreamingResponse(
        io.StringIO(csv_content),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=nombre_photos_{event_id}.csv"},
    )


@router.get("/pack/{bib_number}")
def download_pack(
    event_id: int,
    bib_number: str,
    db: Session = Depends(get_db),
    _=Depends(_tri_user),
):
    """Download a ZIP pack with all photos for a bib number."""
    zip_bytes = generate_bib_pack_zip(db, event_id, bib_number)
    if zip_bytes is None:
        raise HTTPException(status_code=404, detail=f"Aucune photo pour le dossard {bib_number}")

    return StreamingResponse(
        io.BytesIO(zip_bytes),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=pack_{bib_number}.zip"},
    )
