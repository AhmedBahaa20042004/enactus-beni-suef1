from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from core.database import get_db
from core.security import get_current_admin
from models.contact import ContactMessage
from schemas.schemas import ContactIn, ContactOut

router = APIRouter(prefix="/api/contact", tags=["Contact"])

@router.post("/", response_model=ContactOut, status_code=201)
def send_message(data: ContactIn, db: Session = Depends(get_db)):
    """Public endpoint — anyone can submit a contact message."""
    msg = ContactMessage(**data.model_dump())
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg

@router.get("/", response_model=List[ContactOut])
def list_messages(db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    return db.query(ContactMessage).order_by(ContactMessage.created_at.desc()).all()

@router.patch("/{msg_id}/read", response_model=ContactOut)
def mark_read(msg_id: int, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    msg = db.query(ContactMessage).filter(ContactMessage.id == msg_id).first()
    if not msg:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Message not found")
    msg.is_read = True
    db.commit()
    db.refresh(msg)
    return msg

@router.delete("/{msg_id}", status_code=204)
def delete_message(msg_id: int, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    msg = db.query(ContactMessage).filter(ContactMessage.id == msg_id).first()
    if not msg:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Message not found")
    db.delete(msg)
    db.commit()
