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
        const url = `${API_BASE_URL}/doctors`;
        console.log('Calling getAllDoctors API at:', url);
        
        const response = await fetch(url);
        console.log('API response status:', response.status);
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || 'Failed to fetch doctors');
        }
        
        const data = await response.json();
        console.log('Doctors data received:', data);
        return data;
    } catch (error) {
        console.error('Error fetching all doctors:', error);
        throw error;
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
        const response = await fetch(`${API_BASE_URL}/appointments`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            },
            body: JSON.stringify(appointmentData)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || 'Failed to book appointment');
        }
        
        return await response.json();
    } catch (error) {
        console.error('Error booking appointment:', error);
        throw error;
    }
}

// Export the functions for ES modules
export { getAllDoctors, getAvailableDoctors, getAvailableTimeSlots, bookAppointment };

// Also make them available on window for non-module scripts
window.appointmentAPI = {
    getAllDoctors,
    getAvailableDoctors,
    getAvailableTimeSlots,
    bookAppointment
};