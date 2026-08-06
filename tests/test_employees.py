from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def get_token():
    client.post("/auth/register", json={
        "email": "emptest999@gmail.com",
        "username": "emptest999",
        "password": "12345678"
    })
    response = client.post("/auth/login", json={
        "email": "emptest999@gmail.com",
        "password": "12345678"
    })
    return response.json()["access_token"]

def test_get_employees():
    response = client.get("/employees/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_create_employee_without_token():
    response = client.post("/employees/", json={
        "first_name": "Test",
        "last_name": "User",
        "email": "test.emp999@gmail.com",
        "position": "Developer"
    })
    assert response.status_code == 401

def test_create_employee_with_token():
    import time
    token = get_token()
    unique_email = f"pytest.emp{int(time.time())}@gmail.com"
    response = client.post("/employees/", json={
        "first_name": "Pytest",
        "last_name": "Employee",
        "email": unique_email,
        "position": "Developer"
    }, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["first_name"] == "Pytest"

def test_get_employee_not_found():
    response = client.get("/employees/99999")
    assert response.status_code == 404

def test_search_employee():
    response = client.get("/employees/?name=Pytest")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_pagination():
    response = client.get("/employees/?page=1&limit=2")
    assert response.status_code == 200
    assert len(response.json()) <= 2