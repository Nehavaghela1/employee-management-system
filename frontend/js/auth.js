const API = 'http://localhost:8000';

// Save login data
function saveAuth(token, isAdmin, email) {
    localStorage.setItem('token', token);
    localStorage.setItem('is_admin', isAdmin);
    localStorage.setItem('email', email);
}

// Clear login data
function clearAuth() {
    localStorage.removeItem('token');
    localStorage.removeItem('is_admin');
    localStorage.removeItem('email');
    localStorage.removeItem('emp_id');
    localStorage.removeItem('employee_code');
}

// Get token
function getToken() {
    return localStorage.getItem('token');
}

// Check if logged in
function isLoggedIn() {
    const token = getToken();
    if (!token) return false;
    try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        if (Date.now() > payload.exp * 1000) {
            clearAuth();
            return false;
        }
        return true;
    } catch(e) {
        clearAuth();
        return false;
    }
}

// Check if admin
function isAdmin() {
    return localStorage.getItem('is_admin') === 'true';
}

// Get current user email
function getCurrentEmail() {
    return localStorage.getItem('email') || '';
}

// Require login — call at top of protected pages
function requireLogin() {
    if (!isLoggedIn()) {
        window.location.href = 'login.html';
    }
}

// Require admin — call at top of admin pages
function requireAdmin() {
    if (!isLoggedIn()) {
        window.location.href = 'login.html';
        return;
    }
    if (!isAdmin()) {
        window.location.href = 'dashboard.html';
    }
}

// Logout
function logout() {
    clearAuth();
    window.location.href = 'login.html';
}

// Auth headers for API calls
function authHeaders() {
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getToken()}`
    };
}