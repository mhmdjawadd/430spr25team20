# c:\\Users\\User\\Desktop\\430 Nabad\\register_doctors.py
import requests
import json

# --- Configuration ---
BASE_URL = "http://localhost:5000"  # Adjust if your backend runs elsewhere
SIGNUP_ENDPOINT = "/signup"         # Adjust if your signup route is different
# -------------------

doctors_to_register = [
    {
        "email": "doc@gmail.com",
        "password": "password123",
        "first_name": "James",
        "last_name": "Willson",
        "role": "DOCTOR",
        "specialty": "DOCTOR", # General Doctor
        "phone": "111-222-3333"
    },
        {
        "email": "patient@gmail.com",
        "password": "password123",
        "first_name": "Mohammad Jawad",
        "last_name": "Willson",
        "role": "PATIENT",
        "phone": "111-222-3333"
    },
     

    {
        "email": "dr.therapist@.com",
        "password": "password123",
        "first_name": "Sarah",
        "last_name": "Johnson",
        "role": "THERAPIST",
        "specialty": "THERAPIST", # Therapist
        "phone": "444-555-6666"
    },
    {
        "email": "dr.surgeon@gmail.com",
        "password": "password123",
        "first_name": "Michael",
        "last_name": "Chen",
        "role": "SURGEON",
        "specialty": "SURGEON", # Surgeon
        "phone": "777-888-9999"
    },
     {
        "email": "dr.cardio@nabad.com",
        "password": "password123",
        "first_name": "Emily",
        "last_name": "Martinez",
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
