from fastapi import APIRouter, HTTPException, Depends
from auth import get_current_user
import sqlite3
import os
from typing import Optional, List
from pydantic import BaseModel

router = APIRouter(prefix="/api/flights", tags=["flights"])

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "fmg_flights.db")


def get_flights_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


class FlightOut(BaseModel):
    site: str
    day_of_week: str
    flight_number: str
    aircraft: Optional[str]
    depart_location: str
    depart_time: str
    arrive_location: str
    arrive_time: str
    checkin_open: Optional[str]
    checkin_close: Optional[str]
    direction: str


@router.get("/", response_model=List[FlightOut])
async def list_flights(
    site: Optional[str] = None,
    day_of_week: Optional[str] = None,
    direction: Optional[str] = None,
    conn: sqlite3.Connection = Depends(get_flights_db),
    _=Depends(get_current_user)
):
    query = "SELECT * FROM flights WHERE 1=1"
    params = []
    if site:
        query += " AND site = ?"
        params.append(site.upper())
    if day_of_week:
        query += " AND day_of_week = ?"
        params.append(day_of_week.capitalize())
    if direction:
        query += " AND direction = ?"
        params.append(direction.lower())
    query += " ORDER BY site, day_of_week, depart_time"
    rows = conn.execute(query, params).fetchall()
    return [dict(r) for r in rows]


@router.get("/sites")
async def list_sites(conn: sqlite3.Connection = Depends(get_flights_db), _=Depends(get_current_user)):
    rows = conn.execute("SELECT DISTINCT site FROM flights ORDER BY site").fetchall()
    return [r["site"] for r in rows]
