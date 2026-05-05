from datetime import datetime
from pydantic import BaseModel


class ParticipantOut(BaseModel):
    id: int
    event_id: int
    bib_number: str
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    race_time: str | None = None
    country: str | None = None

    class Config:
        from_attributes = True


class ParticipantImportResult(BaseModel):
    imported: int
    skipped: int
    errors: list[str] = []
