"""
Builds fmg_flights.db from fmg_flights.json.
Runs automatically on startup if the DB is missing or stale.
"""
import sqlite3
import json
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
JSON_PATH = os.path.join(DATA_DIR, "fmg_flights.json")
DB_PATH = os.path.join(DATA_DIR, "fmg_flights.db")


def build():
    if not os.path.exists(JSON_PATH):
        print("WARNING: fmg_flights.json not found — flight data unavailable.")
        return

    # Rebuild if DB missing or JSON is newer
    if os.path.exists(DB_PATH):
        if os.path.getmtime(JSON_PATH) <= os.path.getmtime(DB_PATH):
            return  # Already up to date

    print("Building fmg_flights.db from JSON...")
    with open(JSON_PATH, "r") as f:
        flights = json.load(f)

    conn = sqlite3.connect(DB_PATH)
    conn.execute("DROP TABLE IF EXISTS flights")
    conn.execute("""
        CREATE TABLE flights (
            id INTEGER PRIMARY KEY,
            site TEXT,
            day_of_week TEXT,
            flight_number TEXT,
            aircraft TEXT,
            depart_location TEXT,
            depart_time TEXT,
            arrive_location TEXT,
            arrive_time TEXT,
            checkin_open TEXT,
            checkin_close TEXT,
            shuttle TEXT,
            village_dest TEXT,
            direction TEXT
        )
    """)

    conn.executemany("""
        INSERT INTO flights (
            id, site, day_of_week, flight_number, aircraft,
            depart_location, depart_time, arrive_location, arrive_time,
            checkin_open, checkin_close, shuttle, village_dest, direction
        ) VALUES (
            :id, :site, :day_of_week, :flight_number, :aircraft,
            :depart_location, :depart_time, :arrive_location, :arrive_time,
            :checkin_open, :checkin_close, :shuttle, :village_dest, :direction
        )
    """, flights)

    conn.commit()
    conn.close()
    print(f"Done — {len(flights)} flights loaded.")


if __name__ == "__main__":
    build()
