from sqlalchemy import  Column, Integer, String, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship

from .base import * 

class Insurance(Base):
    __tablename__ = 'insurance'
    
    insurance_id = Column(Integer, primary_key=True)
    provider_name = Column(String(100), nullable=False)
    coverage_details = Column(String)  
    is_valid = Column(Boolean, default=True)
    
    # Relationships
    patients = relationship("Patient", back_populates="insurance")
    
    
    
    
