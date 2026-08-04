from fastapi import FastAPI
from app.routers import auth

app = FastAPI(title="Employee Management System")

app.include_router(auth.router)

@app.get("/")
def root():
    return {"message": "Employee Management System API"}