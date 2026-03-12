from sqlalchemy import create_engine, Column, Integer, String, Date, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "")

# Railway sometimes provides postgres:// instead of postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# --- Models ---

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Staff(Base):
    __tablename__ = "staff"
    id = Column(Integer, primary_key=True, index=True)
    emp_number = Column(String, unique=True, index=True)
    full_name = Column(String, nullable=False)
    role = Column(String)  # Technician, Relief
    hub = Column(String)   # EAST, WEST, NORTH etc.
    roster_type = Column(String)  # 8/6, casual
    roster_expiry = Column(Date, nullable=True)
    village = Column(String)  # JV, KV, CB
    site_code = Column(String)  # CC, SOL, ELI etc.
    is_active = Column(Boolean, default=True)


class Swing(Base):
    __tablename__ = "swings"
    id = Column(Integer, primary_key=True, index=True)
    staff_emp = Column(String, index=True)
    fly_in_date = Column(Date, nullable=False)
    fly_out_date = Column(Date, nullable=False)
    fly_in_flight = Column(String)   # e.g. QF2924
    fly_out_flight = Column(String)  # e.g. QF2925
    village = Column(String)
    room_ref = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class RosterOverride(Base):
    __tablename__ = "roster_overrides"
    id = Column(Integer, primary_key=True, index=True)
    staff_emp = Column(String, index=True)
    date = Column(Date, nullable=False)
    status = Column(String, nullable=False)  # AL, LWOP, etc.
    notes = Column(Text, nullable=True)
    created_by = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


# --- DB init ---

def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
