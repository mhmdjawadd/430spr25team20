from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from services.db import db
from models import User, Patient, UserRole, MedicalRecord, Appointment, Notification
from sqlalchemy import or_

class CaregiverController:
    @staticmethod
    @jwt_required()
    def assign_caregiver():
        """
        Assign a caregiver to a patient
        
        Request body:
        {
            "patient_id": int,
            "caregiver_id": int
        }
        """
        # Get the current user to verify permissions
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user:
            return jsonify({"error": "User not found"}), 404
            
        # Only allow doctors or the patient themselves to assign caregivers
        if current_user.role not in [UserRole.DOCTOR, UserRole.RECEPTIONIST] and str(current_user.user_id) != str(request.json.get('patient_id')):
            return jsonify({"error": "Unauthorized to assign caregivers"}), 403
            
        # Get request data
        data = request.get_json()
        patient_id = data.get('patient_id')
        caregiver_id = data.get('caregiver_id')
        
        # Validate required fields
        if not patient_id or not caregiver_id:
            return jsonify({"error": "Missing required fields: patient_id and caregiver_id"}), 400
            
        # Check if patient exists
        patient = Patient.query.get(patient_id)
        if not patient:
            return jsonify({"error": "Patient not found"}), 404
            
        # Check if caregiver exists and has correct role
        caregiver = User.query.get(caregiver_id)
        if not caregiver:
            return jsonify({"error": "Caregiver not found"}), 404
        if caregiver.role != UserRole.CAREGIVER:
            return jsonify({"error": "User is not a caregiver"}), 400
            
        # Update patient with caregiver information
        patient.caregiver_id = caregiver_id
        patient.needs_caregiver = True
        
        try:
            db.session.commit()
            
            # Create notification for patient
            patient_notification = Notification(
                user_id=patient.patient_id,
                message=f"Caregiver {caregiver.first_name} {caregiver.last_name} has been assigned to you.",
                scheduled_time=datetime.now()
            )
            
            # Create notification for caregiver
            caregiver_notification = Notification(
                user_id=caregiver.user_id,
                message=f"You have been assigned as a caregiver for patient {patient.user.first_name} {patient.user.last_name}.",
                scheduled_time=datetime.now()
            )
            
            db.session.add(patient_notification)
            db.session.add(caregiver_notification)
            db.session.commit()
            
            return jsonify({
                "message": "Caregiver assigned successfully",
                "patient_id": patient.patient_id,
                "patient_name": patient.full_name(),
                "caregiver_id": caregiver.user_id,
                "caregiver_name": f"{caregiver.first_name} {caregiver.last_name}"
            }), 200
            
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Failed to assign caregiver: {str(e)}"}), 500
            
    @staticmethod
    @jwt_required()
    def get_caregiver_patients():
        """Get all patients associated with the current caregiver"""
        # Get the current user
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user:
            return jsonify({"error": "User not found"}), 404
            
        # Verify the user is a caregiver
        if current_user.role != UserRole.CAREGIVER:
            return jsonify({"error": "User is not a caregiver"}), 403
            
        # Get all patients assigned to this caregiver
        patients = Patient.query.filter_by(caregiver_id=current_user.user_id).all()
        
        # Format patient data
        patient_list = []
        for patient in patients:
            patient_list.append({
                "patient_id": patient.patient_id,
                "name": patient.full_name(),
                "date_of_birth": patient.date_of_birth.strftime('%Y-%m-%d') if patient.date_of_birth else None,
                "emergency_contact": patient.emergency_contact_name
            })
            
        return jsonify({
            "caregiver_id": current_user.user_id,
            "caregiver_name": f"{current_user.first_name} {current_user.last_name}",
            "patients": patient_list
        }), 200
        
    @staticmethod
    @jwt_required()
    def get_patient_caregiver(patient_id):
        """Get caregiver information for a specific patient"""
        # Get the current user
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user:
            return jsonify({"error": "User not found"}), 404
            
        # Check if the patient exists
        patient = Patient.query.get(patient_id)
        if not patient:
            return jsonify({"error": "Patient not found"}), 404
            
        # Only allow access if current user is the patient or their caregiver or a medical professional
        if (current_user.user_id != int(patient_id) and
            current_user.user_id != patient.caregiver_id and
            current_user.role not in [UserRole.DOCTOR, UserRole.NURSE, UserRole.RECEPTIONIST]):
            return jsonify({"error": "Unauthorized to access this information"}), 403
            
        # If patient has no caregiver
        if not patient.caregiver_id:
            return jsonify({
                "patient_id": patient.patient_id,
                "patient_name": patient.full_name(),
                "has_caregiver": False
            }), 200
            
        # Get caregiver information
        caregiver = User.query.get(patient.caregiver_id)
        if not caregiver:
            return jsonify({"error": "Caregiver record not found"}), 404
            
        return jsonify({
            "patient_id": patient.patient_id,
            "patient_name": patient.full_name(),
            "has_caregiver": True,
            "caregiver_id": caregiver.user_id,
            "caregiver_name": f"{caregiver.first_name} {caregiver.last_name}",
            "caregiver_phone": caregiver.phone,
            "caregiver_email": caregiver.email
        }), 200
        
    @staticmethod
    @jwt_required()
    def send_emergency_alert():
        """
        Send an emergency alert to a patient's caregiver
        
        Request body:
        {
            "patient_id": int,
            "message": string,
            "severity": string (e.g., "high", "medium", "low")
        }
        """
        # Get the current user
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user:
            return jsonify({"error": "User not found"}), 404
            
        # Get request data
        data = request.get_json()
        
        # Determine which patient is sending the alert
        if current_user.role == UserRole.PATIENT:
            patient_id = current_user.user_id
        else:
            patient_id = data.get("patient_id")
            if not patient_id:
                return jsonify({"error": "Missing required field: patient_id"}), 400
                
        # Check if patient exists
        patient = Patient.query.get(patient_id)
        if not patient:
            return jsonify({"error": "Patient not found"}), 404
            
        # Check if patient has a caregiver
        if not patient.caregiver_id:
            return jsonify({"error": "Patient does not have an assigned caregiver"}), 400
            
        # Get message details
        message = data.get("message", "Emergency alert from patient!")
        severity = data.get("severity", "high")
        
        # Create notification for caregiver with emergency flag
        notification = Notification(
            user_id=patient.caregiver_id,
            message=f"EMERGENCY ALERT: {message}",
            scheduled_time=datetime.now(),
            status="emergency"  # Uses the existing status field with a new value
        )
        
        try:
            db.session.add(notification)
            db.session.commit()
            
            # Here we'd integrate with a real-time notification service or SMS gateway
            # For now, we're just creating database records
            
            return jsonify({
                "message": "Emergency alert sent successfully",
                "alert_id": notification.notification_id,
                "patient_id": patient.patient_id,
                "caregiver_id": patient.caregiver_id,
                "severity": severity,
                "timestamp": notification.scheduled_time.isoformat()
            }), 200
            
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Failed to send emergency alert: {str(e)}"}), 500
            
    @staticmethod
    @jwt_required()
    def get_patient_medical_data(patient_id):
        """Get a patient's medical data for caregiver access"""
        # Get the current user
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user:
            return jsonify({"error": "User not found"}), 404
            
        # Check if the patient exists
        patient = Patient.query.get(patient_id)
        if not patient:
            return jsonify({"error": "Patient not found"}), 404
            
        # Only allow access if current user is the patient's caregiver or a medical professional
        if (current_user.user_id != patient.caregiver_id and
            current_user.role not in [UserRole.DOCTOR, UserRole.NURSE, UserRole.SURGEON]):
            return jsonify({"error": "Unauthorized to access this information"}), 403
            
        # Get patient's medical records
        medical_records = MedicalRecord.query.filter_by(patient_id=patient_id).all()
        records_list = []
        for record in medical_records:
            records_list.append({
                "record_id": record.record_id,
                "date": record.created_at.strftime('%Y-%m-%d') if hasattr(record, 'created_at') else None,
                "description": record.description,
                "doctor_name": record.doctor.user.full_name() if record.doctor else "Unknown"
            })
            
        # Get patient's appointments
        appointments = Appointment.query.filter_by(patient_id=patient_id).all()
        appointment_list = []
        for appt in appointments:
            appointment_list.append({
                "appointment_id": appt.appointment_id,
                "date_time": appt.date_time.strftime('%Y-%m-%d %H:%M'),
                "doctor_name": appt.doctor.user.full_name() if appt.doctor else "Unknown",
                "type": appt.type.name if hasattr(appt.type, 'name') else str(appt.type)
            })
            
        return jsonify({
            "patient_id": patient.patient_id,
            "patient_name": patient.full_name(),
            "medical_records": records_list,
            "appointments": appointment_list
        }), 200
            
    @staticmethod
    @jwt_required()
    def get_emergency_alerts():
        """Get all emergency alerts for a caregiver"""
        # Get the current user
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user:
            return jsonify({"error": "User not found"}), 404
            
        # Verify the user is a caregiver
        if current_user.role != UserRole.CAREGIVER:
            return jsonify({"error": "User is not a caregiver"}), 403
            
        # Get all emergency notifications for this caregiver
        notifications = Notification.query.filter_by(
            user_id=current_user.user_id, 
            status="emergency"
        ).order_by(Notification.scheduled_time.desc()).all()
        
        # Format notification data
        alerts_list = []
        for notification in notifications:
            # Try to determine which patient sent this alert
            patient_info = None
            if notification.appointment_id:
                # If this is linked to an appointment, get patient from there
                appointment = Appointment.query.get(notification.appointment_id)
                if appointment:
                    patient = Patient.query.get(appointment.patient_id)
                    if patient:
                        patient_info = {
                            "patient_id": patient.patient_id,
                            "patient_name": patient.full_name()
                        }
            
            alerts_list.append({
                "alert_id": notification.notification_id,
                "message": notification.message,
                "timestamp": notification.scheduled_time.isoformat(),
                "patient": patient_info
            })
            
        return jsonify({
            "caregiver_id": current_user.user_id,
            "caregiver_name": f"{current_user.first_name} {current_user.last_name}",
            "emergency_alerts": alerts_list
        }), 200