from datetime import datetime
from typing import Literal
from pydantic import BaseModel, EmailStr


class WebEventCreate(BaseModel):
    event_id: int
    slug: str
    description: str = ""
    photo_price: float = 2.0
    pack_price: float = 9.90
    all_photos_price: float = 49.90


class WebEventUpdate(BaseModel):
    slug: str | None = None
    description: str | None = None
    cover_image: str | None = None
    is_published: bool | None = None
    photo_price: float | None = None
    pack_price: float | None = None
    all_photos_price: float | None = None


class WebEventOut(BaseModel):
    id: int
    event_id: int
    slug: str
    cover_image: str | None = None
    description: str | None = None
    is_published: bool = False
    photo_price: float = 2.0
    pack_price: float = 9.90
    all_photos_price: float = 49.90
    published_at: datetime | None = None
    created_at: datetime | None = None
    event_name: str = ""
    event_date: str = ""
    photo_count: int = 0
    bib_count: int = 0

    class Config:
        from_attributes = True


class WebPhotoOut(BaseModel):
    id: int
    photo_id: int
    bib_number: str
    thumbnail_url: str = ""
    is_rejected: bool = False
    sort_order: int = 0
    width: int | None = None
    height: int | None = None

    class Config:
        from_attributes = True


class BibPackOut(BaseModel):
    bib_number: str
    photo_count: int
    photos: list[WebPhotoOut] = []


class PublishRequest(BaseModel):
    event_id: int


class CustomerCreate(BaseModel):
    email: str
    first_name: str = ""
    last_name: str = ""
    password: str = ""


class CustomerOut(BaseModel):
    id: int
    email: str
    first_name: str | None = None
    last_name: str | None = None
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class OrderOut(BaseModel):
    id: int
    total: float
    status: str
    created_at: datetime | None = None
    items: list[dict] = []

    class Config:
        from_attributes = True


class CartItem(BaseModel):
    type: Literal["photo", "pack", "all"]
    web_photo_id: int | None = None
    bib_number: str | None = None


class CheckoutRequest(BaseModel):
    email: EmailStr
    first_name: str = ""
    last_name: str = ""
    items: list[CartItem]
    web_event_id: int
