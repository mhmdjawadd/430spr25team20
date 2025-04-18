document.addEventListener('DOMContentLoaded', function() {
    // Initialize filter buttons
    initializeFilters();
    
    // Fetch user appointments from the backend
    fetchUserAppointments();
    
    // Setup appointment actions
    setupAppointmentActions();
    
    // Initialize modal functionality
    initializeModal();
    
    // Initialize pagination
    initializePagination();
    
    // Initialize the reschedule modal
    initializeRescheduleModal();
});

function initializeFilters() {
    const filterButtons = document.querySelectorAll('.filter-btn');
    const appointmentCards = document.querySelectorAll('.appointment-card');
    
    filterButtons.forEach(button => {
        button.addEventListener('click', function() {
            const filter = this.getAttribute('data-filter');
            
            // Update active button
            filterButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            
            // Show/hide appointments based on filter
            appointmentCards.forEach(card => {
                if (filter === 'all') {
                    card.style.display = 'flex';
                } else {
                    if (card.classList.contains(filter)) {
                        card.style.display = 'flex';
                    } else {
                        card.style.display = 'none';
                    }
                }
            });
        });
    });
    
    // Initialize sorting
    const sortSelect = document.getElementById('sort-by');
    sortSelect.addEventListener('change', sortAppointments);
}

function sortAppointments() {
    const sortBy = document.getElementById('sort-by').value;
    const container = document.querySelector('.appointments-container');
    const appointments = Array.from(container.querySelectorAll('.appointment-card'));
    
    appointments.sort((a, b) => {
        if (sortBy === 'date-newest') {
            const dateA = new Date(a.querySelector('.appointment-time span:first-of-type').textContent);
            const dateB = new Date(b.querySelector('.appointment-time span:first-of-type').textContent);
            return dateB - dateA;
        } else if (sortBy === 'date-oldest') {
            const dateA = new Date(a.querySelector('.appointment-time span:first-of-type').textContent);
            const dateB = new Date(b.querySelector('.appointment-time span:first-of-type').textContent);
            return dateA - dateB;
        } else if (sortBy === 'doctor-name') {
            const nameA = a.querySelector('h4').textContent;
            const nameB = b.querySelector('h4').textContent;
            return nameA.localeCompare(nameB);
        } else if (sortBy === 'specialty') {
            const specialtyA = a.querySelector('.appointment-details p').textContent;
            const specialtyB = b.querySelector('.appointment-details p').textContent;
            return specialtyA.localeCompare(specialtyB);
        }
        return 0;
    });
    
    // Remove existing cards and append sorted ones
    appointments.forEach(appointment => container.removeChild(appointment));
    appointments.forEach(appointment => container.appendChild(appointment));
}

function setupAppointmentActions() {
    // Handle detail buttons
    const detailButtons = document.querySelectorAll('.btn-details');
    detailButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            const appointmentCard = this.closest('.appointment-card');
            const doctorName = appointmentCard.querySelector('h4').textContent;
            const specialty = appointmentCard.querySelector('.appointment-details p').textContent;
            const date = appointmentCard.querySelector('.appointment-time span:first-of-type').textContent;
            const time = appointmentCard.querySelector('.appointment-time span:last-of-type').textContent;
            const location = appointmentCard.querySelector('.appointment-location span').textContent;
            
            alert(`Appointment Details:\nDoctor: ${doctorName}\nSpecialty: ${specialty}\nDate: ${date}\nTime: ${time}\nLocation: ${location}`);
        });
    });
    
    // Handle reschedule buttons
    const rescheduleButtons = document.querySelectorAll('.btn-reschedule');
    rescheduleButtons.forEach(button => {
        button.addEventListener('click', function() {
            const appointmentCard = this.closest('.appointment-card');
            const appointmentId = appointmentCard.dataset.id;
            const doctorName = appointmentCard.querySelector('h4').textContent;
            const specialty = appointmentCard.querySelector('.appointment-details p').textContent;
            const date = appointmentCard.querySelector('.appointment-time span:first-of-type').textContent;
            const time = appointmentCard.querySelector('.appointment-time span:last-of-type').textContent;
            const location = appointmentCard.querySelector('.appointment-location span').textContent;
            
            console.log(`Opening reschedule modal for appointment ${appointmentId}`);
            
            // Populate the reschedule modal with current appointment details
            const currentDetailsEl = document.getElementById('current-appointment-details');
            if (currentDetailsEl) {
                currentDetailsEl.innerHTML = `
                    <strong>Doctor:</strong> ${doctorName}<br>
                    <strong>Specialty:</strong> ${specialty}<br>
                    <strong>Current Date:</strong> ${date}<br>
                    <strong>Current Time:</strong> ${time}<br>
                    <strong>Location:</strong> ${location}
                `;
            }
            
            // Store appointment ID in the form for submission
            const rescheduleForm = document.getElementById('reschedule-form');
            if (rescheduleForm) {
                rescheduleForm.dataset.appointmentId = appointmentId;
                rescheduleForm.dataset.doctorId = appointmentCard.dataset.doctorId || '1'; // Fallback to 1 if not set
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
    
    // Handle feedback buttons
    const feedbackButtons = document.querySelectorAll('.btn-feedback');
    feedbackButtons.forEach(button => {
        button.addEventListener('click', function() {
            const appointmentCard = this.closest('.appointment-card');
            const doctorName = appointmentCard.querySelector('h4').textContent;
            alert(`Leave feedback for your appointment with ${doctorName}\nThis feature is coming soon!`);
        });
    });
    
    // Handle book again buttons
    const bookAgainButtons = document.querySelectorAll('.btn-book-again');
    bookAgainButtons.forEach(button => {
        button.addEventListener('click', function() {
            const appointmentCard = this.closest('.appointment-card');
            const doctorName = appointmentCard.querySelector('h4').textContent;
            
            // Pre-fill the form
            const doctorSelect = document.getElementById('doctor');
            for (let i = 0; i < doctorSelect.options.length; i++) {
                if (doctorSelect.options[i].text === doctorName) {
                    doctorSelect.selectedIndex = i;
                    break;
                }
            }
            
            // Open the modal
            document.getElementById('book-appointment-modal').style.display = 'flex';
        });
    });
}

/**
 * Cancel an appointment by making an API call to the backend
 */
async function cancelAppointment(appointmentId, appointmentCard) {
    try {
        const token = localStorage.getItem('token');
        if (!token) {
            console.error('No auth token found');
            showMessage('Please log in to cancel appointments', 'error');
            return;
        }
        
        console.log('Sending cancel request to backend...');
        
        // Show cancellation in progress message
        showMessage('Cancelling appointment...', 'info');
        
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
        appointmentCard.classList.remove('upcoming');
        appointmentCard.classList.add('cancelled');
        
        const statusSpan = appointmentCard.querySelector('.status');
        if (statusSpan) {
            statusSpan.textContent = 'Cancelled';
            statusSpan.className = 'status cancelled';
        }
        
        // Replace action buttons
        const actionDiv = appointmentCard.querySelector('.appointment-actions');
        if (actionDiv) {
            actionDiv.innerHTML = `
                <button class="btn-details"><i class="fas fa-info-circle"></i> Details</button>
                <button class="btn-book-again"><i class="fas fa-redo"></i> Book Again</button>
            `;
            
            // Setup the new buttons
            const newDetailsBtn = actionDiv.querySelector('.btn-details');
            if (newDetailsBtn) {
                newDetailsBtn.addEventListener('click', function() {
                    alert(`Appointment Details for ${doctorName}`);
                });
            }
            
            const newBookAgainBtn = actionDiv.querySelector('.btn-book-again');
            if (newBookAgainBtn) {
                newBookAgainBtn.addEventListener('click', function() {
                    alert(`Book again with ${doctorName}`);
                });
            }
        }
        
        // Show success message
        showMessage('Appointment cancelled successfully', 'success');
        
    } catch (error) {
        console.error('Error in cancelAppointment:', error);
        showMessage(`Failed to cancel appointment: ${error.message}`, 'error');
    }
}

function initializeModal() {
    const modal = document.getElementById('book-appointment-modal');
    const openModalButton = document.getElementById('new-appointment-btn');
    const closeButtons = document.querySelectorAll('.close-modal, .btn-cancel-form');
    const form = document.getElementById('appointment-form');
    
    // Open modal
    openModalButton.addEventListener('click', function() {
        modal.style.display = 'flex';
    });
    
    // Close modal
    closeButtons.forEach(button => {
        button.addEventListener('click', function() {
            modal.style.display = 'none';
            form.reset();
        });
    });
    
    // Close when clicking outside
    window.addEventListener('click', function(event) {
        if (event.target === modal) {
            modal.style.display = 'none';
            form.reset();
        }
    });
    
    // Handle form submission
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // In a real app, you would send the form data to an API
        const specialty = document.getElementById('specialty').value;
        const doctor = document.getElementById('doctor').options[document.getElementById('doctor').selectedIndex].text;
        const date = document.getElementById('appointment-date').value;
        const time = document.getElementById('appointment-time').options[document.getElementById('appointment-time').selectedIndex].text;
        const reason = document.getElementById('reason').value;
        
        alert(`Appointment Booked!\nDoctor: ${doctor}\nSpecialty: ${specialty}\nDate: ${date}\nTime: ${time}\nReason: ${reason}`);
        
        modal.style.display = 'none';
        form.reset();
    });
    
    // Dynamically update doctor options based on specialty
    const specialtySelect = document.getElementById('specialty');
    specialtySelect.addEventListener('change', function() {
        const specialty = this.value;
        const doctorSelect = document.getElementById('doctor');
        
        // Clear existing options
        doctorSelect.innerHTML = '<option value="">Select Doctor</option>';
        
        // Add doctors based on specialty
        if (specialty === 'cardiology') {
            const option = document.createElement('option');
            option.value = 'dr-sarah';
            option.textContent = 'Dr. Sarah Johnson';
            doctorSelect.appendChild(option);
        } else if (specialty === 'neurology') {
            const option = document.createElement('option');
            option.value = 'dr-james';
            option.textContent = 'Dr. James Wilson';
            doctorSelect.appendChild(option);
        } else if (specialty === 'dermatology') {
            const option = document.createElement('option');
            option.value = 'dr-emily';
            option.textContent = 'Dr. Emily Chen';
            doctorSelect.appendChild(option);
        } else if (specialty === 'orthopedics') {
            const option = document.createElement('option');
            option.value = 'dr-michael';
            option.textContent = 'Dr. Michael Brown';
            doctorSelect.appendChild(option);
        } else {
            // Add all doctors for other specialties
            const doctors = [
                { value: 'dr-sarah', text: 'Dr. Sarah Johnson' },
                { value: 'dr-james', text: 'Dr. James Wilson' },
                { value: 'dr-emily', text: 'Dr. Emily Chen' },
                { value: 'dr-michael', text: 'Dr. Michael Brown' }
            ];
            
            doctors.forEach(doctor => {
                const option = document.createElement('option');
                option.value = doctor.value;
                option.textContent = doctor.text;
                doctorSelect.appendChild(option);
            });
        }
    });
}

function initializePagination() {
    const prevButton = document.querySelector('.pagination-btn.prev');
    const nextButton = document.querySelector('.pagination-btn.next');
    const pageButtons = document.querySelectorAll('.pagination-btn.page');
    
    pageButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Remove active class from all page buttons
            pageButtons.forEach(btn => btn.classList.remove('active'));
            
            // Add active class to clicked button
            this.classList.add('active');
            
            // In a real app, you would load the appointments for the selected page
            const page = this.textContent;
            console.log(`Loading page ${page}`);
            
            // Update disabled state of prev/next buttons
            prevButton.classList.toggle('disabled', page === '1');
            nextButton.classList.toggle('disabled', page === '3');
        });
    });
    
    prevButton.addEventListener('click', function() {
        if (!this.classList.contains('disabled')) {
            const activePage = document.querySelector('.pagination-btn.page.active');
            const prevPage = activePage.previousElementSibling;
            if (prevPage && prevPage.classList.contains('page')) {
                activePage.classList.remove('active');
                prevPage.classList.add('active');
                
                // In a real app, you would load the appointments for the selected page
                console.log(`Loading page ${prevPage.textContent}`);
                
                // Update disabled state of prev/next buttons
                this.classList.toggle('disabled', prevPage.textContent === '1');
                nextButton.classList.remove('disabled');
            }
        }
    });
    
    nextButton.addEventListener('click', function() {
        if (!this.classList.contains('disabled')) {
            const activePage = document.querySelector('.pagination-btn.page.active');
            const nextPage = activePage.nextElementSibling;
            if (nextPage && nextPage.classList.contains('page')) {
                activePage.classList.remove('active');
                nextPage.classList.add('active');
                
                // In a real app, you would load the appointments for the selected page
                console.log(`Loading page ${nextPage.textContent}`);
                
                // Update disabled state of prev/next buttons
                prevButton.classList.remove('disabled');
                this.classList.toggle('disabled', nextPage.textContent === '3');
            }
        }
    });
}

/**
 * Fetch all appointments for the current user from the backend
 */
async function fetchUserAppointments() {
    try {
        // Get auth token from localStorage
        const token = localStorage.getItem('token');
        if (!token) {
            showMessage('Please log in to view your appointments', 'error');
            return;
        }
        
        // Display loading state
        const appointmentsContainer = document.querySelector('.appointments-container');
        appointmentsContainer.innerHTML = '<div class="loading-spinner">Loading your appointments...</div>';
        
        // Fetch appointments from the backend
        const response = await fetch('http://localhost:5000/appointments/patient', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error(`Failed to fetch appointments: ${response.status}`);
        }
        
        const appointments = await response.json();
        displayAppointments(appointments);
        
        // Update appointment count in the dashboard
        updateAppointmentCount(appointments);
    } catch (error) {
        console.error('Error fetching appointments:', error);
        const appointmentsContainer = document.querySelector('.appointments-container');
        appointmentsContainer.innerHTML = `<div class="error-message">Failed to load appointments: ${error.message}</div>`;
    }
}

/**
 * Display the fetched appointments in the UI
 */
function displayAppointments(appointments) {
    const appointmentsContainer = document.querySelector('.appointments-container');
    
    // Clear the container
    appointmentsContainer.innerHTML = '';
    
    if (!appointments || appointments.length === 0) {
        appointmentsContainer.innerHTML = '<div class="no-appointments">You have no appointments scheduled. Click "Book New Appointment" to schedule one.</div>';
        return;
    }
    
    // Sort appointments by date (newest first)
    appointments.sort((a, b) => new Date(b.date_time) - new Date(a.date_time));
    
    // Create appointment cards for each appointment
    appointments.forEach(appointment => {
        const appointmentDate = new Date(appointment.date_time);
        const status = getAppointmentStatus(appointment);
        
        const appointmentCard = document.createElement('div');
        appointmentCard.className = `appointment-card ${status.toLowerCase()}`;
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
                    <div class="appointment-location">
                        <i class="fas fa-map-marker-alt"></i>
                        <span>Nabad Medical Center, Room ${getRandomRoom()}</span>
                    </div>
                    <span class="status ${status.toLowerCase()}">${status}</span>
                </div>
            </div>
            <div class="appointment-actions">
                <button class="btn-details"><i class="fas fa-info-circle"></i> Details</button>
                ${getActionButtons(status)}
            </div>
        `;
        
        appointmentsContainer.appendChild(appointmentCard);
    });
    
    // After adding all appointments to the DOM, re-setup the event listeners
    setupAppointmentActions();
}

/**
 * Update the appointment count in the dashboard header
 */
function updateAppointmentCount(appointments) {
    if (!appointments) return;
    
    // Count upcoming appointments
    const upcomingAppointments = appointments.filter(appt => 
        new Date(appt.date_time) > new Date() && !appt.status?.includes('CANCEL')
    );
    
    // Find the element that displays the count, if it exists
    const countElement = document.querySelector('.upcoming-count');
    if (countElement) {
        countElement.textContent = upcomingAppointments.length.toString();
    }
}

/**
 * Helper function to determine appointment status based on date and status field
 */
function getAppointmentStatus(appointment) {
    if (appointment.status) {
        if (appointment.status.includes('CANCEL')) return 'Cancelled';
        if (appointment.status.includes('COMPLETE')) return 'Completed';
    }
    
    const appointmentDate = new Date(appointment.date_time);
    const now = new Date();
    
    if (appointmentDate < now) {
        return 'Completed';
    }
    return 'Upcoming';
}

/**
 * Helper function to get the appropriate action buttons based on appointment status
 */
function getActionButtons(status) {
    if (status === 'Upcoming') {
        return `
            <button class="btn-reschedule"><i class="fas fa-calendar-alt"></i> Reschedule</button>
            <button class="btn-cancel"><i class="fas fa-times"></i> Cancel</button>
        `;
    } else if (status === 'Completed') {
        return `
            <button class="btn-feedback"><i class="fas fa-comment"></i> Leave Feedback</button>
            <button class="btn-book-again"><i class="fas fa-redo"></i> Book Again</button>
        `;
    } else {
        return `
            <button class="btn-book-again"><i class="fas fa-redo"></i> Book Again</button>
        `;
    }
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
 * Helper function to get a random room number for display purposes
 */
function getRandomRoom() {
    return Math.floor(Math.random() * 500) + 100;
}

/**
 * Helper function to get doctor image based on specialty
 */
function getDoctorImage(specialty) {
    const specialtyMap = {
        'cardiology': 'img/doctor-avatar1.jpg',
        'neurology': 'img/doctor-avatar2.jpg',
        'dermatology': 'img/doctor-avatar3.jpg',
        'orthopedics': 'img/doctor-avatar4.jpg',
        'general': 'img/doctor-avatar5.jpg'
    };
    
    return specialtyMap[specialty.toLowerCase()] || 'img/doctor-avatar5.jpg';
}

/**
 * Display a message to the user
 */
function showMessage(message, type = 'info') {
    const messageContainer = document.createElement('div');
    messageContainer.className = `message-container ${type}`;
    messageContainer.textContent = message;
    
    document.body.appendChild(messageContainer);
    
    // Remove the message after 3 seconds
    setTimeout(() => {
        messageContainer.remove();
    }, 3000);
}

/**
 * Initialize the reschedule modal functionality
 */
function initializeRescheduleModal() {
    const modal = document.getElementById('reschedule-modal');
    const closeButtons = document.querySelectorAll('#reschedule-modal .close-modal, #cancel-reschedule');
    const form = document.getElementById('reschedule-form');
    
    // Close modal
    closeButtons.forEach(button => {
        button.addEventListener('click', function() {
            closeRescheduleModal();
        });
    });
    
    // Close when clicking outside
    window.addEventListener('click', function(event) {
        if (event.target === modal) {
            closeRescheduleModal();
        }
    });
    
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
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            submitReschedule();
        });
    }
    
    // Initialize calendar if available
    initializeRescheduleCalendar();
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
 * Initialize the FullCalendar for rescheduling
 */
function initializeRescheduleCalendar() {
    const calendarEl = document.getElementById('reschedule-calendar');
    if (!calendarEl || typeof FullCalendar === 'undefined') return;
    
    window.rescheduleCalendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'timeGridWeek',
        headerToolbar: {
            left: 'prev,next',
            center: 'title',
            right: ''
        },
        height: 400,
        allDaySlot: false,
        slotMinTime: '08:00:00',
        slotMaxTime: '18:00:00',
        slotDuration: '01:00:00',
        selectable: true,
        selectMirror: true,
        businessHours: {
            daysOfWeek: [1, 2, 3, 4, 5], // Monday - Friday
            startTime: '08:00',
            endTime: '18:00',
        },
        select: function(info) {
            // Format date as YYYY-MM-DD
            const clickedDate = info.start.toISOString().split('T')[0];
            
            // Format time as HH:MM
            const clickedTime = info.start.toTimeString().slice(0, 5);
            
            selectRescheduleTimeSlot(clickedDate, clickedTime);
        },
        eventClick: function(info) {
            const eventData = info.event.extendedProps;
            
            // Only allow selecting available slots
            if (eventData.isAvailable) {
                // Clear previous selected events styling
                window.rescheduleCalendar.getEvents().forEach(event => {
                    if (event.extendedProps.isAvailable) {
                        event.setProp('backgroundColor', '#1A76D1');
                        event.setProp('borderColor', '#1A76D1');
                    }
                });
                
                // Update event styling to indicate selection
                info.event.setProp('backgroundColor', '#28a745');
                info.event.setProp('borderColor', '#28a745');
                
                // Get the date and time
                const eventDate = info.event.start.toISOString().split('T')[0];
                const eventTime = info.event.start.toTimeString().slice(0, 5);
                
                // Update time slot selection
                selectRescheduleTimeSlot(eventDate, eventTime);
            }
        },
        datesSet: function(dateInfo) {
            const form = document.getElementById('reschedule-form');
            if (form && form.dataset.doctorId) {
                const doctorId = form.dataset.doctorId;
                
                // Fetch availability for the entire visible range
                fetchAvailabilityRange(
                    doctorId,
                    dateInfo.start,
                    dateInfo.end
                );
            }
        }
    });
    
    window.rescheduleCalendar.render();
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
    const doctorId = form.dataset.doctorId;
    
    if (!appointmentId || !doctorId) {
        showErrorMessage("Missing appointment or doctor information", errorContainer);
        return;
    }
    
    try {
        // Show loading state
        timeSlotsContainer.innerHTML = '<p>Loading available time slots...</p>';
        
        // Get authentication token
        const token = localStorage.getItem('token');
        if (!token) {
            showErrorMessage("Authentication required. Please log in again.", errorContainer);
            return;
        }
        
        // Make a request to get available time slots
        const response = await fetch(`http://localhost:5000/appointments/availability-range`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                doctor_id: doctorId,
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
                
                // Update the date picker to match calendar selection
                const datePicker = document.getElementById('reschedule-date');
                if (datePicker) {
                    datePicker.value = date;
                }
            });
            
            timeSlotsContainer.appendChild(timeSlot);
        });
        
    } catch (error) {
        console.error('Error fetching time slots:', error);
        showErrorMessage(`Failed to load time slots: ${error.message}`, errorContainer);
    }
}

/**
 * Fetch doctor availability for a date range (for the calendar)
 */
async function fetchAvailabilityRange(doctorId, startDate, endDate) {
    const errorContainer = document.getElementById('reschedule-error-container');
    
    try {
        // Format dates in YYYY-MM-DD format
        const formattedStartDate = startDate.toISOString().split('T')[0];
        const formattedEndDate = endDate.toISOString().split('T')[0];
        
        // Get authentication token
        const token = localStorage.getItem('token');
        if (!token) {
            showErrorMessage("Authentication required. Please log in again.", errorContainer);
            return;
        }
        
        // Make API request
        const response = await fetch(`http://localhost:5000/appointments/availability-range`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                doctor_id: doctorId,
                start_date: formattedStartDate,
                end_date: formattedEndDate
            })
        });
        
        if (!response.ok) {
            let errorText = 'Failed to fetch availability data';
            try {
                const errorData = await response.json();
                errorText = errorData.error || errorText;
            } catch (e) {
                // If we can't parse the JSON, just use the default error message
            }
            throw new Error(errorText);
        }
        
        const data = await response.json();
        console.log('Availability data received:', data);
        
        // Update the calendar with the availability data
        if (data && data.availability) {
            updateRescheduleCalendarWithAvailability(data.availability);
        }
    } catch (error) {
        console.error('Error fetching availability range:', error);
        showErrorMessage(`Error: ${error.message}`, errorContainer);
    }
}

/**
 * Update calendar with availability data
 */
function updateRescheduleCalendarWithAvailability(availabilityData) {
    if (!window.rescheduleCalendar) return;
    
    // Clear existing events
    window.rescheduleCalendar.getEvents().forEach(event => event.remove());
    
    // Process each date in the availability data
    Object.keys(availabilityData).forEach(dateStr => {
        const slots = availabilityData[dateStr];
        
        // Add each slot as an event on the calendar
        slots.forEach(slot => {
            // Skip if no start/end time
            if (!slot.start) return;
            
            // Extract start and end times
            const [startHour, startMinute] = slot.start.split(':').map(Number);
            const endTime = slot.end || `${(startHour + 1).toString().padStart(2, '0')}:${startMinute.toString().padStart(2, '0')}`;
            
            // Create date objects for the start and end times
            const startDateTime = `${dateStr}T${slot.start}:00`;
            const endDateTime = `${dateStr}T${endTime}:00`;
            
            // Add event to calendar
            window.rescheduleCalendar.addEvent({
                title: slot.is_booked ? 'Booked' : 'Available',
                start: startDateTime,
                end: endDateTime,
                color: slot.is_booked ? '#ccc' : '#1A76D1',
                textColor: slot.is_booked ? '#666' : '#fff',
                extendedProps: {
                    isAvailable: !slot.is_booked,
                    time: slot.time || `${slot.start} - ${endTime}`
                }
            });
        });
    });
}

/**
 * Select a time slot for rescheduling
 */
function selectRescheduleTimeSlot(date, time) {
    console.log(`Selecting reschedule time slot: date=${date}, time=${time}`);
    
    // Update the date picker
    const datePicker = document.getElementById('reschedule-date');
    if (datePicker) {
        datePicker.value = date;
    }
    
    // Find the matching time slot in the list and select it
    const timeSlots = document.querySelectorAll('#reschedule-time-slots .time-slot');
    let found = false;
    
    timeSlots.forEach(slot => {
        if (slot.dataset.time === time) {
            // Clear previous selections
            timeSlots.forEach(ts => ts.classList.remove('selected'));
            // Select this one
            slot.classList.add('selected');
            found = true;
        }
    });
    
    // If we didn't find a matching slot in the list, we might need to update the list
    if (!found) {
        fetchAvailableTimeSlots(date);
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
    const selectedTimeSlot = document.querySelector('#reschedule-time-slots .time-slot.selected');
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
        showMessage('Rescheduling appointment...', 'info');
        
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
        showMessage('Appointment rescheduled successfully!', 'success');
        
        // Refresh appointments to show updated list
        setTimeout(() => {
            fetchUserAppointments();
        }, 2000);
        
    } catch (error) {
        console.error('Error rescheduling appointment:', error);
        showErrorMessage(`Failed to reschedule appointment: ${error.message}`, errorContainer);
    }
}

/**
 * Show an error message in the specified container
 */
function showErrorMessage(message, container) {
    if (!container) return;
    
    container.innerHTML = `<div class="error-message">${message}</div>`;
    container.style.display = 'block';
}
