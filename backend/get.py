from app import db
from models.doctor import Doctor

def get_all_doctors():
    """
    Retrieves all doctors from the database
    """
    try:
        # If using an ORM like SQLAlchemy
        doctors = Doctor.query.all()
        # Alternatively, if using direct database queries:
        # doctors = db.execute("SELECT * FROM doctors").fetchall()
        return doctors
    except Exception as e:
        print(f"Error retrieving doctors: {e}")
        return []


if __name__ == "__main__":
    doctors = get_all_doctors()
    if doctors:
        for doctor in doctors:
            print(doctor)
    else:
        print("No doctors found or error occurred.")