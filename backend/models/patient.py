from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from .base import Base

class Patient(Base):
    __tablename__ = 'patients'
    
    patient_id = Column(Integer, ForeignKey('users.user_id'), primary_key=True)
    date_of_birth = Column(DateTime)
    emergency_contact_name = Column(String(100))
    emergency_contact_phone = Column(String(20))
    insurance_id = Column(Integer, ForeignKey('insurance.insurance_id'))
    
    # Relationships
    user = relationship("User", back_populates="patient")
    medical_records = relationship("MedicalRecord", back_populates="patient")
    doctor = relationship("Doctor", back_populates="patients")
    chronic_conditions = relationship("ChronicCondition", back_populates="patient")
    
    def __repr__(self):
        return f"<Patient(id={self.patient_id})>"