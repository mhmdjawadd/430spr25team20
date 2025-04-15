from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from .base import Base

class Patient(Base):
    __tablename__ = 'patients'
    
    patient_id = Column(Integer, ForeignKey('users.user_id'), primary_key=True)
    date_of_birth = Column(DateTime)
    emergency_contact_name = Column(String(100))
    emergency_contact_phone = Column(String(20))
    doctor_id = Column(Integer, ForeignKey('doctors.doctor_id'))  
    bill = Column(Integer, default=0)  # Total bill amount
    insurance_id = Column(Integer, ForeignKey('insurance.patient_id'))  # Link to insurance
    caregiver_id = Column(Integer, ForeignKey('users.user_id'))  # Link to caregiver user
    needs_caregiver = Column(Boolean, default=False)  # Flag for patients who need caregivers

    # Relationships
    user = relationship("User", back_populates="patient", foreign_keys=[patient_id])
    medical_records = relationship("MedicalRecord", back_populates="patient")
    doctor = relationship("Doctor", back_populates="patients")
    appointments = relationship("Appointment", back_populates="patient")
    insurance = relationship("Insurance", back_populates="patient", uselist=False, foreign_keys="Insurance.patient_id")
    
    
    def __repr__(self):
        return f"<Patient(id={self.patient_id})>"
        
    def full_name(self):
        """Get the patient's full name from the associated user"""
        if hasattr(self, 'user') and self.user:
            return f"{self.user.first_name} {self.user.last_name}"
        return "Unknown Patient"