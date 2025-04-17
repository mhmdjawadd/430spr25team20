from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.db import db
from models import User, Patient, Insurance, InsuranceCoverage, Doctor, Appointment

class InsuranceController:
    @staticmethod
    @jwt_required()
    def get_patient_insurance():
        """
        Get the insurance information for the current patient or a specified patient
        """
        # Get the current user
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user:
            return jsonify({"error": "User not found"}), 404
        
        # Get query parameters
        patient_id = request.args.get('patient_id')
        
        # If user is not a patient and no patient_id is provided
        if current_user.role.name != "PATIENT" and not patient_id:
            return jsonify({"error": "Patient ID required for non-patient users"}), 400
            
        # Determine which patient's insurance to retrieve
        if patient_id:
            # Only staff can view other patients' insurance
            if current_user.role.name == "PATIENT" and str(current_user.user_id) != patient_id:
                return jsonify({"error": "Unauthorized to view other patients' insurance"}), 403
            patient = Patient.query.get(patient_id)
        else:
            # Use the current user's patient record
            patient = Patient.query.get(current_user.user_id)
            
        if not patient:
            return jsonify({"error": "Patient record not found"}), 404
            
        # Get the insurance information
        insurance = Insurance.query.get(patient.patient_id)
        
        if not insurance:
            return jsonify({
                "patient_id": patient.patient_id,
                "patient_name": patient.full_name(),
                "insurance": None
            }), 200
            
        # Return the insurance details
        return jsonify({
            "patient_id": patient.patient_id,
            "patient_name": patient.full_name(),
            "insurance": {
                "provider": insurance.provider_name,
                "policy_number": insurance.policy_number,
                "coverage_type": insurance.coverage_type.name
            }
        }), 200
        
    @staticmethod
    @jwt_required()
    def update_patient_insurance():
        """
        Update or create insurance information for a patient, including detailed fields.
        """
        # Get the current user
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user:
            return jsonify({"error": "User not found"}), 404
            
        # Get request data
        data = request.get_json()
        
        # Determine which patient's insurance to update
        if current_user.role.name != "PATIENT":
            # Staff members can update any patient's insurance
            if not data.get('patient_id'):
                return jsonify({"error": "Patient ID required for staff users"}), 400
            patient = Patient.query.get(data.get('patient_id'))
        else:
            # Patients can only update their own insurance
            patient = Patient.query.get(current_user.user_id)
            
        if not patient:
            return jsonify({"error": "Patient record not found"}), 404
            
        # Validate required fields - provider_name and policy_number might be optional if coverage_type is NONE
        required_fields = ["coverage_type"]
        if data.get("coverage_type") != "NONE":
            required_fields.extend(["provider_name", "policy_number"])

        for field in required_fields:
            if field not in data or not data[field]: # Check for presence and non-empty value
                # Allow NONE coverage type without provider/policy
                if field in ["provider_name", "policy_number"] and data.get("coverage_type") == "NONE":
                    continue
                return jsonify({"error": f"Missing required field: {field}"}), 400

        # Validate coverage type
        try:
            # Handle potential None value for coverage_type if allowed, otherwise default or raise error
            coverage_input = data.get("coverage_type", "NONE") # Default to NONE if not provided
            coverage_type = InsuranceCoverage[coverage_input.upper()]
        except KeyError:
            valid_types = ", ".join([t.name for t in InsuranceCoverage])
            return jsonify({"error": f"Invalid coverage type. Valid types: {valid_types}"}), 400
        except AttributeError:
             return jsonify({"error": "Coverage type must be a string"}), 400


        # Create or update insurance record
        insurance = Insurance.query.get(patient.patient_id)
        if not insurance:
            insurance = Insurance(patient_id=patient.patient_id)
            db.session.add(insurance)

        # Update all fields from the request data
        insurance.coverage_type = coverage_type
        # Set provider/policy to None if coverage is NONE, otherwise use provided data
        insurance.provider_name = data.get("provider_name") if coverage_type != InsuranceCoverage.NONE else None
        insurance.policy_number = data.get("policy_number") if coverage_type != InsuranceCoverage.NONE else None
        insurance.group_number = data.get("group_number") # Optional field
        insurance.policy_holder_name = data.get("policy_holder_name") # Optional field
        insurance.coverage_start_date = data.get("coverage_start_date") # Optional field, ensure frontend sends YYYY-MM-DD
        insurance.coverage_end_date = data.get("coverage_end_date") # Optional field, ensure frontend sends YYYY-MM-DD
        insurance.front_card_image = data.get("front_card_image") # Optional field (Base64 string)
        insurance.back_card_image = data.get("back_card_image") # Optional field (Base64 string)


        try:
            db.session.commit()
            # Return more detailed insurance info
            return jsonify({
                "message": "Insurance information updated successfully",
                "insurance": {
                    "patient_id": insurance.patient_id,
                    "coverage_type": insurance.coverage_type.name,
                    "provider_name": insurance.provider_name,
                    "policy_number": insurance.policy_number,
                    "group_number": insurance.group_number,
                    "policy_holder_name": insurance.policy_holder_name,
                    "coverage_start_date": str(insurance.coverage_start_date) if insurance.coverage_start_date else None,
                    "coverage_end_date": str(insurance.coverage_end_date) if insurance.coverage_end_date else None,
                    "has_front_card_image": bool(insurance.front_card_image), # Indicate if image exists
                    "has_back_card_image": bool(insurance.back_card_image)   # Indicate if image exists
                }
            }), 200
        except Exception as e:
            db.session.rollback()
            # Provide more specific error logging on the server side if needed
            print(f"Error updating insurance: {e}") # Log the error server-side
            return jsonify({"error": f"Failed to update insurance: {str(e)}"}), 500
            
    @staticmethod
    @jwt_required()
    def verify_coverage():
        """
        Verify if an appointment would be covered by insurance
        """
        # Get the current user
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user:
            return jsonify({"error": "User not found"}), 404
            
        # Get request data
        data = request.get_json()
        
        # Determine which patient's insurance to check
        if current_user.role.name != "PATIENT":
            # Staff members can check any patient's insurance
            if not data.get('patient_id'):
                return jsonify({"error": "Patient ID required for staff users"}), 400
            patient = Patient.query.get(data.get('patient_id'))
        else:
            # Patients can only check their own insurance
            patient = Patient.query.get(current_user.user_id)
            
        if not patient:
            return jsonify({"error": "Patient record not found"}), 404
            
        # Validate required fields
        if "doctor_id" not in data:
            return jsonify({"error": "Missing required field: doctor_id"}), 400
            
        # Get the doctor information
        doctor = Doctor.query.get(data["doctor_id"])
        if not doctor:
            return jsonify({"error": "Doctor not found"}), 404
            
        # Get insurance information
        insurance = Insurance.query.get(patient.patient_id)
        if not insurance:
            return jsonify({
                "has_insurance": False,
                "message": "Patient does not have insurance information on file"
            }), 200
            
        # Calculate coverage
        # Assuming a standard base cost for simplicity - could be based on doctor specialty, etc.
        base_cost = 100  # $100 standard appointment cost
        covered_amount, patient_responsibility = insurance.calculate_coverage(
            doctor_specialty=doctor.specialty.value, 
            base_cost=base_cost
        )
        
        # Determine if appointment is sufficiently covered
        is_covered = covered_amount > 0
        coverage_percent = (covered_amount / base_cost) * 100 if base_cost > 0 else 0
        
        return jsonify({
            "has_insurance": True,
            "is_covered": is_covered,
            "coverage_details": {
                "provider": insurance.provider_name,
                "policy_number": insurance.policy_number,
                "coverage_type": insurance.coverage_type.name,
                "base_cost": base_cost,
                "covered_amount": covered_amount,
                "patient_responsibility": patient_responsibility,
                "coverage_percent": f"{coverage_percent:.1f}%"
            },
            "message": "Insurance verification complete"
        }), 200