
class AppointmentUI {
    constructor() {
        this.initializeEventListeners();
        this.loadAvailableSlots();
        this.setupDateValidation();
    }

    initializeEventListeners() {

        document.getElementById('appointment-date').addEventListener('change', (e) => {
            this.loadAvailableSlots(e.target.value);
        });

   
        document.getElementById('time-slots').addEventListener('change', (e) => {
            this.updateRecurringOptions();
        });

        
        document.getElementById('recurring-toggle').addEventListener('change', (e) => {
            this.toggleRecurringOptions(e.target.checked);
        });

        document.getElementById('recurring-type').addEventListener('change', (e) => {
            this.toggleCustomDays(e.target.value === 'custom');
        });

        
        document.getElementById('appointment-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleAppointmentSubmission();
        });
    }

    setupDateValidation() {
        const dateInput = document.getElementById('appointment-date');
        const today = new Date().toISOString().split('T')[0];
        dateInput.min = today;
    }

    loadAvailableSlots(date) {
        const selectedDate = new Date(date);
        const slots = window.appointmentSystem.getAvailableSlots(selectedDate);
        
        const timeSlotsSelect = document.getElementById('time-slots');
        timeSlotsSelect.innerHTML = '<option value="">Choose a time slot</option>';

        slots.forEach(slot => {
            const option = document.createElement('option');
            option.value = slot.toISOString();
            option.textContent = slot.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            timeSlotsSelect.appendChild(option);
        });
    }

    toggleRecurringOptions(show) {
        const recurringOptions = document.getElementById('recurring-options');
        recurringOptions.style.display = show ? 'block' : 'none';
        recurringOptions.classList.toggle('show', show);
    }

    toggleCustomDays(show) {
        const customDaysGroup = document.getElementById('custom-days-group');
        customDaysGroup.style.display = show ? 'block' : 'none';
    }

    updateRecurringOptions() {
        const selectedDate = new Date(document.getElementById('time-slots').value);
        const nextAppointments = this.calculateNextAppointments(selectedDate);
        
        const nextAppointmentsList = document.getElementById('next-appointments');
        nextAppointmentsList.innerHTML = '';

        nextAppointments.forEach(date => {
            const li = document.createElement('li');
            li.textContent = date.toLocaleString();
            nextAppointmentsList.appendChild(li);
        });
    }

    calculateNextAppointments(startDate) {
        const recurringType = document.getElementById('recurring-type').value;
        const nextAppointments = [];
        let currentDate = new Date(startDate);

        for (let i = 0; i < 5; i++) {
            switch (recurringType) {
                case 'weekly':
                    currentDate.setDate(currentDate.getDate() + 7);
                    break;
                case 'monthly':
                    currentDate.setMonth(currentDate.getMonth() + 1);
                    break;
                case 'custom':
                    const customDays = parseInt(document.getElementById('custom-days').value);
                    currentDate.setDate(currentDate.getDate() + customDays);
                    break;
            }
            nextAppointments.push(new Date(currentDate));
        }

        return nextAppointments;
    }

    handleAppointmentSubmission() {
        const formData = new FormData(document.getElementById('appointment-form'));
        const appointmentData = {
            patientId: formData.get('patient-id'),
            dateTime: new Date(formData.get('time-slots')),
            isRecurring: formData.get('recurring-toggle') === 'on',
            recurrencePattern: formData.get('recurring-type')
        };

        try {
            const appointment = window.appointmentSystem.bookAppointment(
                appointmentData.patientId,
                appointmentData.dateTime,
                appointmentData.isRecurring,
                appointmentData.recurrencePattern
            );

       
            window.reminderSystem.scheduleReminder(appointment);

            this.showConfirmation(appointment);
            this.resetForm();
        } catch (error) {
            this.showError('Failed to book appointment. Please try again.');
        }
    }

    showConfirmation(appointment) {
        const confirmationMessage = document.createElement('div');
        confirmationMessage.className = 'alert alert-success alert-dismissible fade show';
        confirmationMessage.innerHTML = `
            <h4><i class="fas fa-check-circle me-2"></i>Appointment Confirmed!</h4>
            <p>Your appointment has been scheduled for ${new Date(appointment.dateTime).toLocaleString()}</p>
            ${appointment.isRecurring ? '<p>This is a recurring appointment.</p>' : ''}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        const form = document.getElementById('appointment-form');
        form.parentNode.insertBefore(confirmationMessage, form);
    }

    showError(message) {
        const errorMessage = document.createElement('div');
        errorMessage.className = 'alert alert-danger alert-dismissible fade show';
        errorMessage.innerHTML = `
            <h4><i class="fas fa-exclamation-circle me-2"></i>Error</h4>
            <p>${message}</p>
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        const form = document.getElementById('appointment-form');
        form.parentNode.insertBefore(errorMessage, form);
    }

    resetForm() {
        document.getElementById('appointment-form').reset();
        document.getElementById('caregiver-fields').style.display = 'none';
        document.getElementById('recurring-options').style.display = 'none';
        document.getElementById('custom-days-group').style.display = 'none';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.appointmentUI = new AppointmentUI();
}); 