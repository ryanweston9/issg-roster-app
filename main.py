from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from database import init_db, SessionLocal, User, Staff
from routers import auth_router, staff, swings, overrides, flights, agent
from build_flights_db import build as build_flights_db
from auth import hash_password
from datetime import date
import os

app = FastAPI(title="ISSG Roster App", version="1.0.0")


def auto_seed():
    """Seed default users and staff if not already present."""
    db = SessionLocal()
    try:
        users = [
            {"username": "britt", "full_name": "Brittany Crawford", "password": "changeme123"},
            {"username": "ryan", "full_name": "Ryan Weston", "password": "changeme123"},
        ]
        for u in users:
            if not db.query(User).filter(User.username == u["username"]).first():
                db.add(User(
                    username=u["username"],
                    full_name=u["full_name"],
                    hashed_password=hash_password(u["password"])
                ))

        staff_data = [
            {"emp_number": "764148", "full_name": "Amanda Inglis-Baillie", "role": "Technician",
             "hub": "EAST", "roster_type": "8/6", "roster_expiry": date(2026, 8, 18), "village": "JV", "site_code": "CC"},
            {"emp_number": "807406", "full_name": "Clive Ettia", "role": "Technician",
             "hub": "EAST", "roster_type": "8/6", "roster_expiry": date(2026, 8, 19), "village": "KV", "site_code": "CC"},
            {"emp_number": "PETE-CASUAL", "full_name": "Pete Scully", "role": "Relief",
             "hub": "EAST", "roster_type": "casual", "roster_expiry": None, "village": "JV", "site_code": "CC"},
        ]
        for s in staff_data:
            if not db.query(Staff).filter(Staff.emp_number == s["emp_number"]).first():
                db.add(Staff(**s))

        db.commit()
        print("Auto-seed complete.")
    except Exception as e:
        print(f"Seed error: {e}")
        db.rollback()
    finally:
        db.close()


@app.on_event("startup")
def on_startup():
    build_flights_db()
    init_db()
    auto_seed()


app.include_router(auth_router.router)
app.include_router(staff.router)
app.include_router(swings.router)
app.include_router(overrides.router)
app.include_router(flights.router)
app.include_router(agent.router)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return FileResponse("static/index.html")

@app.get("/health")
async def health():
    return {"status": "ok"}
