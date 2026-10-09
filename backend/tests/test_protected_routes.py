from backend.models.user import User
from backend.services.auth_service import AuthService
from backend.extensions import db

def test_unauthorized_dashboard_me_access(client):
    res = client.get("/api/me")
    assert res.status_code == 401
    assert "Authentication required" in res.get_json()["message"]

def test_authorized_me_via_bearer_token(client):
    user = User(name="Leo Leader", email="leo@example.com", is_verified=True)
    user.set_password("Password123!")
    db.session.add(user)
    db.session.commit()

    token = AuthService.create_access_token(user)

    res = client.get("/api/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert data["user"]["email"] == "leo@example.com"
    assert data["user"]["name"] == "Leo Leader"

def test_authorized_me_via_cookie(client):
    user = User(name="Mona Lisa", email="mona@example.com", is_verified=True)
    user.set_password("Password123!")
    db.session.add(user)
    db.session.commit()

    # Log in to get the cookie
    login_res = client.post("/api/login", json={
        "email": "mona@example.com",
        "password": "Password123!"
    })
    assert login_res.status_code == 200

    # Request /api/me (test client persists cookies from login)
    res = client.get("/api/me")
    assert res.status_code == 200
    assert res.get_json()["user"]["email"] == "mona@example.com"

def test_logout_clears_cookie(client):
    user = User(name="Nancy", email="nancy@example.com", is_verified=True)
    user.set_password("Password123!")
    db.session.add(user)
    db.session.commit()

    client.post("/api/login", json={"email": "nancy@example.com", "password": "Password123!"})
    
    # Call logout
    res = client.post("/api/logout")
    assert res.status_code == 200
    # Cookie should have expired / cleared
    set_cookie = res.headers.get("Set-Cookie", "")
    assert "access_token" in set_cookie
    assert "Expires=Thu, 01 Jan 1970" in set_cookie or "Max-Age=0" in set_cookie

def test_health_check_endpoint(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "healthy"
    assert data["services"]["database"] == "healthy"
    assert data["services"]["redis"] == "healthy"
