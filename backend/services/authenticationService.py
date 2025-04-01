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
            
        # Create new user
        hashed_password = generate_password_hash(data['password'])
        new_user = User(
            email=data['email'],
            password_hash=hashed_password,
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            role= UserRole[data.get('role',"PATIENT").upper()],
            phone=data.get('phone', '')
            )
        
        db.session.add(new_user)
        db.session.commit()
        
            # Auto-login by creating access token
        access_token = create_access_token(
            identity=new_user, #identity is the 'sub' claim in the JWT
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
            "role": new_user.role.name
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