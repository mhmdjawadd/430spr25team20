from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime, timedelta, time
from services.db import db
from models import User, Doctor, Patient, Appointment, AppointmentType, RecurrencePattern, Notification, Insurance, UserRole
from services.referralService import ReferralController
import calendar

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
    def generate_recurring_appointments(initial_appointment, recurrence_pattern, occurrences=5):
        """
        Generate future appointments based on the recurrence pattern
        
        Args:
            initial_appointment: The first appointment in the series
            recurrence_pattern: The pattern for repetition (weekly, biweekly, monthly)
            occurrences: Number of recurring appointments to generate (default: 5)
            
        Returns:
            list: List of appointment objects (not yet persisted)
        """
        recurring_appointments = []
        base_date = initial_appointment.date_time
        
        for i in range(1, occurrences + 1):  # Skip the initial appointment (i=0)
            if recurrence_pattern == RecurrencePattern.WEEKLY:
                next_date = base_date + timedelta(days=7 * i)
            elif recurrence_pattern == RecurrencePattern.BIWEEKLY:
                next_date = base_date + timedelta(days=14 * i)
            elif recurrence_pattern == RecurrencePattern.MONTHLY:
                # Handle month incrementation properly
                month = base_date.month - 1 + i  # -1 since we start from 1 month later
                year = base_date.year + month // 12
                month = month % 12 + 1  # Convert back to 1-12 range
                
                # Handle day of month edge cases (e.g., Feb 30 -> Feb 28/29)
                day = min(base_date.day, calendar.monthrange(year, month)[1])
                
                next_date = base_date.replace(year=year, month=month, day=day)
            else:
                continue  # Skip if pattern is NONE or unrecognized
                
            # Skip weekends
            if next_date.weekday() >= 5:  # 5=Saturday, 6=Sunday
                continue
                
            # Create a new appointment
            new_appt = Appointment(
                patient_id=initial_appointment.patient_id,
                doctor_id=initial_appointment.doctor_id,
                date_time=next_date,
                type=AppointmentType.RECURRING,  # Mark as part of a recurring series
                recurrence_pattern=recurrence_pattern,
                
                base_cost=initial_appointment.base_cost,
                insurance_verified=initial_appointment.insurance_verified,
                insurance_coverage_amount=initial_appointment.insurance_coverage_amount,
                patient_responsibility=initial_appointment.patient_responsibility,
                billing_status="pending"
            )
            recurring_appointments.append(new_appt)
            
        return recurring_appointments

    @staticmethod
    @jwt_required()
    def book_appointment():
        """
        Book an appointment with a doctor after checking availability
        
        Request body:
        {
            "doctor_id": int,
            "date_time": "YYYY-MM-DD-HH",
            "appointment_type": string (REGULAR, RECURRING, EMERGENCY),
            "verify_insurance": boolean (optional, defaults to true),
            "notes": string (optional),
            "recurrence_pattern": string (optional, WEEKLY, BIWEEKLY, MONTHLY),
            "recurrence_count": int (optional, number of recurring appointments)
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
        elif current_user.role.name != "PATIENT":
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
            
        # Get doctor's user record to check specialty
        doctor_user = User.query.get(doctor.doctor_id)
        if not doctor_user:
            return jsonify({"error": "Doctor user record not found"}), 404
            
        # Check if appointment with specialist (surgeon or therapist) requires a referral
        if doctor_user.role in [UserRole.SURGEON, UserRole.THERAPIST]:
            # Check if patient has a valid referral to this specialist
            has_referral = ReferralController.patient_has_valid_referral(patient_id, doctor.doctor_id)
            if not has_referral:
                return jsonify({
                    "error": "Cannot book appointment with this specialist. A referral from a general doctor is required.",
                    "message": "Please consult with a general doctor first to get a referral."
                }), 403
        
        # Parse appointment datetime
        try:
            appointment_datetime = datetime.strptime(data["date_time"], "%Y-%m-%d-%H")
        except ValueError:
            return jsonify({"error": "Invalid date_time format. Use YYYY-MM-DD-HH"}), 400
        
        # Validate appointment type
        try:
            appointment_type = AppointmentType[data["appointment_type"].upper()]
        except KeyError:
            valid_types = ", ".join([t.name for t in AppointmentType])
            return jsonify({"error": f"Invalid appointment type. Valid types: {valid_types}"}), 400
        
        # For recurring appointments, validate recurrence pattern
        recurrence_pattern = RecurrencePattern.NONE
        if appointment_type == AppointmentType.RECURRING:
            if "recurrence_pattern" not in data:
                return jsonify({"error": "Missing recurrence_pattern for recurring appointment"}), 400
                
            try:
                recurrence_pattern = RecurrencePattern[data["recurrence_pattern"].upper()]
                if recurrence_pattern == RecurrencePattern.NONE:
                    return jsonify({"error": "Invalid recurrence pattern for recurring appointment"}), 400
            except KeyError:
                valid_patterns = ", ".join([p.name for p in RecurrencePattern if p != RecurrencePattern.NONE])
                return jsonify({"error": f"Invalid recurrence pattern. Valid patterns: {valid_patterns}"}), 400
                
        recurrence_count = data.get("recurrence_count", 5)  # Default to 5 occurrences
        if not isinstance(recurrence_count, int) or recurrence_count < 1:
            return jsonify({"error": "recurrence_count must be a positive integer"}), 400
        
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
            
            type=appointment_type,
            recurrence_pattern=recurrence_pattern,
            base_cost=base_cost,
            insurance_verified=insurance_verified,
            insurance_coverage_amount=insurance_coverage_amount,
            patient_responsibility=patient_responsibility,
            billing_status="pending"
        )
        
        try:
            # Save to database
            db.session.add(new_appointment)
            db.session.flush()  # Get the ID without committing
            
            # Generate recurring appointments if needed
            recurring_appointments = []
            if appointment_type == AppointmentType.RECURRING and recurrence_pattern != RecurrencePattern.NONE:
                recurring_appointments = AppointmentController.generate_recurring_appointments(
                    new_appointment, recurrence_pattern, recurrence_count
                )
                
                # Add all recurring appointments to session
                for appt in recurring_appointments:
                    db.session.add(appt)
            
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
            
            # Prepare recurring appointment information for response
            recurring_info = None
            if recurring_appointments:
                recurring_info = {
                    "count": len(recurring_appointments),
                    "pattern": recurrence_pattern.name,
                    "dates": [appt.date_time.strftime("%Y-%m-%d %H:%M") for appt in recurring_appointments]
                }
            
            return jsonify({
                "message": "Appointment booked successfully",
                "appointment_id": new_appointment.appointment_id,
                "appointment_date": new_appointment.date_time.strftime("%Y-%m-%d %H:%M"),
                "doctor_name": f"Dr. {doctor.user.first_name} {doctor.user.last_name}",
                "status": new_appointment.status.name,
                "insurance": insurance_info,
                "billing_status": new_appointment.billing_status,
                "recurring_appointments": recurring_info
            }), 201
            
        except Exception as e:
            db.session.rollback()
            print(f"Error booking appointment: {str(e)}")
            return jsonify({"error": f"Failed to book appointment: {str(e)}"}), 500
            
    @staticmethod
    @jwt_required()
    def get_recurring_appointments(appointment_id):
        """
        Get all recurring appointments in a series
        """
        # Get the current user
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user:
            return jsonify({"error": "User not found"}), 404
            
        # Get the initial appointment
        appointment = Appointment.query.get(appointment_id)
        if not appointment:
            return jsonify({"error": "Appointment not found"}), 404
            
        # Check permissions
        if (current_user.user_id != appointment.patient_id and
            current_user.user_id != appointment.doctor_id and
            current_user.role.name not in ["RECEPTIONIST", "NURSE"]):
            return jsonify({"error": "Unauthorized to access this appointment"}), 403
            
        # Get all appointments for this patient with the same doctor and recurrence pattern
        recurring_appointments = Appointment.query.filter(
            Appointment.patient_id == appointment.patient_id,
            Appointment.doctor_id == appointment.doctor_id,
            Appointment.type == AppointmentType.RECURRING,
            Appointment.recurrence_pattern == appointment.recurrence_pattern,
            Appointment.date_time >= appointment.date_time,  # Only get current and future appointments
        ).order_by(Appointment.date_time).all()
        
        # Format the appointment data
        appointments_list = []
        for appt in recurring_appointments:
            appointments_list.append({
                "appointment_id": appt.appointment_id,
                "date_time": appt.date_time.strftime("%Y-%m-%d %H:%M"),
                "status": appt.status.name,
                "doctor_name": appt.doctor.user.full_name() if hasattr(appt.doctor, 'user') else "Unknown"
            })
            
        return jsonify({
            "patient_id": appointment.patient_id,
            "patient_name": appointment.patient.full_name() if hasattr(appointment, 'patient') else "Unknown",
            "doctor_id": appointment.doctor_id,
            "doctor_name": appointment.doctor.user.full_name() if hasattr(appointment.doctor, 'user') else "Unknown",
            "recurrence_pattern": appointment.recurrence_pattern.name,
            "appointments": appointments_list
        }), 200
        
    @staticmethod
    @jwt_required()
    def auto_schedule_appointments():
        """
        Automatically schedule recurring appointments for patients
        This endpoint is primarily for receptionists to batch process appointments
        """
        # Get the current user
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user:
            return jsonify({"error": "User not found"}), 404
            
        # Only receptionists can use this endpoint
        if current_user.role.name != "RECEPTIONIST":
            return jsonify({"error": "Only receptionists can auto-schedule appointments"}), 403
            
        # Get request data
        data = request.get_json()
        
        # Process different auto-scheduling options
        schedule_type = data.get("schedule_type", "recurring")
        results = {"scheduled": 0, "errors": 0, "details": []}
        
        if schedule_type == "recurring":
            # Schedule new recurring appointments based on patterns
            # Find appointments that need to be renewed (e.g., last in series is within a week)
            now = datetime.now()
            one_week_from_now = now + timedelta(days=7)
            
            # Get appointments that are recurring and the last one in the series is coming up soon
            patients_needing_renewal = db.session.query(
                Appointment.patient_id,
                Appointment.doctor_id,
                Appointment.recurrence_pattern,
                db.func.max(Appointment.date_time).label('last_date')
            ).filter(
                Appointment.type == AppointmentType.RECURRING,
                Appointment.recurrence_pattern != RecurrencePattern.NONE,
                
            ).group_by(
                Appointment.patient_id,
                Appointment.doctor_id,
                Appointment.recurrence_pattern
            ).having(
                db.func.max(Appointment.date_time) < one_week_from_now
            ).all()
            
            # Schedule new appointments for each pattern
            for patient_id, doctor_id, recurrence_pattern, last_date in patients_needing_renewal:
                try:
                    # Get the last appointment details
                    last_appointment = Appointment.query.filter(
                        Appointment.patient_id == patient_id,
                        Appointment.doctor_id == doctor_id,
                        Appointment.date_time == last_date
                    ).first()
                    
                    if not last_appointment:
                        continue
                        
                    # Calculate the next date based on recurrence pattern
                    if recurrence_pattern == RecurrencePattern.WEEKLY:
                        next_date = last_date + timedelta(days=7)
                    elif recurrence_pattern == RecurrencePattern.BIWEEKLY:
                        next_date = last_date + timedelta(days=14)
                    elif recurrence_pattern == RecurrencePattern.MONTHLY:
                        # Handle month incrementation
                        month = last_date.month % 12 + 1
                        year = last_date.year + (1 if month == 1 else 0)
                        day = min(last_date.day, calendar.monthrange(year, month)[1])
                        next_date = last_date.replace(year=year, month=month, day=day)
                    else:
                        continue
                        
                    # Skip weekends
                    while next_date.weekday() >= 5:  # 5=Saturday, 6=Sunday
                        next_date = next_date + timedelta(days=1)
                        
                    # Check if the time slot is available
                    appointment_end = next_date + timedelta(minutes=30)
                    
                    existing = Appointment.query.filter(
                        Appointment.doctor_id == doctor_id,
                        Appointment.date_time >= next_date.replace(hour=0, minute=0, second=0),
                        Appointment.date_time < next_date.replace(hour=23, minute=59, second=59),
                        
                    ).all()
                    
                    # Check for conflicts
                    conflict = False
                    for appt in existing:
                        existing_start = appt.date_time
                        existing_end = existing_start + timedelta(minutes=30)
                        
                        if (next_date < existing_end and appointment_end > existing_start):
                            conflict = True
                            break
                            
                    if conflict:
                        # Try the next day
                        next_date = next_date + timedelta(days=1)
                        # Skip weekends again
                        while next_date.weekday() >= 5:
                            next_date = next_date + timedelta(days=1)
                    
                    # Create the new appointment
                    new_appointment = Appointment(
                        patient_id=patient_id,
                        doctor_id=doctor_id,
                        date_time=next_date,
                        
                        type=AppointmentType.RECURRING,
                        recurrence_pattern=recurrence_pattern,
                        base_cost=last_appointment.base_cost,
                        insurance_verified=last_appointment.insurance_verified,
                        insurance_coverage_amount=last_appointment.insurance_coverage_amount,
                        patient_responsibility=last_appointment.patient_responsibility,
                        billing_status="pending"
                    )
                    
                    db.session.add(new_appointment)
                    
                    # Create notifications
                    patient = Patient.query.get(patient_id)
                    doctor = Doctor.query.get(doctor_id)
                    
                    if patient and doctor and hasattr(patient, 'user') and hasattr(doctor, 'user'):
                        # Notification for doctor
                        doctor_notification = Notification(
                            user_id=doctor_id,
                            appointment_id=new_appointment.appointment_id,
                            message=f"Recurring appointment automatically scheduled with {patient.user.first_name} {patient.user.last_name} on {next_date.strftime('%Y-%m-%d at %H:%M')}",
                            scheduled_time=next_date - timedelta(hours=24)
                        )
                        
                        # Notification for patient
                        patient_notification = Notification(
                            user_id=patient_id,
                            appointment_id=new_appointment.appointment_id,
                            message=f"Your recurring appointment with Dr. {doctor.user.first_name} {doctor.user.last_name} has been scheduled for {next_date.strftime('%Y-%m-%d at %H:%M')}",
                            scheduled_time=next_date - timedelta(hours=24)
                        )
                        
                        db.session.add(doctor_notification)
                        db.session.add(patient_notification)
                    
                    results["scheduled"] += 1
                    results["details"].append({
                        "patient_id": patient_id,
                        "doctor_id": doctor_id,
                        "date_time": next_date.strftime("%Y-%m-%d %H:%M"),
                        "pattern": recurrence_pattern.name
                    })
                    
                except Exception as e:
                    results["errors"] += 1
                    print(f"Error auto-scheduling appointment: {str(e)}")
            
            # Commit all changes
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                return jsonify({"error": f"Failed to auto-schedule appointments: {str(e)}"}), 500
        
        return jsonify({
            "message": "Auto-scheduling complete",
            "appointments_scheduled": results["scheduled"],
            "errors": results["errors"],
            "details": results["details"]
        }), 200

    @staticmethod
    @jwt_required()
    def cancel_appointment():
        """
        Cancel an existing appointment and notify relevant parties
        
        Request body:
        {
            "appointment_id": int,
            "reason": string (optional),
            "notify_availabilities": boolean (optional, defaults to true)
        }
        """
        # Get the current user
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user:
            return jsonify({"error": "User not found"}), 404
            
        # Get request data
        data = request.get_json()
        appointment_id = data.get('appointment_id')
        reason = data.get('reason', 'No reason provided')
        notify_availabilities = data.get('notify_availabilities', True)
        
        # Validate required fields
        if not appointment_id:
            return jsonify({"error": "Missing required field: appointment_id"}), 400
            
        # Get the appointment
        appointment = Appointment.query.get(appointment_id)
        if not appointment:
            return jsonify({"error": "Appointment not found"}), 404
            
        # Check authorization - only the patient, doctor, or receptionist can cancel
        is_authorized = (current_user.user_id == appointment.patient_id or
                        current_user.user_id == appointment.doctor_id or
                        current_user.role == UserRole.RECEPTIONIST)
                        
        if not is_authorized:
            return jsonify({"error": "Unauthorized to cancel this appointment"}), 403
            
        
            
        
        
        try:
            # Get patient and doctor information for notifications
            patient = Patient.query.get(appointment.patient_id) 
            doctor_user = User.query.get(appointment.doctor_id)
            
            if patient and doctor_user:
                # Create cancellation notification for patient
                patient_notification = Notification(
                    user_id=patient.patient_id,
                    appointment_id=appointment.appointment_id,
                    message=f"Appointment with Dr. {doctor_user.first_name} {doctor_user.last_name} on {appointment.date_time.strftime('%Y-%m-%d at %H:%M')} has been cancelled. Reason: {reason}",
                    scheduled_time=datetime.now()
                )
                db.session.add(patient_notification)
                
                # Create cancellation notification for doctor
                doctor_notification = Notification(
                    user_id=doctor_user.user_id,
                    appointment_id=appointment.appointment_id,
                    message=f"Appointment with {patient.full_name()} on {appointment.date_time.strftime('%Y-%m-%d at %H:%M')} has been cancelled. Reason: {reason}",
                    scheduled_time=datetime.now()
                )
                db.session.add(doctor_notification)
                
                # If patient has a caregiver, notify them too
                if patient.caregiver_id:
                    caregiver_notification = Notification(
                        user_id=patient.caregiver_id,
                        appointment_id=appointment.appointment_id,
                        message=f"Appointment for {patient.full_name()} with Dr. {doctor_user.first_name} {doctor_user.last_name} on {appointment.date_time.strftime('%Y-%m-%d at %H:%M')} has been cancelled.",
                        scheduled_time=datetime.now()
                    )
                    db.session.add(caregiver_notification)
            
            # Commit changes
            db.session.commit()
            
            # If requested, notify other patients about the availability
            response_data = {
                "message": "Appointment cancelled successfully",
                "appointment_id": appointment.appointment_id,
                "patient": patient.full_name() if patient else "Unknown",
                "doctor": f"Dr. {doctor_user.first_name} {doctor_user.last_name}" if doctor_user else "Unknown",
                "date_time": appointment.date_time.strftime("%Y-%m-%d %H:%M")
            }
            
            # Import here to avoid circular imports
            if notify_availabilities and current_user.role in [UserRole.DOCTOR, UserRole.RECEPTIONIST, UserRole.NURSE]:
                from services.reminderService import ReminderController
                
                # Create availability notifications in a separate request
                # This avoids making this transaction too large
                response_data["notify_availabilities"] = True
            
            return jsonify(response_data), 200
            
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Failed to cancel appointment: {str(e)}"}), 500