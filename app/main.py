from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, departments, employees, attendance, leaves, dashboard, audit
from app.database import engine, Base
import app.models.company
import app.models.leave_policy
import app.models.employee_kyc
import app.models.work_experience
import app.models.audit_log
import logging

from sqlalchemy import text

Base.metadata.create_all(bind=engine)

try:
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE employees ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;"))
        conn.execute(text("ALTER TABLE employees ADD COLUMN IF NOT EXISTS resignation_status VARCHAR DEFAULT 'none';"))
        conn.execute(text("ALTER TABLE employees ADD COLUMN IF NOT EXISTS resignation_reason TEXT;"))
        conn.execute(text("ALTER TABLE employees ADD COLUMN IF NOT EXISTS level VARCHAR DEFAULT 'L3';"))
        conn.execute(text("ALTER TABLE employees ADD COLUMN IF NOT EXISTS notice_period_days INT DEFAULT 30;"))
        conn.execute(text("ALTER TABLE employees ADD COLUMN IF NOT EXISTS requested_notice_days INT;"))
        conn.execute(text("ALTER TABLE employees ADD COLUMN IF NOT EXISTS notice_action VARCHAR DEFAULT 'none';"))

        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS company_id INT;"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR DEFAULT 'employee';"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_super_admin BOOLEAN DEFAULT FALSE;"))

        conn.execute(text("ALTER TABLE employees ADD COLUMN IF NOT EXISTS company_id INT;"))
        conn.execute(text("ALTER TABLE employees ADD COLUMN IF NOT EXISTS personal_email VARCHAR;"))
        conn.execute(text("ALTER TABLE employees ADD COLUMN IF NOT EXISTS invitation_status VARCHAR DEFAULT 'not_invited';"))
        conn.execute(text("ALTER TABLE employees ADD COLUMN IF NOT EXISTS invitation_sent_at TIMESTAMP WITH TIME ZONE;"))
        conn.execute(text("ALTER TABLE employees ADD COLUMN IF NOT EXISTS activation_token VARCHAR;"))
        conn.execute(text("ALTER TABLE employees ADD COLUMN IF NOT EXISTS is_on_probation BOOLEAN DEFAULT TRUE;"))
        conn.execute(text("ALTER TABLE employees ADD COLUMN IF NOT EXISTS probation_end_date DATE;"))

        conn.execute(text("ALTER TABLE departments ADD COLUMN IF NOT EXISTS company_id INT;"))
        conn.execute(text("ALTER TABLE departments ADD COLUMN IF NOT EXISTS head_employee_id INT;"))
        conn.commit()
except Exception as e:
    print(f"Migration notice: {e}")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
app = FastAPI(title="Employee Management System")

# ─── Global Exception Handler ───────────────────────────────────────────────
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    # Extracts the specific error message to return to the frontend
    errors = []
    for error in exc.errors():
        loc = error.get("loc", [])
        field = loc[-1] if loc else "field"
        msg = error.get("msg", "invalid input")
        errors.append(f"{field}: {msg}")
    return JSONResponse(
        status_code=422,
        content={"detail": errors}
    )

# ─── Global Security, Rate-Limiting & IP Audit Middleware ───────────────────
import time
from collections import defaultdict

# Stores request timestamps per IP: { "192.168.1.1": [timestamp1, timestamp2, ...] }
request_history = defaultdict(list)

# Blacklisted IP addresses (Can be populated dynamically or loaded from DB)
IP_BLACKLIST = {"198.51.100.42", "203.0.113.19"} 

@app.middleware("http")
async def global_security_middleware(request, call_next):
    client_ip = request.client.host if request.client else "127.0.0.1"
    current_time = time.time()

    # 1. IP Blacklist Verification
    if client_ip in IP_BLACKLIST:
        logger.warning(f"Blocked request from blacklisted IP: {client_ip}")
        return JSONResponse(
            status_code=403,
            content={"detail": f"Access denied. IP address {client_ip} is blocked for security reasons."}
        )

    # 2. Global Rate Limiter Safeguard (Max 60 requests per 60 seconds per IP)
    request_history[client_ip] = [t for t in request_history[client_ip] if current_time - t < 60]
    
    if len(request_history[client_ip]) >= 60:
        logger.warning(f"Rate limit exceeded for IP: {client_ip}")
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many requests. Rate limit exceeded (Max 60/min). Please wait 1 minute."}
        )
    
    request_history[client_ip].append(current_time)

    # 3. Process Request & Track Execution Time
    start_time = time.time()
    response = await call_next(request)
    process_time = round((time.time() - start_time) * 1000, 2)

    # 4. Security Headers Injection
    response.headers["X-Process-Time-MS"] = str(process_time)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"

    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(departments.router)
app.include_router(employees.router)
app.include_router(attendance.router)
app.include_router(leaves.router)
app.include_router(dashboard.router)
app.include_router(audit.router)

@app.get("/")
def root():
    return {"message": "Employee Management System API"}