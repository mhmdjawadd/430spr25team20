from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from services.db import db
from models import User, Notification
from sqlalchemy import desc

class NotificationController:
    @staticmethod
    @jwt_required()
    def get_user_notifications():
        """
        Get all notifications for the current user
        """
        # Get the current user
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user:
            return jsonify({"error": "User not found"}), 404
            
        # Get query parameters
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Get notifications for the user
        notifications = Notification.query.filter_by(
            user_id=current_user.user_id
        ).order_by(
            desc(Notification.scheduled_time)
        ).limit(limit).offset(offset).all()
        
        # Format the notifications data
        notifications_list = []
        for notification in notifications:
            notifications_list.append({
                "notification_id": notification.notification_id,
                "message": notification.message,
                "scheduled_time": notification.scheduled_time.isoformat(),
                "is_read": getattr(notification, 'is_read', False),
                "appointment_id": notification.appointment_id
            })
            
        return jsonify({
            "user_id": current_user.user_id,
            "notifications": notifications_list,
            "count": len(notifications_list)
        }), 200
    
    @staticmethod
    @jwt_required()
    def mark_notification_read(notification_id):
        """
        Mark a notification as read
        """
        # Get the current user
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user:
            return jsonify({"error": "User not found"}), 404
            
        # Get the notification
        notification = Notification.query.get(notification_id)
        
        if not notification:
            return jsonify({"error": "Notification not found"}), 404
            
        # Check if the notification belongs to the current user
        if notification.user_id != current_user.user_id:
            return jsonify({"error": "Unauthorized to access this notification"}), 403
            
        # Mark as read (check if the column exists first)
        if hasattr(notification, 'is_read'):
            notification.is_read = True
            
            try:
                db.session.commit()
                return jsonify({
                    "message": "Notification marked as read",
                    "notification_id": notification.notification_id
                }), 200
            except Exception as e:
                db.session.rollback()
                return jsonify({"error": f"Failed to update notification: {str(e)}"}), 500
        else:
            # If is_read doesn't exist, just return success anyway
            return jsonify({
                "message": "Notification processed (is_read field not available)",
                "notification_id": notification.notification_id
            }), 200