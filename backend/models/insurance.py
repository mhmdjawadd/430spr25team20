from sqlalchemy import  Column, Integer, String, ForeignKey, JSON, Boolean , Enum
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
        
    # Relationships
    patient = relationship("Patient", back_populates="insurance")
    
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

