from sqlalchemy import create_engine, Column, Integer, String, Date, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


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
    role = Column(String)
    hub = Column(String)
    roster_type = Column(String)
    roster_expiry = Column(Date, nullable=True)
    village = Column(String)
    site_code = Column(String)
    is_active = Column(Boolean, default=True)


class Swing(Base):
    __tablename__ = "swings"
    id = Column(Integer, primary_key=True, index=True)
    staff_emp = Column(String, index=True)
    fly_in_date = Column(Date, nullable=False)
    fly_out_date = Column(Date, nullable=False)
    fly_in_flight = Column(String)
    fly_out_flight = Column(String)
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
    status = Column(String, nullable=False)  # AL, LWOP
    notes = Column(Text, nullable=True)
    created_by = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


class ChangeRequest(Base):
    __tablename__ = "change_requests"
    id = Column(Integer, primary_key=True, index=True)
    staff_emp = Column(String, index=True)
    swing_id = Column(Integer, nullable=True)
    change_type = Column(String, nullable=False)
    effective_date = Column(Date, nullable=False)
    new_date = Column(Date, nullable=True)
    reason = Column(Text, nullable=False)
    status = Column(String, default="requested")  # requested, booked, confirmed, notified, complete
    workflow_ref = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    submitted_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
