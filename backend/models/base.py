from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
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
    CLINIC_MANAGER = "clinic_manager"
    CAREGIVER = "caregiver"
    BILLING_STAFF = "billing_staff"

class AppointmentType(enum.Enum):
    REGULAR = "regular"
    RECURRING = "recurring"
    EMERGENCY = "emergency"

class RecordType(enum.Enum):
    CONDITION = "condition"
    PRESCRIPTION = "prescription"
    LAB_RESULT = "lab_result"
    PROGRESS_NOTE = "progress_note"


# Create engine and tables
engine = create_engine('postgresql://user:password@localhost/nabad')
Base.metadata.create_all(engine)