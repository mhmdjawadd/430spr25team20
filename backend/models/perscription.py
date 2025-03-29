from sqlalchemy import  Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from base import * 

class Prescription(Base):
    __tablename__ = 'prescriptions'
    
    prescription_id = Column(Integer, primary_key=True)
    record_id = Column(Integer, ForeignKey('medical_records.record_id'), nullable=False)
    medication_name = Column(String(100), nullable=False)
    dosage = Column(String(50), nullable=False)
    instructions = Column(String)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime)
    
    # Relationships
    medical_record = relationship("MedicalRecord", back_populates="prescriptions")
