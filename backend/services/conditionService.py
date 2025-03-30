from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime
from services.db import db
from models import ChronicCondition, ConditionTracking, Patient, Doctor, User

class ConditionController:
    @staticmethod
    @jwt_required()
    def get_conditions():
        """Get chronic conditions for a patient"""
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        role = claims.get("role")
        
        patient_id = request.args.get('patient_id')
        
        # If role is patient, can only access their own conditions
        if role == "patient":
            patient_id = current_user_id
                
        # If doctor and no patient_id specified, return error
        elif role in ["doctor", "surgeon", "nurse"] and not patient_id:
            return jsonify({
                "status": "error", 
                "message": "Patient ID required for medical staff to access conditions"
            }), 400
            
        # If not patient or medical staff, unauthorized
        elif role not in ["patient", "doctor", "surgeon", "nurse"]:
            return jsonify({
                "status": "error",
                "message": "Unauthorized access to chronic condition data"
            }), 403
        
        # Get conditions
        conditions = ChronicCondition.query.filter_by(patient_id=patient_id).all()
        
        # Format conditions for response
        conditions_list = []
        for condition in conditions:
            # Get latest tracking record if it exists
            latest_tracking = (ConditionTracking.query
                              .filter_by(condition_id=condition.condition_id)
                              .order_by(ConditionTracking.tracked_date.desc())
                              .first())
            
            conditions_list.append({
                "condition_id": condition.condition_id,
                "name": condition.name,
                "diagnosis_date": condition.diagnosis_date.isoformat(),
                "description": condition.description,
                "latest_status": {
                    "date": latest_tracking.tracked_date.isoformat() if latest_tracking else None,
                    "severity": latest_tracking.severity if latest_tracking else None,
                    "notes": latest_tracking.notes if latest_tracking else None
                } if latest_tracking else None
            })
        
        return jsonify({
            "status": "success",
            "conditions": conditions_list
        }), 200
    
    @staticmethod
    @jwt_required()
    def create_condition():
        """Create a new chronic condition record"""
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        role = claims.get("role")
        
        # Only medical staff can create conditions
        if role not in ["doctor", "surgeon", "nurse"]:
            return jsonify({
                "status": "error",
                "message": "Only medical staff can create condition records"
            }), 403
        
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No data provided"}), 400
        
        # Validate required fields
        if not data.get('patient_id') or not data.get('name'):
            return jsonify({
                "status": "error", 
                "message": "Patient ID and condition name are required"
            }), 400
        
        # Parse diagnosis date if provided
        diagnosis_date = None
        if data.get('diagnosis_date'):
            try:
                diagnosis_date = datetime.fromisoformat(data['diagnosis_date'].replace('Z', '+00:00'))
            except ValueError:
                return jsonify({
                    "status": "error",
                    "message": "Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"
                }), 400
        
        # Create condition
        new_condition = ChronicCondition(
            patient_id=data['patient_id'],
            name=data['name'],
            diagnosis_date=diagnosis_date or datetime.utcnow(),
            description=data.get('description', '')
        )
        
        try:
            db.session.add(new_condition)
            db.session.commit()
            
            return jsonify({
                "status": "success",
                "message": "Chronic condition record created successfully",
                "condition_id": new_condition.condition_id
            }), 201
            
        except Exception as e:
            db.session.rollback()
            return jsonify({
                "status": "error",
                "message": f"Failed to create condition record: {str(e)}"
            }), 500
    
    @staticmethod
    @jwt_required()
    def track_condition():
        """Add a tracking record for a chronic condition"""
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        role = claims.get("role")
        
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No data provided"}), 400
        
        # Validate required fields
        if not data.get('condition_id'):
            return jsonify({
                "status": "error", 
                "message": "Condition ID is required"
            }), 400
        
        # Get the condition
        condition = ChronicCondition.query.get(data['condition_id'])
        if not condition:
            return jsonify({
                "status": "error",
                "message": "Condition not found"
            }), 404
        
        # Check authorization
        if role == "patient" and condition.patient_id != current_user_id:
            return jsonify({
                "status": "error",
                "message": "You can only track your own conditions"
            }), 403
        
        # Create tracking record
        new_tracking = ConditionTracking(
            condition_id=condition.condition_id,
            severity=data.get('severity'),
            notes=data.get('notes', ''),
            vital_signs=data.get('vital_signs', '')
        )
        
        try:
            db.session.add(new_tracking)
            db.session.commit()
            
            return jsonify({
                "status": "success",
                "message": "Condition tracking record added successfully",
                "tracking_id": new_tracking.tracking_id
            }), 201
            
        except Exception as e:
            db.session.rollback()
            return jsonify({
                "status": "error",
                "message": f"Failed to add tracking record: {str(e)}"
            }), 500