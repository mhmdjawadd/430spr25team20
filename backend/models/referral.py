from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Boolean
from sqlalchemy.orm import relationship
from .base import *

class Referral(Base):
    __tablename__ = 'referrals'
    
    referral_id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey('patients.patient_id'), nullable=False)
    referring_doctor_id = Column(Integer, ForeignKey('doctors.doctor_id'), nullable=False)
    specialist_id = Column(Integer, ForeignKey('doctors.doctor_id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    reason = Column(Text, nullable=False)
    notes = Column(Text)
    status = Column(String(20), default="pending")  # "pending", "accepted", "completed", "rejected", "cancelled"
    priority = Column(String(20), default="medium")  # "low", "medium", "high", "urgent"
    appointment_id = Column(Integer, ForeignKey('appointments.appointment_id'))
    is_read = Column(Boolean, default=False)  # For tracking if specialist has read the referral
    
    # Relationships
    patient = relationship("Patient", foreign_keys=[patient_id])
    referring_doctor = relationship("Doctor", foreign_keys=[referring_doctor_id], back_populates="sent_referrals")
    specialist = relationship("Doctor", foreign_keys=[specialist_id], back_populates="received_referrals")
    appointment = relationship("Appointment")