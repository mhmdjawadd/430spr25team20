from sqlalchemy.ext.declarative import declarative_base
import enum
from services.db import db

class Base(db.Model):
    """Base model class using Flask-SQLAlchemy"""
    __abstract__ = True  # Prevents table creation for Base
    
    # Add common columns or methods here
    
    def save(self):
        db.session.add(self)
        db.session.commit()
