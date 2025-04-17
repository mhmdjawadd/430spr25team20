// auth-api.js - Handles authentication API calls to the backend

const AUTH_API_URL = 'http://localhost:5000'; // Change this to match your Flask server URL

/**
 * Decode a JWT token to access its payload
 * @param {string} token - JWT token
 * @returns {object} - Decoded token payload
 */
function parseJwt(token) {
    try {
        // Get the payload part of the JWT (second part)
        const base64Url = token.split('.')[1];
        const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
        const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
            return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
        }).join(''));
        
        // Log the token payload during development to see its structure
        console.log('JWT Token payload:', JSON.parse(jsonPayload));
        
        return JSON.parse(jsonPayload);
    } catch (e) {
        console.error('Error parsing JWT token:', e);
        return {};
    }
}

/**
 * Handle user login
 * @param {string} email - User email
 * @param {string} password - User password
 * @returns {Promise<object>} - Response with token and user data or error
 */
async function loginUser(email, password) {
    try {
        const response = await fetch(`${AUTH_API_URL}/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || data.message || 'Login failed');
        }
        
        // Save auth token and user data to localStorage - updated key name
        if (data.access_token) {
            localStorage.setItem('token', data.access_token);
            
            // Extract user data from token and/or response
            let userData = data.user || {};
            
            // If we have a token but no complete user data, try to extract from token
            if (!userData.first_name && !userData.last_name) {
                const tokenPayload = parseJwt(data.access_token);
                userData = {
                    ...userData,
                    user_id: tokenPayload.sub || userData.user_id,
                    email: tokenPayload.email || userData.email,
                    first_name: tokenPayload.first_name || userData.first_name,
                    last_name: tokenPayload.last_name || userData.last_name,
                    role: tokenPayload.role || userData.role
                };
            }
            
            localStorage.setItem('user', JSON.stringify(userData));
        }
        
        return data;
    } catch (error) {
        console.error('Login error:', error);
        throw error;
    }
}

/**
 * Handle user signup/registration
 * @param {object} userData - User registration data
 * @returns {Promise<object>} - Response with success message or error
 */
async function registerUser(userData) {
    try {
        const response = await fetch(`${AUTH_API_URL}/signup`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(userData)
        });

        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || data.message || 'Registration failed');
        }
        
        // Save auth token and user data to localStorage - updated key name
        if (data.access_token) {
            localStorage.setItem('token', data.access_token);
            
            // Store comprehensive user data
            // First try to use data from response
            let userInfo = {
                user_id: data.user_id,
                email: userData.email,
                first_name: userData.first_name,
                last_name: userData.last_name,
                role: data.role
            };
            
            // If we have a token, extract any missing data from it
            const tokenPayload = parseJwt(data.access_token);
            userInfo = {
                ...userInfo,
                user_id: userInfo.user_id || tokenPayload.sub,
                email: userInfo.email || tokenPayload.email,
                first_name: userInfo.first_name || tokenPayload.first_name,
                last_name: userInfo.last_name || tokenPayload.last_name,
                role: userInfo.role || tokenPayload.role
            };
            
            localStorage.setItem('user', JSON.stringify(userInfo));
        }
        
        return data;
    } catch (error) {
        console.error('Registration error:', error);
        throw error;
    }
}

/**
 * Check if user is currently authenticated
 * @returns {boolean} - Whether the user has a valid auth token
 */
function isAuthenticated() {
    const token = localStorage.getItem('token');
    return !!token; // Convert to boolean
}

/**
 * Get the current user data from localStorage or fetch from backend if needed
 * @returns {Promise<object|null>} - User data or null if not logged in
 */
async function getCurrentUserProfile() {
    const token = localStorage.getItem('token');
    if (!token) return null;
    
    // Try to get user from localStorage first
    const userJson = localStorage.getItem('user');
    let userData = userJson ? JSON.parse(userJson) : null;
    
    // Check if we have the basic user profile data
    if (!userData || !userData.first_name || !userData.last_name) {
        try {
            // Fetch user profile from backend
            const response = await fetch(`${AUTH_API_URL}/user/profile`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                const userProfile = await response.json();
                
                // Update user data with fetched profile
                userData = {
                    ...userData,
                    ...userProfile,
                    user_id: userProfile.user_id || (userData ? userData.user_id : null)
                };
                
                // Save updated user data
                localStorage.setItem('user', JSON.stringify(userData));
            }
        } catch (error) {
            console.error('Error fetching user profile:', error);
        }
    }
    
    return userData;
}

/**
 * Get current user data from localStorage
 * @returns {object|null} - Parsed user data or null
 */
function getCurrentUser() {
    const userJson = localStorage.getItem('user');
    return userJson ? JSON.parse(userJson) : null;
}

/**
 * Log out the current user
 */
function logoutUser() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
}