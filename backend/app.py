from flask import Flask, jsonify , request
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
from dotenv import load_dotenv
import os
from services.chatgpt import ChatGPTAPIService
# Load environment variables from .env file
load_dotenv()

# Access the API key
api_key = os.getenv('API_KEY')

# Initialize Flask application
app = Flask(__name__)
# Configure CORS properly with specific settings
CORS(app, resources={r"/*": {
    "origins": ["http://127.0.0.1:5500", "http://localhost:5500"],
    "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    "allow_headers": ["Content-Type", "Authorization"]
}})
# Configuration
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")
app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "dev-jwt-secret")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = 3600 * 2  # 2 hour

# Initialize JWT
jwt = JWTManager(app)

# Initialize database
from services.db import init_db
db =init_db(app)  # Initialize with our Flask app

chatgpt = ChatGPTAPIService(api_key , db=db)


@app.route('/ai/chat', methods=['POST'])
def chat():
    data = request.get_json()
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
    else:
        return jsonify({"error": "Invalid token format"}), 401
    query = data.get('query')
    return chatgpt.coordinator(patient_query=query, token=token)
    
# Endpoint to get current user's ID
@app.route('/ai/book', methods=['POST'])
@jwt_required()
def book_ai():
    
    data = request.get_json()
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
    else:
        return jsonify({"error": "Invalid token format"}), 401
    query = data.get('query')
    return chatgpt.book_appointment_ai(patient_query=query, token=token)

# Endpoint to get current user's ID
@app.route('/ai/recomendation', methods=['POST'])
@jwt_required()
def recommened_ai():
    
    data = request.get_json()
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
    else:
        return jsonify({"error": "Invalid token format"}), 401
    query = data.get('query')
    return chatgpt.recommend_doctor_ai(patient_query=query, token=token)

@app.route('/ai/reschedule', methods=['POST'])
@jwt_required()
def ai_reschudle():
    
    data = request.get_json()
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
    else:
        return jsonify({"error": "Invalid token format"}), 401
    query = data.get('query')
    return chatgpt.reschdule_appointment_ai(patient_query=query, token=token)


@app.route('/ai/cancel', methods=['POST'])
@jwt_required() 
def cancel_ai():
    data = request.get_json()
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
    else:
        return jsonify({"error": "Invalid token format"}), 401
    query = data.get('query')
    return chatgpt.cancel_appointment_ai(patient_query=query, token=token)

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

# Endpoint to get current user's ID
@app.route('/api/auth/me', methods=['GET'])
@jwt_required()
def get_current_user_id():
    """Returns the ID of the currently authenticated user."""
    current_user_id = get_jwt_identity()
    if not current_user_id:
        # This case should ideally not be reached if @jwt_required() works correctly
        return jsonify({"error": "Authentication token is invalid or missing"}), 401
    return jsonify({"user_id": current_user_id}), 200

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
                    "description": doctor.description,
                    
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

@app.route('/appointments/cancel', methods=['PUT'])
@jwt_required()
def cancel_appointment():
    """Cancel an existing appointment and notify all parties"""
    return AppointmentController.cancel_appointment()

@app.route('/appointments/availability-range', methods=['POST'])
def get_doctor_availability_range_route():
    """Get available appointment slots for a doctor across a date range (week/month view)"""
    return AppointmentController.get_doctor_availability_range()

@app.route('/appointments/set-availability', methods=['POST'])
@jwt_required()
def set_doctor_availability_route():
    """Set available time slots for a doctor across a date range"""
    return AppointmentController.set_doctor_availability_range()

@app.route('/appointments/patient', methods=['GET'])
@jwt_required()
def get_patient_appointments():
    """Get all appointments for the current patient"""
    return AppointmentController.get_patient_appointments()

@app.route('/appointments/reschedule', methods=['PUT'])
@jwt_required()
def reschedule_appointment():
    """Reschedule an existing appointment to a new date/time"""
    return AppointmentController.reschedule_appointment()

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

# Messaging routes
@app.route('/messages/contacts', methods=['GET'])
@jwt_required()
def get_messaging_contacts_route():
    """Get all contacts the user can message (doctors, nurses, patients)"""
    return MessagingController.get_messaging_contacts()

@app.route('/messages/<int:contact_id>', methods=['GET'])
@jwt_required()
def get_messages_with_contact_route(contact_id):
    """Get all messages between current user and the specified contact"""
    return MessagingController.get_messages_with_contact(contact_id)

@app.route('/messages/send', methods=['POST'])
@jwt_required()
def send_message_route():
    """Send a message to another user"""
    return MessagingController.send_message()

@app.route('/messages/mark-read/<int:contact_id>', methods=['POST'])
@jwt_required()
def mark_messages_as_read_route(contact_id):
    """Mark all messages from a contact as read"""
    return MessagingController.mark_messages_as_read(contact_id)

@app.route('/messages/unread-count', methods=['GET'])
@jwt_required()
def get_unread_message_count_route():
    """Get the count of unread messages"""
    return MessagingController.get_unread_message_count()

# User profile route
@app.route('/user/profile', methods=['GET'])
@jwt_required()
def user_profile():
    """Return profile info for current user"""
    from flask import jsonify
    from models.user import User
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify({
        'user_id': user.user_id,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': user.email
    })

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
    print(app.url_map)
