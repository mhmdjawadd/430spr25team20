from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

class ChronicCondition(Base):
    __tablename__ = 'chronic_conditions'
    
    condition_id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey('patients.patient_id'), nullable=False)
    name = Column(String(100), nullable=False)
    diagnosis_date = Column(DateTime, default=datetime.utcnow)
    description = Column(Text)
    
    # Relationships
    patient = relationship("Patient", back_populates="chronic_conditions")
    tracking_records = relationship("ConditionTracking", back_populates="condition")


class ConditionTracking(Base):
    __tablename__ = 'condition_tracking'
    
    tracking_id = Column(Integer, primary_key=True)
    condition_id = Column(Integer, ForeignKey('chronic_conditions.condition_id'), nullable=False)
    tracked_date = Column(DateTime, default=datetime.utcnow)
    severity = Column(Float)  # Scale 1-10
    notes = Column(Text)
    vital_signs = Column(Text)  # JSON string of vital signs relevant to condition
    
    # Relationships
    condition = relationship("ChronicCondition", back_populates="tracking_records")