from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from services.db import db
from models import Notification, Appointment, User, AppointmentStatus

class NotificationController:
    @staticmethod
    def schedule_appointment_reminders():
        """
        Scheduled task to create appointment reminder notifications
        This would be called by a scheduler like APScheduler or Celery
        """
        try:
            # Get appointments happening in the next 24 hours
            tomorrow = datetime.now() + timedelta(days=1)
            upcoming_appointments = Appointment.query.filter(
                Appointment.date_time > datetime.now(),
                Appointment.date_time < tomorrow,
                Appointment.status.in_([
                    AppointmentStatus.SCHEDULED, 
                    AppointmentStatus.CONFIRMED
                ])
            ).all()
            
            notifications_created = 0
            
            for appointment in upcoming_appointments:
                # Check if reminder already exists
                existing_reminder = Notification.query.filter_by(
                    appointment_id=appointment.appointment_id,
                    type="reminder"
                ).first()
                
                if not existing_reminder:
                    # Create reminder for patient
                    reminder = Notification(
                        user_id=appointment.patient_id,
                        appointment_id=appointment.appointment_id,
                        type="reminder",
                        message=f"Reminder: You have an appointment tomorrow at {appointment.date_time.strftime('%H:%M')}",
                        scheduled_time=datetime.now(),  # Send immediately
                        status="pending"
                    )
                    db.session.add(reminder)
                    notifications_created += 1
            
            db.session.commit()
            return jsonify({
                "status": "success",
                "message": f"Created {notifications_created} appointment reminders"
            }), 200
            
        except Exception as e:
            db.session.rollback()
            return jsonify({
                "status": "error",
                "message": f"Failed to schedule reminders: {str(e)}"
            }), 500
    
    @staticmethod
    @jwt_required()
    def get_notifications():
        """Get notifications for the current user"""
        try:
            user_id = get_jwt_identity()
            
            # Get recent notifications for the user
            notifications = Notification.query.filter_by(
                user_id=user_id
            ).order_by(Notification.scheduled_time.desc()).limit(20).all()
            
            # Format notifications for response
            notifications_data = []
            for notification in notifications:
                notifications_data.append({
                    'id': notification.notification_id,
                    'type': notification.type,
                    'message': notification.message,
                    'created_at': notification.created_at.isoformat() if notification.created_at else None,
                    'is_read': notification.read_at is not None
                })
            
            return jsonify({
                'status': 'success',
                'notifications': notifications_data
            }), 200
            
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    
    @staticmethod
    @jwt_required()
    def mark_notification_read(notification_id):
        """Mark a notification as read"""
        current_user_id = get_jwt_identity()
        
        notification = Notification.query.filter_by(
            notification_id=notification_id,
            user_id=current_user_id
        ).first()
        
        if not notification:
            return jsonify({
                "status": "error",
                "message": "Notification not found"
            }), 404
        
        notification.status = "read"
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": "Notification marked as read"
        }), 200