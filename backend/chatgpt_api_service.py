from typing import Dict, List, Optional
import json
import requests
from sqlalchemy.orm import Session
import logging

class ChatGPTAPIService:
    def __init__(self, api_key: str, user_id: int, db: Session = None):
        self.api_key = api_key
        self.user_id = user_id
        self.db = db
        self.base_url = "https://api.openai.com/v1/chat/completions"
        self.logger = logging.getLogger(__name__)
        

    def _send_to_api(self, wanted_prompt: str) -> Dict:
        """Send text with specific command to OpenAI API
        Args:
            text (str): Text to send to the API where it is processed by FileProcessorService at app level
            wanted_prompt (str): custom prompt to send to the API
        Returns:
            Dict: Response from the API
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            prompt = f"{wanted_prompt}\n\n"
            
            system_prompt = (
                "You are a medical assistant AI. Your task is to analyze the patient's query and " \
                "help them "
            )

            payload = {
                        "model": "gpt-4o",
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": prompt}
                        ],
                        "response_format": "json_object"
                    }


            response = requests.post(self.base_url, headers=headers, json=payload)
            response.raise_for_status()
            
            return {
                "status": "success",
                "response": response.json()
            }

        except requests.exceptions.RequestException as e:
            self.logger.error(f"API request failed: {str(e)}")
            return {"status": "error", "message": f"API request failed: {str(e)}"}
    
    def get_response_content(self, response_data: Dict) -> str:
        """Extract the content from the API response"""
        try:
            if response_data["status"] == "success":
                return response_data["response"]["choices"][0]["message"]["content"]
            return ""
        except KeyError as e:
            self.logger.error(f"Error extracting content: {str(e)}")
            return ""
    
    def recommend_doctor(self, patient_query: str) -> Dict:
        """
        Analyze patient query and recommend the most suitable doctor
        
        Args:
            patient_query (str): Patient's description of symptoms or medical needs
            
        Returns:
            Dict: Response containing recommended doctor information
        """
        try:
            if not self.db:
                return {"status": "error", "message": "Database session not available"}
            
            # Get all doctors from the database
            doctor_data = self.get_doctors_from_db()
            
            if not doctor_data or len(doctor_data) == 0:
                return {"status": "error", "message": "No doctors found in database"}
            
            # Format doctor data for AI analysis
            
            
            # Create prompt for GPT to analyze and recommend
            prompt = (
                "Based on the patient's query and the available doctors, recommend the most suitable doctor. "
                "Consider the doctor's specialty, expertise, and experience in relation to the patient's needs. "
                "Provide a brief explanation for your recommendation.\n\n"
                "Respond in the following JSON format:\n"
                "{\n"
                "  \"recommended_doctor\": \"Doctor Name\",\n"
                "  \"reason\": \"Reason for recommendation\",\n"
                "  \"doctor_id\": \"Doctor ID\"\n"
                "}\n\n"
                f"Patient Query: {patient_query}\n\n"
                f"Available Doctors:\n{doctor_data}"
            )

            
            # Send to GPT for recommendation
            response = self._send_to_api(prompt)
            
            if response["status"] == "success":
                
                content = response["response"]["choices"][0]["message"]["content"]
            try:
                recommendation = json.loads(content)
                return {
                    "status": "success",
                    "recommendation": recommendation
                }
            except json.JSONDecodeError as e:
                self.logger.error(f"JSON parsing failed: {str(e)}")
                return {"status": "error", "message": "Failed to parse JSON response from API"}
        
            
        except Exception as e:
            self.logger.error(f"Error recommending doctor: {str(e)}")
            return {"status": "error", "message": f"Failed to recommend doctor: {str(e)}"}
    
    def get_doctors_from_db(self) -> List[Dict]:
        """
        Retrieve all doctors and their information from the database
        
        Returns:
            List[Dict]: List of doctor information dictionaries
        """
        try:
            from models.doctor import Doctor
            from models.user import User
            
            # Query to get doctors with user information
            doctors = self.db.query(Doctor).join(Doctor.user).all()
            
            result = []
            for doctor in doctors:
                doctor_info = {
                    "doctor_id": doctor.doctor_id,
                    "full_name": f"{doctor.user.first_name} {doctor.user.last_name}",
                    "specialty": str(doctor.specialty),
                    "description": doctor.description,
                }
                result.append(doctor_info)
                
            return result
            
        except Exception as e:
            self.logger.error(f"Error retrieving doctors from database: {str(e)}")
            return []
    
    
        
   