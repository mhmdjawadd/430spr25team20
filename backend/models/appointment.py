from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum, Text, Float, Boolean
from sqlalchemy.orm import relationship
from .base import *


class AppointmentType(enum.Enum):
    REGULAR = "regular"
    RECURRING = "recurring"
    EMERGENCY = "emergency"


class RecurrencePattern(enum.Enum):
    NONE = "none"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"


class Appointment(Base):
    __tablename__ = 'appointments'
    
    appointment_id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey('patients.patient_id'), nullable=False)
    doctor_id = Column(Integer, ForeignKey('doctors.doctor_id'), nullable=False)
    date_time = Column(DateTime, nullable=False)
    type = Column(Enum(AppointmentType), nullable=False, default=AppointmentType.REGULAR)
    recurrence_pattern = Column(Enum(RecurrencePattern), nullable=False, default=RecurrencePattern.NONE)
    
    # Billing and insurance fields
    base_cost = Column(Float, default=100.00)  # Base cost of appointment
    insurance_verified = Column(Boolean, default=False)  # Whether insurance was verified
    insurance_coverage_amount = Column(Float, default=0.00)  # Amount covered by insurance
    patient_responsibility = Column(Float, default=0.00)  # Amount patient needs to pay
    
    # Relationships
    patient = relationship("Patient", back_populates="appointments")
    notifications = relationship("Notification", back_populates="appointment")
    doctor = relationship("Doctor", back_populates="appointments")




