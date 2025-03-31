from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
import os
from backend.services.therapistService import TherapistController
from services import AuthController, AppointmentController
from services.notificationService import NotificationController
from services.medicalRecordService import MedicalRecordController
from services.prescriptionService import PrescriptionController
from services.conditionService import ConditionController
from services.availabilityService import AvailabilityController
from services.emergencyService import EmergencyController
from services.doctorService import DoctorController
from services.calendarService import CalendarSyncController
from services.nurseService import NurseController

# Initialize Flask application
app = Flask(__name__)
CORS(app)  # Enable CORS

# Configuration
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")
app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "dev-jwt-secret")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = 3600  # 1 hour

# Initialize JWT
jwt = JWTManager(app)

# JWT Configuration
@jwt.user_identity_loader
def user_identity_lookup(user):
    return user.user_id

@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    from models.user import User  # Local import to avoid circular imports
    identity = jwt_data["sub"]
    return User.query.get(identity)

# Initialize database
from services.db import init_db
db =init_db(app)  # Initialize with our Flask app

    

@app.route('/login', methods=['POST'])
def login_route():
    """User login endpoint"""
    return AuthController.login()

@app.route('/signup', methods=['POST'])
def signup_route():
    """User registration endpoint"""
    return AuthController.signup()

@app.route('/appointments', methods=['GET'])
def get_appointments():
    """Get appointments based on user role"""
    return AppointmentController.get_appointments()

@app.route('/appointments', methods=['POST'])
def create_appointments():
    """create appointments """
    return AppointmentController.create_appointment()

@app.route('/referrals', methods=['POST'])
def create_referral():
    """Create a new referral"""
    return AppointmentController.create_referral()

@app.route('/referrals', methods=['POST'])
@jwt_required()
def create_new_referral():
    """Create a new referral to a specialist"""
    return AppointmentController.create_referral()

@app.route('/referrals', methods=['GET'])
def get_referrals():
    """Get referrals based on user role"""
    return AppointmentController.get_referrals()

@app.route('/notifications', methods=['GET'])
@jwt_required()
def get_user_notifications():
    """Get notifications for the current user"""
    return NotificationController.get_notifications()

@app.route('/notifications/<int:notification_id>/read', methods=['POST'])
def mark_notification_read(notification_id):
    """Mark a notification as read"""
    return NotificationController.mark_notification_read(notification_id)

@app.route('/medical-records', methods=['GET'])
def get_medical_records():
    """Get medical records for a patient"""
    return MedicalRecordController.get_patient_records()

@app.route('/medical-records', methods=['POST'])
def create_medical_record():
    """Create a new medical record"""
    return MedicalRecordController.create_medical_record()

@app.route('/appointments/history', methods=['GET'])
def get_appointment_history():
    """Get filtered appointment history"""
    return AppointmentController.get_appointment_history()

# Add scheduler for reminders (uncomment when you add a task scheduler like APScheduler)
# @app.route('/api/admin/schedule-reminders', methods=['POST'])
# def schedule_reminders():
#     """Admin endpoint to trigger reminder scheduling"""
#     return NotificationController.schedule_appointment_reminders()

# Add these routes for chronic condition management
@app.route('/conditions', methods=['GET'])
def get_conditions():
    """Get chronic conditions for a patient"""
    return ConditionController.get_conditions()

@app.route('/conditions', methods=['POST'])
def create_condition():
    """Create a new chronic condition record"""
    return ConditionController.create_condition()

@app.route('/conditions/track', methods=['POST'])
def track_condition():
    """Add a tracking record for a chronic condition"""
    return ConditionController.track_condition()

# Add these routes for prescription management
@app.route('/prescriptions', methods=['GET'])
def get_prescriptions():
    """Get prescriptions for a patient"""
    return PrescriptionController.get_prescriptions()

@app.route('/prescriptions/refill', methods=['POST'])
def request_refill():
    """Request a prescription refill"""
    return PrescriptionController.request_refill()

# Add this route for doctor availability
@app.route('/availability', methods=['GET'])
def check_availability():
    """Check doctor availability"""
    return AvailabilityController.check_availability()

@app.route('/availability', methods=['POST'])
def set_availability():
    """Set doctor availability slots"""
    return AvailabilityController.set_availability()

# Add this route for patient schedule visibility
@app.route('/patient/schedule', methods=['GET'])
def get_patient_schedule():
    """Get patient's consolidated schedule"""
    return AppointmentController.get_patient_schedule()

# Add these routes for emergency features
@app.route('/appointments/emergency', methods=['POST'])
def create_emergency_appointment():
    """Create an emergency appointment with priority"""
    return EmergencyController.create_emergency_appointment()

@app.route('/availability/emergency', methods=['GET'])
def check_emergency_availability():
    """Check immediate availability for emergency care"""
    return EmergencyController.check_emergency_availability()

@app.route('/appointments/prioritize', methods=['POST'])
def prioritize_appointment():
    """Mark an appointment as priority and potentially reschedule"""
    return AppointmentController.prioritize_appointment()

@app.route('/emergency/slots', methods=['GET'])
def get_emergency_slots():
    """Get slots available for emergency appointments"""
    return AvailabilityController.get_emergency_slots()

# Add these routes for doctor features
@app.route('/doctor/patient-history', methods=['GET'])
def get_patient_history():
    """Get integrated patient history for doctors"""
    return DoctorController.get_patient_history()

@app.route('/doctor/schedule', methods=['GET'])
def get_doctor_schedule():
    """Get doctor's daily schedule"""
    return DoctorController.get_doctor_schedule()

@app.route('/referrals/manage', methods=['POST'])
def manage_referral():
    """Update referral status"""
    return DoctorController.manage_referral()

# Calendar sync routes
@app.route('/calendar/connect', methods=['GET'])
def start_calendar_oauth():
    """Start OAuth flow to connect calendar"""
    return CalendarSyncController.start_oauth_flow()

@app.route('/calendar/oauth2callback', methods=['GET'])
def calendar_oauth_callback():
    """Handle OAuth callback from calendar provider"""
    return CalendarSyncController.oauth2callback()

@app.route('/calendar/sync', methods=['POST'])
def sync_calendar():
    """Sync appointments to calendar"""
    return CalendarSyncController.sync_appointments()

# Add these routes for nurse features
@app.route('/nurse/schedule', methods=['GET'])
def get_nurse_schedule():
    """Get nurse's daily schedule"""
    return NurseController.get_nurse_schedule()

@app.route('/care-plans', methods=['GET'])
def get_care_plans():
    """Get care plans for a patient or assigned to a nurse"""
    return NurseController.get_care_plans()

@app.route('/care-plans', methods=['POST'])
def create_care_plan():
    """Create a new care plan"""
    return NurseController.create_care_plan()

@app.route('/care-plans/update', methods=['POST'])
def update_care_plan():
    """Update an existing care plan"""
    return NurseController.update_care_plan()

# Add these routes for therapy session management
@app.route('/therapy/sessions', methods=['GET'])
def get_therapy_sessions():
    """Get therapy sessions for therapist or patient"""
    return TherapistController.get_therapy_sessions()

@app.route('/therapy/sessions', methods=['POST'])
def schedule_therapy_session():
    """Schedule a new therapy session with optional recurrence"""
    return TherapistController.schedule_therapy_session()

@app.route('/specialist/referrals', methods=['GET'])
@jwt_required()
def get_specialist_referrals():
    """Get referrals directed to a specialist"""
    return SpecialistController.get_specialty_referrals()

if __name__ == "__main__":
    app.run(debug=True)