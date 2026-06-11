from fastapi import APIRouter, HTTPException, Depends
from auth import get_current_user
import sqlite3
import os
from typing import Optional, List
from pydantic import BaseModel

router = APIRouter(prefix="/api/flights", tags=["flights"])

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "fmg_flights.db")

# Site codes used by the app map to the full site names stored in the flights DB.
SITE_ALIASES = {"CC": "Christmas Creek"}  # extend per hub as they onboard (CB, etc.)


def get_flights_db():
    # check_same_thread=False: the sync dependency creates the connection in a
    # threadpool worker, but the async endpoint uses it in the event-loop thread.
    # Each request gets its own short-lived connection, so cross-thread use is safe.
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
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
        name = SITE_ALIASES.get(site.strip().upper(), site)
        query += " AND UPPER(site) = UPPER(?)"
        params.append(name)
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
