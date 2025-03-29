from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from base import * 

class Referral(Base):
    __tablename__ = 'referrals'
    
    referral_id = Column(Integer, primary_key=True)
    referring_doctor_id = Column(Integer, ForeignKey('doctors.doctor_id'), nullable=False)
    specialist_id = Column(Integer, ForeignKey('doctors.doctor_id'), nullable=False)
    patient_id = Column(Integer, ForeignKey('patients.patient_id'), nullable=False)
    reason = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
