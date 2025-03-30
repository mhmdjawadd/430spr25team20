from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from services.db import db
from models import MedicalRecord, Patient, Doctor, User

class MedicalRecordController:
    @staticmethod
    @jwt_required()
    def get_patient_records():
        """Get medical records for a patient"""
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        role = claims.get("role")
        
        patient_id = request.args.get('patient_id')
        
        # If role is patient, can only access their own records
        if role == "patient":
            patient = Patient.query.filter_by(patient_id=current_user_id).first()
            if not patient:
                return jsonify({"status": "error", "message": "Patient profile not found"}), 404
            patient_id = patient.patient_id
                
        # If doctor and no patient_id specified, return error
        elif role in ["doctor", "surgeon", "nurse"] and not patient_id:
            return jsonify({
                "status": "error", 
                "message": "Patient ID required for medical staff to access records"
            }), 400
            
        # If not patient or medical staff, unauthorized
        elif role not in ["patient", "doctor", "surgeon", "nurse"]:
            return jsonify({
                "status": "error",
                "message": "Unauthorized access to medical records"
            }), 403
        
        # Get records
        records = MedicalRecord.query.filter_by(patient_id=patient_id).all()
        
        # Format records for response
        records_list = []
        for record in records:
            doctor_user = User.query.get(record.doctor_id)
            
            # Get prescriptions
            prescriptions = []
            for prescription in record.prescriptions:
                prescriptions.append({
                    "medication_name": prescription.medication_name,
                    "dosage": prescription.dosage,
                    "instructions": prescription.instructions,
                    "start_date": prescription.start_date.isoformat(),
                    "end_date": prescription.end_date.isoformat() if prescription.end_date else None
                })
            
            records_list.append({
                "record_id": record.record_id,
                "description": record.description,
                "doctor": f"Dr. {doctor_user.first_name} {doctor_user.last_name}" if doctor_user else "Unknown",
                "date": record.created_at.isoformat() if hasattr(record, 'created_at') else None,
                "prescriptions": prescriptions
            })
        
        return jsonify({
            "status": "success",
            "records": records_list
        }), 200
    
    @staticmethod
    @jwt_required()
    def create_medical_record():
        """Create a new medical record"""
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        role = claims.get("role")
        
        # Only medical staff can create records
        if role not in ["doctor", "surgeon", "nurse"]:
            return jsonify({
                "status": "error",
                "message": "Only medical staff can create records"
            }), 403
        
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No data provided"}), 400
        
        # Validate required fields
        if not data.get('patient_id') or not data.get('description'):
            return jsonify({
                "status": "error", 
                "message": "Patient ID and description are required"
            }), 400
        
        # Create record
        new_record = MedicalRecord(
            patient_id=data['patient_id'],
            doctor_id=current_user_id,
            description=data['description']
        )
        
        try:
            db.session.add(new_record)
            db.session.commit()
            
            # Add prescriptions if provided
            if data.get('prescriptions'):
                from models import Prescription
                for prescription_data in data['prescriptions']:
                    prescription = Prescription(
                        record_id=new_record.record_id,
                        medication_name=prescription_data['medication_name'],
                        dosage=prescription_data['dosage'],
                        instructions=prescription_data.get('instructions', ''),
                        start_date=datetime.fromisoformat(prescription_data['start_date'].replace('Z', '+00:00')),
                        end_date=datetime.fromisoformat(prescription_data['end_date'].replace('Z', '+00:00')) if prescription_data.get('end_date') else None
                    )
                    db.session.add(prescription)
                
                db.session.commit()
            
            return jsonify({
                "status": "success",
                "message": "Medical record created successfully",
                "record_id": new_record.record_id
            }), 201
            
        except Exception as e:
            db.session.rollback()
            return jsonify({
                "status": "error",
                "message": f"Failed to create medical record: {str(e)}"
            }), 500