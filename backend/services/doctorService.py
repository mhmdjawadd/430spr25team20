from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime, timedelta
from services.db import db
from models import (
    User, Doctor, Patient, Appointment, MedicalRecord, 
    Prescription, ChronicCondition, ConditionTracking,
    Referral, Notification, AppointmentStatus
)

class DoctorController:
    @staticmethod
    @jwt_required()
    def get_patient_history():
        """
        Get integrated patient history combining:
        - Medical records
        - Prescriptions
        - Chronic conditions
        - Appointment history
        - Referrals
        """
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        role = claims.get("role")
        
        # Only medical staff can access patient history
        if role not in ["doctor", "surgeon", "nurse"]:
            return jsonify({
                "status": "error",
                "message": "Only medical staff can access patient history"
            }), 403
        
        # Get patient ID from request
        patient_id = request.args.get('patient_id')
        if not patient_id:
            return jsonify({
                "status": "error",
                "message": "Patient ID is required"
            }), 400
        
        # Verify patient exists
        patient = Patient.query.get(patient_id)
        if not patient:
            return jsonify({
                "status": "error",
                "message": "Patient not found"
            }), 404
        
        patient_user = User.query.get(patient.patient_id)
        
        # Get patient's medical records
        medical_records = MedicalRecord.query.filter_by(patient_id=patient_id).all()
        
        # Format into response objects
        records_list = []
        for record in medical_records:
            doctor = Doctor.query.get(record.doctor_id)
            doctor_user = User.query.get(doctor.doctor_id) if doctor else None
            
            # Get prescriptions for this record
            prescriptions = []
            for prescription in record.prescriptions:
                prescriptions.append({
                    "prescription_id": prescription.prescription_id,
                    "medication_name": prescription.medication_name,
                    "dosage": prescription.dosage,
                    "instructions": prescription.instructions,
                    "start_date": prescription.start_date.isoformat(),
                    "end_date": prescription.end_date.isoformat() if prescription.end_date else None,
                    "is_active": not prescription.end_date or prescription.end_date >= datetime.now()
                })
            
            records_list.append({
                "record_id": record.record_id,
                "description": record.description,
                "doctor": f"Dr. {doctor_user.first_name} {doctor_user.last_name}" if doctor_user else "Unknown",
                "date": record.created_at.isoformat() if hasattr(record, 'created_at') else None,
                "prescriptions": prescriptions
            })
        
        # Get chronic conditions
        conditions = ChronicCondition.query.filter_by(patient_id=patient_id).all()
        conditions_list = []
        
        for condition in conditions:
            # Get tracking history
            tracking_history = ConditionTracking.query.filter_by(condition_id=condition.condition_id).order_by(
                ConditionTracking.tracked_date.desc()
            ).all()
            
            tracking_data = []
            for tracking in tracking_history:
                tracking_data.append({
                    "tracking_id": tracking.tracking_id,
                    "date": tracking.tracked_date.isoformat(),
                    "severity": tracking.severity,
                    "notes": tracking.notes,
                    "vital_signs": tracking.vital_signs
                })
            
            conditions_list.append({
                "condition_id": condition.condition_id,
                "name": condition.name,
                "diagnosis_date": condition.diagnosis_date.isoformat(),
                "description": condition.description,
                "tracking_history": tracking_data
            })
        
        # Get appointment history
        appointments = Appointment.query.filter_by(patient_id=patient_id).order_by(
            Appointment.date_time.desc()
        ).all()
        
        appointments_list = []
        for appointment in appointments:
            doctor = Doctor.query.get(appointment.doctor_id)
            doctor_user = User.query.get(doctor.doctor_id)
            
            appointments_list.append({
                "appointment_id": appointment.appointment_id,
                "date_time": appointment.date_time.isoformat(),
                "doctor": f"Dr. {doctor_user.first_name} {doctor_user.last_name}" if doctor_user else "Unknown",
                "type": appointment.type.value,
                "status": appointment.status.value,
                "reason": appointment.reason,
                "duration": appointment.duration
            })
        
        # Get referrals
        referrals_to = Referral.query.filter_by(patient_id=patient_id).all()
        
        referrals_list = []
        for referral in referrals_to:
            referring_doctor = Doctor.query.get(referral.referring_doctor_id)
            referring_doctor_user = User.query.get(referring_doctor.doctor_id) if referring_doctor else None
            
            specialist_doctor = Doctor.query.get(referral.specialist_id)
            specialist_doctor_user = User.query.get(specialist_doctor.doctor_id) if specialist_doctor else None
            
            referrals_list.append({
                "referral_id": referral.referral_id,
                "referring_doctor": f"Dr. {referring_doctor_user.first_name} {referring_doctor_user.last_name}" if referring_doctor_user else "Unknown",
                "specialist": f"Dr. {specialist_doctor_user.first_name} {specialist_doctor_user.last_name}" if specialist_doctor_user else "Unknown",
                "reason": referral.reason,
                "date": referral.created_at.isoformat(),
                "status": referral.status.value if hasattr(referral.status, 'value') else referral.status
            })
        
        # Return integrated patient history
        return jsonify({
            "status": "success",
            "patient": {
                "patient_id": patient.patient_id,
                "name": f"{patient_user.first_name} {patient_user.last_name}",
                "date_of_birth": patient.date_of_birth.isoformat() if patient.date_of_birth else None,
                "emergency_contact": {
                    "name": patient.emergency_contact_name,
                    "phone": patient.emergency_contact_phone
                } if patient.emergency_contact_name else None
            },
            "medical_records": records_list,
            "chronic_conditions": conditions_list,
            "appointments": appointments_list,
            "referrals": referrals_list
        }), 200
    
    @staticmethod
    @jwt_required()
    def get_doctor_schedule():
        """
        Get a doctor's daily schedule with all appointments and activities
        """
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        role = claims.get("role")
        
        # Only doctors can access their schedule
        if role not in ["doctor", "surgeon"]:
            return jsonify({
                "status": "error",
                "message": "Only doctors can access their schedule"
            }), 403
        
        # Get date parameter or use today
        date_str = request.args.get('date')
        try:
            if date_str:
                selected_date = datetime.fromisoformat(date_str.replace('Z', '+00:00')).date()
            else:
                selected_date = datetime.now().date()
        except ValueError:
            return jsonify({
                "status": "error",
                "message": "Invalid date format. Use ISO format (YYYY-MM-DD)"
            }), 400
        
        # Get doctor
        doctor = Doctor.query.filter_by(doctor_id=current_user_id).first()
        if not doctor:
            return jsonify({
                "status": "error",
                "message": "Doctor profile not found"
            }), 404
        
        # Date range for the selected day
        day_start = datetime.combine(selected_date, datetime.min.time())
        day_end = datetime.combine(selected_date, datetime.max.time())
        
        # Get doctor's appointments
        appointments = Appointment.query.filter(
            Appointment.doctor_id == doctor.doctor_id,
            Appointment.date_time >= day_start,
            Appointment.date_time <= day_end
        ).order_by(Appointment.date_time).all()
        
        # Get availability blocks
        availability_blocks = ORAvailability.query.filter(
            ORAvailability.surgeon_id == doctor.doctor_id,
            ORAvailability.start_time <= day_end,
            ORAvailability.end_time >= day_start
        ).all()
        
        # Get notifications for the doctor
        notifications = Notification.query.filter(
            Notification.user_id == doctor.doctor_id,
            Notification.scheduled_time >= day_start,
            Notification.scheduled_time <= day_end
        ).all()
        
        # Format into schedule items
        schedule_items = []
        
        # Add appointments
        for appointment in appointments:
            patient = Patient.query.get(appointment.patient_id)
            patient_user = User.query.get(patient.patient_id) if patient else None
            
            schedule_items.append({
                "type": "appointment",
                "id": appointment.appointment_id,
                "start_time": appointment.date_time.isoformat(),
                "end_time": (appointment.date_time + timedelta(minutes=appointment.duration)).isoformat(),
                "duration_minutes": appointment.duration,
                "patient": f"{patient_user.first_name} {patient_user.last_name}" if patient_user else "Unknown",
                "reason": appointment.reason,
                "status": appointment.status.value,
                "is_emergency": appointment.type == AppointmentType.EMERGENCY,
                "color": "#FF4136" if appointment.type == AppointmentType.EMERGENCY else 
                        "#0074D9" if appointment.status == AppointmentStatus.CONFIRMED else "#2ECC40"
            })
        
        # Add availability blocks
        for block in availability_blocks:
            # Only include blocks that overlap with the selected day
            block_start = max(block.start_time, day_start)
            block_end = min(block.end_time, day_end)
            
            schedule_items.append({
                "type": "availability",
                "id": block.or_id,
                "start_time": block_start.isoformat(),
                "end_time": block_end.isoformat(),
                "status": block.status,
                "color": "#AAAAAA" if block.status != 'available' else "#7FDBFF"
            })
        
        # Add notifications
        for notification in notifications:
            schedule_items.append({
                "type": "notification",
                "id": notification.notification_id,
                "time": notification.scheduled_time.isoformat(),
                "message": notification.message,
                "notification_type": notification.type,
                "status": notification.status,
                "color": "#FF851B" if notification.type in ["urgent_care", "emergency_priority"] else "#FFDC00"
            })
        
        # Sort all items by start time
        schedule_items.sort(key=lambda x: x.get("start_time", x.get("time", "")))
        
        return jsonify({
            "status": "success",
            "date": selected_date.isoformat(),
            "doctor_id": doctor.doctor_id,
            "schedule": schedule_items
        }), 200

    @staticmethod
    @jwt_required()
    def manage_referral():
        """
        Update referral status (accept, reject, complete)
        """
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        role = claims.get("role")
        
        # Only medical staff can manage referrals
        if role not in ["doctor", "surgeon"]:
            return jsonify({
                "status": "error",
                "message": "Only doctors can manage referrals"
            }), 403
        
        data = request.get_json()
        if not data or not data.get('referral_id'):
            return jsonify({
                "status": "error",
                "message": "Referral ID is required"
            }), 400
        
        # Get the referral
        referral = Referral.query.get(data['referral_id'])
        if not referral:
            return jsonify({
                "status": "error",
                "message": "Referral not found"
            }), 404
        
        # Verify the current doctor is either the referring doctor or the specialist
        if referral.specialist_id != current_user_id and referral.referring_doctor_id != current_user_id:
            return jsonify({
                "status": "error",
                "message": "You are not authorized to manage this referral"
            }), 403
        
        # Update referral status
        new_status = data.get('status')
        if not new_status:
            return jsonify({
                "status": "error",
                "message": "New status is required"
            }), 400
        
        try:
            # Convert string status to enum
            new_status_upper = new_status.upper()
            if not hasattr(AppointmentStatus, new_status_upper):
                valid_statuses = [s.name for s in AppointmentStatus]
                return jsonify({
                    "status": "error",
                    "message": f"Invalid status. Valid statuses are: {valid_statuses}"
                }), 400
                
            referral.status = getattr(AppointmentStatus, new_status_upper)
            
            # Add notes if provided
            if data.get('notes'):
                referral.notes = data.get('notes')
            
            # Create notification for the other doctor involved
            recipient_id = referral.referring_doctor_id if current_user_id == referral.specialist_id else referral.specialist_id
            
            patient = Patient.query.get(referral.patient_id)
            patient_user = User.query.get(patient.patient_id) if patient else None
            patient_name = f"{patient_user.first_name} {patient_user.last_name}" if patient_user else "Unknown Patient"
            
            notification = Notification(
                user_id=recipient_id,
                type="referral_update",
                message=f"Referral for {patient_name} has been {new_status.lower()} by Dr. {User.query.get(current_user_id).last_name}",
                scheduled_time=datetime.now(),
                status="pending"
            )
            
            db.session.add(notification)
            db.session.commit()
            
            return jsonify({
                "status": "success",
                "message": "Referral updated successfully"
            }), 200
            
        except Exception as e:
            db.session.rollback()
            return jsonify({
                "status": "error",
                "message": f"Failed to update referral: {str(e)}"
            }), 500