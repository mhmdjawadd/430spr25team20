document.addEventListener('DOMContentLoaded', function() {
    // Initialize filter buttons
    initializeFilters();
    
    // Setup appointment actions
    setupAppointmentActions();
    
    // Initialize modal functionality
    initializeModal();
    
    // Initialize pagination
    initializePagination();
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
                appointmentCard.classList.remove('upcoming');
                appointmentCard.classList.add('cancelled');
                const statusSpan = appointmentCard.querySelector('.status');
                statusSpan.textContent = 'Cancelled';
                statusSpan.className = 'status cancelled';
                
                // Replace action buttons
                const actionDiv = appointmentCard.querySelector('.appointment-actions');
                actionDiv.innerHTML = `
                    <button class="btn-details"><i class="fas fa-info-circle"></i> Details</button>
                    <button class="btn-book-again"><i class="fas fa-redo"></i> Book Again</button>
                `;
                
                // Setup the new buttons
                actionDiv.querySelector('.btn-details').addEventListener('click', function() {
                    alert(`Appointment Details for ${doctorName}`);
                });
                
                actionDiv.querySelector('.btn-book-again').addEventListener('click', function() {
                    alert(`Book again with ${doctorName}`);
                });
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
