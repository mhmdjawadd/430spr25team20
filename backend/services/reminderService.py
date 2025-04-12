from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from services.db import db
from models import User, Patient, Appointment, Notification, UserRole, AppointmentStatus
from sqlalchemy import and_, or_, func

class ReminderController:
    @staticmethod
    @jwt_required()
    def schedule_appointment_reminders():
        """
        Schedule reminders for upcoming appointments
        This endpoint is expected to be triggered by a cron job or scheduler
        
        It creates notifications for:
        1. Patients with upcoming appointments (24h, 2h)
        2. Caregivers for their elderly patients' appointments
        3. Doctors about their upcoming appointments
        """
        # Get the current time
        now = datetime.now()
        
        # Define reminder timeframes
        one_day_from_now = now + timedelta(days=1)
        two_hours_from_now = now + timedelta(hours=2)
        
        # Get all appointments in the next 24 hours that don't have reminders yet
        upcoming_appointments = Appointment.query.filter(
            Appointment.date_time > now,
            Appointment.date_time < one_day_from_now,
            Appointment.status != AppointmentStatus.CANCELLED
        ).all()
        
        notifications_created = 0
        patient_notifications = 0
        caregiver_notifications = 0
        
        try:
            for appointment in upcoming_appointments:
                # Get patient and doctor records
                patient = Patient.query.get(appointment.patient_id)
                doctor_user = User.query.get(appointment.doctor_id)
                
                if not patient or not doctor_user:
                    continue
                
                appointment_time = appointment.date_time
                formatted_time = appointment_time.strftime('%Y-%m-%d at %H:%M')
                
                # Check if we need to create a 24-hour reminder
                if now <= appointment_time - timedelta(hours=24) <= now + timedelta(minutes=30):
                    # 24-hour reminder for patient
                    patient_reminder = Notification(
                        user_id=appointment.patient_id,
                        appointment_id=appointment.appointment_id,
                        message=f"Reminder: Your appointment with Dr. {doctor_user.first_name} {doctor_user.last_name} is tomorrow at {appointment_time.strftime('%H:%M')}.",
                        scheduled_time=now,
                        status='reminder'
                    )
                    db.session.add(patient_reminder)
                    patient_notifications += 1
                    
                    # If patient has a caregiver, notify them too
                    if patient.caregiver_id:
                        caregiver_reminder = Notification(
                            user_id=patient.caregiver_id,
                            appointment_id=appointment.appointment_id,
                            message=f"Reminder: Your patient {patient.full_name()} has an appointment with Dr. {doctor_user.first_name} {doctor_user.last_name} tomorrow at {appointment_time.strftime('%H:%M')}.",
                            scheduled_time=now,
                            status='reminder'
                        )
                        db.session.add(caregiver_reminder)
                        caregiver_notifications += 1
                
                # Check if we need to create a 2-hour reminder
                elif now <= appointment_time - timedelta(hours=2) <= now + timedelta(minutes=30):
                    # 2-hour reminder for patient
                    patient_reminder = Notification(
                        user_id=appointment.patient_id,
                        appointment_id=appointment.appointment_id,
                        message=f"Reminder: Your appointment with Dr. {doctor_user.first_name} {doctor_user.last_name} is in 2 hours at {appointment_time.strftime('%H:%M')}.",
                        scheduled_time=now,
                        status='reminder'
                    )
                    db.session.add(patient_reminder)
                    patient_notifications += 1
                    
                    # If patient has a caregiver, notify them too
                    if patient.caregiver_id:
                        caregiver_reminder = Notification(
                            user_id=patient.caregiver_id,
                            appointment_id=appointment.appointment_id,
                            message=f"Reminder: Your patient {patient.full_name()} has an appointment with Dr. {doctor_user.first_name} {doctor_user.last_name} in 2 hours at {appointment_time.strftime('%H:%M')}.",
                            scheduled_time=now,
                            status='reminder'
                        )
                        db.session.add(caregiver_reminder)
                        caregiver_notifications += 1
                
            # Commit all notifications
            db.session.commit()
            notifications_created = patient_notifications + caregiver_notifications
            
            return jsonify({
                "message": "Reminders scheduled successfully",
                "notifications_created": notifications_created,
                "patient_notifications": patient_notifications,
                "caregiver_notifications": caregiver_notifications
            }), 200
            
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Failed to schedule reminders: {str(e)}"}), 500
            
    @staticmethod
    @jwt_required()
    def notify_cancellation_availabilities():
        """
        Notify patients about cancellations and last-minute availabilities
        This endpoint is expected to be called when an appointment is cancelled
        """
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user:
            return jsonify({"error": "User not found"}), 404
            
        # Only staff can notify about cancellations
        if current_user.role not in [UserRole.DOCTOR, UserRole.RECEPTIONIST, UserRole.NURSE]:
            return jsonify({"error": "Unauthorized to send availability notifications"}), 403
            
        # Get request data
        data = request.get_json()
        doctor_id = data.get('doctor_id')
        appointment_date = data.get('appointment_date')  # Format: YYYY-MM-DD
        cancellation_message = data.get('message', 'A slot has opened up due to a cancellation')
        
        # Validate required fields
        if not doctor_id or not appointment_date:
            return jsonify({"error": "Missing required fields: doctor_id, appointment_date"}), 400
        
        try:
            # Parse the date
            date_obj = datetime.strptime(appointment_date, "%Y-%m-%d").date()
            
            # Find all cancelled appointments for this doctor and date
            cancelled_appointments = Appointment.query.filter(
                Appointment.doctor_id == doctor_id,
                func.date(Appointment.date_time) == date_obj,
                Appointment.status == AppointmentStatus.CANCELLED
            ).all()
            
            if not cancelled_appointments:
                return jsonify({
                    "message": "No cancelled appointments found for this doctor on this date",
                    "notifications_sent": 0
                }), 200
                
            # Get the doctor's information
            doctor = User.query.get(doctor_id)
            if not doctor:
                return jsonify({"error": "Doctor not found"}), 404
                
            # Find patients who might be interested in the available slots
            # For simplicity, we'll notify patients who have had appointments with this doctor before
            potential_patients = db.session.query(Patient.patient_id).distinct().join(
                Appointment, Patient.patient_id == Appointment.patient_id
            ).filter(
                Appointment.doctor_id == doctor_id
            ).all()
            
            # Extract patient IDs
            patient_ids = [p[0] for p in potential_patients]
            
            # Create notifications for these patients
            notifications_sent = 0
            for patient_id in patient_ids:
                # Create notification for this patient
                notification = Notification(
                    user_id=patient_id,
                    message=f"Available appointment: Dr. {doctor.first_name} {doctor.last_name} has an opening on {appointment_date} due to a cancellation. Contact the clinic to book this slot.",
                    scheduled_time=datetime.now(),
                    status='availability'
                )
                db.session.add(notification)
                notifications_sent += 1
            
            # Commit to database
            db.session.commit()
            
            return jsonify({
                "message": "Availability notifications sent successfully",
                "notifications_sent": notifications_sent,
                "doctor_name": f"Dr. {doctor.first_name} {doctor.last_name}",
                "date": appointment_date
            }), 200
            
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Failed to send availability notifications: {str(e)}"}), 500
            
    @staticmethod
    @jwt_required()
    def get_caregiver_appointment_reminders():
        """
        Get all appointment reminders for the elderly patients of a caregiver
        """
        # Get the current user
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user:
            return jsonify({"error": "User not found"}), 404
            
        # Verify the user is a caregiver
        if current_user.role != UserRole.CAREGIVER:
            return jsonify({"error": "User is not a caregiver"}), 403
            
        # Get all appointments for patients this caregiver is responsible for
        # that are scheduled in the future
        now = datetime.now()
        
        # Get all patients assigned to this caregiver
        patients = Patient.query.filter_by(caregiver_id=current_user.user_id).all()
        patient_ids = [patient.patient_id for patient in patients]
        
        if not patient_ids:
            return jsonify({
                "caregiver_id": current_user.user_id,
                "caregiver_name": f"{current_user.first_name} {current_user.last_name}",
                "reminders": [],
                "count": 0
            }), 200
        
        # Get all upcoming appointments for these patients
        appointments = Appointment.query.filter(
            Appointment.patient_id.in_(patient_ids),
            Appointment.date_time > now,
            Appointment.status != AppointmentStatus.CANCELLED
        ).order_by(Appointment.date_time).all()
        
        # Format the appointment data
        reminders_list = []
        for appointment in appointments:
            patient = Patient.query.get(appointment.patient_id)
            doctor = User.query.get(appointment.doctor_id)
            
            reminders_list.append({
                "appointment_id": appointment.appointment_id,
                "date_time": appointment.date_time.strftime("%Y-%m-%d %H:%M"),
                "patient": {
                    "patient_id": patient.patient_id,
                    "name": patient.full_name() if patient else "Unknown"
                },
                "doctor": {
                    "doctor_id": appointment.doctor_id,
                    "name": f"Dr. {doctor.first_name} {doctor.last_name}" if doctor else "Unknown"
                },
                "time_until": ReminderController.format_time_until(now, appointment.date_time)
            })
            
        return jsonify({
            "caregiver_id": current_user.user_id,
            "caregiver_name": f"{current_user.first_name} {current_user.last_name}",
            "reminders": reminders_list,
            "count": len(reminders_list)
        }), 200
        
    @staticmethod
    def format_time_until(now, appointment_time):
        """Helper method to format the time until an appointment in a human-readable way"""
        delta = appointment_time - now
        days = delta.days
        hours, remainder = divmod(delta.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        
        if days > 0:
            return f"{days} days, {hours} hours"
        elif hours > 0:
            return f"{hours} hours, {minutes} minutes"
        else:
            return f"{minutes} minutes"