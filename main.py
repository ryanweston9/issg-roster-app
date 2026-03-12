from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from database import init_db, SessionLocal, User, Staff, Swing
from routers import auth_router, staff, swings, overrides, flights, agent
from routers import changes as changes_router
from build_flights_db import build as build_flights_db
from auth import hash_password
from datetime import date, timedelta
import os

app = FastAPI(title="ISSG Roster App", version="1.0.0")

# Amanda: base 2025-03-05, Clive: base 2025-03-12
# Pattern: day 0 = fly-in, days 1-7 = on site, day 8 = fly-out, days 9-13 = R&R, repeat
# Fly-in Wed QF2924 PER→CCK 06:00→08:20 | Fly-out Wed QF2925 CCK→PER 09:10→11:30

SWING_ON = 8
SWING_OFF = 6
CYCLE = SWING_ON + SWING_OFF

STAFF_SWINGS = [
    {
        "emp": "764148",
        "base": date(2025, 3, 5),   # Amanda — first fly-in
        "village": "JV",
        "fi_flight": "QF2924",
        "fo_flight": "QF2925",
    },
    {
        "emp": "807406",
        "base": date(2025, 3, 12),  # Clive — first fly-in
        "village": "KV",
        "fi_flight": "QF2924",
        "fo_flight": "QF2925",
    },
]


def generate_swings(emp, base, village, fi_flight, fo_flight, months_ahead=6):
    """Generate swing records from base date out to months_ahead."""
    swings = []
    end_date = date.today() + timedelta(days=months_ahead * 30)
    # Wind base back to find the first swing that covers today-3months
    start_lookback = date.today() - timedelta(days=90)
    # Find first swing cycle on or after lookback
    diff = (start_lookback - base).days
    if diff < 0:
        cycle_num = 0
    else:
        cycle_num = diff // CYCLE
    fly_in = base + timedelta(days=cycle_num * CYCLE)
    while fly_in <= end_date:
        fly_out = fly_in + timedelta(days=SWING_ON)
        swings.append({
            "staff_emp": emp,
            "fly_in_date": fly_in,
            "fly_out_date": fly_out,
            "fly_in_flight": fi_flight,
            "fly_out_flight": fo_flight,
            "village": village,
        })
        fly_in += timedelta(days=CYCLE)
    return swings


def auto_seed():
    db = SessionLocal()
    try:
        # Users
        for u in [
            {"username": "britt", "full_name": "Brittany Crawford", "password": "changeme123"},
            {"username": "ryan",  "full_name": "Ryan Weston",        "password": "changeme123"},
        ]:
            if not db.query(User).filter(User.username == u["username"]).first():
                db.add(User(username=u["username"], full_name=u["full_name"],
                            hashed_password=hash_password(u["password"])))

        # Staff
        for s in [
            {"emp_number": "764148",      "full_name": "Amanda Inglis-Baillie", "role": "Technician",
             "hub": "EAST", "roster_type": "8/6", "roster_expiry": date(2026, 8, 18), "village": "JV", "site_code": "CC"},
            {"emp_number": "807406",      "full_name": "Clive Ettia",           "role": "Technician",
             "hub": "EAST", "roster_type": "8/6", "roster_expiry": date(2026, 8, 19), "village": "KV", "site_code": "CC"},
            {"emp_number": "PETE-CASUAL", "full_name": "Pete Scully",           "role": "Relief",
             "hub": "EAST", "roster_type": "casual", "roster_expiry": None, "village": "JV", "site_code": "CC"},
        ]:
            from database import Staff as StaffModel
            if not db.query(StaffModel).filter(StaffModel.emp_number == s["emp_number"]).first():
                db.add(StaffModel(**s))

        # Swings — only seed if table is empty
        if db.query(Swing).count() == 0:
            for cfg in STAFF_SWINGS:
                for sw in generate_swings(**cfg):
                    db.add(Swing(**sw))
            print(f"Seeded swings for Amanda and Clive.")

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
app.include_router(changes_router.router)
app.include_router(flights.router)
app.include_router(agent.router)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return FileResponse("static/index.html")

@app.get("/health")
async def health():
    return {"status": "ok"}
