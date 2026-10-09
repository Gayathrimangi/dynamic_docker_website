from backend.models.user import User
from backend.services.redis_service import RedisService

def test_successful_otp_verification_creates_db_user(client, mock_smtp):
    email = "dave@example.com"
    client.post("/api/register", json={
        "name": "Dave Developer",
        "email": email,
        "password": "Password123!",
        "confirm_password": "Password123!"
    })

    assert len(mock_smtp) == 1
    otp = mock_smtp[0]["otp"]

    # Now verify OTP
    res = client.post("/api/verify-otp", json={
        "email": email,
        "otp": otp
    })

    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert data["user"]["email"] == email
    assert "token" in data

    # Verify cookie is set
    assert "access_token" in res.headers.get("Set-Cookie", "")

    # Verify user exists in PostgreSQL now!
    user = User.query.filter_by(email=email).first()
    assert user is not None
    assert user.name == "Dave Developer"
    assert user.is_verified is True
    assert user.check_password("Password123!") is True

    # Verify Redis is purged
    assert RedisService.get_pending_user(email) is None
    assert RedisService.is_registration_pending(email) is False

def test_invalid_otp_decrements_attempts(client, mock_smtp):
    email = "eve@example.com"
    client.post("/api/register", json={
        "name": "Eve Developer",
        "email": email,
        "password": "Password123!",
        "confirm_password": "Password123!"
    })

    # Send incorrect OTP
    res = client.post("/api/verify-otp", json={
        "email": email,
        "otp": "000000"
    })
    assert res.status_code == 400
    data = res.get_json()
    assert data["success"] is False
    assert "4 attempt(s) remaining" in data["message"]

    # User must still NOT be in DB
    assert User.query.filter_by(email=email).first() is None

def test_exceeding_max_otp_attempts_invalidates_session(client, mock_smtp):
    email = "frank@example.com"
    client.post("/api/register", json={
        "name": "Frank Developer",
        "email": email,
        "password": "Password123!",
        "confirm_password": "Password123!"
    })

    # Enter wrong OTP 5 times
    for i in range(4):
        res = client.post("/api/verify-otp", json={"email": email, "otp": "999999"})
        assert res.status_code == 400

    # 5th attempt: should invalidate
    res = client.post("/api/verify-otp", json={"email": email, "otp": "999999"})
    assert res.status_code in (400, 410)
    assert "Maximum attempts exceeded" in res.get_json()["message"]

    # Pending registration must be completely removed from Redis
    assert RedisService.get_pending_user(email) is None

def test_verify_expired_or_nonexistent_otp(client):
    res = client.post("/api/verify-otp", json={
        "email": "nonexistent@example.com",
        "otp": "123456"
    })
    assert res.status_code in (404, 410)
    assert "expired or not found" in res.get_json()["message"]

def test_verify_malformed_otp(client):
    res = client.post("/api/verify-otp", json={
        "email": "test@example.com",
        "otp": "abc"
    })
    assert res.status_code == 400
    assert "valid 6-digit number" in res.get_json()["message"]
