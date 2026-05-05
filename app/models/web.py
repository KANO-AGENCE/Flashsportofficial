"""Models for the web storefront: customers, orders, published photos."""
from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, func,
)
from sqlalchemy.orm import relationship

from app.db.database import Base


class WebEvent(Base):
    """An event published to the web storefront."""
    __tablename__ = "web_events"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), unique=True, nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    cover_image = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    is_published = Column(Boolean, default=False)
    photo_price = Column(Float, default=2.0)
    pack_price = Column(Float, default=9.90)
    all_photos_price = Column(Float, default=49.90)
    published_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    event = relationship("Event")
    web_photos = relationship("WebPhoto", back_populates="web_event", cascade="all, delete-orphan")


class WebPhoto(Base):
    """A photo indexed on the web storefront, linked to a bib pack."""
    __tablename__ = "web_photos"

    id = Column(Integer, primary_key=True, index=True)
    web_event_id = Column(Integer, ForeignKey("web_events.id", ondelete="CASCADE"), nullable=False, index=True)
    photo_id = Column(Integer, ForeignKey("photos.id", ondelete="CASCADE"), nullable=False)
    bib_number = Column(String(20), nullable=False, index=True)
    thumbnail_path = Column(String(500), nullable=True)
    is_rejected = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())

    web_event = relationship("WebEvent", back_populates="web_photos")
    photo = relationship("Photo")


class Product(Base):
    """A product template (e.g. Pack Digital, Pack Digital + Poster)."""
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(50), default="photos")  # photos, poster, book, frame
    default_price = Column(Float, default=9.90)
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())


class WebEventProduct(Base):
    """A product linked to a specific web event, with custom price."""
    __tablename__ = "web_event_products"

    id = Column(Integer, primary_key=True, index=True)
    web_event_id = Column(Integer, ForeignKey("web_events.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    price = Column(Float, nullable=False)
    is_featured = Column(Boolean, default=False)

    web_event = relationship("WebEvent")
    product = relationship("Product")


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    password_hash = Column(String(255), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    orders = relationship("Order", back_populates="customer", cascade="all, delete-orphan")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    web_event_id = Column(Integer, ForeignKey("web_events.id", ondelete="SET NULL"), nullable=True, index=True)
    total = Column(Float, default=0.0)
    status = Column(String(20), default="pending")  # pending, paid, downloaded, refunded
    payment_intent = Column(String(255), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    customer = relationship("Customer", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    web_photo_id = Column(Integer, ForeignKey("web_photos.id", ondelete="SET NULL"), nullable=True)
    pack_bib = Column(String(20), nullable=True)
    item_type = Column(String(20), default="photo")  # photo, pack, all
    price = Column(Float, default=0.0)

    order = relationship("Order", back_populates="items")
    web_photo = relationship("WebPhoto")
