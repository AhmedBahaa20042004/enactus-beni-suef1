from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from core.database import get_db
from core.security import get_current_admin
from models.user import User
from models.product import Product
from models.order import Order, OrderStatus
from models.contact import ContactMessage

router = APIRouter(prefix="/api/admin", tags=["Admin"])

@router.get("/dashboard")
def dashboard_stats(db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    """Returns summary statistics for the admin dashboard."""
    total_users     = db.query(func.count(User.id)).scalar()
    total_products  = db.query(func.count(Product.id)).scalar()
    total_orders    = db.query(func.count(Order.id)).scalar()
    revenue         = db.query(func.sum(Order.total_egp)).filter(
                        Order.status != OrderStatus.cancelled).scalar() or 0.0
    pending_orders  = db.query(func.count(Order.id)).filter(Order.status == OrderStatus.pending).scalar()
    unread_messages = db.query(func.count(ContactMessage.id)).filter(ContactMessage.is_read == False).scalar()

    recent_orders = db.query(Order).order_by(Order.created_at.desc()).limit(5).all()

    return {
        "total_users": total_users,
        "total_products": total_products,
        "total_orders": total_orders,
        "total_revenue_egp": round(revenue, 2),
        "pending_orders": pending_orders,
        "unread_messages": unread_messages,
        "recent_orders": [
            {
                "id": o.id,
                "customer": o.customer_name,
                "total": o.total_egp,
                "status": o.status,
                "date": o.created_at.isoformat(),
            }
            for o in recent_orders
        ],
    }
