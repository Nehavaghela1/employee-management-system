from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_register_success():
    import time
    unique_email = f"testuser{int(time.time())}@gmail.com"
    response = client.post("/auth/register", json={
        "email": unique_email,
        "username": f"testuser{int(time.time())}",
        "password": "12345678"
    })
    assert response.status_code == 200
    assert response.json()["email"] == unique_email
    assert "hashed_password" not in response.json()

def test_register_duplicate_email():
    client.post("/auth/register", json={
        "email": "duplicate123@gmail.com",
        "username": "dupuser1",
        "password": "12345678"
    })
    response = client.post("/auth/register", json={
        "email": "duplicate123@gmail.com",
        "username": "dupuser2",
        "password": "12345678"
    })
    assert response.status_code == 400

def test_login_success():
    client.post("/auth/register", json={
        "email": "logintest123@gmail.com",
        "username": "logintest123",
        "password": "12345678"
    })
    response = client.post("/auth/login", json={
        "email": "logintest123@gmail.com",
        "password": "12345678"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_login_wrong_password():
    response = client.post("/auth/login", json={
        "email": "logintest123@gmail.com",
        "password": "wrongpassword"
    })
    assert response.status_code == 401

def test_login_nonexistent_user():
    response = client.post("/auth/login", json={
        "email": "nobody999@gmail.com",
        "password": "12345678"
    })
    assert response.status_code == 401