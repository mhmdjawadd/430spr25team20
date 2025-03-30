from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime
from services.db import db
from models import User , AppointmentType ,AppointmentStatus , RecurrencePattern , Doctor , Patient, Appointment


class AppointmentController:
    
    @staticmethod
    @jwt_required()
    def create_appointment():
        """
        Create a new appointment. Only patients can create appointments.
        Requires authentication with a JWT token.
        """
        # Get current user's identity and claims from the token
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        role = claims.get("role")
        
        # Check if user is a patient
        if role != "patient":
            return jsonify({
                "status": "error",
                "message": "Only patients can create appointments"
            }), 403
        
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({
                "status": "error", 
                "message": "No data provided"
            }), 400
            
        # Validate required fields
        required_fields = ['doctor_id', 'appointment_date', 'reason']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "status": "error",
                    "message": f"Missing required field: {field}"
                }), 400
        
        # Get patient record for the current user
        patient = Patient.query.filter_by(user_id=current_user_id).first()
        if not patient:
            return jsonify({
                "status": "error",
                "message": "Patient profile not found"
            }), 404
        
        # Check if doctor exists
        doctor = Doctor.query.get(data['doctor_id'])
        if not doctor:
            return jsonify({
                "status": "error",
                "message": "Doctor not found"
            }), 404
        
        # Parse appointment date
        try:
            appointment_date = datetime.fromisoformat(data['appointment_date'].replace('Z', '+00:00'))
        except ValueError:
            return jsonify({
                "status": "error",
                "message": "Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SS.sssZ)"
            }), 400
        recurrence_pattern = None
        if 'recurrence_pattern' in data and data['recurrence_pattern']:
            try:
                recurrence_pattern_value = data['recurrence_pattern'].upper()
                if not hasattr(RecurrencePattern, recurrence_pattern_value):
                    valid_patterns = [p.name for p in RecurrencePattern]
                    return jsonify({
                        "status": "error",
                        "message": f"Invalid recurrence pattern. Valid patterns are: {valid_patterns}"
                    }), 400
                recurrence_pattern = getattr(RecurrencePattern, recurrence_pattern_value)
            except Exception as e:
                return jsonify({
                    "status": "error",
                    "message": f"Error processing recurrence pattern: {str(e)}"
                }), 400
    
        # Create appointment
        new_appointment = Appointment(
        patient_id=patient.patient_id,
        doctor_id=data['doctor_id'],
        date_time=appointment_date,
        duration=data.get('duration', 30),  # Default to 30 minutes if not specified
        type=getattr(AppointmentType, appointment_type),
        status=getattr(AppointmentStatus, appointment_status),
        recurrence_pattern=recurrence_pattern,
        reason=data['reason'],
        
    )
        
        # Save to database
        try:
            db.session.add(new_appointment)
            db.session.commit()
            
            return jsonify({
                "status": "success",
                "message": "Appointment created successfully",
                "appointment_id": new_appointment.appointment_id
            }), 201
            
        except Exception as e:
            db.session.rollback()
            return jsonify({
                "status": "error",
                "message": f"Failed to create appointment: {str(e)}"
            }), 500
    
    @staticmethod
    @jwt_required()
    def get_appointments():
        """
        Get appointments based on user role.
        Patients see their own appointments.
        Doctors see appointments assigned to them.
        Admins see all appointments.
        """
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        role = claims.get("role")
        
        if role == "patient":
            # Get patient's appointments
            patient = Patient.query.filter_by(user_id=current_user_id).first()
            if not patient:
                return jsonify({"status": "error", "message": "Patient profile not found"}), 404
                
            appointments = Appointment.query.filter_by(patient_id=patient.patient_id).all()
            
        elif role == "doctor":
            # Get doctor's appointments
            doctor = Doctor.query.filter_by(user_id=current_user_id).first()
            if not doctor:
                return jsonify({"status": "error", "message": "Doctor profile not found"}), 404
                
            appointments = Appointment.query.filter_by(doctor_id=doctor.doctor_id).all()
            
        elif role == "admin":
            # Get all appointments
            appointments = Appointment.query.all()
            
        else:
            return jsonify({
                "status": "error",
                "message": "Unauthorized role"
            }), 403
        
        # Convert appointments to JSON
        appointments_list = []
        for appointment in appointments:
            doctor = Doctor.query.get(appointment.doctor_id)
            doctor_user = User.query.get(doctor.user_id)
            
            patient = Patient.query.get(appointment.patient_id)
            patient_user = User.query.get(patient.user_id)
            
            appointments_list.append({
                "appointment_id": appointment.appointment_id,
                "doctor": {
                    "doctor_id": doctor.doctor_id,
                    "name": f"{doctor_user.first_name} {doctor_user.last_name}",
                },
                "patient": {
                    "patient_id": patient.patient_id,
                    "name": f"{patient_user.first_name} {patient_user.last_name}",
                },
                "appointment_date": appointment.appointment_date.isoformat(),
                "reason": appointment.reason,
                "status": appointment.status,
                "notes": appointment.notes
            })
        
        return jsonify({
            "status": "success",
            "appointments": appointments_list
        }), 200

    @staticmethod
    @jwt_required()
    def create_referral():
        """
        Create a new referral for a patient to another doctor.
        Only doctors can create referrals.
        """
        # Get current user's identity and claims from the token
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        role = claims.get("role")
        
        # Check if user is a doctor
        if role != "doctor":
            return jsonify({
                "status": "error",
                "message": "Only doctors can create referrals"
            }), 403
        
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({
                "status": "error", 
                "message": "No data provided"
            }), 400
            
        # Validate required fields
        required_fields = ['patient_id', 'referred_doctor_id', 'reason']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "status": "error",
                    "message": f"Missing required field: {field}"
                }), 400
        
        # Get the referring doctor (current user)
        referring_doctor = Doctor.query.filter_by(user_id=current_user_id).first()
        if not referring_doctor:
            return jsonify({
                "status": "error",
                "message": "Doctor profile not found"
            }), 404
        
        # Check if patient exists
        patient = Patient.query.get(data['patient_id'])
        if not patient:
            return jsonify({
                "status": "error",
                "message": "Patient not found"
            }), 404
        
        # Check if referred doctor exists
        referred_doctor = Doctor.query.get(data['referred_doctor_id'])
        if not referred_doctor:
            return jsonify({
                "status": "error",
                "message": "Referred doctor not found"
            }), 404
        
        # Make sure referred doctor is different from referring doctor
        if referring_doctor.doctor_id == referred_doctor.doctor_id:
            return jsonify({
                "status": "error",
                "message": "Cannot refer to yourself"
            }), 400
            
        # Import the Referral model (add this to your imports at the top)
        from ..models.medical_record.refferal import Referral
        
        # Create referral
        new_referral = Referral(
            patient_id=patient.patient_id,
            referring_doctor_id=referring_doctor.doctor_id,
            referred_doctor_id=referred_doctor.doctor_id,
            reason=data['reason'],
            notes=data.get('notes', ''),
            date_created=datetime.now(),
            status='pending'
        )
        
        # Save to database
        try:
            db.session.add(new_referral)
            db.session.commit()
            
            # Optionally create an appointment automatically
            if data.get('create_appointment', False) and data.get('appointment_date'):
                try:
                    # Parse appointment date
                    appointment_date = datetime.fromisoformat(data['appointment_date'].replace('Z', '+00:00'))
                    
                    # Create appointment with referred doctor
                    new_appointment = Appointment(
                        patient_id=patient.patient_id,
                        doctor_id=referred_doctor.doctor_id,
                        appointment_date=appointment_date,
                        reason=f"Referral: {data['reason']}",
                        status='pending',
                        notes=data.get('notes', ''),
                        referral_id=new_referral.referral_id
                    )
                    
                    db.session.add(new_appointment)
                    db.session.commit()
                    
                    return jsonify({
                        "status": "success",
                        "message": "Referral and appointment created successfully",
                        "referral_id": new_referral.referral_id,
                        "appointment_id": new_appointment.appointment_id
                    }), 201
                    
                except ValueError:
                    # Rollback appointment but keep referral
                    db.session.rollback()
                    return jsonify({
                        "status": "warning",
                        "message": "Referral created but appointment failed due to invalid date format",
                        "referral_id": new_referral.referral_id
                    }), 201
            
            return jsonify({
                "status": "success",
                "message": "Referral created successfully",
                "referral_id": new_referral.referral_id
            }), 201
            
        except Exception as e:
            db.session.rollback()
            return jsonify({
                "status": "error",
                "message": f"Failed to create referral: {str(e)}"
            }), 500
    
    @staticmethod
    @jwt_required()
    def get_referrals():
        """
        Get referrals based on user role.
        Patients see referrals for them.
        Doctors see referrals they've made or received.
        Admins see all referrals.
        """
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        role = claims.get("role")
        
        # Import the Referral model
        from ..models.medical_record.refferal import Referral
        
        if role == "patient":
            # Get patient's referrals
            patient = Patient.query.filter_by(user_id=current_user_id).first()
            if not patient:
                return jsonify({"status": "error", "message": "Patient profile not found"}), 404
                
            referrals = Referral.query.filter_by(patient_id=patient.patient_id).all()
            
        elif role == "doctor":
            # Get doctor's incoming and outgoing referrals
            doctor = Doctor.query.filter_by(user_id=current_user_id).first()
            if not doctor:
                return jsonify({"status": "error", "message": "Doctor profile not found"}), 404
                
            # Combining both referring and referred doctor referrals
            referring = Referral.query.filter_by(referring_doctor_id=doctor.doctor_id).all()
            referred_to = Referral.query.filter_by(referred_doctor_id=doctor.doctor_id).all()
            referrals = referring + referred_to
            
        elif role == "admin":
            # Get all referrals
            referrals = Referral.query.all()
            
        else:
            return jsonify({
                "status": "error",
                "message": "Unauthorized role"
            }), 403
        
        # Convert referrals to JSON
        referrals_list = []
        for referral in referrals:
            # Get patient info
            patient = Patient.query.get(referral.patient_id)
            patient_user = User.query.get(patient.user_id)
            
            # Get referring doctor info
            referring_doctor = Doctor.query.get(referral.referring_doctor_id)
            referring_doctor_user = User.query.get(referring_doctor.user_id)
            
            # Get referred doctor info
            referred_doctor = Doctor.query.get(referral.referred_doctor_id)
            referred_doctor_user = User.query.get(referred_doctor.user_id)
            
            referrals_list.append({
                "referral_id": referral.referral_id,
                "patient": {
                    "patient_id": patient.patient_id,
                    "name": f"{patient_user.first_name} {patient_user.last_name}",
                },
                "referring_doctor": {
                    "doctor_id": referring_doctor.doctor_id,
                    "name": f"{referring_doctor_user.first_name} {referring_doctor_user.last_name}",
                },
                "referred_doctor": {
                    "doctor_id": referred_doctor.doctor_id,
                    "name": f"{referred_doctor_user.first_name} {referred_doctor_user.last_name}",
                },
                "reason": referral.reason,
                "notes": referral.notes,
                "date_created": referral.date_created.isoformat(),
                "status": referral.status
            })
        
        return jsonify({
            "status": "success",
            "referrals": referrals_list
        }), 200