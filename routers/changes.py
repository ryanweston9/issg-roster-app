from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db, ChangeRequest
from auth import get_current_user
from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional, List

router = APIRouter(prefix="/api/changes", tags=["changes"])


class ChangeCreate(BaseModel):
    staff_emp: str
    swing_id: Optional[int] = None
    change_type: str
    effective_date: date
    new_date: Optional[date] = None
    reason: str
    notes: Optional[str] = None


class ChangeStatusUpdate(BaseModel):
    status: str
    workflow_ref: Optional[str] = None
    notes: Optional[str] = None


class ChangeOut(BaseModel):
    id: int
    staff_emp: str
    swing_id: Optional[int]
    change_type: str
    effective_date: date
    new_date: Optional[date]
    reason: str
    status: str
    workflow_ref: Optional[str]
    notes: Optional[str]
    submitted_by: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


@router.get("/", response_model=List[ChangeOut])
async def list_changes(
    staff_emp: Optional[str] = None,
    db: Session = Depends(get_db),
    _=Depends(get_current_user)
):
    q = db.query(ChangeRequest)
    if staff_emp:
        q = q.filter(ChangeRequest.staff_emp == staff_emp)
    return q.order_by(ChangeRequest.created_at.desc()).all()


@router.post("/", response_model=ChangeOut)
async def create_change(
    change: ChangeCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    obj = ChangeRequest(**change.model_dump(), submitted_by=current_user.username, status="requested")
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.put("/{change_id}/status", response_model=ChangeOut)
async def update_status(
    change_id: int,
    update: ChangeStatusUpdate,
    db: Session = Depends(get_db),
    _=Depends(get_current_user)
):
    obj = db.query(ChangeRequest).filter(ChangeRequest.id == change_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Change request not found")
    obj.status = update.status
    if update.workflow_ref:
        obj.workflow_ref = update.workflow_ref
    if update.notes:
        obj.notes = update.notes
    obj.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{change_id}")
async def delete_change(
    change_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_user)
):
    obj = db.query(ChangeRequest).filter(ChangeRequest.id == change_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Change request not found")
    db.delete(obj)
    db.commit()
    return {"ok": True}
