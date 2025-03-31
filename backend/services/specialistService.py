from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime, timedelta
from services.db import db
from models import User, Doctor, Patient, Appointment, MedicalRecord, Referral, Notification, AppointmentStatus

class SpecialistController:
    @staticmethod
    @jwt_required()
    def get_specialty_referrals():
        """
        Get referrals filtered by specialty for a specialist doctor.
        """
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        role = claims.get("role")
        
        # Only doctors can view specialty referrals
        if role not in ["doctor", "surgeon"]:
            return jsonify({
                "status": "error",
                "message": "Only medical specialists can access specialty referrals"
            }), 403
        
        # Get the doctor's specialty
        doctor = Doctor.query.filter_by(doctor_id=current_user_id).first()
        if not doctor:
            return jsonify({
                "status": "error",
                "message": "Doctor profile not found"
            }), 404
        
        specialty = doctor.specialty
        status_filter = request.args.get('status', '').upper()
        sort_by = request.args.get('sort_by', 'date')  # Default sort by date
        
        # Get referrals directed to this doctor or to this specialty
        query = Referral.query.filter(Referral.specialist_id == current_user_id)
        
        # Apply status filter if provided
        if status_filter:
            try:
                if hasattr(AppointmentStatus, status_filter):
                    status_enum = getattr(AppointmentStatus, status_filter)
                    query = query.filter(Referral.status == status_enum)
            except (AttributeError, ValueError):
                pass  # Ignore invalid status filters
        
        # Apply sorting
        if sort_by == 'urgency':
            query = query.order_by(Referral.priority.desc(), Referral.created_at.desc())
        elif sort_by == 'patient':
            # Join with patient table and sort by patient name
            query = query.join(Patient, Referral.patient_id == Patient.patient_id)\
                         .join(User, Patient.patient_id == User.user_id)\
                         .order_by(User.last_name)
        else:  # Default to date sorting
            query = query.order_by(Referral.created_at.desc())
        
        referrals = query.all()
        
        # Format referrals for response
        referrals_list = []
        for referral in referrals:
            # Get patient info
            patient = Patient.query.get(referral.patient_id)
            patient_user = User.query.get(patient.patient_id) if patient else None
            
            # Get referring doctor info
            referring_doctor = Doctor.query.get(referral.referring_doctor_id)
            referring_doctor_user = User.query.get(referring_doctor.doctor_id) if referring_doctor else None
            
            # Calculate days since referral was created
            days_since_referred = (datetime.now() - referral.created_at).days
            
            # Get related medical records
            medical_records = []
            if hasattr(referral, 'medical_record') and referral.medical_record:
                for record in [referral.medical_record]:  # Convert to list if it's a single record
                    medical_records.append({
                        "record_id": record.record_id,
                        "description": record.description,
                        "created_at": record.created_at.isoformat() if hasattr(record, 'created_at') else None
                    })
            
            referrals_list.append({
                "referral_id": referral.referral_id,
                "patient": {
                    "patient_id": patient.patient_id,
                    "name": f"{patient_user.first_name} {patient_user.last_name}" if patient_user else "Unknown"
                },
                "referring_doctor": {
                    "doctor_id": referring_doctor.doctor_id,
                    "name": f"Dr. {referring_doctor_user.first_name} {referring_doctor_user.last_name}" if referring_doctor_user else "Unknown",
                },
                "reason": referral.reason,
                "notes": referral.notes if hasattr(referral, 'notes') else None,
                "status": referral.status.value if hasattr(referral.status, 'value') else str(referral.status),
                "created_at": referral.created_at.isoformat(),
                "days_pending": days_since_referred,
                "priority": referral.priority if hasattr(referral, 'priority') else "NORMAL",
                "medical_records": medical_records,
                "has_appointment": bool(Appointment.query.filter_by(referral_id=referral.referral_id).first())
            })
        
        return jsonify({
            "status": "success",
            "referrals": referrals_list
        }), 200

    @staticmethod
    @jwt_required()
    def set_specialty_availability():
        """
        Set availability slots specific to a specialist's procedures and requirements.
        Allows defining appointment types with different durations.
        """
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        role = claims.get("role")
        
        if role not in ["doctor", "surgeon"]:
            return jsonify({
                "status": "error",
                "message": "Only specialists can set specialty availability"
            }), 403
        
        # Get doctor record and specialty
        doctor = Doctor.query.filter_by(doctor_id=current_user_id).first()
        if not doctor:
            return jsonify({"status": "error", "message": "Doctor profile not found"}), 404
        
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No data provided"}), 400
        
        # Process availability data
        try:
            start_time = datetime.fromisoformat(data.get('start_time').replace('Z', '+00:00'))
            end_time = datetime.fromisoformat(data.get('end_time').replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return jsonify({
                "status": "error", 
                "message": "Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"
            }), 400
        
        # Get specialty-specific data
        allowed_procedures = data.get('allowed_procedures', [])
        equipment_required = data.get('equipment_required', [])
        default_duration = data.get('default_duration', 30)  # Default duration in minutes
        max_patients = data.get('max_patients')
        
        # Create availability slot with specialty-specific metadata
        from models import ORAvailability
        
        # Convert lists to string for storage
        procedures_str = ','.join(allowed_procedures) if allowed_procedures else ''
        equipment_str = ','.join(equipment_required) if equipment_required else ''
        
        # Create availability record with additional metadata
        availability = ORAvailability(
            surgeon_id=doctor.doctor_id,
            start_time=start_time,
            end_time=end_time,
            status='available',
            metadata={
                "specialty": doctor.specialty.value,
                "procedures": procedures_str,
                "equipment": equipment_str,
                "default_duration": default_duration,
                "max_patients": max_patients
            }
        )
        
        try:
            db.session.add(availability)
            db.session.commit()
            return jsonify({
                "status": "success",
                "message": "Specialty availability set successfully"
            }), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({
                "status": "error", 
                "message": f"Failed to set availability: {str(e)}"
            }), 500

    @staticmethod
    @jwt_required()
    def create_case_discussion():
        """
        Create a multi-specialist case discussion for complex cases.
        This facilitates collaboration between different specialists.
        """
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        role = claims.get("role")
        
        # Only medical staff can create case discussions
        if role not in ["doctor", "surgeon"]:
            return jsonify({
                "status": "error",
                "message": "Only specialists can initiate case discussions"
            }), 403
        
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No data provided"}), 400
            
        # Validate required fields
        required_fields = ['patient_id', 'title', 'description']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "status": "error",
                    "message": f"Missing required field: {field}"
                }), 400
        
        # Get invited specialists
        invited_specialists = data.get('invited_specialists', [])
        if not invited_specialists:
            return jsonify({
                "status": "error",
                "message": "At least one specialist must be invited"
            }), 400
        
        # Create case discussion
        from models.case_discussion import CaseDiscussion
        
        new_discussion = CaseDiscussion(
            patient_id=data['patient_id'],
            created_by=current_user_id,
            title=data['title'],
            description=data['description'],
            status='open',
            created_at=datetime.utcnow(),
            priority=data.get('priority', 'normal')
        )
        
        try:
            db.session.add(new_discussion)
            db.session.flush()  # Get ID without committing
            
            # Create invitations for each specialist
            from models.case_discussion import CaseDiscussionParticipant
            
            participants = []
            for specialist_id in invited_specialists:
                # Verify specialist exists
                specialist = Doctor.query.get(specialist_id)
                if not specialist:
                    continue
                
                participant = CaseDiscussionParticipant(
                    case_id=new_discussion.case_id,
                    doctor_id=specialist_id,
                    invited_at=datetime.utcnow(),
                    status='invited'
                )
                participants.append(participant)
                
                # Create notification for the specialist
                notification = Notification(
                    user_id=specialist_id,
                    type="case_discussion_invitation",
                    message=f"You've been invited to a case discussion: {new_discussion.title}",
                    scheduled_time=datetime.utcnow(),
                    status="pending"
                )
                db.session.add(notification)
            
            # Add all participants
            db.session.add_all(participants)
            
            # Add creator as participant
            creator_participant = CaseDiscussionParticipant(
                case_id=new_discussion.case_id,
                doctor_id=current_user_id,
                invited_at=datetime.utcnow(),
                joined_at=datetime.utcnow(),
                status='joined'
            )
            db.session.add(creator_participant)
            
            db.session.commit()
            
            return jsonify({
                "status": "success",
                "message": "Case discussion created successfully",
                "case_id": new_discussion.case_id
            }), 201
            
        except Exception as e:
            db.session.rollback()
            return jsonify({
                "status": "error",
                "message": f"Failed to create case discussion: {str(e)}"
            }), 500

    @staticmethod
    @jwt_required()
    def cross_department_consult():
        """
        Create a cross-department consultation request.
        This allows specialists to coordinate care across departments.
        """
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        role = claims.get("role")
        
        # Only medical staff can create consultations
        if role not in ["doctor", "surgeon"]:
            return jsonify({
                "status": "error",
                "message": "Only specialists can request cross-department consultations"
            }), 403
        
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No data provided"}), 400
            
        # Validate required fields
        required_fields = ['patient_id', 'target_department', 'reason']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "status": "error",
                    "message": f"Missing required field: {field}"
                }), 400
        
        # Create consultation request
        from models.consultation import DepartmentConsultation
        
        # Get patient info
        patient = Patient.query.get(data['patient_id'])
        if not patient:
            return jsonify({
                "status": "error",
                "message": "Patient not found"
            }), 404
        
        # Get doctor info
        doctor = Doctor.query.get(current_user_id)
        
        new_consult = DepartmentConsultation(
            patient_id=data['patient_id'],
            requesting_doctor_id=current_user_id,
            source_department=doctor.specialty.value if hasattr(doctor, 'specialty') else "UNKNOWN",
            target_department=data['target_department'],
            reason=data['reason'],
            priority=data.get('priority', 'normal'),
            needed_by_date=datetime.fromisoformat(data['needed_by_date'].replace('Z', '+00:00')) if data.get('needed_by_date') else None,
            status='pending'
        )
        
        try:
            db.session.add(new_consult)
            db.session.commit()
            
            # Find doctors in the target department to notify
            target_doctors = Doctor.query.filter_by(specialty=data['target_department']).all()
            
            # Notify doctors in the target department
            notifications = []
            for target_doctor in target_doctors:
                notification = Notification(
                    user_id=target_doctor.doctor_id,
                    type="consultation_request",
                    message=f"New consultation request from {doctor.specialty.value if hasattr(doctor, 'specialty') else 'Unknown'} department",
                    scheduled_time=datetime.utcnow(),
                    status="pending"
                )
                notifications.append(notification)
            
            db.session.add_all(notifications)
            db.session.commit()
            
            return jsonify({
                "status": "success",
                "message": "Cross-department consultation request created",
                "consultation_id": new_consult.consultation_id
            }), 201
            
        except Exception as e:
            db.session.rollback()
            return jsonify({
                "status": "error",
                "message": f"Failed to create consultation request: {str(e)}"
            }), 500