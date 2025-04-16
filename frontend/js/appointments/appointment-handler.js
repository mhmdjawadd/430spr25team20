/**
 * Appointment handler for the Nabad healthcare platform
 * Manages the appointment booking UI interactions
 */

import { getAllDoctors, getAvailableDoctors, getAvailableTimeSlots, bookAppointment } from './appointment-api.js';

// DOM elements
const datePickerEl = document.getElementById('datepicker');
const doctorSelectEl = document.getElementById('doctorSelect');
const doctorSelectionMessage = document.getElementById('doctorSelectionMessage');
const timeSlotsContainer = document.getElementById('timeSlots');
const appointmentNotesEl = document.getElementById('appointmentNotes');
const errorContainer = document.getElementById('errorContainer');

// Summary elements
const summaryDateEl = document.getElementById('summaryDate');
const summaryTimeEl = document.getElementById('summaryTime');
const summaryDoctorEl = document.getElementById('summaryDoctor');
const summaryDepartmentEl = document.getElementById('summaryDepartment');

// For nav tabs
const tabButtons = document.querySelectorAll('[data-step-nav]');

// Selected values
let selectedTimeSlot = null;
let selectedDoctor = null;

/**
 * Initialize the appointment handler
 */
function initAppointmentHandler() {
    console.log('initAppointmentHandler called');
    
    // Initialize datepicker if jQuery and the element exist
    if (datePickerEl && typeof $.fn.datepicker !== 'undefined') {
        console.log('Initializing datepicker');
        $(datePickerEl).datepicker({
            format: 'yyyy-mm-dd',
            startDate: new Date(),
            autoclose: true
        });
    } else {
        console.warn('datePickerEl not found or datepicker not available:', datePickerEl, typeof $.fn.datepicker);
    }

    // Add event listeners
    if (datePickerEl) {
        datePickerEl.addEventListener('change', handleDateChange);
    }
    
    if (doctorSelectEl) {
        doctorSelectEl.addEventListener('change', handleDoctorChange);
        console.log('Added change event listener to doctorSelect:', doctorSelectEl);
    } else {
        console.warn('doctorSelectEl not found in DOM during initialization');
    }
    
    // Add event listeners for tab navigation
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            const step = this.getAttribute('data-step-nav');
            activateTab(step);
        });
    });
    
    // Recurring appointment checkbox
    const recurringCheckbox = document.getElementById('recurring');
    const recurringOptions = document.getElementById('recurringOptions');
    if (recurringCheckbox && recurringOptions) {
        recurringCheckbox.addEventListener('change', function() {
            recurringOptions.style.display = this.checked ? 'block' : 'none';
            
            // Update summary
            const summaryRecurringContainer = document.getElementById('summaryRecurringContainer');
            const summaryRecurring = document.getElementById('summaryRecurring');
            if (summaryRecurringContainer && summaryRecurring) {
                summaryRecurringContainer.style.display = this.checked ? 'flex' : 'none';
                summaryRecurring.textContent = this.checked ? 
                    document.querySelector('select[name="recurrence_pattern"]').value : 'No';
            }
        });
    }
    
    // Caregiver reminders checkbox
    const caregiverRemindersCheckbox = document.getElementById('caregiverReminders');
    const caregiverDetails = document.getElementById('caregiverDetails');
    if (caregiverRemindersCheckbox && caregiverDetails) {
        caregiverRemindersCheckbox.addEventListener('change', function() {
            caregiverDetails.style.display = this.checked ? 'block' : 'none';
        });
    }
    
    // Confirm appointment button
    const confirmBtn = document.getElementById('confirmBtn');
    if (confirmBtn) {
        confirmBtn.addEventListener('click', confirmAppointment);
    }
    
    // New appointment button
    const newAppointmentBtn = document.getElementById('newAppointmentBtn');
    if (newAppointmentBtn) {
        newAppointmentBtn.addEventListener('click', resetAppointmentForm);
    }
    
    // Load all doctors when the page loads
    console.log('About to call loadAllDoctors()');
    loadAllDoctors();
}

/**
 * Activate a specific tab
 * @param {string} stepNumber - The step number to activate
 */
function activateTab(stepNumber) {
    // First hide all tabs
    document.querySelectorAll('.tab-pane').forEach(tab => {
        tab.classList.remove('active', 'show');
        tab.classList.add('fade');
    });
    
    // Then show the selected tab
    const selectedTab = document.getElementById(`step${stepNumber}`);
    if (selectedTab) {
        selectedTab.classList.add('active', 'show');
        selectedTab.classList.remove('fade');
    }
    
    // Update the tab navigation
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    
    const navLink = document.querySelector(`.nav-link[href="#step${stepNumber}"]`);
    if (navLink) {
        navLink.classList.add('active');
    }
    
    // Update summary if going to confirmation step
    if (stepNumber === '3') {
        updateSummary();
    }
}

/**
 * Update the appointment summary
 */
function updateSummary() {
    if (summaryDateEl) summaryDateEl.textContent = datePickerEl.value || 'Not selected';
    
    if (summaryTimeEl && selectedTimeSlot) 
        summaryTimeEl.textContent = selectedTimeSlot.textContent || 'Not selected';
    
    if (summaryDoctorEl && selectedDoctor) 
        summaryDoctorEl.textContent = `${selectedDoctor.first_name} ${selectedDoctor.last_name}` || 'Not selected';
    
    if (summaryDepartmentEl && selectedDoctor) 
        summaryDepartmentEl.textContent = selectedDoctor.specialty || 'Not selected';
    
    // Update recurring info if applicable
    const recurringCheckbox = document.getElementById('recurring');
    const summaryRecurringContainer = document.getElementById('summaryRecurringContainer');
    const summaryRecurring = document.getElementById('summaryRecurring');
    
    if (recurringCheckbox && summaryRecurringContainer && summaryRecurring) {
        summaryRecurringContainer.style.display = recurringCheckbox.checked ? 'flex' : 'none';
        if (recurringCheckbox.checked) {
            const pattern = document.querySelector('select[name="recurrence_pattern"]').value;
            const sessions = document.querySelector('input[name="sessions"]').value;
            summaryRecurring.textContent = `${pattern}, ${sessions} sessions`;
        } else {
            summaryRecurring.textContent = 'No';
        }
    }
}

/**
 * Load all doctors from the database
 */
async function loadAllDoctors() {
    try {
        // Show loading message
        showMessage('Loading all doctors...', 'info');
        
        // Get all doctors from the database
        const doctors = await getAllDoctors();
        
        if (doctors.length === 0) {
            showMessage('No doctors available in the system.', 'warning');
        }
        
        // Update the doctor select with all doctors
        updateDoctorSelect(doctors);
    } catch (error) {
        console.error('Error loading all doctors:', error);
        showMessage('Failed to load doctors. Please try again.', 'error');
    }
}

/**
 * Handle date change event
 * @param {Event} event - The change event
 */
async function handleDateChange(event) {
    const selectedDate = event.target.value;
    
    if (!selectedDate) {
        clearTimeSlots();
        return;
    }
    
    // If a doctor is already selected, update the time slots
    const selectedDoctorId = doctorSelectEl.value;
    if (selectedDoctorId) {
        try {
            const timeSlots = await getAvailableTimeSlots(selectedDoctorId, selectedDate);
            updateTimeSlots(timeSlots);
        } catch (error) {
            console.error('Error fetching time slots:', error);
            showMessage('Failed to load available time slots. Please try again.', 'error');
        }
    } else {
        // If no doctor is selected yet but a date is selected, 
        // try to get available doctors for that date
        try {
            const doctors = await getAvailableDoctors(selectedDate);
            updateDoctorSelect(doctors);
            
            if (doctors.length > 0) {
                showMessage(`${doctors.length} doctors available on ${selectedDate}.`, 'success', doctorSelectionMessage);
            } else {
                showMessage('No doctors available on the selected date.', 'warning', doctorSelectionMessage);
            }
        } catch (error) {
            console.error('Error fetching available doctors:', error);
            showMessage('Failed to load available doctors. Please try again.', 'error');
        }
    }
}

/**
 * Handle doctor change event
 * @param {Event} event - The change event
 */
async function handleDoctorChange(event) {
    const doctorId = event.target.value;
    const selectedDate = datePickerEl.value;
    
    // Find the selected doctor object from options
    const selectedOption = doctorSelectEl.options[doctorSelectEl.selectedIndex];
    const doctorText = selectedOption.text;
    
    console.log(`Doctor selected: ${doctorText} with ID: ${doctorId}`);
    console.log(`Selected date: ${selectedDate}`);
    
    // Store selected doctor info for later use
    if (doctorId) {
        try {
            // Extract doctor info from the option text or fetch it
            selectedDoctor = {
                id: doctorId,
                first_name: doctorText.split(' ')[0],
                last_name: doctorText.split(' ')[1],
                specialty: doctorText.match(/\((.*?)\)/)[1] // Extract text between parentheses
            };
            console.log('Selected doctor info:', selectedDoctor);
        } catch (error) {
            console.error('Error parsing doctor info from option text:', error);
            // Fallback
            selectedDoctor = {
                id: doctorId,
                first_name: doctorText,
                last_name: '',
                specialty: 'Doctor'
            };
        }
    } else {
        selectedDoctor = null;
    }
    
    if (!doctorId || !selectedDate) {
        clearTimeSlots();
        return;
    }
    
    try {
        // Show loading message
        showMessage('Loading available time slots...', 'info');
        
        // Get available time slots for the selected doctor and date
        console.log(`Fetching time slots for doctor ${doctorId} on ${selectedDate}`);
        const timeSlots = await getAvailableTimeSlots(doctorId, selectedDate);
        console.log('API response for time slots:', timeSlots);
        
        // Update the time slots - using the direct array returned from the API
        updateTimeSlots(timeSlots);
        
    } catch (error) {
        console.error('Error handling doctor change:', error);
        showMessage('Failed to load available time slots. Please try again.', 'error');
    }
}

/**
 * Update the doctor select with available doctors
 * @param {Array} doctors - List of available doctors
 */
function updateDoctorSelect(doctors) {
    console.log('updateDoctorSelect called with:', doctors);
    
    if (!doctorSelectEl) {
        console.warn('doctorSelectEl not found in DOM!');
        return;
    }
    
    // Clear current options
    doctorSelectEl.innerHTML = '<option value="">Select Doctor</option>';
    
    // Add new options
    doctors.forEach(doctor => {
        const option = document.createElement('option');
        option.value = doctor.id;
        // Show as: FirstName LastName (Specialty)
        option.textContent = `${doctor.first_name} ${doctor.last_name} (${doctor.specialty})`;
        doctorSelectEl.appendChild(option);
        console.log(`Added doctor to dropdown: ${doctor.first_name} ${doctor.last_name}`);
    });
    
    console.log('Doctor dropdown updated, current options:', doctorSelectEl.options.length);
}

/**
 * Update the time slots with available time slots
 * @param {Array} availableSlots - List of available time slots
 */
function updateTimeSlots(availableSlots) {
    console.log('Updating time slots with:', availableSlots);
    
    if (!timeSlotsContainer) {
        console.warn('timeSlotsContainer not found in DOM!');
        return;
    }
    
    // Clear current time slots
    timeSlotsContainer.innerHTML = '';
    
    if (!availableSlots || availableSlots.length === 0) {
        timeSlotsContainer.innerHTML = '<p>No time slots available for the selected date and doctor.</p>';
        return;
    }
    
    // Add new time slots
    availableSlots.forEach(slot => {
        const timeSlot = document.createElement('div');
        timeSlot.className = 'time-slot';
        
        // Handle different API response formats
        if (slot.start && slot.end) {
            // Format using start-end time format
            timeSlot.textContent = `${slot.start} - ${slot.end}`;
            timeSlot.dataset.slotId = `${slot.start}-${slot.end}`;
        } else if (slot.time) {
            // Use time directly if that's what the API returns
            timeSlot.textContent = slot.time;
            timeSlot.dataset.slotId = slot.id || slot.time;
        } else {
            // Fallback
            timeSlot.textContent = JSON.stringify(slot);
            timeSlot.dataset.slotId = JSON.stringify(slot);
        }
        
        if (slot.is_booked) {
            timeSlot.classList.add('booked');
        } else {
            timeSlot.addEventListener('click', function() {
                // Remove selected class from all time slots
                document.querySelectorAll('.time-slot').forEach(s => s.classList.remove('selected'));
                
                // Add selected class to clicked time slot
                this.classList.add('selected');
                
                // Store selected time slot
                selectedTimeSlot = this;
                
                // Update summary
                updateSummary();
            });
        }
        
        timeSlotsContainer.appendChild(timeSlot);
    });
    
    // After adding time slots, show a message
    if (availableSlots.length > 0) {
        showMessage(`${availableSlots.length} time slots available. Please select one.`, 'success');
    }
}

/**
 * Clear time slots
 */
function clearTimeSlots() {
    if (timeSlotsContainer) {
        timeSlotsContainer.innerHTML = '<p>Please select a doctor and date first.</p>';
    }
    selectedTimeSlot = null;
}

/**
 * Confirm appointment
 */
async function confirmAppointment() {
    // Validate all required fields
    if (!datePickerEl.value) {
        showMessage('Please select a date.', 'error');
        activateTab('1');
        return;
    }
    
    if (!doctorSelectEl.value) {
        showMessage('Please select a doctor.', 'error');
        activateTab('1');
        return;
    }
    
    if (!selectedTimeSlot) {
        showMessage('Please select a time slot.', 'error');
        activateTab('2');
        return;
    }
    
    // Gather appointment data
    const appointmentData = {
        date: datePickerEl.value,
        doctor_id: doctorSelectEl.value,
        time_slot_id: selectedTimeSlot.dataset.slotId,
        notes: appointmentNotesEl ? appointmentNotesEl.value : ''
    };
    
    // Add recurring information if applicable
    const recurringCheckbox = document.getElementById('recurring');
    if (recurringCheckbox && recurringCheckbox.checked) {
        appointmentData.recurring = {
            pattern: document.querySelector('select[name="recurrence_pattern"]').value,
            sessions: document.querySelector('input[name="sessions"]').value
        };
    }
    
    // Add reminder preferences
    appointmentData.reminders = {};
    
    const emailReminder = document.getElementById('emailReminder');
    if (emailReminder && emailReminder.checked) {
        const emailInput = document.getElementById('emailAddress');
        appointmentData.reminders.email = emailInput ? emailInput.value : '';
    }
    
    const smsReminder = document.getElementById('smsReminder');
    if (smsReminder && smsReminder.checked) {
        const phoneInput = document.getElementById('phoneNumber');
        appointmentData.reminders.sms = phoneInput ? phoneInput.value : '';
    }
    
    const calendarReminder = document.getElementById('calendarReminder');
    if (calendarReminder) {
        appointmentData.reminders.calendar = calendarReminder.checked;
    }
    
    const caregiverReminders = document.getElementById('caregiverReminders');
    if (caregiverReminders && caregiverReminders.checked) {
        appointmentData.reminders.caregiver = {
            name: document.getElementById('caregiverName') ? document.getElementById('caregiverName').value : '',
            email: document.getElementById('caregiverEmail') ? document.getElementById('caregiverEmail').value : '',
            phone: document.getElementById('caregiverPhone') ? document.getElementById('caregiverPhone').value : ''
        };
    }
    
    try {
        // Show loading message
        showMessage('Booking appointment...', 'info');
        
        // Book the appointment
        const result = await bookAppointment(appointmentData);
        
        // Hide the form and show the success message
        document.querySelector('.appointment-tabs').style.display = 'none';
        
        const appointmentSuccess = document.getElementById('appointmentSuccess');
        if (appointmentSuccess) {
            appointmentSuccess.style.display = 'block';
            
            const successDetails = document.getElementById('successDetails');
            if (successDetails) {
                let doctor = selectedDoctor ? `${selectedDoctor.first_name} ${selectedDoctor.last_name}` : 'the doctor';
                successDetails.textContent = `Your appointment with ${doctor} on ${datePickerEl.value} at ${selectedTimeSlot.textContent} has been confirmed.`;
            }
        }
        
        // Clear form for next appointment
        resetAppointmentForm();
    } catch (error) {
        console.error('Error booking appointment:', error);
        showMessage('Failed to book appointment: ' + (error.message || 'Please try again later.'), 'error');
    }
}

/**
 * Reset the appointment form
 */
function resetAppointmentForm() {
    if (datePickerEl) datePickerEl.value = '';
    if (doctorSelectEl) doctorSelectEl.value = '';
    
    clearTimeSlots();
    
    if (appointmentNotesEl) appointmentNotesEl.value = '';
    
    const recurringCheckbox = document.getElementById('recurring');
    if (recurringCheckbox) recurringCheckbox.checked = false;
    
    const recurringOptions = document.getElementById('recurringOptions');
    if (recurringOptions) recurringOptions.style.display = 'none';
    
    const caregiverRemindersCheckbox = document.getElementById('caregiverReminders');
    if (caregiverRemindersCheckbox) caregiverRemindersCheckbox.checked = false;
    
    const caregiverDetails = document.getElementById('caregiverDetails');
    if (caregiverDetails) caregiverDetails.style.display = 'none';
    
    // Reset global variables
    selectedTimeSlot = null;
    selectedDoctor = null;
    
    // Show the form and hide success message
    const appointmentTabs = document.querySelector('.appointment-tabs');
    if (appointmentTabs) appointmentTabs.style.display = 'block';
    
    const appointmentSuccess = document.getElementById('appointmentSuccess');
    if (appointmentSuccess) appointmentSuccess.style.display = 'none';
    
    // Go back to first step
    activateTab('1');
    
    // Reload all doctors
    loadAllDoctors();
}

/**
 * Show a message to the user
 * @param {string} message - The message to show
 * @param {string} type - The message type (info, success, warning, error)
 * @param {Element} container - The container to show the message in (optional)
 */
function showMessage(message, type, container = null) {
    // Use provided container or default to errorContainer
    const messageContainer = container || errorContainer;
    if (!messageContainer) return;
    
    // Create message element
    const messageElement = document.createElement('div');
    messageElement.className = `alert alert-${type}`;
    messageElement.textContent = message;
    
    // Clear existing messages
    messageContainer.innerHTML = '';
    
    // Add the message
    messageContainer.appendChild(messageElement);
    
    // Auto-hide success and info messages after 5 seconds
    if (type === 'success' || type === 'info') {
        setTimeout(() => {
            messageElement.remove();
        }, 5000);
    }
}

// Ensure initialization always runs
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAppointmentHandler);
} else {
    initAppointmentHandler();
}