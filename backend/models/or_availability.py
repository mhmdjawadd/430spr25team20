from sqlalchemy import  Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import  relationship
from .base import * 

class ORAvailability(Base):
    __tablename__ = 'or_availability'
    
    or_id = Column(Integer, primary_key=True)
    surgeon_id = Column(Integer, ForeignKey('doctors.doctor_id'), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    status = Column(String(20), default='available')
    
    # Relationships
    surgeon = relationship("Doctor", back_populates="or_availability")
