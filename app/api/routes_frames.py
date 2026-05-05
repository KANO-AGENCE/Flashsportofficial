"""Routes for frame management and framed pack generation."""
import io
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.dependencies import require_module
from app.db.database import get_db
from app.models.frame import Frame
from app.models.participant import Participant
from app.schemas.frame import FrameCreate, FrameOut, FrameUpdate
from app.services.export_service import get_bib_photos
from app.services.frame_service import apply_frame_to_photo
from config import settings

router = APIRouter(prefix="/api/events/{event_id}/frames", tags=["Frames"])
_tri_user = require_module("TRI")


@router.get("", response_model=list[FrameOut])
def list_frames(
    event_id: int,
    db: Session = Depends(get_db),
    _=Depends(_tri_user),
):
    return db.query(Frame).filter(Frame.event_id == event_id).all()


@router.post("", response_model=FrameOut)
async def create_frame(
    event_id: int,
    file: UploadFile = File(...),
    name: str = "Cadre",
    text_x: float = 0.5,
    text_y: float = 0.9,
    text_size: int = 48,
    text_color: str = "#FFFFFF",
    db: Session = Depends(get_db),
    _=Depends(_tri_user),
):
    """Upload a frame image and create frame config."""
    allowed_types = {"image/png", "image/webp"}
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Le cadre doit etre un PNG ou WebP (avec transparence)")

    # Save frame image
    frames_dir = Path(settings.upload_dir) / "frames" / str(event_id)
    frames_dir.mkdir(parents=True, exist_ok=True)

    safe_name = file.filename.replace("/", "_").replace("\\", "_") if file.filename else "frame.png"
    dest = frames_dir / safe_name
    content = await file.read()
    dest.write_bytes(content)

    frame = Frame(
        event_id=event_id,
        name=name,
        image_path=str(dest),
        text_x=text_x,
        text_y=text_y,
        text_size=text_size,
        text_color=text_color,
    )
    db.add(frame)
    db.commit()
    db.refresh(frame)
    return frame


@router.put("/{frame_id}", response_model=FrameOut)
def update_frame(
    event_id: int,
    frame_id: int,
    data: FrameUpdate,
    db: Session = Depends(get_db),
    _=Depends(_tri_user),
):
    frame = db.query(Frame).filter(Frame.id == frame_id, Frame.event_id == event_id).first()
    if not frame:
        raise HTTPException(status_code=404, detail="Cadre introuvable")

    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(frame, key, val)

    db.commit()
    db.refresh(frame)
    return frame


@router.delete("/{frame_id}")
def delete_frame(
    event_id: int,
    frame_id: int,
    db: Session = Depends(get_db),
    _=Depends(_tri_user),
):
    frame = db.query(Frame).filter(Frame.id == frame_id, Frame.event_id == event_id).first()
    if not frame:
        raise HTTPException(status_code=404, detail="Cadre introuvable")

    # Delete file
    path = Path(frame.image_path)
    if path.exists():
        path.unlink()

    db.delete(frame)
    db.commit()
    return {"ok": True}


@router.post("/{frame_id}/generate-pack/{bib_number}")
def generate_framed_pack(
    event_id: int,
    frame_id: int,
    bib_number: str,
    db: Session = Depends(get_db),
    _=Depends(_tri_user),
):
    """Generate a ZIP pack with frame overlay for all photos of a bib."""
    frame = db.query(Frame).filter(Frame.id == frame_id, Frame.event_id == event_id).first()
    if not frame:
        raise HTTPException(status_code=404, detail="Cadre introuvable")

    bib_photos = get_bib_photos(db, event_id)
    photos = bib_photos.get(bib_number)
    if not photos:
        raise HTTPException(status_code=404, detail=f"Aucune photo pour le dossard {bib_number}")

    # Get race time from participants
    participant = (
        db.query(Participant)
        .filter(Participant.event_id == event_id, Participant.bib_number == bib_number)
        .first()
    )
    race_time = participant.race_time if participant else None

    buffer = io.BytesIO()
    with TemporaryDirectory() as tmpdir:
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for photo in photos:
                src = Path(photo.filepath)
                if not src.exists():
                    continue
                out_path = Path(tmpdir) / photo.filename
                ok = apply_frame_to_photo(
                    photo_path=str(src),
                    frame_path=frame.image_path,
                    output_path=str(out_path),
                    race_time=race_time,
                    text_x=frame.text_x,
                    text_y=frame.text_y,
                    text_size=frame.text_size,
                    text_color=frame.text_color,
                )
                if ok:
                    zf.write(out_path, f"pack_cadre_{bib_number}/{photo.filename}")

    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=pack_cadre_{bib_number}.zip"},
    )
