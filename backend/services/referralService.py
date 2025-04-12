from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from services.db import db
from models import User, Doctor, Patient, Referral, Notification, UserRole
from sqlalchemy import desc, or_

class ReferralController:
    # Valid status and priority values
    VALID_STATUSES = ["pending", "accepted", "completed", "rejected", "cancelled"]
    VALID_PRIORITIES = ["low", "medium", "high", "urgent"]
    
    @staticmethod
    @jwt_required()
    def create_referral():
        """
        Create a new referral from a doctor to a specialist
        
        Request body:
        {
            "patient_id": int,
            "specialist_id": int,
            "reason": string,
            "notes": string (optional),
            "priority": string (optional, one of "low", "medium", "high", "urgent")
        }
        """
        # Get the current user (referring doctor)
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user:
            return jsonify({"error": "User not found"}), 404
            
        # Check if the user is a doctor
        if current_user.role not in [UserRole.DOCTOR, UserRole.SURGEON, UserRole.THERAPIST, UserRole.NURSE]:
            return jsonify({"error": "Only medical professionals can create referrals"}), 403
            
        # Get request data
        data = request.get_json()
        patient_id = data.get('patient_id')
        specialist_id = data.get('specialist_id')
        reason = data.get('reason')
        notes = data.get('notes', '')
        priority = data.get('priority', 'medium').lower()
        
        # Validate required fields
        if not patient_id or not specialist_id or not reason:
            return jsonify({"error": "Missing required fields: patient_id, specialist_id, reason"}), 400
            
        # Check if patient exists
        patient = Patient.query.get(patient_id)
        if not patient:
            return jsonify({"error": "Patient not found"}), 404
            
        # Check if specialist exists and is a doctor
        specialist = User.query.get(specialist_id)
        if not specialist:
            return jsonify({"error": "Specialist not found"}), 404
            
        if specialist.role not in [UserRole.DOCTOR, UserRole.SURGEON, UserRole.THERAPIST]:
            return jsonify({"error": "The specified user is not a medical specialist"}), 400
            
        # Get doctor records
        referring_doctor = Doctor.query.get(current_user.user_id)
        specialist_doctor = Doctor.query.get(specialist_id)
        
        if not referring_doctor:
            return jsonify({"error": "Referring doctor record not found"}), 404
            
        if not specialist_doctor:
            return jsonify({"error": "Specialist doctor record not found"}), 404
            
        # Validate priority
        if priority not in ReferralController.VALID_PRIORITIES:
            valid_priorities = ", ".join(ReferralController.VALID_PRIORITIES)
            return jsonify({"error": f"Invalid priority. Valid priorities: {valid_priorities}"}), 400
            
        # Create new referral
        new_referral = Referral(
            patient_id=patient_id,
            referring_doctor_id=referring_doctor.doctor_id,
            specialist_id=specialist_doctor.doctor_id,
            reason=reason,
            notes=notes,
            priority=priority,
            status="pending",
            created_at=datetime.now()
        )
        
        try:
            db.session.add(new_referral)
            db.session.flush()  # Get the ID without committing
            
            # Create notification for specialist
            notification = Notification(
                user_id=specialist_id,
                message=f"New patient referral from Dr. {current_user.first_name} {current_user.last_name}",
                scheduled_time=datetime.now()
            )
            
            db.session.add(notification)
            db.session.commit()
            
            return jsonify({
                "message": "Referral created successfully",
                "referral_id": new_referral.referral_id,
                "patient_name": patient.full_name(),
                "specialist_name": specialist.full_name(),
                "status": new_referral.status,
                "created_at": new_referral.created_at.isoformat()
            }), 201
            
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Failed to create referral: {str(e)}"}), 500
    
    @staticmethod
    @jwt_required()
    def get_received_referrals():
        """
        Get all referrals received by the current specialist
        """
        # Get the current user
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user:
            return jsonify({"error": "User not found"}), 404
            
        # Check if the user is a doctor
        if current_user.role not in [UserRole.DOCTOR, UserRole.SURGEON, UserRole.THERAPIST]:
            return jsonify({"error": "Only medical specialists can view received referrals"}), 403
            
        # Get query parameters for filtering
        status = request.args.get('status')
        priority = request.args.get('priority')
        
        # Build the query
        query = Referral.query.filter_by(specialist_id=current_user.user_id)
        
        # Apply filters if provided
        if status and status.lower() in ReferralController.VALID_STATUSES:
            query = query.filter_by(status=status.lower())
                
        if priority and priority.lower() in ReferralController.VALID_PRIORITIES:
            query = query.filter_by(priority=priority.lower())
                
        # Execute the query with ordering - order by priority (urgent first) then by creation date
        referrals = query.all()
        
        # Custom sort based on priority
        priority_order = {
            'urgent': 0,
            'high': 1,
            'medium': 2,
            'low': 3
        }
        
        referrals.sort(key=lambda r: (priority_order.get(r.priority, 999), -int(r.created_at.timestamp())))
        
        # Format the referrals data
        referrals_list = []
        for referral in referrals:
            # Get related records
            patient = Patient.query.get(referral.patient_id)
            referring_doctor = User.query.get(referral.referring_doctor_id)
            
            referrals_list.append({
                "referral_id": referral.referral_id,
                "patient": {
                    "patient_id": referral.patient_id,
                    "name": patient.full_name() if patient else "Unknown"
                },
                "referring_doctor": {
                    "doctor_id": referral.referring_doctor_id,
                    "name": referring_doctor.full_name() if referring_doctor else "Unknown"
                },
                "reason": referral.reason,
                "notes": referral.notes,
                "status": referral.status,
                "priority": referral.priority,
                "created_at": referral.created_at.isoformat(),
                "is_read": referral.is_read
            })
            
        return jsonify({
            "specialist_id": current_user.user_id,
            "specialist_name": current_user.full_name(),
            "referrals": referrals_list,
            "count": len(referrals_list)
        }), 200
    
    @staticmethod
    @jwt_required()
    def get_sent_referrals():
        """
        Get all referrals sent by the current doctor
        """
        # Get the current user
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user:
            return jsonify({"error": "User not found"}), 404
            
        # Check if the user is a doctor
        if current_user.role not in [UserRole.DOCTOR, UserRole.SURGEON, UserRole.THERAPIST, UserRole.NURSE]:
            return jsonify({"error": "Only medical professionals can view sent referrals"}), 403
            
        # Get query parameters for filtering
        status = request.args.get('status')
        specialist_id = request.args.get('specialist_id')
        patient_id = request.args.get('patient_id')
        
        # Build the query
        query = Referral.query.filter_by(referring_doctor_id=current_user.user_id)
        
        # Apply filters if provided
        if status and status.lower() in ReferralController.VALID_STATUSES:
            query = query.filter_by(status=status.lower())
                
        if specialist_id:
            query = query.filter_by(specialist_id=specialist_id)
            
        if patient_id:
            query = query.filter_by(patient_id=patient_id)
            
        # Execute the query with ordering
        referrals = query.order_by(desc(Referral.created_at)).all()
        
        # Format the referrals data
        referrals_list = []
        for referral in referrals:
            # Get related records
            patient = Patient.query.get(referral.patient_id)
            specialist = User.query.get(referral.specialist_id)
            
            referrals_list.append({
                "referral_id": referral.referral_id,
                "patient": {
                    "patient_id": referral.patient_id,
                    "name": patient.full_name() if patient else "Unknown"
                },
                "specialist": {
                    "doctor_id": referral.specialist_id,
                    "name": specialist.full_name() if specialist else "Unknown"
                },
                "reason": referral.reason,
                "status": referral.status,
                "priority": referral.priority,
                "created_at": referral.created_at.isoformat(),
                "appointment_id": referral.appointment_id
            })
            
        return jsonify({
            "doctor_id": current_user.user_id,
            "doctor_name": current_user.full_name(),
            "referrals": referrals_list,
            "count": len(referrals_list)
        }), 200
    
    @staticmethod
    @jwt_required()
    def get_referral_details(referral_id):
        """
        Get detailed information about a specific referral
        """
        # Get the current user
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user:
            return jsonify({"error": "User not found"}), 404
            
        # Get the referral
        referral = Referral.query.get(referral_id)
        if not referral:
            return jsonify({"error": "Referral not found"}), 404
            
        # Check permission - only involved doctors or the patient can view referral details
        is_involved_doctor = (current_user.user_id == referral.referring_doctor_id or 
                            current_user.user_id == referral.specialist_id)
        is_patient = current_user.user_id == referral.patient_id
        
        if not (is_involved_doctor or is_patient):
            return jsonify({"error": "Unauthorized to view this referral"}), 403
            
        # Mark as read if viewed by the specialist and not previously read
        if current_user.user_id == referral.specialist_id and not referral.is_read:
            referral.is_read = True
            db.session.commit()
            
        # Get related records
        patient = Patient.query.get(referral.patient_id)
        referring_doctor = User.query.get(referral.referring_doctor_id)
        specialist = User.query.get(referral.specialist_id)
        
        return jsonify({
            "referral_id": referral.referral_id,
            "patient": {
                "patient_id": referral.patient_id,
                "name": patient.full_name() if patient else "Unknown",
                "date_of_birth": patient.date_of_birth.strftime('%Y-%m-%d') if patient and patient.date_of_birth else None
            },
            "referring_doctor": {
                "doctor_id": referral.referring_doctor_id,
                "name": referring_doctor.full_name() if referring_doctor else "Unknown",
                "specialty": referring_doctor.doctor.specialty.value if referring_doctor and hasattr(referring_doctor, 'doctor') else None
            },
            "specialist": {
                "doctor_id": referral.specialist_id,
                "name": specialist.full_name() if specialist else "Unknown",
                "specialty": specialist.doctor.specialty.value if specialist and hasattr(specialist, 'doctor') else None
            },
            "reason": referral.reason,
            "notes": referral.notes,
            "status": referral.status,
            "priority": referral.priority,
            "created_at": referral.created_at.isoformat(),
            "is_read": referral.is_read,
            "appointment_id": referral.appointment_id
        }), 200
    
    @staticmethod
    @jwt_required()
    def update_referral_status(referral_id):
        """
        Update the status of a referral (accept, reject, complete, etc.)
        
        Request body:
        {
            "status": string (one of "pending", "accepted", "completed", "rejected", "cancelled"),
            "notes": string (optional)
        }
        """
        # Get the current user
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user:
            return jsonify({"error": "User not found"}), 404
            
        # Get the referral
        referral = Referral.query.get(referral_id)
        if not referral:
            return jsonify({"error": "Referral not found"}), 404
            
        # Check permission - only involved doctors can update referral status
        is_referring_doctor = current_user.user_id == referral.referring_doctor_id
        is_specialist = current_user.user_id == referral.specialist_id
        
        if not (is_referring_doctor or is_specialist):
            return jsonify({"error": "Unauthorized to update this referral"}), 403
            
        # Get request data
        data = request.get_json()
        status = data.get('status', '').lower()
        notes = data.get('notes')
        
        if not status:
            return jsonify({"error": "Missing required field: status"}), 400
            
        # Validate status
        if status not in ReferralController.VALID_STATUSES:
            valid_statuses = ", ".join(ReferralController.VALID_STATUSES)
            return jsonify({"error": f"Invalid status. Valid statuses: {valid_statuses}"}), 400
            
        # Apply update
        old_status = referral.status
        referral.status = status
        
        # Add notes if provided
        if notes:
            if referral.notes:
                referral.notes += f"\n\n{datetime.now().strftime('%Y-%m-%d %H:%M')} - {current_user.full_name()}: {notes}"
            else:
                referral.notes = f"{datetime.now().strftime('%Y-%m-%d %H:%M')} - {current_user.full_name()}: {notes}"
        
        try:
            db.session.commit()
            
            # Create notifications for the status change
            if is_specialist:
                # Notify referring doctor
                notification_recipient = referral.referring_doctor_id
                notification_doctor_name = current_user.full_name()
                other_doctor_name = User.query.get(referral.referring_doctor_id).full_name() if User.query.get(referral.referring_doctor_id) else "Unknown"
            else:
                # Notify specialist
                notification_recipient = referral.specialist_id
                notification_doctor_name = current_user.full_name()
                other_doctor_name = User.query.get(referral.specialist_id).full_name() if User.query.get(referral.specialist_id) else "Unknown"
                
            patient_name = Patient.query.get(referral.patient_id).full_name() if Patient.query.get(referral.patient_id) else "Unknown"
                
            notification = Notification(
                user_id=notification_recipient,
                message=f"Referral status updated to {status} by Dr. {notification_doctor_name} for patient {patient_name}",
                scheduled_time=datetime.now()
            )
            
            db.session.add(notification)
            db.session.commit()
            
            return jsonify({
                "message": "Referral status updated successfully",
                "referral_id": referral.referral_id,
                "previous_status": old_status,
                "new_status": status,
                "updated_by": current_user.full_name()
            }), 200
            
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Failed to update referral status: {str(e)}"}), 500
    
    @staticmethod
    @jwt_required()
    def get_patient_referrals(patient_id):
        """
        Get all referrals for a specific patient
        """
        # Get the current user
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user:
            return jsonify({"error": "User not found"}), 404
            
        # Check if the patient exists
        patient = Patient.query.get(patient_id)
        if not patient:
            return jsonify({"error": "Patient not found"}), 404
            
        # Check permission - only the patient themself or involved doctors can view
        is_patient = current_user.user_id == int(patient_id)
        is_doctor = current_user.role in [UserRole.DOCTOR, UserRole.SURGEON, UserRole.THERAPIST, UserRole.NURSE]
        
        # For doctors, check if they're involved in any of the patient's referrals
        if is_doctor and not is_patient:
            doctor_id = current_user.user_id
            # Count referrals where this doctor is either the referring doctor or specialist
            involved_referrals_count = Referral.query.filter(
                Referral.patient_id == patient_id,
                or_(
                    Referral.referring_doctor_id == doctor_id,
                    Referral.specialist_id == doctor_id
                )
            ).count()
            
            # If not involved in any referrals for this patient, check if they're the patient's assigned doctor
            if involved_referrals_count == 0:
                patient_record = Patient.query.get(patient_id)
                if not patient_record or patient_record.doctor_id != doctor_id:
                    return jsonify({"error": "Unauthorized to view this patient's referrals"}), 403
        
        if not (is_patient or is_doctor):
            return jsonify({"error": "Unauthorized to view this patient's referrals"}), 403
            
        # Get all referrals for the patient
        referrals = Referral.query.filter_by(patient_id=patient_id).order_by(desc(Referral.created_at)).all()
        
        # Format the referrals data
        referrals_list = []
        for referral in referrals:
            # Get related doctors
            referring_doctor = User.query.get(referral.referring_doctor_id)
            specialist = User.query.get(referral.specialist_id)
            
            referrals_list.append({
                "referral_id": referral.referral_id,
                "referring_doctor": {
                    "doctor_id": referral.referring_doctor_id,
                    "name": referring_doctor.full_name() if referring_doctor else "Unknown"
                },
                "specialist": {
                    "doctor_id": referral.specialist_id,
                    "name": specialist.full_name() if specialist else "Unknown",
                    "specialty": specialist.doctor.specialty.value if specialist and hasattr(specialist, 'doctor') else None
                },
                "reason": referral.reason,
                "status": referral.status,
                "priority": referral.priority,
                "created_at": referral.created_at.isoformat(),
                "appointment_id": referral.appointment_id
            })
            
        return jsonify({
            "patient_id": int(patient_id),
            "patient_name": patient.full_name(),
            "referrals": referrals_list,
            "count": len(referrals_list)
        }), 200
        
    @staticmethod
    @jwt_required()
    def get_specialists_list():
        """
        Get a list of specialists available for referrals
        """
        # Get the current user
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user:
            return jsonify({"error": "User not found"}), 404
            
        # Check if the user is a medical professional
        if current_user.role not in [UserRole.DOCTOR, UserRole.SURGEON, UserRole.THERAPIST, UserRole.NURSE, UserRole.RECEPTIONIST]:
            return jsonify({"error": "Unauthorized to access specialist list"}), 403
            
        # Get query parameters for filtering
        specialty = request.args.get('specialty')
        
        # Find all doctor users who are specialists
        query = db.session.query(User, Doctor).join(Doctor, User.user_id == Doctor.doctor_id)
        
        # Filter by medical specialties (excluding nurses, etc. if needed)
        query = query.filter(Doctor.specialty.in_([
            UserRole.DOCTOR, UserRole.SURGEON, UserRole.THERAPIST
        ]))
        
        # Apply specialty filter if provided
        if specialty:
            try:
                specialty_enum = UserRole[specialty.upper()]
                query = query.filter(Doctor.specialty == specialty_enum)
            except KeyError:
                pass  # Ignore invalid specialty
                
        # Execute the query
        specialists = query.all()
        
        # Format the specialists data
        specialists_list = []
        for user, doctor in specialists:
            specialists_list.append({
                "doctor_id": user.user_id,
                "name": user.full_name(),
                "specialty": doctor.specialty.value,
                "email": user.email,
                "phone": user.phone
            })
            
        return jsonify({
            "specialists": specialists_list,
            "count": len(specialists_list)
        }), 200
        
    @staticmethod
    @jwt_required()
    def add_message_to_referral(referral_id):
        """
        Add a communication message to an existing referral
        
        Request body:
        {
            "message": string
        }
        """
        # Get the current user
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user:
            return jsonify({"error": "User not found"}), 404
            
        # Get the referral
        referral = Referral.query.get(referral_id)
        if not referral:
            return jsonify({"error": "Referral not found"}), 404
            
        # Check permission - only involved doctors can add messages
        is_involved_doctor = (current_user.user_id == referral.referring_doctor_id or 
                            current_user.user_id == referral.specialist_id)
        
        if not is_involved_doctor:
            return jsonify({"error": "Unauthorized to add messages to this referral"}), 403
            
        # Get request data
        data = request.get_json()
        message = data.get('message')
        
        if not message or not message.strip():
            return jsonify({"error": "Missing required field: message"}), 400
            
        # Add message to notes
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        new_message = f"{timestamp} - Dr. {current_user.full_name()}: {message}"
        
        if referral.notes:
            referral.notes += f"\n\n{new_message}"
        else:
            referral.notes = new_message
            
        try:
            db.session.commit()
            
            # Determine notification recipient (the other doctor)
            if current_user.user_id == referral.referring_doctor_id:
                recipient_id = referral.specialist_id
            else:
                recipient_id = referral.referring_doctor_id
                
            # Create notification for the recipient
            notification = Notification(
                user_id=recipient_id,
                message=f"New message from Dr. {current_user.full_name()} regarding referral for {Patient.query.get(referral.patient_id).full_name() if Patient.query.get(referral.patient_id) else 'Unknown'}",
                scheduled_time=datetime.now()
            )
            
            db.session.add(notification)
            db.session.commit()
            
            return jsonify({
                "message": "Message added successfully",
                "referral_id": referral.referral_id,
                "added_by": current_user.full_name(),
                "timestamp": timestamp
            }), 200
            
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Failed to add message: {str(e)}"}), 500
    
    @staticmethod
    def patient_has_valid_referral(patient_id, specialist_id):
        """
        Check if a patient has a valid (accepted) referral to a specialist
        Returns True if referral exists and is accepted
        """
        # Find any accepted referrals for this patient to this specialist
        referral = Referral.query.filter_by(
            patient_id=patient_id,
            specialist_id=specialist_id,
            status="accepted"
        ).first()
        
        return referral is not None