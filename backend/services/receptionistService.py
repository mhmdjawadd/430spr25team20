from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from models.user import User, UserRole
from models.appointment import Appointment, AppointmentStatus, AppointmentType
from models.doctor import Doctor
from models.notification import Notification
from models.patient import Patient
from services.notificationService import NotificationController

class ReceptionistController:
    @staticmethod
    @jwt_required()
    def get_pending_appointments():
        """Get all pending appointment requests"""
        try:
            user_id = get_jwt_identity()
            user = User.query.get(user_id)
            
            # Verify user is a receptionist
            if user.role != UserRole.RECEPTIONIST:
                return jsonify({"status": "error", "message": "Unauthorized access"}), 403
            
            # Get all pending appointment requests (last 7 days and future)
            week_ago = datetime.now() - timedelta(days=7)
            pending_appointments = Appointment.query.filter(
                Appointment.status == AppointmentStatus.REQUESTED,
                Appointment.date_time >= week_ago
            ).order_by(Appointment.date_time).all()
            
            appointments_data = []
            for appointment in pending_appointments:
                patient = Patient.query.get(appointment.patient_id)
                patient_user = User.query.get(patient.patient_id) if patient else None
                doctor = Doctor.query.get(appointment.doctor_id)
                doctor_user = User.query.get(doctor.doctor_id) if doctor else None
                
                appointments_data.append({
                    "id": appointment.appointment_id,
                    "patient_name": f"{patient_user.first_name} {patient_user.last_name}" if patient_user else "Unknown",
                    "doctor_name": f"{doctor_user.first_name} {doctor_user.last_name}" if doctor_user else "Unknown",
                    "date_time": appointment.date_time.isoformat(),
                    "reason": appointment.reason,
                    "type": appointment.type.value,
                    "priority": appointment.priority
                })
            
            return jsonify({
                "status": "success", 
                "data": appointments_data
            }), 200
            
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500
    
    @staticmethod
    @jwt_required()
    def auto_schedule_appointments():
        """Automatically schedule pending appointment requests based on doctor availability"""
        try:
            user_id = get_jwt_identity()
            user = User.query.get(user_id)
            
            # Verify user is a receptionist
            if user.role != UserRole.RECEPTIONIST:
                return jsonify({"status": "error", "message": "Unauthorized access"}), 403
            
            # Get pending appointments
            pending_appointments = Appointment.query.filter_by(
                status=AppointmentStatus.REQUESTED
            ).order_by(Appointment.priority.desc()).all()
            
            scheduled_count = 0
            failed_count = 0
            
            for appointment in pending_appointments:
                # Get doctor's existing appointments for the day
                appointment_date = appointment.date_time.date()
                day_start = datetime.combine(appointment_date, datetime.min.time())
                day_end = datetime.combine(appointment_date, datetime.max.time())
                
                doctor_appointments = Appointment.query.filter(
                    Appointment.doctor_id == appointment.doctor_id,
                    Appointment.date_time >= day_start,
                    Appointment.date_time <= day_end,
                    Appointment.status.in_([AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED]),
                    Appointment.appointment_id != appointment.appointment_id
                ).order_by(Appointment.date_time).all()
                
                # Find available slots (assuming 9 AM - 5 PM workday)
                work_start = datetime.combine(appointment_date, datetime.strptime("09:00", "%H:%M").time())
                work_end = datetime.combine(appointment_date, datetime.strptime("17:00", "%H:%M").time())
                
                available_slots = []
                current_time = work_start
                
                # Create list of available time slots
                for booked in doctor_appointments:
                    if current_time < booked.date_time:
                        slot_end = booked.date_time
                        slot_duration = (slot_end - current_time).total_seconds() / 60
                        
                        if slot_duration >= appointment.duration:
                            available_slots.append({
                                "start": current_time,
                                "duration": slot_duration
                            })
                    
                    current_time = booked.date_time + timedelta(minutes=booked.duration)
                
                # Check final slot of the day
                if current_time < work_end:
                    final_duration = (work_end - current_time).total_seconds() / 60
                    if final_duration >= appointment.duration:
                        available_slots.append({
                            "start": current_time,
                            "duration": final_duration
                        })
                
                # If no appointments that day, whole day is available
                if not doctor_appointments:
                    available_slots.append({
                        "start": work_start,
                        "duration": 480  # 8 hours in minutes
                    })
                
                # Find optimal slot and schedule appointment
                if available_slots:
                    # Schedule at first available slot
                    best_slot = available_slots[0]["start"]
                    appointment.date_time = best_slot
                    appointment.status = AppointmentStatus.SCHEDULED
                    
                    # Create notifications
                    patient_notification = Notification(
                        user_id=appointment.patient_id,
                        appointment_id=appointment.appointment_id,
                        type="appointment_scheduled",
                        message=f"Your appointment has been scheduled for {best_slot.strftime('%B %d at %I:%M %p')}",
                        scheduled_time=datetime.now()
                    )
                    
                    doctor_notification = Notification(
                        user_id=appointment.doctor_id,
                        appointment_id=appointment.appointment_id,
                        type="new_appointment",
                        message=f"New appointment scheduled for {best_slot.strftime('%B %d at %I:%M %p')}",
                        scheduled_time=datetime.now()
                    )
                    
                    db.session.add(patient_notification)
                    db.session.add(doctor_notification)
                    scheduled_count += 1
                else:
                    failed_count += 1
            
            db.session.commit()
            
            return jsonify({
                "status": "success",
                "message": f"Auto-scheduled {scheduled_count} appointments, {failed_count} could not be scheduled due to no availability"
            }), 200
            
        except Exception as e:
            db.session.rollback()
            return jsonify({"status": "error", "message": str(e)}), 500