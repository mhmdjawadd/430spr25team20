from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
import os
from services import AuthController, ReferralController
from services.appointmentService import AppointmentController
from services.insuranceService import InsuranceController
from services.caregiverService import CaregiverController
from services.messagingService import MessagingController
from services.notificationService import NotificationController
from services.reminderService import ReminderController


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
db =init_db(app)  # Initialize with our Flask app

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

# Doctor routes
@app.route('/doctors', methods=['GET', 'OPTIONS'])
@jwt_required(optional=True)
def get_doctors():
    """Get a list of all doctors"""
    from models.user import User
    from models.doctor import Doctor
    from models.user import UserRole
    from flask import jsonify
    
    try:
        # Query all doctors
        doctors = Doctor.query.all()
        
        # Format the response
        result = []
        for doctor in doctors:
            user = User.query.filter_by(user_id=doctor.doctor_id).first()
            if user:
                result.append({
                    'id': doctor.doctor_id,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'email': user.email,
                    "specialty": doctor.specialty.name,
                    
                })
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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

@app.route('/appointments/cancel', methods=['PUT'])
@jwt_required()
def cancel_appointment():
    """Cancel an existing appointment and notify all parties"""
    return AppointmentController.cancel_appointment()

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

# Reminder routes - NEW
@app.route('/reminders/schedule', methods=['POST'])
@jwt_required()
def schedule_appointment_reminders():
    """Schedule reminders for upcoming appointments"""
    return ReminderController.schedule_appointment_reminders()

@app.route('/reminders/availability', methods=['POST'])
@jwt_required()
def notify_cancellation_availability():
    """Notify patients about cancellations and last-minute availabilities"""
    return ReminderController.notify_cancellation_availabilities()

@app.route('/caregivers/appointment-reminders', methods=['GET'])
@jwt_required()
def get_caregiver_appointment_reminders():
    """Get all appointment reminders for elderly patients of a caregiver"""
    return ReminderController.get_caregiver_appointment_reminders()

# Referral routes
@app.route('/referrals', methods=['POST'])
@jwt_required()
def create_referral_route():
    """Create a new referral from a doctor to a specialist"""
    return ReferralController.create_referral()

@app.route('/referrals/received', methods=['GET'])
@jwt_required()
def get_received_referrals_route():
    """Get all referrals received by the current specialist"""
    return ReferralController.get_received_referrals()

@app.route('/referrals/sent', methods=['GET'])
@jwt_required()
def get_sent_referrals_route():
    """Get all referrals sent by the current doctor"""
    return ReferralController.get_sent_referrals()

@app.route('/referrals/<int:referral_id>', methods=['GET'])
@jwt_required()
def get_referral_details_route(referral_id):
    """Get detailed information about a specific referral"""
    return ReferralController.get_referral_details(referral_id)

@app.route('/referrals/<int:referral_id>/status', methods=['PUT'])
@jwt_required()
def update_referral_status_route(referral_id):
    """Update the status of a referral (accept, reject, complete, etc.)"""
    return ReferralController.update_referral_status(referral_id)

@app.route('/patients/<int:patient_id>/referrals', methods=['GET'])
@jwt_required()
def get_patient_referrals_route(patient_id):
    """Get all referrals for a specific patient"""
    return ReferralController.get_patient_referrals(patient_id)

@app.route('/specialists', methods=['GET'])
@jwt_required()
def get_specialists_list_route():
    """Get a list of specialists available for referrals"""
    return ReferralController.get_specialists_list()

@app.route('/referrals/<int:referral_id>/messages', methods=['POST'])
@jwt_required()
def add_message_to_referral_route(referral_id):
    """Add a communication message to an existing referral"""
    return ReferralController.add_message_to_referral(referral_id)

if __name__ == "__main__":
    app.run(debug=True)