import json
import os
import base64
from datetime import datetime, timedelta
from flask import request, jsonify, redirect, url_for
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
import google.oauth2.credentials
import googleapiclient.discovery
from google_auth_oauthlib.flow import Flow
from services.db import db
from models import Doctor, User, Appointment

class CalendarSyncController:
    # Google Calendar API constants
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    API_SERVICE_NAME = 'calendar'
    API_VERSION = 'v3'
    
    @staticmethod
    def get_client_config():
        """Get OAuth client configuration from environment or config file"""
        # In production, these would come from environment variables or secure storage
        return {
            "web": {
                "client_id": os.environ.get("GOOGLE_CLIENT_ID", "YOUR_CLIENT_ID"),
                "client_secret": os.environ.get("GOOGLE_CLIENT_SECRET", "YOUR_CLIENT_SECRET"),
                "redirect_uris": [os.environ.get("GOOGLE_REDIRECT_URI", "http://localhost:5000/calendar/oauth2callback")],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
        }
    
    @staticmethod
    @jwt_required()
    def start_oauth_flow():
        """Start the OAuth flow to connect Google Calendar"""
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        role = claims.get("role")
        
        # Only doctors can sync calendars
        if role not in ["doctor", "surgeon"]:
            return jsonify({
                "status": "error",
                "message": "Only doctors can sync calendars"
            }), 403
        
        # Create the flow using client config
        flow = Flow.from_client_config(
            CalendarSyncController.get_client_config(),
            scopes=CalendarSyncController.SCOPES,
            redirect_uri=CalendarSyncController.get_client_config()['web']['redirect_uris'][0]
        )
        
        # Generate the authorization URL
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'  # Force prompt to ensure we get a refresh token
        )
        
        # Store the state in the database or session for verification later
        # This is a simplified implementation
        from models import CalendarIntegration
        
        integration = CalendarIntegration(
            user_id=current_user_id,
            provider="google",
            oauth_state=state,
            created_at=datetime.now()
        )
        
        try:
            db.session.add(integration)
            db.session.commit()
            
            return jsonify({
                "status": "success",
                "authorization_url": authorization_url
            }), 200
            
        except Exception as e:
            db.session.rollback()
            return jsonify({
                "status": "error",
                "message": f"Failed to start OAuth flow: {str(e)}"
            }), 500
    
    @staticmethod
    def oauth2callback():
        """Handle the OAuth callback from Google"""
        # Get state and code from the callback
        state = request.args.get('state', '')
        code = request.args.get('code', '')
        
        # Find the integration record with this state
        from models import CalendarIntegration
        integration = CalendarIntegration.query.filter_by(oauth_state=state).first()
        
        if not integration:
            return jsonify({
                "status": "error",
                "message": "Invalid OAuth state"
            }), 400
        
        try:
            # Create the flow with the same parameters
            flow = Flow.from_client_config(
                CalendarSyncController.get_client_config(),
                scopes=CalendarSyncController.SCOPES,
                state=state,
                redirect_uri=CalendarSyncController.get_client_config()['web']['redirect_uris'][0]
            )
            
            # Exchange the code for credentials
            flow.fetch_token(code=code)
            credentials = flow.credentials
            
            # Store the credentials
            integration.access_token = credentials.token
            integration.refresh_token = credentials.refresh_token
            integration.token_expiry = datetime.now() + timedelta(seconds=credentials.expires_in)
            integration.token_uri = credentials.token_uri
            integration.client_id = credentials.client_id
            integration.client_secret = credentials.client_secret
            integration.scopes = json.dumps(credentials.scopes)
            integration.connected_at = datetime.now()
            
            db.session.commit()
            
            # Return success
            return redirect("/calendar/success")
            
        except Exception as e:
            db.session.rollback()
            return jsonify({
                "status": "error",
                "message": f"Failed to complete OAuth flow: {str(e)}"
            }), 500
    
    @staticmethod
    def get_credentials(user_id):
        """Get Google Calendar credentials for a user"""
        from models import CalendarIntegration
        integration = CalendarIntegration.query.filter_by(
            user_id=user_id, 
            provider="google"
        ).first()
        
        if not integration or not integration.access_token:
            return None
        
        # Check if token is expired and needs refresh
        if integration.token_expiry and integration.token_expiry < datetime.now():
            # Would implement token refresh here
            pass
        
        # Create credentials object
        credentials = google.oauth2.credentials.Credentials(
            token=integration.access_token,
            refresh_token=integration.refresh_token,
            token_uri=integration.token_uri,
            client_id=integration.client_id,
            client_secret=integration.client_secret,
            scopes=json.loads(integration.scopes)
        )
        
        return credentials
    
    @staticmethod
    @jwt_required()
    def sync_appointments():
        """Sync appointments to Google Calendar"""
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        role = claims.get("role")
        
        # Only doctors can sync calendars
        if role not in ["doctor", "surgeon"]:
            return jsonify({
                "status": "error",
                "message": "Only doctors can sync calendars"
            }), 403
        
        # Check if user has connected their calendar
        credentials = CalendarSyncController.get_credentials(current_user_id)
        if not credentials:
            return jsonify({
                "status": "error",
                "message": "Calendar not connected. Please connect your Google Calendar first."
            }), 400
        
        try:
            # Build the calendar service
            service = googleapiclient.discovery.build(
                CalendarSyncController.API_SERVICE_NAME,
                CalendarSyncController.API_VERSION,
                credentials=credentials
            )
            
            # Get doctor's appointments that need syncing
            doctor = Doctor.query.filter_by(doctor_id=current_user_id).first()
            
            # Get date range - default to next 30 days
            start_date = datetime.now()
            end_date = start_date + timedelta(days=30)
            
            appointments = Appointment.query.filter(
                Appointment.doctor_id == doctor.doctor_id,
                Appointment.date_time >= start_date,
                Appointment.date_time <= end_date
            ).all()
            
            # Track successful and failed syncs
            synced_count = 0
            failed_count = 0
            
            # For each appointment, create or update Google Calendar event
            for appointment in appointments:
                # Skip if already synced and not modified
                if hasattr(appointment, 'calendar_event_id') and appointment.calendar_event_id:
                    continue
                
                patient = Patient.query.get(appointment.patient_id)
                patient_user = User.query.get(patient.patient_id) if patient else None
                patient_name = f"{patient_user.first_name} {patient_user.last_name}" if patient_user else "Patient"
                
                # Create event
                event = {
                    'summary': f"Appointment with {patient_name}",
                    'description': appointment.reason,
                    'start': {
                        'dateTime': appointment.date_time.isoformat(),
                        'timeZone': 'America/New_York',  # Would use doctor's timezone
                    },
                    'end': {
                        'dateTime': (appointment.date_time + timedelta(minutes=appointment.duration)).isoformat(),
                        'timeZone': 'America/New_York',  # Would use doctor's timezone
                    },
                    'reminders': {
                        'useDefault': False,
                        'overrides': [
                            {'method': 'popup', 'minutes': 15},
                        ],
                    },
                }
                
                try:
                    # Insert the event
                    created_event = service.events().insert(calendarId='primary', body=event).execute()
                    
                    # Update appointment with calendar event ID
                    appointment.calendar_event_id = created_event['id']
                    appointment.last_synced = datetime.now()
                    synced_count += 1
                    
                except Exception as e:
                    print(f"Failed to sync appointment {appointment.appointment_id}: {str(e)}")
                    failed_count += 1
            
            db.session.commit()
            
            return jsonify({
                "status": "success",
                "message": f"Calendar sync completed. {synced_count} appointments synced, {failed_count} failed."
            }), 200
            
        except Exception as e:
            db.session.rollback()
            return jsonify({
                "status": "error",
                "message": f"Failed to sync calendar: {str(e)}"
            }), 500