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

def test_change_password():
    import time
    email = f"chgpass{int(time.time())}@gmail.com"
    client.post("/auth/register", json={
        "email": email,
        "username": f"chgpass{int(time.time())}",
        "password": "oldpassword123"
    })
    login_res = client.post("/auth/login", json={
        "email": email,
        "password": "oldpassword123"
    })
    token = login_res.json()["access_token"]

    # Change password
    chg_res = client.post("/auth/change-password", json={
        "current_password": "oldpassword123",
        "new_password": "newpassword123"
    }, headers={"Authorization": f"Bearer {token}"})
    assert chg_res.status_code == 200

    # Verify login with new password works
    new_login = client.post("/auth/login", json={
        "email": email,
        "password": "newpassword123"
    })
    assert new_login.status_code == 200