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

// Format date to DD/MM/YYYY format
function formatDDMMYYYY(dateStr) {
    if (!dateStr) return '—';
    const parts = dateStr.split('T')[0].split('-');
    if (parts.length === 3) {
        return `${parts[2]}/${parts[1]}/${parts[0]}`;
    }
    return dateStr;
}

// Automatically setup navbar admin links across all pages on DOM load
function autoSetupNavbar() {
    const updateNav = () => {
        const userEmailEl = document.getElementById('user-email');
        if (userEmailEl && !userEmailEl.textContent) {
            userEmailEl.textContent = getCurrentEmail();
        }

        if (isAdmin()) {
            const adminBadge = document.getElementById('admin-badge');
            const adminLink = document.getElementById('admin-link');
            const empLink = document.getElementById('emp-link');
            const deptLink = document.getElementById('dept-link');

            if (adminBadge) adminBadge.style.display = 'inline-block';
            if (adminLink) adminLink.style.display = 'inline-block';
            if (empLink) empLink.style.display = 'inline-block';
            if (deptLink) deptLink.style.display = 'inline-block';

            checkAdminResignationNotifications();
        }
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', updateNav);
    } else {
        updateNav();
    }
}

// Admin Resignation Toast Alert
function checkAdminResignationNotifications() {
    if (!isAdmin()) return;

    const check = async () => {
        try {
            const res = await fetch('http://localhost:8000/audit-logs/?limit=10', { headers: authHeaders() });
            if (!res.ok) return;
            const logs = await res.json();
            const lastSeen = localStorage.getItem('last_seen_resignation_id') || 0;

            const resignLogs = logs.filter(l => l.action === 'EMPLOYEE_RESIGNED' && l.id > Number(lastSeen));
            if (resignLogs.length > 0) {
                const newest = resignLogs[0];
                localStorage.setItem('last_seen_resignation_id', newest.id);
                showResignationToast(newest.details || `Employee ${newest.employee_code} has resigned`);
            }
        } catch(e) {}
    };

    check();
    setInterval(check, 10000);
}

function showResignationToast(message) {
    let toast = document.getElementById('resignation-toast');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'resignation-toast';
        toast.style.cssText = 'position:fixed;top:20px;right:20px;z-index:99999;background:#ef4444;color:#fff;padding:16px 20px;border-radius:12px;box-shadow:0 10px 25px rgba(239,68,68,0.3);font-weight:600;display:flex;align-items:center;gap:12px;max-width:380px;';
        document.body.appendChild(toast);
    }
    toast.innerHTML = `<span>🔔 <strong>Resignation Alert:</strong> ${message}</span> <button onclick="this.parentElement.remove()" style="background:none;border:none;color:#fff;font-size:18px;cursor:pointer;margin-left:auto">&times;</button>`;
}

autoSetupNavbar();