from sqlalchemy import  Column, Integer, String, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship

from base import * 

class Insurance(Base):
    __tablename__ = 'insurance'
    
    insurance_id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey('patients.patient_id'), nullable=False)
    provider_name = Column(String(100), nullable=False)
    policy_number = Column(String(50), nullable=False)
    coverage_details = Column(JSON)  # or JSONB for PostgreSQL
    is_valid = Column(Boolean, default=True)
    
    # Relationships
    patients = relationship("Patient", back_populates="insurance")
