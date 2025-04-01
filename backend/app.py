from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
import os
from services import AuthController

"""
from backend.services.therapistService import TherapistController
from services.notificationService import NotificationController
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
db =init_db(app, True)  # Initialize with our Flask app

# JWT Configuration
@jwt.user_identity_loader
def user_identity_lookup(user):
    return user.user_id

@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    from models.user import User  # Local import to avoid circular imports
    identity = jwt_data["sub"]
    return User.query.get(identity)



@app.route('/login', methods=['POST'])
def login_route():
    """User login endpoint"""
    return AuthController.login()

@app.route('/signup', methods=['POST'])
def signup_route():
    """User registration endpoint"""
    return AuthController.signup()


if __name__ == "__main__":
    app.run(debug=True)