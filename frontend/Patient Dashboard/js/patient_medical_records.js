document.addEventListener('DOMContentLoaded', function() {
    // Initialize filter buttons
    initializeFilters();
    
    // Setup record actions
    setupRecordActions();
    
    // Initialize modal functionality
    initializeModal();
    
    // Initialize pagination
    initializePagination();
});

function initializeFilters() {
    const filterButtons = document.querySelectorAll('.filter-btn');
    const recordCards = document.querySelectorAll('.record-card');
    
    filterButtons.forEach(button => {
        button.addEventListener('click', function() {
            const filter = this.getAttribute('data-filter');
            
            // Update active button
            filterButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            
            // Show/hide records based on filter
            recordCards.forEach(card => {
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
    sortSelect.addEventListener('change', sortRecords);
}

function sortRecords() {
    const sortBy = document.getElementById('sort-by').value;
    const container = document.querySelector('.records-container');
    const records = Array.from(container.querySelectorAll('.record-card'));
    
    records.sort((a, b) => {
        if (sortBy === 'date-newest') {
            const dateA = new Date(a.querySelector('.record-details p:nth-child(3)').textContent.replace('Date: ', ''));
            const dateB = new Date(b.querySelector('.record-details p:nth-child(3)').textContent.replace('Date: ', ''));
            return dateB - dateA;
        } else if (sortBy === 'date-oldest') {
            const dateA = new Date(a.querySelector('.record-details p:nth-child(3)').textContent.replace('Date: ', ''));
            const dateB = new Date(b.querySelector('.record-details p:nth-child(3)').textContent.replace('Date: ', ''));
            return dateA - dateB;
        } else if (sortBy === 'document-type') {
            const typeA = a.querySelector('.record-details p:nth-child(4)').textContent.replace('Type: ', '');
            const typeB = b.querySelector('.record-details p:nth-child(4)').textContent.replace('Type: ', '');
            return typeA.localeCompare(typeB);
        } else if (sortBy === 'provider') {
            const providerA = a.querySelector('.record-details p:nth-child(2)').textContent.replace('Performed by: ', '');
            const providerB = b.querySelector('.record-details p:nth-child(2)').textContent.replace('Performed by: ', '');
            return providerA.localeCompare(providerB);
        }
        return 0;
    });
    
    // Remove existing cards and append sorted ones
    records.forEach(record => container.removeChild(record));
    records.forEach(record => container.appendChild(record));
}

function setupRecordActions() {
    // Handle view buttons
    const viewButtons = document.querySelectorAll('.btn-view');
    viewButtons.forEach(button => {
        button.addEventListener('click', function() {
            const recordCard = this.closest('.record-card');
            const recordTitle = recordCard.querySelector('h4').textContent;
            alert(`Viewing ${recordTitle}\nThis feature is coming soon!`);
        });
    });
    
    // Handle download buttons
    const downloadButtons = document.querySelectorAll('.btn-download');
    downloadButtons.forEach(button => {
        button.addEventListener('click', function() {
            const recordCard = this.closest('.record-card');
            const recordTitle = recordCard.querySelector('h4').textContent;
            alert(`Downloading ${recordTitle}\nThis feature is coming soon!`);
        });
    });
    
    // Handle share buttons
    const shareButtons = document.querySelectorAll('.btn-share');
    shareButtons.forEach(button => {
        button.addEventListener('click', function() {
            const recordCard = this.closest('.record-card');
            const recordTitle = recordCard.querySelector('h4').textContent;
            alert(`Sharing ${recordTitle}\nThis feature is coming soon!`);
        });
    });
}

function initializeModal() {
    const modal = document.getElementById('upload-record-modal');
    const openModalButton = document.getElementById('upload-record-btn');
    const closeButtons = document.querySelectorAll('.close-modal, .btn-cancel-form');
    const form = document.getElementById('record-upload-form');
    
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
        const title = document.getElementById('record-title').value;
        const type = document.getElementById('record-type').options[document.getElementById('record-type').selectedIndex].text;
        const doctor = document.getElementById('doctor-name').value;
        const date = document.getElementById('record-date').value;
        const file = document.getElementById('record-file').files[0] ? document.getElementById('record-file').files[0].name : '';
        const isImportant = document.getElementById('important-record').checked;
        
        alert(`Record Uploaded Successfully!\nTitle: ${title}\nType: ${type}\nHealthcare Provider: ${doctor}\nDate: ${date}\nFile: ${file}\nMarked as Important: ${isImportant ? 'Yes' : 'No'}`);
        
        modal.style.display = 'none';
        form.reset();
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
            
            // In a real app, you would load the records for the selected page
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
                
                // In a real app, you would load the records for the selected page
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
                
                // In a real app, you would load the records for the selected page
                console.log(`Loading page ${nextPage.textContent}`);
                
                // Update disabled state of prev/next buttons
                prevButton.classList.remove('disabled');
                this.classList.toggle('disabled', nextPage.textContent === '3');
            }
        }
    });
}
