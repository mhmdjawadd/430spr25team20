/**
 * Consolidated Appointments System for the Nabad Healthcare Platform
 * Handles all appointment-related functionality including:
 * - Doctor searching and selection
 * - Calendar and time slot management
 * - Appointment booking and confirmation
 */

// Global variables for DOM elements and state
let doctorInputEl;
let doctorSuggestionsEl;
let doctorInfoEl;
let calendarContainer;
let timeSlotContainer;
let timeSlotsEl;
let errorContainer;
let appointmentNotes;
let appointmentType;
let recurring;
let recurringOptions;
let summaryDate;
let summaryTime;
let summaryDoctor;
let summaryDepartment;
let appointmentFormContainer;
let appointmentSuccess;
let successDetails;
let allDoctors = [];
let selectedDoctor = null;
let selectedTimeSlot = null;
let selectedTimeSlotData = null; // Add this new variable to store the raw time slot data
let calendar;

// API base URL
const API_BASE_URL = 'http://localhost:5000';

/**
 * Initialize the appointment page when DOM content is loaded
 */
document.addEventListener('DOMContentLoaded', function() {
    initAppointmentPage();
});

/**
 * Initialize the appointment page
 */
function initAppointmentPage() {
    // Initialize UI elements
    setupUIElements();
    
    // Set up event listeners
    setupEventListeners();
    
    // Initialize calendar if element exists
    initializeCalendar();
    
    // Load doctors on page load
    loadDoctors();
    
    // Check authentication status
    checkAuthStatus();
    
    // Check button connections after a short delay to ensure DOM is loaded
    setTimeout(checkButtonConnections, 2000);
    
    // Add debug button to force show doctor suggestions
    const doctorInput = document.getElementById('doctorInput');
    if (doctorInput) {
        doctorInput.addEventListener('focus', function() {
            if (allDoctors && allDoctors.length > 0) {
                console.log('Doctor input focused, showing all doctors:', allDoctors);
                updateDoctorSuggestions(allDoctors);
            } else {
                console.log('No doctors available to show');
            }
        });
    }
}

/**
 * Set up UI element references
 */
function setupUIElements() {
    // Doctor selection elements
    doctorInputEl = document.getElementById('doctorInput');
    doctorSuggestionsEl = document.getElementById('doctorSuggestions');
    doctorInfoEl = document.getElementById('doctorInfo');
    
    // Calendar and time slot elements
    calendarContainer = document.getElementById('calendarContainer');
    timeSlotContainer = document.getElementById('timeSlotContainer');
    timeSlotsEl = document.getElementById('timeSlots');
    
    // Form and details elements
    appointmentNotes = document.getElementById('appointmentNotes');
    appointmentType = document.getElementById('appointmentType');
    recurring = document.getElementById('recurring');
    recurringOptions = document.getElementById('recurringOptions');
    
    // Summary elements
    summaryDate = document.getElementById('summaryDate');
    summaryTime = document.getElementById('summaryTime');
    summaryDoctor = document.getElementById('summaryDoctor');
    summaryDepartment = document.getElementById('summaryDepartment');
    
    // Success elements
    appointmentFormContainer = document.getElementById('appointmentFormContainer');
    appointmentSuccess = document.getElementById('appointmentSuccess');
    successDetails = document.getElementById('successDetails');
    
    // Error container
    errorContainer = document.getElementById('errorContainer');
}

/**
 * Set up event listeners for interactive elements
 */
function setupEventListeners() {
    // Doctor search
    if (doctorInputEl) {
        doctorInputEl.addEventListener('input', handleDoctorSearch);
        doctorInputEl.addEventListener('focus', function() {
            // Show all doctors when input is focused
            if (allDoctors && allDoctors.length > 0) {
                updateDoctorSuggestions(allDoctors);
                toggleElement(doctorSuggestionsEl, true);
            }
        });
    }
    
    // Handle clicking outside doctor suggestions
    document.addEventListener('click', function(e) {
        if (e.target !== doctorInputEl && e.target !== doctorSuggestionsEl) {
            toggleElement(doctorSuggestionsEl, false);
        }
    });
    
    // Date picker
    const datePickerEl = document.getElementById('datepicker');
    if (datePickerEl) {
        datePickerEl.addEventListener('change', handleDateChange);
        
        // Initialize the datepicker if jQuery is available
        if (typeof $.fn !== 'undefined' && $.fn.datepicker) {
            $(datePickerEl).datepicker({
                format: 'yyyy-mm-dd',
                startDate: new Date(),
                autoclose: true
            });
        }
    }
    
    // Recurring appointment options
    if (recurring) {
        recurring.addEventListener('change', function() {
            toggleElement(recurringOptions, this.checked);
            
            // Update summary
            if (window.summaryRecurringContainer) {
                window.summaryRecurringContainer.style.display = this.checked ? 'flex' : 'none';
                if (window.summaryRecurring) {
                    window.summaryRecurring.textContent = this.checked ? 'Yes' : 'No';
                }
            }
        });
    }
    
    // Caregiver reminders
    const caregiverReminders = document.getElementById('caregiverReminders');
    const caregiverDetails = document.getElementById('caregiverDetails');
    if (caregiverReminders && caregiverDetails) {
        caregiverReminders.addEventListener('change', function() {
            toggleElement(caregiverDetails, this.checked);
        });
    }
    
    // Confirm appointment button - Add direct event listener and console log
    const confirmBtn = document.getElementById('confirmBtn');
    if (confirmBtn) {
        console.log('Found confirm button, adding event listener');
        // Remove any existing event listeners
        confirmBtn.removeEventListener('click', confirmAppointment);
        // Add the event listener
        confirmBtn.addEventListener('click', function(event) {
            console.log('Confirm button clicked!');
            confirmAppointment();
        });
    } else {
        console.error('Confirm button not found in the DOM!');
    }
    
    // Book another appointment button
    const newAppointmentBtn = document.getElementById('newAppointmentBtn');
    if (newAppointmentBtn) {
        newAppointmentBtn.addEventListener('click', resetAppointmentForm);
    }
    
    // Logout button
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', handleLogout);
    }
}


/**
 * Initialize the calendar
 */
function initializeCalendar() {
    const calendarEl = document.getElementById('calendar');
    if (!calendarEl || typeof FullCalendar === 'undefined') return;
    
    calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'timeGridWeek', // Changed to week view by default
        headerToolbar: {
            left: 'prev,next', // Only navigation buttons
            center: 'title',
            right: '' // Removed all view selectors
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
            if (selectedDoctor) {
                // Format date as YYYY-MM-DD
                const clickedDate = info.start.toISOString().split('T')[0];
                
                // Format time as HH:MM
                const clickedTime = info.start.toTimeString().slice(0, 5);
                
                selectTimeSlot(clickedDate, clickedTime);
            } else {
                showMessage('Please select a doctor first', 'warning');
            }
        },
        eventClick: function(info) {
            const eventData = info.event.extendedProps;
            
            // Only allow selecting available slots
            if (eventData.isAvailable) {
                // Clear previous selected events styling
                calendar.getEvents().forEach(event => {
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
                selectTimeSlot(eventDate, eventTime);
                
                // Store direct data from the event
                selectedTimeSlotData = {
                    date: eventDate,
                    start: eventTime,
                    end: info.event.end ? info.event.end.toTimeString().slice(0, 5) : 
                        `${parseInt(eventTime.split(':')[0]) + 1}:${eventTime.split(':')[1]}`
                };
                
                console.log("Selected time slot data from calendar:", selectedTimeSlotData);
            }
        },
        datesSet: function(dateInfo) {
            console.log(`View dates: ${dateInfo.startStr} to ${dateInfo.endStr}`);
            const viewDescriptionEl = document.getElementById('viewDescription');
            
            if (viewDescriptionEl) {
                // Only show week view description since we've removed other views
                viewDescriptionEl.innerHTML = 'Week view: Get an overview of available slots throughout the week.';
            }
            
            // Only fetch range data if we have a selected doctor
            if (selectedDoctor) {
                // Always fetch for the entire visible range
                fetchAvailabilityRange(selectedDoctor.id, dateInfo.start, dateInfo.end);
            }
        }
    });
    
    calendar.render();
}

/**
 * Load doctors from the API
 */
async function loadDoctors() {
    try {
        showMessage('Loading doctors...', 'info');
        
        const API_URL = `${API_BASE_URL}/doctors`;
        const response = await fetch(API_URL, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            mode: 'cors',
            cache: 'no-cache',
            credentials: 'same-origin'
        });
        
        if (response.ok) {
            const doctorsData = await response.json();
            
            // Store doctors globally
            allDoctors = Array.isArray(doctorsData) ? doctorsData : 
                           (doctorsData.doctors || []);
            
            if (allDoctors.length > 0) {
                showMessage(`${allDoctors.length} doctors loaded successfully.`, 'success');
                
                // Show doctors in suggestions dropdown
                if (doctorSuggestionsEl) {
                    updateDoctorSuggestions(allDoctors);
                    // Make sure the suggestions are visible initially
                    toggleElement(doctorSuggestionsEl, true);
                }
            } else {
                showMessage('No doctors found. Please try again later.', 'warning');
            }
        } else {
            showMessage(`Failed to load doctors: ${response.status} ${response.statusText}`, 'error');
        }
    } catch (error) {
        console.error('Error loading doctors:', error);
        showMessage(`Error loading doctors: ${error.message}`, 'error');
    }
}

/**
 * Handle doctor search input
 */
function handleDoctorSearch() {
    const searchText = doctorInputEl.value.toLowerCase().trim();
    
    if (searchText.length > 0) {
        // Filter doctors based on search text
        const filteredDoctors = allDoctors.filter(doctor => {
            const fullName = `${doctor.first_name} ${doctor.last_name}`.toLowerCase();
            return fullName.includes(searchText) || 
                   doctor.specialty.toLowerCase().includes(searchText);
        });
        
        // Update and show suggestions
        updateDoctorSuggestions(filteredDoctors);
        toggleElement(doctorSuggestionsEl, true);
    } else {
        // Show all doctors when search text is empty
        updateDoctorSuggestions(allDoctors);
        toggleElement(doctorSuggestionsEl, true);
    }
}

/**
 * Update doctor suggestions dropdown
 */
function updateDoctorSuggestions(doctors) {
    // Clear previous results
    doctorSuggestionsEl.innerHTML = '';
    
    if (doctors.length === 0) {
        const noResults = document.createElement('div');
        noResults.className = 'doctor-search-item';
        noResults.textContent = 'No doctors found';
        doctorSuggestionsEl.appendChild(noResults);
    } else {
        console.log('Updating doctor suggestions with:', doctors);
        // Add each doctor to the dropdown
        doctors.forEach(doctor => {
            const resultItem = document.createElement('div');
            resultItem.className = 'doctor-search-item';
            resultItem.dataset.id = doctor.id || doctor.doctor_id; // Handle different API response formats
            
            const doctorName = document.createElement('span');
            doctorName.className = 'doctor-name';
            doctorName.textContent = `Dr. ${doctor.first_name} ${doctor.last_name}`;
            
            const doctorSpecialty = document.createElement('span');
            doctorSpecialty.className = 'doctor-specialty';
            doctorSpecialty.textContent = doctor.specialty || doctor.specialization || '';
            
            resultItem.appendChild(doctorName);
            resultItem.appendChild(doctorSpecialty);
            
            // Add click handler to select this doctor
            resultItem.addEventListener('click', function() {
                selectDoctorDirectly(doctor);
            });
            
            doctorSuggestionsEl.appendChild(resultItem);
        });
    }
    
    // Make sure the suggestions container is visible
    toggleElement(doctorSuggestionsEl, true);
}

/**
 * Handle date change event
 */
function handleDateChange() {
    const datePickerEl = document.getElementById('datepicker');
    if (!datePickerEl) return;
    
    const selectedDate = datePickerEl.value;
    
    if (!selectedDate) {
        clearTimeSlots();
        return;
    }
    
    // If doctor is selected, fetch availability for this date
    if (selectedDoctor) {
        fetchAvailability(selectedDoctor.id, selectedDate);
    }
    
    // Update summary
    updateSummary();
}

/**
 * Select a doctor directly
 */
function selectDoctorDirectly(doctor) {
    console.log('Selecting doctor directly:', doctor);
    
    // Store selected doctor
    selectedDoctor = doctor;
    
    // Update input field
    if (doctorInputEl) {
        doctorInputEl.value = `Dr. ${doctor.first_name} ${doctor.last_name}`;
    }
    
    // Update doctor info display
    if (doctorInfoEl) {
        const doctorNameEl = doctorInfoEl.querySelector('.doctor-name');
        const doctorSpecialtyEl = doctorInfoEl.querySelector('.doctor-specialty');
        
        if (doctorNameEl) {
            doctorNameEl.textContent = `Dr. ${doctor.first_name} ${doctor.last_name}`;
        }
        
        if (doctorSpecialtyEl) {
            doctorSpecialtyEl.textContent = `(${doctor.specialty})`;
        }
        
        // Show doctor info
        toggleElement(doctorInfoEl, true);
    }
    
    // Hide suggestions
    toggleElement(doctorSuggestionsEl, false);
    
    // Show calendar
    toggleElement(calendarContainer, true);
    
    // Show time slot container
    toggleElement(timeSlotContainer, true);
    
    // Fetch and display insurance information
    fetchInsuranceInformation(doctor.id);
    
    // Update summary
    updateSummary();
    
    // Display confirmation message
    showMessage(`Doctor selected: Dr. ${doctor.first_name} ${doctor.last_name}`, 'success');
    
    // Make a direct API call to get the doctor's availability
    if (calendar) {
        const view = calendar.view;
        
        // Load availability with a slight delay to ensure the DOM updates first
        setTimeout(() => {
            fetchAvailabilityRange(
                doctor.id,
                view.activeStart,
                view.activeEnd
            );
        }, 100);
    }
}

/**
 * Fetch insurance information for the selected doctor
 */
async function fetchInsuranceInformation(doctorId) {
    const insuranceInfoContainer = document.getElementById('insuranceInfoContainer');
    const insuranceDetails = document.getElementById('insuranceDetails');
    
    if (!insuranceInfoContainer || !insuranceDetails) {
        console.error('Insurance information container not found in DOM');
        return;
    }
    
    try {
        // Show loading message
        insuranceDetails.innerHTML = '<p>Loading insurance information...</p>';
        insuranceInfoContainer.style.display = 'block';
        
        // Get authentication token
        const token = localStorage.getItem('token');
        if (!token) {
            insuranceDetails.innerHTML = '<p>Please log in to view insurance information.</p>';
            return;
        }
        
        // Call the insurance verification endpoint
        const response = await fetch(`${API_BASE_URL}/insurance/verify`, {
            method: 'POST',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                doctor_id: doctorId
            })
        });
        
        if (!response.ok) {
            if (response.status === 404) {
                // No insurance record found
                insuranceDetails.innerHTML = `
                    <div class="alert alert-warning mb-0">
                        <strong>No insurance record found.</strong> 
                        <p>You will be responsible for the full appointment cost of $100.00.</p>
                        <p>To add insurance information, please update your profile.</p>
                    </div>
                `;
            } else {
                // Other API errors
                try {
                    const errorData = await response.json();
                    insuranceDetails.innerHTML = `
                        <div class="alert alert-danger mb-0">
                            <p>${errorData.error || 'Failed to verify insurance coverage'}</p>
                        </div>
                    `;
                } catch (e) {
                    insuranceDetails.innerHTML = `
                        <div class="alert alert-danger mb-0">
                            <p>Failed to verify insurance coverage: ${response.statusText}</p>
                        </div>
                    `;
                }
            }
            return;
        }
        
        // Parse the insurance data - using the correct structure
        const insuranceData = await response.json();
        console.log("Insurance verification response:", insuranceData);
        
        // Check if user has insurance and it's covered
        if (insuranceData.has_insurance && insuranceData.is_covered) {
            // Extract coverage details from the correct field
            const coverageDetails = insuranceData.coverage_details || {};
            const coveredAmount = coverageDetails.covered_amount || 0;
            const patientResponsibility = coverageDetails.patient_responsibility || 100;
            const baseCost = coverageDetails.base_cost || 100;
            const coveragePercent = coverageDetails.coverage_percent || '0%';
            const coverageType = coverageDetails.coverage_type || 'NONE';
            
            // Format the verified insurance information
            insuranceDetails.innerHTML = `
                <div class="alert alert-success mb-0">
                    <strong>Insurance Verification Complete</strong>
                    <p>${insuranceData.message}</p>
                    <div class="insurance-details mt-2">
                        <div class="row">
                            <div class="col-md-6">
                                <p><strong>Coverage Type:</strong> ${coverageType}</p>
                                <p><strong>Coverage Amount:</strong> $${coveredAmount.toFixed(2)}</p>
                            </div>
                            <div class="col-md-6">
                                <p><strong>Coverage Level:</strong> ${coveragePercent}</p>
                                <p><strong>Your Responsibility:</strong> $${patientResponsibility.toFixed(2)}</p>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        } else {
            // Insurance not verified or not covered
            insuranceDetails.innerHTML = `
                <div class="alert alert-warning mb-0">
                    <strong>Insurance Not Verified</strong>
                    <p>${insuranceData.message || 'Your insurance may not cover this appointment.'}</p>
                    <p>Estimated cost: $100.00</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error fetching insurance information:', error);
        insuranceDetails.innerHTML = `
            <div class="alert alert-danger mb-0">
                <p>Failed to load insurance information: ${error.message}</p>
            </div>
        `;
    }
}

/**
 * Fetch doctor availability for a specific date
 */
async function fetchAvailability(doctorId, date) {
    try {
        showMessage(`Loading availability for date: ${date}...`, 'info');
        
        const url = `${API_BASE_URL}/appointments/timeslots?doctor_id=${doctorId}&date=${date}`;
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error(`Failed to fetch time slots: ${response.status}`);
        }
        
        const timeSlots = await response.json();
        
        // Update time slots display
        updateTimeSlots(timeSlots);
        
        // Update calendar with availability
        updateCalendarWithAvailability(timeSlots, date);
        
        showMessage(`Availability loaded for ${date}`, 'success');
    } catch (error) {
        console.error('Error fetching availability:', error);
        showMessage(`Error loading availability: ${error.message}`, 'error');
    }
}

/**
 * Fetch doctor availability for a date range
 */
async function fetchAvailabilityRange(doctorId, startDate, endDate) {
    try {
        const messageEl = document.createElement('div');
        messageEl.className = 'alert alert-info mb-0';
        messageEl.textContent = `Fetching availability for doctor: ${doctorId} from: ${startDate.toISOString().split('T')[0]} to: ${endDate.toISOString().split('T')[0]}`;
        errorContainer.innerHTML = '';
        errorContainer.appendChild(messageEl);
        
        // Format dates in YYYY-MM-DD format
        const formattedStartDate = startDate.toISOString().split('T')[0];
        const formattedEndDate = endDate.toISOString().split('T')[0];
        
        // Make API request
        const response = await fetch(`${API_BASE_URL}/appointments/availability-range`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
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
            updateCalendarWithAvailabilityData(data.availability);
            
            // Update success message
            messageEl.className = 'alert alert-success mb-0';
            messageEl.textContent = `Successfully loaded availability for Dr. ${selectedDoctor.first_name} ${selectedDoctor.last_name}`;
            setTimeout(() => {
                messageEl.remove();
            }, 3000);
        }
    } catch (error) {
        console.error('Error fetching availability range:', error);
        const messageEl = document.createElement('div');
        messageEl.className = 'alert alert-danger mb-0';
        messageEl.textContent = `Error: ${error.message}`;
        errorContainer.innerHTML = '';
        errorContainer.appendChild(messageEl);
    }
}

/**
 * Update calendar with availability data
 */
function updateCalendarWithAvailabilityData(availabilityData) {
    if (!calendar) return;
    
    // Clear existing events
    calendar.getEvents().forEach(event => event.remove());
    
    // Process each date in the availability data
    Object.keys(availabilityData).forEach(dateStr => {
        const slots = availabilityData[dateStr];
        
        // Add each slot as an event on the calendar
        slots.forEach(slot => {
            // Skip if no start/end time
            if (!slot.start || !slot.end) return;
            
            // Extract start and end times
            const [startHour, startMinute] = slot.start.split(':').map(Number);
            const [endHour, endMinute] = slot.end ? slot.end.split(':').map(Number) : [startHour + 1, startMinute];
            
            // Create date objects for the start and end times
            const startDateTime = `${dateStr}T${startHour.toString().padStart(2, '0')}:${startMinute.toString().padStart(2, '0')}:00`;
            const endDateTime = `${dateStr}T${endHour.toString().padStart(2, '0')}:${endMinute.toString().padStart(2, '0')}:00`;
            
            // Add event to calendar
            calendar.addEvent({
                title: slot.is_booked ? 'Booked' : 'Available',
                start: startDateTime,
                end: endDateTime,
                color: slot.is_booked ? '#ccc' : '#1A76D1',
                textColor: slot.is_booked ? '#666' : '#fff',
                extendedProps: {
                    isAvailable: !slot.is_booked,
                    time: slot.time || `${startHour}:${startMinute} - ${endHour}:${endMinute}`
                }
            });
        });
    });
}

/**
 * Update calendar with availability for a specific date
 */
function updateCalendarWithAvailability(slots, date) {
    if (!calendar) return;
    
    // Remove all events for this date
    const events = calendar.getEvents();
    events.forEach(event => {
        const eventDate = event.start.toISOString().split('T')[0];
        if (eventDate === date) {
            event.remove();
        }
    });
    
    // Add new events based on the slots
    slots.forEach(slot => {
        // Skip if no start time
        if (!slot.start) return;
        
        // Extract start and end times
        const [startHour, startMinute] = slot.start.split(':').map(Number);
        const endTime = slot.end || `${(startHour + 1).toString().padStart(2, '0')}:${startMinute.toString().padStart(2, '0')}`;
        
        // Create date objects for the start and end times
        const startDateTime = `${date}T${slot.start}:00`;
        const endDateTime = `${date}T${endTime}:00`;
        
        // Add event to calendar
        calendar.addEvent({
            title: slot.is_booked ? 'Booked' : 'Available',
            start: startDateTime,
            end: endDateTime,
            color: slot.is_booked ? '#ccc' : '#1A76D1',
            textColor: slot.is_booked ? '#666' : '#fff',
            extendedProps: {
                isAvailable: !slot.is_booked,
                time: `${slot.start} - ${endTime}`
            }
        });
    });
    
    // Go to the date on the calendar
    calendar.gotoDate(date);
}

/**
 * Update time slots display
 */
function updateTimeSlots(slots) {
    timeSlotsEl.innerHTML = '';
    
    if (!slots || slots.length === 0) {
        timeSlotsEl.innerHTML = '<p>No available time slots for the selected date.</p>';
        return;
    }
    
    slots.forEach(slot => {
        const timeSlot = document.createElement('div');
        timeSlot.className = 'time-slot';
        timeSlot.dataset.start = slot.start;
        timeSlot.dataset.end = slot.end || '';
        
        // Check if slot is booked
        if (slot.is_booked) {
            timeSlot.className += ' booked';
            timeSlot.textContent = `${slot.start} - Booked`;
        } else {
            timeSlot.textContent = slot.start;
            
            // Add click handler for available slots
            timeSlot.addEventListener('click', function() {
                // Clear previous selections
                document.querySelectorAll('.time-slot').forEach(el => {
                    el.classList.remove('selected');
                });
                
                // Mark this slot as selected
                timeSlot.classList.add('selected');
                
                // Store both the element and the data
                selectedTimeSlot = timeSlot;
                selectedTimeSlotData = {
                    date: calendar.getDate().toISOString().split('T')[0],
                    start: slot.start,
                    end: slot.end || `${parseInt(slot.start.split(':')[0]) + 1}:${slot.start.split(':')[1]}`
                };
                
                console.log("Time slot selected from list:", selectedTimeSlotData);
                
                // Update summary - use the current date from selectedTimeSlotData since we're only in week view
                updateSummary(selectedTimeSlotData.date, slot.start);
            });
        }
        
        timeSlotsEl.appendChild(timeSlot);
    });
}

/**
 * Clear time slots
 */
function clearTimeSlots() {
    if (timeSlotsEl) {
        timeSlotsEl.innerHTML = '<p>Please select a date and doctor first.</p>';
    }
}

/**
 * Select a time slot
 */
function selectTimeSlot(date, time) {
    console.log(`Selecting time slot: date=${date}, time=${time}`);
    
    // First try to find the time slot in the displayed list
    const timeSlotEl = document.querySelector(`.time-slot[data-start="${time}"]`);
    console.log("Found time slot element:", timeSlotEl);
    
    if (timeSlotEl && !timeSlotEl.classList.contains('booked')) {
        // Clear previous selections
        document.querySelectorAll('.time-slot').forEach(el => {
            el.classList.remove('selected');
        });
        
        // Mark this slot as selected
        timeSlotEl.classList.add('selected');
        
        // Store selected time slot
        selectedTimeSlot = timeSlotEl;
        console.log("Time slot selected and stored from element:", selectedTimeSlot);
    } else {
        // If we couldn't find a matching element, create a virtual selection
        // This handles cases where the calendar was clicked but no matching element exists
        console.log("Creating virtual time slot selection since element not found in list");
        
        // Store the selection data even if we don't have a DOM element
        selectedTimeSlotData = {
            date: date,
            start: time,
            end: `${parseInt(time.split(':')[0]) + 1}:${time.split(':')[1]}`
        };
        
        console.log("Virtual time slot data stored:", selectedTimeSlotData);
    }
    
    // Update summary regardless of which path we took
    updateSummary(date, time);
}

/**
 * Update appointment summary
 */
function updateSummary(date, time) {
    if (summaryDate && date) {
        // Format date for display (YYYY-MM-DD to readable format)
        const formattedDate = new Date(date).toLocaleDateString();
        summaryDate.textContent = formattedDate;
    }
    
    if (summaryTime && time) {
        summaryTime.textContent = time;
    }
    
    if (summaryDoctor && selectedDoctor) {
        summaryDoctor.textContent = `Dr. ${selectedDoctor.first_name} ${selectedDoctor.last_name}`;
    }
    
    if (summaryDepartment && selectedDoctor) {
        summaryDepartment.textContent = selectedDoctor.specialty;
    }
    
    // Update recurring info if applicable
    if (window.summaryRecurringContainer && recurring) {
        window.summaryRecurringContainer.style.display = recurring.checked ? 'flex' : 'none';
        if (window.summaryRecurring) {
            window.summaryRecurring.textContent = recurring.checked ? 'Yes' : 'No';
        }
    }
}

/**
 * Confirm appointment - Fixed version
 */
async function confirmAppointment() {
    try {
        console.log("Starting confirmAppointment function");
        
        // Get the selected date from selectedTimeSlotData since we're only showing week view
        let selectedDate;
        
        if (selectedTimeSlotData && selectedTimeSlotData.date) {
            selectedDate = selectedTimeSlotData.date;
        } else {
            // Fallback to getting date from calendar
            selectedDate = calendar.getDate().toISOString().split('T')[0];
        }
        
        console.log("Selected date:", selectedDate);
        
        // Validate required fields
        if (!selectedDate) {
            showMessage('Please select a date.', 'error');
            return;
        }
        
        if (!selectedDoctor) {
            showMessage('Please select a doctor.', 'error');
            doctorInputEl.focus();
            return;
        }
        
        // Get the selected time either from DOM element or from stored data
        let selectedTime;
        let selectedTimeSlotElement = document.querySelector('.time-slot.selected');
        
        // First try to get from the DOM
        if (selectedTimeSlotElement) {
            selectedTime = selectedTimeSlotElement.dataset.start;
            console.log("Selected time from DOM element:", selectedTime);
        } 
        // If not found in DOM, try the stored data
        else if (selectedTimeSlotData) {
            selectedTime = selectedTimeSlotData.start;
            console.log("Selected time from stored data:", selectedTime);
        } 
        // No time slot selected
        else {
            showMessage('Please select a time slot.', 'error');
            return;
        }
        
        if (!selectedTime) {
            showMessage('Invalid time slot selection.', 'error');
            return;
        }
        
        console.log("Selected doctor:", selectedDoctor);
        console.log("Final selected time:", selectedTime);
        
        // Format the appointment data
        const appointmentData = {
            doctor_id: selectedDoctor.id,
            date_time: `${selectedDate}-${selectedTime.split(':')[0]}`,
            appointment_type: "REGULAR",
            notes: appointmentNotes.value || ''
        };
        
        // Add recurring appointment details if enabled
        if (recurring && recurring.checked) {
            const recurrencePattern = document.getElementById('recurrencePattern');
            const sessions = document.getElementById('sessions');
            
            if (recurrencePattern && sessions) {
                appointmentData.recurrence_pattern = recurrencePattern.value;
                appointmentData.recurrence_count = parseInt(sessions.value, 10);
            }
        }
        
        // Add caregiver notification preferences if configured
        const smsToCaregiverReminder = document.getElementById('smsToCaregiverReminder');
        const emailToCaregiverReminder = document.getElementById('emailToCaregiverReminder');
        const caregiverPhone = document.getElementById('caregiverPhone');
        const caregiverEmail = document.getElementById('caregiverEmail');
        
        if (smsToCaregiverReminder && smsToCaregiverReminder.checked && caregiverPhone && caregiverPhone.value) {
            appointmentData.caregiver_sms = true;
            appointmentData.caregiver_phone = caregiverPhone.value;
        }
        
        if (emailToCaregiverReminder && emailToCaregiverReminder.checked && caregiverEmail && caregiverEmail.value) {
            appointmentData.caregiver_email = true;
            appointmentData.caregiver_email_address = caregiverEmail.value;
        }
        
        console.log("Final appointment data being sent:", JSON.stringify(appointmentData, null, 2));
        
        showMessage('Booking appointment...', 'info');
        
        // Get authentication token
        const token = localStorage.getItem('token');
        if (!token) {
            throw new Error('Authentication required. Please log in again.');
        }
        
        // Call booking API
        const API_URL = `${API_BASE_URL}/appointments`;
        
        console.log(`Sending POST request to ${API_URL}`);
        console.log(`Authorization: Bearer ${token.substring(0, 10)}...`);
        
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(appointmentData)
        });
        
        console.log(`Response status: ${response.status} ${response.statusText}`);
        
        // Parse response - log the raw response first
        const responseText = await response.text();
        console.log("Raw response:", responseText);
        
        // Try to parse as JSON
        let responseData;
        try {
            responseData = JSON.parse(responseText);
            console.log("Parsed response data:", responseData);
        } catch (e) {
            console.error("Could not parse response as JSON:", e);
            throw new Error("Invalid response from server");
        }
        
        if (!response.ok) {
            throw new Error(responseData.error || responseData.message || 'Failed to book appointment');
        }
        
        console.log('Appointment booked successfully!');
        
        // Show success message
        showMessage('Appointment booked successfully!', 'success');
        
        // Hide form and show success message
        if (appointmentFormContainer) {
            appointmentFormContainer.style.display = 'none';
        }
        
        if (appointmentSuccess) {
            appointmentSuccess.style.display = 'block';
            
            // Format success details
            let successText = `Your appointment with Dr. ${selectedDoctor.first_name} ${selectedDoctor.last_name} on ${new Date(selectedDate).toLocaleDateString()} at ${selectedTime} has been confirmed.`;
            
            // Add appointment ID for reference
            if (responseData.appointment_id) {
                successText += `<br><br>Appointment ID: ${responseData.appointment_id}`;
            }
            
            // Add recurring appointment details if applicable
            if (responseData.recurring_appointments) {
                successText += `<br><br>This is a recurring appointment. ${responseData.recurring_appointments.count} additional appointments have been scheduled.`;
            }
            
            // Add insurance information if available
            if (responseData.insurance) {
                successText += `<br><br>Insurance information: ${responseData.insurance.message}`;
            }
            
            if (successDetails) {
                successDetails.innerHTML = successText;
            }
        }
    } catch (error) {
        console.error('Error booking appointment:', error);
        showMessage('Failed to book appointment: ' + error.message, 'error');
    }
}

/**
 * Reset the appointment form
 */
function resetAppointmentForm() {
    // Reset form elements
    if (doctorInputEl) doctorInputEl.value = '';
    if (appointmentNotes) appointmentNotes.value = '';
    if (appointmentType) appointmentType.value = 'REGULAR';
    if (recurring) recurring.checked = false;
    
    // Reset selections
    selectedDoctor = null;
    selectedTimeSlot = null;
    selectedTimeSlotData = null;
    
    // Reset UI
    toggleElement(doctorInfoEl, false);
    toggleElement(calendarContainer, false);
    toggleElement(timeSlotContainer, false);
    toggleElement(recurringOptions, false);
    
    // Reset summary
    if (summaryDate) summaryDate.textContent = 'Not selected';
    if (summaryTime) summaryTime.textContent = 'Not selected';
    if (summaryDoctor) summaryDoctor.textContent = 'Not selected';
    if (summaryDepartment) summaryDepartment.textContent = 'Not selected';
    
    // Show form and hide success message
    if (appointmentFormContainer) {
        appointmentFormContainer.style.display = 'block';
    }
    
    if (appointmentSuccess) {
        appointmentSuccess.style.display = 'none';
    }
    
    // Clear any messages
    errorContainer.innerHTML = '';
}

/**
 * Check authentication status
 */
function checkAuthStatus() {
    const token = localStorage.getItem('token');
    const userGreeting = document.getElementById('userGreeting');
    
    if (token) {
        // User is logged in, display greeting
        const username = localStorage.getItem('username') || 'User';
        if (userGreeting) {
            userGreeting.textContent = `Hi, ${username}`;
        }
    } else {
        // User is not logged in, redirect to login page
        showMessage('Please log in to access appointments', 'warning');
        setTimeout(() => {
            window.location.href = 'login.html';
        }, 3000);
    }
}

/**
 * Handle logout
 */
function handleLogout() {
    if (confirm('Are you sure you want to logout?')) {
        // Clear token and user data
        localStorage.removeItem('token');
        localStorage.removeItem('username');
        
        // Show message and redirect
        showMessage('Logging out...', 'info');
        setTimeout(() => {
            window.location.href = 'login.html';
        }, 1000);
    }
}

/**
 * Toggle element visibility
 */
function toggleElement(element, show) {
    if (!element) return;
    
    if (show) {
        element.classList.remove('hidden');
    } else {
        element.classList.add('hidden');
    }
}

/**
 * Show a message to the user
 */
function showMessage(message, type = 'info') {
    if (!errorContainer) return;
    
    const messageEl = document.createElement('div');
    messageEl.className = `alert alert-${type} mb-0`;
    messageEl.textContent = message;
    
    // Clear previous messages and add new one
    errorContainer.innerHTML = '';
    errorContainer.appendChild(messageEl);
    
    // Auto-dismiss success and info messages after 3 seconds
    if (type === 'success' || type === 'info') {
        setTimeout(() => {
            messageEl.remove();
        }, 3000);
    }
}