from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db, RosterOverride
from auth import get_current_user
from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional, List

router = APIRouter(prefix="/api/overrides", tags=["overrides"])


class OverrideCreate(BaseModel):
    staff_emp: str
    date: date
    status: str
    notes: Optional[str] = None


class OverrideOut(BaseModel):
    id: int
    staff_emp: str
    date: date
    status: str
    notes: Optional[str]
    created_by: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/", response_model=List[OverrideOut])
async def list_overrides(
    staff_emp: Optional[str] = None,
    db: Session = Depends(get_db),
    _=Depends(get_current_user)
):
    q = db.query(RosterOverride)
    if staff_emp:
        q = q.filter(RosterOverride.staff_emp == staff_emp)
    return q.order_by(RosterOverride.date).all()


@router.post("/", response_model=OverrideOut)
async def create_override(
    override: OverrideCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    db_override = RosterOverride(**override.model_dump(), created_by=current_user.username)
    db.add(db_override)
    db.commit()
    db.refresh(db_override)
    return db_override


@router.delete("/{override_id}")
async def delete_override(override_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    obj = db.query(RosterOverride).filter(RosterOverride.id == override_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Override not found")
    db.delete(obj)
    db.commit()
    return {"ok": True}
