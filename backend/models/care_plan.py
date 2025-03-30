from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Text, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

class CarePlan(Base):
    __tablename__ = 'care_plans'
    
    care_plan_id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey('patients.patient_id'), nullable=False)
    created_by_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    assigned_nurse_id = Column(Integer, ForeignKey('users.user_id'))
    supervising_doctor_id = Column(Integer, ForeignKey('doctors.doctor_id'))
    description = Column(Text, nullable=False)
    goals = Column(Text)
    start_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    end_date = Column(DateTime)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    patient = relationship("Patient")
    created_by = relationship("User", foreign_keys=[created_by_id])
    assigned_nurse = relationship("User", foreign_keys=[assigned_nurse_id])
    supervising_doctor = relationship("Doctor", foreign_keys=[supervising_doctor_id])
    tasks = relationship("CarePlanTask", back_populates="care_plan", cascade="all, delete-orphan")
    updates = relationship("CarePlanUpdate", back_populates="care_plan", cascade="all, delete-orphan", 
                          order_by="desc(CarePlanUpdate.updated_at)")
    
    @property
    def daily_tasks(self):
        """Get tasks that should be performed daily"""
        return [task for task in self.tasks if task.frequency == 'daily']


class CarePlanTask(Base):
    __tablename__ = 'care_plan_tasks'
    
    task_id = Column(Integer, primary_key=True)
    care_plan_id = Column(Integer, ForeignKey('care_plans.care_plan_id'), nullable=False)
    description = Column(String, nullable=False)
    frequency = Column(String, default='daily')  # daily, weekly, monthly, as_needed
    priority = Column(String, default='normal')  # low, normal, high
    status = Column(String, default='pending')  # pending, completed, skipped
    scheduled_time = Column(DateTime)
    completed_at = Column(DateTime)
    completed_by_id = Column(Integer, ForeignKey('users.user_id'))
    notes = Column(Text)
    
    # Relationships
    care_plan = relationship("CarePlan", back_populates="tasks")
    completed_by = relationship("User")
    
    def should_perform_on_date(self, date):
        """Check if this task should be performed on the given date based on frequency"""
        if not self.scheduled_time:
            return True  # If no specific time, always show
            
        if self.frequency == 'daily':
            return True
        elif self.frequency == 'weekly':
            # If same day of week
            return self.scheduled_time.weekday() == date.weekday()
        elif self.frequency == 'monthly':
            # If same day of month
            return self.scheduled_time.day == date.day
        elif self.frequency == 'as_needed':
            return False  # Don't show as_needed tasks in regular schedule
        return False


class CarePlanUpdate(Base):
    __tablename__ = 'care_plan_updates'
    
    update_id = Column(Integer, primary_key=True)
    care_plan_id = Column(Integer, ForeignKey('care_plans.care_plan_id'), nullable=False)
    updated_by_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    notes = Column(Text)
    changes = Column(Text)  # JSON string describing changes
    
    # Relationships
    care_plan = relationship("CarePlan", back_populates="updates")
    updated_by = relationship("User")