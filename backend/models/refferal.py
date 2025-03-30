from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime , relationship, Enum
from base import * 

class Referral(Base):
    __tablename__ = 'referrals'
    
    referral_id = Column(Integer, primary_key=True)
    referring_doctor_id = Column(Integer, ForeignKey('doctors.doctor_id'), nullable=False)
    specialist_id = Column(Integer, ForeignKey('doctors.doctor_id'), nullable=False)
    patient_id = Column(Integer, ForeignKey('patients.patient_id'), nullable=False)
    reason = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(Enum(AppointmentStatus), nullable=False, default=AppointmentStatus.SCHEDULED )


    medical_record= relationship("MedicalRecord", back_populates="referrals")
