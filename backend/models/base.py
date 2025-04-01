from sqlalchemy.ext.declarative import declarative_base
import enum
from services.db import db

class Base(db.Model):
    """Base model class using Flask-SQLAlchemy"""
    __abstract__ = True  # Prevents table creation for Base
    
    # Add common columns or methods here
    
    def save(self):
        db.session.add(self)
        db.session.commit()

# Enums
class UserRole(enum.Enum):
    PATIENT = "patient"
    DOCTOR = "doctor"
    NURSE = "nurse"
    SURGEON = "surgeon"
    THERAPIST = "therapist"
    RECEPTIONIST = "receptionist"
    CAREGIVER = "caregiver"

class AppointmentType(enum.Enum):
    REGULAR = "regular"
    RECURRING = "recurring"
    EMERGENCY = "emergency"

class AppointmentStatus(enum.Enum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    CHECKED_IN = "checked_in"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    RESCHEDULED = "rescheduled"

class RecurrencePattern(enum.Enum):
    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"



