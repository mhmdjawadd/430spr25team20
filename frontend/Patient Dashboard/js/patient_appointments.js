document.addEventListener('DOMContentLoaded', function() {
    initializeFilters();
    fetchUserAppointments();
    setupAppointmentActions();
    initializeModal();
    initializePagination();
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
                    card.style.display = card.classList.contains(filter) ? 'flex' : 'none';
                }
            });
        });
    });
    
    // Initialize sorting
    const sortSelect = document.getElementById('sort-by');
    if (sortSelect) {
        sortSelect.addEventListener('change', sortAppointments);
    }
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
    setupDetailButtons();
    setupRescheduleButtons();
    setupCancelButtons();
    setupFeedbackButtons();
    setupBookAgainButtons();
}

function setupDetailButtons() {
    const detailButtons = document.querySelectorAll('.btn-details');
    detailButtons.forEach(button => {
        button.addEventListener('click', function() {
            const appointmentCard = this.closest('.appointment-card');
            const doctorName = appointmentCard.querySelector('h4').textContent;
            const specialty = appointmentCard.querySelector('.appointment-details p').textContent;
            const date = appointmentCard.querySelector('.appointment-time span:first-of-type').textContent;
            const time = appointmentCard.querySelector('.appointment-time span:last-of-type').textContent;
            const location = appointmentCard.querySelector('.appointment-location span').textContent;
            
            alert(`Appointment Details:\nDoctor: ${doctorName}\nSpecialty: ${specialty}\nDate: ${date}\nTime: ${time}\nLocation: ${location}`);
        });
    });
}

function setupRescheduleButtons() {
    const rescheduleButtons = document.querySelectorAll('.btn-reschedule');
    rescheduleButtons.forEach(button => {
        button.addEventListener('click', function() {
            const appointmentCard = this.closest('.appointment-card');
            const appointmentId = appointmentCard.dataset.id;
            const doctorId = appointmentCard.dataset.doctorId || '1';
            const doctorName = appointmentCard.querySelector('h4').textContent;
            const specialty = appointmentCard.querySelector('.appointment-details p').textContent;
            const date = appointmentCard.querySelector('.appointment-time span:first-of-type').textContent;
            const time = appointmentCard.querySelector('.appointment-time span:last-of-type').textContent;
            const location = appointmentCard.querySelector('.appointment-location span').textContent;
            
            // Populate the reschedule modal
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
            
            // Store appointment ID and doctor info in the form for submission
            const rescheduleForm = document.getElementById('reschedule-form');
            if (rescheduleForm) {
                rescheduleForm.dataset.appointmentId = appointmentId;
                rescheduleForm.dataset.doctorId = doctorId;
                rescheduleForm.dataset.doctorName = doctorName;
                rescheduleForm.dataset.specialty = specialty;
            }
            
            // Show the modal
            const modal = document.getElementById('reschedule-modal');
            if (modal) {
                modal.style.display = 'flex';
                
                // Initialize calendar if not already initialized
                if (window.rescheduleCalendar) {
                    // Force refresh calendar after modal is shown
                    setTimeout(() => {
                        window.rescheduleCalendar.updateSize();
                        
                        // Fetch availability for the currently visible range
                        const view = window.rescheduleCalendar.view;
                        fetchAvailabilityRange(
                            doctorId,
                            view.activeStart,
                            view.activeEnd
                        );
                    }, 100);
                }
            }
            
            // Clear error messages
            const errorContainer = document.getElementById('reschedule-error-container');
            if (errorContainer) {
                errorContainer.innerHTML = '';
            }
        });
    });
}

function setupCancelButtons() {
    const cancelButtons = document.querySelectorAll('.btn-cancel');
    cancelButtons.forEach(button => {
        button.addEventListener('click', function() {
            const appointmentCard = this.closest('.appointment-card');
            const appointmentId = appointmentCard.dataset.id;
            const doctorName = appointmentCard.querySelector('h4').textContent;
            
            if (confirm(`Are you sure you want to cancel your appointment with ${doctorName}?`)) {
                cancelAppointment(appointmentId, appointmentCard);
            }
        });
    });
}

function setupFeedbackButtons() {
    const feedbackButtons = document.querySelectorAll('.btn-feedback');
    feedbackButtons.forEach(button => {
        button.addEventListener('click', function() {
            const appointmentCard = this.closest('.appointment-card');
            const doctorName = appointmentCard.querySelector('h4').textContent;
            alert(`Leave feedback for your appointment with ${doctorName}\nThis feature is coming soon!`);
        });
    });
}

function setupBookAgainButtons() {
    const bookAgainButtons = document.querySelectorAll('.btn-book-again');
    bookAgainButtons.forEach(button => {
        button.addEventListener('click', function() {
            const appointmentCard = this.closest('.appointment-card');
            const doctorName = appointmentCard.querySelector('h4').textContent;
            
            // Pre-fill the form
            const doctorSelect = document.getElementById('doctor');
            if (doctorSelect) {
                for (let i = 0; i < doctorSelect.options.length; i++) {
                    if (doctorSelect.options[i].text === doctorName) {
                        doctorSelect.selectedIndex = i;
                        break;
                    }
                }
            }
            
            // Open the modal
            const modal = document.getElementById('book-appointment-modal');
            if (modal) {
                modal.style.display = 'flex';
            }
        });
    });
}

async function cancelAppointment(appointmentId, appointmentCard) {
    try {
        const token = localStorage.getItem('token');
        if (!token) {
            showMessage('Please log in to cancel appointments', 'error');
            return;
        }
        
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
        
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Failed to cancel appointment: ${response.status} - ${errorText}`);
        }
        
        const result = await response.json();
        
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
            
            // Re-attach event listeners to the new buttons
            const newDetailsBtn = actionDiv.querySelector('.btn-details');
            const newBookAgainBtn = actionDiv.querySelector('.btn-book-again');
            
            if (newDetailsBtn) {
                newDetailsBtn.addEventListener('click', function() {
                    const doctorName = appointmentCard.querySelector('h4').textContent;
                    alert(`Appointment Details for ${doctorName}`);
                });
            }
            
            if (newBookAgainBtn) {
                newBookAgainBtn.addEventListener('click', function() {
                    const doctorName = appointmentCard.querySelector('h4').textContent;
                    alert(`Book again with ${doctorName}`);
                });
            }
        }
        
        showMessage('Appointment cancelled successfully', 'success');
        
    } catch (error) {
        showMessage(`Failed to cancel appointment: ${error.message}`, 'error');
    }
}

function initializeModal() {
    const modal = document.getElementById('book-appointment-modal');
    // Removed openModalButton related to 'new-appointment-btn'
    const closeButtons = document.querySelectorAll('#book-appointment-modal .close-modal, #book-appointment-modal .btn-cancel-form');
    const form = document.getElementById('appointment-form');
    
    // Check if modal and form exist, but don't require the specific open button anymore for this initialization
    if (!modal || !form) return;
    
    // Removed: openModalButton.addEventListener('click', () => modal.style.display = 'flex');
    
    // Close modal functionality remains
    closeButtons.forEach(button => {
        button.addEventListener('click', () => {
            modal.style.display = 'none';
            form.reset();
        });
    });
    
    // Close when clicking outside remains
    window.addEventListener('click', (event) => {
        // Ensure we only close the booking modal, not others like reschedule
        if (event.target === modal) {
            modal.style.display = 'none';
            form.reset();
        }
    });
    
    // Handle form submission remains
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const specialty = document.getElementById('specialty').value;
        const doctorSelect = document.getElementById('doctor');
        const doctor = doctorSelect ? doctorSelect.options[doctorSelect.selectedIndex].text : '';
        const date = document.getElementById('appointment-date').value;
        const timeSelect = document.getElementById('appointment-time');
        const time = timeSelect ? timeSelect.options[timeSelect.selectedIndex].text : '';
        const reason = document.getElementById('reason').value;
        
        alert(`Appointment Booked!\nDoctor: ${doctor}\nSpecialty: ${specialty}\nDate: ${date}\nTime: ${time}\nReason: ${reason}`);
        
        modal.style.display = 'none';
        form.reset();
    });
    
    // Update doctor options based on specialty remains
    const specialtySelect = document.getElementById('specialty');
    if (specialtySelect) {
        specialtySelect.addEventListener('change', updateDoctorsBySpecialty);
    }
}

function updateDoctorsBySpecialty() {
    const specialty = this.value;
    const doctorSelect = document.getElementById('doctor');
    
    if (!doctorSelect) return;
    
    // Clear existing options
    doctorSelect.innerHTML = '<option value="">Select Doctor</option>';
    
    // Define doctors by specialty
    const doctorsBySpecialty = {
        'cardiology': [{ value: 'dr-sarah', text: 'Dr. Sarah Johnson' }],
        'neurology': [{ value: 'dr-james', text: 'Dr. James Wilson' }],
        'dermatology': [{ value: 'dr-emily', text: 'Dr. Emily Chen' }],
        'orthopedics': [{ value: 'dr-michael', text: 'Dr. Michael Brown' }]
    };
    
    // Get doctors for selected specialty or all doctors
    const doctors = doctorsBySpecialty[specialty] || Object.values(doctorsBySpecialty).flat();
    
    // Add doctors to select
    doctors.forEach(doctor => {
        const option = document.createElement('option');
        option.value = doctor.value;
        option.textContent = doctor.text;
        doctorSelect.appendChild(option);
    });
}

function initializePagination() {
    const prevButton = document.querySelector('.pagination-btn.prev');
    const nextButton = document.querySelector('.pagination-btn.next');
    const pageButtons = document.querySelectorAll('.pagination-btn.page');
    
    if (!prevButton || !nextButton || pageButtons.length === 0) return;
    
    pageButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Remove active class from all page buttons
            pageButtons.forEach(btn => btn.classList.remove('active'));
            
            // Add active class to clicked button
            this.classList.add('active');
            
            // Handle page loading logic here
            const page = this.textContent;
            
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
                
                // Handle page loading logic here
                
                // Update button states
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
                
                // Handle page loading logic here
                
                // Update button states
                prevButton.classList.remove('disabled');
                this.classList.toggle('disabled', nextPage.textContent === '3');
            }
        }
    });
}

async function fetchUserAppointments() {
    try {
        const token = localStorage.getItem('token');
        if (!token) {
            showMessage('Please log in to view your appointments', 'error');
            return;
        }
        
        // Display loading state
        const appointmentsContainer = document.querySelector('.appointments-container');
        if (!appointmentsContainer) return;
        
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
        updateAppointmentCount(appointments);
    } catch (error) {
        const appointmentsContainer = document.querySelector('.appointments-container');
        if (appointmentsContainer) {
            appointmentsContainer.innerHTML = `<div class="error-message">Failed to load appointments: ${error.message}</div>`;
        }
    }
}

function displayAppointments(appointments) {
    const appointmentsContainer = document.querySelector('.appointments-container');
    if (!appointmentsContainer) return;
    
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
        
        // Add the doctor_id as a data attribute - this is crucial for rescheduling
        appointmentCard.dataset.doctorId = appointment.doctor_id || (appointment.doctor && appointment.doctor.id) || '1';
        
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
    
    // Setup event listeners for action buttons
    setupAppointmentActions();
}

function updateAppointmentCount(appointments) {
    if (!appointments) return;
    
    // Count upcoming appointments
    const upcomingAppointments = appointments.filter(appt => 
        new Date(appt.date_time) > new Date() && !appt.status?.includes('CANCEL')
    );
    
    // Update count in UI
    const countElement = document.querySelector('.upcoming-count');
    if (countElement) {
        countElement.textContent = upcomingAppointments.length.toString();
    }
}

function getAppointmentStatus(appointment) {
    if (appointment.status) {
        if (appointment.status.includes('CANCEL')) return 'Cancelled';
        if (appointment.status.includes('COMPLETE')) return 'Completed';
    }
    
    return new Date(appointment.date_time) < new Date() ? 'Completed' : 'Upcoming';
}

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

function formatDate(date) {
    const options = { year: 'numeric', month: 'long', day: 'numeric' };
    return date.toLocaleDateString('en-US', options);
}

function formatTime(date) {
    const options = { hour: 'numeric', minute: '2-digit', hour12: true };
    return date.toLocaleTimeString('en-US', options);
}

function getRandomRoom() {
    return Math.floor(Math.random() * 500) + 100;
}

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

function showMessage(message, type = 'info') {
    const messageContainer = document.createElement('div');
    messageContainer.className = `message-container ${type}`;
    messageContainer.textContent = message;
    document.body.appendChild(messageContainer);
    
    // Remove the message after 3 seconds
    setTimeout(() => messageContainer.remove(), 3000);
}

function initializeRescheduleModal() {
    const modal = document.getElementById('reschedule-modal');
    const closeButtons = document.querySelectorAll('#reschedule-modal .close-modal, #cancel-reschedule');
    const form = document.getElementById('reschedule-form');
    
    if (!modal) return;
    
    // Close modal
    closeButtons.forEach(button => {
        button.addEventListener('click', closeRescheduleModal);
    });
    
    // Close when clicking outside
    window.addEventListener('click', function(event) {
        if (event.target === modal) {
            closeRescheduleModal();
        }
    });
    
    // Setup form submission
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            submitReschedule();
        });
    }
    
    // Initialize calendar instead of using the date picker
    initializeRescheduleCalendar();
}

function closeRescheduleModal() {
    const modal = document.getElementById('reschedule-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

function initializeRescheduleCalendar() {
    const calendarEl = document.getElementById('reschedule-calendar');
    if (!calendarEl || typeof FullCalendar === 'undefined') {
        return;
    }
    
    window.rescheduleCalendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'timeGridWeek',
        headerToolbar: {
            left: 'prev,next',
            center: 'title',
            right: ''
        },
        height: 'auto',
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
            const clickedDate = info.start.toISOString().split('T')[0];
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
                
                // Store selected time slot data
                window.selectedRescheduleTimeSlotData = {
                    date: eventDate,
                    start: eventTime,
                    end: info.event.end ? info.event.end.toTimeString().slice(0, 5) : 
                        `${parseInt(eventTime.split(':')[0]) + 1}:${eventTime.split(':')[1]}`
                };
            }
        },
        datesSet: function(dateInfo) {
            const form = document.getElementById('reschedule-form');
            if (form && form.dataset.doctorId) {
                fetchAvailabilityRange(
                    form.dataset.doctorId,
                    dateInfo.start,
                    dateInfo.end
                );
            }
        }
    });
    
    window.rescheduleCalendar.render();
}

function selectRescheduleTimeSlot(date, time) {
    // Update the date picker if it exists (for backward compatibility)
    const datePicker = document.getElementById('reschedule-date');
    if (datePicker) {
        datePicker.value = date;
    }
    
    // Store the selected time globally
    window.selectedRescheduleTime = time;
    window.selectedRescheduleDate = date;
    
    // Find the matching time slot in the list and select it
    const timeSlots = document.querySelectorAll('#reschedule-time-slots .time-slot');
    let found = false;
    timeSlots.forEach(slot => {
        slot.classList.remove('selected');
        if (slot.dataset.time === time) {
            slot.classList.add('selected');
            found = true;
        }
    });
    
    // If we didn't find a matching slot in the list, fetch new slots
    if (!found && datePicker) {
        fetchAvailableTimeSlots(date);
    }
    
    // Update the schedule button state
    const scheduleButton = document.getElementById('submit-reschedule');
    if (scheduleButton) {
        scheduleButton.disabled = false;
    }
    
    // Show selection confirmation
    const selectionConfirmation = document.getElementById('selected-slot-confirmation');
    if (selectionConfirmation) {
        const dateObj = new Date(`${date}T${time}`);
        const form = document.getElementById('reschedule-form');
        // Get doctor info from the form's dataset
        const doctorName = form ? form.dataset.doctorName || 'your doctor' : 'your doctor';
        selectionConfirmation.innerHTML = `
            <div class="selected-slot-info">
                <i class="fas fa-check-circle"></i> 
                Selected: ${dateObj.toLocaleDateString()} at ${dateObj.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})} with ${doctorName}
            </div>
        `;
        selectionConfirmation.style.display = 'block';
    }
}

async function fetchAvailabilityRange(doctorId, startDate, endDate) {
    const errorContainer = document.getElementById('reschedule-error-container');
    try {
        // Format dates in YYYY-MM-DD format
        const formattedStartDate = startDate.toISOString().split('T')[0];
        const formattedEndDate = endDate.toISOString().split('T')[0];
        
        // Show loading message
        if (errorContainer) {
            errorContainer.innerHTML = '<div class="loading-message">Loading doctor availability...</div>';
        }
        
        // Get authentication token
        const token = localStorage.getItem('token');
        if (!token) {
            showErrorMessage("Authentication required. Please log in again.", errorContainer);
            return;
        }
        
        // Log doctor ID for debugging
        console.log(`Fetching availability for doctor ID: ${doctorId}`);
        
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
                // Use default error if JSON parsing fails
            }
            throw new Error(errorText);
        }
        
        const data = await response.json();
        
        // Clear any loading or error messages
        if (errorContainer) {
            errorContainer.innerHTML = '';
        }
        
        // Update the calendar with the availability data
        if (data && data.availability) {
            updateRescheduleCalendarWithAvailability(data.availability);
        }
    } catch (error) {
        showErrorMessage(`Error: ${error.message}`, errorContainer);
    }
}

function updateRescheduleCalendarWithAvailability(availabilityData) {
    if (!window.rescheduleCalendar) {
        return;
    }
    
    // Clear existing events
    window.rescheduleCalendar.getEvents().forEach(event => event.remove());
    
    // Track if we have any available slots
    let hasAvailableSlots = false;
    
    // Process each date in the availability data
    Object.keys(availabilityData).forEach(dateStr => {
        const slots = availabilityData[dateStr];
        
        // Add each slot as an event on the calendar
        slots.forEach(slot => {
            // Skip if no start time
            if (!slot.start) return;
            
            // Extract start and end times
            const [startHour, startMinute] = slot.start.split(':').map(Number);
            const endTime = slot.end || `${(startHour + 1).toString().padStart(2, '0')}:${startMinute.toString().padStart(2, '0')}`;
            
            // Create date objects for the start and end times
            const startDateTime = `${dateStr}T${slot.start}:00`;
            const endDateTime = `${dateStr}T${endTime}:00`;
            
            if (!slot.is_booked) {
                hasAvailableSlots = true;
            }
            
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
    
    // Show message if no available slots
    if (!hasAvailableSlots) {
        const errorContainer = document.getElementById('reschedule-error-container');
        if (errorContainer) {
            errorContainer.innerHTML = '<div class="notice-message">No available slots found in this date range. Try another week.</div>';
        }
    }
}

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
        
        // Extract slots for the selected date
        const slots = availabilityData.availability[date] || [];
        
        // Display time slots
        if (slots.length === 0) {
            timeSlotsContainer.innerHTML = '<p>No available time slots for the selected date. Please choose another date.</p>';
            return;
        }
        
        timeSlotsContainer.innerHTML = '';
        let availableSlotCount = 0;
        
        slots.forEach(slot => {
            if (slot.is_booked) return; // Skip booked slots
            
            availableSlotCount++;
            const timeSlot = document.createElement('div');
            timeSlot.className = 'time-slot';
            timeSlot.dataset.time = slot.start;
            timeSlot.dataset.end = slot.end || '';
            timeSlot.textContent = slot.time || slot.start;
            
            // Check if this slot matches our previously selected time
            if (window.selectedRescheduleTime === slot.start && window.selectedRescheduleDate === date) {
                timeSlot.classList.add('selected');
            }
            
            timeSlot.addEventListener('click', function() {
                // Clear previous selections
                document.querySelectorAll('.time-slot').forEach(ts => ts.classList.remove('selected'));
                
                // Select this slot
                timeSlot.classList.add('selected');
                
                // Store the selected time
                window.selectedRescheduleTime = slot.start;
                window.selectedRescheduleDate = date;
                
                // Highlight the corresponding event in the calendar
                if (window.rescheduleCalendar) {
                    // Reset all events to default color
                    window.rescheduleCalendar.getEvents().forEach(event => {
                        if (event.extendedProps.isAvailable) {
                            event.setProp('backgroundColor', '#1A76D1');
                            event.setProp('borderColor', '#1A76D1');
                        }
                    });
                    
                    // Highlight the matching event
                    window.rescheduleCalendar.getEvents().forEach(event => {
                        if (event.extendedProps.isAvailable && 
                            event.start.toISOString().split('T')[0] === date && 
                            event.start.toTimeString().slice(0, 5) === slot.start) {
                            event.setProp('backgroundColor', '#28a745');
                            event.setProp('borderColor', '#28a745');
                        }
                    });
                }
                
                // Enable the submit button
                const scheduleButton = document.getElementById('submit-reschedule');
                if (scheduleButton) {
                    scheduleButton.disabled = false;
                }
                
                // Show selection confirmation
                const selectionConfirmation = document.getElementById('selected-slot-confirmation');
                if (selectionConfirmation) {
                    const dateObj = new Date(`${date}T${slot.start}`);
                    const form = document.getElementById('reschedule-form');
                    // Get the doctor name from the original appointment
                    const doctorName = form && form.dataset.doctorName 
                        ? form.dataset.doctorName 
                        : 'your doctor';
                    
                    selectionConfirmation.innerHTML = `
                        <div class="selected-slot-info">
                            <i class="fas fa-check-circle"></i> 
                            Selected: ${dateObj.toLocaleDateString()} at ${dateObj.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})} with ${doctorName}
                        </div>
                    `;
                    selectionConfirmation.style.display = 'block';
                }
            });
            
            timeSlotsContainer.appendChild(timeSlot);
        });
        
        if (availableSlotCount === 0) {
            timeSlotsContainer.innerHTML = '<p>No available time slots for the selected date. Please choose another date.</p>';
        }
    } catch (error) {
        showErrorMessage(`Failed to load time slots: ${error.message}`, errorContainer);
    }
}

async function submitReschedule() {
    const form = document.getElementById('reschedule-form');
    const reasonInput = document.getElementById('reschedule-reason');
    const errorContainer = document.getElementById('reschedule-error-container');
    
    if (!form) return;
    
    const appointmentId = form.dataset.appointmentId;
    const doctorName = form.dataset.doctorName;
    let selectedDate, selectedTime;
    
    // Get date and time from our global variables or DOM elements
    if (window.selectedRescheduleDate && window.selectedRescheduleTime) {
        selectedDate = window.selectedRescheduleDate;
        selectedTime = window.selectedRescheduleTime;
    } else if (window.selectedRescheduleTimeSlotData) {
        selectedDate = window.selectedRescheduleTimeSlotData.date;
        selectedTime = window.selectedRescheduleTimeSlotData.start;
    } else {
        const datePicker = document.getElementById('reschedule-date');
        selectedDate = datePicker ? datePicker.value : null;
        
        const selectedTimeSlot = document.querySelector('.time-slot.selected');
        selectedTime = selectedTimeSlot ? selectedTimeSlot.dataset.time : null;
    }
    
    const reason = reasonInput ? reasonInput.value : '';
    
    if (!appointmentId || !selectedDate || !selectedTime) {
        showErrorMessage("Please select a date and time slot", errorContainer);
        return;
    }
    
    try {
        showMessage(`Rescheduling appointment with ${doctorName}...`, 'info');
        
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
        
        // Close the modal
        closeRescheduleModal();
        
        // Show success message
        showMessage('Appointment rescheduled successfully!', 'success');
        
        // Refresh appointments to show updated list
        setTimeout(() => {
            fetchUserAppointments();
        }, 2000);
    } catch (error) {
        showErrorMessage(`Failed to reschedule appointment: ${error.message}`, errorContainer);
    }
}

function showErrorMessage(message, container) {
    if (!container) return;
    
    container.innerHTML = `<div class="error-message">${message}</div>`;
    container.style.display = 'block';
}
