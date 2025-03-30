from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.db import db
from models import Patient, User, Insurance

class PatientController:
    @staticmethod
    @jwt_required()
    def create_patient_profile():
        """Create or update patient profile for the authenticated user"""
        current_user_id = get_jwt_identity()
        
        # Check if profile already exists
        existing_profile = Patient.query.filter_by(patient_id=current_user_id).first()
        if existing_profile:
            return jsonify({
                "status": "error",
                "message": "Patient profile already exists"
            }), 409
            
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No data provided"}), 400
            
        # Create new patient profile
        new_patient = Patient(
            patient_id=current_user_id,
            date_of_birth=data.get('date_of_birth'),
            emergency_contact_name=data.get('emergency_contact_name'),
            emergency_contact_phone=data.get('emergency_contact_phone')
        )
        
        try:
            db.session.add(new_patient)
            db.session.commit()
            return jsonify({
                "status": "success",
                "message": "Patient profile created successfully"
            }), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({
                "status": "error",
                "message": f"Failed to create patient profile: {str(e)}"
            }), 500