from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from base import *

class Doctor(Base):
    __tablename__ = 'doctors'
    
    doctor_id = Column(Integer, ForeignKey('users.user_id'), primary_key=True)
    specialty = Column(String(100), nullable=False)
    license_number = Column(String(50), unique=True, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="doctor")
    appointments = relationship("Appointment", back_populates="provider")
    medical_records = relationship("MedicalRecord", back_populates="doctor")
    or_availability = relationship("ORAvailability", back_populates="surgeon")
