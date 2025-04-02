from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum, Text
from sqlalchemy.orm import relationship
from .base import *


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




class Appointment(Base):
    __tablename__ = 'appointments'
    
    appointment_id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey('patients.patient_id'), nullable=False)
    doctor_id = Column(Integer, ForeignKey('doctors.doctor_id'), nullable=False)
    date_time = Column(DateTime, nullable=False)
    type = Column(Enum(AppointmentType), nullable=False, default=AppointmentType.REGULAR)
    status = Column(Enum(AppointmentStatus), nullable=False, default=AppointmentStatus.SCHEDULED)
    reason = Column(String, nullable=True)  # Reason for the appointment
    recurrence_pattern = Column(Enum(RecurrencePattern), nullable=False, default=RecurrencePattern.NONE)
       
    
    # Relationships
    patient = relationship("Patient", back_populates="appointments")
    notifications = relationship("Notification", back_populates="appointment")
    doctor = relationship("Doctor", back_populates="appointments")
    



