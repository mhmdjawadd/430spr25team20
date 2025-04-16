
class AppointmentSystem {
    constructor() {
        this.appointments = this.loadAppointments();
        this.availableSlots = [];
        this.initializeCalendar();
    }

    loadAppointments() {
        const savedAppointments = localStorage.getItem('appointments');
        return savedAppointments ? JSON.parse(savedAppointments) : [];
    }

    saveAppointments() {
        localStorage.setItem('appointments', JSON.stringify(this.appointments));
    }

    initializeCalendar() {
        this.generateAvailableSlots();
    }

    generateAvailableSlots() {
        const today = new Date();
        for (let i = 0; i < 30; i++) {
            const date = new Date(today);
            date.setDate(today.getDate() + i);
            

            for (let hour = 9; hour < 17; hour++) {
                for (let minute = 0; minute < 60; minute += 30) {
                    const slot = new Date(date);
                    slot.setHours(hour, minute, 0, 0);
                    
                
                    if (!this.isSlotBooked(slot)) {
                        this.availableSlots.push(slot);
                    }
                }
            }
        }
    }

    isSlotBooked(slot) {
        return this.appointments.some(apt => {
            const aptDate = new Date(apt.dateTime);
            return aptDate.getTime() === slot.getTime();
        });
    }

    bookAppointment(patientId, dateTime, isRecurring = false, recurrencePattern = null) {
        const appointment = {
            id: Date.now(),
            patientId,
            dateTime,
            isRecurring,
            recurrencePattern,
            status: 'confirmed',
            createdAt: new Date().toISOString()
        };

        this.appointments.push(appointment);
        this.removeBookedSlot(dateTime);
        this.saveAppointments();
        return appointment;
    }

    removeBookedSlot(dateTime) {
        this.availableSlots = this.availableSlots.filter(slot => 
            slot.getTime() !== dateTime.getTime()
        );
    }

    getAvailableSlots(date) {
        return this.availableSlots.filter(slot => 
            slot.toDateString() === date.toDateString()
        );
    }

    getRecurringAppointments(patientId) {
        return this.appointments.filter(apt => 
            apt.patientId === patientId && apt.isRecurring
        );
    }

    cancelAppointment(appointmentId) {
        const appointment = this.appointments.find(apt => apt.id === appointmentId);
        if (appointment) {
            appointment.status = 'cancelled';
            this.saveAppointments();
            return true;
        }
        return false;
    }

    rescheduleAppointment(appointmentId, newDateTime) {
        const appointment = this.appointments.find(apt => apt.id === appointmentId);
        if (appointment) {
            appointment.dateTime = newDateTime;
            appointment.status = 'rescheduled';
            this.saveAppointments();
            return true;
        }
        return false;
    }

    getUpcomingAppointments(patientId) {
        const now = new Date();
        return this.appointments
            .filter(apt => 
                apt.patientId === patientId && 
                new Date(apt.dateTime) > now &&
                apt.status === 'confirmed'
            )
            .sort((a, b) => new Date(a.dateTime) - new Date(b.dateTime));
    }
}

const appointmentSystem = new AppointmentSystem();


window.appointmentSystem = appointmentSystem; 