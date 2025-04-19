from typing import Dict, List, Optional
import json
import requests
from sqlalchemy.orm import Session
import logging
from datetime import datetime
import re
from models import AppointmentType

class ChatGPTAPIService:
    def __init__(self, api_key: str , db):
        self.api_key = api_key
        self.db = db
        self.base_url = "https://api.openai.com/v1/chat/completions"

        self.logger = logging.getLogger(__name__)
        self.BASE_URL = "http://localhost:5000"

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
                        ]
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
            return(response)
            if response["status"] == "success":
                content = response["response"]["choices"][0]["message"]["content"]
                return content
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
            from sqlalchemy.orm import Session
            
            # Query to get doctors with user information
            # Use the session from the db instance instead of calling the db module directly
            doctors = self.db.session.query(Doctor).join(Doctor.user).all()
            
            result = []
            for doctor in doctors:
                doctor_info = {
                    "doctor_id": doctor.doctor_id,
                    "full_name": f"{doctor.user.first_name} {doctor.user.last_name}",
                    "specialty": str(doctor.specialty),
                    "description": doctor.description if hasattr(doctor, 'description') else "",
                }
                result.append(doctor_info)
                
            formatted_doctors = self.format_doctor_data(result)
            return formatted_doctors
            
        except Exception as e:
            self.logger.error(f"Error retrieving doctors from database: {str(e)}")
            return []
    
    def format_doctor_data(self, doctor_data: List[Dict]) -> str:
        """
        Format doctor data for inclusion in the prompt to GPT
        
        Args:
            doctor_data (List[Dict]): List of doctor information
            
        Returns:
            str: Formatted string of doctor information
        """
        formatted_data = ""
        
        for i, doctor in enumerate(doctor_data, 1):
            formatted_data += f"{i}. Dr. {doctor['full_name']}\n"
            formatted_data += f"   ID: {doctor['doctor_id']}\n"
            formatted_data += f"   Specialty: {doctor['specialty']}\n"
            if doctor.get('description'):
                formatted_data += f"   Description: {doctor['description']}\n"
            formatted_data += "\n"
            
        return formatted_data
    
    def book_appointment_ai(self, patient_query:str, token:str ) ->Dict:
        """
        Book an appointment with a doctor based on the patient's query
        
        Args:
            patient_query (str): Patient's description of symptoms or medical needs
            
        Returns:
            Dict: Response containing appointment booking information
        """
        try:
            # Get all doctors from the database
            doctor_data = self.get_doctors_from_db()
            
            if not doctor_data or len(doctor_data) == 0:
                return {"status": "error", "message": "No doctors found in database"}
                        
            today = datetime.now().date()
            
            # Create prompt for GPT to analyze and book appointment
            prompt = (
                "Based on the patient's query and the available doctors, book an appointment with the most suitable doctor. "
                "Consider the doctor's specialty, expertise, and experience in relation to the patient's needs. "
                "Provide a brief explanation for your recommendation.\n\n"
                f"please know that todays date is {today}"
                "please just reposnd with the following  : "
                "also note to let the appointment_datetime to be yyyy-mm-dd-hh"
                "doctor_id=doctor.doctor_id"
                "date_time=appointment_datetime,"
                "please return both of them in 'doctor_id' : the id of doctor  and 'date_time':appointment_datetime  format\n\n"
                
                f"Patient Query: {patient_query}\n\n"
                f"Available Doctors:\n{doctor_data}"
            )

            # Send to GPT for booking appointment
            
            response = self._send_to_api(prompt)
            
            if response["status"] == "success":
                
                content = response["response"]["choices"][0]["message"]["content"]
                doctor_data = json.loads(re.sub(r"```json|```", "", content).strip())
                
                
            try:
                
                
                """Sends a POST request to register to a single doctor."""
                url = self.BASE_URL + "/appointments"

                headers = {'Content-Type': 'application/json' , 'Authorization': f'Bearer {token}'}
                try:
                    
                    doctor_data ["appointment_type"]= "REGULAR"
                    doctor_data ["verify_insurance"]= True
                    doctor_data ["notes"]= "Booked with AI assistance"
                    doctor_data ["recurrence_pattern"]= "NONE"
                    doctor_data ["recurrence_count"]= 3
                                
                            
                    data = json.dumps(doctor_data)
                    response = requests.post(url, headers=headers, data = data) 
                    if response.status_code == 409:
                        return {"status": "error", "message": "Appointment already in this time exists"}
                    elif response.status_code == 201:
                        return {"status": "success", "message": "Appointment booked successfully"}
                except requests.exceptions.RequestException as e:
                    self.logger.error(f"API request failed: {str(e)}")
                    return {"status": "error", "message": f"API request failed: {str(e)}"}
                
            except json.JSONDecodeError as e:
                self.logger.error(f"JSON parsing failed: {str(e)}")
                return {"status": "error", "message": "Failed to parse JSON response from API"}
        
        except Exception as e:
            self.logger.error(f"Error booking appointment: {str(e)}")
            return {"status": "error", "message": f"Failed to book appointment: {str(e)}"}

    def cancel_appointment_ai(self, patient_query: str, token:str) :
        """
        Cancel an appointment based on the appointment ID
        
        Args:
            appointment_id (int): ID of the appointment to cancel
            
        Returns:
            Dict: Response containing appointment cancellation information

        """

        try:
            url = self.BASE_URL + "/appointments/patient"

            headers = {'Content-Type': 'application/json' , 'Authorization': f'Bearer {token}'}

            appointments =  requests.get(url, headers=headers)
            appointments = appointments.json()
            appointments = [appt for appt in appointments if appt["status"] == "UPCOMING"]
            
            today = datetime.now().date()
            # Create prompt for GPT to analyze and cancel appointment
            prompt = (
                "Based on the patient's request, cancel the specified appointment. "
                f"the patients query is: {patient_query}\n\n"
                f"Available Appointments:\n{appointments}"
                "please return the id of the appointment to be cancelled in int value in json, i just want the appointment_id as in appointment_id : (actual id )\n"
                f"note that todays date is {today}"
            )

            # Send to GPT for cancellation
            response = self._send_to_api(prompt)
           
            if response["status"] == "success":
                content = response["response"]["choices"][0]["message"]["content"]
                
            else:
                return response   
            
            try:
                url = self.BASE_URL + "/appointments/cancel"

                headers = {'Content-Type': 'application/json' , 'Authorization': f'Bearer {token}'}
                
                match = re.search(r'"appointment_id"\s*:\s*(\d+)', content)

                if match:
                    appointment_id = int(match.group(1))
                   
                appointment_id = int(appointment_id)
                
                data = json.dumps({"appointment_id": appointment_id})
                response = requests.put(url, headers=headers, data=data)

                return {"status": "success", "message": "Appointment cancelled successfully"}
            except json.JSONDecodeError as e:
                self.logger.error(f"JSON parsing failed: {str(e)}")
                return {"status": "error", "message": "Failed to parse JSON response from API"}
        
        except Exception as e:
            self.logger.error(f"Error cancelling appointment: {str(e)}")
            return {"status": "error", "message": f"Failed to cancel appointment: {str(e)}"}
        
    def reschdule_appointment_ai(self , patient_query:str, token:str) ->Dict:
        """
        Reschedule an appointment based on the appointment ID
        
        Args:
            appointment_id (int): ID of the appointment to reschedule
            
        Returns:
            Dict: Response containing appointment rescheduling information

        """
        try:
            url = self.BASE_URL + "/appointments/patient"

            headers = {'Content-Type': 'application/json' , 'Authorization': f'Bearer {token}'}

            appointments =  requests.get(url, headers=headers)
            appointments = appointments.json()
            appointments = [appt for appt in appointments if appt["status"] == "UPCOMING"]
            
            today = datetime.now().date()
            # Create prompt for GPT to analyze and cancel appointment
            prompt = (
                "Based on the patient's request, cancel the specified appointment. "
                f"the patients query is: {patient_query}\n\n"
                f"Available Appointments:\n{appointments}"
                "please return the id of the appointment and the date in yyyy-mm-dd-hh to be cancelled in int value in json, \n"
                "i just want the appointment_id and new date to be rescheduled as in appointment_id : (actual id ) ,new_date_time = (actual new date in yyyy-mm-dd-hh)\n"
                f"note that todays date is {today}"
            )

            # Send to GPT for cancellation
            response = self._send_to_api(prompt)
           
            if response["status"] == "success":
                content = response["response"]["choices"][0]["message"]["content"]
                
            else:
                return response   
            
            try:
                url = self.BASE_URL + "/appointments/reschedule"

                headers = {'Content-Type': 'application/json' , 'Authorization': f'Bearer {token}'}

                
                match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
                if match:
                    json_str = match.group(1)
                json_str = json.loads(json_str)
                json_str["reason"]= "Rescheduled with AI assistance"
                data = json.dumps(json_str)
                
                response = requests.put(url, headers=headers, data=data)

                return {"status": "success", "message": "Appointment reschudeled successfully"}
            except json.JSONDecodeError as e:
                self.logger.error(f"JSON parsing failed: {str(e)}")
                return {"status": "error", "message": "Failed to parse JSON response from API"}
        
        except Exception as e:
            self.logger.error(f"Error cancelling appointment: {str(e)}")
            return {"status": "error", "message": f"Failed to cancel appointment: {str(e)}"}
        

    def recommend_doctor_ai(self, patient_query: str, token: str) -> Dict:
            """
            Recommend a doctor based on patient's query by analyzing all doctor specialties and descriptions
            
            Args:
                patient_query (str): Patient's description of symptoms or medical needs
                token (str): Authentication token for API requests
                
            Returns:
                Dict: Response containing recommended doctor information
            """
            try:
                # Get all doctors from the database
                doctor_data = self.get_doctors_from_db()
                
                if not doctor_data or len(doctor_data) == 0:
                    return {"status": "error", "message": "No doctors found in database"}
                
                today = datetime.now().date()
                
                # Create prompt for GPT to analyze doctor profiles and recommend based on patient query
                prompt = (
                    "You are a medical assistant AI. Based on the patient's query and the available doctors' "
                    "specialties and descriptions, recommend the most suitable doctor for this patient's needs. "
                    "Consider the doctor's specialty, expertise, and how it relates to the patient's condition. "
                    "Provide a brief explanation for your recommendation.\n\n"
                    f"Today's date is {today}\n\n"
                    f"Patient Query: {patient_query}\n\n"
                    f"Available Doctors:\n{doctor_data}\n\n"
                    "Please respond with a JSON object in the following format:\n"
                    "{\n"
                    '  "doctor_id": 123,\n'
                    '  "doctor_name": "Dr. Full Name",\n'
                    '  "reason": "Brief explanation of why this doctor is the best match"\n'
                    "}"
                )
        
                # Send to GPT for doctor recommendation
                response = self._send_to_api(prompt)
                
                if response["status"] == "success":
                    content = response["response"]["choices"][0]["message"]["content"]
                    
                    # Clean up the response to extract the JSON
                    content = re.sub(r"```json|```", "", content).strip()
                    
                    try:
                        recommendation = json.loads(content)
                        
                        # Validate that recommendation contains required fields
                        required_fields = ["doctor_id", "doctor_name", "reason"]
                        for field in required_fields:
                            if field not in recommendation:
                                return {
                                    "status": "error", 
                                    "message": f"AI response missing required field: {field}",
                                    "raw_response": content
                                }
                        
                        # Fetch more information about the recommended doctor
                        doctor_details = self.get_doctor_details(recommendation["doctor_id"], token)
                        
                        if doctor_details["status"] == "success":
                            # Combine AI recommendation with doctor details
                            result = {
                                "status": "success",
                                "recommendation": {
                                    "doctor_id": recommendation["doctor_id"],
                                    "doctor_name": recommendation["doctor_name"],
                                    "reason": recommendation["reason"],
                                    "details": doctor_details["data"]
                                }
                            }
                            return result
                        else:
                            # Return just the basic recommendation if we can't get details
                            return {
                                "status": "success",
                                "recommendation": recommendation
                            }
                            
                    except json.JSONDecodeError as e:
                        self.logger.error(f"JSON parsing failed: {str(e)}")
                        return {"status": "error", "message": "Failed to parse AI response as JSON", "raw_response": content}
                else:
                    return response
            
            except Exception as e:
                self.logger.error(f"Error recommending doctor: {str(e)}")
                return {"status": "error", "message": f"Failed to recommend doctor: {str(e)}"}
        
    def get_doctor_details(self, doctor_id: int, token: str) -> Dict:
            """
            Get detailed information about a specific doctor
            
            Args:
                doctor_id (int): ID of the doctor
                token (str): Authentication token
                
            Returns:
                Dict: Doctor details
            """
            url = f"{self.BASE_URL}/doctors/{doctor_id}"
            headers = {'Authorization': f'Bearer {token}'}
            
            try:
                response = requests.get(url, headers=headers)
                
                if response.status_code == 200:
                    return {"status": "success", "data": response.json()}
                else:
                    self.logger.error(f"Failed to get doctor details: {response.status_code}")
                    return {"status": "error", "message": f"Failed to get doctor details: {response.status_code}"}
            except requests.exceptions.RequestException as e:
                self.logger.error(f"API request failed: {str(e)}")
                return {"status": "error", "message": f"API request failed: {str(e)}"}