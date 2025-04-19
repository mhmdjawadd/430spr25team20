from sqlalchemy import Column, Enum, Integer, String, ForeignKey , JSON
from sqlalchemy.orm import relationship
from .base import *
from .user import UserRole

class Doctor(Base):
    __tablename__ = 'doctors'
    
    doctor_id = Column(Integer, ForeignKey('users.user_id'), primary_key=True)
    specialty = Column(Enum(UserRole), nullable=False) #  nurse ,  doctor , surgeon , therapist
    availability = Column(JSON, nullable=True, default={
    "monday": ["09-10", "10-11", "11-12", "12-13", "13-14", "14-15", "15-16", "16-17"],
    "tuesday": ["09-10", "10-11", "11-12", "12-13", "13-14", "14-15", "15-16", "16-17"],
    "wednesday": ["09-10", "10-11", "11-12", "12-13", "13-14", "14-15", "15-16", "16-17"],
    "thursday": ["09-10", "10-11", "11-12", "12-13", "13-14", "14-15", "15-16", "16-17"],
    "friday": ["09-10", "10-11", "11-12", "12-13", "13-14", "14-15", "15-16", "16-17"],
    "saturday": [],
    "sunday": []
})

    # Relationships
    user = relationship("User", back_populates="doctor")
    appointments = relationship("Appointment", back_populates="doctor")
    
    patients = relationship("Patient", back_populates="doctor")
    medical_records = relationship("MedicalRecord", back_populates="doctor")
    sent_referrals = relationship("Referral", foreign_keys="Referral.referring_doctor_id", back_populates="referring_doctor")
    received_referrals = relationship("Referral", foreign_keys="Referral.specialist_id", back_populates="specialist")

    @classmethod
    def get_availability(cls, db_session, name, date):
        """
        Get doctor's real-time availability accounting for booked appointments
        
        Args:
            db_session: Database session
            name: Doctor's name (optional)
            date: Specific date to check (optional, defaults to today)
            
        Returns:
            List of doctors with their available time slots after accounting for bookings
        """
        from datetime import datetime, timedelta, time
        from sqlalchemy import and_, func
        from models.appointment import Appointment
        
        # Use today's date if not specified
        if not date:
            date = datetime.now().date()
        
        # Get weekday as integer (0=Monday, 6=Sunday)
        weekday_num = date.weekday()
        weekday_name = date.strftime("%A")
         
        # Build query to get doctors
        query = db_session.query(cls).join(cls.user)
        if name:
            try:
                first_name = name.split()[0]
                last_name = name.split()[1] if len(name.split()) > 1 else ""
                query = query.filter(cls.user.has(first_name=first_name, last_name=last_name))
            except Exception as e:
                print(f"Error filtering by name: {e}")
                # Continue without the name filter
        
        doctors = query.all()
        result = []
        
        for doctor in doctors:
            # Default time slots for the day (8am-5pm in 30 min increments)
            available_slots = []
            
            # Only process weekdays (Monday=0 through Friday=4)
            if weekday_num < 5:  # 0-4 are weekdays
                # Generate slots in 30-minute increments
                current_time = datetime.combine(date, time(8, 0))  # Start at 8 AM
                end_time = datetime.combine(date, time(17, 0))     # End at 5 PM
                
                # Get appointments for this doctor on the specified date
                appointments = db_session.query(Appointment).filter(
                    and_(
                        Appointment.doctor_id == doctor.doctor_id,
                        func.date(Appointment.date_time) == date
                    )
                ).all()
                
                # Create a list of booked time slots
                booked_slots = []
                for appt in appointments:
                    appt_start = appt.date_time
                    appt_end = appt_start + timedelta(minutes=30)
                    booked_slots.append((appt_start, appt_end))
                
                # Generate available slots in 30-minute increments
                while current_time < end_time:
                    slot_start = current_time
                    slot_end = current_time + timedelta(minutes=30)
                    
                    # Check if this slot overlaps with any booked appointment
                    is_available = True
                    for booked_start, booked_end in booked_slots:
                        if slot_start < booked_end and slot_end > booked_start:
                            is_available = False
                            break
                    
                    # If slot is available, add it to the list
                    if is_available:
                        available_slots.append({
                            "start": slot_start.strftime("%H:%M"),
                            "end": slot_end.strftime("%H:%M")
                        })
                    
                    # Move to the next slot
                    current_time = slot_end
            
            result.append({
                "doctor_id": doctor.doctor_id,
                "name": f"{doctor.user.first_name} {doctor.user.last_name}",
                "specialty": doctor.specialty.name if hasattr(doctor.specialty, 'name') else str(doctor.specialty),
                "date": date.strftime("%Y-%m-%d"),
                "day": weekday_name,
                "available_slots": available_slots
            })
            
        return result