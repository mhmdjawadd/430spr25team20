from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
import os
from services import AuthController
from services.appointmentService import AppointmentController
from services.insuranceService import InsuranceController
from services.caregiverService import CaregiverController
from services.messagingService import MessagingController
from services.notificationService import NotificationController

"""
from backend.services.therapistService import TherapistController
from services.medicalRecordService import MedicalRecordController
from services.prescriptionService import PrescriptionController
from services.conditionService import ConditionController
from services.availabilityService import AvailabilityController
from services.emergencyService import EmergencyController
from services.doctorService import DoctorController
from services.calendarService import CalendarSyncController
from services.nurseService import NurseController
"""

# Initialize Flask application
app = Flask(__name__)
CORS(app)  # Enable CORS

# Configuration
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")
app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "dev-jwt-secret")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = 3600  # 1 hour

# Initialize JWT
jwt = JWTManager(app)

# Initialize database
from services.db import init_db
db =init_db(app,True)  # Initialize with our Flask app

@jwt.user_identity_loader
def user_identity_lookup(user):
    return str(user.user_id)  # Convert user_id to a string

@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    from models.user import User  # Local import to avoid circular imports
    identity = jwt_data["sub"]
    return User.query.get(int(identity))  # Convert back to integer when querying


# Authentication routes
@app.route('/login', methods=['POST'])
def login_route():
    """User login endpoint"""
    return AuthController.login()

@app.route('/signup', methods=['POST'])
def signup_route():
    """User registration endpoint"""
    return AuthController.signup()

# Appointment routes
@app.route('/appointments', methods=['GET'])
@jwt_required()
def get_doctor_availability():
    """Get available appointment slots for a doctor on a specific date"""
    return AppointmentController.get_doctor_availability()

@app.route('/appointments', methods=['POST'])
@jwt_required()
def book_appointment():
    """Book an appointment with a doctor"""
    return AppointmentController.book_appointment()

@app.route('/appointments/recurring/<int:appointment_id>', methods=['GET'])
@jwt_required()
def get_recurring_appointments(appointment_id):
    """Get all recurring appointments in a series"""
    return AppointmentController.get_recurring_appointments(appointment_id)

@app.route('/appointments/auto-schedule', methods=['POST'])
@jwt_required()
def auto_schedule_appointments():
    """Automatically schedule recurring appointments (receptionist only)"""
    return AppointmentController.auto_schedule_appointments()

# Insurance routes
@app.route('/insurance', methods=['GET'])
@jwt_required()
def get_insurance():
    """Get insurance information for a patient"""
    return InsuranceController.get_patient_insurance()

@app.route('/insurance', methods=['POST'])
@jwt_required()
def update_insurance():
    """Update insurance information for a patient"""
    return InsuranceController.update_patient_insurance()

@app.route('/insurance/verify', methods=['POST'])
@jwt_required()
def verify_insurance():
    """Verify insurance coverage for a specific doctor/service"""
    return InsuranceController.verify_coverage()

# Caregiver routes
@app.route('/caregivers/assign', methods=['POST'])
@jwt_required()
def assign_caregiver():
    """Assign a caregiver to a patient"""
    return CaregiverController.assign_caregiver()

@app.route('/caregivers/patients', methods=['GET'])
@jwt_required()
def get_caregiver_patients():
    """Get all patients for a caregiver"""
    return CaregiverController.get_caregiver_patients()

@app.route('/patients/<int:patient_id>/caregiver', methods=['GET'])
@jwt_required()
def get_patient_caregiver(patient_id):
    """Get caregiver information for a patient"""
    return CaregiverController.get_patient_caregiver(patient_id)

@app.route('/emergency/alert', methods=['POST'])
@jwt_required()
def send_emergency_alert():
    """Send an emergency alert to a patient's caregiver"""
    return CaregiverController.send_emergency_alert()

@app.route('/patients/<int:patient_id>/medical', methods=['GET'])
@jwt_required()
def get_patient_medical_data(patient_id):
    """Get a patient's medical data for caregiver access"""
    return CaregiverController.get_patient_medical_data(patient_id)

@app.route('/caregivers/emergency-alerts', methods=['GET'])
@jwt_required()
def get_caregiver_emergency_alerts():
    """Get all emergency alerts for a caregiver"""
    return CaregiverController.get_emergency_alerts()

# Messaging routes
@app.route('/messages', methods=['POST'])
@jwt_required()
def send_message_route():
    """Send a message to another user"""
    return MessagingController.send_message()

@app.route('/messages/conversations', methods=['GET'])
@jwt_required()
def get_conversations_route():
    """Get all conversations for the current user"""
    return MessagingController.get_conversations()

@app.route('/messages/<int:user_id>', methods=['GET'])
@jwt_required()
def get_messages_route(user_id):
    """Get all messages between the current user and another user"""
    return MessagingController.get_messages(user_id)

# Notification routes
@app.route('/notifications', methods=['GET'])
@jwt_required()
def get_notifications():
    """Get all notifications for the current user"""
    return NotificationController.get_user_notifications()

@app.route('/notifications/<int:notification_id>/read', methods=['POST'])
@jwt_required()
def mark_notification_read(notification_id):
    """Mark a notification as read"""
    return NotificationController.mark_notification_read(notification_id)

if __name__ == "__main__":
    app.run(debug=True)