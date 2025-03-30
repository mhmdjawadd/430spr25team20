from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime, timedelta
from services.db import db
from models import User, AppointmentType, AppointmentStatus, Doctor, Patient, Appointment, Notification

class EmergencyController:
    @staticmethod
    @jwt_required()
    def create_emergency_appointment():
        """
        Create an emergency appointment with priority scheduling.
        Bypasses normal availability checks and notifies staff immediately.
        """
        current_user_id = get_jwt_identity()
        
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({
                "status": "error", 
                "message": "No data provided"
            }), 400
            
        # Validate required fields
        required_fields = ['reason']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "status": "error",
                    "message": f"Missing required field: {field}"
                }), 400
        
        # Get patient record for the current user or specified patient
        patient_id = data.get('patient_id', current_user_id)
        
        patient = Patient.query.filter_by(patient_id=patient_id).first()
        if not patient:
            return jsonify({
                "status": "error",
                "message": "Patient profile not found"
            }), 404
        
        # Find available doctor specializing in emergency care
        # In a real system, you might have different logic for selecting the right doctor
        emergency_doctors = Doctor.query.filter(Doctor.specialty.in_([
            "DOCTOR", "SURGEON"  # Assuming these roles handle emergencies
        ])).all()
        
        if not emergency_doctors:
            return jsonify({
                "status": "error",
                "message": "No emergency doctors available"
            }), 404
        
        # For emergency, use current time as appointment time
        appointment_time = datetime.now()
        
        # Create the emergency appointment with the first available doctor
        # In a real system, you would have more sophisticated doctor selection
        new_appointment = Appointment(
            patient_id=patient.patient_id,
            doctor_id=emergency_doctors[0].doctor_id,
            date_time=appointment_time,
            duration=data.get('duration', 60),  # Default to 60 minutes for emergencies
            type=AppointmentType.EMERGENCY,
            status=AppointmentStatus.CONFIRMED,  # Automatically confirm emergency appointments
            reason=data['reason'],
        )
        
        try:
            db.session.add(new_appointment)
            db.session.commit()
            
            # Send urgent care alerts
            EmergencyController.send_urgent_care_alerts(new_appointment)
            
            return jsonify({
                "status": "success",
                "message": "Emergency appointment created successfully",
                "appointment_id": new_appointment.appointment_id,
                "urgent": True,
                "time": appointment_time.isoformat()
            }), 201
            
        except Exception as e:
            db.session.rollback()
            return jsonify({
                "status": "error",
                "message": f"Failed to create emergency appointment: {str(e)}"
            }), 500
    
    @staticmethod
    def send_urgent_care_alerts(appointment):
        """Send urgent notifications to medical staff about the emergency"""
        try:
            # Get all medical staff
            medical_staff_roles = ["doctor", "surgeon", "nurse"]
            medical_staff = User.query.filter(User.role.in_(medical_staff_roles)).all()
            
            # Get patient and doctor information for the notification
            patient = Patient.query.get(appointment.patient_id)
            patient_user = User.query.get(patient.patient_id)
            
            doctor = Doctor.query.get(appointment.doctor_id)
            doctor_user = User.query.get(doctor.doctor_id)
            
            notifications = []
            
            # Create notification for the assigned doctor
            doctor_notification = Notification(
                user_id=doctor.doctor_id,
                appointment_id=appointment.appointment_id,
                type="urgent_care",
                message=f"URGENT: New emergency appointment with {patient_user.first_name} {patient_user.last_name}. "
                        f"Reason: {appointment.reason}",
                scheduled_time=datetime.now(),
                status="pending"
            )
            notifications.append(doctor_notification)
            
            # Create notifications for other relevant medical staff
            # In a real system, you might have more targeted alerting
            for staff in medical_staff:
                # Don't send duplicate notification to assigned doctor
                if staff.user_id == doctor.doctor_id:
                    continue
                    
                staff_notification = Notification(
                    user_id=staff.user_id,
                    appointment_id=appointment.appointment_id,
                    type="urgent_care_alert",
                    message=f"Emergency patient arrived: {patient_user.first_name} {patient_user.last_name} "
                            f"assigned to Dr. {doctor_user.first_name} {doctor_user.last_name}",
                    scheduled_time=datetime.now(),
                    status="pending"
                )
                notifications.append(staff_notification)
            
            # Add all notifications to database
            db.session.add_all(notifications)
            db.session.commit()
            
            return True
        except Exception as e:
            print(f"Error sending urgent care alerts: {str(e)}")
            db.session.rollback()
            return False

    @staticmethod
    @jwt_required()
    def check_emergency_availability():
        """
        Check immediate availability for emergency care.
        Returns doctors who can handle emergencies right now.
        """
        # Get medical specialties that can handle emergencies
        emergency_specialties = ["DOCTOR", "SURGEON"]
        
        # Find doctors with these specialties
        doctors = Doctor.query.filter(Doctor.specialty.in_(emergency_specialties)).all()
        
        if not doctors:
            return jsonify({
                "status": "error",
                "message": "No doctors available for emergency care"
            }), 404
        
        # Get current time
        now = datetime.now()
        
        # Check which doctors are available immediately
        # This is simplified logic - in reality you'd check current appointments and availability
        available_doctors = []
        
        for doctor in doctors:
            # Check if doctor has any appointments happening right now
            current_appointment = Appointment.query.filter(
                Appointment.doctor_id == doctor.doctor_id,
                Appointment.date_time <= now,
                now <= Appointment.date_time + timedelta(minutes=Appointment.duration),
                Appointment.status.in_([
                    AppointmentStatus.SCHEDULED,
                    AppointmentStatus.CONFIRMED,
                    AppointmentStatus.CHECKED_IN
                ])
            ).first()
            
            if not current_appointment:
                doctor_user = User.query.get(doctor.doctor_id)
                available_doctors.append({
                    "doctor_id": doctor.doctor_id,
                    "name": f"Dr. {doctor_user.first_name} {doctor_user.last_name}",
                    "specialty": doctor.specialty.value,
                })
        
        return jsonify({
            "status": "success",
            "available_emergency_doctors": available_doctors,
            "timestamp": now.isoformat()
        }), 200