from datetime import datetime
from sqlalchemy import  Column, Integer, String, DateTime, Enum
from sqlalchemy.orm import relationship
from .base import Base 
import enum
# Enums
class UserRole(enum.Enum):
    PATIENT = "patient"
    DOCTOR = "doctor"
    NURSE = "nurse"
    SURGEON = "surgeon"
    THERAPIST = "therapist"
    RECEPTIONIST = "receptionist"
    CAREGIVER = "caregiver"

# Tables
class User(Base):
    __tablename__ = 'users'
    
    user_id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    phone = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    patient = relationship("Patient", uselist=False, back_populates="user", foreign_keys="Patient.patient_id")
    doctor = relationship("Doctor", uselist=False, back_populates="user")
    sent_messages = relationship("Message", foreign_keys="Message.sender_id", back_populates="sender")
    received_messages = relationship("Message", foreign_keys="Message.receiver_id", back_populates="receiver")
    # Add a relationship for patients where this user is a caregiver
    patients_as_caregiver = relationship("Patient", foreign_keys="Patient.caregiver_id", backref="caregiver_user")

    def full_name(self):
        """Return the user's full name"""
        return f"{self.first_name} {self.last_name}"