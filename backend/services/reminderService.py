from models.db import db
from models.notification import Notification
from models.appointment import Appointment
from models.user import User
from datetime import datetime, timedelta

class ReminderService:
    @staticmethod
    def schedule_appointment_reminders(appointment_id):
        """Schedule reminders for a specific appointment"""
        try:
            # Get the appointment
            appointment = Appointment.query.get(appointment_id)
            if not appointment:
                return False
                
            # Get doctor name
            doctor = User.query.get(appointment.doctor_id)
            doctor_name = f"Dr. {doctor.last_name}" if doctor else "your doctor"
                
            # Schedule a reminder for 24 hours before the appointment
            day_reminder = Notification(
                user_id=appointment.patient_id,
                appointment_id=appointment.appointment_id,
                type="reminder",
                message=f"Reminder: You have an appointment with {doctor_name} tomorrow at {appointment.date_time.strftime('%I:%M %p')}",
                scheduled_time=appointment.date_time - timedelta(days=1)
            )
            db.session.add(day_reminder)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error scheduling reminder: {str(e)}")
            return False
    
    @staticmethod
    def send_pending_reminders():
        """Send all pending reminders that are due"""
        try:
            # Find all notifications that are scheduled for now or in the past and haven't been sent yet
            now = datetime.utcnow()
            pending_notifications = Notification.query.filter(
                Notification.scheduled_time <= now,
                Notification.is_sent == False
            ).all()
            
            for notification in pending_notifications:
                # In a real app, you'd send emails/SMS here
                # For this project, just mark them as sent
                notification.is_sent = True
                notification.sent_at = now
            
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error processing reminders: {str(e)}")
            return False