from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from .base import Base

class CalendarIntegration(Base):
    __tablename__ = 'calendar_integrations'
    
    integration_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    provider = Column(String(50), nullable=False)  # google, outlook, etc.
    oauth_state = Column(String(100))
    access_token = Column(Text)
    refresh_token = Column(Text)
    token_expiry = Column(DateTime)
    token_uri = Column(String(255))
    client_id = Column(String(255))
    client_secret = Column(String(255))
    scopes = Column(Text)  # JSON string of scopes
    created_at = Column(DateTime, nullable=False)
    connected_at = Column(DateTime)
    
    # Relationships
    user = relationship("User")