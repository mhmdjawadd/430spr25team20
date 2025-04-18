/**
 * Doctor Calendar Integration
 * Handles fetching doctor appointment data from backend and populating the calendar
 */

// Global calendar instance
let doctorCalendar;

/**
 * Initialize the doctor's calendar
 * @param {string} calendarElementId - The ID of the calendar DOM element
 * @param {Object} calendarOptions - Additional calendar options to merge with defaults
 */
function initDoctorCalendar(calendarElementId = 'calendar', calendarOptions = {}) {
    // Get the calendar element
    const calendarEl = document.getElementById(calendarElementId);
    if (!calendarEl) {
        console.error(`Calendar element with ID '${calendarElementId}' not found`);
        return;
    }

    // Default calendar options
    const defaultOptions = {
        initialView: 'timeGridWeek',
        height: 'auto',
        headerToolbar: { 
            left: 'prev,next today', 
            center: 'title', 
            right: 'timeGridDay,timeGridWeek,dayGridMonth' 
        },
        selectable: true,
        nowIndicator: true,
        businessHours: {
            daysOfWeek: [1, 2, 3, 4, 5], // Monday - Friday
            startTime: '08:00',
            endTime: '18:00',
        },
        eventClick: function(info) {
            // Show appointment details when clicked
            if(info.event.extendedProps.isBooked) {
                const patient = info.event.extendedProps.patientName || info.event.title;
                const type = info.event.extendedProps.type || 'Consultation';
                const notes = info.event.extendedProps.notes || '';
                
                // Build detailed info popup
                let details = `<strong>Patient:</strong> ${patient}<br>`;
                details += `<strong>Type:</strong> ${type}<br>`;
                if (notes) details += `<strong>Notes:</strong> ${notes}<br>`;
                details += `<strong>Time:</strong> ${info.event.start.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})} - ${info.event.end.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}`;
                
                // Use a modal or alert to show the details
                showAppointmentDetails(details, patient);
            }
        },
        eventContent: function(arg) {
            const isBooked = arg.event.extendedProps.isBooked;
            let html = '';
            
            if(isBooked) {
                const patient = arg.event.extendedProps.patientName || arg.event.title;
                html = `<div class="fc-event-main-frame">
                    <div class="fc-event-time">${arg.timeText}</div>
                    <div class="fc-event-title-container">
                        <div class="fc-event-title">${patient}</div>
                        <div class="fc-event-subtitle">${arg.event.extendedProps.type || ''}</div>
                    </div>
                </div>`;
            } else {
                html = `<div class="fc-event-main-frame">
                    <div class="fc-event-time">${arg.timeText}</div>
                    <div class="fc-event-title-container">
                        <div class="fc-event-title">Available</div>
                    </div>
                </div>`;
            }
            
            return { html: html };
        },
        datesSet: function(dateInfo) {
            // When date range changes, fetch new appointment data
            fetchDoctorAppointmentsForRange(
                getCurrentDoctorId(),
                dateInfo.start,
                dateInfo.end
            );
        }
    };

    // Merge custom options with defaults
    const options = { ...defaultOptions, ...calendarOptions };

    // Initialize the calendar
    doctorCalendar = new FullCalendar.Calendar(calendarEl, options);
    doctorCalendar.render();

    // Store the calendar instance globally for external access
    window.doctorCalendar = doctorCalendar;

    // Fetch initial appointments
    fetchDoctorAppointments(getCurrentDoctorId());

    return doctorCalendar;
}

/**
 * Get the current doctor's ID from session storage, localStorage or fallback to default
 * In a real app, this would come from the auth system
 */
function getCurrentDoctorId() {
    return localStorage.getItem('doctorId') || sessionStorage.getItem('doctorId') || '1';
}

/**
 * Get the auth token
 */
function getAuthToken() {
    return localStorage.getItem('token') || sessionStorage.getItem('token');
}

/**
 * Fetch doctor appointments from the backend
 * @param {string} doctorId - The doctor's ID
 */
async function fetchDoctorAppointments(doctorId) {
    try {
        showMessage('Loading appointments...', 'info');
        
        // Get the date range for the current calendar view
        const today = new Date();
        const weekFromNow = new Date(today);
        weekFromNow.setDate(today.getDate() + 7);
        
        // Use current view dates if calendar is initialized
        let start, end;
        if (doctorCalendar) {
            const view = doctorCalendar.view;
            start = formatDateForAPI(view.activeStart);
            end = formatDateForAPI(view.activeEnd);
        } else {
            start = formatDateForAPI(today);
            end = formatDateForAPI(weekFromNow);
        }
        
        // Fetch appointments for the date range
        await fetchDoctorAppointmentsForRange(doctorId, start, end);
        
    } catch (error) {
        console.error('Error in fetchDoctorAppointments:', error);
        showMessage('Failed to load appointments: ' + error.message, 'error');
        
        // Load sample data for demo/testing
        loadSampleAppointments();
    }
}

/**
 * Fetch doctor appointments for a specific date range
 * @param {string} doctorId - The doctor's ID
 * @param {Date|string} start - Start date
 * @param {Date|string} end - End date
 */
async function fetchDoctorAppointmentsForRange(doctorId, start, end) {
    try {
        const token = getAuthToken();
        if (!token) {
            throw new Error('Authentication required. Please log in again.');
        }

        // Format dates if they're Date objects
        const startDate = start instanceof Date ? formatDateForAPI(start) : start;
        const endDate = end instanceof Date ? formatDateForAPI(end) : end;
        
        console.log(`Fetching appointments for doctor ${doctorId} from ${startDate} to ${endDate}`);
        
        // API endpoint for availability range
        const API_URL = 'http://localhost:5000/appointments/availability-range';
        
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                doctor_id: doctorId,
                start_date: startDate,
                end_date: endDate
            })
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Failed to fetch appointments: ${response.status} - ${errorText}`);
        }

        const data = await response.json();
        
        // Clear existing events
        if (doctorCalendar) {
            doctorCalendar.getEvents().forEach(e => e.remove());
        }

        // Process and display the data
        if (data && data.availability) {
            updateCalendarWithAvailability(data.availability);
            showMessage('Appointment schedule loaded', 'success');
        } else {
            console.warn('No availability data in response:', data);
            showMessage('No appointment data available for the selected date range', 'warning');
        }

    } catch (error) {
        console.error('Error fetching appointments for range:', error);
        showMessage(`Error: ${error.message}`, 'error');
        
        // If this is an auth error, redirect to login
        if (error.message.includes('Authentication required') || 
            error.message.includes('token')) {
            handleAuthError();
        }
    }
}

/**
 * Update the calendar with availability data
 * @param {Object} availabilityData - The availability data from the API
 */
function updateCalendarWithAvailability(availabilityData) {
    if (!doctorCalendar) return;
    
    // Process each date in the availability data
    Object.keys(availabilityData).forEach(dateStr => {
        const slots = availabilityData[dateStr];
        
        // Add each slot as an event on the calendar
        slots.forEach(slot => {
            // Skip if no start/end time
            if (!slot.start || !slot.end) return;
            
            const startDateTime = `${dateStr}T${slot.start}`;
            const endDateTime = `${dateStr}T${slot.end}`;
            
            // Determine event title and color based on booking status
            const isBooked = slot.is_booked;
            const title = isBooked ? (slot.patient_name || 'Booked') : 'Available';
            const color = isBooked ? '#e57373' : '#81c784'; // Red for booked, green for available
            
            // Add event to calendar
            doctorCalendar.addEvent({
                title: title,
                start: startDateTime,
                end: endDateTime,
                color: color,
                textColor: '#fff',
                extendedProps: {
                    isBooked: isBooked,
                    patientName: slot.patient_name || '',
                    type: slot.appointment_type || '',
                    notes: slot.notes || ''
                }
            });
        });
    });
    
    // Update appointment list if function exists
    if (typeof renderAppointmentList === 'function') {
        renderAppointmentList();
    }
}

/**
 * Load sample appointment data for testing/demo
 */
function loadSampleAppointments() {
    if (!doctorCalendar) return;
    
    // Clear existing events
    doctorCalendar.getEvents().forEach(e => e.remove());
    
    // Get date range from calendar view
    const view = doctorCalendar.view;
    const startDate = view.activeStart;
    const endDate = view.activeEnd;
    
    // Create a sample availability object
    const availability = {};
    
    // Loop through each day in the range
    const currentDate = new Date(startDate);
    while (currentDate < endDate) {
        const dateStr = formatDateForAPI(currentDate);
        
        // Skip weekends (0 = Sunday, 6 = Saturday)
        if (currentDate.getDay() !== 0 && currentDate.getDay() !== 6) {
            availability[dateStr] = [];
            
            // Create hourly slots from 9 AM to 5 PM
            for (let hour = 9; hour < 17; hour++) {
                // Random booking status (30% chance of being booked)
                const isBooked = Math.random() < 0.3;
                
                // Start and end times
                const startTime = `${hour.toString().padStart(2, '0')}:00:00`;
                const endTime = `${(hour + 1).toString().padStart(2, '0')}:00:00`;
                
                // Create slot object
                const slot = {
                    start: startTime,
                    end: endTime,
                    is_booked: isBooked
                };
                
                // Add patient data if booked
                if (isBooked) {
                    const patients = [
                        'Sarah Johnson',
                        'Michael Brown',
                        'Emma Davis',
                        'William Wilson',
                        'Olivia Martinez'
                    ];
                    
                    const types = [
                        'Follow-up',
                        'Consultation',
                        'New Patient',
                        'Emergency',
                        'Routine Check'
                    ];
                    
                    slot.patient_name = patients[Math.floor(Math.random() * patients.length)];
                    slot.appointment_type = types[Math.floor(Math.random() * types.length)];
                    slot.notes = 'Sample appointment note';
                }
                
                availability[dateStr].push(slot);
            }
        }
        
        // Move to next day
        currentDate.setDate(currentDate.getDate() + 1);
    }
    
    // Update calendar with sample data
    updateCalendarWithAvailability(availability);
    
    console.log('Loaded sample appointment data');
}

/**
 * Format a date for API use (YYYY-MM-DD)
 * @param {Date} date - The date to format
 * @returns {string} Formatted date string
 */
function formatDateForAPI(date) {
    return date.toISOString().split('T')[0];
}

/**
 * Handle authentication error
 */
function handleAuthError() {
    showMessage('Your session has expired. Please log in again.', 'error');
    
    // Redirect to login page after a short delay
    setTimeout(() => {
        window.location.href = '../login.html'; // Adjust path as needed
    }, 3000);
}

/**
 * Show a message to the user
 * @param {string} message - Message text
 * @param {string} type - Message type (info, success, warning, error)
 */
function showMessage(message, type = 'info') {
    // Create message element
    const messageEl = document.createElement('div');
    messageEl.className = `alert alert-${type}`;
    messageEl.style.position = 'fixed';
    messageEl.style.top = '20px';
    messageEl.style.right = '20px';
    messageEl.style.zIndex = '9999';
    messageEl.style.padding = '10px 20px';
    messageEl.style.borderRadius = '4px';
    messageEl.style.boxShadow = '0 4px 8px rgba(0,0,0,0.1)';
    
    // Style based on message type
    switch(type) {
        case 'info':
            messageEl.style.backgroundColor = '#e3f2fd';
            messageEl.style.color = '#0d47a1';
            break;
        case 'success':
            messageEl.style.backgroundColor = '#e8f5e9';
            messageEl.style.color = '#2e7d32';
            break;
        case 'warning':
            messageEl.style.backgroundColor = '#fff3e0';
            messageEl.style.color = '#ef6c00';
            break;
        case 'error':
            messageEl.style.backgroundColor = '#ffebee';
            messageEl.style.color = '#c62828';
            break;
    }
    
    messageEl.textContent = message;
    document.body.appendChild(messageEl);
    
    // Auto-remove after delay
    setTimeout(() => {
        messageEl.remove();
    }, 3000);
}

/**
 * Show appointment details
 * @param {string} detailsHtml - HTML content with appointment details
 * @param {string} patientName - Name of the patient
 */
function showAppointmentDetails(detailsHtml, patientName) {
    // Check if modal exists, create if not
    let modal = document.getElementById('appointmentDetailsModal');
    
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'appointmentDetailsModal';
        modal.className = 'modal';
        modal.style.cssText = 'display:none; position:fixed; inset:0; background:rgba(0,0,0,.45); justify-content:center; align-items:center; z-index:999;';
        
        modal.innerHTML = `
            <div class="modal-content" style="background:#fff; border-radius:16px; width:90%; max-width:450px; box-shadow:0 10px 30px rgba(0,0,0,.2); animation:fadeIn .3s;">
                <div class="modal-header" style="background:#0066cc; color:#fff; padding:15px 20px; border-radius:16px 16px 0 0; display:flex; justify-content:space-between; align-items:center;">
                    <h3 id="appointmentDetailsTitle">Appointment Details</h3>
                    <button class="close-btn" style="background:none; border:none; font-size:24px; color:#fff; cursor:pointer; opacity:.8;" onclick="document.getElementById('appointmentDetailsModal').style.display='none'">&times;</button>
                </div>
                <div id="appointmentDetailsBody" class="modal-body" style="padding:20px;"></div>
                <div class="modal-footer" style="padding:15px 20px; background:#f8f9fa; border-radius:0 0 16px 16px; display:flex; justify-content:flex-end; gap:10px;">
                    <button class="btn-primary" style="background:#0066cc; color:#fff; border:none; padding:8px 16px; border-radius:6px; cursor:pointer;" onclick="document.getElementById('appointmentDetailsModal').style.display='none'">Close</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
    }
    
    // Update modal content
    const title = document.getElementById('appointmentDetailsTitle');
    const body = document.getElementById('appointmentDetailsBody');
    
    if (title) title.textContent = `Appointment with ${patientName}`;
    if (body) body.innerHTML = detailsHtml;
    
    // Show modal
    modal.style.display = 'flex';
}

/**
 * Set doctor ID in storage (for testing/demo)
 * @param {string} doctorId - The doctor ID to set
 */
function setCurrentDoctor(doctorId) {
    localStorage.setItem('doctorId', doctorId);
    console.log(`Current doctor set to ID: ${doctorId}`);
}

/**
 * Format a time string (HH:MM:SS to HH:MM AM/PM)
 * @param {string} timeStr - Time string to format
 * @returns {string} Formatted time
 */
function formatTime(timeStr) {
    if (!timeStr) return '';
    return new Date(`2000-01-01T${timeStr}`).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
}
