from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from .base import * 

class Notification(Base):
    __tablename__ = 'notifications'
    
    notification_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    appointment_id = Column(Integer, ForeignKey('appointments.appointment_id'))
    message = Column(String, nullable=False)
    scheduled_time = Column(DateTime, nullable=False)
    status = Column(String(20), default='pending')
    
    # Relationships
    user = relationship("User")
    appointment = relationship("Appointment", back_populates="notifications")
