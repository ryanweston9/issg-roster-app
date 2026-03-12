"""
Run once after deploy to seed users and staff.
Usage: python seed.py
"""
from database import SessionLocal, init_db, User, Staff
from auth import hash_password
from datetime import date


def seed():
    init_db()
    db = SessionLocal()

    # --- Users ---
    users = [
        {"username": "britt", "full_name": "Brittany Crawford", "password": "changeme123"},
        {"username": "ryan", "full_name": "Ryan Weston", "password": "changeme123"},
    ]
    for u in users:
        existing = db.query(User).filter(User.username == u["username"]).first()
        if not existing:
            db.add(User(
                username=u["username"],
                full_name=u["full_name"],
                hashed_password=hash_password(u["password"])
            ))
            print(f"Created user: {u['username']}")
        else:
            print(f"User already exists: {u['username']}")

    # --- Eastern Hub Staff ---
    staff = [
        {
            "emp_number": "764148",
            "full_name": "Amanda Inglis-Baillie",
            "role": "Technician",
            "hub": "EAST",
            "roster_type": "8/6",
            "roster_expiry": date(2026, 8, 18),
            "village": "JV",
            "site_code": "CC",
        },
        {
            "emp_number": "807406",
            "full_name": "Clive Ettia",
            "role": "Technician",
            "hub": "EAST",
            "roster_type": "8/6",
            "roster_expiry": date(2026, 8, 19),
            "village": "KV",
            "site_code": "CC",
        },
        {
            "emp_number": "PETE-CASUAL",
            "full_name": "Pete Scully",
            "role": "Relief",
            "hub": "EAST",
            "roster_type": "casual",
            "roster_expiry": None,
            "village": "JV",
            "site_code": "CC",
        },
    ]
    for s in staff:
        existing = db.query(Staff).filter(Staff.emp_number == s["emp_number"]).first()
        if not existing:
            db.add(Staff(**s))
            print(f"Created staff: {s['full_name']}")
        else:
            print(f"Staff already exists: {s['full_name']}")

    db.commit()
    db.close()
    print("Seed complete.")


if __name__ == "__main__":
    seed()
