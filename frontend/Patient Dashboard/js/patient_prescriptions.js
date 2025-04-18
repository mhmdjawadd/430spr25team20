document.addEventListener('DOMContentLoaded', function() {
    // Initialize filter buttons
    initializeFilters();
    
    // Setup prescription actions
    setupPrescriptionActions();
    
    // Initialize modal functionality
    initializeModal();
    
    // Initialize pagination
    initializePagination();
});

function initializeFilters() {
    const filterButtons = document.querySelectorAll('.filter-btn');
    const prescriptionCards = document.querySelectorAll('.prescription-card');
    
    filterButtons.forEach(button => {
        button.addEventListener('click', function() {
            const filter = this.getAttribute('data-filter');
            
            // Update active button
            filterButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            
            // Show/hide prescriptions based on filter
            prescriptionCards.forEach(card => {
                if (filter === 'all') {
                    card.style.display = 'block';
                } else {
                    if (card.classList.contains(filter)) {
                        card.style.display = 'block';
                    } else {
                        card.style.display = 'none';
                    }
                }
            });
        });
    });
    
    // Initialize sorting
    const sortSelect = document.getElementById('sort-by');
    sortSelect.addEventListener('change', sortPrescriptions);
}

function sortPrescriptions() {
    const sortBy = document.getElementById('sort-by').value;
    const container = document.querySelector('.prescriptions-container');
    const prescriptions = Array.from(container.querySelectorAll('.prescription-card'));
    
    prescriptions.sort((a, b) => {
        if (sortBy === 'date-newest') {
            const dateA = new Date(a.querySelector('.prescription-date p:first-child').textContent.replace('Prescribed: ', ''));
            const dateB = new Date(b.querySelector('.prescription-date p:first-child').textContent.replace('Prescribed: ', ''));
            return dateB - dateA;
        } else if (sortBy === 'date-oldest') {
            const dateA = new Date(a.querySelector('.prescription-date p:first-child').textContent.replace('Prescribed: ', ''));
            const dateB = new Date(b.querySelector('.prescription-date p:first-child').textContent.replace('Prescribed: ', ''));
            return dateA - dateB;
        } else if (sortBy === 'medication') {
            const nameA = a.querySelector('.prescription-title h4').textContent;
            const nameB = b.querySelector('.prescription-title h4').textContent;
            return nameA.localeCompare(nameB);
        } else if (sortBy === 'doctor') {
            const doctorA = a.querySelector('.prescription-info p:first-child').textContent.replace('Doctor: ', '');
            const doctorB = b.querySelector('.prescription-info p:first-child').textContent.replace('Doctor: ', '');
            return doctorA.localeCompare(doctorB);
        }
        return 0;
    });
    
    // Remove existing cards and append sorted ones
    prescriptions.forEach(prescription => container.removeChild(prescription));
    prescriptions.forEach(prescription => container.appendChild(prescription));
}

function setupPrescriptionActions() {
    // Handle details buttons
    const detailButtons = document.querySelectorAll('.btn-details');
    detailButtons.forEach(button => {
        button.addEventListener('click', function() {
            const prescriptionCard = this.closest('.prescription-card');
            const medicationName = prescriptionCard.querySelector('.prescription-title h4').textContent;
            const details = prescriptionCard.querySelector('.prescription-details').textContent.trim();
            alert(`${medicationName} Details:\n${details}`);
        });
    });
    
    // Handle refill buttons
    const refillButtons = document.querySelectorAll('.btn-refill');
    refillButtons.forEach(button => {
        button.addEventListener('click', function() {
            const prescriptionCard = this.closest('.prescription-card');
            const medicationName = prescriptionCard.querySelector('.prescription-title h4').textContent;
            
            // Pre-select this medication in the refill modal
            const prescriptionSelect = document.getElementById('prescription-select');
            for (let i = 0; i < prescriptionSelect.options.length; i++) {
                if (prescriptionSelect.options[i].text.includes(medicationName)) {
                    prescriptionSelect.selectedIndex = i;
                    break;
                }
            }
            
            // Open the modal
            document.getElementById('refill-request-modal').style.display = 'flex';
        });
    });
    
    // Handle set reminder buttons
    const reminderButtons = document.querySelectorAll('.btn-reminder');
    reminderButtons.forEach(button => {
        button.addEventListener('click', function() {
            const prescriptionCard = this.closest('.prescription-card');
            const medicationName = prescriptionCard.querySelector('.prescription-title h4').textContent;
            alert(`Set medication reminder for ${medicationName}\nThis feature is coming soon!`);
        });
    });
    
    // Handle request new buttons
    const requestNewButtons = document.querySelectorAll('.btn-request-new');
    requestNewButtons.forEach(button => {
        button.addEventListener('click', function() {
            const prescriptionCard = this.closest('.prescription-card');
            const medicationName = prescriptionCard.querySelector('.prescription-title h4').textContent;
            alert(`Request new prescription for ${medicationName}\nThis feature is coming soon!`);
        });
    });
}

function initializeModal() {
    const modal = document.getElementById('refill-request-modal');
    const openModalButton = document.getElementById('request-refill-btn');
    const closeButtons = document.querySelectorAll('.close-modal, .btn-cancel-form');
    const form = document.getElementById('refill-request-form');
    
    // Show/hide pharmacy details based on selection
    const pharmacySelect = document.getElementById('pharmacy-select');
    pharmacySelect.addEventListener('change', function() {
        const pharmacyDetails = document.querySelectorAll('.pharmacy-details');
        pharmacyDetails.forEach(detail => {
            if (this.value === 'other') {
                detail.style.display = 'block';
            } else {
                detail.style.display = 'none';
            }
        });
    });
    
    // Open modal
    openModalButton.addEventListener('click', function() {
        modal.style.display = 'flex';
    });
    
    // Close modal
    closeButtons.forEach(button => {
        button.addEventListener('click', function() {
            modal.style.display = 'none';
            form.reset();
            // Hide pharmacy details when closing
            document.querySelectorAll('.pharmacy-details').forEach(detail => {
                detail.style.display = 'none';
            });
        });
    });
    
    // Close when clicking outside
    window.addEventListener('click', function(event) {
        if (event.target === modal) {
            modal.style.display = 'none';
            form.reset();
            // Hide pharmacy details when closing
            document.querySelectorAll('.pharmacy-details').forEach(detail => {
                detail.style.display = 'none';
            });
        }
    });
    
    // Handle form submission
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // In a real app, you would send the form data to an API
        const prescription = document.getElementById('prescription-select').options[document.getElementById('prescription-select').selectedIndex].text;
        const pharmacy = document.getElementById('pharmacy-select').value === 'other' ? 
                         document.getElementById('pharmacy-name').value : 
                         document.getElementById('pharmacy-select').options[document.getElementById('pharmacy-select').selectedIndex].text;
        const deliveryOption = document.getElementById('delivery-option').options[document.getElementById('delivery-option').selectedIndex].text;
        
        alert(`Refill Request Submitted!\nPrescription: ${prescription}\nPharmacy: ${pharmacy}\nDelivery Option: ${deliveryOption}\n\nYour request has been sent to the pharmacy. You will be notified when it's ready.`);
        
        modal.style.display = 'none';
        form.reset();
        // Hide pharmacy details
        document.querySelectorAll('.pharmacy-details').forEach(detail => {
            detail.style.display = 'none';
        });
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
            
            // In a real app, you would load the prescriptions for the selected page
            const page = this.textContent;
            console.log(`Loading page ${page}`);
            
            // Update disabled state of prev/next buttons
            prevButton.classList.toggle('disabled', page === '1');
            nextButton.classList.toggle('disabled', page === '2');
        });
    });
    
    prevButton.addEventListener('click', function() {
        if (!this.classList.contains('disabled')) {
            const activePage = document.querySelector('.pagination-btn.page.active');
            const prevPage = activePage.previousElementSibling;
            if (prevPage && prevPage.classList.contains('page')) {
                activePage.classList.remove('active');
                prevPage.classList.add('active');
                
                // In a real app, you would load the prescriptions for the selected page
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
                
                // In a real app, you would load the prescriptions for the selected page
                console.log(`Loading page ${nextPage.textContent}`);
                
                // Update disabled state of prev/next buttons
                prevButton.classList.remove('disabled');
                this.classList.toggle('disabled', nextPage.textContent === '2');
            }
        }
    });
}
