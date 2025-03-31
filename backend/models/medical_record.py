from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from .base import *


class MedicalRecord(Base):
    __tablename__ = 'medical_records'
    
    record_id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey('patients.patient_id'), nullable=False)
    description = Column(String, nullable=False)
    
    # Relationships
    patient = relationship("Patient", back_populates="medical_records") # to see the records per patient
    doctor = relationship("Doctor", back_populates="medical_records") # to see the records oer doctor
    


