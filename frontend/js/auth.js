function checkAuth() {
   
    // Get current page filename
    const currentPage = window.location.pathname.split('/').pop();
    
    console.log("Auth check running on page:", currentPage);
    
    // Skip auth check for these pages - allow direct access
    // Added more robust checks for insurance portal
    if (currentPage === 'appointments.html' || 
        currentPage === 'insurance-portal.html' ||
        currentPage === 'insurance-portal' ||
        window.location.href.includes('insurance-portal') ||
        currentPage === '') {
        console.log("Auth check bypassed for:", currentPage);
        return;
    }

    // Rest of authentication logic
    const isLoggedIn = sessionStorage.getItem('isLoggedIn');
    const userType = sessionStorage.getItem('userType');

    if (!isLoggedIn) {
        console.log("Not logged in, redirecting to login page");
        window.location.href = 'login.html';
        return;
    }

   
    if (window.location.pathname.includes('or-calendar.html') && userType !== 'surgeon') {
        window.location.href = 'index.html';
    }
}

// Function to update the user greeting with the actual user's name
function updateUserGreeting() {
    const userGreetingElement = document.getElementById('userGreeting');
    if (!userGreetingElement) return;
    // Use centralized helper to get current user
    const userData = getCurrentUser();
    // Determine display name
    let displayName;
    if (userData && (userData.first_name || userData.email)) {
        displayName = userData.first_name || userData.email.split('@')[0];
        userGreetingElement.innerHTML = `<i class="fas fa-user"></i> Welcome, ${displayName}!`;
    } else {
        userGreetingElement.innerHTML = `<i class="fas fa-user"></i> Welcome, Guest!`;
    }
}

// Execute auth check and update greeting when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    checkAuth();
    updateUserGreeting();
});

// Function to handle logout
function handleLogout() {
    // Clear authentication data
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    sessionStorage.removeItem('isLoggedIn');
    sessionStorage.removeItem('userType');
    
    // Redirect to login page
    window.location.href = 'login.html';
}