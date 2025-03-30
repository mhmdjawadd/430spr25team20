from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime, timedelta
from services.db import db
from models import User, Doctor, Patient, Appointment, MedicalRecord, Notification, CarePlan, CarePlanUpdate

class NurseController:
    @staticmethod
    @jwt_required()
    def get_nurse_schedule():
        """Get a nurse's daily schedule with all tasks and appointments"""
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        role = claims.get("role")
        
        # Only nurses can access their schedule
        if role != "nurse":
            return jsonify({
                "status": "error",
                "message": "Only nurses can access their nurse schedule"
            }), 403
        
        # Get date parameter or use today
        date_str = request.args.get('date')
        try:
            if date_str:
                selected_date = datetime.fromisoformat(date_str.replace('Z', '+00:00')).date()
            else:
                selected_date = datetime.now().date()
        except ValueError:
            return jsonify({
                "status": "error",
                "message": "Invalid date format. Use ISO format (YYYY-MM-DD)"
            }), 400
        
        # Date range for the selected day
        day_start = datetime.combine(selected_date, datetime.min.time())
        day_end = datetime.combine(selected_date, datetime.max.time())
        
        # Get assigned care plans
        care_plans = CarePlan.query.filter(
            CarePlan.assigned_nurse_id == current_user_id,
            CarePlan.is_active == True
        ).all()
        
        # Get appointments where the nurse is needed
        appointments = Appointment.query.filter(
            Appointment.date_time >= day_start,
            Appointment.date_time <= day_end,
            Appointment.nurse_id == current_user_id
        ).order_by(Appointment.date_time).all()
        
        # Get notifications for the nurse
        notifications = Notification.query.filter(
            Notification.user_id == current_user_id,
            Notification.scheduled_time >= day_start,
            Notification.scheduled_time <= day_end
        ).all()
        
        # Format into schedule items
        schedule_items = []
        
        # Add care plan tasks
        for plan in care_plans:
            patient = Patient.query.get(plan.patient_id)
            patient_user = User.query.get(patient.patient_id) if patient else None
            
            # Add daily tasks from care plan
            for task in plan.daily_tasks:
                # Check if task is for today (based on frequency)
                if task.should_perform_on_date(selected_date):
                    schedule_items.append({
                        "type": "care_task",
                        "id": task.task_id,
                        "patient": f"{patient_user.first_name} {patient_user.last_name}" if patient_user else "Unknown",
                        "description": task.description,
                        "priority": task.priority,
                        "status": task.status,
                        "time": task.scheduled_time.isoformat() if task.scheduled_time else None,
                        "color": "#FF851B" if task.priority == "high" else "#2ECC40"
                    })
        
        # Add appointments
        for appointment in appointments:
            patient = Patient.query.get(appointment.patient_id)
            patient_user = User.query.get(patient.patient_id) if patient else None
            
            doctor = Doctor.query.get(appointment.doctor_id)
            doctor_user = User.query.get(doctor.doctor_id) if doctor else None
            
            schedule_items.append({
                "type": "appointment",
                "id": appointment.appointment_id,
                "start_time": appointment.date_time.isoformat(),
                "end_time": (appointment.date_time + timedelta(minutes=appointment.duration)).isoformat(),
                "duration_minutes": appointment.duration,
                "patient": f"{patient_user.first_name} {patient_user.last_name}" if patient_user else "Unknown",
                "doctor": f"Dr. {doctor_user.first_name} {doctor_user.last_name}" if doctor_user else "",
                "reason": appointment.reason,
                "status": appointment.status.value,
                "is_emergency": appointment.type == AppointmentType.EMERGENCY,
                "color": "#FF4136" if appointment.type == AppointmentType.EMERGENCY else "#0074D9"
            })
        
        # Add notifications
        for notification in notifications:
            schedule_items.append({
                "type": "notification",
                "id": notification.notification_id,
                "time": notification.scheduled_time.isoformat(),
                "message": notification.message,
                "notification_type": notification.type,
                "status": notification.status,
                "color": "#FFDC00"
            })
        
        # Sort all items by start time
        schedule_items.sort(key=lambda x: x.get("start_time", x.get("time", "")))
        
        return jsonify({
            "status": "success",
            "date": selected_date.isoformat(),
            "nurse_id": current_user_id,
            "schedule": schedule_items
        }), 200
    
    @staticmethod
    @jwt_required()
    def update_care_plan():
        """Update a patient's care plan"""
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        role = claims.get("role")
        
        # Only nurses and doctors can update care plans
        if role not in ["nurse", "doctor"]:
            return jsonify({
                "status": "error",
                "message": "Only nurses and doctors can update care plans"
            }), 403
        
        data = request.get_json()
        if not data or not data.get('care_plan_id'):
            return jsonify({
                "status": "error",
                "message": "Care plan ID is required"
            }), 400
        
        # Get care plan
        care_plan = CarePlan.query.get(data['care_plan_id'])
        if not care_plan:
            return jsonify({
                "status": "error",
                "message": "Care plan not found"
            }), 404
        
        # Verify user is assigned to this care plan or is the supervising doctor
        if role == "nurse" and care_plan.assigned_nurse_id != current_user_id:
            return jsonify({
                "status": "error",
                "message": "You are not authorized to update this care plan"
            }), 403
        elif role == "doctor" and care_plan.supervising_doctor_id != current_user_id:
            return jsonify({
                "status": "error",
                "message": "You are not authorized to update this care plan"
            }), 403
        
        # Create update record
        update = CarePlanUpdate(
            care_plan_id=care_plan.care_plan_id,
            updated_by_id=current_user_id,
            notes=data.get('notes', ''),
            changes=data.get('changes', '')
        )
        
        # Update care plan fields if provided
        if 'description' in data:
            care_plan.description = data['description']
        if 'goals' in data:
            care_plan.goals = data['goals']
        if 'is_active' in data:
            care_plan.is_active = data['is_active']
        
        # Add new tasks if provided
        if 'new_tasks' in data and isinstance(data['new_tasks'], list):
            for task_data in data['new_tasks']:
                task = CarePlanTask(
                    care_plan_id=care_plan.care_plan_id,
                    description=task_data.get('description', ''),
                    frequency=task_data.get('frequency', 'daily'),
                    priority=task_data.get('priority', 'normal'),
                    status='pending',
                    scheduled_time=datetime.fromisoformat(task_data['scheduled_time'].replace('Z', '+00:00')) if task_data.get('scheduled_time') else None
                )
                db.session.add(task)
        
        # Update tasks if provided
        if 'update_tasks' in data and isinstance(data['update_tasks'], list):
            for task_update in data['update_tasks']:
                if not task_update.get('task_id'):
                    continue
                    
                task = CarePlanTask.query.get(task_update['task_id'])
                if task and task.care_plan_id == care_plan.care_plan_id:
                    if 'status' in task_update:
                        task.status = task_update['status']
                    if 'description' in task_update:
                        task.description = task_update['description']
                    if 'priority' in task_update:
                        task.priority = task_update['priority']
        
        # Send notification to doctor if nurse is updating
        if role == "nurse" and care_plan.supervising_doctor_id:
            doctor_notification = Notification(
                user_id=care_plan.supervising_doctor_id,
                type="care_plan_update",
                message=f"Nurse updated care plan for patient {Patient.query.get(care_plan.patient_id).full_name()}",
                scheduled_time=datetime.now(),
                status="pending"
            )
            db.session.add(doctor_notification)
            
        # Send notification to nurse if doctor is updating
        elif role == "doctor" and care_plan.assigned_nurse_id:
            nurse_notification = Notification(
                user_id=care_plan.assigned_nurse_id,
                type="care_plan_update",
                message=f"Dr. {User.query.get(current_user_id).last_name} updated care plan for patient {Patient.query.get(care_plan.patient_id).full_name()}",
                scheduled_time=datetime.now(),
                status="pending"
            )
            db.session.add(nurse_notification)
        
        try:
            db.session.add(update)
            db.session.commit()
            return jsonify({
                "status": "success",
                "message": "Care plan updated successfully"
            }), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({
                "status": "error",
                "message": f"Failed to update care plan: {str(e)}"
            }), 500
    
    @staticmethod
    @jwt_required()
    def create_care_plan():
        """Create a new care plan for a patient"""
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        role = claims.get("role")
        
        # Only nurses and doctors can create care plans
        if role not in ["nurse", "doctor"]:
            return jsonify({
                "status": "error",
                "message": "Only nurses and doctors can create care plans"
            }), 403
        
        data = request.get_json()
        if not data or not data.get('patient_id'):
            return jsonify({
                "status": "error",
                "message": "Patient ID is required"
            }), 400
        
        # Validate patient exists
        patient = Patient.query.get(data['patient_id'])
        if not patient:
            return jsonify({
                "status": "error",
                "message": "Patient not found"
            }), 404
        
        # Create care plan
        care_plan = CarePlan(
            patient_id=data['patient_id'],
            created_by_id=current_user_id,
            assigned_nurse_id=data.get('assigned_nurse_id', current_user_id if role == "nurse" else None),
            supervising_doctor_id=data.get('supervising_doctor_id', current_user_id if role == "doctor" else None),
            description=data.get('description', ''),
            goals=data.get('goals', ''),
            start_date=datetime.now(),
            is_active=True
        )
        
        try:
            db.session.add(care_plan)
            db.session.commit()
            
            # Create initial tasks if provided
            if 'tasks' in data and isinstance(data['tasks'], list):
                for task_data in data['tasks']:
                    task = CarePlanTask(
                        care_plan_id=care_plan.care_plan_id,
                        description=task_data.get('description', ''),
                        frequency=task_data.get('frequency', 'daily'),
                        priority=task_data.get('priority', 'normal'),
                        status='pending',
                        scheduled_time=datetime.fromisoformat(task_data['scheduled_time'].replace('Z', '+00:00')) if task_data.get('scheduled_time') else None
                    )
                    db.session.add(task)
                db.session.commit()
            
            # Send notification to nurse if created by doctor
            if role == "doctor" and care_plan.assigned_nurse_id and care_plan.assigned_nurse_id != current_user_id:
                nurse_notification = Notification(
                    user_id=care_plan.assigned_nurse_id,
                    type="care_plan_assigned",
                    message=f"Dr. {User.query.get(current_user_id).last_name} assigned you to a new care plan for patient {patient.full_name()}",
                    scheduled_time=datetime.now(),
                    status="pending"
                )
                db.session.add(nurse_notification)
                db.session.commit()
                
            # Send notification to doctor if created by nurse
            elif role == "nurse" and care_plan.supervising_doctor_id and care_plan.supervising_doctor_id != current_user_id:
                doctor_notification = Notification(
                    user_id=care_plan.supervising_doctor_id,
                    type="care_plan_created",
                    message=f"Nurse {User.query.get(current_user_id).full_name()} created a new care plan for patient {patient.full_name()}",
                    scheduled_time=datetime.now(),
                    status="pending"
                )
                db.session.add(doctor_notification)
                db.session.commit()
            
            return jsonify({
                "status": "success",
                "message": "Care plan created successfully",
                "care_plan_id": care_plan.care_plan_id
            }), 201
            
        except Exception as e:
            db.session.rollback()
            return jsonify({
                "status": "error",
                "message": f"Failed to create care plan: {str(e)}"
            }), 500
    
    @staticmethod
    @jwt_required()
    def get_care_plans():
        """Get care plans for a patient or assigned to a nurse"""
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        role = claims.get("role")
        
        # Filter parameters
        patient_id = request.args.get('patient_id')
        active_only = request.args.get('active_only', 'true').lower() == 'true'
        
        # Build query based on role and filters
        query = CarePlan.query
        
        if role == "nurse":
            # Nurses see care plans assigned to them
            query = query.filter(CarePlan.assigned_nurse_id == current_user_id)
            
            # If patient_id specified, further filter by patient
            if patient_id:
                query = query.filter(CarePlan.patient_id == patient_id)
                
        elif role == "doctor":
            # Doctors see care plans they supervise
            query = query.filter(CarePlan.supervising_doctor_id == current_user_id)
            
            # If patient_id specified, further filter by patient
            if patient_id:
                query = query.filter(CarePlan.patient_id == patient_id)
                
        elif role == "patient":
            # Patients see only their own care plans
            query = query.filter(CarePlan.patient_id == current_user_id)
            
        else:
            return jsonify({
                "status": "error",
                "message": "Unauthorized role"
            }), 403
        
        # Filter by active status if requested
        if active_only:
            query = query.filter(CarePlan.is_active == True)
        
        # Execute query
        care_plans = query.order_by(CarePlan.start_date.desc()).all()
        
        # Format care plans for response
        care_plans_list = []
        for plan in care_plans:
            # Get patient info
            patient = Patient.query.get(plan.patient_id)
            patient_user = User.query.get(patient.patient_id) if patient else None
            
            # Get nurse info
            nurse = None
            if plan.assigned_nurse_id:
                nurse = User.query.get(plan.assigned_nurse_id)
            
            # Get doctor info
            doctor = None
            if plan.supervising_doctor_id:
                doctor = User.query.get(plan.supervising_doctor_id)
            
            # Get tasks
            tasks = []
            for task in plan.tasks:
                tasks.append({
                    "task_id": task.task_id,
                    "description": task.description,
                    "status": task.status,
                    "frequency": task.frequency,
                    "priority": task.priority,
                    "scheduled_time": task.scheduled_time.isoformat() if task.scheduled_time else None
                })
            
            # Get recent updates
            updates = []
            for update in plan.updates[:5]:  # Get 5 most recent updates
                updater = User.query.get(update.updated_by_id)
                updates.append({
                    "update_id": update.update_id,
                    "updated_by": f"{updater.first_name} {updater.last_name}" if updater else "Unknown",
                    "notes": update.notes,
                    "changes": update.changes,
                    "updated_at": update.updated_at.isoformat()
                })
            
            care_plans_list.append({
                "care_plan_id": plan.care_plan_id,
                "patient": {
                    "patient_id": patient.patient_id,
                    "name": f"{patient_user.first_name} {patient_user.last_name}" if patient_user else "Unknown"
                },
                "assigned_nurse": f"{nurse.first_name} {nurse.last_name}" if nurse else None,
                "supervising_doctor": f"Dr. {doctor.first_name} {doctor.last_name}" if doctor else None,
                "description": plan.description,
                "goals": plan.goals,
                "start_date": plan.start_date.isoformat(),
                "end_date": plan.end_date.isoformat() if plan.end_date else None,
                "is_active": plan.is_active,
                "tasks": tasks,
                "recent_updates": updates
            })
        
        return jsonify({
            "status": "success",
            "care_plans": care_plans_list
        }), 200
        
    @staticmethod
    @jwt_required()
    def collaborate_with_doctor():
        """
        Send a message or request to a doctor about a patient.
        This creates both a message and a notification.
        """
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        role = claims.get("role")
        
        # Only nurses can initiate collaboration
        if role != "nurse":
            return jsonify({
                "status": "error",
                "message": "Only nurses can use this collaboration endpoint"
            }), 403
        
        data = request.get_json()
        if not data or not data.get('doctor_id') or not data.get('message'):
            return jsonify({
                "status": "error",
                "message": "Doctor ID and message are required"
            }), 400
            
        # Validate doctor exists
        doctor_id = data['doctor_id']
        doctor = Doctor.query.get(doctor_id)
        if not doctor:
            return jsonify({
                "status": "error",
                "message": "Doctor not found"
            }), 404
        
        # If patient_id is provided, validate patient exists
        patient_id = data.get('patient_id')
        patient = None
        if patient_id:
            patient = Patient.query.get(patient_id)
            if not patient:
                return jsonify({
                    "status": "error",
                    "message": "Patient not found"
                }), 404
        
        try:
            # Create a message
            from models import Message
            message = Message(
                sender_id=current_user_id,
                receiver_id=doctor_id,
                content=data['message'],
                sent_at=datetime.now()
            )
            db.session.add(message)
            
            # Create a notification
            from models import Notification
            
            # Customize notification based on collaboration type
            collab_type = data.get('type', 'general')
            urgency = data.get('urgency', 'normal')
            
            if collab_type == 'consult':
                notification_type = "consult_request"
                notification_message = f"Consult requested: {data['message']}"
            elif collab_type == 'update':
                notification_type = "patient_update"
                notification_message = f"Patient update: {data['message']}"
            elif collab_type == 'question':
                notification_type = "medical_question"
                notification_message = f"Medical question: {data['message']}"
            else:
                notification_type = "nurse_message"
                notification_message = f"Message from nurse: {data['message']}"
            
            # Add patient info if provided
            if patient:
                patient_user = User.query.get(patient.patient_id)
                patient_name = f"{patient_user.first_name} {patient_user.last_name}" if patient_user else "Unknown patient"
                notification_message = f"RE: {patient_name} - " + notification_message
                
            notification = Notification(
                user_id=doctor_id,
                type=notification_type,
                message=notification_message,
                scheduled_time=datetime.now(),
                status="pending",
                priority=urgency
            )
            db.session.add(notification)
            
            db.session.commit()
            
            return jsonify({
                "status": "success",
                "message": "Collaboration message sent successfully",
                "message_id": message.message_id
            }), 201
            
        except Exception as e:
            db.session.rollback()
            return jsonify({
                "status": "error",
                "message": f"Failed to send collaboration message: {str(e)}"
            }), 500
    
    @staticmethod
    @jwt_required()
    def assign_nurse_to_appointment():
        """Assign a nurse to assist with an appointment"""
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        role = claims.get("role")
        
        # Only doctors can assign nurses to appointments
        if role not in ["doctor", "surgeon"]:
            return jsonify({
                "status": "error",
                "message": "Only doctors can assign nurses to appointments"
            }), 403
        
        data = request.get_json()
        if not data or not data.get('appointment_id') or not data.get('nurse_id'):
            return jsonify({
                "status": "error",
                "message": "Appointment ID and nurse ID are required"
            }), 400
        
        # Get appointment
        appointment = Appointment.query.get(data['appointment_id'])
        if not appointment:
            return jsonify({
                "status": "error",
                "message": "Appointment not found"
            }), 404
            
        # Verify user is the doctor for this appointment
        if appointment.doctor_id != current_user_id:
            return jsonify({
                "status": "error",
                "message": "You can only assign nurses to your own appointments"
            }), 403
            
        # Verify nurse exists and has the nurse role
        nurse = User.query.get(data['nurse_id'])
        if not nurse or nurse.role != UserRole.NURSE:
            return jsonify({
                "status": "error",
                "message": "Invalid nurse ID"
            }), 400
            
        try:
            # Update appointment with nurse ID
            appointment.nurse_id = nurse.user_id
            
            # Create notification for the nurse
            patient = Patient.query.get(appointment.patient_id)
            patient_user = User.query.get(patient.patient_id) if patient else None
            
            notification = Notification(
                user_id=nurse.user_id,
                appointment_id=appointment.appointment_id,
                type="assigned_to_appointment",
                message=f"You've been assigned to assist with an appointment for {patient_user.first_name} {patient_user.last_name if patient_user else 'Unknown'} on {appointment.date_time.strftime('%Y-%m-%d %H:%M')}",
                scheduled_time=datetime.now(),
                status="pending"
            )
            db.session.add(notification)
            
            db.session.commit()
            
            return jsonify({
                "status": "success",
                "message": f"Nurse {nurse.first_name} {nurse.last_name} assigned to appointment successfully"
            }), 200
            
        except Exception as e:
            db.session.rollback()
            return jsonify({
                "status": "error",
                "message": f"Failed to assign nurse to appointment: {str(e)}"
            }), 500