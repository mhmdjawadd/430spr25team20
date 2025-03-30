from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime, timedelta
from services.db import db
from models import User , AppointmentType ,AppointmentStatus , RecurrencePattern , Doctor , Patient, Appointment


class AppointmentController:
    
    @staticmethod
    @jwt_required()
    def create_appointment():
        """
        Create a new appointment. Only patients can create appointments.
        Requires authentication with a JWT token.
        """
        # Get current user's identity and claims from the token
        current_user_id = get_jwt_identity()
        
        
        
        
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({
                "status": "error", 
                "message": "No data provided"
            }), 400
            
        # Validate required fields
        required_fields = ['doctor_id', 'appointment_date', 'reason']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "status": "error",
                    "message": f"Missing required field: {field}"
                }), 400
        
        # Get patient record for the current user
        patient = Patient.query.filter_by(user_id=current_user_id).first()
        if not patient:
            return jsonify({
                "status": "error",
                "message": "Patient profile not found"
            }), 404
        
        # Check if doctor exists
        doctor = Doctor.query.get(data['doctor_id'])
        if not doctor:
            return jsonify({
                "status": "error",
                "message": "Doctor not found"
            }), 404
        
        # Parse appointment date
        try:
            appointment_date = datetime.fromisoformat(data['appointment_date'].replace('Z', '+00:00'))
        except ValueError:
            return jsonify({
                "status": "error",
                "message": "Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SS.sssZ)"
            }), 400
        recurrence_pattern = None
        if 'recurrence_pattern' in data and data['recurrence_pattern']:
            try:
                recurrence_pattern_value = data['recurrence_pattern'].upper()
                if not hasattr(RecurrencePattern, recurrence_pattern_value):
                    valid_patterns = [p.name for p in RecurrencePattern]
                    return jsonify({
                        "status": "error",
                        "message": f"Invalid recurrence pattern. Valid patterns are: {valid_patterns}"
                    }), 400
                recurrence_pattern = getattr(RecurrencePattern, recurrence_pattern_value)
            except Exception as e:
                return jsonify({
                    "status": "error",
                    "message": f"Error processing recurrence pattern: {str(e)}"
                }), 400
        appointment_type = data.get('type', 'REGULAR').upper()
        if not hasattr(AppointmentType, appointment_type):
            valid_types = [t.name for t in AppointmentType]
            return jsonify({
                "status": "error",
                "message": f"Invalid appointment type. Valid types are: {valid_types}"
            }), 400

        # Handle appointment status
        appointment_status = data.get('status', 'SCHEDULED').upper()
        if not hasattr(AppointmentStatus, appointment_status):
            valid_statuses = [s.name for s in AppointmentStatus]
            return jsonify({
                "status": "error",
                "message": f"Invalid appointment status. Valid statuses are: {valid_statuses}"
            }), 400
        # Create appointment
        new_appointment = Appointment(
        patient_id=patient.patient_id,
        doctor_id=data['doctor_id'],
        date_time=appointment_date,
        duration=data.get('duration', 30),  # Default to 30 minutes if not specified
        type=appointment_type,
        status=appointment_status,
        recurrence_pattern=recurrence_pattern,
        reason=data['reason'],
        
    )
        
        # Save to database
        try:
            db.session.add(new_appointment)
            db.session.commit()
            
            # After successfully creating the appointment, handle recurrence if specified
            if recurrence_pattern and recurrence_pattern != RecurrencePattern.NONE:
                # Get recurrence count or end date from request data, if provided
                recurrence_count = data.get('recurrence_count')
                recurrence_end_date = None
                if data.get('recurrence_end_date'):
                    try:
                        recurrence_end_date = datetime.fromisoformat(data['recurrence_end_date'].replace('Z', '+00:00'))
                    except ValueError:
                        # If invalid end date format, just use count
                        pass
                        
                # Generate recurring appointments
                recurring_appointment_ids = AppointmentController.generate_recurring_appointments(
                    new_appointment, 
                    recurrence_pattern,
                    end_date=recurrence_end_date,
                    count=recurrence_count
                )
                
                return jsonify({
                    "status": "success",
                    "message": "Appointment series created successfully",
                    "appointment_id": new_appointment.appointment_id,
                    "recurring_appointment_ids": recurring_appointment_ids
                }), 201
            
            return jsonify({
                "status": "success",
                "message": "Appointment created successfully",
                "appointment_id": new_appointment.appointment_id
            }), 201
            
        except Exception as e:
            db.session.rollback()
            return jsonify({
                "status": "error",
                "message": f"Failed to create appointment: {str(e)}"
            }), 500
    
    @staticmethod
    @jwt_required()
    def get_appointments():
        """
        Get appointments based on user role.
        Patients see their own appointments.
        Doctors see appointments assigned to them.
        Admins see all appointments.
        """
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        role = claims.get("role")
        
        if role == "patient":
            # Get patient's appointments
            patient = Patient.query.filter_by(user_id=current_user_id).first()
            if not patient:
                return jsonify({"status": "error", "message": "Patient profile not found"}), 404
                
            appointments = Appointment.query.filter_by(patient_id=patient.patient_id).all()
            
        elif role == "doctor":
            # Get doctor's appointments
            doctor = Doctor.query.filter_by(user_id=current_user_id).first()
            if not doctor:
                return jsonify({"status": "error", "message": "Doctor profile not found"}), 404
                
            appointments = Appointment.query.filter_by(doctor_id=doctor.doctor_id).all()
            
            
        else:
            return jsonify({
                "status": "error",
                "message": "Unauthorized role"
            }), 403
        
        # Convert appointments to JSON
        appointments_list = []
        for appointment in appointments:
            doctor = Doctor.query.get(appointment.doctor_id)
            doctor_user = User.query.get(doctor.user_id)
            
            patient = Patient.query.get(appointment.patient_id)
            patient_user = User.query.get(patient.user_id)
            
            appointments_list.append({
                "appointment_id": appointment.appointment_id,
                "doctor": {
                    "doctor_id": doctor.doctor_id,
                    "name": f"{doctor_user.first_name} {doctor_user.last_name}",
                },
                "patient": {
                    "patient_id": patient.patient_id,
                    "name": f"{patient_user.first_name} {patient_user.last_name}",
                },
                "appointment_date": appointment.appointment_date.isoformat(),
                "reason": appointment.reason,
                "status": appointment.status,
                "notes": appointment.notes
            })
        
        return jsonify({
            "status": "success",
            "appointments": appointments_list
        }), 200

    @staticmethod
    @jwt_required()
    def create_referral():
        """
        Create a new referral for a patient to another doctor.
        Only doctors can create referrals.
        """
        # Get current user's identity and claims from the token
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        role = claims.get("role")
        
        # Check if user is a doctor
        if role != "doctor":
            return jsonify({
                "status": "error",
                "message": "Only doctors can create referrals"
            }), 403
        
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({
                "status": "error", 
                "message": "No data provided"
            }), 400
            
        # Validate required fields
        required_fields = ['patient_id', 'referred_doctor_id', 'reason']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "status": "error",
                    "message": f"Missing required field: {field}"
                }), 400
        
        # Get the referring doctor (current user)
        referring_doctor = Doctor.query.filter_by(user_id=current_user_id).first()
        if not referring_doctor:
            return jsonify({
                "status": "error",
                "message": "Doctor profile not found"
            }), 404
        
        # Check if patient exists
        patient = Patient.query.get(data['patient_id'])
        if not patient:
            return jsonify({
                "status": "error",
                "message": "Patient not found"
            }), 404
        
        # Check if referred doctor exists
        referred_doctor = Doctor.query.get(data['referred_doctor_id'])
        if not referred_doctor:
            return jsonify({
                "status": "error",
                "message": "Referred doctor not found"
            }), 404
        
        # Make sure referred doctor is different from referring doctor
        if referring_doctor.doctor_id == referred_doctor.doctor_id:
            return jsonify({
                "status": "error",
                "message": "Cannot refer to yourself"
            }), 400
            
        # Import the Referral model (add this to your imports at the top)
        from models.refferal import Referral
        
        # Create referral
        new_referral = Referral(
            patient_id=patient.patient_id,
            referring_doctor_id=referring_doctor.doctor_id,
            specialist_id=referred_doctor.doctor_id,
            reason=data['reason'],
            status='pending'
        )
        
        # Save to database
        try:
            db.session.add(new_referral)
            db.session.commit()
            
            # create an appointment automatically
            if data.get('create_appointment', False) and data.get('appointment_date'):
                try:
                    # Parse appointment date
                    appointment_date = datetime.fromisoformat(data['appointment_date'].replace('Z', '+00:00'))
                    
                    # Create appointment with referred doctor
                    new_appointment = Appointment(
                        patient_id=patient.patient_id,
                        doctor_id=referred_doctor.doctor_id,
                        date_time=appointment_date,
                        reason=f"Referral: {data['reason']}",
                        status='pending',
                        
                        
                    )
                    
                    db.session.add(new_appointment)
                    db.session.commit()
                    
                    return jsonify({
                        "status": "success",
                        "message": "Referral and appointment created successfully",
                        "referral_id": new_referral.referral_id,
                        "appointment_id": new_appointment.appointment_id
                    }), 201
                    
                except ValueError:
                    # Rollback appointment but keep referral
                    db.session.rollback()
                    return jsonify({
                        "status": "warning",
                        "message": "Referral created but appointment failed due to invalid date format",
                        "referral_id": new_referral.referral_id
                    }), 201
            
            return jsonify({
                "status": "success",
                "message": "Referral created successfully",
                "referral_id": new_referral.referral_id
            }), 201
            
        except Exception as e:
            db.session.rollback()
            return jsonify({
                "status": "error",
                "message": f"Failed to create referral: {str(e)}"
            }), 500
    
    @staticmethod
    @jwt_required()
    def get_referrals():
        """
        Get referrals based on user role.
        Patients see referrals for them.
        Doctors see referrals they've made or received.
        Admins see all referrals.
        """
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        role = claims.get("role")
        
        # Import the Referral model
        from models.refferal import Referral
        
        if role == "patient":
            # Get patient's referrals
            patient = Patient.query.filter_by(user_id=current_user_id).first()
            if not patient:
                return jsonify({"status": "error", "message": "Patient profile not found"}), 404
                
            referrals = Referral.query.filter_by(patient_id=patient.patient_id).all()
            
        elif role == "doctor":
            # Get doctor's incoming and outgoing referrals
            doctor = Doctor.query.filter_by(user_id=current_user_id).first()
            if not doctor:
                return jsonify({"status": "error", "message": "Doctor profile not found"}), 404
                
            # Combining both referring and referred doctor referrals
            referring = Referral.query.filter_by(referring_doctor_id=doctor.doctor_id).all()
            referred_to = Referral.query.filter_by(referred_doctor_id=doctor.doctor_id).all()
            referrals = referring + referred_to
            
            
        else:
            return jsonify({
                "status": "error",
                "message": "Unauthorized role"
            }), 403
        
        # Convert referrals to JSON
        referrals_list = []
        for referral in referrals:
            # Get patient info
            patient = Patient.query.get(referral.patient_id)
            patient_user = User.query.get(patient.user_id)
            
            # Get referring doctor info
            referring_doctor = Doctor.query.get(referral.referring_doctor_id)
            referring_doctor_user = User.query.get(referring_doctor.user_id)
            
            # Get referred doctor info
            referred_doctor = Doctor.query.get(referral.referred_doctor_id)
            referred_doctor_user = User.query.get(referred_doctor.user_id)
            
            referrals_list.append({
                "referral_id": referral.referral_id,
                "patient": {
                    "patient_id": patient.patient_id,
                    "name": f"{patient_user.first_name} {patient_user.last_name}",
                },
                "referring_doctor": {
                    "doctor_id": referring_doctor.doctor_id,
                    "name": f"{referring_doctor_user.first_name} {referring_doctor_user.last_name}",
                },
                "referred_doctor": {
                    "doctor_id": referred_doctor.doctor_id,
                    "name": f"{referred_doctor_user.first_name} {referred_doctor_user.last_name}",
                },
                "reason": referral.reason,
                "notes": referral.notes,
                "date_created": referral.date_created.isoformat(),
                "status": referral.status
            })
        
        return jsonify({
            "status": "success",
            "referrals": referrals_list
        }), 200

    @staticmethod
    def generate_recurring_appointments(original_appointment, recurrence_pattern, end_date=None, count=None):
        """
        Generate recurring appointments based on the pattern
        This is called after creating the first appointment
        
        Parameters:
        - original_appointment: The first appointment in the series
        - recurrence_pattern: Pattern from RecurrencePattern enum
        - end_date: Optional end date for the recurrence
        - count: Optional number of occurrences
        
        Returns:
        - List of created appointment IDs
        """
        # Default to creating 6 recurrences if no end_date or count specified
        if not end_date and not count:
            count = 6
            
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
                # Handle month addition with appropriate date handling
                month = last_date.month + 1
                year = last_date.year + month // 12
                month = month % 12 if month % 12 else 12
                try:
                    next_date = last_date.replace(year=year, month=month)
                except ValueError:
                    # Handle case where the day doesn't exist in the next month
                    # e.g., January 31 -> February 28/29
                    if month in [4, 6, 9, 11] and last_date.day > 30:
                        next_date = last_date.replace(year=year, month=month, day=30)
                    elif month == 2:
                        # Check for leap year
                        if (year % 4 == 0 and year % 100 != 0) or year % 400 == 0:
                            max_day = 29
                        else:
                            max_day = 28
                        next_date = last_date.replace(year=year, month=month, day=min(last_date.day, max_day))
            elif recurrence_pattern == RecurrencePattern.QUARTERLY:
                # Add 3 months
                month = last_date.month + 3
                year = last_date.year + month // 12
                month = month % 12 if month % 12 else 12
                try:
                    next_date = last_date.replace(year=year, month=month)
                except ValueError:
                    # Handle case where the day doesn't exist
                    if month in [4, 6, 9, 11] and last_date.day > 30:
                        next_date = last_date.replace(year=year, month=month, day=30)
                    elif month == 2:
                        # Check for leap year
                        if (year % 4 == 0 and year % 100 != 0) or year % 400 == 0:
                            max_day = 29
                        else:
                            max_day = 28
                        next_date = last_date.replace(year=year, month=month, day=min(last_date.day, max_day))
            elif recurrence_pattern == RecurrencePattern.YEARLY:
                next_date = last_date.replace(year=last_date.year + 1)
            else:
                # No recurrence or unrecognized pattern
                break
                
            # Create the new appointment as a copy of the original
            new_appointment = Appointment(
                patient_id=original_appointment.patient_id,
                doctor_id=original_appointment.doctor_id,
                date_time=next_date,
                duration=original_appointment.duration,
                type=original_appointment.type,
                status=AppointmentStatus.SCHEDULED,  # Always start as scheduled
                recurrence_pattern=original_appointment.recurrence_pattern,
                reason=original_appointment.reason
            )
            
            try:
                db.session.add(new_appointment)
                db.session.commit()
                created_appointments.append(new_appointment.appointment_id)
                last_date = next_date
                current_count += 1
            except Exception as e:
                db.session.rollback()
                print(f"Error creating recurring appointment: {str(e)}")
                break
        
        return created_appointments

    @staticmethod
    @jwt_required()
    def get_patient_schedule():
        """
        Get a consolidated view of a patient's schedule including:
        - Upcoming appointments
        - Medication schedule
        - Regular check-ups for chronic conditions
        """
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        role = claims.get("role")
        
        # If not a patient or medical staff viewing a patient's schedule, unauthorized
        if role != "patient" and role not in ["doctor", "surgeon", "nurse"]:
            return jsonify({
                "status": "error",
                "message": "Unauthorized access to patient schedule"
            }), 403
        
        # Get query parameters
        patient_id = request.args.get('patient_id')
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        # If role is patient, can only access their own schedule
        if role == "patient":
            patient = Patient.query.filter_by(patient_id=current_user_id).first()
            if not patient:
                return jsonify({"status": "error", "message": "Patient profile not found"}), 404
            patient_id = patient.patient_id
        
        # If medical staff but no patient_id specified, return error
        elif role in ["doctor", "surgeon", "nurse"] and not patient_id:
            return jsonify({
                "status": "error", 
                "message": "Patient ID required for medical staff to view schedule"
            }), 400
        
        # Process date range
        today = datetime.now()
        try:
            if start_date_str:
                start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
            else:
                start_date = today
                
            if end_date_str:
                end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
            else:
                # Default to showing 30 days ahead
                end_date = today + timedelta(days=30)
        except ValueError:
            return jsonify({
                "status": "error",
                "message": "Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"
            }), 400
        
        # Get patient information
        patient = Patient.query.get(patient_id)
        if not patient:
            return jsonify({
                "status": "error",
                "message": "Patient not found"
            }), 404
        
        patient_user = User.query.get(patient.patient_id)
        
        # Prepare response with patient info
        response = {
            "status": "success",
            "patient": {
                "patient_id": patient.patient_id,
                "name": f"{patient_user.first_name} {patient_user.last_name}",
            },
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            }
        }
        
        # 1. Get upcoming appointments in the date range
        appointments = Appointment.query.filter(
            Appointment.patient_id == patient_id,
            Appointment.date_time >= start_date,
            Appointment.date_time <= end_date,
            Appointment.status.in_([
                AppointmentStatus.SCHEDULED,
                AppointmentStatus.CONFIRMED,
                AppointmentStatus.CHECKED_IN
            ])
        ).order_by(Appointment.date_time).all()
        
        appointments_list = []
        for appt in appointments:
            doctor = Doctor.query.get(appt.doctor_id)
            doctor_user = User.query.get(doctor.doctor_id)
            
            appointments_list.append({
                "appointment_id": appt.appointment_id,
                "date_time": appt.date_time.isoformat(),
                "duration": appt.duration,
                "type": appt.type.value,
                "status": appt.status.value,
                "reason": appt.reason,
                "doctor": f"Dr. {doctor_user.first_name} {doctor_user.last_name}",
                "doctor_specialty": doctor.specialty.value if hasattr(doctor, 'specialty') else "",
                "is_recurring": appt.recurrence_pattern != RecurrencePattern.NONE,
                "calendar_type": "appointment"
            })
        
        # 2. Get active prescriptions and their schedules
        from models.medical_record import MedicalRecord
        from models.perscription import Prescription
        
        # Get all medical records for this patient
        medical_records = MedicalRecord.query.filter_by(patient_id=patient_id).all()
        record_ids = [record.record_id for record in medical_records]
        
        # Query active prescriptions
        active_prescriptions = Prescription.query.filter(
            Prescription.record_id.in_(record_ids),
            (Prescription.end_date >= today) | (Prescription.end_date.is_(None))
        ).all()
        
        medication_schedules = []
        for prescription in active_prescriptions:
            # Simple algorithm to display medication in schedule
            # Assumes instructions contain timing information
            medication_schedules.append({
                "prescription_id": prescription.prescription_id,
                "medication_name": prescription.medication_name,
                "dosage": prescription.dosage,
                "instructions": prescription.instructions,
                "start_date": prescription.start_date.isoformat(),
                "end_date": prescription.end_date.isoformat() if prescription.end_date else None,
                "calendar_type": "medication"
            })
        
        # 3. Get chronic condition check-ups
        from models.chronic_condition import ChronicCondition
        
        chronic_conditions = ChronicCondition.query.filter_by(patient_id=patient_id).all()
        condition_checkups = []
        
        for condition in chronic_conditions:
            # For each chronic condition, add recommended check-up dates
            # This is a simplified approach - in reality, the frequency would depend on the condition
            condition_checkups.append({
                "condition_id": condition.condition_id,
                "name": condition.name,
                "recommended_checkup": (today + timedelta(days=90)).isoformat(),  # Example: quarterly check-up
                "last_tracked": None,  # Would be filled with actual tracking data
                "calendar_type": "condition_checkup"
            })
        
        # Combine all items into one consolidated schedule
        schedule_items = appointments_list + medication_schedules + condition_checkups
        
        # Sort by date for appointments (medications don't have specific times in this implementation)
        schedule_items.sort(key=lambda x: x.get("date_time", x.get("start_date", "9999-12-31")))
        
        response["schedule"] = schedule_items
        
        return jsonify(response), 200

    @staticmethod
    @jwt_required()
    def prioritize_appointment():
        """
        Prioritize an appointment by potentially rescheduling lower-priority appointments.
        This is used for emergency situations.
        """
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        role = claims.get("role")
        
        # Only medical staff can prioritize appointments
        if role not in ["doctor", "surgeon", "nurse"]:
            return jsonify({
                "status": "error",
                "message": "Only medical staff can prioritize appointments"
            }), 403
        
        data = request.get_json()
        if not data or not data.get('appointment_id'):
            return jsonify({
                "status": "error",
                "message": "Appointment ID is required"
            }), 400
        
        # Get the appointment to prioritize
        appointment = Appointment.query.get(data['appointment_id'])
        if not appointment:
            return jsonify({
                "status": "error",
                "message": "Appointment not found"
            }), 404
        
        # If already an emergency appointment, no need to prioritize
        if appointment.type == AppointmentType.EMERGENCY:
            return jsonify({
                "status": "success",
                "message": "Appointment is already marked as emergency priority"
            }), 200
        
        try:
            # Update appointment type to emergency
            appointment.type = AppointmentType.EMERGENCY
            
            # If appointment is not today, move it to today if requested
            reschedule_to_today = data.get('reschedule_to_today', False)
            if reschedule_to_today and appointment.date_time.date() > datetime.now().date():
                # Find a suitable time today
                doctor = Doctor.query.get(appointment.doctor_id)
                
                # Get all appointments for this doctor today
                today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                today_end = today_start + timedelta(days=1)
                
                today_appointments = Appointment.query.filter(
                    Appointment.doctor_id == doctor.doctor_id,
                    Appointment.date_time >= today_start,
                    Appointment.date_time < today_end,
                    Appointment.appointment_id != appointment.appointment_id,  # Exclude this appointment
                    Appointment.status.in_([
                        AppointmentStatus.SCHEDULED,
                        AppointmentStatus.CONFIRMED
                    ])
                ).order_by(Appointment.date_time).all()
                
                # Find the first available slot (simple algorithm)
                current_time = datetime.now()
                slot_found = False
                
                # If there are no other appointments today, use current time
                if not today_appointments:
                    new_time = current_time
                    slot_found = True
                else:
                    # Try to fit between existing appointments
                    for i in range(len(today_appointments)):
                        if i == 0 and current_time + timedelta(minutes=appointment.duration) <= today_appointments[0].date_time:
                            # Slot before first appointment
                            new_time = current_time
                            slot_found = True
                            break
                            
                        if i < len(today_appointments) - 1:
                            # Check gap between appointments
                            appt1_end = today_appointments[i].date_time + timedelta(minutes=today_appointments[i].duration)
                            appt2_start = today_appointments[i+1].date_time
                            
                            if appt1_end + timedelta(minutes=appointment.duration) <= appt2_start:
                                new_time = appt1_end
                                slot_found = True
                                break
                    
                    # If no slot found between appointments, add after the last one
                    if not slot_found:
                        last_appt = today_appointments[-1]
                        new_time = last_appt.date_time + timedelta(minutes=last_appt.duration)
                        slot_found = True
                
                if slot_found:
                    old_time = appointment.date_time
                    appointment.date_time = new_time
                    
                    # Create notification about rescheduling
                    patient_notification = Notification(
                        user_id=appointment.patient_id,
                        appointment_id=appointment.appointment_id,
                        type="emergency_reschedule",
                        message=f"Your appointment has been prioritized as urgent and moved from {old_time.strftime('%Y-%m-%d %H:%M')} to today at {new_time.strftime('%H:%M')}",
                        scheduled_time=datetime.now(),
                        status="pending"
                    )
                    db.session.add(patient_notification)
            
            # Create notifications
            doctor_notification = Notification(
                user_id=appointment.doctor_id,
                appointment_id=appointment.appointment_id,
                type="emergency_priority",
                message=f"Appointment #{appointment.appointment_id} has been flagged as emergency priority",
                scheduled_time=datetime.now(),
                status="pending"
            )
            db.session.add(doctor_notification)
            
            db.session.commit()
            
            return jsonify({
                "status": "success",
                "message": "Appointment prioritized successfully",
                "new_time": appointment.date_time.isoformat() if reschedule_to_today else None
            }), 200
            
        except Exception as e:
            db.session.rollback()
            return jsonify({
                "status": "error",
                "message": f"Failed to prioritize appointment: {str(e)}"
            }), 500