function checkAuth() {
   
    const isLoggedIn = sessionStorage.getItem('isLoggedIn');
    const userType = sessionStorage.getItem('userType');

    // Skip auth check for appointments page - allow direct access
    if (window.location.pathname.includes('appointments.html')) {
        return;
    }

    if (!isLoggedIn) {
        window.location.href = 'login.html';
        return;
    }

   
    if (window.location.pathname.includes('or-calendar.html') && userType !== 'surgeon') {
        window.location.href = 'index.html';
    }
}


document.addEventListener('DOMContentLoaded', checkAuth);