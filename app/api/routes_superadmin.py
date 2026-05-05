from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import require_role
from app.db.database import get_db
from app.models.auth import User
from app.models.models import Event, Photo

router = APIRouter(prefix="/api/superadmin", tags=["superadmin"])


@router.get("/stats")
def get_stats(
    db: Session = Depends(get_db),
    _=Depends(require_role("SUPERADMIN")),
):
    photos = db.query(Photo).filter(Photo.processed == True).count()
    events = db.query(Event).count()
    users = db.query(User).count()
    return {"photos": photos, "events": events, "users": users}
