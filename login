<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - Mediplus</title>
    <style>
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Poppins', sans-serif;
        }

        body {
            background: #f5f6fa;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }

        .login-container {
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
            width: 400px;
        }

        .logo {
            text-align: center;
            margin-bottom: 30px;
        }

        .logo img {
            width: 200px;
        }

        h2 {
            color: #2C3E50;
            margin-bottom: 30px;
            text-align: center;
            font-size: 24px;
        }

        .form-group {
            margin-bottom: 20px;
        }

        .form-group label {
            display: block;
            margin-bottom: 8px;
            color: #2C3E50;
            font-weight: 500;
        }

        .form-group select,
        .form-group input {
            width: 100%;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }

        .form-group select {
            background: white;
        }

        .login-btn {
            width: 100%;
            padding: 12px;
            background: #1A76D1;
            color: white;
            border: none;
            border-radius: 4px;
            font-size: 16px;
            cursor: pointer;
            margin-top: 20px;
        }

        .login-btn:hover {
            background: #1557a0;
        }

        .forgot-password {
            text-align: center;
            margin-top: 20px;
        }

        .forgot-password a {
            color: #1A76D1;
            text-decoration: none;
        }

        .register-link {
            text-align: center;
            margin-top: 20px;
            color: #666;
        }

        .register-link a {
            color: #1A76D1;
            text-decoration: none;
            font-weight: 500;
        }

        .nurse-card {
            background: #f0f7ff;
            border-left: 4px solid #3498db;
        }

        .role-nurse {
            color: #3498db;
            background: rgba(52, 152, 219, 0.1);
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
        }

        .modal {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            display: none;
            justify-content: center;
            align-items: center;
            z-index: 1000;
        }

        .modal-content {
            background: white;
            border-radius: 12px;
            width: 500px;
            max-width: 90%;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        }

        .modal-header {
            padding: 20px;
            border-bottom: 1px solid #eee;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .modal-header h3 {
            margin: 0;
            color: #333;
        }

        .modal-body {
            padding: 20px;
        }

        .modal-footer {
            padding: 20px;
            border-top: 1px solid #eee;
            display: flex;
            justify-content: flex-end;
            gap: 10px;
        }

        .close-btn {
            background: none;
            border: none;
            font-size: 24px;
            cursor: pointer;
            color: #666;
        }

        .form-group {
            margin-bottom: 15px;
        }

        .form-group label {
            display: block;
            margin-bottom: 5px;
            color: #333;
            font-weight: 500;
        }

        .form-group input,
        .form-group select,
        .form-group textarea {
            width: 100%;
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 6px;
            font-size: 14px;
        }

        .form-group textarea {
            resize: vertical;
        }

        .btn-primary {
            background: #0066cc;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
        }

        .btn-secondary {
            background: #f8f9fa;
            color: #333;
            border: 1px solid #ddd;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="logo">
            <img src="img/nabad.png" alt="Mediplus">
        </div>
        
        <h2>Welcome Back</h2>
        
        <form onsubmit="handleLogin(event)">
            <div class="form-group">
                <label for="role">Role</label>
                <select name="role" id="role" required>
                    <option value="">Select Role</option>
                    <option value="patient">Patient</option>
                    <option value="doctor">Doctor</option>
                    <option value="nurse">Nurse</option>
                    <option value="receptionist">Receptionist</option>
                    <option value="admin">Admin</option>
                </select>
            </div>

            <div class="form-group">
                <label>Healthcare Provider</label>
                <div class="input-with-icon">
                    <i class="fas fa-user-md"></i>
                    <select id="providerSelect" required>
                        <option value="">Select Provider</option>
                        <optgroup label="Doctors">
                            <option value="dr-smith">Dr. Smith - Surgery</option>
                            <option value="dr-johnson">Dr. Johnson - Cardiology</option>
                            <option value="dr-williams">Dr. Williams - Pediatrics</option>
                        </optgroup>
                        <optgroup label="Nurses">
                            <option value="nurse-brown">Nurse Brown - General Care</option>
                            <option value="nurse-davis">Nurse Davis - Pediatrics</option>
                            <option value="nurse-wilson">Nurse Wilson - Emergency</option>
                        </optgroup>
                    </select>
                </div>
            </div>

            <div class="form-group">
                <label>Email</label>
                <input type="email" required>
            </div>

            <div class="form-group">
                <label>Password</label>
                <input type="password" required>
            </div>

            <button type="submit" class="login-btn">Log In</button>
        </form>

        <div class="forgot-password">
            <a href="forgot-password.html">Forgot Password?</a>
        </div>

        <div class="register-link">
            Don't have an account? <a href="register.html">Register Now</a>
        </div>
    </div>

    <div class="modal" id="appointmentModal" style="display: none;">
        <div class="modal-content">
            <div class="modal-header">
                <h3>Schedule New Appointment</h3>
                <button class="close-btn" onclick="closeAppointmentModal()">&times;</button>
            </div>
            <div class="modal-body">
                <form id="appointmentForm">
                    <div class="form-group">
                        <label>Patient Name</label>
                        <input type="text" id="patientName" required>
                    </div>

                    <div class="form-group">
                        <label>Appointment Type</label>
                        <select id="appointmentType" required>
                            <option value="">Select Type</option>
                            <option value="Follow-up">Follow-up</option>
                            <option value="Consultation">Consultation</option>
                            <option value="New Patient">New Patient</option>
                            <option value="Emergency">Emergency</option>
                        </select>
                    </div>

                    <div class="form-group">
                        <label>Date</label>
                        <input type="date" id="appointmentDate" required>
                    </div>

                    <div class="form-group">
                        <label>Time</label>
                        <input type="time" id="appointmentTime" required>
                    </div>

                    <div class="form-group">
                        <label>Notes</label>
                        <textarea id="appointmentNotes" rows="3"></textarea>
                    </div>
                </form>
            </div>
            <div class="modal-footer">
                <button class="btn-secondary" onclick="closeAppointmentModal()">Cancel</button>
                <button class="btn-primary" onclick="saveAppointment()">Schedule</button>
            </div>
        </div>
    </div>

    <script>
        function handleLogin(event) {
            event.preventDefault();
            
            const role = document.getElementById('role').value;
            
            
            switch(role) {
                case 'doctor':
                    window.location.href = 'doctor-dashboard.html';
                    break;
                case 'patient':
                    window.location.href = 'index.html';
                    break;
                case 'nurse':
                    window.location.href = 'nurse-dashboard.html';
                    break;
                case 'receptionist':
                    window.location.href = 'receptionist-dashboard.html';
                    break;
                case 'admin':
                    window.location.href = 'manager-dashboard.html';
                    break;
                default:
                    alert('Please select a role');
            }
        }

        document.getElementById('userRole').addEventListener('change', function() {
            const nurseFields = document.querySelector('.nurse-fields');
            if (this.value === 'nurse') {
                nurseFields.style.display = 'block';
            } else {
                nurseFields.style.display = 'none';
            }
        });

        function createUser(formData) {
            const role = formData.get('userRole');
            let userData = {
                name: formData.get('fullName'),
                role: role,
                email: formData.get('email'),
            
            };

            if (role === 'nurse') {
                userData = {
                    ...userData,
                    department: formData.get('nurseDepartment'),
                    shift: formData.get('nurseShift'),
                    specialization: formData.get('nurseSpecialization'),
                    licenseNumber: formData.get('licenseNumber')
                };
            }

            
            addUserToSystem(userData);
            updateUsersList();
            showNotification('User created successfully');
        }

        
        function showAppointmentModal() {
            const modal = document.getElementById('appointmentModal');
            modal.style.display = 'flex';
            
           
            const today = new Date().toISOString().split('T')[0];
            document.getElementById('appointmentDate').value = today;
        }

       
        function closeAppointmentModal() {
            const modal = document.getElementById('appointmentModal');
            modal.style.display = 'none';
        }

     
        function saveAppointment() {
            const patientName = document.getElementById('patientName').value;
            const appointmentType = document.getElementById('appointmentType').value;
            const appointmentDate = document.getElementById('appointmentDate').value;
            const appointmentTime = document.getElementById('appointmentTime').value;
            const appointmentNotes = document.getElementById('appointmentNotes').value;

            if (!patientName || !appointmentType || !appointmentDate || !appointmentTime) {
                alert('Please fill in all required fields');
                return;
            }

       
            const eventData = {
                title: `${patientName} - ${appointmentType}`,
                start: `${appointmentDate}T${appointmentTime}`,
                end: addHours(`${appointmentDate}T${appointmentTime}`, 1),
                extendedProps: {
                    patient: patientName,
                    type: appointmentType,
                    notes: appointmentNotes
                }
            };

            
            calendar.addEvent(eventData);

        
            addToUpcomingPatients(eventData);

            
            showNotification('Appointment scheduled successfully');

            
            closeAppointmentModal();
        }

        
        function addToUpcomingPatients(appointment) {
            const patientList = document.querySelector('.patient-list');
            const patientItem = document.createElement('div');
            patientItem.className = 'patient-item';
            patientItem.innerHTML = `
                <div class="patient-info">
                    <div class="patient-name">${appointment.extendedProps.patient}</div>
                    <div class="patient-details">
                        ${formatTime(appointment.start)} - ${appointment.extendedProps.type}
                    </div>
                </div>
                <button class="action-btn btn-secondary" onclick="viewAppointment('${appointment.id}')">View</button>
            `;
            patientList.appendChild(patientItem);
        }

        
        function formatTime(dateTime) {
            return new Date(dateTime).toLocaleTimeString('en-US', {
                hour: '2-digit',
                minute: '2-digit'
            });
        }

       
        document.querySelector('.btn-primary').addEventListener('click', showAppointmentModal);

        window.onclick = function(event) {
            const modal = document.getElementById('appointmentModal');
            if (event.target === modal) {
                closeAppointmentModal();
            }
        }
    </script>
</body>
</html> 
