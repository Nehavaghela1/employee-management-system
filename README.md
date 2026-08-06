## Setup and Installation

### Prerequisites
- Python 3.12+
- PostgreSQL
- pip

### Step 1 — Clone the repository
```bash
git clone https://github.com/Nehavaghela1/employee-management-system.git
cd employee-management-system
```

### Step 2 — Create virtual environment
```bash
python3 -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows
```

### Step 3 — Install dependencies
```bash
pip install -r requirements.txt
```

### Step 4 — Set up environment variables
```bash
cp .env.example .env
```

Edit `.env` with your values:
### Step 5 — Create PostgreSQL database
```bash
psql -U postgres
CREATE DATABASE employee_management;
\q
```

### Step 6 — Run database migrations
```bash
alembic upgrade head
```

### Step 7 — Start the server
```bash
uvicorn app.main:app --reload
```

### Step 8 — Access the application
- API: http://localhost:8000
- Swagger docs: http://localhost:8000/docs
- Frontend: Open `frontend/index.html` in browser

## API Documentation

Full API documentation is available at `http://localhost:8000/docs` (Swagger UI).

### Authentication
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | /auth/register | Register new user | No |
| POST | /auth/login | Login and get JWT token | No |

### Departments
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | /departments/ | Get all departments | No |
| POST | /departments/ | Create department | Login |
| GET | /departments/{id} | Get department by ID | No |
| PUT | /departments/{id} | Update department | Admin |
| DELETE | /departments/{id} | Delete department | Admin |

### Employees
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | /employees/ | Get all employees (search, filter, sort, paginate) | No |
| POST | /employees/ | Create employee | Login |
| GET | /employees/{id} | Get employee by ID | No |
| PUT | /employees/{id} | Update employee | Login |
| DELETE | /employees/{id} | Delete employee | Admin |

### Attendance
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | /attendance/ | Get all attendance | Login |
| POST | /attendance/ | Mark today's attendance | Login |
| GET | /attendance/{id} | Get attendance record | Login |
| PUT | /attendance/{id} | Update check-out time | Login |
| DELETE | /attendance/{id} | Delete attendance | Admin |

### Leaves
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | /leaves/ | Get all leaves | Login |
| POST | /leaves/ | Request leave | Login |
| GET | /leaves/{id} | Get leave by ID | Login |
| PUT | /leaves/{id} | Approve/reject leave | Admin |
| DELETE | /leaves/{id} | Delete leave | Admin |

### Dashboard
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | /dashboard/ | Get system statistics | Login |

## Database Schema

### Users
- id, email (unique), username (unique), hashed_password, is_active, is_admin, created_at

### Departments
- id, name (unique), description, created_at

### Employees
- id, first_name, last_name, email (unique), phone, position, salary, hire_date, department_id (FK → departments), created_at

### Attendance
- id, employee_id (FK → employees), date, check_in, check_out, status, created_at

### Leaves
- id, employee_id (FK → employees), leave_type, start_date, end_date, reason, status, created_at

## Database Migration Instructions

```bash
# Create a new migration after model changes
alembic revision --autogenerate -m "description"

# Apply all migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

## Security

- Passwords hashed using bcrypt
- JWT tokens expire after 30 minutes
- Environment variables used for sensitive config
- Admin-only routes protected with role-based authorization
- Input validation via Pydantic schemas

## Assumptions and Design Decisions

1. **User and Employee are separate entities** — A user account (login) is separate from an employee record. An admin creates employee records; not all employees need login access.

2. **Attendance is today-only** — Attendance can only be marked for the current date to prevent backdating.

3. **Leave validation** — Leave requests cannot be created for past dates. End date must be after start date.

4. **Admin setup** — Admin users are set manually via database. First admin must be set with: `UPDATE users SET is_admin = TRUE WHERE email = 'admin@example.com';`

5. **Employee uniqueness** — Employees are unique by email AND by first+last name combination.

6. **Hire date** — Hire date cannot be set to a future date.

## Running Tests

```bash
pytest tests/ -v
```

## Frontend

Open `frontend/index.html` directly in browser while the backend server is running.

Features:
- Register and login
- View dashboard statistics
- Manage departments (admin: create, update, delete)
- Manage employees (search by name, filter by department, sort by salary/name, pagination)
- Mark daily attendance and update check-out time
- Submit and manage leave requests

## Known Limitations

- Employee list is publicly accessible (no login required to view)
- No employee-to-user account linking (future improvement)
- No email notifications for leave approvals
- No refresh token implementation (re-login required after 30 minutes)