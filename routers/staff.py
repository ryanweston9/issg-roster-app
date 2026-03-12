from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db, Staff
from auth import get_current_user
from typing import List
from pydantic import BaseModel
from datetime import date
from typing import Optional

router = APIRouter(prefix="/api/staff", tags=["staff"])


class StaffOut(BaseModel):
    id: int
    emp_number: str
    full_name: str
    role: str
    hub: str
    roster_type: str
    roster_expiry: Optional[date]
    village: str
    site_code: str
    is_active: bool

    class Config:
        from_attributes = True


@router.get("/", response_model=List[StaffOut])
async def list_staff(hub: Optional[str] = None, db: Session = Depends(get_db), _=Depends(get_current_user)):
    q = db.query(Staff).filter(Staff.is_active == True)
    if hub:
        q = q.filter(Staff.hub == hub)
    return q.all()


@router.get("/{emp_number}", response_model=StaffOut)
async def get_staff(emp_number: str, db: Session = Depends(get_db), _=Depends(get_current_user)):
    staff = db.query(Staff).filter(Staff.emp_number == emp_number).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")
    return staff
