from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from core.database import get_db
from core.security import get_current_admin, get_current_user
from models.product import Product, ProductVariant
from schemas.schemas import ProductIn, ProductOut, ProductUpdate, VariantIn, VariantOut

router = APIRouter(prefix="/api/products", tags=["Products"])

# ── PUBLIC ──────────────────────────────────────────────────

@router.get("/", response_model=List[ProductOut])
def list_products(
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    q = db.query(Product).filter(Product.is_active == True)
    if category:
        q = q.filter(Product.category == category)
    return q.all()

@router.get("/{slug}", response_model=ProductOut)
def get_product(slug: str, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.slug == slug).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

# ── ADMIN ───────────────────────────────────────────────────

@router.post("/", response_model=ProductOut, status_code=201)
def create_product(data: ProductIn, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    if db.query(Product).filter(Product.slug == data.slug).first():
        raise HTTPException(status_code=400, detail="Slug already exists")
    product = Product(
        name=data.name,
        slug=data.slug,
        description=data.description,
        category=data.category,
        is_active=data.is_active,
    )
    db.add(product)
    db.flush()  # get product.id before adding variants
    for v in data.variants:
        variant = ProductVariant(product_id=product.id, **v.model_dump())
        db.add(variant)
    db.commit()
    db.refresh(product)
    return product

@router.patch("/{product_id}", response_model=ProductOut)
def update_product(product_id: int, data: ProductUpdate, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    return product

@router.delete("/{product_id}", status_code=204)
def delete_product(product_id: int, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(product)
    db.commit()

# ── VARIANTS ────────────────────────────────────────────────

@router.post("/{product_id}/variants", response_model=VariantOut, status_code=201)
def add_variant(product_id: int, data: VariantIn, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    variant = ProductVariant(product_id=product_id, **data.model_dump())
    db.add(variant)
    db.commit()
    db.refresh(variant)
    return variant

@router.patch("/variants/{variant_id}", response_model=VariantOut)
def update_variant(variant_id: int, data: VariantIn, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    variant = db.query(ProductVariant).filter(ProductVariant.id == variant_id).first()
    if not variant:
        raise HTTPException(status_code=404, detail="Variant not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(variant, field, value)
    db.commit()
    db.refresh(variant)
    return variant

@router.delete("/variants/{variant_id}", status_code=204)
def delete_variant(variant_id: int, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    variant = db.query(ProductVariant).filter(ProductVariant.id == variant_id).first()
    if not variant:
        raise HTTPException(status_code=404, detail="Variant not found")
    db.delete(variant)
    db.commit()
