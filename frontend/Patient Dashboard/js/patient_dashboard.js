// JavaScript for patient dashboard

document.addEventListener('DOMContentLoaded', function() {
    // Initialize notifications
    initializeNotifications();
    
    // Initialize health metrics
    initializeHealthMetrics();
    
    // Handle appointment actions
    setupAppointmentActions();
    
    // Handle medical record actions
    setupRecordActions();
});

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
            const doctorName = appointmentCard.querySelector('h4').textContent;
            alert(`Reschedule appointment with ${doctorName}\nThis feature is coming soon!`);
        });
    });
    
    // Handle cancel buttons
    const cancelButtons = document.querySelectorAll('.btn-cancel');
    cancelButtons.forEach(button => {
        button.addEventListener('click', function() {
            const appointmentCard = this.closest('.appointment-card');
            const doctorName = appointmentCard.querySelector('h4').textContent;
            if (confirm(`Are you sure you want to cancel your appointment with ${doctorName}?`)) {
                alert('Appointment cancelled successfully!');
                // In a real app, you would call an API to cancel the appointment
                // and then update the UI accordingly
            }
        });
    });
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
