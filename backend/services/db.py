import os
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text


db = SQLAlchemy()

def init_db(app , reset = False):
    """Initialize the database with the Flask app"""
    # Configure Flask app for SQLAlchemy
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/430lecture')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize app with SQLAlchemy
    db.init_app(app)
    
    # Create tables
    with app.app_context():
        if reset:
            # Drop all tables if reset is True
                # This will safely drop all tables respecting dependencies
            db.session.execute(text("DROP SCHEMA public CASCADE;"))
            db.session.execute(text("CREATE SCHEMA public;"))
            db.session.commit()
            db.drop_all()
            print("All tables dropped successfully!")
            
        # Import all models to ensure they're registered with SQLAlchemy
        # Import your models here
        from  models.user import User
        from  models.doctor import Doctor
        from  models.patient import Patient
        from  models.appointment import Appointment
        from  models.message import Message
        from  models.notification import Notification
        
        
        # Medical records models
        from models.medical_record import MedicalRecord
        from models.insurance import Insurance
        
        # Create all tables
        db.create_all()
        print("Database tables created successfully!")

    return db