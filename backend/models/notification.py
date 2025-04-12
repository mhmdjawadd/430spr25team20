from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from .base import * 

class Notification(Base):
    __tablename__ = 'notifications'
    
    notification_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    appointment_id = Column(Integer, ForeignKey('appointments.appointment_id'))
    message = Column(String, nullable=False)
    scheduled_time = Column(DateTime, nullable=False)
    is_read = Column(Boolean, default=False)
    status = Column(String, default='normal')  # normal, emergency, etc.
    
    # Relationships
    user = relationship("User")
    appointment = relationship("Appointment", back_populates="notifications")
