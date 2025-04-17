from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime
from services.db import db
from models import User, Doctor, Patient, Message, Appointment, UserRole
from sqlalchemy import or_, and_, desc , text
import traceback

class MessagingController:
    
    @staticmethod
    @jwt_required()
    def get_messaging_contacts():
        """
        Get all contacts (doctors and nurses) that the user can message.
        For patients: retrieve appointments the patient booked and then list only the doctors from those appointments.
        For doctors: patients they have appointments with and nurses.
        For nurses: all patients and doctors.
        """
        try:
            current_user_id = get_jwt_identity()
            print(f"Fetching contacts for user ID: {current_user_id}")
            current_user = User.query.get(current_user_id)
            if not current_user:
                print(f"User not found for ID: {current_user_id}")
                return jsonify({"error": "User not found"}), 404
            contacts = []
            print(f"User role: {current_user.role}")
            # Patient: Get only doctors from appointments booked by this patient.
            if current_user.role == UserRole.PATIENT:
                print("Processing contacts for a patient using appointment data")
                query = text("""
                    SELECT DISTINCT a.doctor_id, u.first_name, u.last_name, u.role
                    FROM appointments a
                    JOIN users u ON a.doctor_id = u.user_id
                    WHERE a.patient_id = :patient_id
                """)
                result = db.session.execute(query, {'patient_id': current_user_id})
                doctor_rows = result.fetchall()
                print(f"Found {len(doctor_rows)} doctors from appointments")
                for row in doctor_rows:
                    doctor_id, first_name, last_name, role = row
                    unread_count = Message.query.filter(
                        Message.sender_id == doctor_id,
                        Message.receiver_id == current_user_id,
                        Message.is_read == False
                    ).count()
                    contacts.append({
                        "id": doctor_id,
                        "name": f"Dr. {first_name} {last_name}",
                        "role": "Doctor",
                        "specialty": "Doctor",
                        "unread_count": unread_count
                    })
            elif current_user.role in [UserRole.DOCTOR, UserRole.SURGEON, UserRole.THERAPIST]:
                print("Processing contacts for a doctor")
                # Get patients doctor has appointments with
                patient_ids = db.session.query(Appointment.patient_id)\
                    .filter(Appointment.doctor_id == current_user_id)\
                    .distinct().all()
                    
                patient_ids = [p[0] for p in patient_ids]
                print(f"Found {len(patient_ids)} patient IDs for appointments")
                
                if patient_ids:
                    patients = User.query.filter(User.user_id.in_(patient_ids)).all()
                    print(f"Found {len(patients)} patient user records")
                    
                    for patient in patients:
                        # Count unread messages from this patient
                        unread_count = Message.query.filter(
                            Message.sender_id == patient.user_id,
                            Message.receiver_id == current_user_id,
                            Message.is_read == False
                        ).count()
                        
                        contacts.append({
                            "id": patient.user_id,
                            "name": f"{patient.first_name} {patient.last_name}",
                            "role": "Patient",
                            "unread_count": unread_count
                        })
                
                # Get all nurses too
                nurses = User.query.filter(User.role == UserRole.NURSE).all()
                print(f"Found {len(nurses)} nurse user records")
                
                for nurse in nurses:
                    if nurse.user_id != current_user_id:  # Don't include yourself
                        # Count unread messages from this nurse
                        unread_count = Message.query.filter(
                            Message.sender_id == nurse.user_id,
                            Message.receiver_id == current_user_id,
                            Message.is_read == False
                        ).count()
                        
                        contacts.append({
                            "id": nurse.user_id,
                            "name": f"Nurse {nurse.first_name} {nurse.last_name}",
                            "role": "Nurse",
                            "unread_count": unread_count
                        })
            
            elif current_user.role == UserRole.NURSE:
                print("Processing contacts for a nurse")
                # Get all patients
                patients = User.query.filter(User.role == UserRole.PATIENT).all()
                print(f"Found {len(patients)} patient user records")
                
                for patient in patients:
                    # Count unread messages from this patient
                    unread_count = Message.query.filter(
                        Message.sender_id == patient.user_id,
                        Message.receiver_id == current_user_id,
                        Message.is_read == False
                    ).count()
                    
                    contacts.append({
                        "id": patient.user_id,
                        "name": f"{patient.first_name} {patient.last_name}",
                        "role": "Patient",
                        "unread_count": unread_count
                    })
                
                # Get all doctors
                doctors = User.query.filter(User.role.in_([UserRole.DOCTOR, UserRole.SURGEON, UserRole.THERAPIST])).all()
                print(f"Found {len(doctors)} doctor user records")
                
                for doctor in doctors:
                    # Count unread messages from this doctor
                    unread_count = Message.query.filter(
                        Message.sender_id == doctor.user_id,
                        Message.receiver_id == current_user_id,
                        Message.is_read == False
                    ).count()
                    
                    contacts.append({
                        "id": doctor.user_id,
                        "name": f"Dr. {doctor.first_name} {doctor.last_name}",
                        "role": "Doctor",
                        "specialty": doctor.role.name if hasattr(doctor, 'role') else "Doctor",
                        "unread_count": unread_count
                    })
            else:
                print(f"Unsupported user role: {current_user.role}")
                return jsonify({"error": "Your account type does not support messaging"}), 403

            contacts.sort(key=lambda x: x["name"])
            print(f"Successfully retrieved {len(contacts)} contacts")
            return jsonify({"contacts": contacts}), 200
        except Exception as e:
            db.session.rollback()
            print(f"Error getting messaging contacts: {str(e)}")
            print(traceback.format_exc())
            return jsonify({"error": f"Failed to get contacts: {str(e)}"}), 500

    @staticmethod
    @jwt_required()
    def get_messages_with_contact(contact_id):
        """
        Get all messages between current user and the specified contact
        """
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user:
            return jsonify({"error": "User not found"}), 404

        contact = User.query.get(contact_id)
        if not contact:
            return jsonify({"error": "Contact not found"}), 404
        
        try:
            # Get messages between current user and contact (both ways)
            messages_query = Message.query.filter(
                or_(
                    and_(Message.sender_id == current_user_id, Message.receiver_id == contact_id),
                    and_(Message.sender_id == contact_id, Message.receiver_id == current_user_id)
                )
            ).order_by(Message.timestamp.asc())
            
            messages = messages_query.all()
            
            # Format messages for response
            messages_data = []
            for msg in messages:
                messages_data.append({
                    "id": msg.message_id,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "is_sent": msg.sender_id == current_user_id,
                    "is_read": msg.is_read
                })
            
            # Get contact information
            contact_name = f"{contact.first_name} {contact.last_name}"
            if contact.role in [UserRole.DOCTOR, UserRole.SURGEON, UserRole.THERAPIST]:
                contact_name = f"Dr. {contact.first_name} {contact.last_name}"
            elif contact.role == UserRole.NURSE:
                contact_name = f"Nurse {contact.first_name} {contact.last_name}"
                
            contact_info = {
                "id": contact.user_id,
                "name": contact_name,
                "role": contact.role.name if hasattr(contact.role, 'name') else str(contact.role)
            }
            
            return jsonify({
                "contact": contact_info,
                "messages": messages_data
            }), 200
            
        except Exception as e:
            db.session.rollback()
            print(f"Error getting messages: {str(e)}")
            return jsonify({"error": f"Failed to get messages: {str(e)}"}), 500

    @staticmethod
    @jwt_required()
    def send_message():
        """
        Send a message to another user
        """
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user:
            return jsonify({"error": "User not found"}), 404
            
        data = request.get_json()
        
        # Validate required fields
        if not data or not data.get('recipient_id') or not data.get('content'):
            return jsonify({"error": "Missing required fields: recipient_id, content"}), 400
        
        recipient_id = data['recipient_id']
        content = data['content']
        
        # Validate recipient exists
        recipient = User.query.get(recipient_id)
        if not recipient:
            return jsonify({"error": "Recipient not found"}), 404
            
        # Check if user is allowed to message this recipient
        allowed = False
        
        # Patient can message doctors they have appointments with and nurses
        if current_user.role == UserRole.PATIENT:
            if recipient.role == UserRole.NURSE:
                allowed = True
            elif recipient.role in [UserRole.DOCTOR, UserRole.SURGEON, UserRole.THERAPIST]:
                # Check if patient has an appointment with this doctor
                appointment = Appointment.query.filter(
                    Appointment.patient_id == current_user_id,
                    Appointment.doctor_id == recipient_id
                ).first()
                allowed = appointment is not None
                
        # Doctor can message patients they have appointments with and nurses
        elif current_user.role in [UserRole.DOCTOR, UserRole.SURGEON, UserRole.THERAPIST]:
            if recipient.role == UserRole.NURSE:
                allowed = True
            elif recipient.role == UserRole.PATIENT:
                # Check if doctor has an appointment with this patient
                appointment = Appointment.query.filter(
                    Appointment.patient_id == recipient_id,
                    Appointment.doctor_id == current_user_id
                ).first()
                allowed = appointment is not None
                
        # Nurse can message all patients and doctors
        elif current_user.role == UserRole.NURSE:
            if recipient.role in [UserRole.PATIENT, UserRole.DOCTOR, UserRole.SURGEON, UserRole.THERAPIST, UserRole.NURSE]:
                allowed = True
        
        if not allowed:
            return jsonify({"error": "You are not allowed to message this user"}), 403
            
        try:
            # Create message
            message = Message(
                sender_id=current_user_id,
                receiver_id=recipient_id,
                content=content,
                timestamp=datetime.utcnow(),
                is_read=False
            )
            
            db.session.add(message)
            db.session.commit()
            
            return jsonify({
                "message": "Message sent successfully",
                "message_id": message.message_id,
                "timestamp": message.timestamp.isoformat()
            }), 201
            
        except Exception as e:
            db.session.rollback()
            print(f"Error sending message: {str(e)}")
            return jsonify({"error": f"Failed to send message: {str(e)}"}), 500

    @staticmethod
    @jwt_required()
    def mark_messages_as_read(contact_id):
        """
        Mark all messages from a specific contact as read
        """
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user:
            return jsonify({"error": "User not found"}), 404
            
        try:
            # Find all unread messages from the contact
            unread_messages = Message.query.filter(
                Message.sender_id == contact_id,
                Message.receiver_id == current_user_id,
                Message.is_read == False
            ).all()
            
            # Update each message
            for message in unread_messages:
                message.is_read = True
                
            db.session.commit()
            
            return jsonify({
                "message": f"Marked {len(unread_messages)} messages as read",
                "count": len(unread_messages)
            }), 200
            
        except Exception as e:
            db.session.rollback()
            print(f"Error marking messages as read: {str(e)}")
            return jsonify({"error": f"Failed to mark messages as read: {str(e)}"}), 500

    @staticmethod
    @jwt_required()
    def get_unread_message_count():
        """
        Get the count of unread messages for the current user
        """
        current_user_id = get_jwt_identity()
        
        try:
            # Count unread messages
            unread_count = Message.query.filter(
                Message.receiver_id == current_user_id,
                Message.is_read == False
            ).count()
            
            return jsonify({
                "unread_count": unread_count
            }), 200
            
        except Exception as e:
            print(f"Error getting unread message count: {str(e)}")
            return jsonify({"error": f"Failed to get unread message count: {str(e)}"}), 500
            
    @staticmethod
    @jwt_required()
    def get_conversations():
        """
        Get all conversation summaries for the current user
        Returns a list of users that the current user has exchanged messages with
        and the latest message in each conversation
        """
        current_user_id = get_jwt_identity()
        # Ensure current_user_id is an integer
        try:
            current_user_id = int(current_user_id)
        except (ValueError, TypeError):
            print(f"Invalid user ID format: {current_user_id}")
            return jsonify({"error": "Invalid user ID format"}), 400
            
        current_user = User.query.get(current_user_id)
        
        if not current_user:
            return jsonify({"error": "User not found"}), 404
            
        try:
            # Get all users the current user has exchanged messages with
            # This is a bit complex as we need to get both sent and received messages
            
            # First, get all users the current user has sent messages to
            sent_to_users = db.session.query(Message.receiver_id.distinct()).filter(
                Message.sender_id == current_user_id
            ).all()
            sent_to_user_ids = [int(user[0]) for user in sent_to_users]
            
            # Then, get all users who have sent messages to the current user
            received_from_users = db.session.query(Message.sender_id.distinct()).filter(
                Message.receiver_id == current_user_id
            ).all()
            received_from_user_ids = [int(user[0]) for user in received_from_users]
            
            # Combine and deduplicate
            conversation_user_ids = list(set(sent_to_user_ids + received_from_user_ids))
            
            if not conversation_user_ids:
                return jsonify({"conversations": []}), 200
                
            # Get user objects
            conversation_users = User.query.filter(User.user_id.in_(conversation_user_ids)).all()
            
            conversations = []
            
            for user in conversation_users:
                # Ensure user_id is an integer
                user_id = int(user.user_id)
                
                # Get the latest message between these users
                latest_message = Message.query.filter(
                    or_(
                        and_(Message.sender_id == current_user_id, Message.receiver_id == user_id),
                        and_(Message.sender_id == user_id, Message.receiver_id == current_user_id)
                    )
                ).order_by(Message.timestamp.desc()).first()
                
                if not latest_message:
                    continue
                    
                # Count unread messages from this user
                unread_count = Message.query.filter(
                    Message.sender_id == user_id,
                    Message.receiver_id == current_user_id,
                    Message.is_read == False
                ).count()
                
                # Format user name based on role
                user_name = f"{user.first_name} {user.last_name}"
                if user.role in [UserRole.DOCTOR, UserRole.SURGEON, UserRole.THERAPIST]:
                    user_name = f"Dr. {user.first_name} {user.last_name}"
                elif user.role == UserRole.NURSE:
                    user_name = f"Nurse {user.first_name} {user.last_name}"
                
                conversations.append({
                    "user_id": user_id,
                    "name": user_name,
                    "role": user.role.name,
                    "latest_message": {
                        "id": latest_message.message_id,
                        "content": latest_message.content[:50] + ('...' if len(latest_message.content) > 50 else ''),
                        "timestamp": latest_message.timestamp.isoformat(),
                        "is_sent": latest_message.sender_id == current_user_id,
                        "is_read": latest_message.is_read
                    },
                    "unread_count": unread_count
                })
            
            # Sort by latest message timestamp, newest first
            conversations.sort(key=lambda x: x["latest_message"]["timestamp"], reverse=True)
            
            return jsonify({"conversations": conversations}), 200
            
        except Exception as e:
            error_traceback = traceback.format_exc()
            print(f"Error getting conversations: {str(e)}")
            print(f"Traceback: {error_traceback}")
            return jsonify({"error": f"Failed to get conversations: {str(e)}"}), 500