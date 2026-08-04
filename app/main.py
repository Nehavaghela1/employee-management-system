from fastapi import FastAPI

app = FastAPI(title="Employee Management System")

@app.get("/")
def root():
    return {"message": "Employee Management System API"}