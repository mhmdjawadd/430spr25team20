from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime, timedelta
from models.user import User, UserRole
from models.appointment import Appointment, AppointmentStatus, AppointmentType, RecurrencePattern
from models.patient import Patient
from models.therapist import Therapist
from models.therapy_session import TherapySession
from models.db import db
import json

class TherapistController:
    @staticmethod
    @jwt_required()
    def schedule_therapy_session():
        """
        Schedule a new therapy session with optional recurrence
        """
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        role = claims.get("role")
        
        # Only therapists can schedule therapy sessions
        if role != "therapist":
            return jsonify({
                "status": "error",
                "message": "Only therapists can schedule therapy sessions"
            }), 403
        
        try:
            data = request.get_json()
            
            # Validate required fields
            required_fields = ["patient_id", "session_date", "duration", "session_type"]
            for field in required_fields:
                if field not in data:
                    return jsonify({
                        "status": "error",
                        "message": f"Missing required field: {field}"
                    }), 400
            
            # Parse and validate the session date
            try:
                session_date = datetime.fromisoformat(data["session_date"])
                if session_date < datetime.now():
                    return jsonify({
                        "status": "error",
                        "message": "Cannot schedule sessions in the past"
                    }), 400
            except ValueError:
                return jsonify({
                    "status": "error",
                    "message": "Invalid session date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)."
                }), 400
            
            # Check therapist availability
            conflicting_appointments = Appointment.query.filter(
                Appointment.doctor_id == current_user_id,
                Appointment.status != AppointmentStatus.CANCELLED,
                Appointment.date_time < session_date + timedelta(minutes=data["duration"]),
                Appointment.date_time + timedelta(minutes=Appointment.duration) > session_date
            ).all()
            
            if conflicting_appointments:
                return jsonify({
                    "status": "error",
                    "message": "You already have an appointment scheduled during this time."
                }), 409
                
            # Create the appointment
            new_appointment = Appointment(
                patient_id=data["patient_id"],
                doctor_id=current_user_id,  # Therapist ID
                date_time=session_date,
                duration=data["duration"],
                type=AppointmentType.THERAPY,
                status=AppointmentStatus.SCHEDULED,
                reason=data.get("notes", "Therapy session"),
                recurrence_pattern=data.get("recurrence_pattern")
            )
            
            db.session.add(new_appointment)
            db.session.flush()  # Get the ID without committing
            
            # Create associated therapy session record with more details
            therapy_session = TherapySession(
                appointment_id=new_appointment.appointment_id,
                session_type=data["session_type"],
                treatment_plan_id=data.get("treatment_plan_id"),
                session_goals=data.get("session_goals"),
                focus_areas=json.dumps(data.get("focus_areas", [])),
                progress_notes=data.get("progress_notes")
            )
            
            db.session.add(therapy_session)
            
            # Create recurring appointments if specified
            recurring_appointments = []
            if data.get("recurrence_pattern") and data.get("recurrence_pattern") in [p.value for p in RecurrencePattern]:
                recurrence_pattern = RecurrencePattern(data["recurrence_pattern"])
                end_date = datetime.fromisoformat(data["recurrence_end_date"]) if data.get("recurrence_end_date") else None
                occurrences = data.get("recurrence_count")
                
                recurring_appointments = TherapistController.generate_recurring_therapy_sessions(
                    new_appointment, 
                    therapy_session, 
                    recurrence_pattern, 
                    end_date, 
                    occurrences
                )
            
            db.session.commit()
            
            return jsonify({
                "status": "success",
                "message": "Therapy session scheduled successfully",
                "session_id": new_appointment.appointment_id,
                "recurring_sessions": recurring_appointments
            }), 201
            
        except Exception as e:
            db.session.rollback()
            return jsonify({
                "status": "error",
                "message": f"Failed to schedule therapy session: {str(e)}"
            }), 500
    
    @staticmethod
    def generate_recurring_therapy_sessions(original_appointment, original_therapy_session, recurrence_pattern, end_date=None, count=None):
        """
        Generate recurring therapy sessions based on the pattern
        
        Parameters:
        - original_appointment: The first appointment in the series
        - original_therapy_session: The associated therapy session details
        - recurrence_pattern: Pattern from RecurrencePattern enum
        - end_date: Optional end date for the recurrence
        - count: Optional number of occurrences
        
        Returns:
        - List of created appointment IDs
        """
        # Default to creating 12 weekly sessions if no end_date or count specified
        if not end_date and not count:
            count = 12
            
        created_appointments = []
        last_date = original_appointment.date_time
        current_count = 0
        
        # Keep creating appointments until we hit the end date or count limit
        while (not end_date or last_date < end_date) and (not count or current_count < count):
            # Calculate next date based on recurrence pattern
            if recurrence_pattern == RecurrencePattern.DAILY:
                next_date = last_date + timedelta(days=1)
            elif recurrence_pattern == RecurrencePattern.WEEKLY:
                next_date = last_date + timedelta(weeks=1)
            elif recurrence_pattern == RecurrencePattern.BIWEEKLY:
                next_date = last_date + timedelta(weeks=2)
            elif recurrence_pattern == RecurrencePattern.MONTHLY:
                # Add one month, handling month boundaries
                month = last_date.month + 1
                year = last_date.year
                if month > 12:
                    month = 1
                    year += 1
                next_date = last_date.replace(year=year, month=month)
            else:
                # Unsupported pattern
                break
                
            # Check if therapist is available for this recurring session
            therapist_id = original_appointment.doctor_id
            session_duration = original_appointment.duration
            session_end_time = next_date + timedelta(minutes=session_duration)
            
            # Check for conflicting appointments
            conflicting_appointments = Appointment.query.filter(
                Appointment.doctor_id == therapist_id,
                Appointment.status != AppointmentStatus.CANCELLED,
                Appointment.date_time < session_end_time,
                (Appointment.date_time + timedelta(minutes=Appointment.duration)) > next_date
            ).all()
            
            if conflicting_appointments:
                # Skip this date and try the next one
                last_date = next_date
                continue
                
            # Create the new appointment as a copy of the original
            new_appointment = Appointment(
                patient_id=original_appointment.patient_id,
                doctor_id=original_appointment.doctor_id,
                date_time=next_date,
                duration=original_appointment.duration,
                type=original_appointment.type,
                status=AppointmentStatus.SCHEDULED,
                recurrence_pattern=original_appointment.recurrence_pattern,
                reason=original_appointment.reason
            )
            
            db.session.add(new_appointment)
            db.session.flush()  # Get the ID without committing
            
            # Create associated therapy session record
            therapy_session = TherapySession(
                appointment_id=new_appointment.appointment_id,
                session_type=original_therapy_session.session_type,
                treatment_plan_id=original_therapy_session.treatment_plan_id,
                session_goals=original_therapy_session.session_goals,
                focus_areas=original_therapy_session.focus_areas,
                progress_notes=""  # Progress notes will be empty for future sessions
            )
            
            db.session.add(therapy_session)
            
            created_appointments.append(new_appointment.appointment_id)
            last_date = next_date
            current_count += 1
        
        return created_appointments
    
    @staticmethod
    @jwt_required()
    def get_therapy_sessions():
        """Get therapy sessions for therapist or patient"""
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        role = claims.get("role")
        
        # Check if user is patient or therapist
        if role == "therapist":
            # For therapists - get all their scheduled sessions
            appointments = Appointment.query.filter(
                Appointment.doctor_id == current_user_id,
                Appointment.type == AppointmentType.THERAPY
            ).order_by(Appointment.date_time).all()
        elif role == "patient":
            # For patients - get all their therapy sessions
            appointments = Appointment.query.filter(
                Appointment.patient_id == current_user_id,
                Appointment.type == AppointmentType.THERAPY
            ).order_by(Appointment.date_time).all()
        else:
            return jsonify({
                "status": "error",
                "message": "Unauthorized access"
            }), 403
        
        # Format sessions for response
        sessions_data = []
        for appointment in appointments:
            # Get associated therapy session details
            therapy_session = TherapySession.query.filter_by(
                appointment_id=appointment.appointment_id
            ).first()
            
            # Get patient info
            patient = Patient.query.get(appointment.patient_id)
            patient_user = User.query.get(patient.patient_id) if patient else None
            
            # Get therapist info
            therapist = Therapist.query.get(appointment.doctor_id)
            therapist_user = User.query.get(therapist.therapist_id) if therapist else None
            
            sessions_data.append({
                "appointment_id": appointment.appointment_id,
                "patient": {
                    "id": patient.patient_id,
                    "name": f"{patient_user.first_name} {patient_user.last_name}" if patient_user else "Unknown"
                },
                "therapist": {
                    "id": therapist.therapist_id if therapist else None,
                    "name": f"{therapist_user.first_name} {therapist_user.last_name}" if therapist_user else "Unknown"
                },
                "date_time": appointment.date_time.isoformat(),
                "duration": appointment.duration,
                "status": appointment.status.value,
                "session_type": therapy_session.session_type if therapy_session else None,
                "session_goals": therapy_session.session_goals if therapy_session else None,
                "focus_areas": json.loads(therapy_session.focus_areas) if therapy_session and therapy_session.focus_areas else [],
                "recurrence_pattern": appointment.recurrence_pattern.value if appointment.recurrence_pattern else None
            })
        
        return jsonify({
            "status": "success",
            "data": sessions_data
        }), 200