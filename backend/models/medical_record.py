from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum 
from sqlalchemy.orm import relationship

from base import *


class MedicalRecord(Base):
    __tablename__ = 'medical_records'
    
    record_id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey('patients.patient_id'), nullable=False)
    doctor_id = Column(Integer, ForeignKey('doctors.doctor_id'), nullable=False)
    record_type = Column(Enum(RecordType), nullable=False)
    description = Column(String, nullable=False)
    file_path = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    patient = relationship("Patient", back_populates="medical_records")
    doctor = relationship("Doctor", back_populates="medical_records")
    prescriptions = relationship("Prescription", back_populates="medical_record")

