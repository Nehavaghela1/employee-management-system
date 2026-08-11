from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, departments, employees, attendance, leaves, dashboard, audit
from app.database import engine, Base
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
        conn.commit()
except Exception:
    pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
app = FastAPI(title="Employee Management System")

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