from flask import request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from datetime import timedelta
from models import User , UserRole
from services.db import db

class AuthController:
    @staticmethod
    def signup():
        data = request.get_json()
        
        # Validate input
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({"error": "Missing email or password"}), 400
            
        # Check if user exists
        if User.query.filter_by(email=data['email']).first():
            return jsonify({"error": "User already exists"}), 409
            
        # Determine user role - default to PATIENT if not provided
        role_str = data.get('role', "PATIENT").upper()
        if role_str not in [role.name for role in UserRole]:
            return jsonify({"error": f"Invalid role: {role_str}"}), 400

        role = UserRole[role_str]
        
        # Create new user
        hashed_password = generate_password_hash(data['password'])
        new_user = User(
            email=data['email'],
            password_hash=hashed_password,
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            role=role,
            phone=data.get('phone', '')
        )
        
        db.session.add(new_user)
        db.session.flush()  # This assigns the user_id without committing the transaction
        
        # Create role-specific record
        if role in [UserRole.DOCTOR, UserRole.NURSE, UserRole.SURGEON, UserRole.THERAPIST]:
            # Import here to avoid circular imports
            from models import Doctor
            
            # Validate specialty for doctors
            specialty = data.get('specialty')
            if not specialty:
                specialty = role  # Default to their role as specialty if not provided
            
            description = data.get('description')

            # Create doctor record
            doctor = Doctor(
                doctor_id=new_user.user_id,
                specialty=specialty,
                description=description
            )
            db.session.add(doctor)
            
        elif role == UserRole.PATIENT:
            # Import here to avoid circular imports
            from models import Patient
            
            # Create patient record
            patient = Patient(
                patient_id=new_user.user_id,
                date_of_birth=data.get('date_of_birth'),
                emergency_contact_name=data.get('emergency_contact_name'),
                emergency_contact_phone=data.get('emergency_contact_phone'),
                insurance_id=data.get('insurance_id'),
            )
            db.session.add(patient)
        
        # Now commit everything
        db.session.commit()
        
        # Auto-login by creating access token
        access_token = create_access_token(
            identity=new_user,
            expires_delta=timedelta(hours=1),
            additional_claims={
                "role": new_user.role.name,
                "email": new_user.email
            }
        )
        
        return jsonify({
            "message": "User created successfully",
            "access_token": access_token,
            "user_id": new_user.user_id,
            "role": role.name
        }), 201


    @staticmethod
    def login():
        data = request.get_json()
        
        # Validate input
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({"error": "Missing email or password"}), 400
            
        user = User.query.filter_by(email=data['email']).first()
        
        # Verify user and password
        if not user or not check_password_hash(user.password_hash, data['password']):
            return jsonify({"error": "Invalid credentials"}), 401
            
        # Create JWT token
        access_token = create_access_token(
            identity=user,
            expires_delta=timedelta(hours=1),
            additional_claims={
                "role": user.role.name,
                "email": user.email
            }
        )
        
        return jsonify({
            "access_token": access_token,
            "user_id": user.user_id,
            "role": user.role.name
        }), 200

    @staticmethod
    @jwt_required()
    def protected():
        current_user = get_jwt_identity()
        return jsonify(logged_in_as=current_user), 200