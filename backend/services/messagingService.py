from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from services.db import db
from models import User, Message, Notification
from sqlalchemy import or_, desc

class MessagingController:
    @staticmethod
    @jwt_required()
    def send_message():
        """
        Send a message from one user to another
        
        Request body:
        {
            "receiver_id": int,
            "content": string
        }
        """
        # Get the current user
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user:
            return jsonify({"error": "User not found"}), 404
            
        # Get request data
        data = request.get_json()
        receiver_id = data.get('receiver_id')
        content = data.get('content')
        
        # Validate required fields
        if not receiver_id:
            return jsonify({"error": "Missing required field: receiver_id"}), 400
            
        if not content or not content.strip():
            return jsonify({"error": "Missing required field: content"}), 400
            
        # Check if receiver exists
        receiver = User.query.get(receiver_id)
        if not receiver:
            return jsonify({"error": "Receiver not found"}), 404
            
        # Create new message
        new_message = Message(
            sender_id=current_user.user_id,
            receiver_id=receiver.user_id,
            content=content,
            sent_at=datetime.now()
        )
        
        # Create notification for receiver
        notification = Notification(
            user_id=receiver.user_id,
            message=f"New message from {current_user.first_name} {current_user.last_name}",
            scheduled_time=datetime.now()
        )
        
        try:
            db.session.add(new_message)
            db.session.add(notification)
            db.session.commit()
            
            return jsonify({
                "message": "Message sent successfully",
                "message_id": new_message.message_id,
                "sent_at": new_message.sent_at.isoformat(),
                "sender": current_user.full_name(),
                "receiver": receiver.full_name()
            }), 201
            
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Failed to send message: {str(e)}"}), 500
    
    @staticmethod
    @jwt_required()
    def get_conversations():
        """
        Get a list of all users the current user has exchanged messages with
        """
        # Get the current user
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user:
            return jsonify({"error": "User not found"}), 404
        
        # Find all users that the current user has exchanged messages with
        conversations_query = db.session.query(
            User,
            # Get the latest message timestamp for each conversation
            db.func.max(Message.sent_at).label('latest_message_time')
        ).join(
            Message,
            or_(
                (User.user_id == Message.sender_id) & (Message.receiver_id == current_user.user_id),
                (User.user_id == Message.receiver_id) & (Message.sender_id == current_user.user_id)
            )
        ).filter(
            User.user_id != current_user.user_id
        ).group_by(
            User.user_id
        ).order_by(
            desc('latest_message_time')
        ).all()
        
        # Format the conversation data
        conversations = []
        for user, latest_time in conversations_query:
            # Get the most recent message for this conversation
            latest_message = Message.query.filter(
                or_(
                    (Message.sender_id == current_user.user_id) & (Message.receiver_id == user.user_id),
                    (Message.sender_id == user.user_id) & (Message.receiver_id == current_user.user_id)
                )
            ).order_by(Message.sent_at.desc()).first()
            
            # Count unread messages
            unread_count = Message.query.filter(
                Message.sender_id == user.user_id,
                Message.receiver_id == current_user.user_id,
                Message.is_read == False
            ).count()
            
            conversations.append({
                "user_id": user.user_id,
                "name": user.full_name(),
                "role": user.role.name,
                "latest_message": latest_message.content if latest_message else "",
                "latest_message_time": latest_time.isoformat() if latest_time else None,
                "unread_count": unread_count
            })
        
        return jsonify({
            "user_id": current_user.user_id,
            "name": current_user.full_name(),
            "conversations": conversations
        }), 200
    
    @staticmethod
    @jwt_required()
    def get_messages(user_id):
        """
        Get all messages between the current user and another user
        """
        # Get the current user
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user:
            return jsonify({"error": "User not found"}), 404
            
        # Check if the other user exists
        other_user = User.query.get(user_id)
        if not other_user:
            return jsonify({"error": "User not found"}), 404
            
        # Get all messages between these two users
        messages = Message.query.filter(
            or_(
                (Message.sender_id == current_user.user_id) & (Message.receiver_id == other_user.user_id),
                (Message.sender_id == other_user.user_id) & (Message.receiver_id == current_user.user_id)
            )
        ).order_by(Message.sent_at).all()
        
        # Mark messages from the other user as read
        unread_messages = [msg for msg in messages if msg.sender_id == other_user.user_id and not msg.is_read]
        for msg in unread_messages:
            msg.is_read = True
        
        if unread_messages:
            db.session.commit()
        
        # Format the message data
        messages_list = []
        for message in messages:
            messages_list.append({
                "message_id": message.message_id,
                "sender_id": message.sender_id,
                "sender_name": message.sender.full_name() if message.sender else "Unknown",
                "receiver_id": message.receiver_id,
                "receiver_name": message.receiver.full_name() if message.receiver else "Unknown",
                "content": message.content,
                "sent_at": message.sent_at.isoformat(),
                "is_mine": message.sender_id == current_user.user_id
            })
            
        return jsonify({
            "current_user": {
                "user_id": current_user.user_id,
                "name": current_user.full_name()
            },
            "other_user": {
                "user_id": other_user.user_id,
                "name": other_user.full_name()
            },
            "messages": messages_list
        }), 200