from sqlalchemy import Column, Enum, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from .base import *
from .user import UserRole
class Doctor(Base):
    __tablename__ = 'doctors'
    
    doctor_id = Column(Integer, ForeignKey('users.user_id'), primary_key=True)
    specialty = Column(Enum(UserRole), nullable=False) #  nurse ,  doctor , surgeon , therapist

    # Relationships
    user = relationship("User", back_populates="doctor")
    appointments = relationship("Appointment", back_populates="doctor")
    or_availability = relationship("ORAvailability", back_populates="surgeon")
    patients = relationship("Patient", back_populates="doctor")
    medical_records = relationship("MedicalRecord", back_populates="doctor")

    @classmethod # i used this to look over all the docs 
    def get_availability(cls, db_session, name, date):
        """
        Private function to get doctor's real-time availability accounting for booked appointments
        
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
        query = db_session.query(Doctor).join(Doctor.user)
        if name:
            first_name = name.split()[0] 
            last_name = name.split()[1]
            query = query.filter(
            Doctor.user.has(first_name=first_name, last_name=last_name)
            )
        
        doctors = query.all()
        result = []
        
        for doctor in doctors:
            # Set standard working hours (8am-5pm weekdays)
            available_slots = []
            
            # Only process weekdays (Monday=0 through Friday=4)
            if weekday_num < 5:  # 0-4 are weekdays
                # Standard hours: 8am to 5pm
                start_time = time(8, 0)
                end_time = time(17, 0)
                
                # Convert time objects to datetime for easier manipulation
                start_dt = datetime.combine(date, start_time)
                end_dt = datetime.combine(date, end_time)
                
                # Start with the full day available
                free_periods = [(start_dt, end_dt)]
                
                # Get appointments for this doctor on the specified date
                appointments = db_session.query(Appointment).filter(
                    and_(
                        Appointment.doctor_id == doctor.doctor_id,
                        func.date(Appointment.date_time) == date
                    )
                ).order_by(Appointment.date_time).all()
                
                # Remove appointment times
                for appt in appointments:
                    appt_start = appt.appointment_datetime
                    appt_end = appt_start + timedelta(minutes=30)  # Assuming 30-min appointments
                    
                    # Create new list of free times by removing this appointment
                    updated_free_periods = []
                    
                    for free_start, free_end in free_periods:
                        # Case 1: Appointment is completely within free period
                        if free_start < appt_start and free_end > appt_end:
                            updated_free_periods.append((free_start, appt_start))
                            updated_free_periods.append((appt_end, free_end))
                        # Case 2: Appointment starts during free period
                        elif free_start < appt_start <= free_end:
                            updated_free_periods.append((free_start, appt_start))
                        # Case 3: Appointment ends during free period
                        elif free_start <= appt_end < free_end:
                            updated_free_periods.append((appt_end, free_end))
                        # Case 4: No overlap with this free period
                        elif appt_end <= free_start or appt_start >= free_end:
                            updated_free_periods.append((free_start, free_end))
                    
                    free_periods = updated_free_periods
                
                # Add the free periods to our result
                for free_start, free_end in free_periods:
                    available_slots.append({
                        "start": free_start.strftime("%H:%M"),
                        "end": free_end.strftime("%H:%M")
                    })
            
            result.append({
                "doctor_id": doctor.doctor_id,
                "name": doctor.user.first_name + " " + doctor.user.last_name,
                "specialty": doctor.specialty.value,
                "date": date.strftime("%Y-%m-%d"),
                "day": weekday_name,
                "available_slots": available_slots,
                
            })
            
        return result
        """
        Private function to get doctor's real-time availability accounting for booked appointments
        
        Args:
            db_session: Database session
            name: Doctor's name (optional)
            date: Specific date to check (optional, defaults to today)
            
        Returns:
            List of doctors with their available time slots after accounting for bookings
        """
        from datetime import datetime, timedelta
        from sqlalchemy import and_, func
        from models.appointment import Appointment
        
        # Use today's date if not specified
        if not date:
            date = datetime.now().date()
        

        
        # Build query to get doctors
        query = db_session.query(Doctor).join(Doctor.user)
        if name:
            query = query.filter(Doctor.user.has(name=name))
        
        doctors = query.all()
        result = []
        
        for doctor in doctors:
            # Get working hours for this day
            working_hours = db_session.query(DoctorAvailability).filter(
                and_(
                    DoctorAvailability.doctor_id == doctor.doctor_id,
                    DoctorAvailability.day_of_week == weekday
                )
            ).all()
            
            # Get appointments for this doctor on the specified date
            appointments = db_session.query(Appointment).filter(
                and_(
                    Appointment.doctor_id == doctor.doctor_id,
                    func.date(Appointment.appointment_datetime) == date
                )
            ).order_by(Appointment.appointment_datetime).all()
            
            # Calculate available slots by removing booked times
            available_slots = []
            
            for work_slot in working_hours:
                # Convert time objects to datetime for easier manipulation
                start_dt = datetime.combine(date, work_slot.start_time)
                end_dt = datetime.combine(date, work_slot.end_time)
                
                # Start with the full slot available
                free_periods = [(start_dt, end_dt)]
                
                # Remove appointment times
                for appt in appointments:
                    appt_start = appt.appointment_datetime
                    appt_end = appt_start + timedelta(minutes=30)  # Assuming 30-min appointments
                    
                    # Check if appointment overlaps with this working slot
                    if appt_start.date() == date and appt_start.time() >= work_slot.start_time and appt_end.time() <= work_slot.end_time:
                        # Create new list of free times by removing this appointment
                        updated_free_periods = []
                        
                        for free_start, free_end in free_periods:
                            # Case 1: Appointment is completely within free period
                            if free_start < appt_start and free_end > appt_end:
                                updated_free_periods.append((free_start, appt_start))
                                updated_free_periods.append((appt_end, free_end))
                            # Case 2: Appointment starts during free period
                            elif free_start < appt_start <= free_end:
                                updated_free_periods.append((free_start, appt_start))
                            # Case 3: Appointment ends during free period
                            elif free_start <= appt_end < free_end:
                                updated_free_periods.append((appt_end, free_end))
                            # Case 4: No overlap with this free period
                            elif appt_end <= free_start or appt_start >= free_end:
                                updated_free_periods.append((free_start, free_end))
                        
                        free_periods = updated_free_periods
                
                # Add the free periods to our result
                for free_start, free_end in free_periods:
                    available_slots.append({
                        "start": free_start.strftime("%H:%M"),
                        "end": free_end.strftime("%H:%M")
                    })
            
            result.append({
                "doctor_id": doctor.doctor_id,
                "name": doctor.user.name,
                "specialty": doctor.specialty.value,
                "date": date.strftime("%Y-%m-%d"),
                "day": weekday.value,
                "available_slots": available_slots
            })
            
        return result