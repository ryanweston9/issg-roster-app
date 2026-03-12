from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db, Swing
from auth import get_current_user
from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional, List

router = APIRouter(prefix="/api/swings", tags=["swings"])


class SwingCreate(BaseModel):
    staff_emp: str
    fly_in_date: date
    fly_out_date: date
    fly_in_flight: Optional[str] = None
    fly_out_flight: Optional[str] = None
    village: Optional[str] = None
    room_ref: Optional[str] = None
    notes: Optional[str] = None


class SwingOut(BaseModel):
    id: int
    staff_emp: str
    fly_in_date: date
    fly_out_date: date
    fly_in_flight: Optional[str]
    fly_out_flight: Optional[str]
    village: Optional[str]
    room_ref: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


@router.get("/", response_model=List[SwingOut])
async def list_swings(
    staff_emp: Optional[str] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    db: Session = Depends(get_db),
    _=Depends(get_current_user)
):
    q = db.query(Swing)
    if staff_emp:
        q = q.filter(Swing.staff_emp == staff_emp)
    if from_date:
        q = q.filter(Swing.fly_out_date >= from_date)
    if to_date:
        q = q.filter(Swing.fly_in_date <= to_date)
    return q.order_by(Swing.fly_in_date).all()


@router.post("/", response_model=SwingOut)
async def create_swing(swing: SwingCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    db_swing = Swing(**swing.model_dump())
    db.add(db_swing)
    db.commit()
    db.refresh(db_swing)
    return db_swing


@router.put("/{swing_id}", response_model=SwingOut)
async def update_swing(swing_id: int, swing: SwingCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    db_swing = db.query(Swing).filter(Swing.id == swing_id).first()
    if not db_swing:
        raise HTTPException(status_code=404, detail="Swing not found")
    for k, v in swing.model_dump().items():
        setattr(db_swing, k, v)
    db_swing.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_swing)
    return db_swing


@router.delete("/{swing_id}")
async def delete_swing(swing_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    db_swing = db.query(Swing).filter(Swing.id == swing_id).first()
    if not db_swing:
        raise HTTPException(status_code=404, detail="Swing not found")
    db.delete(db_swing)
    db.commit()
    return {"ok": True}
