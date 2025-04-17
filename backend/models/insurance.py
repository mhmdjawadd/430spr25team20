from sqlalchemy import  Column, Integer, String, ForeignKey, JSON, Boolean, Enum, Date, Text
from sqlalchemy.orm import relationship
import enum
from .base import * 

class InsuranceCoverage(enum.Enum):
    LIMITED = "Limited"       # Insurance A (20% for doctor visits only)
    STANDARD = "Standard"     # Insurance B (50% for therapists and general doctors)
    PREMIUM = "Premium"       # Insurance C (all-inclusive)
    NONE = "None"             # No insurance

class Insurance(Base):
    __tablename__ = 'insurance'
    
    patient_id = Column(Integer, ForeignKey('patients.patient_id'), primary_key=True)
    coverage_type = Column(Enum(InsuranceCoverage), nullable=False)
    provider_name = Column(String(100), nullable=True)  # Added provider name
    policy_number = Column(String(50), nullable=True)   # Added policy number
    group_number = Column(String(50), nullable=True)    # Added group number
    policy_holder_name = Column(String(100), nullable=True)  # Added policy holder name
    coverage_start_date = Column(Date, nullable=True)   # Added coverage start date
    coverage_end_date = Column(Date, nullable=True)     # Added coverage end date
    front_card_image = Column(Text, nullable=True)      # Base64 encoded image for front of card
    back_card_image = Column(Text, nullable=True)       # Base64 encoded image for back of card
        
    # Relationships - explicitly define foreign keys
    patient = relationship("Patient", back_populates="insurance", foreign_keys=[patient_id])
    
    def calculate_coverage(self,  doctor_specialty, base_cost):
        """
        Calculate the coverage amount based on insurance type and service
        
        Args:
service_type: Type of appointment/service
            doctor_specialty: Specialty of the doctor
            base_cost: The original cost of the service
            
        Returns:
            tuple: (covered_amount, patient_responsibility)
        """
        if self.coverage_type == InsuranceCoverage.LIMITED:
            # Insurance A: 20% coverage for doctor visits only
            if doctor_specialty == "doctor":
                covered_amount = base_cost * 0.2
            else:
                covered_amount = 0
                
        elif self.coverage_type == InsuranceCoverage.STANDARD:
            # Insurance B: 50% for therapists and general doctors
            if doctor_specialty in ["therapist", "doctor"]:
                covered_amount = base_cost * 0.5
            else:
                covered_amount = 0
                
        elif self.coverage_type == InsuranceCoverage.PREMIUM:
            # Insurance C: All-inclusive (80% coverage for everything)
            covered_amount = base_cost * 0.8
            
        else:
            covered_amount = 0
            
        patient_responsibility = base_cost - covered_amount
        return (covered_amount, patient_responsibility)

