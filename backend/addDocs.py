# c:\\Users\\User\\Desktop\\430 Nabad\\register_doctors.py
import requests
import json

# --- Configuration ---
BASE_URL = "http://localhost:5000"  # Adjust if your backend runs elsewhere
SIGNUP_ENDPOINT = "/signup"         # Adjust if your signup route is different
# -------------------

doctors_to_register = [
    {
        "email": "dr.general@nabad.com",
        "password": "password123",
        "first_name": "General",
        "last_name": "Practitioner",
        "role": "DOCTOR",
        "specialty": "DOCTOR", # General Doctor
        "phone": "111-222-3333"
    },
    {
        "email": "dr.therapist@nabad.com",
        "password": "password123",
        "first_name": "Mental",
        "last_name": "Wellness",
        "role": "THERAPIST",
        "specialty": "THERAPIST", # Therapist
        "phone": "444-555-6666"
    },
    {
        "email": "dr.surgeon@nabad.com",
        "password": "password123",
        "first_name": "Skilled",
        "last_name": "Hands",
        "role": "SURGEON",
        "specialty": "SURGEON", # Surgeon
        "phone": "777-888-9999"
    },
     {
        "email": "dr.cardio@nabad.com",
        "password": "password123",
        "first_name": "Cardio",
        "last_name": "Expert",
        "role": "DOCTOR",
        "specialty": "DOCTOR", # Another Doctor, could be specialized if needed
        "phone": "123-456-7890"
    }
]

def register_doctor(doctor_data):
    """Sends a POST request to register a single doctor."""
    url = BASE_URL + SIGNUP_ENDPOINT
    headers = {'Content-Type': 'application/json'}
    try:
        response = requests.post(url, headers=headers, data=json.dumps(doctor_data))
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        print(f"Successfully registered {doctor_data['email']}. Response: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"Error registering {doctor_data['email']}: {e}")
        if e.response is not None:
            try:
                print(f"Server response: {e.response.json()}")
            except json.JSONDecodeError:
                print(f"Server response (non-JSON): {e.response.text}")

if __name__ == "__main__":
    print("Starting doctor registration...")
    for doctor in doctors_to_register:
        register_doctor(doctor)
    print("Doctor registration script finished.")
