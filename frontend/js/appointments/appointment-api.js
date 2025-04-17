/**
 * Appointment API functions for the Nabad healthcare platform
 * Handles all API calls related to appointments
 */

// Base API URL
const API_BASE_URL = 'http://localhost:5000';

/**
 * Get all doctors from the database
 * @returns {Promise} Promise object represents the list of all doctors
 */
async function getAllDoctors() {
    try {
        // Enhanced debugging
        console.log(`%c[API CALL] getAllDoctors - Starting`, 'color: blue; font-weight: bold');
        
        // Make the API URL absolutely clear
        const url = `${API_BASE_URL}/doctors`;
        console.log(`%c[API URL] ${url}`, 'color: green; font-weight: bold');
        
        // Add specific headers for troubleshooting CORS issues
        const headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        };
        console.log('[API Headers]', headers);
        
        // Make the fetch request with explicit options
        const response = await fetch(url, {
            method: 'GET',
            headers: headers,
            mode: 'cors',
            cache: 'no-cache',
            credentials: 'same-origin'
        });
        
        // Log detailed response info
        console.log(`%c[API Response] Status: ${response.status} ${response.statusText}`, 
                   response.ok ? 'color: green' : 'color: red; font-weight: bold');
        console.log('[API Response Headers]', [...response.headers.entries()]);
        
        // Handle response based on status
        if (!response.ok) {
            try {
                const errorData = await response.json();
                console.error('[API Error Response]', errorData);
                return []; // Return empty array instead of throwing
            } catch (jsonError) {
                const errorText = await response.text();
                console.error('[API Error Text]', errorText);
                return []; // Return empty array instead of throwing
            }
        }
        
        // Parse and validate response
        const data = await response.json();
        console.log('[API Success Response]', data);
        
        // Normalize the response format to always return an array
        let doctorsArray = data;
        
        // If the API returns an object with a doctors property, use that
        if (!Array.isArray(data) && data.doctors && Array.isArray(data.doctors)) {
            doctorsArray = data.doctors;
        } 
        // If the API returns a non-array that isn't a doctors object, return empty array
        else if (!Array.isArray(data)) {
            console.warn('[API Warning] Expected array of doctors but got:', typeof data);
            return [];
        }
        
        console.log(`%c[API SUCCESS] Retrieved ${doctorsArray.length} doctors`, 'color: green; font-weight: bold');
        return doctorsArray;
    } catch (error) {
        console.error('%c[API ERROR] Error fetching doctors:', 'color: red; font-weight: bold', error);
        return []; // Return empty array to gracefully handle errors
    }
}

/**
 * Get available doctors for a specific date
 * @param {string} date - Date in YYYY-MM-DD format
 * @param {string} department - Optional department filter
 * @returns {Promise} Promise object represents the list of available doctors
 */
async function getAvailableDoctors(date, department = null) {
    try {
        let url = `${API_BASE_URL}/doctors/available?date=${date}`;
        
        if (department) {
            url += `&department=${department}`;
        }
        
        const response = await fetch(url);
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || 'Failed to fetch available doctors');
        }
        
        return await response.json();
    } catch (error) {
        console.error('Error fetching available doctors:', error);
        throw error;
    }
}

/**
 * Get available time slots for a specific doctor on a given date
 * @param {number} doctorId - The ID of the doctor
 * @param {string} date - Date in YYYY-MM-DD format
 * @returns {Promise} Promise object represents the list of available time slots
 */
async function getAvailableTimeSlots(doctorId, date) {
    try {
        const url = `${API_BASE_URL}/appointments/timeslots?doctor_id=${doctorId}&date=${date}`;
        const response = await fetch(url);
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || 'Failed to fetch available time slots');
        }
        
        return await response.json();
    } catch (error) {
        console.error('Error fetching available time slots:', error);
        throw error;
    }
}

/**
 * Book an appointment
 * @param {Object} appointmentData - The appointment data
 * @returns {Promise} Promise object represents the created appointment
 */
async function bookAppointment(appointmentData) {
    try {
        console.log('Sending appointment data:', JSON.stringify(appointmentData));
        
        // Debug token availability - using consistent key name 'token'
        const token = localStorage.getItem('token');
        console.log('JWT Token available:', token ? 'Yes' : 'No (null or empty)');
        
        if (!token) {
            console.error('No JWT token found in localStorage. User may not be logged in.');
            throw new Error('Authentication required. Please log in to book an appointment.');
        }
        
        const response = await fetch(`${API_BASE_URL}/appointments`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(appointmentData)
        });
        
        console.log('Received status:', response.status);
        
        if (!response.ok) {
            const errorData = await response.json();
            console.error('API error details:', errorData);
            throw new Error(errorData.error || errorData.message || 'Failed to book appointment');
        }
        
        return await response.json();
    } catch (error) {
        console.error('Error booking appointment:', error);
        throw error;
    }
}

/**
 * Check insurance coverage for a specific doctor
 * @param {number} doctorId - The ID of the doctor
 * @returns {Promise} Promise object represents insurance coverage details
 */
async function checkInsuranceCoverage(doctorId) {
    try {
        const token = localStorage.getItem('token');
        if (!token) {
            throw new Error('Authentication required for insurance verification');
        }
        
        const url = `${API_BASE_URL}/insurance/verify`;
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ doctor_id: doctorId })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to verify insurance');
        }
        
        return await response.json();
    } catch (error) {
        console.error('Error checking insurance coverage:', error);
        throw error;
    }
}

/**
 * Get doctor availability for a date range (week/month view)
 * @param {number} doctorId - The ID of the doctor
 * @param {Date} startDate - The start date of the range
 * @param {Date} endDate - The end date of the range
 * @returns {Promise<Object>} - Promise that resolves to availability data by date
 */
async function getDoctorAvailabilityRange(doctorId, startDate, endDate) {
    try {
        // Format dates in YYYY-MM-DD format for the API
        const formattedStartDate = startDate.toISOString().split('T')[0];
        const formattedEndDate = endDate.toISOString().split('T')[0];
        
        // Make API request to get availability range
        const response = await fetch(`${API_BASE_URL}/appointments/availability-range`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            },
            body: JSON.stringify({
                doctor_id: doctorId,
                start_date: formattedStartDate,
                end_date: formattedEndDate
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to fetch availability range');
        }
        
        return await response.json();
    } catch (error) {
        console.error('Error fetching doctor availability range:', error);
        throw error;
    }
}

// Export the functions for ES modules - FIXED: removed duplicate export
export { getAllDoctors, getAvailableDoctors, getAvailableTimeSlots, bookAppointment, checkInsuranceCoverage, getDoctorAvailabilityRange };

// Also make them available on window for non-module scripts
window.appointmentAPI = {
    getAllDoctors,
    getAvailableDoctors,
    getAvailableTimeSlots,
    bookAppointment,
    checkInsuranceCoverage,
    getDoctorAvailabilityRange
};