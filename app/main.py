from fastapi import FastAPI
from app.routers import auth ,departments

app = FastAPI(title="Employee Management System")

app.include_router(auth.router)
app.include_router(departments.router)

@app.get("/")
def root():
    return {"message": "Employee Management System API"}