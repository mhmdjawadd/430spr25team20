
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from base import *

class Patient(Base):
    __tablename__ = 'patients'
    
    patient_id = Column(Integer, ForeignKey('users.user_id'), primary_key=True)
    date_of_birth = Column(DateTime)
    emergency_contact_name = Column(String(100))
    emergency_contact_phone = Column(String(20))
    insurance_id = Column(Integer, ForeignKey('insurance.insurance_id')) # insurance = 0 => no insurance
    
    # Relationships
    user = relationship("User", back_populates="patient")
    medical_records = relationship("MedicalRecord", back_populates="patient")
    doctor = relationship("Doctor", back_populates="patients")

    # all can be null expect user since when creating a patient we dont need to have them all
    
    def __repr__(self):
        return f"<Patient(id={self.id}, name={self.first_name} {self.last_name})>"