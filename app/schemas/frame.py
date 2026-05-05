from pydantic import BaseModel


class FrameCreate(BaseModel):
    name: str
    text_x: float = 0.5
    text_y: float = 0.9
    text_size: int = 48
    text_color: str = "#FFFFFF"


class FrameUpdate(BaseModel):
    name: str | None = None
    text_x: float | None = None
    text_y: float | None = None
    text_size: int | None = None
    text_color: str | None = None


class FrameOut(BaseModel):
    id: int
    event_id: int
    name: str
    image_path: str
    text_x: float
    text_y: float
    text_size: int
    text_color: str

    class Config:
        from_attributes = True
