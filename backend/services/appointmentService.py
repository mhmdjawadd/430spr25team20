from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime, timedelta, time
from services.db import db
from models import User, Doctor, Patient, Appointment, AppointmentStatus, AppointmentType, RecurrencePattern, Notification, Insurance

class AppointmentController:
   
    @staticmethod
    def get_doctor_availability():
        # Get query parameters
        data = request.get_json()
        name = data.get('name')
        date_str = data.get('date')  # Expect format YYYY-MM-DD
        
        print('Fetching availability for doctor:', name, 'on date:', date_str)
        
        if date_str:
            try:
                date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
        
        availability = Doctor.get_availability(db.session, name, date)

        return jsonify(availability)
        
    @staticmethod
    def verify_insurance_coverage(patient_id, doctor_id):
        """
        Helper method to verify insurance coverage for an appointment
        Returns (is_verified, coverage_amount, patient_responsibility, message)
        """
        patient = Patient.query.get(patient_id)
        doctor = Doctor.query.get(doctor_id)
        
        if not patient:
            return False, 0, 100, "Patient not found"
        
        if not doctor:
            return False, 0, 100, "Doctor not found"
            
        # Get insurance information
        insurance = Insurance.query.get(patient.patient_id)
        if not insurance:
            return False, 0, 100, "No insurance on file"
            
        # Standard appointment cost for simplicity
        base_cost = 100.0
        
        # Calculate coverage based on doctor specialty and base cost
        covered_amount, patient_responsibility = insurance.calculate_coverage(
            doctor_specialty=doctor.specialty.value,
            base_cost=base_cost
        )
        
        # Determine if coverage is sufficient (any coverage is considered verified)
        is_verified = covered_amount > 0
        verification_message = (
            f"Insurance verified: {insurance.provider_name}, "
            f"Coverage: ${covered_amount:.2f}, "
            f"Patient Responsibility: ${patient_responsibility:.2f}"
        )
        
        return is_verified, covered_amount, patient_responsibility, verification_message

    @staticmethod
    @jwt_required()
    def book_appointment():
        """
        Book an appointment with a doctor after checking availability
        
        Request body:
        {
            "doctor_id": int,
            "date_time": "YYYY-MM-DD HH:MM:SS",
            "appointment_type": string (CONSULTATION, FOLLOWUP, etc.),
            "verify_insurance": boolean (optional, defaults to true)
            "notes": string (optional)
        }
        """
        # Get the current user
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user:
            return jsonify({"error": "User not found"}), 404
        
        # Get request data
        data = request.get_json()
        patient_id = ''
        if current_user.role.name == "PATIENT":
            patient_id = current_user.user_id
        elif current_user.role.name != "PATIENT" :
            if "patient_id" not in data:
                return jsonify({"error": "Missing patient_id for non-patient users"}), 400
            patient_id = data["patient_id"] 
        else:
            return jsonify({"error": "Unauthorized action"}), 403

        # Validate required fields
        required_fields = ["doctor_id", "date_time"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Get patient record
        patient = Patient.query.filter_by(patient_id=patient_id).first()
        if not patient:
            return jsonify({"error": "Patient record not found"}), 404
        
        # Get doctor record
        doctor = Doctor.query.get(data["doctor_id"])
        if not doctor:
            return jsonify({"error": "Doctor not found"}), 404
        
        # Parse appointment datetime
        try:
            appointment_datetime = datetime.strptime(data["date_time"], "%Y-%m-%d-%H")
        except ValueError:
            return jsonify({"error": "Invalid date_time format. Use YYYY MM DD HH"}), 400
        
        # Validate appointment type
        try:
            appointment_type = AppointmentType[data["appointment_type"].upper()]
        except KeyError:
            valid_types = ", ".join([t.name for t in AppointmentType])
            return jsonify({"error": f"Invalid appointment type. Valid types: {valid_types}"}), 400
        
        # Check if the requested time is within doctor's available slots
        appointment_date = appointment_datetime.date()
        appointment_time = appointment_datetime.time()
        weekday_num = appointment_date.weekday()
        
        # 1. Check if it's a weekday (doctor available)
        if weekday_num >= 5:  # Weekend
            return jsonify({"error": "Doctor is not available on weekends"}), 400
        
        # 2. Check if the time is within working hours (8 AM to 5 PM)
        if appointment_time < time(8, 0) or appointment_time >= time(17, 0):
            return jsonify({"error": "Appointment time must be between 8:00 AM and 5:00 PM"}), 400
        
        # 3. Check if the slot is already booked
        # We'll define a 30-minute appointment slot
        appointment_end = appointment_datetime + timedelta(minutes=30)
        
        # Make sure to use correct field name from your model (date_time instead of appointment_datetime)
        existing_appointments = Appointment.query.filter(
            Appointment.doctor_id == doctor.doctor_id,
            Appointment.date_time >= appointment_datetime.replace(hour=0, minute=0, second=0),  # Start of day
            Appointment.date_time < appointment_datetime.replace(hour=23, minute=59, second=59),  # End of day
            Appointment.status != AppointmentStatus.CANCELLED  # Don't count cancelled appointments
        ).all()
        
        # Check for conflicts
        for existing in existing_appointments:
            existing_start = existing.date_time  # Using date_time from your model
            existing_end = existing_start + timedelta(minutes=30)
            
            # Check if new appointment overlaps with existing one
            if (appointment_datetime < existing_end and appointment_end > existing_start):
                return jsonify({
                    "error": "Time slot not available. Doctor already has an appointment at this time.",
                    "conflict_with": existing_start.strftime("%H:%M")
                }), 409
        
        # Verify insurance if requested (default to True)
        verify_insurance = data.get("verify_insurance", True)
        
        # Insurance verification
        base_cost = 100.0  # Standard appointment cost
        insurance_verified = False
        insurance_coverage_amount = 0.0
        patient_responsibility = base_cost
        insurance_message = "Insurance verification not requested"
        
        if verify_insurance:
            insurance_verified, insurance_coverage_amount, patient_responsibility, insurance_message = AppointmentController.verify_insurance_coverage(
                patient_id=patient.patient_id,
                doctor_id=doctor.doctor_id
            )
            
        # If we get here, the time slot is available
        # Create new appointment
        new_appointment = Appointment(
            patient_id=patient.patient_id,
            doctor_id=doctor.doctor_id,
            date_time=appointment_datetime,
            status=AppointmentStatus.SCHEDULED,
            type=appointment_type,
            base_cost=base_cost,
            insurance_verified=insurance_verified,
            insurance_coverage_amount=insurance_coverage_amount,
            patient_responsibility=patient_responsibility,
            billing_status="pending"
        )
        
        try:
            # Save to database
            db.session.add(new_appointment)
            db.session.commit()
            
            # Create notification for doctor
            doctor_notification = Notification(
                user_id=doctor.doctor_id,
                appointment_id=new_appointment.appointment_id,
                message=f"New appointment scheduled with {patient.user.first_name} {patient.user.last_name} on {appointment_datetime.strftime('%Y-%m-%d at %H:%M')}",
                scheduled_time=appointment_datetime - timedelta(hours=1)
            )
            
            # Create confirmation notification for patient
            patient_notification = Notification(
                user_id=patient.patient_id,
                appointment_id=new_appointment.appointment_id,
                message=f"Appointment confirmed with Dr. {doctor.user.first_name} {doctor.user.last_name} on {appointment_datetime.strftime('%Y-%m-%d at %H:%M')}",
                scheduled_time=appointment_datetime - timedelta(hours=1)
            )
            
            db.session.add(doctor_notification)
            db.session.add(patient_notification)
            db.session.commit()
            
            # Prepare insurance information for response
            insurance_info = None
            if verify_insurance:
                insurance_info = {
                    "verified": insurance_verified,
                    "coverage_amount": insurance_coverage_amount,
                    "patient_responsibility": patient_responsibility,
                    "message": insurance_message
                }
            
            return jsonify({
                "message": "Appointment booked successfully",
                "appointment_id": new_appointment.appointment_id,
                "appointment_date": new_appointment.date_time.strftime("%Y-%m-%d %H:%M"),
                "doctor_name": f"Dr. {doctor.user.first_name} {doctor.user.last_name}",
                "status": new_appointment.status.name,
                "insurance": insurance_info,
                "billing_status": new_appointment.billing_status
            }), 201
            
        except Exception as e:
            db.session.rollback()
            print(f"Error booking appointment: {str(e)}")
            return jsonify({"error": f"Failed to book appointment: {str(e)}"}), 500