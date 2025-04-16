
class ReminderSystem {
    constructor() {
        this.reminders = this.loadReminders();
        this.initializeEventListeners();
        this.requestNotificationPermission();
    }

    loadReminders() {
        const savedReminders = localStorage.getItem('reminders');
        return savedReminders ? JSON.parse(savedReminders) : [];
    }

    saveReminders() {
        localStorage.setItem('reminders', JSON.stringify(this.reminders));
    }

    async requestNotificationPermission() {
        if ('Notification' in window) {
            const permission = await Notification.requestPermission();
            if (permission === 'granted') {
                console.log('Notification permission granted');
            }
        }
    }

    initializeEventListeners() {
        document.getElementById('has-caregiver').addEventListener('change', (e) => {
            this.toggleCaregiverFields(e.target.checked);
        });

       
        document.querySelectorAll('input[name$="-reminder"]').forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                this.validateReminderPreferences();
            });
        });
    }

    toggleCaregiverFields(show) {
        const caregiverFields = document.getElementById('caregiver-fields');
        caregiverFields.style.display = show ? 'block' : 'none';
        caregiverFields.classList.toggle('show', show);
    }

    validateReminderPreferences() {
        const emailReminder = document.getElementById('email-reminder');
        const smsReminder = document.getElementById('sms-reminder');
        const pushReminder = document.getElementById('push-reminder');

        
        if (!emailReminder.checked && !smsReminder.checked && !pushReminder.checked) {
            emailReminder.checked = true;
        }
    }

    scheduleReminder(appointment) {
        const reminderTime = parseInt(document.getElementById('reminder-time').value);
        const reminderDate = new Date(appointment.dateTime);
        reminderDate.setHours(reminderDate.getHours() - reminderTime);

        const reminder = {
            id: Date.now(),
            appointmentId: appointment.id,
            patientId: appointment.patientId,
            reminderDate: reminderDate.toISOString(),
            notificationMethods: this.getNotificationMethods(),
            caregiver: this.getCaregiverInfo(),
            status: 'scheduled'
        };

        this.reminders.push(reminder);
        this.saveReminders();
        this.setupReminderNotifications(reminder);
        return reminder;
    }

    getNotificationMethods() {
        const methods = [];
        if (document.getElementById('email-reminder').checked) methods.push('email');
        if (document.getElementById('sms-reminder').checked) methods.push('sms');
        if (document.getElementById('push-reminder').checked) methods.push('push');
        return methods;
    }

    getCaregiverInfo() {
        const hasCaregiver = document.getElementById('has-caregiver').checked;
        if (!hasCaregiver) return null;

        return {
            name: document.getElementById('caregiver-name').value,
            phone: document.getElementById('caregiver-phone').value,
            email: document.getElementById('caregiver-email').value,
            relation: document.getElementById('caregiver-relation').value
        };
    }

    setupReminderNotifications(reminder) {
        const now = new Date();
        const reminderDate = new Date(reminder.reminderDate);
        const timeUntilReminder = reminderDate - now;

        if (timeUntilReminder > 0) {
            setTimeout(() => {
                this.sendReminder(reminder);
            }, timeUntilReminder);
        }
    }

    sendReminder(reminder) {
       
        reminder.notificationMethods.forEach(method => {
            switch (method) {
                case 'email':
                    this.sendEmailReminder(reminder);
                    break;
                case 'sms':
                    this.sendSMSReminder(reminder);
                    break;
                case 'push':
                    this.sendPushReminder(reminder);
                    break;
            }
        });

        
        if (reminder.caregiver) {
            this.sendCaregiverReminder(reminder);
        }

        
        reminder.status = 'sent';
        this.saveReminders();
    }

    sendEmailReminder(reminder) {
  
        console.log(`Sending email reminder for appointment ${reminder.appointmentId}`);
        this.showLocalNotification('Email Reminder', 'Appointment reminder sent to your email');
    }

    sendSMSReminder(reminder) {

        console.log(`Sending SMS reminder for appointment ${reminder.appointmentId}`);
        this.showLocalNotification('SMS Reminder', 'Appointment reminder sent via SMS');
    }

    sendPushReminder(reminder) {
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification('Appointment Reminder', {
                body: `You have an appointment scheduled for ${new Date(reminder.reminderDate).toLocaleString()}`,
                icon: '/img/logo.png'
            });
        }
    }

    sendCaregiverReminder(reminder) {

        console.log(`Sending caregiver reminder for appointment ${reminder.appointmentId}`);
        this.showLocalNotification('Caregiver Reminder', 'Appointment reminder sent to caregiver');
    }

    showLocalNotification(title, message) {
        const notification = document.createElement('div');
        notification.className = 'alert alert-info alert-dismissible fade show';
        notification.innerHTML = `
            <strong>${title}</strong><br>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.querySelector('.appointment-container').insertBefore(notification, document.querySelector('.appointment-form'));
    }

    cancelReminder(appointmentId) {
        const reminder = this.reminders.find(r => r.appointmentId === appointmentId);
        if (reminder) {
            reminder.status = 'cancelled';
            this.saveReminders();
            this.notifyStaffCancellation(reminder);
        }
    }

    notifyStaffCancellation(reminder) {
     
        console.log(`Notifying staff about cancelled appointment ${reminder.appointmentId}`);
        this.showLocalNotification('Staff Notification', 'Appointment cancellation notified to staff');
    }
}


const reminderSystem = new ReminderSystem();

window.reminderSystem = reminderSystem; 