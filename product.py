from sqlalchemy import Column, Integer, String, Float, Boolean, Text, DateTime
from datetime import datetime
from core.database import Base

class Product(Base):
    __tablename__ = "products"

    id          = Column(Integer, primary_key=True, index=True)
    name        = Column(String(150), nullable=False)
    slug        = Column(String(150), unique=True, index=True)
    description = Column(Text, nullable=True)
    category    = Column(String(100), nullable=True)   # e.g. "powder", "capsule", "coating"
    is_active   = Column(Boolean, default=True)
    created_at  = Column(DateTime, default=datetime.utcnow)
    updated_at  = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    variants = relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan")

from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey

class ProductVariant(Base):
    """Each product can have multiple size/quantity variants with their own price."""
    __tablename__ = "product_variants"

    id         = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    label      = Column(String(100), nullable=False)   # e.g. "100g", "30 capsules"
    price_egp  = Column(Float, nullable=False)
    stock      = Column(Integer, default=0)
    is_active  = Column(Boolean, default=True)

    product = relationship("Product", back_populates="variants")
    order_items = relationship("OrderItem", back_populates="variant")
