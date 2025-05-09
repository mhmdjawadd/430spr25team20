from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime, timedelta, time
from services.db import db
from models import User, Doctor, Patient, Appointment, AppointmentType, RecurrencePattern, Notification, Insurance, UserRole
from services.referralService import ReferralController
import calendar
import logging

logging.getLogger(__name__)
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
        
        
        
        
        # 3. Check if the slot is already booked
        # We'll define a 1-hour appointment slot (changed from 30 minutes)
        appointment_end = appointment_datetime + timedelta(minutes=60)
        
        # Make sure to use correct field name from your model (date_time instead of appointment_datetime)
        existing_appointments = Appointment.query.filter(
            Appointment.doctor_id == doctor.doctor_id,
            Appointment.date_time >= appointment_datetime.replace(hour=0, minute=0, second=0),  # Start of day
            Appointment.date_time < appointment_datetime.replace(hour=23, minute=59, second=59),  # End of day
            
        ).all()
        
        # Check for conflicts
        for existing in existing_appointments:
            existing_start = existing.date_time
            existing_end = existing_start + timedelta(minutes=60)  # Changed from 30 to 60 minutes
            
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
                
                "insurance": insurance_info,
                
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
    def cancel_appointment():
        """
        Cancel an existing appointment by deleting it from the database and notify relevant parties
        
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
            
            # Store appointment details before deletion for response and notifications
            appointment_details = {
                "appointment_id": appointment.appointment_id,
                "patient_id": appointment.patient_id,
                "doctor_id": appointment.doctor_id,
                "date_time": appointment.date_time.strftime("%Y-%m-%d %H:%M"),
                "patient_name": patient.full_name() if patient else "Unknown",
                "doctor_name": f"Dr. {doctor_user.first_name} {doctor_user.last_name}" if doctor_user else "Unknown"
            }
            
            if patient and doctor_user:
                # Create cancellation notification for patient
                patient_notification = Notification(
                    user_id=patient.patient_id,
                    message=f"Appointment with Dr. {doctor_user.first_name} {doctor_user.last_name} on {appointment.date_time.strftime('%Y-%m-%d at %H:%M')} has been cancelled. Reason: {reason}",
                    scheduled_time=datetime.now()
                )
                db.session.add(patient_notification)
                
                # Create cancellation notification for doctor
                doctor_notification = Notification(
                    user_id=doctor_user.user_id,
                    message=f"Appointment with {patient.full_name()} on {appointment.date_time.strftime('%Y-%m-%d at %H:%M')} has been cancelled. Reason: {reason}",
                    scheduled_time=datetime.now()
                )
                db.session.add(doctor_notification)
                
                # If patient has a caregiver, notify them too
                if patient.caregiver_id:
                    caregiver_notification = Notification(
                        user_id=patient.caregiver_id,
                        message=f"Appointment for {patient.full_name()} with Dr. {doctor_user.first_name} {doctor_user.last_name} on {appointment.date_time.strftime('%Y-%m-%d at %H:%M')} has been cancelled.",
                        scheduled_time=datetime.now()
                    )
                    db.session.add(caregiver_notification)
            
            # Delete the appointment from the database
            print(f"Deleting appointment ID: {appointment.appointment_id}")
            db.session.delete(appointment)
            
            # Commit changes
            db.session.commit()
            
            # If requested, notify other patients about the availability
            response_data = {
                "message": "Appointment cancelled and deleted successfully",
                "appointment_id": appointment_details["appointment_id"],
                "patient": appointment_details["patient_name"],
                "doctor": appointment_details["doctor_name"],
                "date_time": appointment_details["date_time"]
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
            print(f"Error deleting appointment: {str(e)}")
            return jsonify({"error": f"Failed to cancel appointment: {str(e)}"}), 500




    @staticmethod
    def get_doctor_availability_range():
        """
        Get a doctor's availability over a date range considering their hourly slots
        and existing appointments.
        
        Expected request body:
        {
            "doctor_id": int,
            "start_date": "YYYY-MM-DD",
            "end_date": "YYYY-MM-DD"
        }
        
        Returns JSON with availability by date
        """
        # Get query parameters
        data = request.get_json()
        doctor_id = data.get('doctor_id')
        start_date_str = data.get('start_date')  # Format YYYY-MM-DD
        end_date_str = data.get('end_date')      # Format YYYY-MM-DD
        
        print('Fetching availability range for doctor:', doctor_id, 'from:', start_date_str, 'to:', end_date_str)
        
        if not doctor_id:
            return jsonify({"error": "Missing doctor_id parameter"}), 400
        
        if not start_date_str or not end_date_str:
            return jsonify({"error": "Missing date range parameters"}), 400
        
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
        
        # Limit range to 31 days to avoid performance issues
        date_diff = (end_date - start_date).days
        if date_diff > 31:
            return jsonify({"error": "Date range too large. Maximum 31 days"}), 400
        
        # Get doctor record
        doctor = Doctor.query.get(doctor_id)
        if not doctor:
            return jsonify({"error": "Doctor not found"}), 404
        
        # Initialize the result
        availability_by_date = {}
        
        # Loop through each date in the range
        current_date = start_date
        while current_date <= end_date:
            # Get day name in lowercase (monday, tuesday, etc.)
            day_name = current_date.strftime("%A").lower()
            
            # Check if doctor has slots for this day
            day_slots = doctor.availability.get(day_name, []) if doctor.availability else []
            
            # Only process if doctor has slots for this day
            if day_slots:
                # Check existing appointments for this doctor on this date
                day_start = datetime.combine(current_date, time(0, 0, 0))
                day_end = datetime.combine(current_date, time(23, 59, 59))
                
                booked_appointments = Appointment.query.filter(
                    Appointment.doctor_id == doctor_id,
                    Appointment.date_time >= day_start,
                    Appointment.date_time <= day_end
                ).all()
                
                # Convert booked appointments to a set of booked hour slots
                booked_hours = set()
                for appt in booked_appointments:
                    slot_hour = appt.date_time.hour
                    booked_hours.add(slot_hour)
                
                # Process each slot for this day
                formatted_slots = []
                for slot in day_slots:
                    # Parse slot (e.g., "09-10" -> start_hour=9, end_hour=10)
                    try:
                        start_hour = int(slot[0:2])
                        end_hour = int(slot[3:5])
                        
                        # Check if this slot is booked
                        is_booked = start_hour in booked_hours
                        
                        # Format for display
                        display_hour = start_hour if start_hour <= 12 else start_hour - 12
                        if display_hour == 0:
                            display_hour = 12
                        am_pm = "PM" if start_hour >= 12 else "AM"
                        
                        # Create the slot info
                        formatted_slot = {
                            "time": f"{display_hour}:00 {am_pm}",
                            "is_booked": is_booked,
                            "start": f"{start_hour:02d}:00",
                            "end": f"{end_hour:02d}:00"
                        }
                        formatted_slots.append(formatted_slot)
                    except (ValueError, IndexError) as e:
                        print(f"Error processing slot '{slot}': {e}")
                        continue
                
                # Add the formatted slots to the result
                availability_by_date[current_date.isoformat()] = formatted_slots
            
            # Move to the next day
            current_date += timedelta(days=1)
        
        return jsonify({
            "doctor_id": doctor_id,
            "doctor_name": f"Dr. {doctor.user.first_name} {doctor.user.last_name}",
            "availability": availability_by_date
        })
    
    @staticmethod
    def set_doctor_availability_range():
        """
        Sets the doctor's default weekly availability using hourly slots.
        
        Args:
            db_session: The SQLAlchemy Session object.
            data: A dictionary containing:
                - doctor_id (int): The ID of the doctor to update.
                - availability (dict): A dictionary where keys are day names (monday, tuesday, etc.)
                  and values are lists of hourly slots (e.g., ["09-10", "10-11", "14-15"])
        
        Returns:
            A dictionary with success message or error details.
        """
        data = request.get_json()
        doctor_id = data.get('doctor_id')
        availability_data = data.get('availability')
        
        if not doctor_id:
            return {"error": "Missing doctor_id parameter"}, 400
        if not isinstance(doctor_id, int):
            return {"error": "doctor_id must be an integer"}, 400
        
        if not availability_data or not isinstance(availability_data, dict):
            return {"error": "Missing or invalid availability data"}, 400
        
        # Fetch the doctor
        doctor = db.session.query(Doctor).get(doctor_id)
        if not doctor:
            return {"error": f"Doctor with ID {doctor_id} not found"}, 404
        
        # Initialize new availability JSON with empty slots for each day
        new_availability_json = {
            "monday": [],
            "tuesday": [],
            "wednesday": [],
            "thursday": [],
            "friday": [],
            "saturday": [],
            "sunday": []
        }
        
        # Process each day's slots
        days_of_week = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        
        for day in days_of_week:
            if day in availability_data and isinstance(availability_data[day], list):
                # Validate each slot
                valid_slots = []
                for slot in availability_data[day]:
                    # Check if slot is in the correct format (e.g., "09-10")
                    if isinstance(slot, str) and len(slot) == 5 and slot[2] == '-':
                        try:
                            start_hour = int(slot[0:2])
                            end_hour = int(slot[3:5])
                            
                            # Validate hours
                            if 0 <= start_hour < 24 and 0 <= end_hour < 24 and start_hour < end_hour:
                                valid_slots.append(slot)
                            else:
                                print(f"Warning: Invalid time range in slot '{slot}' for {day}")
                        except ValueError:
                            print(f"Warning: Could not parse hours in slot '{slot}' for {day}")
                    else:
                        print(f"Warning: Slot '{slot}' is not in the correct format (HH-HH) for {day}")
                
                # Update with validated slots
                new_availability_json[day] = valid_slots
        
        # Update the doctor's record
        try:
            doctor.availability = new_availability_json
            db.session.commit()
            
            return {
                "message": "Doctor availability updated successfully",
                "doctor_id": doctor_id,
                "doctor_name": f"Dr. {doctor.user.first_name} {doctor.user.last_name}",
                "current_availability": doctor.availability
            }, 200
        except Exception as e:
            db.session.rollback()
            print(f"Database error updating availability for Doctor ID {doctor_id}: {e}")
            return {"error": f"Failed to update availability: {e}"}, 500

    @staticmethod
    @jwt_required()
    def get_patient_appointments():
        """
        Get all appointments for the current patient
        """
        # Get the current user
        patient_id = get_jwt_identity()
        
        patient = Patient.query.get(patient_id)
        if not patient:
            return jsonify({"error": "User not found"}), 404
        
        # Query appointments for this patient
        appointments = Appointment.query.filter_by(patient_id=patient_id).order_by(Appointment.date_time).all()
        
        # Format appointments for response
        appointments_list = []
        for appointment in appointments:
            # Get doctor information
            doctor = User.query.get(appointment.doctor_id)
            doctor_info = Doctor.query.get(appointment.doctor_id)
            
            appointment_data = {
                "appointment_id": appointment.appointment_id,
                "date_time": appointment.date_time.strftime("%Y-%m-%d %H:%M"),
                "doctor_id": appointment.doctor_id,
                "doctor_name": f"Dr. {doctor.first_name} {doctor.last_name}" if doctor else "Unknown",
                "doctor_specialty": doctor_info.specialty.name if doctor_info and hasattr(doctor_info, "specialty") else "General",
                "type": appointment.type.name,
                "recurrence_pattern": appointment.recurrence_pattern.name,
                "status": "UPCOMING" if appointment.date_time > datetime.now() else "COMPLETED"
            }
            appointments_list.append(appointment_data)
        
        return jsonify(appointments_list), 200

    @staticmethod
    @jwt_required()
    def reschedule_appointment():
        """
        Reschedule an existing appointment to a new date/time
        
        Request body:
        {
            "appointment_id": int,
            "new_date_time": "YYYY-MM-DD-HH",
            "reason": string (optional)
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
        new_date_time_str = data.get('new_date_time')
        reason = data.get('reason', 'No reason provided')
        
        # Validate required fields
        if not appointment_id:
            return jsonify({"error": "Missing required field: appointment_id"}), 400
            
        if not new_date_time_str:
            return jsonify({"error": "Missing required field: new_date_time"}), 400
            
        # Parse the new date time
        try:
            new_date_time = datetime.strptime(new_date_time_str, "%Y-%m-%d-%H")
        except ValueError:
            return jsonify({"error": "Invalid date_time format. Use YYYY-MM-DD-HH"}), 400
            
        # Get the appointment
        appointment = Appointment.query.get(appointment_id)
        if not appointment:
            return jsonify({"error": "Appointment not found"}), 404
            
        # Check authorization - only the patient, doctor, or receptionist can reschedule
        is_authorized = (current_user.user_id == appointment.patient_id or
                        current_user.user_id == appointment.doctor_id or
                        current_user.role == UserRole.RECEPTIONIST)
                        
        if not is_authorized:
            return jsonify({"error": "Unauthorized to reschedule this appointment"}), 403
            
        # Save old appointment time for notifications
        old_date_time = appointment.date_time.strftime("%Y-%m-%d at %H:%M")
        
        # Check if the new time is valid
        new_date = new_date_time.date()
        new_time = new_date_time.time()
        weekday_num = new_date.weekday()
        
        # 1. Check if it's a weekday (doctor available)
        if weekday_num >= 5:  # Weekend
            return jsonify({"error": "Cannot reschedule to a weekend. Doctor is not available on weekends"}), 400
        
        # 2. Check if the time is within working hours (8 AM to 5 PM)
        if new_time < time(8, 0) or new_time >= time(17, 0):
            return jsonify({"error": "Appointment time must be between 8:00 AM and 5:00 PM"}), 400
        
        # 3. Check if the slot is already booked
        appointment_end = new_date_time + timedelta(minutes=60)
        
        existing_appointments = Appointment.query.filter(
            Appointment.doctor_id == appointment.doctor_id,
            Appointment.appointment_id != appointment.appointment_id,  # Exclude the current appointment
            Appointment.date_time >= new_date_time.replace(hour=0, minute=0, second=0),  # Start of day
            Appointment.date_time < new_date_time.replace(hour=23, minute=59, second=59),  # End of day
        ).all()
        
        # Check for conflicts
        for existing in existing_appointments:
            existing_start = existing.date_time
            existing_end = existing_start + timedelta(minutes=60)
            
            # Check if new appointment overlaps with existing one
            if (new_date_time < existing_end and appointment_end > existing_start):
                return jsonify({
                    "error": "Time slot not available. Doctor already has an appointment at this time.",
                    "conflict_with": existing_start.strftime("%H:%M")
                }), 409
                
        try:
            # Get patient and doctor information for notifications
            patient = Patient.query.get(appointment.patient_id) 
            doctor_user = User.query.get(appointment.doctor_id)
            
            # Update the appointment date and time
            appointment.date_time = new_date_time
            
            # Create notification for doctor
            if doctor_user:
                doctor_notification = Notification(
                    user_id=doctor_user.user_id,
                    appointment_id=appointment.appointment_id,
                    message=f"Appointment with {patient.full_name() if patient else 'Unknown'} has been rescheduled from {old_date_time} to {new_date_time.strftime('%Y-%m-%d at %H:%M')}. Reason: {reason}",
                    scheduled_time=datetime.now()
                )
                db.session.add(doctor_notification)
            
            # Create notification for patient
            if patient:
                patient_notification = Notification(
                    user_id=patient.patient_id,
                    appointment_id=appointment.appointment_id,
                    message=f"Your appointment with Dr. {doctor_user.first_name} {doctor_user.last_name if doctor_user else 'Unknown'} has been rescheduled from {old_date_time} to {new_date_time.strftime('%Y-%m-%d at %H:%M')}. Reason: {reason}",
                    scheduled_time=datetime.now()
                )
                db.session.add(patient_notification)
                
                # If patient has a caregiver, notify them too
                if patient.caregiver_id:
                    caregiver_notification = Notification(
                        user_id=patient.caregiver_id,
                        message=f"Appointment for {patient.full_name()} with Dr. {doctor_user.first_name} {doctor_user.last_name if doctor_user else 'Unknown'} has been rescheduled from {old_date_time} to {new_date_time.strftime('%Y-%m-%d at %H:%M')}",
                        scheduled_time=datetime.now()
                    )
                    db.session.add(caregiver_notification)
            
            # Commit changes
            db.session.commit()
            
            return jsonify({
                "message": "Appointment rescheduled successfully",
                "appointment_id": appointment.appointment_id,
                "old_date_time": old_date_time,
                "new_date_time": new_date_time.strftime("%Y-%m-%d %H:%M"),
                "doctor": f"Dr. {doctor_user.first_name} {doctor_user.last_name}" if doctor_user else "Unknown",
                "patient": patient.full_name() if patient else "Unknown"
            }), 200
            
        except Exception as e:
            db.session.rollback()
            print(f"Error rescheduling appointment: {str(e)}")
            return jsonify({"error": f"Failed to reschedule appointment: {str(e)}"}), 500