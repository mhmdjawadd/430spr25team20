from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime, timedelta
from services.db import db
from models import Prescription, MedicalRecord, Patient, Doctor, User, Notification

class PrescriptionController:
    @staticmethod
    @jwt_required()
    def get_prescriptions():
        """Get prescriptions for a patient"""
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        role = claims.get("role")
        
        patient_id = request.args.get('patient_id')
        active_only = request.args.get('active_only', 'false').lower() == 'true'
        
        # If role is patient, can only access their own prescriptions
        if role == "patient":
            patient_id = current_user_id
                
        # If doctor and no patient_id specified, return error
        elif role in ["doctor", "surgeon", "nurse"] and not patient_id:
            return jsonify({
                "status": "error", 
                "message": "Patient ID required for medical staff to access prescriptions"
            }), 400
            
        # If not patient or medical staff, unauthorized
        elif role not in ["patient", "doctor", "surgeon", "nurse"]:
            return jsonify({
                "status": "error",
                "message": "Unauthorized access to prescription data"
            }), 403
        
        # Get all medical records for this patient
        medical_records = MedicalRecord.query.filter_by(patient_id=patient_id).all()
        record_ids = [record.record_id for record in medical_records]
        
        # Query all prescriptions for these records
        query = Prescription.query.filter(Prescription.record_id.in_(record_ids))
        
        # Filter active prescriptions if requested
        if active_only:
            today = datetime.now()
            query = query.filter(
                (Prescription.end_date >= today) | 
                (Prescription.end_date.is_(None))
            )
        
        prescriptions = query.all()
        
        # Format prescriptions for response
        prescriptions_list = []
        for prescription in prescriptions:
            record = MedicalRecord.query.get(prescription.record_id)
            doctor = Doctor.query.get(record.doctor_id)
            doctor_user = User.query.get(doctor.doctor_id) if doctor else None
            
            prescriptions_list.append({
                "prescription_id": prescription.prescription_id,
                "medication_name": prescription.medication_name,
                "dosage": prescription.dosage,
                "instructions": prescription.instructions,
                "start_date": prescription.start_date.isoformat(),
                "end_date": prescription.end_date.isoformat() if prescription.end_date else None,
                "is_active": not prescription.end_date or prescription.end_date >= datetime.now(),
                "days_remaining": (prescription.end_date - datetime.now()).days if prescription.end_date else None,
                "needs_refill": prescription.end_date and (prescription.end_date - datetime.now()).days <= 7,
                "prescribing_doctor": f"Dr. {doctor_user.first_name} {doctor_user.last_name}" if doctor_user else "Unknown"
            })
        
        return jsonify({
            "status": "success",
            "prescriptions": prescriptions_list
        }), 200
    
    @staticmethod
    @jwt_required()
    def request_refill():
        """Request a prescription refill"""
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        role = claims.get("role")
        
        # Only patients can request refills
        if role != "patient":
            return jsonify({
                "status": "error",
                "message": "Only patients can request prescription refills"
            }), 403
        
        data = request.get_json()
        if not data or not data.get('prescription_id'):
            return jsonify({
                "status": "error", 
                "message": "Prescription ID is required"
            }), 400
        
        # Get prescription
        prescription = Prescription.query.get(data['prescription_id'])
        if not prescription:
            return jsonify({
                "status": "error",
                "message": "Prescription not found"
            }), 404
        
        # Verify patient is requesting their own prescription
        record = MedicalRecord.query.get(prescription.record_id)
        if not record or record.patient_id != current_user_id:
            return jsonify({
                "status": "error",
                "message": "You can only request refills for your own prescriptions"
            }), 403
        
        # Create notification for the doctor
        notification = Notification(
            user_id=record.doctor_id,
            type="refill_request",
            message=f"Refill requested for {prescription.medication_name}",
            scheduled_time=datetime.now(),
            status="pending"
        )
        
        try:
            db.session.add(notification)
            db.session.commit()
            
            return jsonify({
                "status": "success",
                "message": "Refill request sent successfully"
            }), 200
            
        except Exception as e:
            db.session.rollback()
            return jsonify({
                "status": "error",
                "message": f"Failed to send refill request: {str(e)}"
            }), 500
    
    @staticmethod
    def schedule_medication_reminders():
        """
        Scheduled task to create medication reminder notifications
        This would be called by a scheduler like APScheduler or Celery
        """
        try:
            # Get active prescriptions
            today = datetime.now()
            active_prescriptions = Prescription.query.filter(
                (Prescription.end_date >= today) | 
                (Prescription.end_date.is_(None))
            ).all()
            
            reminders_created = 0
            
            for prescription in active_prescriptions:
                record = MedicalRecord.query.get(prescription.record_id)
                
                # Check if reminder already exists for today
                existing_reminder = Notification.query.filter(
                    Notification.user_id == record.patient_id,
                    Notification.type == "medication_reminder",
                    Notification.message.like(f"%{prescription.medication_name}%"),
                    Notification.scheduled_time >= today.replace(hour=0, minute=0, second=0),
                    Notification.scheduled_time <= today.replace(hour=23, minute=59, second=59)
                ).first()
                
                if not existing_reminder:
                    # Create reminder for patient
                    reminder = Notification(
                        user_id=record.patient_id,
                        type="medication_reminder",
                        message=f"Remember to take your {prescription.medication_name}: {prescription.instructions}",
                        scheduled_time=datetime.now(),
                        status="pending"
                    )
                    db.session.add(reminder)
                    reminders_created += 1
                    
                # Check for upcoming refills needed (7 days before expiration)
                if prescription.end_date and (prescription.end_date - today).days <= 7:
                    # Check if refill reminder already exists
                    existing_refill_reminder = Notification.query.filter(
                        Notification.user_id == record.patient_id,
                        Notification.type == "refill_reminder",
                        Notification.message.like(f"%{prescription.medication_name}%"),
                        Notification.status == "pending"
                    ).first()
                    
                    if not existing_refill_reminder:
                        # Create refill reminder
                        refill_reminder = Notification(
                            user_id=record.patient_id,
                            type="refill_reminder",
                            message=f"Your {prescription.medication_name} prescription needs refill soon. Expires on {prescription.end_date.strftime('%Y-%m-%d')}",
                            scheduled_time=datetime.now(),
                            status="pending"
                        )
                        db.session.add(refill_reminder)
                        reminders_created += 1
            
            db.session.commit()
            return jsonify({
                "status": "success",
                "message": f"Created {reminders_created} medication reminders"
            }), 200
            
        except Exception as e:
            db.session.rollback()
            return jsonify({
                "status": "error",
                "message": f"Failed to schedule medication reminders: {str(e)}"
            }), 500