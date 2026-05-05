"""Routes for the mailing module: CRUD mailings, preview, segment."""
from datetime import datetime

from html import escape as html_escape

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.dependencies import require_module
from app.db.database import get_db
from app.models.mailing import Mailing
from app.models.models import Event
from app.models.web import Customer, Order

router = APIRouter(prefix="/api/mailing", tags=["mailing"])

_mailing_user = require_module("MAILING")


# --- Schemas ---

class MailingCreate(BaseModel):
    subject: str
    raw_content: str = ""
    event_id: int | None = None


class MailingUpdate(BaseModel):
    subject: str | None = None
    raw_content: str | None = None
    event_id: int | None = None
    status: str | None = None


class MailingOut(BaseModel):
    id: int
    subject: str
    raw_content: str | None
    html_content: str | None
    event_id: int | None
    event_name: str | None = None
    status: str
    sent_count: int
    sent_at: datetime | None
    created_at: datetime | None
    updated_at: datetime | None
    recipient_count: int = 0


# --- Helpers ---

def _generate_html(subject: str, raw_content: str) -> str:
    """Generate basic HTML email from raw content. Placeholder for future AI generation."""
    paragraphs = raw_content.strip().split("\n\n") if raw_content else []
    body_html = "".join(f"<p style='margin:0 0 16px;color:#333;font-size:16px;line-height:1.6'>{html_escape(p).replace(chr(10), '<br>')}</p>" for p in paragraphs)
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#f5f5f0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif">
<div style="max-width:600px;margin:0 auto;background:#ffffff;border-radius:12px;overflow:hidden;margin-top:20px;margin-bottom:20px">
  <div style="background:linear-gradient(135deg,#1a2332,#2d3748);padding:30px;text-align:center">
    <h1 style="margin:0;color:#f5a623;font-size:24px">FlashSport</h1>
  </div>
  <div style="padding:30px">
    <h2 style="margin:0 0 20px;color:#1a2332;font-size:20px">{html_escape(subject)}</h2>
    {body_html}
  </div>
  <div style="background:#f5f5f0;padding:20px;text-align:center;font-size:12px;color:#888">
    <p style="margin:0">FlashSport - Vos photos de course</p>
  </div>
</div>
</body>
</html>"""


def _count_recipients(event_id: int | None, db: Session) -> int:
    """Count how many customers match the segment."""
    if event_id:
        return db.query(func.count(func.distinct(Customer.id))).join(
            Order, Customer.id == Order.customer_id
        ).filter(Order.web_event_id == event_id).scalar() or 0
    return db.query(func.count(Customer.id)).scalar() or 0


def _mailing_out(m: Mailing, db: Session) -> MailingOut:
    event_name = None
    if m.event_id:
        ev = db.query(Event).filter(Event.id == m.event_id).first()
        event_name = ev.name if ev else None
    return MailingOut(
        id=m.id,
        subject=m.subject,
        raw_content=m.raw_content,
        html_content=m.html_content,
        event_id=m.event_id,
        event_name=event_name,
        status=m.status,
        sent_count=m.sent_count,
        sent_at=m.sent_at,
        created_at=m.created_at,
        updated_at=m.updated_at,
        recipient_count=_count_recipients(m.event_id, db),
    )


# --- Routes ---

@router.get("/stats")
def mailing_stats(db: Session = Depends(get_db), _=Depends(_mailing_user)):
    total = db.query(func.count(Mailing.id)).scalar() or 0
    drafts = db.query(func.count(Mailing.id)).filter(Mailing.status == "draft").scalar() or 0
    sent = db.query(func.count(Mailing.id)).filter(Mailing.status == "sent").scalar() or 0
    total_customers = db.query(func.count(Customer.id)).scalar() or 0
    total_sent = db.query(func.coalesce(func.sum(Mailing.sent_count), 0)).scalar() or 0
    return {
        "total_mailings": total,
        "drafts": drafts,
        "sent": sent,
        "total_customers": total_customers,
        "total_emails_sent": total_sent,
    }


@router.get("/events")
def list_events_for_segment(db: Session = Depends(get_db), _=Depends(_mailing_user)):
    """List events that have orders (for segment dropdown)."""
    events = db.query(Event).order_by(Event.date.desc()).all()
    return [{"id": e.id, "name": e.name, "date": str(e.date)} for e in events]


@router.get("", response_model=list[MailingOut])
def list_mailings(db: Session = Depends(get_db), _=Depends(_mailing_user)):
    mailings = db.query(Mailing).order_by(Mailing.created_at.desc()).all()
    return [_mailing_out(m, db) for m in mailings]


@router.post("", response_model=MailingOut)
def create_mailing(data: MailingCreate, db: Session = Depends(get_db), _=Depends(_mailing_user)):
    html = _generate_html(data.subject, data.raw_content)
    m = Mailing(
        subject=data.subject,
        raw_content=data.raw_content,
        html_content=html,
        event_id=data.event_id,
    )
    db.add(m)
    db.commit()
    db.refresh(m)
    return _mailing_out(m, db)


@router.get("/{mailing_id}", response_model=MailingOut)
def get_mailing(mailing_id: int, db: Session = Depends(get_db), _=Depends(_mailing_user)):
    m = db.query(Mailing).filter(Mailing.id == mailing_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Mailing not found")
    return _mailing_out(m, db)


@router.put("/{mailing_id}", response_model=MailingOut)
def update_mailing(mailing_id: int, data: MailingUpdate, db: Session = Depends(get_db), _=Depends(_mailing_user)):
    m = db.query(Mailing).filter(Mailing.id == mailing_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Mailing not found")
    if data.subject is not None:
        m.subject = data.subject
    if data.raw_content is not None:
        m.raw_content = data.raw_content
        m.html_content = _generate_html(m.subject, data.raw_content)
    if data.event_id is not None:
        m.event_id = data.event_id if data.event_id > 0 else None
    if data.status is not None:
        m.status = data.status
    db.commit()
    db.refresh(m)
    return _mailing_out(m, db)


@router.post("/{mailing_id}/send")
def send_mailing(mailing_id: int, db: Session = Depends(get_db), _=Depends(_mailing_user)):
    """Mark mailing as sent. Actual email sending is a future integration."""
    m = db.query(Mailing).filter(Mailing.id == mailing_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Mailing not found")
    if m.status == "sent":
        raise HTTPException(status_code=400, detail="Already sent")

    recipient_count = _count_recipients(m.event_id, db)
    m.status = "sent"
    m.sent_count = recipient_count
    m.sent_at = datetime.utcnow()
    db.commit()
    db.refresh(m)
    return {"message": f"Mailing envoye a {recipient_count} destinataires", "sent_count": recipient_count}


@router.delete("/{mailing_id}")
def delete_mailing(mailing_id: int, db: Session = Depends(get_db), _=Depends(_mailing_user)):
    m = db.query(Mailing).filter(Mailing.id == mailing_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Mailing not found")
    db.delete(m)
    db.commit()
    return {"message": "Mailing deleted"}


@router.get("/{mailing_id}/preview")
def preview_mailing(mailing_id: int, db: Session = Depends(get_db), _=Depends(_mailing_user)):
    """Return the HTML content for iframe preview."""
    m = db.query(Mailing).filter(Mailing.id == mailing_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Mailing not found")
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=m.html_content or "<p>Pas de contenu</p>")
