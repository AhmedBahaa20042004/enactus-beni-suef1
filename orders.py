from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from core.database import get_db
from core.security import get_current_user, get_current_admin
from core.email import notify_admin_new_order, notify_customer_order_received, notify_customer_status_update
from models.order import Order, OrderItem
from models.product import ProductVariant
from schemas.schemas import OrderIn, OrderOut, OrderStatusUpdate

router = APIRouter(prefix="/api/orders", tags=["Orders"])

def _load_order(db, order_id):
    return (
        db.query(Order)
        .options(
            joinedload(Order.items).joinedload(OrderItem.variant).joinedload(ProductVariant.product)
        )
        .filter(Order.id == order_id)
        .first()
    )

@router.post("/", response_model=OrderOut, status_code=201)
def place_order(data: OrderIn, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    if not data.items:
        raise HTTPException(status_code=400, detail="Order must have at least one item")

    total = 0.0
    order = Order(
        customer_name=data.customer_name,
        customer_email=data.customer_email,
        customer_phone=data.customer_phone,
        address=data.address,
        notes=data.notes,
        total_egp=0,
    )
    db.add(order)
    db.flush()

    for item_data in data.items:
        variant = db.query(ProductVariant).filter(ProductVariant.id == item_data.variant_id).first()
        if not variant:
            raise HTTPException(status_code=404, detail=f"Variant {item_data.variant_id} not found")
        if variant.stock < item_data.quantity:
            raise HTTPException(status_code=400, detail=f"Insufficient stock for {variant.label}")
        variant.stock -= item_data.quantity
        line_total = variant.price_egp * item_data.quantity
        total += line_total
        item = OrderItem(
            order_id=order.id,
            variant_id=variant.id,
            quantity=item_data.quantity,
            unit_price=variant.price_egp,
        )
        db.add(item)

    order.total_egp = total
    db.commit()

    # Reload with relationships for email
    full_order = _load_order(db, order.id)

    # Send emails in background so the API response is instant
    background_tasks.add_task(notify_admin_new_order, full_order)
    background_tasks.add_task(notify_customer_order_received, full_order)

    return full_order

@router.get("/", response_model=List[OrderOut])
def list_orders(status: Optional[str] = None, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    q = db.query(Order).options(
        joinedload(Order.items).joinedload(OrderItem.variant).joinedload(ProductVariant.product)
    )
    if status:
        q = q.filter(Order.status == status)
    return q.order_by(Order.created_at.desc()).all()

@router.get("/my-orders", response_model=List[OrderOut])
def my_orders(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return db.query(Order).filter(Order.customer_email == current_user.email).order_by(Order.created_at.desc()).all()

@router.get("/{order_id}", response_model=OrderOut)
def get_order(order_id: int, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    order = _load_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@router.patch("/{order_id}/status", response_model=OrderOut)
def update_order_status(order_id: int, data: OrderStatusUpdate, background_tasks: BackgroundTasks, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    order = _load_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    order.status = data.status
    db.commit()
    db.refresh(order)
    full_order = _load_order(db, order_id)
    # Email customer about the status change
    background_tasks.add_task(notify_customer_status_update, full_order)
    return full_order

@router.delete("/{order_id}", status_code=204)
def delete_order(order_id: int, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    db.delete(order)
    db.commit()
