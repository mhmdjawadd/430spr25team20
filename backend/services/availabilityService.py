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

    @staticmethod
    @jwt_required()
    def get_emergency_slots():
        """
        Get slots available for emergency appointments.
        This prioritizes immediate availability.
        """
        # Get query parameters
        doctor_id = request.args.get('doctor_id')
        
        # Get current time
        now = datetime.now()
        end_time = now + timedelta(hours=24)  # Next 24 hours
        
        # If no doctor_id provided, find all doctors who can handle emergencies
        if not doctor_id:
            emergency_doctors = Doctor.query.filter(Doctor.specialty.in_(["DOCTOR", "SURGEON"])).all()
            doctor_ids = [doctor.doctor_id for doctor in emergency_doctors]
        else:
            doctor_ids = [doctor_id]
        
        emergency_slots = []
        
        for doctor_id in doctor_ids:
            # Validate doctor exists
            doctor = Doctor.query.filter_by(doctor_id=doctor_id).first()
            if not doctor:
                continue
                
            doctor_user = User.query.get(doctor.doctor_id)
            
            # Get doctor's current appointment
            current_appointment = Appointment.query.filter(
                Appointment.doctor_id == doctor_id,
                Appointment.date_time <= now,
                now <= Appointment.date_time + timedelta(minutes=Appointment.duration),
                Appointment.status.in_([
                    AppointmentStatus.SCHEDULED,
                    AppointmentStatus.CONFIRMED,
                    AppointmentStatus.CHECKED_IN
                ])
            ).first()
            
            if current_appointment:
                # Doctor is busy, find the next available slot
                next_available_time = current_appointment.date_time + timedelta(minutes=current_appointment.duration)
            else:
                # Doctor is available now
                next_available_time = now
                
            # Get upcoming appointments to find gaps
            upcoming_appointments = Appointment.query.filter(
                Appointment.doctor_id == doctor_id,
                Appointment.date_time >= next_available_time,
                Appointment.date_time <= end_time,
                Appointment.status.in_([
                    AppointmentStatus.SCHEDULED,
                    AppointmentStatus.CONFIRMED,
                    AppointmentStatus.CHECKED_IN
                ])
            ).order_by(Appointment.date_time).all()
            
            # Current availability slot
            current_slot = {
                "doctor_id": doctor_id,
                "doctor_name": f"Dr. {doctor_user.first_name} {doctor_user.last_name}",
                "specialty": doctor.specialty.value,
                "start_time": next_available_time.isoformat(),
                "is_immediate": next_available_time == now,
                "can_be_rescheduled": False  # Emergency slots can't be rescheduled
            }
            
            # If there are upcoming appointments, end time is the next appointment
            if upcoming_appointments:
                current_slot["end_time"] = upcoming_appointments[0].date_time.isoformat()
            else:
                # If no upcoming appointments, available until end of day
                current_slot["end_time"] = end_time.isoformat()
                
            emergency_slots.append(current_slot)
        
        # Sort by availability (immediate first, then by start time)
        emergency_slots.sort(key=lambda x: (not x["is_immediate"], x["start_time"]))
        
        return jsonify({
            "status": "success",
            "emergency_slots": emergency_slots,
            "current_time": now.isoformat()
        }), 200