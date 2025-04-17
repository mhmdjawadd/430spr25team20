/**
 * Appointment handler for the Nabad healthcare platform
 * Manages the appointment booking UI interactions
 */

import { getAllDoctors, getAvailableDoctors, getAvailableTimeSlots, bookAppointment, checkInsuranceCoverage } from './appointment-api.js';

// Global variables for DOM elements and state
let datePickerEl;
let doctorInputEl;
let doctorSuggestionsEl;
let doctorInfoEl;
let timeSlotContainer;
let timeSlotsContainer;
let appointmentNotesEl;
let appointmentTypeEl;
let errorContainer;
let allDoctors = [];
let selectedDoctor = null;
let selectedTimeSlot = null;
let searchTimeout = null;
let insuranceDetails = null;

/**
 * Initialize the appointment handler
 */
function initAppointmentHandler() {
    console.log('Initializing appointment handler...');
    
    // Get DOM references after content is loaded
    datePickerEl = document.getElementById('datepicker');
    doctorInputEl = document.getElementById('doctorInput');
    doctorSuggestionsEl = document.getElementById('doctorSuggestions');
    doctorInfoEl = document.getElementById('doctorInfo');
    timeSlotContainer = document.getElementById('timeSlotContainer');
    timeSlotsContainer = document.getElementById('timeSlots');
    appointmentNotesEl = document.getElementById('appointmentNotes');
    appointmentTypeEl = document.getElementById('appointmentType');
    errorContainer = document.getElementById('errorContainer');

    // Initialize datepicker
    if (datePickerEl && typeof $.fn.datepicker !== 'undefined') {
        console.log('Initializing datepicker...');
        $(datePickerEl).datepicker({
            format: 'yyyy-mm-dd',
            startDate: new Date(),
            autoclose: true
        });
    }

    // Add event listeners
    if (datePickerEl) {
        datePickerEl.addEventListener('change', handleDateChange);
    }
    
    if (doctorInputEl) {
        doctorInputEl.addEventListener('input', handleDoctorSearch);
        doctorInputEl.addEventListener('focus', function() {
            // Show suggestions if input has some text
            if (doctorInputEl.value.trim().length > 0) {
                handleDoctorSearch({ target: doctorInputEl });
            }
        });
        
        // Hide suggestions when clicking outside
        document.addEventListener('click', function(e) {
            if (e.target !== doctorInputEl && e.target !== doctorSuggestionsEl) {
                toggleElement(doctorSuggestionsEl, false);
            }
        });
    }
    
    // Recurring appointment checkbox
    const recurringCheckbox = document.getElementById('recurring');
    const recurringOptions = document.getElementById('recurringOptions');
    if (recurringCheckbox && recurringOptions) {
        recurringCheckbox.addEventListener('change', function() {
            toggleElement(recurringOptions, this.checked);
            updateSummary();
        });
    }
    
    // Caregiver reminders checkbox
    const caregiverRemindersCheckbox = document.getElementById('caregiverReminders');
    const caregiverDetails = document.getElementById('caregiverDetails');
    if (caregiverRemindersCheckbox && caregiverDetails) {
        caregiverRemindersCheckbox.addEventListener('change', function() {
            toggleElement(caregiverDetails, this.checked);
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
    loadAllDoctors();
}

/**
 * Helper function to toggle element visibility
 * @param {Element} element - The element to toggle
 * @param {boolean} show - Whether to show or hide the element
 */
function toggleElement(element, show) {
    if (element) {
        if (show) {
            element.classList.remove('hidden');
        } else {
            element.classList.add('hidden');
        }
    }
}

/**
 * Update the appointment summary
 */
function updateSummary() {
    const summaryDateEl = document.getElementById('summaryDate');
    const summaryTimeEl = document.getElementById('summaryTime');
    const summaryDoctorEl = document.getElementById('summaryDoctor');
    const summaryDepartmentEl = document.getElementById('summaryDepartment');

    // Update date
    if (summaryDateEl && datePickerEl) {
        summaryDateEl.textContent = datePickerEl.value || 'Not selected';
    }
    
    // Update time
    if (summaryTimeEl) {
        if (selectedTimeSlot) {
            summaryTimeEl.textContent = selectedTimeSlot.textContent;
        } else {
            summaryTimeEl.textContent = 'Not selected';
        }
    }
    
    // Update doctor
    if (summaryDoctorEl) {
        summaryDoctorEl.textContent = selectedDoctor ? 
            `Dr. ${selectedDoctor.first_name} ${selectedDoctor.last_name}` : 'Not selected';
    }
    
    // Update department/specialty
    if (summaryDepartmentEl) {
        summaryDepartmentEl.textContent = selectedDoctor ? selectedDoctor.specialty : 'Not selected';
    }
    
    // Update recurring info if applicable
    const recurringCheckbox = document.getElementById('recurring');
    const summaryRecurringContainer = document.getElementById('summaryRecurringContainer');
    const summaryRecurring = document.getElementById('summaryRecurring');
    
    if (recurringCheckbox && summaryRecurringContainer && summaryRecurring) {
        summaryRecurringContainer.style.display = recurringCheckbox.checked ? 'flex' : 'none';
        if (recurringCheckbox.checked) {
            const pattern = document.getElementById('recurrencePattern').value;
            const sessions = document.getElementById('sessions').value;
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
        showMessage('Loading doctors...', 'info');
        
        // Get all doctors from the database
        const doctors = await getAllDoctors();
        console.log('Received doctors from API:', doctors);
        
        if (!Array.isArray(doctors) || doctors.length === 0) {
            showMessage('No doctors available in the system.', 'warning');
            return;
        }
        
        // Store all doctors for filtering
        allDoctors = doctors;
        
        // Show all doctors immediately in the dropdown
        updateDoctorSuggestions(doctors);
        toggleElement(doctorSuggestionsEl, true);
        
        showMessage(`${doctors.length} doctors loaded successfully.`, 'success');
    } catch (error) {
        console.error('Error loading doctors:', error);
        showMessage('Failed to load doctors. Please try again.', 'error');
    }
}

/**
 * Handle doctor search input
 * @param {Event} event - The input event
 */
function handleDoctorSearch(event) {
    const searchText = event.target.value.toLowerCase().trim();
    
    // Clear previous timeout
    if (searchTimeout) {
        clearTimeout(searchTimeout);
    }
    
    // Set a new timeout to avoid excessive filtering
    searchTimeout = setTimeout(() => {
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
            // Hide suggestions if search text is empty
            toggleElement(doctorSuggestionsEl, false);
            
            // If input is cleared, also clear selected doctor
            if (selectedDoctor) {
                selectedDoctor = null;
                toggleElement(doctorInfoEl, false);
                clearTimeSlots();
                updateSummary();
            }
        }
    }, 300);
}

/**
 * Update doctor suggestions dropdown
 * @param {Array} doctors - List of filtered doctors
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
        // Add new results
        doctors.forEach(doctor => {
            const resultItem = document.createElement('div');
            resultItem.className = 'doctor-search-item';
            resultItem.dataset.id = doctor.id;
            
            const doctorName = document.createElement('span');
            doctorName.className = 'doctor-name';
            doctorName.textContent = `Dr. ${doctor.first_name} ${doctor.last_name}`;
            
            const doctorSpecialty = document.createElement('span');
            doctorSpecialty.className = 'doctor-specialty';
            doctorSpecialty.textContent = doctor.specialty;
            
            resultItem.appendChild(doctorName);
            resultItem.appendChild(doctorSpecialty);
            
            // Add click event to select this doctor
            resultItem.addEventListener('click', () => {
                selectDoctor(doctor);
            });
            
            doctorSuggestionsEl.appendChild(resultItem);
        });
    }
}

/**
 * Select a doctor from suggestions
 * @param {Object} doctor - The selected doctor object
 */
async function selectDoctor(doctor) {
    // Store selected doctor
    selectedDoctor = doctor;
    
    // Update doctor input field
    doctorInputEl.value = `Dr. ${doctor.first_name} ${doctor.last_name}`;
    
    // Update selected doctor info display
    const doctorNameEl = doctorInfoEl.querySelector('.doctor-name');
    const doctorSpecialtyEl = doctorInfoEl.querySelector('.doctor-specialty');
    
    if (doctorNameEl) {
        doctorNameEl.textContent = `Dr. ${doctor.first_name} ${doctor.last_name}`;
    }
    
    if (doctorSpecialtyEl) {
        doctorSpecialtyEl.textContent = `(${doctor.specialty})`;
    }
    
    // Show selected doctor info
    toggleElement(doctorInfoEl, true);
    
    // Hide suggestions
    toggleElement(doctorSuggestionsEl, false);
    
    // Check insurance coverage for this doctor
    try {
        // Get insurance container
        const insuranceContainer = document.getElementById('insuranceInfoContainer');
        const insuranceDetailsEl = document.getElementById('insuranceDetails');
        
        if (insuranceContainer && insuranceDetailsEl) {
            // Show loading state
            insuranceContainer.style.display = 'block';
            insuranceDetailsEl.innerHTML = '<p>Checking insurance coverage...</p>';
            
            // Get insurance coverage
            const coverage = await checkInsuranceCoverage(doctor.id);
            insuranceDetails = coverage; // Store for later use
            
            // Update UI based on coverage
            if (coverage.has_insurance) {
                if (coverage.is_covered) {
                    const coverageAmount = coverage.coverage_details.covered_amount.toFixed(2);
                    const patientResponsibility = coverage.coverage_details.patient_responsibility.toFixed(2);
                    const coveragePercent = coverage.coverage_details.coverage_percent;
                    
                    insuranceDetailsEl.innerHTML = `
                        <div class="alert alert-success mb-0">
                            <strong>Insurance Verified:</strong> ${coverage.coverage_details.provider}<br>
                            <strong>Coverage:</strong> $${coverageAmount} (${coveragePercent})<br>
                            <strong>Your Responsibility:</strong> $${patientResponsibility}
                        </div>
                    `;
                } else {
                    insuranceDetailsEl.innerHTML = `
                        <div class="alert alert-warning mb-0">
                            <strong>Insurance Notice:</strong> Your insurance plan (${coverage.coverage_details.provider}) 
                            does not cover visits with this doctor specialty.<br>
                            <strong>Your Responsibility:</strong> $${coverage.coverage_details.base_cost.toFixed(2)}
                        </div>
                    `;
                }
            } else {
                // No insurance on file
                insuranceDetailsEl.innerHTML = `
                    <div class="alert alert-info mb-0">
                        <strong>No Insurance Found:</strong> You don't have insurance information on file.<br>
                        <strong>Your Responsibility:</strong> $${doctor.specialty === 'DOCTOR' ? '100.00' : '150.00'}
                    </div>
                `;
            }
        }
    } catch (error) {
        console.error('Error checking insurance:', error);
        // Don't show an error message to the user as requested
        
        // Just hide the insurance container if there's an error
        const insuranceContainer = document.getElementById('insuranceInfoContainer');
        if (insuranceContainer) {
            insuranceContainer.style.display = 'none';
        }
    }
    
    // Update time slots if a date is already selected
    if (datePickerEl.value) {
        fetchAndShowTimeSlots(doctor.id, datePickerEl.value);
    }
    
    // Update appointment summary
    updateSummary();
}

/**
 * Handle date change event
 */
async function handleDateChange() {
    const selectedDate = datePickerEl.value;
    
    if (!selectedDate) {
        clearTimeSlots();
        return;
    }
    
    // If a doctor is already selected, update the time slots
    if (selectedDoctor) {
        try {
            await fetchAndShowTimeSlots(selectedDoctor.id, selectedDate);
        } catch (error) {
            console.error('Error fetching time slots:', error);
            showMessage('Failed to load available time slots. Please try again.', 'error');
        }
    }
    
    // Update summary whenever date changes
    updateSummary();
}

/**
 * Fetch and show time slots for selected doctor and date
 */
async function fetchAndShowTimeSlots(doctorId, date) {
    try {
        showMessage('Loading available time slots...', 'info');
        
        const timeSlots = await getAvailableTimeSlots(doctorId, date);
        console.log('Time slots received:', timeSlots);
        
        updateTimeSlots(timeSlots);
    } catch (error) {
        console.error('Error fetching time slots:', error);
        throw error;
    }
}

/**
 * Update time slots display
 */
function updateTimeSlots(availableSlots) {
    // Clear previous selection
    selectedTimeSlot = null;
    
    // Get fresh reference to ensure we have the current element
    const currentTimeSlotContainer = document.getElementById('timeSlotContainer');
    const currentTimeSlotsContainer = document.getElementById('timeSlots');
    
    if (!currentTimeSlotsContainer) {
        console.warn('Time slots container not found in DOM!');
        return;
    }
    
    // Show the time slot container
    toggleElement(currentTimeSlotContainer, true);
    
    // Clear current time slots
    currentTimeSlotsContainer.innerHTML = '';
    
    if (!availableSlots || availableSlots.length === 0) {
        currentTimeSlotsContainer.innerHTML = '<p>No time slots available for the selected date and doctor.</p>';
        return;
    }
    
    // Add time slots
    availableSlots.forEach(slot => {
        const timeSlot = document.createElement('div');
        timeSlot.className = 'time-slot';
        
        // Handle different API response formats
        if (slot.start && slot.end) {
            timeSlot.textContent = `${slot.start} - ${slot.end}`;
            timeSlot.dataset.slotId = `${slot.start}-${slot.end}`;
        } else if (slot.time) {
            timeSlot.textContent = slot.time;
            timeSlot.dataset.slotId = slot.id || slot.time;
        } else {
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
        
        currentTimeSlotsContainer.appendChild(timeSlot);
    });
    
    showMessage(`${availableSlots.length} time slots available. Please select one.`, 'success');
}

/**
 * Clear time slots
 */
function clearTimeSlots() {
    const currentTimeSlotContainer = document.getElementById('timeSlotContainer');
    const currentTimeSlotsContainer = document.getElementById('timeSlots');
    
    if (currentTimeSlotsContainer) {
        currentTimeSlotsContainer.innerHTML = '<p>Please select a date and doctor first.</p>';
    }
    
    // Hide the time slot container
    toggleElement(currentTimeSlotContainer, false);
    
    selectedTimeSlot = null;
}

/**
 * Confirm appointment
 */
async function confirmAppointment() {
    // Validate all required fields
    if (!datePickerEl.value) {
        showMessage('Please select a date.', 'error');
        datePickerEl.focus();
        return;
    }
    
    if (!selectedDoctor) {
        showMessage('Please select a doctor.', 'error');
        doctorInputEl.focus();
        return;
    }
    
    if (!selectedTimeSlot) {
        showMessage('Please select a time slot.', 'error');
        document.getElementById('timeSlots').scrollIntoView({ behavior: 'smooth' });
        return;
    }
    
    // Extract hour from the time slot (assuming format like "10:00 AM - 11:00 AM")
    let hour = "00";
    if (selectedTimeSlot.textContent) {
        const timeText = selectedTimeSlot.textContent;
        const match = timeText.match(/(\d+):/);
        if (match && match[1]) {
            hour = match[1].padStart(2, '0');
        }
    }
    
    // Gather appointment data in the format expected by the backend
    const appointmentData = {
        doctor_id: selectedDoctor.id,
        date_time: `${datePickerEl.value}-${hour}`, // Format as YYYY-MM-DD-HH
        appointment_type: appointmentTypeEl ? appointmentTypeEl.value : "REGULAR", // Default value
        verify_insurance: true, // Default value
        notes: appointmentNotesEl ? appointmentNotesEl.value : ''
    };
    
    // Add recurring information if applicable
    const recurringCheckbox = document.getElementById('recurring');
    if (recurringCheckbox && recurringCheckbox.checked) {
        appointmentData.appointment_type = "RECURRING";
        appointmentData.recurrence_pattern = document.getElementById('recurrencePattern').value.toUpperCase(); // WEEKLY, BIWEEKLY, MONTHLY
        appointmentData.recurrence_count = parseInt(document.getElementById('sessions').value, 10);
    }
    
    // Check if it's an emergency appointment
    const emergencyCheckbox = document.getElementById('emergency');
    if (emergencyCheckbox && emergencyCheckbox.checked) {
        appointmentData.appointment_type = "EMERGENCY";
    }
    
    // Include insurance details if available
    if (insuranceDetails) {
        appointmentData.insurance_details = insuranceDetails;
    }
    
    // Store reminder preferences separately (not included in the backend request format)
    const reminderPreferences = {};
    
    const emailReminder = document.getElementById('emailReminder');
    if (emailReminder && emailReminder.checked) {
        const emailInput = document.getElementById('emailAddress');
        reminderPreferences.email = emailInput ? emailInput.value : '';
    }
    
    const smsReminder = document.getElementById('smsReminder');
    if (smsReminder && smsReminder.checked) {
        const phoneInput = document.getElementById('phoneNumber');
        reminderPreferences.sms = phoneInput ? phoneInput.value : '';
    }
    
    const calendarReminder = document.getElementById('calendarReminder');
    if (calendarReminder) {
        reminderPreferences.calendar = calendarReminder.checked;
    }
    
    const caregiverReminders = document.getElementById('caregiverReminders');
    if (caregiverReminders && caregiverReminders.checked) {
        reminderPreferences.caregiver = {
            name: document.getElementById('caregiverName') ? document.getElementById('caregiverName').value : '',
            email: document.getElementById('caregiverEmail') ? document.getElementById('caregiverEmail').value : '',
            phone: document.getElementById('caregiverPhone') ? document.getElementById('caregiverPhone').value : ''
        };
    }
    
    // Store reminder preferences separately as they are not part of the backend request schema
    localStorage.setItem('lastReminderPreferences', JSON.stringify(reminderPreferences));
    
    try {
        // Show loading message
        showMessage('Booking appointment...', 'info');
        
        // Book the appointment
        const result = await bookAppointment(appointmentData);
        console.log('Appointment booked:', result);
        
        // Hide the form and show the success message
        const appointmentFormContainer = document.getElementById('appointmentFormContainer');
        if (appointmentFormContainer) {
            appointmentFormContainer.style.display = 'none';
        }
        
        const appointmentSuccess = document.getElementById('appointmentSuccess');
        if (appointmentSuccess) {
            appointmentSuccess.style.display = 'block';
            
            const successDetails = document.getElementById('successDetails');
            if (successDetails) {
                successDetails.textContent = `Your appointment with Dr. ${selectedDoctor.first_name} ${selectedDoctor.last_name} on ${datePickerEl.value} at ${selectedTimeSlot.textContent} has been confirmed.`;
            }
        }
    } catch (error) {
        console.error('Error booking appointment:', error);
        showMessage('Failed to book appointment: ' + (error.message || 'Please try again later.'), 'error');
    }
}

/**
 * Reset the appointment form
 */
function resetAppointmentForm() {
    // Reset form fields
    if (datePickerEl) datePickerEl.value = '';
    if (doctorInputEl) doctorInputEl.value = '';
    if (appointmentNotesEl) appointmentNotesEl.value = '';
    if (appointmentTypeEl) appointmentTypeEl.value = 'REGULAR';
    
    // Hide doctor info
    toggleElement(doctorInfoEl, false);
    
    // Clear time slots
    clearTimeSlots();
    
    // Reset checkboxes and their dependent elements
    const recurringCheckbox = document.getElementById('recurring');
    if (recurringCheckbox) recurringCheckbox.checked = false;
    
    const recurringOptions = document.getElementById('recurringOptions');
    if (recurringOptions) toggleElement(recurringOptions, false);
    
    const caregiverRemindersCheckbox = document.getElementById('caregiverReminders');
    if (caregiverRemindersCheckbox) caregiverRemindersCheckbox.checked = false;
    
    const caregiverDetails = document.getElementById('caregiverDetails');
    if (caregiverDetails) toggleElement(caregiverDetails, false);
    
    // Reset selected doctor and time slot
    selectedDoctor = null;
    selectedTimeSlot = null;
    
    // Show the form and hide success message
    const appointmentFormContainer = document.getElementById('appointmentFormContainer');
    if (appointmentFormContainer) appointmentFormContainer.style.display = 'block';
    
    const appointmentSuccess = document.getElementById('appointmentSuccess');
    if (appointmentSuccess) appointmentSuccess.style.display = 'none';
    
    // Reset the summary
    updateSummary();
}

/**
 * Show a message to the user
 * @param {string} message - The message to show
 * @param {string} type - The message type (info, success, warning, error)
 */
function showMessage(message, type) {
    const messageContainer = document.getElementById('errorContainer');
    if (!messageContainer) return;
    
    // Create message element
    const messageElement = document.createElement('div');
    messageElement.className = `alert alert-${type}`;
    messageElement.textContent = message;
    
    // Clear existing messages
    messageContainer.innerHTML = '';
    
    // Add the message
    messageContainer.appendChild(messageElement);
    
    // Auto-hide non-error messages after 5 seconds
    if (type !== 'error') {
        setTimeout(() => {
            messageElement.remove();
        }, 5000);
    }
}

// Ensure initialization runs when DOM is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAppointmentHandler);
} else {
    initAppointmentHandler();
}

// Make functions available globally and export for module usage
window.confirmAppointment = confirmAppointment;
window.resetAppointmentForm = resetAppointmentForm;

export { initAppointmentHandler };