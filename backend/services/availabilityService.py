from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime, timedelta
from backend.models.appointment import Appointment
from backend.models.base import AppointmentStatus
from services.db import db
from models import Doctor, ORAvailability

class AvailabilityController:
    @staticmethod
    @jwt_required()
    def set_availability():
        """Set available time slots for a doctor"""
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        role = claims.get("role")
        
        if role not in ["doctor", "surgeon"]:
            return jsonify({
                "status": "error",
                "message": "Only doctors can set availability"
            }), 403
            
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No data provided"}), 400
            
        # Get doctor record
        doctor = Doctor.query.filter_by(doctor_id=current_user_id).first()
        if not doctor:
            return jsonify({"status": "error", "message": "Doctor profile not found"}), 404
            
        # Process availability data
        start_time = datetime.fromisoformat(data.get('start_time').replace('Z', '+00:00'))
        end_time = datetime.fromisoformat(data.get('end_time').replace('Z', '+00:00'))
        
        # Create availability slot
        availability = ORAvailability(
            surgeon_id=doctor.doctor_id,
            start_time=start_time,
            end_time=end_time,
            status='available'
        )
        
        try:
            db.session.add(availability)
            db.session.commit()
            return jsonify({
                "status": "success",
                "message": "Availability set successfully"
            }), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({
                "status": "error", 
                "message": f"Failed to set availability: {str(e)}"
            }), 500
        

                
    
    @staticmethod
    @jwt_required()
    def check_availability():
            """Get available time slots for a doctor"""
            # Get query parameters
            doctor_id = request.args.get('doctor_id')
            start_date_str = request.args.get('start_date')
            end_date_str = request.args.get('end_date')
            
            # Default time range: today to 14 days ahead if not specified
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            default_end = today + timedelta(days=14)
            
            # Parse dates or use defaults
            try:
                if start_date_str:
                    start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
                else:
                    start_date = today
                    
                if end_date_str:
                    end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
                else:
                    end_date = default_end
            except ValueError:
                return jsonify({
                    "status": "error",
                    "message": "Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"
                }), 400
            
            # If no doctor_id provided, check if current user is a doctor
            if not doctor_id:
                current_user_id = get_jwt_identity()
                claims = get_jwt()
                role = claims.get("role")
                
                if role in ["doctor", "surgeon"]:
                    doctor = Doctor.query.filter_by(doctor_id=current_user_id).first()
                    if doctor:
                        doctor_id = doctor.doctor_id
                
                if not doctor_id:
                    return jsonify({
                        "status": "error",
                        "message": "No doctor ID provided and current user is not a doctor"
                    }), 400
            
            # Validate doctor exists
            doctor = Doctor.query.filter_by(doctor_id=doctor_id).first()
            if not doctor:
                return jsonify({
                    "status": "error",
                    "message": f"Doctor with ID {doctor_id} not found"
                }), 404
                
            # Query availability
            available_slots = ORAvailability.query.filter(
                ORAvailability.surgeon_id == doctor_id,
                ORAvailability.start_time >= start_date,
                ORAvailability.end_time <= end_date,
                ORAvailability.status == 'available'
            ).all()
            
            # Query booked appointments to exclude them
            booked_appointments = Appointment.query.filter(
                Appointment.doctor_id == doctor_id,
                Appointment.date_time >= start_date,
                Appointment.date_time <= end_date,
                Appointment.status.in_([
                    AppointmentStatus.SCHEDULED,
                    AppointmentStatus.CONFIRMED,
                    AppointmentStatus.CHECKED_IN
                ])
            ).all()
            
            # Convert to list of dictionaries for JSON response
            available_slots_list = []
            for slot in available_slots:
                # Check if slot overlaps with any booked appointment
                is_available = True
                for appointment in booked_appointments:
                    appt_end_time = appointment.date_time + timedelta(minutes=appointment.duration)
                    if (slot.start_time <= appointment.date_time < slot.end_time or
                        slot.start_time < appt_end_time <= slot.end_time):
                        is_available = False
                        break
                
                if is_available:
                    available_slots_list.append({
                        "availability_id": slot.or_id,
                        "doctor_id": slot.surgeon_id,
                        "start_time": slot.start_time.isoformat(),
                        "end_time": slot.end_time.isoformat(),
                        "duration_minutes": int((slot.end_time - slot.start_time).total_seconds() / 60)
                    })
            
            return jsonify({
                "status": "success",
                "doctor_id": doctor_id,
                "available_slots": available_slots_list
            }), 200