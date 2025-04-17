/**
 * Mock appointment service to provide test data when backend is not available
 */

// Generate mock availability data for a date range
function generateMockAvailabilityData(doctorId, startDate, endDate) {
    const availability = {};
    
    // Convert dates to Date objects if they're strings
    const start = typeof startDate === 'string' ? new Date(startDate) : startDate;
    const end = typeof endDate === 'string' ? new Date(endDate) : endDate;
    
    // Generate data for each day in the range
    const currentDate = new Date(start);
    while (currentDate <= end) {
        // Skip weekends
        if (currentDate.getDay() !== 0 && currentDate.getDay() !== 6) {
            const dateStr = currentDate.toISOString().split('T')[0];
            availability[dateStr] = generateDailySlots();
        }
        
        // Move to next day
        currentDate.setDate(currentDate.getDate() + 1);
    }
    
    return {
        doctor_id: doctorId,
        doctor_name: "Dr. Mock Doctor",
        availability: availability
    };
}

// Generate slots for a single day
function generateDailySlots() {
    const slots = [];
    
    // Generate slots from 8 AM to 4 PM (1-hour intervals)
    for (let hour = 8; hour < 17; hour++) {
        const isBooked = Math.random() < 0.3; // 30% chance of being booked
        
        slots.push({
            start: `${hour.toString().padStart(2, '0')}:00`,
            end: `${(hour + 1).toString().padStart(2, '0')}:00`,
            is_booked: isBooked,
            time: `${hour}:00 ${hour >= 12 ? 'PM' : 'AM'} - ${hour+1}:00 ${hour+1 >= 12 ? 'PM' : 'AM'}`
        });
    }
    
    return slots;
}

// Generate mock time slots for a specific date
function generateMockTimeSlots(doctorId, date) {
    const slots = [];
    
    // Generate slots from 8 AM to 4 PM (1-hour intervals)
    for (let hour = 8; hour < 17; hour++) {
        const isBooked = Math.random() < 0.3; // 30% chance of being booked
        
        slots.push({
            start: `${hour.toString().padStart(2, '0')}:00`,
            end: `${(hour + 1).toString().padStart(2, '0')}:00`,
            is_booked: isBooked
        });
    }
    
    return slots;
}

// Make mock functions available globally
window.mockAppointmentService = {
    generateMockAvailabilityData,
    generateMockTimeSlots
};

// Removed the export statement that was causing the SyntaxError
// This file is included as a regular script, not as an ES module
