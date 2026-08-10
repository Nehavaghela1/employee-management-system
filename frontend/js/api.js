// AUTH
async function apiRegister(email, username, password) {
    const res = await fetch(`${API}/auth/register`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({email, username, password})
    });
    return {ok: res.ok, data: await res.json()};
}

async function apiLogin(email, password) {
    const res = await fetch(`${API}/auth/login`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({email, password})
    });
    return {ok: res.ok, data: await res.json()};
}

async function apiMakeAdmin(userId) {
    const res = await fetch(`${API}/auth/make-admin/${userId}`, {
        method: 'POST',
        headers: authHeaders()
    });
    return {ok: res.ok, data: await res.json()};
}

// DASHBOARD
async function apiDashboard() {
    const res = await fetch(`${API}/dashboard/`, {headers: authHeaders()});
    return {ok: res.ok, data: await res.json()};
}

// DEPARTMENTS
async function apiGetDepartments(page=1, limit=10) {
    const res = await fetch(`${API}/departments/?page=${page}&limit=${limit}`);
    return {ok: res.ok, data: await res.json()};
}

async function apiCreateDepartment(name, description) {
    const res = await fetch(`${API}/departments/`, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({name, description})
    });
    return {ok: res.ok, data: await res.json()};
}

async function apiUpdateDepartment(id, name, description) {
    const body = {};
    if (name) body.name = name;
    if (description) body.description = description;
    const res = await fetch(`${API}/departments/${id}`, {
        method: 'PUT',
        headers: authHeaders(),
        body: JSON.stringify(body)
    });
    return {ok: res.ok, data: await res.json()};
}

async function apiDeleteDepartment(id) {
    const res = await fetch(`${API}/departments/${id}`, {
        method: 'DELETE',
        headers: authHeaders()
    });
    return {ok: res.ok, data: await res.json()};
}

// EMPLOYEES
async function apiGetEmployees(params={}) {
    const q = new URLSearchParams(params).toString();
    const res = await fetch(`${API}/employees/?${q}`);
    return {ok: res.ok, data: await res.json()};
}

async function apiCreateEmployee(data) {
    const res = await fetch(`${API}/employees/`, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify(data)
    });
    return {ok: res.ok, data: await res.json()};
}

async function apiUpdateEmployee(id, data) {
    const res = await fetch(`${API}/employees/${id}`, {
        method: 'PUT',
        headers: authHeaders(),
        body: JSON.stringify(data)
    });
    return {ok: res.ok, data: await res.json()};
}

async function apiDeleteEmployee(id) {
    const res = await fetch(`${API}/employees/${id}`, {
        method: 'DELETE',
        headers: authHeaders()
    });
    return {ok: res.ok, data: await res.json()};
}

// ATTENDANCE
async function apiGetAttendance(params={}) {
    const q = new URLSearchParams(params).toString();
    const res = await fetch(`${API}/attendance/?${q}`, {headers: authHeaders()});
    return {ok: res.ok, data: await res.json()};
}

async function apiMarkAttendance(data) {
    const res = await fetch(`${API}/attendance/`, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify(data)
    });
    return {ok: res.ok, data: await res.json()};
}

async function apiUpdateAttendance(id, data) {
    const res = await fetch(`${API}/attendance/${id}`, {
        method: 'PUT',
        headers: authHeaders(),
        body: JSON.stringify(data)
    });
    return {ok: res.ok, data: await res.json()};
}

// LEAVES
async function apiGetLeaves(params={}) {
    const q = new URLSearchParams(params).toString();
    const res = await fetch(`${API}/leaves/?${q}`, {headers: authHeaders()});
    return {ok: res.ok, data: await res.json()};
}

async function apiCreateLeave(data) {
    const res = await fetch(`${API}/leaves/`, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify(data)
    });
    return {ok: res.ok, data: await res.json()};
}

async function apiUpdateLeave(id, status) {
    const res = await fetch(`${API}/leaves/${id}`, {
        method: 'PUT',
        headers: authHeaders(),
        body: JSON.stringify({status})
    });
    return {ok: res.ok, data: await res.json()};
}

async function apiDeleteLeave(id) {
    const res = await fetch(`${API}/leaves/${id}`, {
        method: 'DELETE',
        headers: authHeaders()
    });
    return {ok: res.ok, data: await res.json()};
}