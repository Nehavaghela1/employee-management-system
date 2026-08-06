from fastapi import FastAPI
from app.routers import auth ,departments, employees ,attendance,leaves,dashboard

app = FastAPI(title="Employee Management System")

app.include_router(auth.router)
app.include_router(departments.router)
app.include_router(employees.router)
app.include_router(attendance.router)
app.include_router(leaves.router)
app.include_router(dashboard.router)


@app.get("/")
def root():
    return {"message": "Employee Management System API"}