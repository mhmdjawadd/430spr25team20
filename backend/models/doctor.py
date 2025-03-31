from sqlalchemy import Column, Enum, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from .base import *

class Doctor(Base):
    __tablename__ = 'doctors'
    
    doctor_id = Column(Integer, ForeignKey('users.user_id'), primary_key=True)
    specialty = Column(Enum(UserRole), nullable=False) #  nurse ,  doctor , surgeon , therapist
    # Relationships
    user = relationship("User", back_populates="doctor")
    appointments = relationship("Appointment", back_populates="doctor")
    or_availability = relationship("ORAvailability", back_populates="surgeon")
    patients = relationship("Patient", back_populates="doctor")
    medical_records = relationship("MedicalRecord", back_populates="doctor") # too see the records they created
