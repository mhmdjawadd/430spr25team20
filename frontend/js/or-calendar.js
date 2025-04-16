document.addEventListener('DOMContentLoaded', function() {
 
    var calendarEl = document.getElementById('calendar');
    var calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'timeGridWeek',
        slotMinTime: '07:00:00',
        slotMaxTime: '19:00:00',
        allDaySlot: false,
        headerToolbar: false,
        editable: true,
        selectable: true,
        selectMirror: true,
        dayMaxEvents: true,
        select: function(info) {
            showScheduleModal(info);
        }
    });
    calendar.render();


    document.querySelector('.btn-schedule, button[onclick="showScheduleModal()"]').addEventListener('click', function() {
        showScheduleModal();
    });

 
    document.querySelector('button.manage-resources').addEventListener('click', function() {
        showResourcesModal();
    });

    
    document.querySelectorAll('.room-checkbox input').forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            updateCalendarView();
        });
    });

    
    document.querySelector('.modal .close-btn, .modal .btn-cancel').addEventListener('click', function() {
        closeModal();
    });

    
    document.querySelector('.modal .btn-schedule').addEventListener('click', function(e) {
        e.preventDefault();
        handleScheduleSubmission();
    });

  
    document.querySelector('.modal .btn-cancel').addEventListener('click', function() {
        closeModal();
    });
});


function showScheduleModal(info = null) {
    const modal = document.getElementById('scheduleModal');
    modal.style.display = 'block';
    
    if (info) {
        
        const dateInput = modal.querySelector('input[type="date"]');
        const timeInput = modal.querySelector('input[type="time"]');
        
        if (info.startStr) {
            const startDate = new Date(info.startStr);
            dateInput.value = startDate.toISOString().split('T')[0];
            timeInput.value = startDate.toTimeString().slice(0,5);
        }
    }
}


function closeModal() {
    const modal = document.getElementById('scheduleModal');
    modal.style.display = 'none';
  
    document.getElementById('surgeryForm').reset();
}


function handleScheduleSubmission() {
  
    const surgeryType = document.querySelector('select[name="surgeryType"]').value;
    const operatingRoom = document.querySelector('select[name="operatingRoom"]').value;
    const date = document.querySelector('input[type="date"]').value;
    const time = document.querySelector('input[type="time"]').value;
    
   
    if (!surgeryType || !operatingRoom || !date || !time) {
        alert('Please fill in all required fields');
        return;
    }

 
    const event = {
        title: surgeryType,
        start: `${date}T${time}`,
        resourceId: operatingRoom
    };

    
    calendar.addEvent(event);

 
    closeModal();

 
    alert('Surgery scheduled successfully!');
}


function checkForConflicts(room, date, time) {
    
    return false;
}


function showConflictAlert() {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-danger';
    alertDiv.innerHTML = `
        <i class="fas fa-exclamation-triangle"></i>
        Resource conflict detected! Please select a different time or room.
    `;
    document.body.appendChild(alertDiv);
    setTimeout(() => alertDiv.remove(), 3000);
}


function showSuccessMessage(message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-success';
    alertDiv.textContent = message;
    document.body.appendChild(alertDiv);
    setTimeout(() => alertDiv.remove(), 3000);
}


function addHours(time, hours) {
    const [h, m] = time.split(':');
    const date = new Date();
    date.setHours(parseInt(h) + hours);
    date.setMinutes(parseInt(m));
    return date.toTimeString().slice(0,5);
}


function updateCalendarView() {
    const selectedRooms = Array.from(document.querySelectorAll('.room-checkbox input:checked'))
        .map(checkbox => checkbox.dataset.room);
    
 
    calendar.getEvents().forEach(event => {
        if (selectedRooms.includes(event.extendedProps.resourceId)) {
            event.show();
        } else {
            event.hide();
        }
    });
} 