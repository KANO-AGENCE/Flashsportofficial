"""API routes for the web storefront (public + admin)."""
import logging
from pathlib import Path

import shutil
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from pydantic import BaseModel
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_module
from app.db.database import get_db
from app.models.models import Event, Photo
from app.models.web import Customer, Order, OrderItem, Product, WebEvent, WebEventProduct, WebPhoto
from app.schemas.web import (
    BibPackOut,
    CheckoutRequest,
    OrderOut,
    PublishRequest,
    WebEventCreate,
    WebEventOut,
    WebPhotoOut,
    WebEventUpdate,
)
from app.services.publish import publish_event_to_web
from config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/web", tags=["web-storefront"])

_web_user = require_module("WEB")


# ========== ADMIN ROUTES (called from TRI platform) ==========

@router.post("/publish")
def publish_to_web(data: PublishRequest, db: Session = Depends(get_db), _=Depends(get_current_user)):
    """Publish validated photos from TRI to the web storefront."""
    result = publish_event_to_web(data.event_id, db)
    return result


@router.get("/admin/events", response_model=list[WebEventOut])
def admin_list_web_events(db: Session = Depends(get_db), _=Depends(_web_user)):
    """List all web events (admin view)."""
    web_events = db.query(WebEvent).order_by(WebEvent.created_at.desc()).all()
    result = []
    for we in web_events:
        event = db.query(Event).filter(Event.id == we.event_id).first()
        photo_count = db.query(WebPhoto).filter(
            WebPhoto.web_event_id == we.id,
            WebPhoto.is_rejected == False,
        ).count()
        bib_count = len(set(
            wp.bib_number for wp in db.query(WebPhoto).filter(
                WebPhoto.web_event_id == we.id,
                WebPhoto.is_rejected == False,
            ).all()
        ))
        result.append(WebEventOut(
            id=we.id,
            event_id=we.event_id,
            slug=we.slug,
            cover_image=we.cover_image,
            description=we.description,
            is_published=we.is_published,
            photo_price=we.photo_price,
            pack_price=we.pack_price,
            all_photos_price=we.all_photos_price,
            published_at=we.published_at,
            created_at=we.created_at,
            event_name=event.name if event else "",
            event_date=str(event.date) if event else "",
            photo_count=photo_count,
            bib_count=bib_count,
        ))
    return result


@router.put("/admin/events/{web_event_id}", response_model=WebEventOut)
def admin_update_web_event(web_event_id: int, data: WebEventUpdate, db: Session = Depends(get_db), _=Depends(_web_user)):
    we = db.query(WebEvent).filter(WebEvent.id == web_event_id).first()
    if not we:
        raise HTTPException(status_code=404, detail="Web event not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(we, field, value)
    db.commit()
    db.refresh(we)
    event = db.query(Event).filter(Event.id == we.event_id).first()
    return WebEventOut(
        id=we.id, event_id=we.event_id, slug=we.slug,
        cover_image=we.cover_image, description=we.description,
        is_published=we.is_published, photo_price=we.photo_price,
        pack_price=we.pack_price, all_photos_price=we.all_photos_price,
        published_at=we.published_at, created_at=we.created_at,
        event_name=event.name if event else "", event_date=str(event.date) if event else "",
    )


@router.get("/admin/stats")
def admin_web_stats(db: Session = Depends(get_db), _=Depends(_web_user)):
    """Global web stats for superadmin dashboard."""
    total_events = db.query(WebEvent).count()
    published_events = db.query(WebEvent).filter(WebEvent.is_published == True).count()
    total_photos = db.query(WebPhoto).filter(WebPhoto.is_rejected == False).count()
    total_orders = db.query(Order).count()
    total_revenue = sum(o.total for o in db.query(Order).filter(Order.status == "paid").all())
    total_customers = db.query(Customer).count()
    return {
        "total_events": total_events,
        "published_events": published_events,
        "total_photos": total_photos,
        "total_orders": total_orders,
        "total_revenue": round(total_revenue, 2),
        "total_customers": total_customers,
    }


@router.post("/admin/events")
def admin_create_web_event(data: WebEventCreate, db: Session = Depends(get_db), _=Depends(_web_user)):
    """Create a new web event, optionally linked to a TRI event."""
    # Check if TRI event exists (if linking)
    if data.event_id:
        event = db.query(Event).filter(Event.id == data.event_id).first()
        if not event:
            raise HTTPException(status_code=404, detail="TRI event not found")
        # Check not already linked
        existing = db.query(WebEvent).filter(WebEvent.event_id == data.event_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="This TRI event is already linked to a web event")

    # Validate slug uniqueness
    if db.query(WebEvent).filter(WebEvent.slug == data.slug).first():
        raise HTTPException(status_code=400, detail="This slug is already taken")

    we = WebEvent(
        event_id=data.event_id,
        slug=data.slug,
        description=data.description,
        photo_price=data.photo_price,
        pack_price=data.pack_price,
        all_photos_price=data.all_photos_price,
    )
    db.add(we)
    db.commit()
    db.refresh(we)

    event = db.query(Event).filter(Event.id == we.event_id).first()
    return WebEventOut(
        id=we.id, event_id=we.event_id, slug=we.slug,
        cover_image=we.cover_image, description=we.description,
        is_published=we.is_published, photo_price=we.photo_price,
        pack_price=we.pack_price, all_photos_price=we.all_photos_price,
        published_at=we.published_at, created_at=we.created_at,
        event_name=event.name if event else "", event_date=str(event.date) if event else "",
    )


@router.delete("/admin/events/{web_event_id}")
def admin_delete_web_event(web_event_id: int, db: Session = Depends(get_db), _=Depends(_web_user)):
    we = db.query(WebEvent).filter(WebEvent.id == web_event_id).first()
    if not we:
        raise HTTPException(status_code=404, detail="Web event not found")
    db.delete(we)
    db.commit()
    return {"message": "Deleted"}


@router.post("/admin/events/{web_event_id}/cover")
async def admin_upload_cover(web_event_id: int, file: UploadFile, db: Session = Depends(get_db), _=Depends(_web_user)):
    """Upload a cover image for a web event."""
    we = db.query(WebEvent).filter(WebEvent.id == web_event_id).first()
    if not we:
        raise HTTPException(status_code=404, detail="Web event not found")

    # Validate file type
    allowed_types = {"image/jpeg", "image/png", "image/webp"}
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Type de fichier non autorise (JPG, PNG, WebP uniquement)")

    covers_dir = Path(settings.upload_dir) / "covers"
    covers_dir.mkdir(parents=True, exist_ok=True)

    ext = Path(file.filename or "cover.jpg").suffix or ".jpg"
    filename = f"cover_{web_event_id}_{uuid.uuid4().hex[:8]}{ext}"
    dest = covers_dir / filename

    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)

    we.cover_image = f"/uploads/covers/{filename}"
    db.commit()
    return {"cover_image": we.cover_image}


@router.get("/admin/tri-events")
def admin_list_tri_events(db: Session = Depends(get_db), _=Depends(_web_user)):
    """List TRI events available for linking (not already linked to a web event)."""
    linked_ids = [we.event_id for we in db.query(WebEvent).all()]
    events = db.query(Event).filter(Event.id.notin_(linked_ids) if linked_ids else True).order_by(Event.date.desc()).all()
    return [{"id": e.id, "name": e.name, "date": str(e.date)} for e in events]


# ========== PRODUCTS CRUD ==========

@router.get("/admin/products")
def admin_list_products(db: Session = Depends(get_db), _=Depends(_web_user)):
    products = db.query(Product).order_by(Product.sort_order, Product.id).all()
    return [
        {"id": p.id, "name": p.name, "description": p.description, "icon": p.icon,
         "default_price": p.default_price, "is_active": p.is_active, "sort_order": p.sort_order}
        for p in products
    ]


class ProductCreate(BaseModel):
    name: str
    description: str = ""
    icon: str = "photos"
    default_price: float = 9.90


class ProductUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    icon: str | None = None
    default_price: float | None = None
    is_active: bool | None = None
    sort_order: int | None = None


@router.post("/admin/products")
def admin_create_product(data: ProductCreate, db: Session = Depends(get_db), _=Depends(_web_user)):
    p = Product(name=data.name, description=data.description, icon=data.icon, default_price=data.default_price)
    db.add(p)
    db.commit()
    db.refresh(p)
    return {"id": p.id, "name": p.name, "description": p.description, "icon": p.icon,
            "default_price": p.default_price, "is_active": p.is_active}


@router.put("/admin/products/{product_id}")
def admin_update_product(product_id: int, data: ProductUpdate, db: Session = Depends(get_db), _=Depends(_web_user)):
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(p, field, value)
    db.commit()
    return {"id": p.id, "name": p.name, "description": p.description, "icon": p.icon,
            "default_price": p.default_price, "is_active": p.is_active}


@router.delete("/admin/products/{product_id}")
def admin_delete_product(product_id: int, db: Session = Depends(get_db), _=Depends(_web_user)):
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(p)
    db.commit()
    return {"message": "Deleted"}


# ========== EVENT-PRODUCT LINKS ==========

@router.get("/admin/events/{web_event_id}/products")
def admin_list_event_products(web_event_id: int, db: Session = Depends(get_db), _=Depends(_web_user)):
    weps = db.query(WebEventProduct).filter(WebEventProduct.web_event_id == web_event_id).all()
    return [
        {"id": wep.id, "product_id": wep.product_id, "product_name": wep.product.name,
         "product_icon": wep.product.icon, "product_description": wep.product.description,
         "price": wep.price, "is_featured": wep.is_featured}
        for wep in weps
    ]


class EventProductAdd(BaseModel):
    product_id: int
    price: float
    is_featured: bool = False


@router.post("/admin/events/{web_event_id}/products")
def admin_add_event_product(web_event_id: int, data: EventProductAdd, db: Session = Depends(get_db), _=Depends(_web_user)):
    we = db.query(WebEvent).filter(WebEvent.id == web_event_id).first()
    if not we:
        raise HTTPException(status_code=404, detail="Web event not found")
    existing = db.query(WebEventProduct).filter(
        WebEventProduct.web_event_id == web_event_id,
        WebEventProduct.product_id == data.product_id,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Product already added to this event")
    wep = WebEventProduct(
        web_event_id=web_event_id, product_id=data.product_id,
        price=data.price, is_featured=data.is_featured,
    )
    db.add(wep)
    db.commit()
    db.refresh(wep)
    return {"id": wep.id, "product_id": wep.product_id, "price": wep.price, "is_featured": wep.is_featured}


class EventProductUpdate(BaseModel):
    price: float | None = None
    is_featured: bool | None = None


@router.put("/admin/event-products/{wep_id}")
def admin_update_event_product(wep_id: int, data: EventProductUpdate, db: Session = Depends(get_db), _=Depends(_web_user)):
    wep = db.query(WebEventProduct).filter(WebEventProduct.id == wep_id).first()
    if not wep:
        raise HTTPException(status_code=404, detail="Not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(wep, field, value)
    db.commit()
    return {"id": wep.id, "price": wep.price, "is_featured": wep.is_featured}


@router.delete("/admin/event-products/{wep_id}")
def admin_delete_event_product(wep_id: int, db: Session = Depends(get_db), _=Depends(_web_user)):
    wep = db.query(WebEventProduct).filter(WebEventProduct.id == wep_id).first()
    if not wep:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(wep)
    db.commit()
    return {"message": "Deleted"}


# ========== PUBLIC ROUTES (web storefront) ==========

@router.get("/events")
def public_list_events(db: Session = Depends(get_db)):
    """List published events for the public storefront."""
    web_events = db.query(WebEvent).filter(WebEvent.is_published == True).order_by(WebEvent.created_at.desc()).all()
    result = []
    for we in web_events:
        event = db.query(Event).filter(Event.id == we.event_id).first()
        photo_count = db.query(WebPhoto).filter(
            WebPhoto.web_event_id == we.id,
            WebPhoto.is_rejected == False,
        ).count()
        result.append({
            "id": we.id,
            "slug": we.slug,
            "name": event.name if event else "",
            "date": str(event.date) if event else "",
            "cover_image": we.cover_image,
            "description": we.description,
            "photo_count": photo_count,
            "photo_price": we.photo_price,
            "pack_price": we.pack_price,
            "all_photos_price": we.all_photos_price,
        })
    return result


@router.get("/events/{slug}")
def public_get_event(slug: str, db: Session = Depends(get_db)):
    """Get event details by slug."""
    we = db.query(WebEvent).filter(WebEvent.slug == slug, WebEvent.is_published == True).first()
    if not we:
        raise HTTPException(status_code=404, detail="Event not found")
    event = db.query(Event).filter(Event.id == we.event_id).first()
    photo_count = db.query(WebPhoto).filter(
        WebPhoto.web_event_id == we.id, WebPhoto.is_rejected == False,
    ).count()
    bib_numbers = sorted(set(
        wp.bib_number for wp in db.query(WebPhoto).filter(
            WebPhoto.web_event_id == we.id, WebPhoto.is_rejected == False,
        ).all()
    ), key=lambda x: x.zfill(10))
    return {
        "id": we.id,
        "slug": we.slug,
        "name": event.name if event else "",
        "date": str(event.date) if event else "",
        "cover_image": we.cover_image,
        "description": we.description,
        "photo_count": photo_count,
        "bib_numbers": bib_numbers,
    }


@router.get("/events/{slug}/search")
def public_search_bib(slug: str, bib: str, db: Session = Depends(get_db)):
    """Search photos by bib number in an event."""
    we = db.query(WebEvent).filter(WebEvent.slug == slug, WebEvent.is_published == True).first()
    if not we:
        raise HTTPException(status_code=404, detail="Event not found")

    web_photos = (
        db.query(WebPhoto)
        .filter(
            WebPhoto.web_event_id == we.id,
            WebPhoto.bib_number == bib,
            WebPhoto.is_rejected == False,
        )
        .order_by(WebPhoto.sort_order)
        .all()
    )

    photos = []
    for wp in web_photos:
        photo = db.query(Photo).filter(Photo.id == wp.photo_id).first()
        photos.append({
            "id": wp.id,
            "photo_id": wp.photo_id,
            "bib_number": wp.bib_number,
            "thumbnail_url": f"/api/web/thumbnails/{wp.id}",
            "width": photo.width if photo else None,
            "height": photo.height if photo else None,
        })

    # Get products for this event
    weps = db.query(WebEventProduct).filter(WebEventProduct.web_event_id == we.id).all()
    products = []
    for wep in weps:
        products.append({
            "id": wep.id,
            "product_id": wep.product_id,
            "name": wep.product.name,
            "description": wep.product.description,
            "icon": wep.product.icon,
            "price": wep.price,
            "is_featured": wep.is_featured,
        })
    # Sort: featured first
    products.sort(key=lambda p: (not p["is_featured"], p["price"]))

    return {
        "bib_number": bib,
        "photo_count": len(photos),
        "photos": photos,
        "products": products,
    }


@router.get("/thumbnails/{web_photo_id}")
def serve_thumbnail(web_photo_id: int, db: Session = Depends(get_db)):
    """Serve a watermarked thumbnail image."""
    wp = db.query(WebPhoto).filter(WebPhoto.id == web_photo_id).first()
    if not wp or not wp.thumbnail_path:
        raise HTTPException(status_code=404, detail="Thumbnail not found")
    path = Path(wp.thumbnail_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Thumbnail file not found")
    return FileResponse(
        str(path),
        media_type="image/jpeg",
        headers={
            "Cache-Control": "public, max-age=86400",
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.post("/checkout")
def checkout(data: CheckoutRequest, db: Session = Depends(get_db)):
    """Process a cart checkout (creates order, placeholder for payment)."""
    we = db.query(WebEvent).filter(WebEvent.id == data.web_event_id).first()
    if not we:
        raise HTTPException(status_code=404, detail="Event not found")

    # Get or create customer
    customer = db.query(Customer).filter(Customer.email == data.email).first()
    if not customer:
        customer = Customer(
            email=data.email,
            first_name=data.first_name,
            last_name=data.last_name,
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)

    # Calculate total
    total = 0.0
    order_items = []
    if not data.items:
        raise HTTPException(status_code=400, detail="Le panier est vide")

    for item in data.items:
        if item.type == "photo" and item.web_photo_id:
            price = we.photo_price
            order_items.append(OrderItem(
                web_photo_id=item.web_photo_id,
                item_type="photo",
                price=price,
            ))
            total += price
        elif item.type == "pack" and item.bib_number:
            price = we.pack_price
            order_items.append(OrderItem(
                pack_bib=item.bib_number,
                item_type="pack",
                price=price,
            ))
            total += price
        elif item.type == "all":
            price = we.all_photos_price
            order_items.append(OrderItem(
                item_type="all",
                price=price,
            ))
            total += price

    order = Order(
        customer_id=customer.id,
        web_event_id=we.id,
        total=round(total, 2),
        status="pending",
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    for oi in order_items:
        oi.order_id = order.id
        db.add(oi)
    db.commit()

    return {
        "order_id": order.id,
        "total": order.total,
        "status": order.status,
        "message": "Commande creee. Paiement a integrer.",
    }
