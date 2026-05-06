from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime
from models.order import OrderStatus

# ─── AUTH ───────────────────────────────────────────────────
class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    name: str
    email: str
    is_admin: bool
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut

# ─── PRODUCTS ───────────────────────────────────────────────
class VariantIn(BaseModel):
    label: str
    price_egp: float
    stock: int = 0
    is_active: bool = True

class VariantOut(VariantIn):
    id: int
    product_id: int
    model_config = {"from_attributes": True}

class ProductIn(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    category: Optional[str] = None
    is_active: bool = True
    variants: List[VariantIn] = []

class ProductOut(BaseModel):
    id: int
    name: str
    slug: str
    description: Optional[str]
    category: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    variants: List[VariantOut] = []
    model_config = {"from_attributes": True}

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    is_active: Optional[bool] = None

# ─── ORDERS ─────────────────────────────────────────────────
class OrderItemIn(BaseModel):
    variant_id: int
    quantity: int = 1

class OrderIn(BaseModel):
    customer_name: str
    customer_email: EmailStr
    customer_phone: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    items: List[OrderItemIn]

class OrderItemOut(BaseModel):
    id: int
    variant_id: int
    quantity: int
    unit_price: float
    model_config = {"from_attributes": True}

class OrderOut(BaseModel):
    id: int
    customer_name: str
    customer_email: str
    customer_phone: Optional[str]
    address: Optional[str]
    total_egp: float
    status: OrderStatus
    notes: Optional[str]
    created_at: datetime
    items: List[OrderItemOut] = []
    model_config = {"from_attributes": True}

class OrderStatusUpdate(BaseModel):
    status: OrderStatus

# ─── CONTACT ────────────────────────────────────────────────
class ContactIn(BaseModel):
    name: str
    email: EmailStr
    subject: Optional[str] = None
    message: str

class ContactOut(ContactIn):
    id: int
    is_read: bool
    created_at: datetime
    model_config = {"from_attributes": True}
