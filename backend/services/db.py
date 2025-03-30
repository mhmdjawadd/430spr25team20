import os
from flask_sqlalchemy import SQLAlchemy

# Create SQLAlchemy instance
db = SQLAlchemy()

def init_db(app):
    """Initialize the database with the Flask app"""
    # Configure Flask app for SQLAlchemy
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///nabad.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize app with SQLAlchemy
    db.init_app(app)
    
    # Create tables
    with app.app_context():
        # Import all models to ensure they're registered with SQLAlchemy
        # Import your models here
        from  models.user import User
        from  models.doctor import Doctor
        from  models.patient import Patient
        from  models.medical_record.appointment import Appointment
        from  models.message import Message
        from  models.notification import Notification
        from  models.or_availability import ORAvailability
        
        # Medical records models
        from models.medical_record.medical_record import MedicalRecord
        from models.medical_record.perscription import Prescription
        from models.medical_record.refferal import Referral
        from models.medical_record.insurance import Insurance
        
        # Create all tables
        db.create_all()
        print("Database tables created successfully!")

    return db