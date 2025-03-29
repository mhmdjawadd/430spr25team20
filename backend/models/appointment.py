from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON,  Enum
from sqlalchemy.orm import relationship, backref
from base import * 


class Appointment(Base):
    __tablename__ = 'appointments'
    
    appointment_id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey('patients.patient_id'), nullable=False)
    provider_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    date_time = Column(DateTime, nullable=False)
    duration = Column(Integer, nullable=False)  # Minutes
    type = Column(Enum(AppointmentType), nullable=False)
    status = Column(String(20), default='scheduled')
    reason = Column(String)
    recurrence_pattern = Column(JSON)  # or JSONB for PostgreSQL
    parent_appointment_id = Column(Integer, ForeignKey('appointments.appointment_id'))
    
    # Relationships
    patient = relationship("Patient", back_populates="appointments")
    provider = relationship("User", foreign_keys=[provider_id])
    notifications = relationship("Notification", back_populates="appointment")
    children = relationship("Appointment", backref=backref('parent', remote_side=[appointment_id]))
