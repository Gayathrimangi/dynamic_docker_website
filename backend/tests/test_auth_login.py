from backend.models.user import User
from backend.extensions import db

def test_login_successful(client):
    user = User(name="Jack User", email="jack@example.com", is_verified=True)
    user.set_password("Secret123!")
    db.session.add(user)
    db.session.commit()

    res = client.post("/api/login", json={
        "email": "jack@example.com",
        "password": "Secret123!"
    })

    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert data["user"]["email"] == "jack@example.com"
    assert "token" in data
    assert "access_token" in res.headers.get("Set-Cookie", "")

def test_login_invalid_password(client):
    user = User(name="Jack User", email="jack@example.com", is_verified=True)
    user.set_password("Secret123!")
    db.session.add(user)
    db.session.commit()

    res = client.post("/api/login", json={
        "email": "jack@example.com",
        "password": "WrongPassword!"
    })

    assert res.status_code == 401
    assert "Invalid email or password" in res.get_json()["message"]

def test_login_nonexistent_user(client):
    res = client.post("/api/login", json={
        "email": "unknown@example.com",
        "password": "Password123!"
    })
    assert res.status_code == 401
    assert "Invalid email or password" in res.get_json()["message"]

def test_login_unverified_pending_user_returns_403(client, mock_smtp):
    # Register but do not verify
    client.post("/api/register", json={
        "name": "Karen",
        "email": "karen@example.com",
        "password": "Password123!",
        "confirm_password": "Password123!"
    })

    # Karen tries to login before verifying OTP
    res = client.post("/api/login", json={
        "email": "karen@example.com",
        "password": "Password123!"
    })
    assert res.status_code == 403
    assert "pending OTP verification" in res.get_json()["message"]
