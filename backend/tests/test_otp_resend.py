from backend.services.redis_service import RedisService
from backend.extensions import get_redis

def test_resend_cooldown_restriction(client, mock_smtp):
    email = "grace@example.com"
    client.post("/api/register", json={
        "name": "Grace",
        "email": email,
        "password": "Password123!",
        "confirm_password": "Password123!"
    })

    # Immediate resend attempt should hit cooldown (429)
    res = client.post("/api/resend-otp", json={"email": email})
    assert res.status_code == 429
    data = res.get_json()
    assert data["success"] is False
    assert "Please wait" in data["message"]
    assert data["cooldown_seconds"] > 0

def test_resend_after_cooldown_generates_new_otp(client, mock_smtp):
    email = "heidi@example.com"
    client.post("/api/register", json={
        "name": "Heidi",
        "email": email,
        "password": "Password123!",
        "confirm_password": "Password123!"
    })
    initial_otp = mock_smtp[-1]["otp"]

    # Simulate cooldown expiry by deleting cooldown key in Redis
    r = get_redis()
    r.delete(RedisService._cooldown_key(email))

    # Now resend
    res = client.post("/api/resend-otp", json={"email": email})
    assert res.status_code == 200
    assert res.get_json()["success"] is True

    # New email sent with new OTP
    assert len(mock_smtp) == 2
    new_otp = mock_smtp[-1]["otp"]
    assert new_otp != initial_otp

    # Old OTP should no longer verify
    res_old = client.post("/api/verify-otp", json={"email": email, "otp": initial_otp})
    assert res_old.status_code == 400

    # New OTP verifies successfully!
    res_new = client.post("/api/verify-otp", json={"email": email, "otp": new_otp})
    assert res_new.status_code == 200

def test_resend_max_limit_enforced(client, mock_smtp):
    email = "ian@example.com"
    client.post("/api/register", json={
        "name": "Ian",
        "email": email,
        "password": "Password123!",
        "confirm_password": "Password123!"
    })

    r = get_redis()
    # Perform 3 resends (clearing cooldown each time)
    for _ in range(3):
        r.delete(RedisService._cooldown_key(email))
        res = client.post("/api/resend-otp", json={"email": email})
        assert res.status_code == 200

    # 4th resend exceeds maximum allowed (3)
    r.delete(RedisService._cooldown_key(email))
    res = client.post("/api/resend-otp", json={"email": email})
    assert res.status_code == 400
    assert "Maximum OTP resend limit" in res.get_json()["message"]
