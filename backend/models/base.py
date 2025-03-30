from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import declarative_base
import enum

Base = declarative_base()
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



