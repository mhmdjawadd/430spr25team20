// JavaScript for patient dashboard

document.addEventListener('DOMContentLoaded', function() {
    console.log('Patient dashboard loading...');
    // Initialize the dashboard
    initializeDashboard();
    
    // Setup appointment actions
    setupAppointmentActions();
    
    // Fetch user appointments for the dashboard
    console.log('Fetching appointments for dashboard...');
    fetchDashboardAppointments();
    
    // Initialize notifications
    initializeNotifications();
    
    // Initialize health metrics
    initializeHealthMetrics();
});

/**
 * Fetch upcoming appointments for the dashboard
 */
async function fetchDashboardAppointments() {
    try {
        console.log('Starting appointment fetch operation');
        // Get auth token from localStorage
        const token = localStorage.getItem('token');
        if (!token) {
            console.error('No authentication token found in localStorage');
            showDashboardMessage('Please log in to view your appointments', 'error');
            return;
        }
        
        console.log('Authentication token found, making API request');
        
        // Fetch appointments from the backend
        const response = await fetch('http://localhost:5000/appointments/patient', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        console.log('API response received:', response.status, response.statusText);
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('Error response from server:', errorText);
            throw new Error(`Failed to fetch appointments: ${response.status} - ${errorText}`);
        }
        
        const appointments = await response.json();
        console.log('Appointments data received:', appointments);
        
        if (appointments && appointments.length > 0) {
            console.log(`Found ${appointments.length} appointments`);
        } else {
            console.log('No appointments found for this user');
        }
        
        displayDashboardAppointments(appointments);
        
        // Update appointment stats
        updateDashboardStats(appointments);
    } catch (error) {
        console.error('Error in fetchDashboardAppointments:', error);
        const appointmentsList = document.getElementById('upcomingAppointmentsList');
        if (appointmentsList) {
            appointmentsList.innerHTML = `<div class="error-message">Failed to load appointments: ${error.message}</div>`;
        }
    }
}

/**
 * Display upcoming appointments on the dashboard
 */
function displayDashboardAppointments(appointments) {
    console.log('Displaying appointments on dashboard');
    const appointmentsList = document.getElementById('upcomingAppointmentsList');
    if (!appointmentsList) {
        console.error('Cannot find upcomingAppointmentsList element in the DOM');
        return;
    }
    
    // Clear the container
    appointmentsList.innerHTML = '';
    
    if (!appointments || appointments.length === 0) {
        console.log('No appointments to display');
        appointmentsList.innerHTML = '<div class="no-appointments">No upcoming appointments.</div>';
        return;
    }
    
    // Filter to only upcoming appointments and sort by date
    const upcomingAppointments = appointments
        .filter(appointment => {
            const isUpcoming = new Date(appointment.date_time) > new Date() && 
                  (!appointment.status || !appointment.status.includes('CANCEL'));
            console.log(`Appointment ${appointment.appointment_id}: isUpcoming=${isUpcoming}`);
            return isUpcoming;
        })
        .sort((a, b) => new Date(a.date_time) - new Date(b.date_time));
    
    console.log(`Found ${upcomingAppointments.length} upcoming appointments to display`);
    
    // Show only the first 3 upcoming appointments
    const appointmentsToShow = upcomingAppointments.slice(0, 3);
    
    if (appointmentsToShow.length === 0) {
        appointmentsList.innerHTML = '<div class="no-appointments">No upcoming appointments.</div>';
        return;
    }
    
    // Create appointment cards for each appointment
    appointmentsToShow.forEach(appointment => {
        console.log(`Creating card for appointment ID ${appointment.appointment_id}`);
        const appointmentDate = new Date(appointment.date_time);
        
        const appointmentCard = document.createElement('div');
        appointmentCard.className = 'appointment-card';
        appointmentCard.dataset.id = appointment.appointment_id;
        
        appointmentCard.innerHTML = `
            <div class="appointment-info">
                <img src="${getDoctorImage(appointment.doctor_specialty || 'general')}" alt="Doctor Image">
                <div class="appointment-details">
                    <h4>${appointment.doctor_name || 'Dr. Unknown'}</h4>
                    <p>${appointment.doctor_specialty || 'General Medicine'}</p>
                    <div class="appointment-time">
                        <i class="fas fa-calendar"></i>
                        <span>${formatDate(appointmentDate)}</span>
                        <i class="fas fa-clock"></i>
                        <span>${formatTime(appointmentDate)}</span>
                    </div>
                </div>
            </div>
            <div class="appointment-actions">
                <button class="btn-reschedule">Reschedule</button>
                <button class="btn-cancel">Cancel</button>
            </div>
        `;
        
        appointmentsList.appendChild(appointmentCard);
    });
    
    // If there are more appointments that we're not showing
    if (upcomingAppointments.length > appointmentsToShow.length) {
        console.log(`${upcomingAppointments.length - appointmentsToShow.length} more appointments not shown`);
        const moreAppointmentsNote = document.createElement('div');
        moreAppointmentsNote.className = 'more-appointments-note';
        moreAppointmentsNote.innerHTML = `
            <p>+ ${upcomingAppointments.length - appointmentsToShow.length} more appointment(s). <a href="patient_appointments.html">View all</a></p>
        `;
        appointmentsList.appendChild(moreAppointmentsNote);
    }
    
    console.log('Appointment display complete');
    
    // After adding all appointments to the DOM, re-setup the event listeners
    setupAppointmentActions();
}

/**
 * Update stats on the dashboard based on appointments
 */
function updateDashboardStats(appointments) {
    if (!appointments) return;
    
    // Count upcoming appointments
    const upcomingAppointments = appointments.filter(appt => 
        new Date(appt.date_time) > new Date() && !appt.status?.includes('CANCEL')
    );
    
    // Find the element that displays the count, if it exists
    const upcomingCountElements = document.querySelectorAll('.stat-value.upcoming-count');
    upcomingCountElements.forEach(el => {
        el.textContent = upcomingAppointments.length.toString();
    });
    
    // Count total appointments
    const totalCountElements = document.querySelectorAll('.stat-value.total-count');
    totalCountElements.forEach(el => {
        el.textContent = appointments.length.toString();
    });
    
    // Count completed appointments
    const completedAppointments = appointments.filter(appt => 
        new Date(appt.date_time) < new Date() || appt.status?.includes('COMPLETE')
    );
    
    const completedCountElements = document.querySelectorAll('.stat-value.completed-count');
    completedCountElements.forEach(el => {
        el.textContent = completedAppointments.length.toString();
    });
}

/**
 * Helper function to format date to a readable format
 */
function formatDate(date) {
    const options = { year: 'numeric', month: 'long', day: 'numeric' };
    return date.toLocaleDateString('en-US', options);
}

/**
 * Helper function to format time to a readable format
 */
function formatTime(date) {
    const options = { hour: 'numeric', minute: '2-digit', hour12: true };
    return date.toLocaleTimeString('en-US', options);
}

/**
 * Helper function to get doctor image based on specialty
 */
function getDoctorImage(specialty) {
    const specialtyMap = {
        'cardiology': '../img/doctor-avatar1.jpg',
        'neurology': '../img/doctor-avatar2.jpg',
        'dermatology': '../img/doctor-avatar3.jpg',
        'orthopedics': '../img/doctor-avatar4.jpg',
        'general': '../img/doctor-avatar5.jpg'
    };
    
    return specialtyMap[specialty.toLowerCase()] || '../img/doctor-avatar5.jpg';
}

/**
 * Display a message on the dashboard
 */
function showDashboardMessage(message, type = 'info') {
    const messageContainer = document.createElement('div');
    messageContainer.className = `message-container ${type}`;
    messageContainer.textContent = message;
    
    document.body.appendChild(messageContainer);
    
    // Remove the message after 3 seconds
    setTimeout(() => {
        messageContainer.remove();
    }, 3000);
}

function initializeNotifications() {
    const notificationIcon = document.querySelector('.notification');
    
    if (notificationIcon) {
        notificationIcon.addEventListener('click', function() {
            // Here you would typically show a notification dropdown
            alert('Notifications feature coming soon!');
        });
    }
}

function initializeHealthMetrics() {
    // This function would normally fetch health metrics from an API
    // For demo purposes, we're just setting up the display
    
    const metrics = [
        { id: 'heart-rate', value: '72 bpm', status: 'normal' },
        { id: 'blood-pressure', value: '120/80 mmHg', status: 'normal' },
        { id: 'daily-steps', value: '5,280', status: 'warning' },
        { id: 'weight', value: '72 kg', status: 'normal' }
    ];
    
    // In a real application, you would update the metrics in the DOM
    console.log('Health metrics initialized with:', metrics);
    
    // Add click event to health metric cards
    const metricCards = document.querySelectorAll('.metric-card');
    metricCards.forEach(card => {
        card.addEventListener('click', function() {
            const metricName = this.querySelector('h4').textContent;
            const metricValue = this.querySelector('.metric-value').textContent;
            alert(`${metricName}: ${metricValue}\nClick for detailed history and trends.`);
        });
    });
}

function setupAppointmentActions() {
    // Handle reschedule buttons
    const rescheduleButtons = document.querySelectorAll('.btn-reschedule');
    rescheduleButtons.forEach(button => {
        button.addEventListener('click', function() {
            const appointmentCard = this.closest('.appointment-card');
            const appointmentId = appointmentCard.dataset.id;
            const doctorName = appointmentCard.querySelector('h4').textContent;
            const appointmentDate = appointmentCard.querySelector('.appointment-time span:first-of-type').textContent;
            const appointmentTime = appointmentCard.querySelector('.appointment-time span:last-of-type').textContent;
            
            console.log(`Opening reschedule modal for appointment ${appointmentId}`);
            
            // Populate the reschedule modal with current appointment details
            const currentDetailsEl = document.getElementById('current-appointment-details');
            if (currentDetailsEl) {
                currentDetailsEl.innerHTML = `
                    <strong>Doctor:</strong> ${doctorName}<br>
                    <strong>Date:</strong> ${appointmentDate}<br>
                    <strong>Time:</strong> ${appointmentTime}
                `;
            }
            
            // Store appointment ID in the form for submission
            const rescheduleForm = document.getElementById('reschedule-form');
            if (rescheduleForm) {
                rescheduleForm.dataset.appointmentId = appointmentId;
            }
            
            // Set minimum date to tomorrow
            const datePicker = document.getElementById('reschedule-date');
            if (datePicker) {
                const tomorrow = new Date();
                tomorrow.setDate(tomorrow.getDate() + 1);
                datePicker.min = tomorrow.toISOString().split('T')[0];
                
                // Clear any previous selection
                datePicker.value = '';
            }
            
            // Clear time slots
            const timeSlotsContainer = document.getElementById('reschedule-time-slots');
            if (timeSlotsContainer) {
                timeSlotsContainer.innerHTML = '<p>Please select a date to see available time slots.</p>';
            }
            
            // Reset error container
            const errorContainer = document.getElementById('reschedule-error-container');
            if (errorContainer) {
                errorContainer.innerHTML = '';
            }
            
            // Show the modal
            const modal = document.getElementById('reschedule-modal');
            if (modal) {
                modal.style.display = 'flex';
            }
        });
    });
    
    // Setup modal close button
    const closeModalButton = document.querySelector('#reschedule-modal .close-modal');
    if (closeModalButton) {
        closeModalButton.addEventListener('click', closeRescheduleModal);
    }
    
    // Setup cancel button
    const cancelButton = document.getElementById('cancel-reschedule');
    if (cancelButton) {
        cancelButton.addEventListener('click', closeRescheduleModal);
    }
    
    // Setup date picker change event
    const datePicker = document.getElementById('reschedule-date');
    if (datePicker) {
        datePicker.addEventListener('change', function() {
            if (this.value) {
                fetchAvailableTimeSlots(this.value);
            }
        });
    }
    
    // Setup form submission
    const rescheduleForm = document.getElementById('reschedule-form');
    if (rescheduleForm) {
        rescheduleForm.addEventListener('submit', function(e) {
            e.preventDefault();
            submitReschedule();
        });
    }
    
    // Handle cancel buttons
    const cancelButtons = document.querySelectorAll('.btn-cancel');
    cancelButtons.forEach(button => {
        button.addEventListener('click', function() {
            const appointmentCard = this.closest('.appointment-card');
            const appointmentId = appointmentCard.dataset.id;
            const doctorName = appointmentCard.querySelector('h4').textContent;
            
            if (confirm(`Are you sure you want to cancel your appointment with ${doctorName}?`)) {
                console.log(`Attempting to cancel appointment ID: ${appointmentId}`);
                cancelAppointment(appointmentId, appointmentCard);
            }
        });
    });
}

/**
 * Close the reschedule modal
 */
function closeRescheduleModal() {
    const modal = document.getElementById('reschedule-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

/**
 * Fetch available time slots for a given date
 */
async function fetchAvailableTimeSlots(date) {
    const timeSlotsContainer = document.getElementById('reschedule-time-slots');
    const errorContainer = document.getElementById('reschedule-error-container');
    const form = document.getElementById('reschedule-form');
    
    if (!timeSlotsContainer || !form) return;
    
    const appointmentId = form.dataset.appointmentId;
    if (!appointmentId) {
        showErrorMessage("Missing appointment ID", errorContainer);
        return;
    }
    
    try {
        // Show loading state
        timeSlotsContainer.innerHTML = '<p>Loading available time slots...</p>';
        
        // Get appointment details to get doctor ID
        const token = localStorage.getItem('token');
        if (!token) {
            showErrorMessage("Authentication required. Please log in again.", errorContainer);
            return;
        }
        
        // Get doctor ID from the form dataset
        // Alternatively, we could fetch this from the appointment details
        // For now, we'll create a placeholder API call to get doctor availability
        
        // Make a request to get available time slots
        const response = await fetch(`http://localhost:5000/appointments/availability-range`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                doctor_id: 1, // This would be dynamically populated in a real app
                start_date: date,
                end_date: date
            })
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Failed to fetch available time slots: ${response.status} - ${errorText}`);
        }
        
        const availabilityData = await response.json();
        console.log('Availability data:', availabilityData);
        
        // Extract slots for the selected date
        const slots = availabilityData.availability[date] || [];
        
        // Display time slots
        if (slots.length === 0) {
            timeSlotsContainer.innerHTML = '<p>No available time slots for the selected date. Please choose another date.</p>';
            return;
        }
        
        timeSlotsContainer.innerHTML = '';
        slots.forEach(slot => {
            if (slot.is_booked) return; // Skip booked slots
            
            const timeSlot = document.createElement('div');
            timeSlot.className = 'time-slot';
            timeSlot.dataset.time = slot.start;
            timeSlot.textContent = slot.time || slot.start;
            
            timeSlot.addEventListener('click', function() {
                // Clear previous selections
                document.querySelectorAll('.time-slot').forEach(ts => ts.classList.remove('selected'));
                // Select this slot
                timeSlot.classList.add('selected');
            });
            
            timeSlotsContainer.appendChild(timeSlot);
        });
        
    } catch (error) {
        console.error('Error fetching time slots:', error);
        showErrorMessage(`Failed to load time slots: ${error.message}`, errorContainer);
    }
}

/**
 * Submit the reschedule request
 */
async function submitReschedule() {
    const form = document.getElementById('reschedule-form');
    const datePicker = document.getElementById('reschedule-date');
    const reasonInput = document.getElementById('reschedule-reason');
    const errorContainer = document.getElementById('reschedule-error-container');
    
    if (!form || !datePicker) return;
    
    const appointmentId = form.dataset.appointmentId;
    const selectedDate = datePicker.value;
    const reason = reasonInput ? reasonInput.value : '';
    
    // Get selected time slot
    const selectedTimeSlot = document.querySelector('.time-slot.selected');
    if (!selectedTimeSlot) {
        showErrorMessage("Please select a time slot", errorContainer);
        return;
    }
    
    const selectedTime = selectedTimeSlot.dataset.time;
    
    if (!appointmentId || !selectedDate || !selectedTime) {
        showErrorMessage("Please fill out all required fields", errorContainer);
        return;
    }
    
    try {
        showDashboardMessage('Rescheduling appointment...', 'info');
        
        const token = localStorage.getItem('token');
        if (!token) {
            throw new Error('Authentication required. Please log in again.');
        }
        
        // Format the new date time as expected by the API (YYYY-MM-DD-HH)
        const hour = selectedTime.split(':')[0];
        const newDateTime = `${selectedDate}-${hour}`;
        
        // Call the reschedule API
        const response = await fetch('http://localhost:5000/appointments/reschedule', {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                appointment_id: appointmentId,
                new_date_time: newDateTime,
                reason: reason || 'Rescheduled by patient'
            })
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Failed to reschedule appointment: ${response.status} - ${errorText}`);
        }
        
        const result = await response.json();
        console.log('Appointment rescheduled successfully:', result);
        
        // Close the modal
        closeRescheduleModal();
        
        // Show success message
        showDashboardMessage('Appointment rescheduled successfully!', 'success');
        
        // Refresh appointments to show updated list
        setTimeout(() => {
            fetchDashboardAppointments();
        }, 2000);
        
    } catch (error) {
        console.error('Error rescheduling appointment:', error);
        showErrorMessage(`Failed to reschedule appointment: ${error.message}`, errorContainer);
        showDashboardMessage(`Failed to reschedule appointment: ${error.message}`, 'error');
    }
}

/**
 * Show an error message in the specified container
 */
function showErrorMessage(message, container) {
    if (!container) return;
    
    container.textContent = message;
    container.style.display = 'block';
}

/**
 * Cancel an appointment by making an API call to the backend
 */
async function cancelAppointment(appointmentId, appointmentCard) {
    try {
        const token = localStorage.getItem('token');
        if (!token) {
            console.error('No auth token found');
            showDashboardMessage('Please log in to cancel appointments', 'error');
            return;
        }
        
        console.log('Sending cancel request to backend...');
        
        // Show cancellation in progress message
        showDashboardMessage('Cancelling appointment...', 'info');
        
        const response = await fetch('http://localhost:5000/appointments/cancel', {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                appointment_id: appointmentId,
                reason: 'Cancelled by patient through dashboard',
                notify_availabilities: true
            })
        });
        
        console.log('Received response from server:', response.status);
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('Error cancelling appointment:', errorText);
            throw new Error(`Failed to cancel appointment: ${response.status} - ${errorText}`);
        }
        
        const result = await response.json();
        console.log('Appointment cancelled successfully:', result);
        
        // Update the UI to reflect the cancellation
        updateAppointmentAfterCancellation(appointmentCard);
        
        // Show success message
        showDashboardMessage('Appointment cancelled successfully', 'success');
        
        // Refresh appointments to get the updated list
        setTimeout(() => {
            fetchDashboardAppointments();
        }, 2000);
        
    } catch (error) {
        console.error('Error in cancelAppointment:', error);
        showDashboardMessage(`Failed to cancel appointment: ${error.message}`, 'error');
    }
}

/**
 * Update the appointment card UI after cancellation
 */
function updateAppointmentAfterCancellation(appointmentCard) {
    // Add cancelled class
    appointmentCard.classList.add('cancelled');
    
    // Update status if there's a status element
    const statusElement = appointmentCard.querySelector('.status');
    if (statusElement) {
        statusElement.textContent = 'Cancelled';
        statusElement.className = 'status cancelled';
    }
    
    // Update or disable action buttons
    const actionButtons = appointmentCard.querySelector('.appointment-actions');
    if (actionButtons) {
        actionButtons.innerHTML = `
            <button class="btn-details" disabled>Details</button>
            <button class="btn-book-again">Book Again</button>
        `;
        
        // Setup new book again button
        const bookAgainButton = actionButtons.querySelector('.btn-book-again');
        if (bookAgainButton) {
            bookAgainButton.addEventListener('click', function() {
                const doctorName = appointmentCard.querySelector('h4').textContent;
                alert(`Book again with ${doctorName}\nThis feature is coming soon!`);
            });
        }
    }
}

function setupRecordActions() {
    // Handle view buttons for medical records
    const viewButtons = document.querySelectorAll('.btn-view');
    viewButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const recordCard = this.closest('.record-card');
            const recordTitle = recordCard.querySelector('h4').textContent;
            alert(`Viewing ${recordTitle}\nThis feature is coming soon!`);
        });
    });
}

/**
 * Initialize the dashboard components
 */
function initializeDashboard() {
    console.log('Initializing dashboard components');
    // This function would normally set up dashboard components
    // For demo purposes, let's just log some information
    
    // Check if user is logged in
    const token = localStorage.getItem('token');
    if (!token) {
        console.warn('User is not logged in or token is missing');
        // In a real app, you might redirect to login page
    } else {
        console.log('User is authenticated with token');
    }
    
    // Load user profile information if available
    const userName = document.querySelector('.profile .name');
    if (userName) {
        // In a real app, you would fetch the user profile from the backend
        console.log('User profile element found in the DOM');
    } else {
        console.warn('User profile element not found in the DOM');
    }
    
    console.log('Dashboard initialization complete');
}
