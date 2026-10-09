from backend.models.user import User
from backend.services.redis_service import RedisService
from backend.services.email_service import EmailService, EmailDeliveryError

def test_successful_registration_does_not_create_db_user(client, mock_smtp):
    payload = {
        "name": "Alice Developer",
        "email": "alice@example.com",
        "password": "Password123!",
        "confirm_password": "Password123!"
    }
    response = client.post("/api/register", json=payload)
    assert response.status_code == 201
    data = response.get_json()
    assert data["success"] is True
    assert "Verification code sent" in data["message"]

    # Verify PostgreSQL has NO record yet
    user_in_db = User.query.filter_by(email="alice@example.com").first()
    assert user_in_db is None

    # Verify Redis HAS pending user
    pending = RedisService.get_pending_user("alice@example.com")
    assert pending is not None
    assert pending["name"] == "Alice Developer"
    assert pending["password_hash"] != "Password123!"  # Hashed

    # Verify mock SMTP received email
    assert len(mock_smtp) == 1
    assert mock_smtp[0]["to_email"] == "alice@example.com"
    assert len(mock_smtp[0]["otp"]) == 6

def test_registration_validation_errors(client):
    # Short password
    res = client.post("/api/register", json={
        "name": "Bob",
        "email": "bob@example.com",
        "password": "short",
        "confirm_password": "short"
    })
    assert res.status_code == 400
    assert "at least 8 characters" in res.get_json()["message"]

    # Password mismatch
    res = client.post("/api/register", json={
        "name": "Bob",
        "email": "bob@example.com",
        "password": "Password123!",
        "confirm_password": "Different123!"
    })
    assert res.status_code == 400
    assert "Passwords do not match" in res.get_json()["message"]

    # Invalid email
    res = client.post("/api/register", json={
        "name": "Bob",
        "email": "invalid-email-address",
        "password": "Password123!",
        "confirm_password": "Password123!"
    })
    assert res.status_code == 400
    assert "valid email" in res.get_json()["message"]

def test_registration_duplicate_email(client, mock_smtp):
    # First, insert user in DB
    user = User(name="Existing User", email="existing@example.com", password_hash="dummyhash", is_verified=True)
    from backend.extensions import db
    db.session.add(user)
    db.session.commit()

    # Try registering with same email
    res = client.post("/api/register", json={
        "name": "Duplicate Tester",
        "email": "existing@example.com",
        "password": "Password123!",
        "confirm_password": "Password123!"
    })
    assert res.status_code == 409
    assert "already exists" in res.get_json()["message"]

def test_smtp_failure_cleans_up_redis(client, monkeypatch):
    def failing_send(*args, **kwargs):
        raise EmailDeliveryError("SMTP connection timed out")

    monkeypatch.setattr(EmailService, "send_otp_email", failing_send)

    res = client.post("/api/register", json={
        "name": "Charlie",
        "email": "charlie@example.com",
        "password": "Password123!",
        "confirm_password": "Password123!"
    })
    assert res.status_code == 503
    assert "Failed to send verification email" in res.get_json()["message"]

    # Ensure Redis has NO pending record left
    pending = RedisService.get_pending_user("charlie@example.com")
    assert pending is None
