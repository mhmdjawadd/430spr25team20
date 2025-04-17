const API_URL = 'http://localhost:5000'; // Match your Flask server URL

document.addEventListener('DOMContentLoaded', () => {
    if (!isAuthenticated()) {
        // Redirect to login if not authenticated, maybe pass current page as redirect target
        window.location.href = `login.html?redirect=${encodeURIComponent(window.location.pathname)}`;
        return;
    }

    loadInsuranceData();

    const updateButton = document.getElementById('updateInsurance');
    if (updateButton) {
        updateButton.addEventListener('click', handleUpdateInsurance);
    }

    // Add listeners to clear provider/policy if coverage is NONE
    const coverageTypeSelect = document.getElementById('coverageType');
    if (coverageTypeSelect) {
        coverageTypeSelect.addEventListener('change', handleCoverageTypeChange);
    }
});

function handleCoverageTypeChange() {
    const coverageType = document.getElementById('coverageType').value;
    const providerNameInput = document.getElementById('providerName');
    const policyNumberInput = document.getElementById('policyNumber');

    if (coverageType === 'NONE') {
        providerNameInput.value = '';
        policyNumberInput.value = '';
        providerNameInput.disabled = true;
        policyNumberInput.disabled = true;
    } else {
        providerNameInput.disabled = false;
        policyNumberInput.disabled = false;
    }
}

async function loadInsuranceData() {
    const token = localStorage.getItem('token');
    if (!token) return;

    try {
        const response = await fetch(`${API_URL}/insurance`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            // silently fail without user notification
            return;
        }

        const data = await response.json();

        if (data.insurance) {
            document.getElementById('coverageType').value = data.insurance.coverage_type || '';
            document.getElementById('providerName').value = data.insurance.provider_name || '';
            document.getElementById('policyNumber').value = data.insurance.policy_number || '';
            document.getElementById('groupNumber').value = data.insurance.group_number || '';
            document.getElementById('policyHolderName').value = data.insurance.policy_holder_name || '';
            document.getElementById('coverageStartDate').value = data.insurance.coverage_start_date || '';
            document.getElementById('coverageEndDate').value = data.insurance.coverage_end_date || '';
        }
        handleCoverageTypeChange();

    } catch (e) {
        // silently ignore all errors
    }
}

async function handleUpdateInsurance() {
    const token = localStorage.getItem('token');
    if (!token) {
        alert('Authentication error. Please log in again.');
        // Redirect to login might be better here
        window.location.href = `login.html?redirect=${encodeURIComponent(window.location.pathname)}`;
        return;
    }

    // Disable button to prevent multiple clicks
    const updateButton = document.getElementById('updateInsurance');
    updateButton.disabled = true;
    updateButton.textContent = 'Updating...';

    const coverageType = document.getElementById('coverageType').value;
    const providerName = document.getElementById('providerName').value;
    const policyNumber = document.getElementById('policyNumber').value;
    const groupNumber = document.getElementById('groupNumber').value;
    const policyHolderName = document.getElementById('policyHolderName').value;
    const coverageStartDate = document.getElementById('coverageStartDate').value;
    const coverageEndDate = document.getElementById('coverageEndDate').value;
    const frontCardImageInput = document.getElementById('frontCardImage');
    const backCardImageInput = document.getElementById('backCardImage');

    // Basic validation
    if (!coverageType) {
        alert('Please select a coverage type.');
        updateButton.disabled = false;
        updateButton.textContent = 'Update Insurance Information';
        return;
    }
    if (coverageType !== 'NONE' && (!providerName || !policyNumber)) {
        alert('Provider Name and Policy Number are required unless coverage type is None.');
        updateButton.disabled = false;
        updateButton.textContent = 'Update Insurance Information';
        return;
    }

    const payload = {
        coverage_type: coverageType,
        provider_name: coverageType !== 'NONE' ? providerName : null,
        policy_number: coverageType !== 'NONE' ? policyNumber : null,
        group_number: groupNumber || null,
        policy_holder_name: policyHolderName || null,
        coverage_start_date: coverageStartDate || null,
        coverage_end_date: coverageEndDate || null,
        // Images will be added below if present
    };

    try {
        // Handle file uploads - convert to Base64
        if (frontCardImageInput.files.length > 0) {
            payload.front_card_image = await fileToBase64(frontCardImageInput.files[0]);
        }
        if (backCardImageInput.files.length > 0) {
            payload.back_card_image = await fileToBase64(backCardImageInput.files[0]);
        }

        const response = await fetch(`${API_URL}/insurance`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        // Check for specific 401 Unauthorized error
        if (response.status === 401) {
            // Token is likely expired or invalid
            alert('Your session has expired. Please log in again.');
            // Optionally clear the expired token and redirect
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            window.location.href = `login.html?redirect=${encodeURIComponent(window.location.pathname)}`;
            return; // Stop further processing
        }

        const result = await response.json();

        if (!response.ok) {
            // Handle other errors (e.g., 400 Bad Request, 500 Internal Server Error)
            throw new Error(result.error || `Failed to update insurance information (Status: ${response.status})`);
        }

        alert('Insurance information updated successfully!');
        // Optionally reload data or clear form fields if needed
        // loadInsuranceData(); // Reload to show updated data (excluding images)

    } catch (error) {
        console.error('Error updating insurance:', error);
        alert(`Error: ${error.message}`);
    } finally {
        // Re-enable button
        updateButton.disabled = false;
        updateButton.textContent = 'Update Insurance Information';
    }
}

// Helper function to convert a file to Base64
function fileToBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onload = () => resolve(reader.result); // result includes 'data:image/jpeg;base64,' prefix
        reader.onerror = error => reject(error);
    });
}

// Assume isAuthenticated, getCurrentUser, etc., are available globally
// if auth-api.js is included before this script in the HTML.
// If not, you might need to import them if using modules, or ensure
// auth-api.js is loaded first.

// Add a placeholder for isAuthenticated if auth-api.js might not be loaded first
// This prevents errors but won't actually work without auth-api.js
if (typeof isAuthenticated === 'undefined') {
    function isAuthenticated() {
        console.warn("isAuthenticated function not found. Make sure auth-api.js is loaded.");
        return !!localStorage.getItem('token'); // Basic check
    }
}