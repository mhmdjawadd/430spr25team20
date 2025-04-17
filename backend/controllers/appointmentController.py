from datetime import datetime, timedelta
from flask import request, jsonify
from models.appointment import AppointmentType, RecurrencePattern
from services.appointmentService import AppointmentService

class AppointmentController:
    @staticmethod
    def book_appointment():
        """Book a new appointment"""
        try:
            # Get request data
            data = request.get_json()
            
            # Book the appointment using the appointment service
            appointment = AppointmentService.book_appointment(data)
            
            # Return the appointment details
            return jsonify({
                "status": "success",
                "appointment": appointment
            }), 201
        except Exception as e:
            return jsonify({
                "status": "error",
                "error": str(e)
            }), 400
    
    @staticmethod
    def get_available_slots():
        """Get available appointment slots for a doctor on a specific date"""
        try:
            doctor_id = request.args.get('doctor_id')
            date_str = request.args.get('date')
            
            if not doctor_id or not date_str:
                return jsonify({
                    "status": "error",
                    "error": "Missing required parameters"
                }), 400
            
            # Parse date
            date = datetime.strptime(date_str, "%Y-%m-%d").date()
            
            # Get available slots using the appointment service
            slots = AppointmentService.get_available_slots(doctor_id, date)
            
            # Return the slots
            return jsonify(slots), 200
        except Exception as e:
            return jsonify({
                "status": "error",
                "error": str(e)
            }), 400
    
    @staticmethod
    def get_doctor_availability_range():
        """Get doctor availability across a date range (week/month view)"""
        try:
            # Get request data
            data = request.get_json()
            doctor_id = data.get('doctor_id')
            start_date_str = data.get('start_date')
            end_date_str = data.get('end_date')
            
            if not doctor_id or not start_date_str or not end_date_str:
                return jsonify({
                    "status": "error",
                    "error": "Missing required parameters"
                }), 400
            
            # Parse dates
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            
            # Get availability across the date range
            availability = AppointmentService.get_availability_range(doctor_id, start_date, end_date)
            
            # Return the availability data
            return jsonify({
                "status": "success",
                "availability": availability
            }), 200
        except Exception as e:
            return jsonify({
                "status": "error",
                "error": str(e)
            }), 400